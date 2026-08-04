"""IFTA worksheet engine — computation spec 3.5, verbatim.

Per quarter, per fuel type: fleet_mpg = total_miles_all_jurisdictions /
total_tractor_gallons_normalized. Per jurisdiction J: taxable_gallons_J =
miles_J / fleet_mpg; net_tax_J = taxable_gallons_J × rate_J −
tax_paid_gallons_J × rate_J (+ a surcharge line when the rate table
carries one). Rates come only from the versioned rate_tables; the
worksheet stores which version it used. No fabricated rate is ever
substituted for a missing one — MissingRateError instead.
"""
from __future__ import annotations

import calendar
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

        miles_by_jurisdiction, total_miles = self._aggregate_mileage(start, end)
        gallons_by_jurisdiction, total_tractor_gallons = self._aggregate_fuel(start, end, fuel_type)

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
                self._conn,
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
                }
            )

        if missing_rates:
            raise MissingRateError(missing_rates, quarter, fuel_type, rate_table_version)

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
                    taxable_gallons, tax_paid_gallons, rate, surcharge, net_tax
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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

    def _aggregate_mileage(self, start: date, end: date) -> tuple[dict[str, float], float]:
        rows = self._ro_conn.execute(
            "SELECT jurisdiction, miles, period_start, period_end FROM mileage_records"
        ).fetchall()
        by_jurisdiction: dict[str, float] = {}
        total = 0.0
        for row in rows:
            period_start = date.fromisoformat(row["period_start"])
            period_end = date.fromisoformat(row["period_end"])
            if period_start >= start and period_end <= end:
                by_jurisdiction[row["jurisdiction"]] = by_jurisdiction.get(row["jurisdiction"], 0.0) + row["miles"]
                total += row["miles"]
        return by_jurisdiction, total

    def _aggregate_fuel(
        self, start: date, end: date, fuel_type: str
    ) -> tuple[dict[str, float], float]:
        rows = self._ro_conn.execute(
            """
            SELECT jurisdiction, gallons_normalized, purchase_date, tractor_or_reefer
            FROM fuel_records WHERE fuel_type = ?
            """,
            (fuel_type,),
        ).fetchall()
        by_jurisdiction: dict[str, float] = {}
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
                total += row["gallons_normalized"]
        return by_jurisdiction, total
