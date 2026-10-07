"""
G2 & G3 Prompt Guardrails (TRD §10)
G2: PII Scanner — blocks any text containing Indian phone numbers, PAN, or Aadhaar.
G3: Prompt Injection Barrier — strips delimiter attempts.
"""

import re
from typing import Tuple

# Regex patterns for Indian PII
PHONE_REGEX = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{9}\b")
PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
AADHAAR_REGEX = re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b")


def scan_for_pii(text: str) -> Tuple[bool, str]:
    """Returns (has_pii, pii_type) if PII is detected."""
    if PHONE_REGEX.search(text):
        return True, "PHONE_NUMBER"
    if PAN_REGEX.search(text):
        return True, "PAN_CARD"
    if AADHAAR_REGEX.search(text):
        return True, "AADHAAR_NUMBER"
    return False, ""


def sanitize_prompt_delimiters(text: str) -> str:
    """Neutralizes injection attempts (e.g. system override tags)."""
    text = re.sub(r"```.*system.*```", "", text, flags=re.IGNORECASE)
    text = text.replace("<|im_start|>", "").replace("<|im_end|>", "")
    return text
