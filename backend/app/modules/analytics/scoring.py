"""Follow-up priority scorer stub — Phase 2 full implementation."""
from app.contracts import FollowUp
from app.modules.ingest.parser import ParsedData


def rank_followups(parsed: ParsedData, metrics: dict) -> list[FollowUp]:
    """Rank customers for follow-up. Full implementation in Phase 2."""
    return []
