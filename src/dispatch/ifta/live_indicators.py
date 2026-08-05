"""IFTA Live Indicators — Category 2 of the Exception Dashboard
(IFTA_CLERK_BLUEPRINT_v1 section 8, approved in principle 2026-08-04).

Informational only. Calling live_indicators() answers "would any of these
four detectors flag something if a worksheet were built for this quarter
right now?" — it never answers "has Mike been asked to decide about
this." Only a real build() followed by run_all_detectors() creates a
governed exception: a persisted ifta_exceptions row and a real Queue
item. Nothing in this module ever does either of those things, no matter
how many times or how often it's called. Viewing a live indicator is not
a workflow event and never triggers one.

Same five structural protections dispatch.ifta.worksheet.preview() was
built to, checked the same way in this module's own tests (inspect/ast,
not just today's return value):

1. Read only. live_indicators() takes exactly one connection parameter,
   read_only_conn — there is no write-capable connection anywhere in its
   scope to write with.
2. Non-persistent. run_all_detectors() -- the only code in this lane
   that writes an ifta_exceptions row -- is never imported or called
   here.
3. No queue activity. dispatch.queue.store.QueueStore is never
   imported or constructed here; no queue_items row is ever touched.
4. No approval activity. dispatch.ifta.package -- submit_for_approval,
   attempt_seal -- is never imported here.
5. No audit activity. dispatch.common.audit.write_audit_entry is never
   imported or called here. This is exactly why broken_evidence_linkage
   is deliberately excluded from this module even though it shares the
   other four detectors' worksheet-free function signature: it calls
   EvidenceSpine.retrieve(), which always writes a real audit_log row
   and, on a hash mismatch, a real urgent Queue item -- a side effect
   from viewing a dashboard, which is exactly what this module exists to
   never do. It remains available today only through a real build(), as
   a Category 1 (confirmed) exception.

A missing fuel_records/mileage_records/ifta_worksheets table (a
genuinely fresh install, or a quarter with no worksheet ever built) reads
back as "nothing to find yet," not a crash -- the same reasoning
dispatch.ifta.worksheet.preview() already applies to its own aggregators,
applied here at this module's own layer since exceptions.py itself is
out of this change's scope.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from dispatch.ifta.exceptions import (
    active_truck_days_no_mileage,
    late_arrival_closed_quarter,
    odometer_discontinuity,
    reefer_in_propulsion,
)
from dispatch.ifta.worksheet import quarter_bounds


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

# Deliberately its own vocabulary, not Lane B's urgent/today/whenever Queue
# priority -- a live indicator never touches the Queue, so it must never
# read as if it had. "critical" > "warning" > "notice".
SEVERITY_BY_EXCEPTION_TYPE = {
    # The router already refuses to create a reefer-flagged fuel_record in
    # the first place (router.ReeferMisroutedError). This firing at all
    # means a bug elsewhere or a hand-edited row -- the worst signal here.
    "reefer_in_propulsion": "critical",
    # A document dated inside an already-sealed, already-filed quarter --
    # a real filing-integrity question that needs a human decision.
    "late_arrival_closed_quarter": "warning",
    # A real data gap: this truck bought fuel but has no mileage on file
    # for the quarter -- will block an accurate worksheet build.
    "active_truck_days_no_mileage": "warning",
    # Worth a look, but most likely to have an innocuous explanation (a
    # replaced or reset odometer) rather than a genuine problem.
    "odometer_discontinuity": "notice",
}


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table_name,)
    ).fetchone()
    return row is not None


def _safe_call(detector, *args: Any) -> list[dict[str, Any]]:
    """A table the detector expects (fuel_records, mileage_records,
    ifta_worksheets) may not exist yet -- reads as no findings, not a
    crash. exceptions.py itself is unmodified; this guard lives here."""
    try:
        return detector(*args)
    except sqlite3.OperationalError as exc:
        if "no such table" not in str(exc):
            raise
        return []


def _tag(findings: list[dict[str, Any]], severity: str) -> list[dict[str, Any]]:
    return [dict(finding, severity=severity) for finding in findings]


def live_indicators(read_only_conn: sqlite3.Connection, *, quarter: str, fuel_type: str) -> dict[str, Any]:
    """A live, non-persisting look at what the four worksheet-free
    detectors would flag right now, for this quarter/fuel_type, from real
    current data. Never queued, never counted toward "open exceptions" in
    any governed sense -- see the module docstring."""
    start, end = quarter_bounds(quarter)

    findings: list[dict[str, Any]] = []
    findings += _tag(
        _safe_call(odometer_discontinuity, read_only_conn, start, end),
        SEVERITY_BY_EXCEPTION_TYPE["odometer_discontinuity"],
    )
    findings += _tag(
        _safe_call(active_truck_days_no_mileage, read_only_conn, start, end),
        SEVERITY_BY_EXCEPTION_TYPE["active_truck_days_no_mileage"],
    )
    # late_arrival_closed_quarter's signature is (conn, ro_conn, fuel_type):
    # the same read-only connection satisfies both -- every query it runs,
    # against ifta_worksheets and fuel_records alike, is a plain SELECT.
    findings += _tag(
        _safe_call(late_arrival_closed_quarter, read_only_conn, read_only_conn, fuel_type),
        SEVERITY_BY_EXCEPTION_TYPE["late_arrival_closed_quarter"],
    )
    findings += _tag(
        _safe_call(reefer_in_propulsion, read_only_conn),
        SEVERITY_BY_EXCEPTION_TYPE["reefer_in_propulsion"],
    )

    return {
        "status": "live_indicator",
        "is_live_indicator": True,
        "quarter": quarter,
        "fuel_type": fuel_type,
        "findings": findings,
        "generated_at": _utc_now_iso(),
    }
