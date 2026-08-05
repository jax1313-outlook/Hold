"""dispatch.ifta_clerk.dashboard -- assembles the Review Dashboard's
seven panels (IFTA_CLERK_BLUEPRINT_v1 section 7), now the primary user
experience of the IFTA Clerk (approved 2026-08-04). Entirely read-only,
entirely assembled from existing, already-governed sources -- no new
table, no new writer, no duplicate store.

**Evidence First.** The Evidence Record is always authoritative; nothing
here re-derives or second-guesses anything Lane C's router already
computed -- every number is read exactly as stored.

**Read-only Workspace.** build_dashboard() takes only a read-only
connection -- there is no write-capable connection anywhere in its scope
to write with. No INSERT/UPDATE/DELETE appears anywhere in this file
(tests/ifta_clerk/test_dashboard.py checks this by source scan, the same
technique every other lane's boundary-refusal tests use).

**Human Authority.** Nothing here approves, seals, resolves, or builds
anything. Every action a panel might suggest (approve an exception,
build a worksheet) is a plain link out to the real Queue or /ifta's real
write routes -- never replicated here.

**Recommendation Packages Only / no QuickBooks / no DocuSign / no
Filing.** Trivially true this phase: nothing here writes anywhere, so
there is no external system to integrate with yet.

**Panel 6 (evidence links) deliberately does not call
EvidenceSpine.retrieve().** retrieve() writes a real audit_log row on
every call and, on a hash mismatch, a real urgent Queue item -- exactly
the class of dashboard-viewing side effect already ruled out for
broken_evidence_linkage in Category 2 Live Indicators. Calling it once
per fuel record shown on this dashboard would mean every page view
writes N audit rows. This panel is a plain reference read against
evidence_records instead -- document_type, archive_path, file_hash, no
hash re-verification, no audit trail. Hash verification remains a
real, available, per-record action -- just not one this dashboard
triggers merely by being viewed.

**Rate table version, a gap the blueprint didn't resolve.** preview()
requires a rate_table_version, and there's no global "current" one --
multiple can coexist (build/ifta-ui's own Build form let Mike choose).
Rather than guess, this module looks at how many distinct source_versions
exist for the quarter/fuel_type: exactly one -> use it; zero -> "no rate
entered yet"; more than one -> "ambiguous, resolve via a real build",
never silently picking one. Same "no fabrication" doctrine
IFTA_CONSTITUTION_v1 already applies to MissingRateError.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date
from typing import Any

from dispatch.ifta.live_indicators import live_indicators
from dispatch.ifta.worksheet import (
    InsufficientDataError,
    MissingRateError,
    latest_worksheet_for,
    preview,
    quarter_bounds,
)

DEFAULT_CONFIDENCE_THRESHOLD = 0.75  # same placeholder validators.py uses -- not yet calibrated, IFTA_CLERK_BLUEPRINT_v1 sections 9/12.3


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table_name,)
    ).fetchone()
    return row is not None


def _miles_by_jurisdiction(conn: sqlite3.Connection, start: date, end: date) -> dict[str, float]:
    if not _table_exists(conn, "mileage_records"):
        return {}
    rows = conn.execute(
        "SELECT jurisdiction, miles, period_start, period_end FROM mileage_records"
    ).fetchall()
    by_jurisdiction: dict[str, float] = {}
    for row in rows:
        period_start = date.fromisoformat(row["period_start"])
        period_end = date.fromisoformat(row["period_end"])
        if period_start >= start and period_end <= end:
            by_jurisdiction[row["jurisdiction"]] = by_jurisdiction.get(row["jurisdiction"], 0.0) + row["miles"]
    return by_jurisdiction


def _fuel_by_jurisdiction(conn: sqlite3.Connection, start: date, end: date, fuel_type: str) -> dict[str, float]:
    if not _table_exists(conn, "fuel_records"):
        return {}
    rows = conn.execute(
        "SELECT jurisdiction, gallons_normalized, purchase_date FROM fuel_records WHERE fuel_type = ?",
        (fuel_type,),
    ).fetchall()
    by_jurisdiction: dict[str, float] = {}
    for row in rows:
        purchase_date = date.fromisoformat(row["purchase_date"])
        if start <= purchase_date <= end:
            by_jurisdiction[row["jurisdiction"]] = by_jurisdiction.get(row["jurisdiction"], 0.0) + row["gallons_normalized"]
    return by_jurisdiction


def _suspect_entries(
    conn: sqlite3.Connection, start: date, end: date, fuel_type: str, threshold: float
) -> list[dict[str, Any]]:
    """fuel_records/expense_records below the confidence threshold,
    within the quarter -- read-only, no recomputation of confidence
    itself (that's Lane C's, computed once at extraction time)."""
    suspects: list[dict[str, Any]] = []
    if _table_exists(conn, "fuel_records"):
        rows = conn.execute(
            "SELECT fuel_record_id, vendor_name, purchase_date, extraction_confidence, evidence_record_id "
            "FROM fuel_records WHERE fuel_type = ? AND extraction_confidence < ?",
            (fuel_type, threshold),
        ).fetchall()
        for row in rows:
            if start <= date.fromisoformat(row["purchase_date"]) <= end:
                suspects.append(
                    {
                        "record_type": "fuel",
                        "record_id": row["fuel_record_id"],
                        "vendor_name": row["vendor_name"],
                        "purchase_date": row["purchase_date"],
                        "extraction_confidence": row["extraction_confidence"],
                        "evidence_record_id": row["evidence_record_id"],
                    }
                )
    if _table_exists(conn, "expense_records"):
        rows = conn.execute(
            "SELECT expense_record_id, vendor_name, purchase_date, extraction_confidence, evidence_record_id "
            "FROM expense_records WHERE extraction_confidence < ?",
            (threshold,),
        ).fetchall()
        for row in rows:
            if start <= date.fromisoformat(row["purchase_date"]) <= end:
                suspects.append(
                    {
                        "record_type": "expense",
                        "record_id": row["expense_record_id"],
                        "vendor_name": row["vendor_name"],
                        "purchase_date": row["purchase_date"],
                        "extraction_confidence": row["extraction_confidence"],
                        "evidence_record_id": row["evidence_record_id"],
                    }
                )
    return suspects


def _evidence_links(conn: sqlite3.Connection, start: date, end: date, fuel_type: str) -> list[dict[str, Any]]:
    """Plain references, no EvidenceSpine.retrieve() call -- see module
    docstring. One row per fuel_record's evidence_record_id in the
    quarter, joined against evidence_records for document_type/archive
    path/hash -- all already-stored values, none re-verified here."""
    if not _table_exists(conn, "fuel_records") or not _table_exists(conn, "evidence_records"):
        return []
    rows = conn.execute(
        """
        SELECT fr.fuel_record_id, fr.purchase_date, fr.evidence_record_id,
               er.document_type, er.archive_path, er.file_hash
        FROM fuel_records fr
        JOIN evidence_records er ON er.evidence_record_id = fr.evidence_record_id
        WHERE fr.fuel_type = ?
        """,
        (fuel_type,),
    ).fetchall()
    links: list[dict[str, Any]] = []
    for row in rows:
        if start <= date.fromisoformat(row["purchase_date"]) <= end:
            links.append(dict(row))
    return links


def _confirmed_exceptions(conn: sqlite3.Connection, ifta_worksheet_id: str) -> list[dict[str, Any]]:
    """Category 1 -- real, persisted findings for a real, built worksheet."""
    if not _table_exists(conn, "ifta_exceptions"):
        return []
    rows = conn.execute(
        "SELECT * FROM ifta_exceptions WHERE ifta_worksheet_id = ?", (ifta_worksheet_id,)
    ).fetchall()
    findings = []
    for row in rows:
        finding = dict(row)
        finding["related_record_ids"] = json.loads(finding["related_record_ids"]) if finding["related_record_ids"] else []
        findings.append(finding)
    return findings


def distinct_rate_versions_for_quarter(conn: sqlite3.Connection, *, quarter: str, fuel_type: str) -> list[str]:
    """Public (not module-private) because prepare.py's real build() call
    needs the identical no-fabrication rate-version resolution this
    module's own preview() estimate already uses -- shared within this
    package, not reimplemented a second time."""
    if not _table_exists(conn, "rate_tables"):
        return []
    rows = conn.execute(
        "SELECT DISTINCT source_version FROM rate_tables WHERE quarter = ? AND fuel_type = ?",
        (quarter, fuel_type),
    ).fetchall()
    return sorted(row["source_version"] for row in rows)


def _tax_position(conn: sqlite3.Connection, worksheet: dict[str, Any] | None, *, quarter: str, fuel_type: str) -> dict[str, Any]:
    if worksheet is not None:
        return {"source": "worksheet", "worksheet": worksheet, "estimate": None, "error": None}

    rate_versions = distinct_rate_versions_for_quarter(conn, quarter=quarter, fuel_type=fuel_type)
    if len(rate_versions) == 0:
        return {"source": "preview", "worksheet": None, "estimate": None, "error": "no rate has been entered for this quarter yet"}
    if len(rate_versions) > 1:
        return {
            "source": "preview", "worksheet": None, "estimate": None,
            "error": f"multiple rate versions on file ({', '.join(rate_versions)}) -- ambiguous, resolve via a real build",
        }
    try:
        estimate = preview(conn, quarter=quarter, fuel_type=fuel_type, rate_table_version=rate_versions[0])
        return {"source": "preview", "worksheet": None, "estimate": estimate, "error": None}
    except (InsufficientDataError, MissingRateError) as exc:
        return {"source": "preview", "worksheet": None, "estimate": None, "error": str(exc)}


def _readiness_status(
    *, confirmed_exceptions: list, live_findings: list, suspects: list, miles_by_jurisdiction: dict
) -> str:
    """One rollup label -- pure computation over what the other panels
    already fetched, no new query. The one genuinely new piece of logic
    on this dashboard, and a small one."""
    if confirmed_exceptions:
        return f"{len(confirmed_exceptions)} exception(s) open"
    if suspects:
        return f"{len(suspects)} record(s) below confidence threshold"
    if live_findings:
        critical = [f for f in live_findings if f["severity"] == "critical"]
        if critical:
            return f"{len(critical)} critical live indicator(s)"
        return f"{len(live_findings)} live indicator(s) noted"
    if not miles_by_jurisdiction:
        return "no mileage recorded yet this quarter"
    return "ready to prepare"


def build_dashboard(read_only_conn: sqlite3.Connection, *, quarter: str, fuel_type: str) -> dict[str, Any]:
    """Assembles all seven Review Dashboard panels from real current
    data. Takes only a read-only connection -- the same structural
    guarantee preview()/live_indicators() already use. Never persists,
    never queues, never audits, no matter how many times it's called."""
    start, end = quarter_bounds(quarter)

    worksheet = latest_worksheet_for(read_only_conn, quarter=quarter, fuel_type=fuel_type)
    confirmed_exceptions = _confirmed_exceptions(read_only_conn, worksheet["ifta_worksheet_id"]) if worksheet else []
    tax_position = _tax_position(read_only_conn, worksheet, quarter=quarter, fuel_type=fuel_type)

    live = live_indicators(read_only_conn, quarter=quarter, fuel_type=fuel_type)
    live_findings = live["findings"]

    miles_by_jurisdiction = _miles_by_jurisdiction(read_only_conn, start, end)
    fuel_by_jurisdiction = _fuel_by_jurisdiction(read_only_conn, start, end, fuel_type)
    suspects = _suspect_entries(read_only_conn, start, end, fuel_type, DEFAULT_CONFIDENCE_THRESHOLD)
    evidence_links = _evidence_links(read_only_conn, start, end, fuel_type)

    readiness_status = _readiness_status(
        confirmed_exceptions=confirmed_exceptions,
        live_findings=live_findings,
        suspects=suspects,
        miles_by_jurisdiction=miles_by_jurisdiction,
    )

    return {
        "quarter": quarter,
        "fuel_type": fuel_type,
        "readiness_status": readiness_status,
        "miles_by_jurisdiction": miles_by_jurisdiction,
        "fuel_by_jurisdiction": fuel_by_jurisdiction,
        "confirmed_exceptions": confirmed_exceptions,
        "live_indicator_findings": live_findings,
        "suspect_entries": suspects,
        "confidence_threshold": DEFAULT_CONFIDENCE_THRESHOLD,
        "evidence_links": evidence_links,
        "tax_position": tax_position,
    }
