"""
Template Phrasing Adapter (Deterministic, Offline-first, Zero-token)
PRD §10, TRD §2.1
"""

import structlog
from typing import Dict, Any, List
from app.contracts import FindingsObject, ModelOutput, ActionItem, WeakArea
from app.modules.llm_adapter.base import PhrasingAdapter
from app.modules.llm_adapter.templates import TEMPLATES_EN, TEMPLATES_HI

log = structlog.get_logger(__name__)


class TemplatePhrasingAdapter(PhrasingAdapter):
    """Deterministic rule-template adapter. 100% reliable, zero token cost."""

    async def is_available(self) -> bool:
        return True

    def phrase_sync(
        self,
        findings: FindingsObject,
        language: str = "en"
    ) -> ModelOutput:
        templates = TEMPLATES_HI if language == "hi" else TEMPLATES_EN
        
        # Build 3 actionable items from detected weak areas
        actions: List[ActionItem] = []
        weak_areas: List[WeakArea] = findings.detected_weak_areas

        for idx, wa in enumerate(weak_areas[:3]):
            tmpl = templates.get(wa.rule_id, templates.get("W1"))
            action_text = wa.recommended_action or (tmpl["action"] if tmpl else "Review operations.")
            first_step = tmpl["first_step"] if tmpl else "Check ledger records."
            
            actions.append(
                ActionItem(
                    n=idx + 1,
                    action_id=f"act_{idx+1}",
                    title=tmpl["title"] if tmpl else (wa.title or "Action Item"),
                    description=action_text,
                    first_step=first_step,
                    rationale=wa.evidence or "Derived from monthly business activity review.",
                    estimated_impact="Improves operating cash flow and working capital efficiency.",
                    language="hi" if language == "hi" else "en",
                    source="template",
                    rule_id=wa.rule_id,
                )
            )

        # Pad to exactly 3 if fewer detected
        defaults = ["W1", "W2", "W3"]
        d_idx = 0
        while len(actions) < 3:
            rule_id = defaults[d_idx % len(defaults)]
            tmpl = templates[rule_id]
            actions.append(
                ActionItem(
                    n=len(actions) + 1,
                    action_id=f"act_{len(actions)+1}",
                    title=tmpl["title"],
                    description=tmpl["action"],
                    first_step=tmpl["first_step"],
                    rationale="Standard retail optimization guideline for steady monthly growth.",
                    estimated_impact="Consistent business health discipline.",
                    language="hi" if language == "hi" else "en",
                    source="template",
                    rule_id=rule_id,
                )
            )
            d_idx += 1

        verdict = (
            "Dukaan health is stable this month with clear cash recovery opportunities."
            if language == "en" else
            "इस महीने दुकान की स्थिति संतुलित है और नकद वसूली के अच्छे अवसर हैं।"
        )

        return ModelOutput(
            verdict=verdict,
            actions=actions,
            summary=(
                f"Generated {len(actions)} high-priority action items for monthly growth."
            )
        )

    async def phrase_findings(
        self,
        findings: FindingsObject,
        language: str = "en"
    ) -> ModelOutput:
        return self.phrase_sync(findings, language)
