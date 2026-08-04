"""Lane D's own schema bootstrap for print_queue — the one table this
lane is allowed to write to.

src/dispatch/common/db.py doesn't create this table (out of Lane A's
scope), so this module installs it itself, idempotently, the same
pattern every other lane used for its own tables.

print_queue never gets a DELETE code path, ever — see
docs/lanes/D/LANE_D_LAUNCH_PACKAGE_v1.md risk #1 for the reasoning:
"clearing" a queue entry is a status transition (queued -> printed ->
cleared), the same shape Lane B gave queue_items, not a real deletion.
This sidesteps any tension with DISPATCH_BASE_CONSTITUTION_v1 #6 ("no
worker deletes anything, anywhere, ever") entirely, rather than deciding
print_queue is a constitutional exception.
"""
from __future__ import annotations

import sqlite3

_SCHEMA = """
CREATE TABLE IF NOT EXISTS print_queue (
    print_queue_id TEXT PRIMARY KEY,
    report_type TEXT NOT NULL,
    template_version TEXT NOT NULL,
    as_of TEXT NOT NULL,
    period_label TEXT NOT NULL,
    filters TEXT,
    snapshot_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    saved_at TEXT NOT NULL,
    schema_version TEXT NOT NULL DEFAULT '1.0'
);
"""


def install_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)
    conn.execute(
        """
        CREATE TRIGGER IF NOT EXISTS trg_print_queue_no_delete
        BEFORE DELETE ON print_queue
        BEGIN
            SELECT RAISE(ABORT, 'print_queue entries are cleared via status, never deleted');
        END;
        """
    )
