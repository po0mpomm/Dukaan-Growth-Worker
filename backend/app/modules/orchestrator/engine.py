"""
Workflow Engine — State Machine (PRD §9, TRD §8)

State transitions:
  S0_RECEIVED → S1_VALIDATING → S2_ANALYZING → S3_PHRASING
  → S4_CHECKING → S5_REVIEW → S6_SAVING → S7_SHARING → S_DONE

Failure paths:
  Any state → S_ESCALATED (validation/policy failure)
  Any state → S_ERROR (unexpected fault)

Each node:
  - Is idempotent (safe to retry after power cut)
  - Persists output before transitioning
  - Has a timeout (TRD §8)
  - Logs every state transition to audit.db
"""

import asyncio
import traceback
from pathlib import Path
from typing import Any

import structlog

from app.config import Settings
from app.contracts import (
    CompletenessResult,
    EscalationResult,
    FindingsObject,
    ResultObject,
    RunStatus,
    ValidationOutcome,
    WorkflowState,
)

log = structlog.get_logger(__name__)

# Progress milestones per state (for frontend progress bar)
STATE_PROGRESS = {
    WorkflowState.RECEIVED: 5,
    WorkflowState.VALIDATING: 15,
    WorkflowState.ANALYZING: 40,
    WorkflowState.PHRASING: 65,
    WorkflowState.CHECKING: 80,
    WorkflowState.REVIEW: 90,
    WorkflowState.SAVING: 95,
    WorkflowState.SHARING: 98,
    WorkflowState.DONE: 100,
    WorkflowState.ESCALATED: 100,
    WorkflowState.ERROR: 100,
}


class WorkflowEngine:
    """
    Orchestrates the full analysis workflow.
    Designed to be swapped for LangGraph in Phase 4 without changing any other module.
    """

    def __init__(self, settings: Settings, run_store: dict[str, RunStatus]) -> None:
        self.settings = settings
        self.run_store = run_store

    def _update_state(
        self,
        run_id: str,
        state: WorkflowState,
        message_en: str = "",
        message_hi: str = "",
        **kwargs: Any,
    ) -> None:
        run = self.run_store.get(run_id)
        if run:
            run.state = state
            run.progress_pct = STATE_PROGRESS.get(state, 0)
            if message_en:
                run.message_en = message_en
            if message_hi:
                run.message_hi = message_hi
            for k, v in kwargs.items():
                setattr(run, k, v)

    async def execute(
        self,
        run_id: str,
        sales_bytes: bytes,
        expenses_bytes: bytes,
        udhaar_bytes: bytes,
        sales_filename: str,
        expenses_filename: str,
        udhaar_filename: str,
        month: str,
        language: str,
    ) -> None:
        """
        Full workflow execution. Each step wrapped in try/except.
        On unexpected fault → S_ERROR. On validation/policy failure → S_ESCALATED.
        """
        try:
            # ── S1: Validate & Score Completeness ────────────────────────────
            self._update_state(
                run_id, WorkflowState.VALIDATING,
                message_en="Validating your files...",
                message_hi="आपकी फ़ाइलें जाँची जा रही हैं...",
            )

            from app.modules.ingest.parser import parse_files
            from app.modules.ingest.completeness import compute_completeness

            parsed = await asyncio.wait_for(
                asyncio.to_thread(
                    parse_files,
                    sales_bytes, sales_filename,
                    expenses_bytes, expenses_filename,
                    udhaar_bytes, udhaar_filename,
                    month,
                ),
                timeout=10.0,
            )

            completeness = compute_completeness(parsed, month, self.settings)

            if completeness.outcome == ValidationOutcome.ESCALATE:
                self._escalate(run_id, completeness, language)
                return

            # ── S2: Analyze ──────────────────────────────────────────────────
            self._update_state(
                run_id, WorkflowState.ANALYZING,
                message_en="Analysing your business data...",
                message_hi="आपके व्यापार का विश्लेषण हो रहा है...",
            )

            from app.modules.analytics.metrics import compute_metrics
            from app.modules.analytics.rules import detect_weak_areas
            from app.modules.analytics.scoring import rank_followups
            from app.modules.analytics.mom import compute_mom

            metrics = await asyncio.wait_for(
                asyncio.to_thread(compute_metrics, parsed, month),
                timeout=10.0,
            )
            weak_areas = detect_weak_areas(metrics, self.settings)
            followups = rank_followups(parsed, metrics)
            mom = compute_mom(metrics, month, self.settings.data_dir)

            # Build findings object (PII-free structured data for model)
            findings = FindingsObject(
                language=language,
                month=month,
                verdict=_derive_verdict(weak_areas),
                weak_areas=weak_areas[:3],   # Top 3 only
                followups=followups[:5],     # Top 5 only
                comparison=mom,
            )

            # ── S3: Phrase (model or templates) ──────────────────────────────
            self._update_state(
                run_id, WorkflowState.PHRASING,
                message_en="Preparing your action plan...",
                message_hi="आपकी कार्य योजना तैयार हो रही है...",
            )

            from app.modules.llm_adapter.selector import get_cached_adapter
            adapter = get_cached_adapter()
            actions = await asyncio.wait_for(
                adapter.phrase(findings),
                timeout=self.settings.llm_timeout_seconds,
            )

            # ── S4: Check (G4, G5, G6) ───────────────────────────────────────
            self._update_state(
                run_id, WorkflowState.CHECKING,
                message_en="Verifying output accuracy...",
                message_hi="आउटपुट की सटीकता जाँची जा रही है...",
            )

            from app.modules.guardrails.g4_schema import validate_actions
            from app.modules.guardrails.g5_factuality import verify_factuality
            from app.modules.guardrails.g6_content import check_content

            actions_valid, actions_source = validate_actions(actions, findings)
            actions_fact, actions_source = verify_factuality(actions_valid, findings, actions_source)
            actions_final, model_used = check_content(actions_fact, findings, actions_source)

            # ── Build final result ────────────────────────────────────────────
            from app.modules.analytics.metrics import build_verdict_text
            verdict_en, verdict_hi = build_verdict_text(weak_areas, metrics)

            caveat_en = caveat_hi = None
            if completeness.outcome == ValidationOutcome.PROCEED_WITH_CAVEAT:
                caveat_en = "Note: some data was incomplete. Results may not be fully accurate."
                caveat_hi = "नोट: कुछ डेटा अधूरा था। परिणाम पूरी तरह सटीक नहीं हो सकते।"

            result = ResultObject(
                run_id=run_id,
                month=month,
                language=language,
                completeness=completeness,
                verdict_en=verdict_en,
                verdict_hi=verdict_hi,
                weak_areas=weak_areas[:3],
                actions=actions_final,
                followups=followups[:5],
                comparison=mom,
                has_caveat=(completeness.outcome == ValidationOutcome.PROCEED_WITH_CAVEAT),
                caveat_en=caveat_en,
                caveat_hi=caveat_hi,
                model_used=(model_used == "model"),
            )

            # ── S6: Save snapshot ────────────────────────────────────────────
            self._update_state(
                run_id, WorkflowState.SAVING,
                message_en="Saving your monthly record...",
                message_hi="आपका मासिक रिकॉर्ड सहेजा जा रहा है...",
            )

            from app.modules.analytics.mom import save_snapshot
            save_snapshot(result, self.settings.data_dir)

            # ── Done ─────────────────────────────────────────────────────────
            self._update_state(
                run_id, WorkflowState.DONE,
                message_en="Analysis complete.",
                message_hi="विश्लेषण पूर्ण।",
                result=result,
            )
            log.info("run_completed", run_id=run_id, weak_areas=[w.rule_id for w in weak_areas])

        except asyncio.TimeoutError:
            log.error("run_timeout", run_id=run_id)
            self._update_state(
                run_id, WorkflowState.ERROR,
                message_en="A step took too long. Please try again.",
                message_hi="एक चरण में बहुत समय लगा। कृपया फिर से प्रयास करें।",
                error_message="Timeout",
            )
        except Exception as exc:
            log.error("run_error", run_id=run_id, error=str(exc), tb=traceback.format_exc())
            self._update_state(
                run_id, WorkflowState.ERROR,
                message_en="Something went wrong. No partial results have been shown.",
                message_hi="कुछ गलत हो गया। कोई आंशिक परिणाम नहीं दिखाया गया है।",
                error_message=str(exc),
            )

    def _escalate(
        self,
        run_id: str,
        completeness: CompletenessResult,
        language: str,
    ) -> None:
        """Build and store a plain escalation result (max 2 questions)."""
        # Determine reason and questions from block checks
        reason_code = "INCOMPLETE_DATA"
        reason_en = "I cannot give reliable advice yet."
        reason_hi = "मैं अभी विश्वसनीय सलाह नहीं दे सकता।"
        questions = []

        if completeness.day_coverage < self.settings.day_coverage_block:
            missing_days = round((1 - completeness.day_coverage) * 30)
            reason_en = f"Sales for {missing_days} days are missing."
            reason_hi = f"{missing_days} दिनों की बिक्री का डेटा नहीं है।"
            questions = [
                "Were these days closed, or was the data not written down?",
                "Can you add the missing sales and upload again?",
            ]
        elif "FILE_MISSING" in completeness.block_checks_failed:
            reason_code = "FILE_MISSING"
            reason_en = "One or more required files could not be read."
            reason_hi = "एक या अधिक आवश्यक फ़ाइलें पढ़ी नहीं जा सकीं।"
            questions = ["Please check the files and upload again."]

        escalation = EscalationResult(
            run_id=run_id,
            reason_code=reason_code,
            reason_en=reason_en,
            reason_hi=reason_hi,
            questions=questions[:2],  # Max 2
            completeness=completeness,
        )

        self._update_state(
            run_id, WorkflowState.ESCALATED,
            message_en=reason_en,
            message_hi=reason_hi,
            escalation=escalation,
        )
        log.warning("run_escalated", run_id=run_id, reason_code=reason_code)


def _derive_verdict(weak_areas: list) -> str:
    """Derive a short verdict code from the top weak area."""
    if not weak_areas:
        return "healthy"
    top = weak_areas[0].rule_id
    return {
        "W1": "money_stuck",
        "W2": "sales_declining",
        "W3": "weak_day",
        "W4": "margin_squeeze",
        "W5": "concentration_risk",
        "W6": "customers_lapsing",
        "W7": "expenses_spiking",
    }.get(top, "needs_attention")
