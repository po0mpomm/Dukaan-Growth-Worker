"""
Unit tests for Month-on-Month Comparison & Persistence (PRD §8.2, TRD §7.1)
"""

import tempfile
from pathlib import Path
from app.contracts import (
    ActionItem,
    CompletenessResult,
    ResultObject,
    ValidationOutcome,
    WeakArea,
)
from app.modules.analytics.mom import compute_mom, save_snapshot


def test_mom_persistence_and_delta_computation():
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)

        completeness = CompletenessResult(
            score=0.9,
            day_coverage=1.0,
            expense_coverage=1.0,
            udhaar_integrity=1.0,
            flagged_row_ratio=0.0,
            outcome=ValidationOutcome.PROCEED,
        )

        # 1. Month 1 (August 2026): sales = 40,000, credit_ratio = 20.0
        result_aug = ResultObject(
            run_id="run_aug_001",
            month="2026-08",
            language="en",
            completeness=completeness,
            verdict_en="Steady",
            verdict_hi="स्थिर",
            weak_areas=[WeakArea(rule_id="W1", title_en="Udhaar", title_hi="उधार", rupee_impact=8000.0)],
            actions=[ActionItem(n=1, title="A1", first_step="S1", done=True)],
            metrics={
                "total_sales": 40000.0,
                "credit_ratio": 20.0,
                "uncollected_udhaar": 8000.0,
                "stock_expenses": 25000.0,
            },
        )
        save_snapshot(result_aug, data_dir)

        # 2. Month 2 (September 2026): sales = 50,000 (+25% growth), credit_ratio = 16.0 (-4.0% drop)
        sept_metrics = {
            "total_sales": 50000.0,
            "credit_ratio": 16.0,
            "uncollected_udhaar": 8000.0,
            "weak_areas": [],
        }

        mom = compute_mom(sept_metrics, "2026-09", data_dir)

        assert mom.has_prior_month is True
        assert mom.prior_month == "2026-08"
        assert mom.sales_change_pct == 25.0              # (50000 - 40000) / 40000 * 100
        assert mom.credit_share_change_pct == -4.0       # 16.0 - 20.0
        assert mom.overdue_change_pct == 0.0             # (8000 - 8000) / 8000 * 100
        assert "W1" in mom.rules_resolved                # W1 was in Aug, resolved in Sept!
