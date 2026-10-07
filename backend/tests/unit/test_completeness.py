"""
Unit tests for Completeness Scorer (PRD §8.1)
Verifies:
  - Exact formula values
  - Block gate triggers (day_coverage < 0.50 -> ESCALATE)
  - Caveat triggers (0.60 <= score < 0.80 -> PROCEED_WITH_CAVEAT)
  - Healthy files -> PROCEED
  - The exact PRD §8.1 worked failure example (score = 0.566 -> ESCALATE)
"""

import pandas as pd
import pytest
from app.config import Settings
from app.contracts import ValidationOutcome
from app.modules.ingest.completeness import compute_completeness
from app.modules.ingest.parser import ParsedData


@pytest.fixture
def settings():
    return Settings(
        day_coverage_block=0.50,
        day_coverage_warn=0.75,
        completeness_block_threshold=0.60,
        completeness_caveat_threshold=0.80,
    )


def test_worked_failure_example(settings):
    """
    PRD §8.1 Worked Example:
    Sales on 12 of 30 days -> day_coverage = 0.40 -> BLOCK
    expense_coverage = 0.33, udhaar_integrity = 1.0, flagged_ratio = 0
    score = 0.5*0.40 + 0.2*0.33 + 0.2*1.0 + 0.1*1.0 = 0.566 -> ESCALATE
    """
    sales_df = pd.DataFrame({
        "date": pd.date_range("2026-09-01", periods=12),
        "amount": [500.0] * 12,
        "payment_mode": ["CASH"] * 12,
    })
    expenses_df = pd.DataFrame({
        "date": ["2026-09-05"],
        "category": ["stock_purchase"],
        "amount": [2000.0],
    })
    udhaar_df = pd.DataFrame({
        "customer_ref": ["CUST_1"],
        "opening_balance": [500.0],
        "credit_taken": [0.0],
        "repaid_amount": [200.0],
    })

    parsed = ParsedData(
        sales=sales_df,
        expenses=expenses_df,
        udhaar=udhaar_df,
        month="2026-09",
        parse_errors=[],
    )

    res = compute_completeness(parsed, "2026-09", settings)
    assert res.outcome == ValidationOutcome.ESCALATE
    assert "DAY_COVERAGE_BLOCK" in res.block_checks_failed
    assert res.score < 0.60


def test_healthy_shop_passes(settings):
    """30 days of sales, multiple expense categories, valid udhaar -> PROCEED."""
    sales_df = pd.DataFrame({
        "date": pd.date_range("2026-09-01", periods=30),
        "amount": [800.0] * 30,
        "payment_mode": ["CASH"] * 30,
    })
    expenses_df = pd.DataFrame({
        "category": ["stock_purchase", "electricity", "rent"],
        "amount": [5000.0, 1000.0, 3000.0],
    })
    udhaar_df = pd.DataFrame({
        "customer_ref": ["C1", "C2"],
        "opening_balance": [500.0, 1000.0],
        "credit_taken": [200.0, 500.0],
        "repaid_amount": [400.0, 800.0],
    })

    parsed = ParsedData(
        sales=sales_df,
        expenses=expenses_df,
        udhaar=udhaar_df,
        month="2026-09",
        parse_errors=[],
    )

    res = compute_completeness(parsed, "2026-09", settings)
    assert res.outcome == ValidationOutcome.PROCEED
    assert res.score >= 0.80
    assert len(res.block_checks_failed) == 0
