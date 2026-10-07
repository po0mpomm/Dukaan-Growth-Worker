"""
G9 Escalation Guardrail (TRD §10)
Triggers safe escalation when data completeness is insufficient (<0.60 score)
or out-of-scope domain input is encountered.
"""

from app.contracts import CompletenessResult, ValidationOutcome


def should_escalate(completeness: CompletenessResult) -> bool:
    """Returns True if completeness score or failed checks require escalation."""
    return completeness.outcome == ValidationOutcome.ESCALATE
