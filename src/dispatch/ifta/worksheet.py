"""IFTA worksheet engine — computation spec 3.5, verbatim.

Per quarter, per fuel type: fleet_mpg = total_miles_all_jurisdictions /
total_tractor_gallons_normalized. Per jurisdiction J: taxable_gallons_J =
miles_J / fleet_mpg; net_tax_J = taxable_gallons_J × rate_J −
tax_paid_gallons_J × rate_J (+ a surcharge line when the rate table
carries one). Rates come only from the versioned rate_tables; the
worksheet stores which version it used. No fabricated rate is ever
substituted for a missing one — MissingRateError instead.

WorksheetEngine.build() computes this and persists it. The module-level
preview() below computes the identical thing from a read-only connection
and never persists anything — approved in principle 2026-08-04
(IFTA_CLERK_BLUEPRINT_v1 section 6.1). Both call the same
_aggregate_mileage/_aggregate_fuel/_compute_worksheet_lines so the
arithmetic itself exists in exactly one place.
"""
from __future__ import annotations

import calendar
import json
import re
import sqlite3
from datetime import date, datetime, timezone
from typing import Any

from dispatch.common.ids import new_ulid
from dispatch.ifta import rates
from dispatch.ifta.db import install_schema

_QUARTER_PATTERN = re.compile(r"^(\d{4})-Q([1-4])$")
_QUARTER_MONTHS = {1: (1, 3), 2: (4, 6), 3: (7, 9), 4: (10, 12)}


class WorksheetError(ValueError):
    """Base class for worksheet-building failures."""


class InvalidQuarterError(WorksheetError):
    pass


class MissingRateError(WorksheetError):
    def __init__(self, jurisdictions: list[str], quarter: str, fuel_type: str, rate_table_version: str):
        super().__init__(
            f"no rate found for jurisdiction(s) {sorted(jurisdictions)} in "
            f"{quarter}/{fuel_type}/{rate_table_version!r} — refusing to fabricate one"
        )
        self.jurisdictions = jurisdictions


class InsufficientDataError(WorksheetError):
    pass


class WorksheetNotFoundError(WorksheetError):
    pass


def quarter_bounds(quarter: str) -> tuple[date, date]:
    match = _QUARTER_PATTERN.match(quarter)
    if not match:
        raise InvalidQuarterError(f"quarter must look like '2026-Q2', got {quarter!r}")
    year, q = int(match.group(1)), int(match.group(2))
    start_month, end_month = _QUARTER_MONTHS[q]
    start = date(year, start_month, 1)
    end_day = calendar.monthrange(year, end_month)[1]
    end = date(year, end_month, end_day)
    return start, end


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table_name,)
    ).fetchone()
    return row is not None


def _aggregate_mileage(
    conn: sqlite3.Connection, start: date, end: date
) -> tuple[dict[str, float], float, dict[str, list[str]]]:
    """Module-level, read-only-safe: takes whichever connection the caller
    has (WorksheetEngine's read_only_conn, or preview()'s own), never a
    self reference. A genuinely fresh database with no mileage ever
    recorded has no mileage_records table at all -- that's an absence of
    data, not an error, so it reads back as (empty, 0.0, empty) rather
    than a raw sqlite3.OperationalError.

    Also returns which mileage_record_id contributed to each
    jurisdiction's total -- provenance alongside the sum, not a second
    computation of it, so the Archive Package (package.py's sealed
    bundle) can trace a number back to the real records behind it."""
    if not _table_exists(conn, "mileage_records"):
        return {}, 0.0, {}
    rows = conn.execute(
        "SELECT mileage_record_id, jurisdiction, miles, period_start, period_end FROM mileage_records"
    ).fetchall()
    by_jurisdiction: dict[str, float] = {}
    record_ids_by_jurisdiction: dict[str, list[str]] = {}
    total = 0.0
    for row in rows:
        period_start = date.fromisoformat(row["period_start"])
        period_end = date.fromisoformat(row["period_end"])
        if period_start >= start and period_end <= end:
            by_jurisdiction[row["jurisdiction"]] = by_jurisdiction.get(row["jurisdiction"], 0.0) + row["miles"]
            record_ids_by_jurisdiction.setdefault(row["jurisdiction"], []).append(row["mileage_record_id"])
            total += row["miles"]
    return by_jurisdiction, total, record_ids_by_jurisdiction


def _aggregate_fuel(
    conn: sqlite3.Connection, start: date, end: date, fuel_type: str
) -> tuple[dict[str, float], float, dict[str, list[str]]]:
    """Same reasoning as _aggregate_mileage, including the added
    fuel_record_id provenance: no fuel_records table yet reads back as no
    fuel recorded yet, not a crash."""
    if not _table_exists(conn, "fuel_records"):
        return {}, 0.0, {}
    rows = conn.execute(
        """
        SELECT fuel_record_id, jurisdiction, gallons_normalized, purchase_date, tractor_or_reefer
        FROM fuel_records WHERE fuel_type = ?
        """,
        (fuel_type,),
    ).fetchall()
    by_jurisdiction: dict[str, float] = {}
    record_ids_by_jurisdiction: dict[str, list[str]] = {}
    total = 0.0
    for row in rows:
        purchase_date = date.fromisoformat(row["purchase_date"])
        # tractor_or_reefer == 'tractor' should always be true here (the
        # router never creates a reefer-flagged fuel_record — see
        # router.ReeferMisroutedError) but this filter is the worksheet
        # engine's own defense-in-depth, matching exception #9's intent.
        if start <= purchase_date <= end and row["tractor_or_reefer"] == "tractor":
            by_jurisdiction[row["jurisdiction"]] = (
                by_jurisdiction.get(row["jurisdiction"], 0.0) + row["gallons_normalized"]
            )
            record_ids_by_jurisdiction.setdefault(row["jurisdiction"], []).append(row["fuel_record_id"])
            total += row["gallons_normalized"]
    return by_jurisdiction, total, record_ids_by_jurisdiction


def _compute_worksheet_lines(
    conn: sqlite3.Connection,
    *,
    quarter: str,
    fuel_type: str,
    rate_table_version: str,
    miles_by_jurisdiction: dict[str, float],
    total_miles: float,
    gallons_by_jurisdiction: dict[str, float],
    total_tractor_gallons: float,
    mileage_record_ids_by_jurisdiction: dict[str, list[str]],
    fuel_record_ids_by_jurisdiction: dict[str, list[str]],
) -> tuple[float, list[dict[str, Any]]]:
    """Computation spec 3.5 itself, verbatim -- the one place fleet_mpg,
    taxable_gallons, and net_tax get computed. build() (which persists the
    result) and preview() (which does not) both call this, so the
    arithmetic exists exactly once rather than being reimplemented for the
    preview path. conn is only ever read from here (rate lookups) --
    build() passes its write connection, preview() its read-only one, and
    either is safe against this function's own access pattern.

    mileage_record_ids_by_jurisdiction/fuel_record_ids_by_jurisdiction
    carry through unchanged from _aggregate_mileage/_aggregate_fuel into
    each line's related_record_ids -- provenance, not arithmetic; the
    net_tax computation below never reads either dict."""
    if total_tractor_gallons <= 0:
        raise InsufficientDataError(
            f"no tractor {fuel_type} gallons recorded for {quarter}; cannot compute fleet_mpg"
        )
    if total_miles <= 0:
        raise InsufficientDataError(
            f"no mileage recorded within {quarter}; cannot compute fleet_mpg"
        )
    fleet_mpg = total_miles / total_tractor_gallons

    jurisdictions = sorted(set(miles_by_jurisdiction) | set(gallons_by_jurisdiction))
    missing_rates: list[str] = []
    lines: list[dict[str, Any]] = []

    for jurisdiction in jurisdictions:
        miles_j = miles_by_jurisdiction.get(jurisdiction, 0.0)
        tax_paid_gallons_j = gallons_by_jurisdiction.get(jurisdiction, 0.0)
        taxable_gallons_j = miles_j / fleet_mpg

        rate_row = rates.get_rate(
            conn,
            jurisdiction=jurisdiction,
            quarter=quarter,
            fuel_type=fuel_type,
            source_version=rate_table_version,
        )
        if rate_row is None:
            missing_rates.append(jurisdiction)
            continue

        rate = rate_row["rate"]
        surcharge = rate_row.get("surcharge")
        net_tax = taxable_gallons_j * rate - tax_paid_gallons_j * rate
        if surcharge:
            net_tax += taxable_gallons_j * surcharge

        lines.append(
            {
                "jurisdiction": jurisdiction,
                "miles": miles_j,
                "taxable_gallons": taxable_gallons_j,
                "tax_paid_gallons": tax_paid_gallons_j,
                "rate": rate,
                "surcharge": surcharge,
                "net_tax": net_tax,
                "related_record_ids": {
                    "mileage_record_ids": sorted(mileage_record_ids_by_jurisdiction.get(jurisdiction, [])),
                    "fuel_record_ids": sorted(fuel_record_ids_by_jurisdiction.get(jurisdiction, [])),
                },
            }
        )

    if missing_rates:
        raise MissingRateError(missing_rates, quarter, fuel_type, rate_table_version)

    return fleet_mpg, lines


def preview(read_only_conn: sqlite3.Connection, *, quarter: str, fuel_type: str, rate_table_version: str) -> dict[str, Any]:
    """A live, non-persisting estimate of what build() would produce right
    now if called this instant -- approved in principle 2026-08-04
    (IFTA_CLERK_BLUEPRINT_v1 §6.1), under six conditions. Each is
    structural here, not merely a convention this function happens to
    follow:

    1. No database writes. preview() is a module-level function taking
       only a read-only connection as its sole parameter -- there is no
       write-capable connection anywhere in its scope to write with.
    2. No worksheet IDs. new_ulid() is never called on this path.
    3. No audit status changes. Nothing here touches ifta_worksheets or
       ifta_worksheet_lines, and install_schema() is never called against
       a write connection here.
    4. No approval path activation. preview() never receives or
       constructs a QueueStore; dispatch.ifta.package is never imported
       here.
    5. Clearly labeled PREVIEW. The returned dict carries
       "status": "preview" and "is_preview": True.
    6. Cannot be mistaken for a filed worksheet. Follows directly from 2,
       3, and 5 together: no id, no queue link, and an explicit label a
       caller would have to deliberately discard.

    Shares _aggregate_mileage/_aggregate_fuel/_compute_worksheet_lines
    with build() so computation spec 3.5 exists in exactly one place --
    this function only ever skips the INSERTs build() does afterward.

    rate_tables not existing yet (no rate has ever been entered against
    this database) is data that isn't there yet, same as fuel/mileage
    with no table -- InsufficientDataError, not a raw crash from a
    read-only connection hitting install_schema()'s CREATE TABLE."""
    if not _table_exists(read_only_conn, "rate_tables"):
        raise InsufficientDataError(
            f"no rate table exists yet for {rate_table_version!r} -- no rate has "
            "ever been entered against this database"
        )

    start, end = quarter_bounds(quarter)
    miles_by_jurisdiction, total_miles, mileage_record_ids_by_jurisdiction = _aggregate_mileage(
        read_only_conn, start, end
    )
    gallons_by_jurisdiction, total_tractor_gallons, fuel_record_ids_by_jurisdiction = _aggregate_fuel(
        read_only_conn, start, end, fuel_type
    )

    fleet_mpg, lines = _compute_worksheet_lines(
        read_only_conn,
        quarter=quarter,
        fuel_type=fuel_type,
        rate_table_version=rate_table_version,
        miles_by_jurisdiction=miles_by_jurisdiction,
        total_miles=total_miles,
        gallons_by_jurisdiction=gallons_by_jurisdiction,
        total_tractor_gallons=total_tractor_gallons,
        mileage_record_ids_by_jurisdiction=mileage_record_ids_by_jurisdiction,
        fuel_record_ids_by_jurisdiction=fuel_record_ids_by_jurisdiction,
    )
    total_net_tax = sum(line["net_tax"] for line in lines)

    return {
        "status": "preview",
        "is_preview": True,
        "quarter": quarter,
        "fuel_type": fuel_type,
        "rate_table_version": rate_table_version,
        "fleet_mpg": fleet_mpg,
        "total_net_tax": total_net_tax,
        "lines": lines,
        "generated_at": _utc_now_iso(),
    }


def live_fleet_mpg_estimate(read_only_conn: sqlite3.Connection, *, quarter: str, fuel_type: str) -> float | None:
    """A live fleet_mpg estimate for this quarter/fuel_type right now --
    deliberately independent of any rate table, unlike preview(), since
    fleet_mpg = total_miles / total_tractor_gallons never involves a
    rate. Built for dispatch.ifta_clerk's mileage-entry route: give
    early, non-blocking plausibility feedback (against the same
    DEFAULT_MPG_BAND exceptions.py's fleet_mpg_out_of_band detector
    already uses) the moment mileage is entered, without needing a rate
    table to exist yet.

    Returns None on insufficient data (no mileage, or no tractor fuel,
    recorded yet) rather than raising -- this is a soft signal, not a
    worksheet build; a caller with nothing to estimate from should just
    skip the check, never fabricate a number or block the entry that was
    just made. Shares _aggregate_mileage/_aggregate_fuel with build() and
    preview() so this is the same computation, not a second one."""
    start, end = quarter_bounds(quarter)
    _, total_miles, _ = _aggregate_mileage(read_only_conn, start, end)
    _, total_tractor_gallons, _ = _aggregate_fuel(read_only_conn, start, end, fuel_type)
    if total_miles <= 0 or total_tractor_gallons <= 0:
        return None
    return total_miles / total_tractor_gallons


class WorksheetEngine:
    """write_conn owns the ifta_* tables (read-write); read_only_conn is a
    SQLite mode=ro connection to the same database file, used for every
    read of fuel_records/mileage_records — the enforcement mechanism
    IFTA_CONSTITUTION_v1 names for source-immutability."""

    def __init__(self, write_conn: sqlite3.Connection, read_only_conn: sqlite3.Connection):
        self._conn = write_conn
        self._ro_conn = read_only_conn
        install_schema(self._conn)

    def build(self, *, quarter: str, fuel_type: str, rate_table_version: str) -> dict[str, Any]:
        start, end = quarter_bounds(quarter)

        miles_by_jurisdiction, total_miles, mileage_record_ids_by_jurisdiction = _aggregate_mileage(
            self._ro_conn, start, end
        )
        gallons_by_jurisdiction, total_tractor_gallons, fuel_record_ids_by_jurisdiction = _aggregate_fuel(
            self._ro_conn, start, end, fuel_type
        )

        fleet_mpg, lines = _compute_worksheet_lines(
            self._conn,
            quarter=quarter,
            fuel_type=fuel_type,
            rate_table_version=rate_table_version,
            miles_by_jurisdiction=miles_by_jurisdiction,
            total_miles=total_miles,
            gallons_by_jurisdiction=gallons_by_jurisdiction,
            total_tractor_gallons=total_tractor_gallons,
            mileage_record_ids_by_jurisdiction=mileage_record_ids_by_jurisdiction,
            fuel_record_ids_by_jurisdiction=fuel_record_ids_by_jurisdiction,
        )

        total_net_tax = sum(line["net_tax"] for line in lines)
        worksheet_id = new_ulid()

        self._conn.execute(
            """
            INSERT INTO ifta_worksheets (
                ifta_worksheet_id, quarter, fuel_type, fleet_mpg, rate_table_version,
                status, total_net_tax, created_at, sealed_at, queue_item_id, schema_version
            ) VALUES (?, ?, ?, ?, ?, 'draft', ?, ?, NULL, NULL, '1.0')
            """,
            (worksheet_id, quarter, fuel_type, fleet_mpg, rate_table_version, total_net_tax, _utc_now_iso()),
        )
        for line in lines:
            self._conn.execute(
                """
                INSERT INTO ifta_worksheet_lines (
                    ifta_worksheet_line_id, ifta_worksheet_id, jurisdiction, miles,
                    taxable_gallons, tax_paid_gallons, rate, surcharge, net_tax,
                    related_record_ids
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_ulid(),
                    worksheet_id,
                    line["jurisdiction"],
                    line["miles"],
                    line["taxable_gallons"],
                    line["tax_paid_gallons"],
                    line["rate"],
                    line["surcharge"],
                    line["net_tax"],
                    json.dumps(line["related_record_ids"]),
                ),
            )

        return self.get(worksheet_id)

    def get(self, ifta_worksheet_id: str) -> dict[str, Any]:
        row = self._conn.execute(
            "SELECT * FROM ifta_worksheets WHERE ifta_worksheet_id = ?", (ifta_worksheet_id,)
        ).fetchone()
        if row is None:
            raise WorksheetNotFoundError(f"no worksheet {ifta_worksheet_id!r}")
        worksheet = dict(row)
        lines = self._conn.execute(
            "SELECT * FROM ifta_worksheet_lines WHERE ifta_worksheet_id = ? ORDER BY jurisdiction",
            (ifta_worksheet_id,),
        ).fetchall()
        worksheet["lines"] = [dict(line) for line in lines]
        return worksheet


def latest_worksheet_for(conn: sqlite3.Connection, *, quarter: str, fuel_type: str) -> dict[str, Any] | None:
    """The most recently created worksheet for this quarter/fuel_type, if
    any -- None if none exists yet. A plain SELECT, safe against either a
    write or a read-only connection, and against a genuinely fresh
    database with no ifta_worksheets table at all.

    get() alone can't answer "does a real worksheet already exist for
    this quarter?" -- it requires already knowing the id. This is the
    read a caller needs before choosing between a real worksheet's stored
    numbers and preview()'s live estimate (IFTA_CLERK_BLUEPRINT_v1
    section 6's rule: never show both at once for the same quarter)."""
    if not _table_exists(conn, "ifta_worksheets"):
        return None
    row = conn.execute(
        # created_at is only second-precision (_utc_now_iso); ifta_worksheet_id
        # (a ULID) sorts lexicographically by millisecond creation time, so it's
        # the reliable tie-breaker for two worksheets built within the same second.
        "SELECT * FROM ifta_worksheets WHERE quarter = ? AND fuel_type = ? "
        "ORDER BY created_at DESC, ifta_worksheet_id DESC LIMIT 1",
        (quarter, fuel_type),
    ).fetchone()
    if row is None:
        return None
    worksheet = dict(row)
    lines = conn.execute(
        "SELECT * FROM ifta_worksheet_lines WHERE ifta_worksheet_id = ? ORDER BY jurisdiction",
        (worksheet["ifta_worksheet_id"],),
    ).fetchall()
    worksheet["lines"] = [dict(line) for line in lines]
    return worksheet
