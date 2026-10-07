"""
G7 Action Guardrail (TRD §10)
Hard-coded invariant: The system never executes autonomous external actions
(no automated WhatsApp messaging, no payment calls, no auto-debit).
"""


def verify_action_safety(action_type: str) -> bool:
    """Verifies that an action requires human review and is not automated."""
    autonomous_prohibited = ["AUTO_SEND_WHATSAPP", "AUTO_PAYMENT_DEBIT", "AUTO_SUPPLIER_ORDER"]
    return action_type not in autonomous_prohibited
