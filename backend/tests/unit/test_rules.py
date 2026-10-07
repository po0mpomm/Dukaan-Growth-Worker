"""
Unit tests for W1–W7 Rules Engine (PRD §8.3)
"""

from app.config import Settings
from app.modules.analytics.rules import detect_weak_areas


def test_rules_trigger_high_udhaar():
    settings = Settings()
    metrics = {
        "total_sales": 50000.0,
        "uncollected_udhaar": 25000.0,
        "credit_ratio": 50.0,
        "total_expenses": 5000.0,
        "expense_ratio": 10.0,
        "slump_drop_pct": 5.0,
        "top3_concentration_pct": 60.0,
        "unique_customers": 25,
    }

    weak_areas = detect_weak_areas(metrics, settings)
    rule_ids = [w.rule_id for w in weak_areas]

    assert "W1" in rule_ids
    assert "W7" in rule_ids
    assert weak_areas[0].rank == 1
    assert weak_areas[0].rupee_impact >= weak_areas[1].rupee_impact
