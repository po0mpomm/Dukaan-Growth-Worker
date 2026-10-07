"""
Unit tests for G2/G3 PII Scanning and Hash-Chained Audit Trail (TRD §10, §11)
"""

import tempfile
from pathlib import Path
from app.modules.guardrails.g2_g3_prompt import scan_for_pii
from app.modules.audit.logger import AuditLogger


def test_pii_detection():
    # Indian phone numbers
    has_pii, kind = scan_for_pii("Contact customer at 9876543210")
    assert has_pii is True
    assert kind == "PHONE_NUMBER"

    # PAN card
    has_pii, kind = scan_for_pii("Shop PAN is ABCDE1234F")
    assert has_pii is True
    assert kind == "PAN_CARD"

    # Aadhaar number
    has_pii, kind = scan_for_pii("ID is 1234 5678 9012")
    assert has_pii is True
    assert kind == "AADHAAR_NUMBER"

    # Clean text
    has_pii, _ = scan_for_pii("Customer alias CUST_10 owes 500 rupees")
    assert has_pii is False


def test_hash_chain_integrity_and_tamper_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "audit.db"
        logger = AuditLogger(db_path)

        # Log 3 events
        logger.log_event("STATE_TRANSITION", {"from": "S0", "to": "S1"})
        logger.log_event("VALIDATION_OK", {"score": 0.95})
        logger.log_event("SAVING", {"status": "done"})

        # Integrity check must pass
        res = logger.verify_integrity()
        assert res["valid"] is True
        assert res["count"] == 3

        # Tamper directly with the database row
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        conn.execute("UPDATE audit_events SET details_json = '{\"tampered\": true}' WHERE seq = 2")
        conn.commit()
        conn.close()

        # Integrity check must fail and catch tampering!
        tampered_res = logger.verify_integrity()
        assert tampered_res["valid"] is False
        assert tampered_res["tampered_at_seq"] == 2
