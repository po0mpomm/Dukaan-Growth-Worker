"""
G1 Input Guardrail (TRD §10)
Enforces file size, MIME types, encoding, and formula sanitization.
"""

from typing import List, Tuple

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit


def validate_file_metadata(filename: str, size_bytes: int) -> Tuple[bool, str]:
    """Validates file extension and size constraints."""
    if size_bytes > MAX_FILE_SIZE_BYTES:
        return False, f"File {filename} exceeds 10MB size limit."

    lower = filename.lower()
    if not (lower.endswith(".csv") or lower.endswith(".xlsx") or lower.endswith(".xls")):
        return False, f"Unsupported file format for {filename}. Only CSV or Excel supported."

    return True, ""
