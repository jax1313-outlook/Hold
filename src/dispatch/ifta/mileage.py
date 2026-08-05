"""Manual mileage entry -- the one real write path, shared by
tools/mileage_worksheet.py (CLI, scripting/backfill) and
dispatch.ifta_clerk's mileage-entry route (UI). Moved here 2026-08-05 so
neither duplicates the INSERT; previously this lived only in the CLI
tool, which application code under src/ has no business importing from.

Takes an already-open connection rather than a config dict, matching
dispatch.ifta.package.attempt_seal()/prepare.prepare_quarter()'s shape
-- the caller owns connection lifecycle (the CLI tool bootstraps its
own and exits; dispatch.ifta_clerk reuses its flask.g-cached write
connection, closed by teardown_appcontext like every other write
action in that app).

v1 reality (contracts/mileage_record.schema.json): entered by a human;
the schema is identical when Dispatch Ops automates it later. There is
no ELD/GPS/odometer-device integration anywhere in this codebase, and
none is planned -- manual entry is this system's permanent source of
truth for mileage (IFTA_CLERK_BLUEPRINT_v1 section 12, question 2;
resolved 2026-08-05, see docs/decisions/DECISION_LOG.md)."""
from __future__ import annotations

import sqlite3

from dispatch.common.ids import new_ulid


def record_mileage(
    conn: sqlite3.Connection,
    *,
    unit_number: str,
    jurisdiction: str,
    period_start: str,
    period_end: str,
    miles: float,
    entered_by: str,
    odometer_start: int | None = None,
    odometer_end: int | None = None,
    source: str = "manual_worksheet",
) -> str:
    mileage_record_id = new_ulid()
    conn.execute(
        """
        INSERT INTO mileage_records (
            mileage_record_id, unit_number, period_start, period_end,
            jurisdiction, miles, source, odometer_start, odometer_end,
            entered_by, schema_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '1.0')
        """,
        (
            mileage_record_id, unit_number, period_start, period_end,
            jurisdiction, miles, source, odometer_start, odometer_end, entered_by,
        ),
    )
    return mileage_record_id
