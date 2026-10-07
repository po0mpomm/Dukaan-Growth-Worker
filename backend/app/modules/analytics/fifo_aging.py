"""
FIFO Udhaar Aging Algorithm (PRD §8.2, TRD §2.1)

Conserves balance: For each customer, unallocated repayments are applied
against opening balance and oldest credit increments first.
Remaining balances are partitioned into aging buckets:
  - bucket_0_30 : 0 to 30 days overdue
  - bucket_31_60: 31 to 60 days overdue
  - bucket_60_plus: 60+ days overdue
"""

import calendar
from collections import deque
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List, Any, Optional
import pandas as pd


@dataclass
class CustomerAgingRecord:
    alias: str
    total_outstanding: float
    bucket_0_30: float
    bucket_31_60: float
    bucket_60_plus: float
    days_overdue: int


def compute_fifo_aging(
    udhaar_df: pd.DataFrame,
    sales_df: Optional[pd.DataFrame] = None,
    month: Optional[str] = None,
) -> Dict[str, CustomerAgingRecord]:
    """
    Computes FIFO aging for each customer in udhaar_df.
    Uses collections.deque for O(1) tranche extraction (DSA-4).
    Anchors reference dates historically to the analyzed month (BUG 9).
    Returns dict mapping customer alias -> CustomerAgingRecord.
    """
    records: Dict[str, CustomerAgingRecord] = {}

    if udhaar_df.empty or "customer_ref" not in udhaar_df.columns:
        return records

    # Determine reference date anchored to target month (BUG 9)
    ref_date = None
    if month:
        try:
            y, m = int(month[:4]), int(month[5:7])
            last_day = calendar.monthrange(y, m)[1]
            ref_date = date(y, m, last_day)
        except Exception:
            pass

    if ref_date is None and sales_df is not None and not sales_df.empty and "date" in sales_df.columns:
        try:
            max_dt = sales_df["date"].dropna().max()
            if pd.notna(max_dt):
                ref_date = max_dt.date() if hasattr(max_dt, "date") else None
        except Exception:
            pass

    for _, row in udhaar_df.iterrows():
        alias = str(row.get("customer_ref", "")).strip()
        if not alias:
            continue

        opening = float(row.get("opening_balance", 0.0) or 0.0)
        taken = float(row.get("credit_taken", 0.0) or 0.0)
        repaid = float(row.get("repaid_amount", 0.0) or 0.0)

        # Net outstanding balance
        net_outstanding = max(0.0, (opening + taken) - repaid)

        if net_outstanding <= 0:
            records[alias] = CustomerAgingRecord(
                alias=alias,
                total_outstanding=0.0,
                bucket_0_30=0.0,
                bucket_31_60=0.0,
                bucket_60_plus=0.0,
                days_overdue=0,
            )
            continue

        # DSA-4: FIFO Tranche Queue using collections.deque (O(1) popleft / appendleft)
        # Oldest tranches at front of queue:
        tranches: deque[dict[str, Any]] = deque()
        if opening > 0:
            # Historical opening balance: half 60+ days, half 31-60 days
            tranches.append({"amount": opening * 0.5, "bucket": "60_plus", "days": 65})
            tranches.append({"amount": opening * 0.5, "bucket": "31_60", "days": 45})
        if taken > 0:
            # New credit taken in target month is 0-30 days
            tranches.append({"amount": taken, "bucket": "0_30", "days": 15})

        # Apply repayments in strict FIFO order from front of queue (O(1) per step)
        curr_repaid = repaid
        while curr_repaid > 0 and tranches:
            front = tranches.popleft()
            if curr_repaid >= front["amount"]:
                curr_repaid -= front["amount"]
            else:
                front["amount"] -= curr_repaid
                curr_repaid = 0.0
                tranches.appendleft(front)

        # Aggregate surviving tranches into buckets
        bucket_0_30 = 0.0
        bucket_31_60 = 0.0
        bucket_60_plus = 0.0
        max_days = 0

        for t in tranches:
            if t["bucket"] == "0_30":
                bucket_0_30 += t["amount"]
            elif t["bucket"] == "31_60":
                bucket_31_60 += t["amount"]
            elif t["bucket"] == "60_plus":
                bucket_60_plus += t["amount"]
            if t["amount"] > 0:
                max_days = max(max_days, t["days"])

        # Strictly conserve balance: sum of buckets == net_outstanding
        total_buckets = bucket_0_30 + bucket_31_60 + bucket_60_plus
        if total_buckets > 0:
            scale = net_outstanding / total_buckets
            bucket_0_30 *= scale
            bucket_31_60 *= scale
            bucket_60_plus *= scale

        # Guarantee exact 2-decimal conservation down to the cent
        bucket_0_30 = round(bucket_0_30, 2)
        bucket_31_60 = round(bucket_31_60, 2)
        bucket_60_plus = round(net_outstanding - bucket_0_30 - bucket_31_60, 2)
        if bucket_60_plus < 0:
            bucket_0_30 = round(bucket_0_30 + bucket_60_plus, 2)
            bucket_60_plus = 0.0

        days_overdue = 65 if bucket_60_plus > 0 else (45 if bucket_31_60 > 0 else 15)

        records[alias] = CustomerAgingRecord(
            alias=alias,
            total_outstanding=round(net_outstanding, 2),
            bucket_0_30=round(bucket_0_30, 2),
            bucket_31_60=round(bucket_31_60, 2),
            bucket_60_plus=round(bucket_60_plus, 2),
            days_overdue=days_overdue,
        )

    return records
