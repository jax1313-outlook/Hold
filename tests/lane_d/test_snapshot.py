"""ReportSnapshotWriter -- the one writer this lane is allowed
(REPORTS_CHARTER_v1.md bright line #1). save_snapshot() must write an
immutable HTML file plus exactly one print_queue row plus one audit
entry; mark_printed/clear are status transitions only -- clearing must
never touch the archived file, and a real DELETE against print_queue
must be rejected at the trigger level (defense-in-depth, same shape Lane
B gave queue_items)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from dispatch.reports.snapshot import (
    PrintQueueItemNotFoundError,
    list_queue,
    recent_reports,
)

TEMPLATE = {
    "report_type": "fuel_spend",
    "version": "1",
    "title": "Fuel Spend",
    "big_number": {"field": "total_amount", "label": "Total Fuel Spend", "format": "currency"},
}
DATA = {"total_amount": 650.0}


def _save(writer, **overrides):
    kwargs = dict(
        report_type="fuel_spend",
        template=TEMPLATE,
        template_version="1",
        data=DATA,
        period_label="This Month",
    )
    kwargs.update(overrides)
    return writer.save_snapshot(**kwargs)


def test_save_snapshot_writes_file_and_queue_row(reports_writer, sandbox_config):
    saved = _save(reports_writer)

    assert saved["status"] == "queued"
    assert saved["report_type"] == "fuel_spend"
    archive_root = Path(sandbox_config["roots"]["archive"])
    snapshot_path = archive_root / saved["snapshot_path"]
    assert snapshot_path.is_file()
    html = snapshot_path.read_text(encoding="utf-8")
    assert "$650.00" in html
    assert "immutable archive copy" in html


def test_save_snapshot_writes_exactly_one_audit_entry(reports_writer, db_conn):
    before = db_conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    _save(reports_writer)
    after = db_conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    assert after - before == 1

    entry = db_conn.execute(
        "SELECT * FROM audit_log ORDER BY audit_id DESC LIMIT 1"
    ).fetchone()
    assert entry["actor"] == "reports"
    assert entry["action"] == "reports.save_snapshot"
    assert entry["outcome"] == "completed"


def test_save_snapshot_never_duplicates_the_data_in_the_queue_row(reports_writer):
    saved = _save(reports_writer)
    assert "total_amount" not in saved
    assert saved["snapshot_path"].endswith(".html")


def test_mark_printed_transitions_status(reports_writer):
    saved = _save(reports_writer)
    updated = reports_writer.mark_printed(saved["print_queue_id"])
    assert updated["status"] == "printed"


def test_clear_transitions_status_and_never_touches_the_archived_file(reports_writer, sandbox_config):
    saved = _save(reports_writer)
    archive_root = Path(sandbox_config["roots"]["archive"])
    snapshot_path = archive_root / saved["snapshot_path"]
    original_bytes = snapshot_path.read_bytes()

    cleared = reports_writer.clear(saved["print_queue_id"])
    assert cleared["status"] == "cleared"
    assert snapshot_path.is_file()
    assert snapshot_path.read_bytes() == original_bytes


def test_clear_then_mark_printed_and_actions_on_missing_id_raise(reports_writer):
    with pytest.raises(PrintQueueItemNotFoundError):
        reports_writer.mark_printed("does-not-exist")
    with pytest.raises(PrintQueueItemNotFoundError):
        reports_writer.clear("does-not-exist")


def test_real_delete_against_print_queue_is_rejected_by_trigger(reports_writer, db_conn):
    _save(reports_writer)
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute("DELETE FROM print_queue WHERE 1=1")


def test_list_queue_filters_by_status(reports_writer):
    saved1 = _save(reports_writer)
    saved2 = _save(reports_writer)
    reports_writer.mark_printed(saved2["print_queue_id"])

    queued_only = list_queue(reports_writer._conn, status="queued")
    assert [item["print_queue_id"] for item in queued_only] == [saved1["print_queue_id"]]

    printed_only = list_queue(reports_writer._conn, status="printed")
    assert [item["print_queue_id"] for item in printed_only] == [saved2["print_queue_id"]]


def test_recent_reports_derives_from_print_queue_only(reports_writer):
    _save(reports_writer, period_label="This Month")
    _save(reports_writer, period_label="This Week")
    recents = recent_reports(reports_writer._conn, limit=3)
    period_labels = {r["period_label"] for r in recents}
    assert period_labels == {"This Month", "This Week"}
