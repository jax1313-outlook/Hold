"""Read-only access to the database file -- this module's own copy.

Same reasoning as dispatch.ifta.readonly and dispatch.reports.readonly:
each surface owns its own copy rather than importing another's. Opening
the database file itself with SQLite's mode=ro means any write attempt
through this connection -- against any table -- raises immediately, the
structural guarantee this entire package (dashboard.py, app.py) depends
on: there is never a write-capable connection anywhere in scope.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path


def open_read_only(database_path: Path | str) -> sqlite3.Connection:
    uri = f"file:{Path(database_path).resolve()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn
