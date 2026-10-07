"""
Audit hash chain verifier (TRD §6.1, §11)
"""

from pathlib import Path
from typing import Dict, Any
from app.modules.audit.logger import get_audit_logger


def verify_chain(data_dir: Path) -> Dict[str, Any]:
    """Recomputes hash chain and returns report."""
    logger = get_audit_logger(data_dir)
    res = logger.verify_integrity()
    return {
        "valid": res.get("valid", False),
        "event_count": res.get("count", 0),
        "head_hash": res.get("head_hash", "0" * 64),
        "tampered_at_seq": res.get("tampered_at_seq"),
        "error": res.get("error")
    }
