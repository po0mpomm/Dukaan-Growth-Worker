"""
G1 Input Sanitizer (TRD §10, PRD §8.1)
Neutralizes CSV/Excel formula injection and normalizes heterogeneous values.
"""

import re
from typing import Any, Optional


def sanitize_string(val: Any) -> str:
    """Escapes formula characters (=, +, -, @) to prevent formula execution."""
    if val is None:
        return ""
    s = str(val).strip()
    if s and s[0] in ("=", "+", "-", "@"):
        # Neutralize by prefixing with single quote
        return f"'{s}"
    return s


def normalize_payment_mode(mode_val: Any) -> str:
    """Normalizes colloquial and bilingual payment modes to standard enums."""
    if not mode_val:
        return "CASH"
    s = str(mode_val).strip().upper()
    
    # UPI matches
    if any(k in s for k in ("UPI", "GPAY", "PHONEPE", "PAYTM", "QR")):
        return "UPI"
    # Udhaar / Credit matches
    if any(k in s for k in ("UDHAAR", "UDHAR", "CREDIT", "BAAKI", "BAKI", "उधार", "बाकी")):
        return "UDHAAR"
    # Bank matches
    if any(k in s for k in ("BANK", "CHEQUE", "NEFT", "RTGS", "IMPS", "TRANSFER")):
        return "BANK"
    # Default Cash
    return "CASH"


def parse_float_safe(val: Any, default: float = 0.0) -> float:
    """Parses numeric amount safely, stripping rupee symbols, commas, spaces."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    # Remove currency symbols and formatting commas
    cleaned = re.sub(r"[₹$,\s]", "", s)
    try:
        return float(cleaned)
    except ValueError:
        return default
