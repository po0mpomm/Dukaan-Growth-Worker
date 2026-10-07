"""
Customer Follow-up Priority Scorer (PRD §8.4, TRD §2.1)

Formula:
  score = 0.4 * overdue_factor
        + 0.3 * balance_weight
        + 0.2 * aging_severity
        + 0.1 * recency_weight

Bounds: [0.0, 100.0]
Ranks customers for targeted recovery without aggressive collection tactics.
"""

from typing import List, Dict, Any
from app.contracts import FollowUp
from app.modules.ingest.parser import ParsedData


def rank_followups(parsed: ParsedData, metrics: Dict[str, Any]) -> List[FollowUp]:
    """Ranks customers for polite owner follow-up."""
    aging_records = metrics.get("aging_records", {})
    uncollected_udhaar = metrics.get("uncollected_udhaar", 1.0) or 1.0

    candidates = []

    for alias, rec in aging_records.items():
        if rec.total_outstanding <= 0:
            continue

        # Overdue factor (0 to 40)
        overdue_factor = min(40.0, (rec.days_overdue / 60.0) * 40.0)

        # Balance share (0 to 30)
        share = rec.total_outstanding / uncollected_udhaar
        balance_weight = min(30.0, share * 100.0 * 0.3)

        # Aging severity (0 to 20): high proportion in 60+ bucket
        sev_ratio = (rec.bucket_60_plus / rec.total_outstanding) if rec.total_outstanding > 0 else 0
        aging_severity = sev_ratio * 20.0

        # Base recency weight
        recency = 10.0

        score = min(100.0, max(0.0, overdue_factor + balance_weight + aging_severity + recency))

        if rec.days_overdue >= 45:
            reason_code = "LARGE_OVERDUE"
            reason_en = f"₹{rec.total_outstanding:,.0f} balance pending for {rec.days_overdue} days."
            reason_hi = f"₹{rec.total_outstanding:,.0f} का बकाया {rec.days_overdue} दिनों से लंबित है।"
        elif share >= 0.15:
            reason_code = "HIGH_BALANCE"
            reason_en = f"High credit balance (₹{rec.total_outstanding:,.0f})."
            reason_hi = f"अधिक बकाया राशि (₹{rec.total_outstanding:,.0f})।"
        else:
            reason_code = "ROUTINE_CHECK"
            reason_en = f"Regular customer check-in (₹{rec.total_outstanding:,.0f} balance)."
            reason_hi = f"नियमित ग्राहक हिसाब मिलान (₹{rec.total_outstanding:,.0f} बकाया)।"

        candidates.append({
            "alias": alias,
            "score": round(score, 1),
            "reason_code": reason_code,
            "reason_en": reason_en,
            "reason_hi": reason_hi,
            "outstanding_amount": rec.total_outstanding,
            "days_overdue": rec.days_overdue,
            "is_lapsed_regular": rec.days_overdue >= 45,
        })

    # DSA-2: Priority queue top-K extraction with heap (heapq.nlargest)
    # O(N log K) time and O(K) space instead of O(N log N) full sorting
    import heapq
    top_candidates = heapq.nlargest(5, candidates, key=lambda c: c["score"])

    result: List[FollowUp] = []
    for idx, c in enumerate(top_candidates):
        result.append(
            FollowUp(
                rank=idx + 1,
                alias=c["alias"],
                score=c["score"],
                reason_code=c["reason_code"],
                reason_en=c["reason_en"],
                reason_hi=c["reason_hi"],
                outstanding_amount=c["outstanding_amount"],
                days_overdue=c["days_overdue"],
                is_lapsed_regular=c["is_lapsed_regular"],
            )
        )

    return result
