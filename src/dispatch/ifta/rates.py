"""Rate table access.

IFTA_CONSTITUTION_v1: "rates come only from the versioned rate_tables for
that quarter; the worksheet stores the rate-table version it used." A
rate correction is a new row under a new source_version, never an edit
of a published one (rate_tables is INSERT-only — see db.py).

Fixture rows built for this lane's own testing must be tagged so they can
never be mistaken for a real quarterly publication — see
library_seed/RateTables/README.md and docs/lanes/C/NOTES.md.
"""
from __future__ import annotations

import sqlite3
from typing import Any

from dispatch.ifta.db import install_schema

FIXTURE_SOURCE_VERSION_PREFIX = "fixture-"


def insert_rate(
    conn: sqlite3.Connection,
    *,
    jurisdiction: str,
    quarter: str,
    fuel_type: str,
    rate: float,
    source_version: str,
    surcharge: float | None = None,
) -> None:
    # Idempotent -- makes this module usable before a WorksheetEngine has
    # ever been constructed against this connection, not just after.
    install_schema(conn)
    conn.execute(
        """
        INSERT INTO rate_tables (jurisdiction, quarter, fuel_type, rate, surcharge, source_version)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (jurisdiction, quarter, fuel_type, rate, surcharge, source_version),
    )


def get_rate(
    conn: sqlite3.Connection,
    *,
    jurisdiction: str,
    quarter: str,
    fuel_type: str,
    source_version: str,
) -> dict[str, Any] | None:
    install_schema(conn)
    row = conn.execute(
        """
        SELECT rate, surcharge FROM rate_tables
        WHERE jurisdiction = ? AND quarter = ? AND fuel_type = ? AND source_version = ?
        """,
        (jurisdiction, quarter, fuel_type, source_version),
    ).fetchone()
    return dict(row) if row is not None else None


def distinct_versions_for(
    conn: sqlite3.Connection, *, jurisdiction: str, quarter: str, fuel_type: str
) -> list[str]:
    install_schema(conn)
    rows = conn.execute(
        """
        SELECT DISTINCT source_version FROM rate_tables
        WHERE jurisdiction = ? AND quarter = ? AND fuel_type = ?
        """,
        (jurisdiction, quarter, fuel_type),
    ).fetchall()
    return [row[0] for row in rows]
