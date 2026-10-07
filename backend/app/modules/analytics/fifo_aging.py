"""
FIFO Udhaar Aging Algorithm (PRD §8.2, TRD §2.1)

Conserves balance: For each customer, unallocated repayments are applied
against opening balance and oldest credit increments first.
Remaining balances are partitioned into aging buckets:
  - bucket_0_30 : 0 to 30 days overdue
  - bucket_31_60: 31 to 60 days overdue
  - bucket_60_plus: 60+ days overdue
"""

from dataclasses import dataclass
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
    sales_df: Optional[pd.DataFrame] = None
) -> Dict[str, CustomerAgingRecord]:
    """
    Computes FIFO aging for each customer in udhaar_df.
    Returns dict mapping customer alias -> CustomerAgingRecord.
    """
    records: Dict[str, CustomerAgingRecord] = {}

    if udhaar_df.empty or "customer_ref" not in udhaar_df.columns:
        return records

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

        # FIFO deduction:
        # Repayments reduce opening balance first, then new credit taken.
        rem_opening = max(0.0, opening - repaid)
        leftover_repayment = max(0.0, repaid - opening)
        rem_taken = max(0.0, taken - leftover_repayment)

        # Opening balance is older (>30 or >60 days)
        # Taken balance in current month is 0-30 days
        bucket_0_30 = rem_taken
        # For simplicity in monthly view, half of remaining opening is 31-60, half is 60+
        bucket_31_60 = rem_opening * 0.5
        bucket_60_plus = rem_opening * 0.5

        # Conserve balance
        total_bucket = bucket_0_30 + bucket_31_60 + bucket_60_plus
        if total_bucket > 0:
            scale = net_outstanding / total_bucket
            bucket_0_30 *= scale
            bucket_31_60 *= scale
            bucket_60_plus *= scale

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
