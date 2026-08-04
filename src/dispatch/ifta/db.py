"""Lane C's own schema bootstrap for the IFTA tables.

Same reasoning as src/dispatch/receipt/db.py: src/dispatch/common/db.py is
a forbidden file for this lane, so this module installs its own tables
and immutability rules, idempotently, whenever install_schema() runs.

- `rate_tables`: INSERT-only. A rate correction is a new row (new
  source_version), never an edit of a published one.
- `ifta_worksheet_lines`, `ifta_exceptions`: INSERT-only. These are
  computation snapshots — recomputing means building a new worksheet
  (new id), never mutating an old one's lines or exceptions.
- `ifta_worksheets`: DELETE is blocked (no worker deletes anything,
  ever), but UPDATE is allowed for exactly one transition, draft -> sealed
  (package.py), the same way queue_items allows status transitions.
"""
from __future__ import annotations

import sqlite3

_SCHEMA = """
CREATE TABLE IF NOT EXISTS rate_tables (
    jurisdiction TEXT NOT NULL,
    quarter TEXT NOT NULL,
    fuel_type TEXT NOT NULL,
    rate REAL NOT NULL,
    surcharge REAL,
    source_version TEXT NOT NULL,
    PRIMARY KEY (jurisdiction, quarter, fuel_type, source_version)
);

CREATE TABLE IF NOT EXISTS ifta_worksheets (
    ifta_worksheet_id TEXT PRIMARY KEY,
    quarter TEXT NOT NULL,
    fuel_type TEXT NOT NULL,
    fleet_mpg REAL NOT NULL,
    rate_table_version TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    total_net_tax REAL NOT NULL,
    created_at TEXT NOT NULL,
    sealed_at TEXT,
    queue_item_id TEXT,
    schema_version TEXT NOT NULL DEFAULT '1.0'
);

CREATE TABLE IF NOT EXISTS ifta_worksheet_lines (
    ifta_worksheet_line_id TEXT PRIMARY KEY,
    ifta_worksheet_id TEXT NOT NULL REFERENCES ifta_worksheets(ifta_worksheet_id),
    jurisdiction TEXT NOT NULL,
    miles REAL NOT NULL,
    taxable_gallons REAL NOT NULL,
    tax_paid_gallons REAL NOT NULL,
    rate REAL NOT NULL,
    surcharge REAL,
    net_tax REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS ifta_exceptions (
    ifta_exception_id TEXT PRIMARY KEY,
    ifta_worksheet_id TEXT,
    exception_type TEXT NOT NULL,
    detail TEXT,
    related_record_ids TEXT,
    detected_at TEXT NOT NULL,
    queue_item_id TEXT
);
"""

_INSERT_ONLY_TABLES = ("rate_tables", "ifta_worksheet_lines", "ifta_exceptions")
_NO_DELETE_ONLY_TABLES = ("ifta_worksheets",)


def install_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)

    for table in _INSERT_ONLY_TABLES:
        conn.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS trg_{table}_no_update
            BEFORE UPDATE ON {table}
            BEGIN
                SELECT RAISE(ABORT, '{table} is insert-only: UPDATE is not permitted');
            END;
            """
        )
        conn.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS trg_{table}_no_delete
            BEFORE DELETE ON {table}
            BEGIN
                SELECT RAISE(ABORT, '{table} is insert-only: DELETE is not permitted');
            END;
            """
        )

    for table in _NO_DELETE_ONLY_TABLES:
        conn.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS trg_{table}_no_delete
            BEFORE DELETE ON {table}
            BEGIN
                SELECT RAISE(ABORT, '{table} is immutable: DELETE is not permitted');
            END;
            """
        )
