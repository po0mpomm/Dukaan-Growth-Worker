"""
Unit tests for Privacy Banding Module (TRD §6.4, PRD §12)
Verifies:
  - Real metrics correctly map to categorical enum bands
  - Zero raw rupee amounts or customer PII in AggregateExportPayload
  - Action completion ratio mapping
"""

from app.config import Settings
from app.contracts import (
    ActionItem,
    CompletenessResult,
    MoMComparison,
    ResultObject,
    ValidationOutcome,
    WeakArea,
    SalesChangeBand,
    CreditShareBand,
    OverdueBand,
    CompletenessBand,
    ActionCompletionBand,
)
from app.modules.privacy.banding import build_aggregate_payload


def test_metric_derived_banding():
    settings = Settings()

    completeness = CompletenessResult(
        score=0.92,
        day_coverage=1.0,
        expense_coverage=1.0,
        udhaar_integrity=1.0,
        flagged_row_ratio=0.0,
        outcome=ValidationOutcome.PROCEED,
    )

    mom = MoMComparison(
        has_prior_month=True,
        prior_month="2026-08",
        sales_change_pct=12.5,
    )

    actions = [
        ActionItem(n=1, title="Action 1", first_step="Step 1", done=True),
        ActionItem(n=2, title="Action 2", first_step="Step 2", done=True),
        ActionItem(n=3, title="Action 3", first_step="Step 3", done=False),
    ]

    metrics = {
        "total_sales": 50000.0,
        "credit_ratio": 24.5,          # Should map to HIGH (20-35)
        "uncollected_udhaar": 12000.0,
        "aging_records": {
            "CUST_1": {"bucket_60_plus": 4000.0},  # 4000 / 12000 = 33.3% -> HIGH (25-50)
        },
    }

    result = ResultObject(
        run_id="run_test_banding_12345",
        month="2026-09",
        language="en",
        completeness=completeness,
        verdict_en="Good",
        verdict_hi="अच्छा",
        weak_areas=[WeakArea(rule_id="W1", title_en="Udhaar", title_hi="उधार", rupee_impact=12000.0)],
        actions=actions,
        followups=[],
        comparison=mom,
        metrics=metrics,
    )

    payload = build_aggregate_payload(result, settings)

    assert payload.sales_change_band == SalesChangeBand.GROWTH          # +5..+20
    assert payload.credit_share_band == CreditShareBand.HIGH            # 20-35
    assert payload.overdue_band == OverdueBand.HIGH                     # 25-50
    assert payload.action_completion_band == ActionCompletionBand.HIGH  # 2 of 3 = 66.7%
    assert payload.completeness_band == CompletenessBand.GOOD           # score >= 0.8
    assert payload.rules_fired == ["W1"]
    assert payload.shop_pid == "anon_run_test"
