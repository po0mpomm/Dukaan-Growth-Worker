"""
Unit tests for G1 Input Sanitizer & File Constraints (TRD §10)
"""

from app.modules.ingest.sanitizer import sanitize_string, normalize_payment_mode
from app.modules.guardrails.g1_input import validate_file_metadata


def test_formula_injection_neutralization():
    assert sanitize_string("=SUM(A1:A10)") == "'=SUM(A1:A10)"
    assert sanitize_string("@cmd|' /C calc'!A0") == "'@cmd|' /C calc'!A0"
    assert sanitize_string("+1+2") == "'+1+2"
    assert sanitize_string("-500") == "'-500"
    assert sanitize_string("CUST_NORMAL") == "CUST_NORMAL"


def test_payment_mode_normalization():
    assert normalize_payment_mode("nagad") == "CASH"
    assert normalize_payment_mode("phonepe") == "UPI"
    assert normalize_payment_mode("उधार") == "UDHAAR"
    assert normalize_payment_mode("cheque") == "BANK"


def test_file_metadata_validation():
    ok, _ = validate_file_metadata("sales.csv", 1024)
    assert ok is True

    bad_ext, err = validate_file_metadata("malicious.exe", 1024)
    assert bad_ext is False
    assert "Unsupported" in err

    oversized, err2 = validate_file_metadata("big.csv", 15 * 1024 * 1024)
    assert oversized is False
    assert "exceeds" in err2
