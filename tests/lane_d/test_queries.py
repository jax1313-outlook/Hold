"""queries.py correctness -- checked against fixture data produced by
Lane A's real EvidenceSpine and Lane C's real Router/WorksheetEngine (see
tests/fixtures/README.md), and cross-checked with independent SQL over
the read-only connection so the aggregation logic can't silently agree
with itself."""
from __future__ import annotations

from datetime import date

from dispatch.reports import queries


def test_fuel_spend_query_totals_match_fixture_data(reports_ro_conn, seeded_pipeline_data):
    result = queries.fuel_spend_query(
        reports_ro_conn, date_from=date(2026, 8, 1), date_to=date(2026, 8, 31)
    )
    assert result["total_amount"] == 650.0  # 400.0 (TX) + 250.0 (MO)
    assert result["total_gallons"] == 160.0  # 100.0 + 60.0
    breakdown = {row["jurisdiction"]: row for row in result["breakdown"]}
    assert breakdown["TX"]["amount"] == 400.0
    assert breakdown["TX"]["gallons"] == 100.0
    assert breakdown["MO"]["amount"] == 250.0
    assert breakdown["MO"]["gallons"] == 60.0


def test_fuel_spend_query_fidelity_vs_independent_sql(reports_ro_conn, seeded_pipeline_data):
    result = queries.fuel_spend_query(
        reports_ro_conn, date_from=date(2026, 8, 1), date_to=date(2026, 8, 31)
    )
    independent_total = reports_ro_conn.execute(
        "SELECT SUM(total_amount), SUM(gallons_normalized) FROM fuel_records"
    ).fetchone()
    assert result["total_amount"] == independent_total[0]
    assert result["total_gallons"] == independent_total[1]


def test_fuel_spend_query_filters_by_date_range(reports_ro_conn, seeded_pipeline_data):
    result = queries.fuel_spend_query(
        reports_ro_conn, date_from=date(2026, 8, 1), date_to=date(2026, 8, 1)
    )
    assert result["total_amount"] == 400.0  # only the 8/1 TX purchase


def test_fuel_spend_query_filters_by_unit_number_and_jurisdiction(reports_ro_conn, seeded_pipeline_data):
    none_result = queries.fuel_spend_query(
        reports_ro_conn, date_from=date(2026, 8, 1), date_to=date(2026, 8, 31), unit_number="T-999"
    )
    assert none_result["total_amount"] == 0
    assert none_result["breakdown"] == []

    tx_only = queries.fuel_spend_query(
        reports_ro_conn, date_from=date(2026, 8, 1), date_to=date(2026, 8, 31), jurisdiction="TX"
    )
    assert tx_only["total_amount"] == 400.0


def test_expense_summary_query_breakdown_by_category(reports_ro_conn, seeded_pipeline_data):
    # The router creates an ExpenseRecord for every line, including fuel
    # (Decision D1's dual-record fuel) -- so "all expenses" here is the
    # two fuel purchases (category "fuel") plus the one meal, not just
    # the meal alone.
    result = queries.expense_summary_query(
        reports_ro_conn, date_from=date(2026, 8, 1), date_to=date(2026, 8, 31)
    )
    assert result["total_amount"] == 672.0  # 400.0 + 250.0 (fuel) + 22.0 (meals)
    assert result["breakdown"] == [
        {"category": "fuel", "amount": 650.0},
        {"category": "meals", "amount": 22.0},
    ]
    assert result["line_items"] == []


def test_expense_summary_query_category_filter_returns_drilldown_line_items(reports_ro_conn, seeded_pipeline_data):
    result = queries.expense_summary_query(
        reports_ro_conn, date_from=date(2026, 8, 1), date_to=date(2026, 8, 31), category="meals"
    )
    assert result["breakdown"] == []
    assert len(result["line_items"]) == 1
    assert result["line_items"][0]["vendor_name"] == "Truck Stop Diner"
    assert result["line_items"][0]["amount"] == 22.0


def test_ifta_position_query_returns_none_when_no_worksheet_for_quarter(reports_ro_conn, seeded_pipeline_data):
    assert queries.ifta_position_query(reports_ro_conn, quarter="2026-Q3") is None


def test_ifta_position_query_reads_stored_values_exactly(reports_ro_conn, seeded_ifta_worksheet):
    result = queries.ifta_position_query(reports_ro_conn, quarter="2026-Q3")
    assert result is not None
    assert result["quarter"] == "2026-Q3"
    assert len(result["worksheets"]) == 1
    stored = result["worksheets"][0]
    assert stored["fleet_mpg"] == seeded_ifta_worksheet["fleet_mpg"]
    assert stored["total_net_tax"] == seeded_ifta_worksheet["total_net_tax"]
    assert stored["status"] == seeded_ifta_worksheet["status"]
    assert result["total_net_tax"] == seeded_ifta_worksheet["total_net_tax"]

    stored_lines = {line["jurisdiction"]: line for line in seeded_ifta_worksheet["lines"]}
    for line in result["lines"]:
        expected = stored_lines[line["jurisdiction"]]
        assert line["miles"] == expected["miles"]
        assert line["taxable_gallons"] == expected["taxable_gallons"]
        assert line["net_tax"] == expected["net_tax"]
        assert line["rate"] == expected["rate"]


def test_ifta_position_query_exception_count_is_zero_with_none_recorded(reports_ro_conn, seeded_ifta_worksheet):
    result = queries.ifta_position_query(reports_ro_conn, quarter="2026-Q3")
    assert result["exception_count"] == 0


def test_pending_review_count_is_zero_with_no_queue_items(reports_ro_conn, db_conn):
    assert queries.pending_review_count(reports_ro_conn) == 0


def test_pending_review_count_counts_open_and_in_review_only(reports_ro_conn, db_conn):
    db_conn.execute(
        "INSERT INTO queue_items (queue_item_id, type, source_worker, created_at, priority, subject, status) "
        "VALUES ('q1', 'exception', 'ifta', 'now', 'today', 'x', 'open')"
    )
    db_conn.execute(
        "INSERT INTO queue_items (queue_item_id, type, source_worker, created_at, priority, subject, status) "
        "VALUES ('q2', 'exception', 'ifta', 'now', 'today', 'x', 'in_review')"
    )
    db_conn.execute(
        "INSERT INTO queue_items (queue_item_id, type, source_worker, created_at, priority, subject, status) "
        "VALUES ('q3', 'exception', 'ifta', 'now', 'today', 'x', 'resolved')"
    )
    assert queries.pending_review_count(reports_ro_conn) == 2
