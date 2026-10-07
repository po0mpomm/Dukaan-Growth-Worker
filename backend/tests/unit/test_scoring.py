"""
Unit tests for Customer Follow-up Priority Scorer (PRD §8.4)
"""

import pandas as pd
from app.modules.analytics.scoring import rank_followups
from app.modules.analytics.fifo_aging import CustomerAgingRecord
from app.modules.ingest.parser import ParsedData


def test_followup_ranking_bounds_and_sorting():
    aging_records = {
        "CUST_1": CustomerAgingRecord("CUST_1", 8000.0, 2000.0, 3000.0, 3000.0, 65),
        "CUST_2": CustomerAgingRecord("CUST_2", 1500.0, 1500.0, 0.0, 0.0, 15),
        "CUST_3": CustomerAgingRecord("CUST_3", 4500.0, 1000.0, 2500.0, 1000.0, 45),
    }

    metrics = {
        "aging_records": aging_records,
        "uncollected_udhaar": 14000.0,
    }

    parsed = ParsedData(
        sales=pd.DataFrame(),
        expenses=pd.DataFrame(),
        udhaar=pd.DataFrame(),
        month="2026-09",
        parse_errors=[],
    )

    followups = rank_followups(parsed, metrics)

    assert len(followups) == 3
    # Scores must be bounded within [0, 100]
    for f in followups:
        assert 0.0 <= f.score <= 100.0

    # Must be sorted descending by score
    assert followups[0].score >= followups[1].score >= followups[2].score
    assert followups[0].rank == 1
    assert followups[0].alias == "CUST_1"  # Oldest and largest debt
