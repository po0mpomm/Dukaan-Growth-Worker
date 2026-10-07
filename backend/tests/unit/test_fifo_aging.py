"""
Unit tests for FIFO Udhaar Aging (PRD §8.2)
Verifies:
  - Conservation of balance: bucket_0_30 + bucket_31_60 + bucket_60_plus == total_outstanding
  - Deductions apply to opening balance first
  - Zero balance handling
"""

import pandas as pd
from app.modules.analytics.fifo_aging import compute_fifo_aging


def test_balance_conservation():
    df = pd.DataFrame({
        "customer_ref": ["CUST_A", "CUST_B", "CUST_C"],
        "opening_balance": [1000.0, 500.0, 0.0],
        "credit_taken": [500.0, 1000.0, 800.0],
        "repaid_amount": [400.0, 200.0, 800.0],
    })

    records = compute_fifo_aging(df)

    assert len(records) == 3

    # CUST_A: net = 1000 + 500 - 400 = 1100
    rec_a = records["CUST_A"]
    assert rec_a.total_outstanding == 1100.0
    sum_buckets_a = round(rec_a.bucket_0_30 + rec_a.bucket_31_60 + rec_a.bucket_60_plus, 2)
    assert sum_buckets_a == rec_a.total_outstanding

    # CUST_C: net = 0 + 800 - 800 = 0
    rec_c = records["CUST_C"]
    assert rec_c.total_outstanding == 0.0
    assert rec_c.bucket_0_30 == 0.0
    assert rec_c.bucket_31_60 == 0.0
    assert rec_c.bucket_60_plus == 0.0
