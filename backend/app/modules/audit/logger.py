"""
SHA-256 Hash-Chained Audit Logger (TRD §7.1, §11)
Maintains an immutable, append-only hash chain in audit.db.
Ensures explicit connection closing for Windows file lock compatibility.
"""

import hashlib
import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional
import structlog
from app.contracts import AuditEvent

log = structlog.get_logger(__name__)


class AuditLogger:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._ensure_table()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self) -> None:
        conn = self._get_connection()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    timestamp REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    run_id TEXT,
                    details_json TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    entry_hash TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def _get_last_hash(self) -> str:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT entry_hash FROM audit_events ORDER BY seq DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                return row["entry_hash"]
            return "0" * 64
        finally:
            conn.close()

    def log_event(self, event_type: str, details: Dict[str, Any], run_id: Optional[str] = None) -> AuditEvent:
        prev_hash = self._get_last_hash()
        ts = time.time()
        event_id = str(uuid.uuid4())
        details_str = json.dumps(details, sort_keys=True)

        payload_to_hash = f"{event_id}|{ts}|{event_type}|{run_id or ''}|{details_str}|{prev_hash}"
        entry_hash = hashlib.sha256(payload_to_hash.encode("utf-8")).hexdigest()

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_events (event_id, timestamp, event_type, run_id, details_json, prev_hash, entry_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (event_id, ts, event_type, run_id, details_str, prev_hash, entry_hash)
            )
            seq = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()

        event = AuditEvent(
            seq=seq,
            event_id=event_id,
            timestamp=ts,
            event_type=event_type,
            run_id=run_id,
            details=details,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
        )
        return event

    def verify_integrity(self) -> Dict[str, Any]:
        """Recomputes entire hash chain to verify zero tampering."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_events ORDER BY seq ASC")
            rows = cursor.fetchall()
        finally:
            conn.close()

        if not rows:
            return {"valid": True, "count": 0, "message": "Audit chain empty."}

        expected_prev = "0" * 64
        for row in rows:
            if row["prev_hash"] != expected_prev:
                return {
                    "valid": False,
                    "tampered_at_seq": row["seq"],
                    "error": f"Prev hash mismatch at seq {row['seq']}"
                }
            payload = f"{row['event_id']}|{row['timestamp']}|{row['event_type']}|{row['run_id'] or ''}|{row['details_json']}|{row['prev_hash']}"
            computed_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            if computed_hash != row["entry_hash"]:
                return {
                    "valid": False,
                    "tampered_at_seq": row["seq"],
                    "error": f"Entry hash mismatch at seq {row['seq']}"
                }
            expected_prev = computed_hash

        return {"valid": True, "count": len(rows), "head_hash": expected_prev}


_audit_loggers: Dict[str, AuditLogger] = {}


def get_audit_logger(data_dir: Path) -> AuditLogger:
    key = str(data_dir)
    if key not in _audit_loggers:
        db_path = data_dir / "audit.db"
        _audit_loggers[key] = AuditLogger(db_path)
    return _audit_loggers[key]
