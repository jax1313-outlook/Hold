"""Read-only access to source records.

IFTA_CONSTITUTION_v1's "source-immutability" section names this mechanism
explicitly: "The IFTA Agent cannot alter a fuel or mileage record to
balance a worksheet — enforced via read-only views, verified with a
negative test." Opening the database file itself with SQLite's `mode=ro`
means any write attempt through this connection — against any table, not
just fuel_records/mileage_records — raises immediately. That's a stronger
guarantee than "the code just doesn't happen to write here."
"""
from __future__ import annotations

import sqlite3
from pathlib import Path


def open_read_only(database_path: Path | str) -> sqlite3.Connection:
    uri = f"file:{Path(database_path).resolve()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn
