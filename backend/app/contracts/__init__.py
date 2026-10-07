"""
Pydantic contracts for all internal data structures.
These mirror the TypeScript types.ts in the frontend.

TRD §6.2 — FindingsObject: the ONLY thing the model ever sees.
TRD §6.3 — ModelOutput: strict JSON schema, exactly 3 actions.
TRD §6.4 — AggregateExportPayload: allow-listed fields only.
PRD §9    — WorkflowState: state machine states.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ── State Machine States (PRD §9) ─────────────────────────────────────────────

class WorkflowState(str, Enum):
    RECEIVED = "S0_RECEIVED"
    VALIDATING = "S1_VALIDATING"
    ANALYZING = "S2_ANALYZING"
    PHRASING = "S3_PHRASING"
    CHECKING = "S4_CHECKING"
    REVIEW = "S5_REVIEW"
    SAVING = "S6_SAVING"
    SHARING = "S7_SHARING"
    DONE = "S_DONE"
    ESCALATED = "S_ESCALATED"
    ERROR = "S_ERROR"


class ValidationOutcome(str, Enum):
    PROCEED = "PROCEED"
    PROCEED_WITH_CAVEAT = "PROCEED_WITH_CAVEAT"
    ESCALATE = "ESCALATE"


# ── Completeness Result (PRD §8.1) ───────────────────────────────────────────

class CompletenessResult(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    day_coverage: float = Field(ge=0.0, le=1.0)
    expense_coverage: float = Field(ge=0.0, le=1.0)
    udhaar_integrity: float = Field(ge=0.0, le=1.0)
    flagged_row_ratio: float = Field(ge=0.0, le=1.0)
    block_checks_failed: List[str] = Field(default_factory=list)
    warn_checks: List[str] = Field(default_factory=list)
    outcome: ValidationOutcome


# ── Weak Area (PRD §8.3, W1–W7) ──────────────────────────────────────────────

class WeakArea(BaseModel):
    rule_id: str                     # W1..W7
    title_en: str
    title_hi: str
    metrics: Dict[str, Any] = Field(default_factory=dict)  # Rule-specific metrics with rupee evidence
    rupee_impact: float = 0.0        # For ranking (0 = risk-only rule)
    rank: int = 1                    # 1 = highest impact
    title: Optional[str] = None
    evidence: Optional[str] = None
    recommended_action: Optional[str] = None


# ── Follow-Up Customer (PRD §8.4) ────────────────────────────────────────────

class FollowUp(BaseModel):
    rank: int = 1                    # 1 = highest priority
    alias: str                       # customer_ref, never a real name
    score: float = Field(default=50.0, ge=0.0, le=100.0)
    reason_code: str                 # e.g. LARGE_OVERDUE, LAPSED_REGULAR
    reason_en: str                   # Human readable one-liner
    reason_hi: str
    outstanding_amount: Optional[float] = None
    days_overdue: Optional[int] = None
    is_lapsed_regular: bool = False


# ── Action Item (PRD §11) ─────────────────────────────────────────────────────

class ActionItem(BaseModel):
    n: int = Field(default=1, ge=1, le=3)       # 1, 2, or 3 — exactly 3 actions always
    action_id: Optional[str] = None
    title: str = Field(max_length=100)
    why: str = Field(default="", max_length=200)
    description: Optional[str] = None
    first_step: str = Field(max_length=150)
    language: Literal["en", "hi"] = "en"
    source: Literal["model", "template"] = "template"
    rule_id: str = "W1"
    done: bool = False
    rationale: Optional[str] = None
    estimated_impact: Optional[str] = None


# ── Model Output ─────────────────────────────────────────────────────────────

class ModelOutput(BaseModel):
    verdict: str
    actions: List[ActionItem]
    summary: Optional[str] = None


# ── Month-on-Month Comparison (PRD §8.2) ────────────────────────────────────

class MoMComparison(BaseModel):
    has_prior_month: bool = False
    prior_month: Optional[str] = None  # YYYY-MM
    sales_change_pct: Optional[float] = None
    credit_share_change_pct: Optional[float] = None
    overdue_change_pct: Optional[float] = None
    rules_resolved: List[str] = Field(default_factory=list)
    rules_new: List[str] = Field(default_factory=list)
    actions_completed: int = 0
    actions_total: int = 0


# ── Findings Object (TRD §6.2) ───────────────────────────────────────────────

class FindingsObject(BaseModel):
    schema_version: str = "findings/1.0"
    language: Literal["en", "hi"] = "en"
    month: str
    verdict: str
    weak_areas: List[WeakArea] = Field(default_factory=list)
    followups: List[FollowUp] = Field(default_factory=list)
    comparison: Optional[MoMComparison] = None

    @property
    def detected_weak_areas(self) -> List[WeakArea]:
        return self.weak_areas


# ── Full Result Object (PRD §11) ──────────────────────────────────────────────

class ResultObject(BaseModel):
    run_id: str
    month: str
    language: Literal["en", "hi"] = "en"
    completeness: CompletenessResult
    verdict_en: str
    verdict_hi: str
    weak_areas: List[WeakArea] = Field(default_factory=list)
    actions: List[ActionItem] = Field(default_factory=list)
    followups: List[FollowUp] = Field(default_factory=list)
    comparison: Optional[MoMComparison] = None
    has_caveat: bool = False
    caveat_en: Optional[str] = None
    caveat_hi: Optional[str] = None
    model_used: bool = False
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metrics: Optional[Dict[str, Any]] = None

    @property
    def completeness_score(self) -> float:
        return self.completeness.score


# ── Escalation Output (PRD §9, PRD §17) ──────────────────────────────────────

class EscalationResult(BaseModel):
    run_id: str
    reason_code: str
    reason_en: str
    reason_hi: str
    questions: List[str] = Field(default_factory=list)
    completeness: Optional[CompletenessResult] = None


# ── Run Status (for frontend polling) ────────────────────────────────────────

class RunStatus(BaseModel):
    run_id: str
    state: WorkflowState
    progress_pct: int = Field(ge=0, le=100)
    message_en: str = ""
    message_hi: str = ""
    result: Optional[ResultObject] = None
    escalation: Optional[EscalationResult] = None
    error_message: Optional[str] = None


# ── Aggregate Export Payload (TRD §6.4) ──────────────────────────────────────

class SalesChangeBand(str, Enum):
    LARGE_DECLINE = "<-20"
    DECLINE = "-20..-5"
    FLAT = "-5..+5"
    GROWTH = "+5..+20"
    LARGE_GROWTH = ">+20"

class CreditShareBand(str, Enum):
    LOW = "0-10"
    MEDIUM = "10-20"
    HIGH = "20-35"
    VERY_HIGH = "35-50"
    EXTREME = ">50"

class OverdueBand(str, Enum):
    LOW = "0-10"
    MEDIUM = "10-25"
    HIGH = "25-50"
    CRITICAL = ">50"

class CompletenessBand(str, Enum):
    CAVEAT = "0.6-0.8"
    GOOD = "0.8-1.0"

class ActionCompletionBand(str, Enum):
    LOW = "0-33"
    MEDIUM = "33-66"
    HIGH = "66-100"

class AggregateExportPayload(BaseModel):
    schema_version: str = "aggregate/1.0"
    shop_pid: str
    month: str
    region_type: Literal["urban", "semi_urban", "rural", "deep_rural"] = "semi_urban"
    sales_change_band: SalesChangeBand = SalesChangeBand.FLAT
    credit_share_band: CreditShareBand = CreditShareBand.MEDIUM
    overdue_band: OverdueBand = OverdueBand.LOW
    rules_fired: List[str] = Field(default_factory=list)
    completeness_band: CompletenessBand = CompletenessBand.GOOD
    action_completion_band: ActionCompletionBand = ActionCompletionBand.MEDIUM

    model_config = {"extra": "ignore"}


# ── Audit Event (PRD §13, TRD §7.1) ─────────────────────────────────────────

class AuditEvent(BaseModel):
    seq: Optional[int] = None
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=lambda: datetime.utcnow().timestamp())
    event_type: str = "GENERIC"
    run_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    prev_hash: str = ""
    entry_hash: str = ""
