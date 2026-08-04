"""Read-only access to governed storage.

REPORTS_CHARTER_v1.md's first bright line: "Database connection opened
READ-ONLY (mode=ro) everywhere except one narrow print-queue/snapshot
writer. Any other write attempt must fail." This is deliberately a
near-duplicate of dispatch.ifta.readonly — not imported from there, or
from anywhere else under src/dispatch/{evidence,queue,receipt,ifta}/**.
Reports reads other lanes' tables directly via SQL; it never imports
their business logic (see docs/lanes/D/LANE_D_LAUNCH_PACKAGE_v1.md §4 for
why that line is deliberately kept sharp).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path


def open_read_only(database_path: Path | str) -> sqlite3.Connection:
    uri = f"file:{Path(database_path).resolve()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn
