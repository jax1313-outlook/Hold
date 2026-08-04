"""ifta_position_query returning None (no worksheet for the quarter yet)
must never crash the app or render a fabricated zero -- REPORTS_CHARTER_v1.md:
"no report renders without complete data behind it." Covers both the
query layer directly and the real Flask routes on top of it."""
from __future__ import annotations

import pytest

from dispatch.reports import queries
from dispatch.reports.app import create_app


def test_ifta_position_query_returns_none_with_no_worksheet(reports_ro_conn):
    assert queries.ifta_position_query(reports_ro_conn, quarter="2099-Q1") is None


def test_ifta_position_query_does_not_crash_when_ifta_worksheets_table_never_existed(reports_ro_conn, db_conn):
    # Regression: ifta_worksheets is created lazily by Lane C's own
    # WorksheetEngine, not by dispatch.common.db.bootstrap(). On a fresh
    # database where no worksheet has ever been built, the table doesn't
    # exist at all yet -- that must read as "no data", not crash.
    exists = db_conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'ifta_worksheets'"
    ).fetchone()
    assert exists is None
    assert queries.ifta_position_query(reports_ro_conn, quarter="2026-Q3") is None


def test_fuel_spend_and_expense_summary_do_not_crash_when_receipt_tables_never_existed(reports_ro_conn, db_conn):
    # Same bug class, one layer down: fuel_records/expense_records are
    # created lazily by Lane C's Router, not by bootstrap() either.
    for table in ("fuel_records", "expense_records"):
        exists = db_conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
        ).fetchone()
        assert exists is None

    from datetime import date

    fuel_result = queries.fuel_spend_query(reports_ro_conn, date_from=date(2026, 1, 1), date_to=date(2026, 12, 31))
    assert fuel_result == {"total_amount": 0, "total_gallons": 0, "breakdown": []}

    expense_result = queries.expense_summary_query(
        reports_ro_conn, date_from=date(2026, 1, 1), date_to=date(2026, 12, 31)
    )
    assert expense_result == {"total_amount": 0, "breakdown": [], "line_items": []}


def test_run_route_shows_no_data_page_instead_of_crashing(seeded_library):
    app = create_app(seeded_library)
    with app.test_client() as client:
        resp = client.get("/run", query_string={"report_type": "ifta_position", "date_range": "this_month"})
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "No data behind this report yet" in body
    assert "nothing fabricated" in body
    # and definitely no fabricated $0.00 answer masquerading as real data
    assert "big-number" not in body


def test_save_route_refuses_to_save_a_report_with_no_data(seeded_library):
    app = create_app(seeded_library)
    with app.test_client() as client:
        resp = client.post("/save", data={"report_type": "ifta_position", "date_range": "this_month"})
    assert resp.status_code == 400


def test_ifta_position_available_once_a_real_worksheet_exists(seeded_library, seeded_ifta_worksheet):
    app = create_app(seeded_library)
    with app.test_client() as client:
        resp = client.get(
            "/run", query_string={"report_type": "ifta_position", "date_range": "custom",
                                   "custom_from": "2026-09-01", "custom_to": "2026-09-30"},
        )
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "No data behind this report yet" not in body
    assert "Estimated Net Tax" in body
