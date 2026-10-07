"""
SQLite database initializer.

Creates all four SQLite databases in WAL mode:
  - analytics.db : monthly snapshots + customer_activity
  - audit.db     : SHA-256 hash-chained event log
  - outbox.db    : transactional outbox for cloud sync
  - vault.db     : AES-256-GCM encrypted PII vault (customer names/phones)

TRD §7.1 — DDL specifications.
"""

import sqlite3
from pathlib import Path

import structlog

log = structlog.get_logger(__name__)


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Open a SQLite connection in WAL mode (safe for power cuts, concurrent reads)."""
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


# ── analytics.db DDL (TRD §7.1) ──────────────────────────────────────────────

ANALYTICS_DDL = """
CREATE TABLE IF NOT EXISTS snapshots (
    month                TEXT PRIMARY KEY,    -- YYYY-MM
    total_sales          REAL NOT NULL,
    stock_cost_ratio     REAL,                -- stock_purchase / sales (PRD §8.2 caveat)
    credit_share         REAL,               -- outstanding / sales
    overdue_amount       REAL,
    rules_fired          TEXT,               -- JSON array of W1..W7
    actions_json         TEXT,               -- JSON array of ActionItem
    actions_done         INTEGER DEFAULT 0,
    completeness         REAL NOT NULL,
    created_at           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS customer_activity (
    -- LOCAL ONLY: aliases only, never exported (PRD §13)
    alias                TEXT PRIMARY KEY,   -- customer_ref, NOT a real name
    last_purchase        TEXT,              -- ISO date
    purchases_60d        INTEGER DEFAULT 0,
    value_90d            REAL DEFAULT 0.0,
    updated_at           TEXT NOT NULL
);
""";

# ── audit.db DDL (TRD §7.1) ──────────────────────────────────────────────────

AUDIT_DDL = """
CREATE TABLE IF NOT EXISTS audit (
    seq          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id     TEXT UNIQUE NOT NULL,       -- idempotent: run_id:node:attempt
    ts           TEXT NOT NULL,
    run_id       TEXT NOT NULL,
    kind         TEXT NOT NULL,              -- STATE_TRANSITION, G5_FAIL, MODEL_FALLBACK, etc.
    detail       TEXT NOT NULL,             -- JSON string, no PII
    prev_hash    TEXT NOT NULL DEFAULT '',
    hash         TEXT NOT NULL              -- SHA-256(prev_hash || canonical_json(event))
);

CREATE INDEX IF NOT EXISTS idx_audit_run_id ON audit(run_id);
""";

# ── outbox.db DDL (TRD §7.1, ADR-009) ────────────────────────────────────────

OUTBOX_DDL = """
CREATE TABLE IF NOT EXISTS outbox (
    id             TEXT PRIMARY KEY,         -- UUID
    payload        TEXT NOT NULL,            -- JSON: AggregateExportPayload
    payload_hash   TEXT NOT NULL,            -- SHA-256 of payload (must match preview hash)
    consent_ts     TEXT NOT NULL,            -- ISO timestamp of owner consent
    notice_version TEXT NOT NULL,            -- Version of consent notice shown
    status         TEXT NOT NULL DEFAULT 'queued'
                   CHECK(status IN ('queued', 'sent', 'rejected')),
    attempts       INTEGER NOT NULL DEFAULT 0,
    next_try       TEXT NOT NULL             -- ISO timestamp for next retry
);
""";

# ── vault.db DDL (TRD §7.1, ADR-004) ────────────────────────────────────────
# Values encrypted with AES-256-GCM. Nonce stored alongside ciphertext.
# This table is NEVER read by analysis, model, logs, or export modules.

VAULT_DDL = """
CREATE TABLE IF NOT EXISTS vault (
    alias        TEXT PRIMARY KEY,           -- customer_ref alias (NOT the real name)
    name_enc     BLOB,                       -- AES-256-GCM encrypted customer name
    phone_enc    BLOB,                       -- AES-256-GCM encrypted phone number
    updated_at   TEXT NOT NULL
);
""";


def init_all_databases(data_dir: Path) -> None:
    """Initialize all four SQLite databases. Called once at app startup."""
    data_dir.mkdir(parents=True, exist_ok=True)

    _init_db(data_dir / "analytics.db", ANALYTICS_DDL, "analytics")
    _init_db(data_dir / "audit.db", AUDIT_DDL, "audit")
    _init_db(data_dir / "outbox.db", OUTBOX_DDL, "outbox")
    _init_db(data_dir / "vault.db", VAULT_DDL, "vault")


def _init_db(db_path: Path, ddl: str, name: str) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(ddl)
        conn.commit()
        log.info("db_initialized", db=name, path=str(db_path))
    finally:
        conn.close()
