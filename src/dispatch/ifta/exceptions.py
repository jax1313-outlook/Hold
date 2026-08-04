"""The ten IFTA exception detectors — IFTA_CONSTITUTION_v1's exception
list, verbatim. Every detector returns plain dicts describing what it
found; `run_all_detectors` is what persists them to `ifta_exceptions` and
raises a queue item for each — the IFTA Agent never auto-resolves any of
these, per the same constitution.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from typing import Any

from dispatch.evidence.interface import EvidenceIntegrityError, EvidenceNotFoundError, EvidenceSpine
from dispatch.ifta import rates
from dispatch.ifta.worksheet import quarter_bounds

DEFAULT_MPG_BAND = (4.0, 9.5)
DEFAULT_CORNER_CLIP_MILES = 5.0


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _exc(exception_type: str, detail: str, related_record_ids: list[str] | None = None) -> dict[str, Any]:
    return {
        "exception_type": exception_type,
        "detail": detail,
        "related_record_ids": related_record_ids or [],
    }


# -- 1. fuel purchased in a jurisdiction with zero recorded miles -----------

def fuel_no_miles(worksheet: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _exc(
            "fuel_no_miles",
            f"{line['jurisdiction']}: {line['tax_paid_gallons']:.2f} gallons purchased, 0 miles recorded",
        )
        for line in worksheet["lines"]
        if line["tax_paid_gallons"] > 0 and line["miles"] == 0
    ]


# -- 2. substantial miles in a jurisdiction with an implausible fuel gap ----

def miles_no_fuel_gap(worksheet: dict[str, Any], *, miles_threshold: float = 50.0) -> list[dict[str, Any]]:
    return [
        _exc(
            "miles_no_fuel_gap",
            f"{line['jurisdiction']}: {line['miles']:.1f} miles recorded, 0 gallons purchased there",
        )
        for line in worksheet["lines"]
        if line["miles"] > miles_threshold and line["tax_paid_gallons"] == 0
    ]


# -- 3. fleet MPG out of band -------------------------------------------------

def fleet_mpg_out_of_band(
    worksheet: dict[str, Any], *, band: tuple[float, float] = DEFAULT_MPG_BAND
) -> list[dict[str, Any]]:
    low, high = band
    mpg = worksheet["fleet_mpg"]
    if not (low <= mpg <= high):
        return [_exc("fleet_mpg_out_of_band", f"fleet_mpg {mpg:.2f} outside plausible range [{low}, {high}]")]
    return []


# -- 4. odometer discontinuities ---------------------------------------------

def odometer_discontinuity(ro_conn: sqlite3.Connection, start: date, end: date) -> list[dict[str, Any]]:
    rows = ro_conn.execute(
        """
        SELECT fuel_record_id, unit_number, purchase_date, odometer FROM fuel_records
        WHERE odometer IS NOT NULL ORDER BY unit_number, purchase_date
        """
    ).fetchall()
    findings = []
    last_by_unit: dict[str, tuple[str, int]] = {}
    for row in rows:
        purchase_date = date.fromisoformat(row["purchase_date"])
        if not (start <= purchase_date <= end):
            continue
        unit = row["unit_number"]
        if unit in last_by_unit:
            _, last_odometer = last_by_unit[unit]
            if row["odometer"] < last_odometer:
                findings.append(
                    _exc(
                        "odometer_discontinuity",
                        f"unit {unit}: odometer {row['odometer']} < prior reading {last_odometer}",
                        [row["fuel_record_id"]],
                    )
                )
        last_by_unit[unit] = (row["purchase_date"], row["odometer"])
    return findings


# -- 5. active-truck days with no mileage records ----------------------------

def active_truck_days_no_mileage(ro_conn: sqlite3.Connection, start: date, end: date) -> list[dict[str, Any]]:
    fuel_units = {
        row["unit_number"]
        for row in ro_conn.execute("SELECT unit_number, purchase_date FROM fuel_records").fetchall()
        if start <= date.fromisoformat(row["purchase_date"]) <= end
    }
    mileage_units = {
        row["unit_number"]
        for row in ro_conn.execute("SELECT unit_number, period_start, period_end FROM mileage_records").fetchall()
        if date.fromisoformat(row["period_start"]) >= start and date.fromisoformat(row["period_end"]) <= end
    }
    return [
        _exc("active_truck_days_no_mileage", f"unit {unit} purchased fuel this quarter but has no mileage records")
        for unit in sorted(fuel_units - mileage_units)
    ]


# -- 6. fuel record with broken evidence linkage -----------------------------

def broken_evidence_linkage(
    ro_conn: sqlite3.Connection, spine: EvidenceSpine, start: date, end: date
) -> list[dict[str, Any]]:
    rows = ro_conn.execute(
        "SELECT fuel_record_id, evidence_record_id, purchase_date FROM fuel_records"
    ).fetchall()
    findings = []
    for row in rows:
        if not (start <= date.fromisoformat(row["purchase_date"]) <= end):
            continue
        try:
            spine.retrieve(row["evidence_record_id"])
        except (EvidenceNotFoundError, EvidenceIntegrityError) as exc:
            findings.append(
                _exc(
                    "broken_evidence_linkage",
                    f"fuel_record {row['fuel_record_id']}: {exc}",
                    [row["fuel_record_id"], row["evidence_record_id"]],
                )
            )
    return findings


# -- 7. late-arriving documents dated in a closed quarter --------------------

def late_arrival_closed_quarter(
    conn: sqlite3.Connection, ro_conn: sqlite3.Connection, fuel_type: str
) -> list[dict[str, Any]]:
    sealed = conn.execute(
        "SELECT quarter FROM ifta_worksheets WHERE fuel_type = ? AND status = 'sealed'", (fuel_type,)
    ).fetchall()
    findings = []
    for row in sealed:
        sealed_quarter = row["quarter"]
        start, end = quarter_bounds(sealed_quarter)
        stragglers = ro_conn.execute(
            "SELECT fuel_record_id, purchase_date FROM fuel_records WHERE fuel_type = ?", (fuel_type,)
        ).fetchall()
        for straggler in stragglers:
            purchase_date = date.fromisoformat(straggler["purchase_date"])
            if start <= purchase_date <= end:
                findings.append(
                    _exc(
                        "late_arrival_closed_quarter",
                        f"fuel_record {straggler['fuel_record_id']} dated {straggler['purchase_date']} "
                        f"falls in already-sealed quarter {sealed_quarter} — never silently absorbed",
                        [straggler["fuel_record_id"]],
                    )
                )
    return findings


# -- 8. rate-table version mismatch ------------------------------------------

def rate_version_mismatch(conn: sqlite3.Connection, worksheet: dict[str, Any]) -> list[dict[str, Any]]:
    findings = []
    for line in worksheet["lines"]:
        versions = rates.distinct_versions_for(
            conn, jurisdiction=line["jurisdiction"], quarter=worksheet["quarter"], fuel_type=worksheet["fuel_type"]
        )
        if len(versions) > 1:
            findings.append(
                _exc(
                    "rate_version_mismatch",
                    f"{line['jurisdiction']}: {len(versions)} rate versions exist for "
                    f"{worksheet['quarter']}/{worksheet['fuel_type']} ({sorted(versions)}); "
                    f"worksheet used {worksheet['rate_table_version']!r}",
                )
            )
    return findings


# -- 9. reefer-flagged fuel appearing in propulsion gallons ------------------

def reefer_in_propulsion(ro_conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = ro_conn.execute(
        "SELECT fuel_record_id FROM fuel_records WHERE tractor_or_reefer = 'reefer'"
    ).fetchall()
    return [
        _exc("reefer_in_propulsion", f"fuel_record {row['fuel_record_id']} is reefer-flagged but exists in fuel_records", [row["fuel_record_id"]])
        for row in rows
    ]


# -- 10. corner-clipping jurisdictions ---------------------------------------

def corner_clipping(worksheet: dict[str, Any], *, threshold: float = DEFAULT_CORNER_CLIP_MILES) -> list[dict[str, Any]]:
    return [
        _exc(
            "corner_clipping",
            f"{line['jurisdiction']}: only {line['miles']:.2f} miles — annotated, not suppressed",
        )
        for line in worksheet["lines"]
        if 0 < line["miles"] < threshold
    ]


def run_all_detectors(
    conn: sqlite3.Connection,
    ro_conn: sqlite3.Connection,
    spine: EvidenceSpine,
    queue,
    worksheet: dict[str, Any],
    *,
    mpg_band: tuple[float, float] = DEFAULT_MPG_BAND,
    corner_clip_threshold: float = DEFAULT_CORNER_CLIP_MILES,
) -> list[dict[str, Any]]:
    """Runs all ten detectors, persists every finding to ifta_exceptions,
    and raises one queue item per finding. Never auto-resolves anything —
    that's the point."""
    from dispatch.common.ids import new_ulid

    start, end = quarter_bounds(worksheet["quarter"])
    findings: list[dict[str, Any]] = []
    findings += fuel_no_miles(worksheet)
    findings += miles_no_fuel_gap(worksheet)
    findings += fleet_mpg_out_of_band(worksheet, band=mpg_band)
    findings += odometer_discontinuity(ro_conn, start, end)
    findings += active_truck_days_no_mileage(ro_conn, start, end)
    findings += broken_evidence_linkage(ro_conn, spine, start, end)
    findings += late_arrival_closed_quarter(conn, ro_conn, worksheet["fuel_type"])
    findings += rate_version_mismatch(conn, worksheet)
    findings += reefer_in_propulsion(ro_conn)
    findings += corner_clipping(worksheet, threshold=corner_clip_threshold)

    persisted = []
    for finding in findings:
        exception_id = new_ulid()
        queue_item = queue.create(
            type="exception",
            source_worker="ifta",
            priority="today",
            subject=f"IFTA exception ({finding['exception_type']}): {finding['detail'][:80]}",
            payload_refs=finding["related_record_ids"],
        )
        conn.execute(
            """
            INSERT INTO ifta_exceptions (
                ifta_exception_id, ifta_worksheet_id, exception_type, detail,
                related_record_ids, detected_at, queue_item_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                exception_id,
                worksheet["ifta_worksheet_id"],
                finding["exception_type"],
                finding["detail"],
                json.dumps(finding["related_record_ids"]),
                _utc_now_iso(),
                queue_item["queue_item_id"],
            ),
        )
        persisted.append({**finding, "ifta_exception_id": exception_id, "queue_item_id": queue_item["queue_item_id"]})

    return persisted
