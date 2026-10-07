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
    """
    Builds a strictly banded payload with NO raw rupee numbers or PII.
    Derives categorical bands deterministically from computed shop metrics.
    """
    weak_rules = [w.rule_id for w in result.weak_areas]
    completeness_score = result.completeness.score if result.completeness else 1.0
    metrics = result.metrics or {}

    # 1. Sales Change Band (derived from MoM comparison)
    if result.comparison and result.comparison.has_prior_month and result.comparison.sales_change_pct is not None:
        chg = result.comparison.sales_change_pct
        if chg < -20.0:
            sales_band = SalesChangeBand.LARGE_DECLINE
        elif chg < -5.0:
            sales_band = SalesChangeBand.DECLINE
        elif chg <= 5.0:
            sales_band = SalesChangeBand.FLAT
        elif chg <= 20.0:
            sales_band = SalesChangeBand.GROWTH
        else:
            sales_band = SalesChangeBand.LARGE_GROWTH
    else:
        sales_band = SalesChangeBand.FLAT

    # 2. Credit Share Band (derived from credit_ratio: uncollected / sales * 100)
    credit_ratio = float(metrics.get("credit_ratio", 0.0))
    if credit_ratio < 10.0:
        credit_band = CreditShareBand.LOW
    elif credit_ratio < 20.0:
        credit_band = CreditShareBand.MEDIUM
    elif credit_ratio < 35.0:
        credit_band = CreditShareBand.HIGH
    elif credit_ratio <= 50.0:
        credit_band = CreditShareBand.VERY_HIGH
    else:
        credit_band = CreditShareBand.EXTREME

    # 3. Overdue Band (ratio of 60+ day aging overdue to total uncollected udhaar)
    uncollected = float(metrics.get("uncollected_udhaar", 0.0))
    aging_records = metrics.get("aging_records", {})
    overdue_pct = 0.0
    if uncollected > 0 and isinstance(aging_records, dict):
        bucket_60_sum = 0.0
        for rec in aging_records.values():
            if isinstance(rec, dict):
                bucket_60_sum += float(rec.get("bucket_60_plus", 0.0))
            elif hasattr(rec, "bucket_60_plus"):
                bucket_60_sum += float(rec.bucket_60_plus)
        overdue_pct = (bucket_60_sum / uncollected) * 100.0

    if overdue_pct < 10.0:
        overdue_band = OverdueBand.LOW
    elif overdue_pct < 25.0:
        overdue_band = OverdueBand.MEDIUM
    elif overdue_pct < 50.0:
        overdue_band = OverdueBand.HIGH
    else:
        overdue_band = OverdueBand.CRITICAL

    # 4. Action Completion Band
    actions = result.actions
    done_count = sum(1 for a in actions if a.done)
    total_actions = len(actions) or 3
    completion_pct = (done_count / total_actions) * 100.0
    if completion_pct < 33.3:
        action_band = ActionCompletionBand.LOW
    elif completion_pct < 66.6:
        action_band = ActionCompletionBand.MEDIUM
    else:
        action_band = ActionCompletionBand.HIGH

    # 5. Completeness Band
    comp_band = CompletenessBand.GOOD if completeness_score >= 0.8 else CompletenessBand.CAVEAT

    return AggregateExportPayload(
        shop_pid="anon_" + result.run_id[:8],
        month=result.month,
        region_type="semi_urban",
        sales_change_band=sales_band,
        credit_share_band=credit_band,
        overdue_band=overdue_band,
        rules_fired=weak_rules,
        completeness_band=comp_band,
        action_completion_band=action_band,
    )
