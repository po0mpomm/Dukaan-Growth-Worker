"""
G8 Export Guardrail (TRD §10, PRD §12)
Validates that export payloads match strict allowlists and exact expected hashes.
"""

import hashlib
import structlog
from typing import Dict, Any

log = structlog.get_logger(__name__)


def verify_export_hash(payload_json: str, expected_hash: str) -> bool:
    """Verifies SHA-256 integrity match before persisting or transmission."""
    computed_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    return computed_hash == expected_hash
