"""REPORTS_CHARTER_v1.md bright line #1: "Database connection opened
READ-ONLY (mode=ro) everywhere except one narrow print-queue/snapshot
writer. Any other write attempt must fail." Same proof technique as
tests/lane_c/test_worksheet.py::test_read_only_connection_rejects_any_write
-- across every table this lane touches, not just print_queue."""
from __future__ import annotations

import sqlite3

import pytest


def test_readonly_connection_rejects_write_to_print_queue(reports_writer, reports_ro_conn):
    with pytest.raises(sqlite3.OperationalError):
        reports_ro_conn.execute(
            "INSERT INTO print_queue (print_queue_id, report_type, template_version, as_of, "
            "period_label, snapshot_path, saved_at) VALUES ('x', 'fuel_spend', '1', 'now', "
            "'Today', 'x.html', 'now')"
        )


def test_readonly_connection_rejects_write_to_fuel_records(reports_ro_conn, seeded_pipeline_data):
    with pytest.raises(sqlite3.OperationalError):
        reports_ro_conn.execute("UPDATE fuel_records SET vendor_name = 'tampered' WHERE 1=1")
    with pytest.raises(sqlite3.OperationalError):
        reports_ro_conn.execute("DELETE FROM fuel_records WHERE 1=1")


def test_readonly_connection_rejects_write_to_expense_records(reports_ro_conn, seeded_pipeline_data):
    with pytest.raises(sqlite3.OperationalError):
        reports_ro_conn.execute("DELETE FROM expense_records WHERE 1=1")


def test_readonly_connection_rejects_write_to_ifta_worksheets(reports_ro_conn, seeded_ifta_worksheet):
    with pytest.raises(sqlite3.OperationalError):
        reports_ro_conn.execute("UPDATE ifta_worksheets SET total_net_tax = 0 WHERE 1=1")


def test_readonly_connection_rejects_write_to_queue_items(reports_ro_conn):
    with pytest.raises(sqlite3.OperationalError):
        reports_ro_conn.execute(
            "INSERT INTO queue_items (queue_item_id, type, source_worker, created_at, "
            "priority, subject, status) VALUES ('x', 'exception', 'reports', 'now', 'today', 'x', 'open')"
        )


def test_readonly_connection_rejects_write_to_evidence_records(reports_ro_conn):
    with pytest.raises(sqlite3.OperationalError):
        reports_ro_conn.execute("DELETE FROM evidence_records WHERE 1=1")
