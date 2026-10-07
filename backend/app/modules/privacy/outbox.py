"""
Transactional Outbox (TRD §7.1, §9)
Persists aggregate export payloads safely in outbox.db until uploaded.
"""

import sqlite3
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
import structlog
from app.contracts import AggregateExportPayload

log = structlog.get_logger(__name__)


def enqueue_payload(
    data_dir: Path,
    payload: AggregateExportPayload,
    payload_hash: str,
    notice_version: str,
) -> str:
    """Enqueues consented banded payload into outbox.db."""
    db_path = data_dir / "outbox.db"
    outbox_id = str(uuid.uuid4())
    payload_json = payload.model_dump_json()
    ts = time.time()

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS outbox_messages (
                id TEXT PRIMARY KEY,
                created_at REAL NOT NULL,
                payload_json TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                notice_version TEXT NOT NULL,
                status TEXT NOT NULL,
                attempts INTEGER DEFAULT 0,
                last_error TEXT
            )
            """
        )
        conn.execute(
            """
            INSERT INTO outbox_messages (id, created_at, payload_json, payload_hash, notice_version, status)
            VALUES (?, ?, ?, ?, ?, 'QUEUED')
            """,
            (outbox_id, ts, payload_json, payload_hash, notice_version)
        )
        conn.commit()
    finally:
        conn.close()

    log.info("outbox_payload_enqueued", outbox_id=outbox_id, hash=payload_hash[:16])
    return outbox_id
