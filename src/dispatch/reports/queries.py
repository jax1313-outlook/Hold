"""The actual SQL each report type runs — aggregate/group-by only.

REPORTS_CHARTER_v1.md's second bright line: "Reports may sum, average,
count, and group-by over stored records. It may never compute tax,
classify, apply accrual logic, or reclassify anything on the fly."
`ifta_position_query` is the one that matters most here: it reads
`ifta_worksheets`/`ifta_worksheet_lines` values exactly as stored and
performs no arithmetic on them beyond formatting — fleet_mpg and net_tax
are read columns, never recomputed.

Every function here takes a read-only connection (dispatch.reports.readonly)
and returns plain dicts — no other lane's business logic is imported.
"""
from __future__ import annotations

import sqlite3
from datetime import date
from typing import Any


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    """fuel_records/expense_records (Lane C's receipt side) and
    ifta_worksheets (Lane C's IFTA side) are created by those lanes' own
    install_schema() the first time they actually run something, not by
    dispatch.common.db.bootstrap() -- so on a fresh database where no
    receipt has been processed or no worksheet built yet, the table
    genuinely doesn't exist. That's a "no data" state, not an error: a
    report screen must never 500 just because nothing has happened yet
    (REPORTS_CHARTER_v1.md's "no report renders without complete data").
    Querying sqlite_master is itself a read, safe on the mode=ro connection
    regardless of which tables happen to exist."""
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table_name,)
    ).fetchone()
    return row is not None


def fuel_spend_query(
    conn: sqlite3.Connection,
    *,
    date_from: date,
    date_to: date,
    unit_number: str | None = None,
    jurisdiction: str | None = None,
) -> dict[str, Any]:
    if not _table_exists(conn, "fuel_records"):
        return {"total_amount": 0, "total_gallons": 0, "breakdown": []}

    where = ["purchase_date BETWEEN ? AND ?"]
    params: list[Any] = [date_from.isoformat(), date_to.isoformat()]
    if unit_number:
        where.append("unit_number = ?")
        params.append(unit_number)
    if jurisdiction:
        where.append("jurisdiction = ?")
        params.append(jurisdiction)
    clause = " AND ".join(where)

    totals = conn.execute(
        f"SELECT COALESCE(SUM(total_amount), 0) AS total_amount, "
        f"COALESCE(SUM(gallons_normalized), 0) AS total_gallons "
        f"FROM fuel_records WHERE {clause}",
        params,
    ).fetchone()

    breakdown = conn.execute(
        f"SELECT jurisdiction, SUM(total_amount) AS amount, SUM(gallons_normalized) AS gallons "
        f"FROM fuel_records WHERE {clause} GROUP BY jurisdiction ORDER BY jurisdiction",
        params,
    ).fetchall()

    return {
        "total_amount": totals["total_amount"],
        "total_gallons": totals["total_gallons"],
        "breakdown": [dict(row) for row in breakdown],
    }


def expense_summary_query(
    conn: sqlite3.Connection,
    *,
    date_from: date,
    date_to: date,
    unit_number: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    if not _table_exists(conn, "expense_records"):
        return {"total_amount": 0, "breakdown": [], "line_items": []}

    where = ["purchase_date BETWEEN ? AND ?"]
    params: list[Any] = [date_from.isoformat(), date_to.isoformat()]
    if unit_number:
        where.append("unit_number = ?")
        params.append(unit_number)
    if category:
        where.append("category = ?")
        params.append(category)
    clause = " AND ".join(where)

    total = conn.execute(
        f"SELECT COALESCE(SUM(amount), 0) AS total_amount FROM expense_records WHERE {clause}",
        params,
    ).fetchone()["total_amount"]

    result: dict[str, Any] = {"total_amount": total, "breakdown": [], "line_items": []}

    if category:
        # Category drill-down: the design review's "category drill-down
        # shows the line items" -- when a caller has already narrowed to
        # one category, show what's actually in it rather than a
        # one-row breakdown of itself.
        line_items = conn.execute(
            f"SELECT vendor_name, purchase_date, amount, line_description "
            f"FROM expense_records WHERE {clause} ORDER BY purchase_date, vendor_name",
            params,
        ).fetchall()
        result["line_items"] = [dict(row) for row in line_items]
    else:
        breakdown = conn.execute(
            f"SELECT category, SUM(amount) AS amount FROM expense_records WHERE {clause} "
            f"GROUP BY category ORDER BY category",
            params,
        ).fetchall()
        result["breakdown"] = [dict(row) for row in breakdown]

    return result


def ifta_position_query(conn: sqlite3.Connection, *, quarter: str) -> dict[str, Any] | None:
    if not _table_exists(conn, "ifta_worksheets"):
        return None  # no worksheet has ever been built -- same "no data" contract as an empty result

    worksheets = conn.execute(
        "SELECT * FROM ifta_worksheets WHERE quarter = ? ORDER BY fuel_type", (quarter,)
    ).fetchall()
    if not worksheets:
        return None  # no report renders without complete data behind it -- caller shows "no data yet"

    worksheet_ids = [row["ifta_worksheet_id"] for row in worksheets]
    placeholders = ",".join("?" for _ in worksheet_ids)

    lines = conn.execute(
        f"""
        SELECT l.jurisdiction, l.miles, l.taxable_gallons, l.tax_paid_gallons,
               l.rate, l.surcharge, l.net_tax, w.fuel_type, w.status
        FROM ifta_worksheet_lines l
        JOIN ifta_worksheets w ON w.ifta_worksheet_id = l.ifta_worksheet_id
        WHERE l.ifta_worksheet_id IN ({placeholders})
        ORDER BY w.fuel_type, l.jurisdiction
        """,
        worksheet_ids,
    ).fetchall()

    exception_count = conn.execute(
        f"SELECT COUNT(*) FROM ifta_exceptions WHERE ifta_worksheet_id IN ({placeholders})",
        worksheet_ids,
    ).fetchone()[0]

    return {
        "quarter": quarter,
        "worksheets": [
            {
                "fuel_type": row["fuel_type"],
                "fleet_mpg": row["fleet_mpg"],  # read exactly as stored, never recomputed
                "status": row["status"],
                "rate_table_version": row["rate_table_version"],
                "total_net_tax": row["total_net_tax"],  # read exactly as stored, never recomputed
            }
            for row in worksheets
        ],
        "lines": [dict(line) for line in lines],
        "total_net_tax": sum(row["total_net_tax"] for row in worksheets),
        "exception_count": exception_count,
    }


def pending_review_count(conn: sqlite3.Connection) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM queue_items WHERE status IN ('open', 'in_review')"
    ).fetchone()[0]
