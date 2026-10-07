"""
Unit tests for G5 Factuality Guardrail (TRD §10)
Planted hallucinated numbers in model output must be detected
and trigger deterministic fallback to template phrasing.
"""

from app.contracts import ActionItem, FindingsObject, WeakArea
from app.modules.guardrails.g5_factuality import verify_factuality


def test_g5_passes_verified_numbers():
    findings = FindingsObject(
        language="en",
        month="2026-09",
        verdict="money_stuck",
        weak_areas=[
            WeakArea(
                rule_id="W1",
                title_en="Udhaar Lockup",
                title_hi="उधार",
                metrics={"uncollected_udhaar": 15000.0},
                rupee_impact=15000.0,
                evidence="₹15,000 locked in udhaar.",
                rank=1,
            )
        ],
        followups=[],
    )

    # Action uses only verified numbers (1, 15000, 2%)
    actions = [
        ActionItem(
            n=1,
            title="Collect Udhaar",
            description="Recover the ₹15,000 pending from customers.",
            first_step="Offer 2% spot discount.",
            language="en",
            source="model",
            rule_id="W1",
        )
    ]

    checked_actions, source = verify_factuality(actions, findings, "model")
    assert source == "model"


def test_g5_catches_hallucinated_number_and_falls_back():
    findings = FindingsObject(
        language="en",
        month="2026-09",
        verdict="money_stuck",
        weak_areas=[
            WeakArea(
                rule_id="W1",
                title_en="Udhaar Lockup",
                title_hi="उधार",
                metrics={"uncollected_udhaar": 15000.0},
                rupee_impact=15000.0,
                evidence="₹15,000 locked in udhaar.",
                rank=1,
            )
        ],
        followups=[],
    )

    # Model hallucinates a number NOT in findings: ₹89,450
    actions = [
        ActionItem(
            n=1,
            title="Phantom Claim",
            description="You will lose ₹89,450 if you don't act now!",
            first_step="Panic.",
            language="en",
            source="model",
            rule_id="W1",
        )
    ]

    checked_actions, source = verify_factuality(actions, findings, "model")
    # Must reject model output and fall back to template!
    assert source == "template"
