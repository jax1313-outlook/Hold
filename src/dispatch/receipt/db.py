"""Lane C's own schema bootstrap for fuel_records and expense_records.

src/dispatch/common/db.py is a forbidden file for this lane (Lane A's
allowed files, not Lane C's) — same pattern Lane B used for
`queue_items`: this module installs its own tables and triggers,
idempotently, whenever install_schema() is called against a connection.

Both tables are INSERT-only in this lane's code: no update path exists
for review_status or any other field. A quarantined line's eventual
resolution is a fresh human action recorded elsewhere (the Manager's
queue), not a mutation of a record — because no record is created at all
for anything quarantined; see router.py. Blocking UPDATE/DELETE at the
trigger level is a deliberate defense-in-depth choice, consistent with
the rest of this codebase (DISPATCH_BASE_CONSTITUTION_v1 #6: "no worker
deletes anything, anywhere, ever"), not something this lane's own
constitution names by table.
"""
from __future__ import annotations

import sqlite3

_SCHEMA = """
CREATE TABLE IF NOT EXISTS fuel_records (
    fuel_record_id TEXT PRIMARY KEY,
    evidence_record_id TEXT NOT NULL,
    expense_record_id TEXT NOT NULL,
    purchase_date TEXT NOT NULL,
    purchase_time TEXT,
    vendor_name TEXT NOT NULL,
    vendor_address TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    fuel_type TEXT NOT NULL,
    tractor_or_reefer TEXT NOT NULL,
    volume_as_received REAL NOT NULL,
    volume_as_received_unit TEXT NOT NULL,
    gallons_normalized REAL NOT NULL,
    unit_price REAL NOT NULL,
    total_amount REAL NOT NULL,
    currency TEXT NOT NULL,
    taxes_included INTEGER NOT NULL,
    unit_number TEXT NOT NULL,
    driver TEXT,
    odometer INTEGER,
    payment_method TEXT,
    card_last4 TEXT,
    receipt_number TEXT,
    dedup_key TEXT NOT NULL,
    extraction_confidence REAL NOT NULL,
    review_status TEXT NOT NULL,
    schema_version TEXT NOT NULL DEFAULT '1.0'
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fuel_records_dedup_key
    ON fuel_records(dedup_key);

CREATE TABLE IF NOT EXISTS expense_records (
    expense_record_id TEXT PRIMARY KEY,
    evidence_record_id TEXT NOT NULL,
    fuel_record_id TEXT,
    purchase_date TEXT NOT NULL,
    vendor_name TEXT NOT NULL,
    vendor_location TEXT,
    line_description TEXT NOT NULL,
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    tax_amount REAL,
    currency TEXT NOT NULL,
    payment_method TEXT,
    card_last4 TEXT,
    unit_number TEXT,
    driver TEXT,
    load_id TEXT,
    dedup_key TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'staged',
    quickbooks_ref TEXT,
    extraction_confidence REAL NOT NULL,
    review_status TEXT NOT NULL,
    schema_version TEXT NOT NULL DEFAULT '1.0'
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_expense_records_dedup_key
    ON expense_records(dedup_key);
"""

_IMMUTABLE_TABLES = ("fuel_records", "expense_records")


def install_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)
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
