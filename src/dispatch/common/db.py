"""SQLite bootstrap: WAL mode, foreign keys, immutability triggers.

Creates only the tables inside Lane A's allowed files (LANE_A_LAUNCH_PACKAGE_v1
§2): evidence_records, mileage_records, queue_items, audit_log. Also creates
evidence_children, an append-only backing store for evidence_records'
derived_record_ids (see src/dispatch/evidence/README.md for why). Does NOT
create fuel_records or expense_records — those tables are Lane C's router,
out of this lane's allowed files, independent of their FROZEN/DRAFT status.

bootstrap() is idempotent: every statement is CREATE-IF-NOT-EXISTS, so any
module that needs a connection just calls it and gets one back with the
schema and pragmas guaranteed in place.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS evidence_records (
    evidence_record_id TEXT PRIMARY KEY,
    archive_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    document_type TEXT NOT NULL,
    vendor TEXT,
    document_date TEXT NOT NULL,
    capture_date TEXT NOT NULL,
    statement_period_start TEXT,
    statement_period_end TEXT,
    page_count INTEGER,
    extraction_status TEXT NOT NULL,
    duplicate_of TEXT,
    reviewed_by TEXT,
    review_date TEXT,
    retention_class TEXT NOT NULL DEFAULT 'ifta_4yr',
    schema_version TEXT NOT NULL DEFAULT '1.0'
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_evidence_records_file_hash
    ON evidence_records(file_hash);

-- Append-only backing store for evidence_records.derived_record_ids.
-- link_children() only ever INSERTs here; nothing in this codebase issues
-- UPDATE or DELETE against evidence_records itself to grow that list.
CREATE TABLE IF NOT EXISTS evidence_children (
    evidence_record_id TEXT NOT NULL REFERENCES evidence_records(evidence_record_id),
    derived_record_id TEXT NOT NULL,
    linked_at TEXT NOT NULL,
    PRIMARY KEY (evidence_record_id, derived_record_id)
);

CREATE TABLE IF NOT EXISTS mileage_records (
    mileage_record_id TEXT PRIMARY KEY,
    unit_number TEXT NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    miles REAL NOT NULL,
    source TEXT NOT NULL,
    odometer_start REAL,
    odometer_end REAL,
    entered_by TEXT NOT NULL,
    schema_version TEXT NOT NULL DEFAULT '1.0'
);

CREATE TABLE IF NOT EXISTS queue_items (
    queue_item_id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    source_worker TEXT NOT NULL,
    created_at TEXT NOT NULL,
    priority TEXT NOT NULL,
    subject TEXT NOT NULL,
    payload_refs TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    decided_by TEXT,
    decided_at TEXT,
    decision_note TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    actor TEXT NOT NULL,
    actor_version TEXT NOT NULL,
    constitution_version TEXT NOT NULL,
    action TEXT NOT NULL,
    input_refs TEXT,
    output_refs TEXT,
    gate_ref TEXT,
    trade_memory_refs TEXT,
    outcome TEXT NOT NULL,
    note TEXT
);
"""

# Tables with no update/delete code path, permanently (DISPATCH_BASE_CONSTITUTION_v1
# #6; evidence_record.schema.json and audit_entry.schema.json "immutability").
# evidence_children is included: its rows are also "appended only, never
# removed" per the derived_record_ids contract note.
_IMMUTABLE_TABLES = ("evidence_records", "evidence_children", "audit_log")


def _install_immutability_triggers(conn: sqlite3.Connection) -> None:
    for table in _IMMUTABLE_TABLES:
        conn.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS trg_{table}_no_update
            BEFORE UPDATE ON {table}
            BEGIN
                SELECT RAISE(ABORT, '{table} is immutable: UPDATE is not permitted');
            END;
            """
        )
        conn.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS trg_{table}_no_delete
            BEFORE DELETE ON {table}
            BEGIN
                SELECT RAISE(ABORT, '{table} is immutable: DELETE is not permitted');
            END;
            """
        )


def bootstrap(db_path: Path | str, *, busy_timeout_ms: int = 5000) -> sqlite3.Connection:
    """Open (creating if needed) the dispatch SQLite database, with WAL mode,
    foreign keys, a busy timeout for concurrent lane access, the Lane A
    tables, and the immutability triggers installed. Safe to call repeatedly,
    including from multiple lanes/processes against the same file."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute(f"PRAGMA busy_timeout={busy_timeout_ms};")
    conn.executescript(_SCHEMA)
    _install_immutability_triggers(conn)
    return conn
