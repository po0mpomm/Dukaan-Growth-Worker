"""
Completeness Scorer — PRD §8.1

Formula:
  score = 0.5 * day_coverage
        + 0.2 * expense_coverage
        + 0.2 * udhaar_integrity
        + 0.1 * (1 - flagged_row_ratio)

Gate:
  score < 0.6 or any BLOCK → ESCALATE
  0.6 ≤ score < 0.8       → PROCEED_WITH_CAVEAT
  score ≥ 0.8             → PROCEED

Worked example (PRD §8.1):
  Sales on 12 of 30 days → day_coverage = 0.40 → BLOCK
  expense_coverage = 0.33, udhaar_integrity = 1.0, flagged_ratio = 0
  score = 0.5*0.40 + 0.2*0.33 + 0.2*1.0 + 0.1*1.0
        = 0.20 + 0.066 + 0.20 + 0.10 = 0.566 → ESCALATE
"""

import calendar
from collections import defaultdict
from datetime import date

from app.config import Settings
from app.contracts import CompletenessResult, ValidationOutcome
from app.modules.ingest.parser import ParsedData


def compute_completeness(parsed: ParsedData, month: str, settings: Settings) -> CompletenessResult:
    """
    Compute completeness score from parsed DataFrames.
    Returns a CompletenessResult with outcome: PROCEED, CAVEAT, or ESCALATE.
    """
    block_checks_failed = []
    warn_checks = []

    # ── Handle parse errors / missing files early (DSA-7: short-circuit) ───────
    if parsed.parse_errors:
        for err in parsed.parse_errors:
            if "FILE_PARSE_ERROR" in err:
                block_checks_failed.append("FILE_MISSING")

    # If critical files completely failed parsing, return early with ESCALATE
    if "FILE_MISSING" in block_checks_failed:
        return CompletenessResult(
            score=0.0,
            day_coverage=0.0,
            expense_coverage=0.0,
            udhaar_integrity=0.0,
            flagged_row_ratio=1.0,
            block_checks_failed=block_checks_failed,
            warn_checks=warn_checks,
            outcome=ValidationOutcome.ESCALATE,
        )

    # ── Parse year and month ──────────────────────────────────────────────────
    try:
        year, mon = int(month[:4]), int(month[5:7])
        days_in_month = calendar.monthrange(year, mon)[1]
    except (ValueError, IndexError):
        block_checks_failed.append("INVALID_MONTH_FORMAT")
        days_in_month = 30

    # ── Day coverage (PRD §8.1) ───────────────────────────────────────────────
    day_coverage = 0.0
    if not parsed.sales.empty and "date" in parsed.sales.columns:
        try:
            unique_days = parsed.sales["date"].nunique()
            day_coverage = unique_days / days_in_month
        except Exception:
            day_coverage = 0.0
    elif parsed.sales.empty:
        day_coverage = 0.0

    if day_coverage < settings.day_coverage_block:
        block_checks_failed.append("DAY_COVERAGE_BLOCK")
    elif day_coverage < settings.day_coverage_warn:
        warn_checks.append("DAY_COVERAGE_WARN")

    # ── Expense coverage: stock_purchase, rent, electricity ───────────────────
    expense_coverage = 0.0
    expected_expense_categories = {"stock_purchase", "rent", "electricity"}
    if not parsed.expenses.empty and "category" in parsed.expenses.columns:
        present = set(parsed.expenses["category"].str.lower().unique())
        matched = expected_expense_categories.intersection(present)
        expense_coverage = len(matched) / len(expected_expense_categories)
    elif not parsed.expenses.empty:
        expense_coverage = 0.5   # File present but no category column — partial credit

    # ── Udhaar integrity: no customer with negative net balance ──────────────
    udhaar_integrity = 1.0
    if not parsed.udhaar.empty and "customer_ref" in parsed.udhaar.columns:
        udhaar_integrity = _compute_udhaar_integrity(parsed)

    # ── Flagged row ratio ─────────────────────────────────────────────────────
    total_rows = len(parsed.sales) + len(parsed.expenses) + len(parsed.udhaar)
    flagged_rows = 0  # Full check implemented in Phase 2
    flagged_row_ratio = flagged_rows / max(total_rows, 1)

    # ── Final score formula (PRD §8.1) ───────────────────────────────────────
    score = (
        0.5 * day_coverage
        + 0.2 * expense_coverage
        + 0.2 * udhaar_integrity
        + 0.1 * (1.0 - flagged_row_ratio)
    )
    score = round(score, 4)

    # ── Determine outcome ─────────────────────────────────────────────────────
    if block_checks_failed or score < settings.completeness_block_threshold:
        outcome = ValidationOutcome.ESCALATE
    elif score < settings.completeness_caveat_threshold:
        outcome = ValidationOutcome.PROCEED_WITH_CAVEAT
    else:
        outcome = ValidationOutcome.PROCEED

    return CompletenessResult(
        score=score,
        day_coverage=round(day_coverage, 4),
        expense_coverage=round(expense_coverage, 4),
        udhaar_integrity=round(udhaar_integrity, 4),
        flagged_row_ratio=round(flagged_row_ratio, 4),
        block_checks_failed=block_checks_failed,
        warn_checks=warn_checks,
        outcome=outcome,
    )


def _compute_udhaar_integrity(parsed: ParsedData) -> float:
    """
    Udhaar integrity = 1 - (customers_with_negative_balance / total_active_customers)
    A customer has a negative balance if payments exceed credit + opening balance.
    O(N) single-pass dictionary aggregation (DSA optimal).
    """
    try:
        df = parsed.udhaar
        if df.empty or "customer_ref" not in df.columns:
            return 1.0

        # Ledger summary format: opening_balance, credit_taken, repaid_amount
        if any(col in df.columns for col in ("opening_balance", "credit_taken", "repaid_amount")):
            negatives = 0
            total = 0
            for _, row in df.iterrows():
                alias = str(row.get("customer_ref", "")).strip()
                if not alias:
                    continue
                opening = float(row.get("opening_balance", 0.0) or 0.0)
                taken = float(row.get("credit_taken", 0.0) or 0.0)
                repaid = float(row.get("repaid_amount", 0.0) or 0.0)
                total += 1
                if (opening + taken) < repaid:
                    negatives += 1
            return 1.0 - (negatives / total) if total > 0 else 1.0

        # Transaction stream format: amount and type
        if "amount" in df.columns and "type" in df.columns:
            balances: defaultdict[str, float] = defaultdict(float)
            for _, row in df.iterrows():
                alias = str(row.get("customer_ref", "")).strip()
                if not alias:
                    continue
                amt = float(row.get("amount", 0.0) or 0.0)
                ctype = str(row.get("type", "")).lower()
                if ctype in ("opening_balance", "credit_given", "credit"):
                    balances[alias] += amt
                elif ctype in ("payment_received", "payment", "repayment"):
                    balances[alias] -= amt

            if not balances:
                return 1.0
            neg_count = sum(1 for bal in balances.values() if bal < 0)
            return 1.0 - (neg_count / len(balances))

        return 1.0
    except Exception:
        return 1.0
