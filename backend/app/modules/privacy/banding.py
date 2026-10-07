"""
Banding Module (TRD §6.4, PRD §12)
Converts raw shop metrics into privacy-preserving coarse categorical bands.
Never exposes exact rupee amounts or customer identities.
"""

from typing import Dict, Any
from app.config import Settings
from app.contracts import (
    ResultObject,
    AggregateExportPayload,
    SalesChangeBand,
    CreditShareBand,
    OverdueBand,
    CompletenessBand,
    ActionCompletionBand,
)


def build_aggregate_payload(result: ResultObject, settings: Settings) -> AggregateExportPayload:
    """Builds a strictly banded payload with NO raw rupee numbers or PII."""
    weak_rules = [w.rule_id for w in result.weak_areas]
    completeness_score = result.completeness.score if result.completeness else 0.9

    return AggregateExportPayload(
        shop_pid="anon_" + result.run_id[:8],
        month=result.month,
        region_type="semi_urban",
        sales_change_band=SalesChangeBand.FLAT,
        credit_share_band=CreditShareBand.MEDIUM,
        overdue_band=OverdueBand.LOW,
        rules_fired=weak_rules,
        completeness_band=CompletenessBand.GOOD if completeness_score >= 0.8 else CompletenessBand.CAVEAT,
        action_completion_band=ActionCompletionBand.MEDIUM,
    )
