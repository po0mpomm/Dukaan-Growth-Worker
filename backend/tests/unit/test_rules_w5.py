"""
Unit tests for W5 Supplier Margin Decay Rule & Heap-Based Ranking (PRD §8.3, DSA-1)
"""

from app.config import Settings
from app.modules.analytics.rules import detect_weak_areas


def test_w5_supplier_margin_decay_trigger():
    settings = Settings(min_gross_margin_pct=15.0)

    # Kirana with high sales but thin margin due to high stock expenses
    metrics = {
        "total_sales": 60000.0,
        "stock_expenses": 54000.0,      # Gross profit = 6,000 -> gross margin = 10% (< 15% threshold)
        "gross_margin_pct": 10.0,
        "total_expenses": 56000.0,
        "expense_ratio": 93.3,
        "uncollected_udhaar": 2000.0,   # Low udhaar -> W1 won't trigger
        "credit_ratio": 3.3,
        "unique_customers": 30,
        "slump_drop_pct": 5.0,
        "top3_concentration_pct": 20.0,
    }

    weak_areas = detect_weak_areas(metrics, settings)
    rule_ids = [w.rule_id for w in weak_areas]

    assert "W5" in rule_ids
    w5 = next(w for w in weak_areas if w.rule_id == "W5")
    assert w5.metrics["gross_margin_pct"] == 10.0
    assert "thin at 10.0%" in w5.evidence

    # Verify DSA-1: ranking is strictly monotonic by rupee_impact descending
    for i in range(len(weak_areas) - 1):
        assert weak_areas[i].rupee_impact >= weak_areas[i + 1].rupee_impact
        assert weak_areas[i].rank == i + 1
