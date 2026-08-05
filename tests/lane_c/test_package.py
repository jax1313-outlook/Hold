"""Package builder: DRAFT status, seal-on-approval via the real queue —
there is no other way for a worksheet to reach 'sealed'."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dispatch.ifta import package, rates
from dispatch.queue.store import QueueStore
from tests.lane_c.conftest import insert_fuel_record, insert_mileage_record


@pytest.fixture
def queue(db_conn) -> QueueStore:
    return QueueStore(db_conn)


def _seeded_worksheet(ifta_engine, db_conn):
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1000.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0, unit_number="T-100")
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    return ifta_engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")


def test_submit_for_approval_creates_and_links_queue_item(ifta_engine, db_conn, queue):
    worksheet = _seeded_worksheet(ifta_engine, db_conn)
    queue_item = package.submit_for_approval(db_conn, queue, worksheet)

    assert queue_item["type"] == "approval"
    linked = db_conn.execute(
        "SELECT queue_item_id FROM ifta_worksheets WHERE ifta_worksheet_id = ?",
        (worksheet["ifta_worksheet_id"],),
    ).fetchone()
    assert linked["queue_item_id"] == queue_item["queue_item_id"]


def test_seal_refuses_before_approval(ifta_engine, db_conn, queue, sandbox_config):
    worksheet = _seeded_worksheet(ifta_engine, db_conn)
    package.submit_for_approval(db_conn, queue, worksheet)

    with pytest.raises(package.ApprovalNotYetGrantedError):
        package.attempt_seal(db_conn, queue, sandbox_config["roots"], worksheet["ifta_worksheet_id"])


def test_seal_refuses_with_no_submission_at_all(ifta_engine, db_conn, queue, sandbox_config):
    worksheet = _seeded_worksheet(ifta_engine, db_conn)
    with pytest.raises(package.ApprovalNotYetGrantedError):
        package.attempt_seal(db_conn, queue, sandbox_config["roots"], worksheet["ifta_worksheet_id"])


def test_seal_succeeds_after_approval_and_writes_bundle(ifta_engine, db_conn, queue, sandbox_config):
    worksheet = _seeded_worksheet(ifta_engine, db_conn)
    queue_item = package.submit_for_approval(db_conn, queue, worksheet)
    queue.approve(queue_item["queue_item_id"], decided_by="human:mike", decision_note="checked, looks right")

    sealed = package.attempt_seal(db_conn, queue, sandbox_config["roots"], worksheet["ifta_worksheet_id"])
    assert sealed["status"] == "sealed"
    assert sealed["sealed_at"] is not None

    bundle_path = Path(sandbox_config["roots"]["archive"]) / "IFTA" / "2026-Q2" / f"{worksheet['ifta_worksheet_id']}.json"
    assert bundle_path.is_file()
    bundle = json.loads(bundle_path.read_text())
    assert bundle["approved_by"] == "human:mike"
    assert bundle["worksheet"]["status"] == "sealed"
    assert len(bundle["lines"]) == 1


def test_seal_is_idempotent_once_sealed(ifta_engine, db_conn, queue, sandbox_config):
    worksheet = _seeded_worksheet(ifta_engine, db_conn)
    queue_item = package.submit_for_approval(db_conn, queue, worksheet)
    queue.approve(queue_item["queue_item_id"], decided_by="human:mike")
    package.attempt_seal(db_conn, queue, sandbox_config["roots"], worksheet["ifta_worksheet_id"])

    sealed_again = package.attempt_seal(db_conn, queue, sandbox_config["roots"], worksheet["ifta_worksheet_id"])
    assert sealed_again["status"] == "sealed"


def test_seal_refuses_a_rejected_worksheet(ifta_engine, db_conn, queue, sandbox_config):
    worksheet = _seeded_worksheet(ifta_engine, db_conn)
    queue_item = package.submit_for_approval(db_conn, queue, worksheet)
    queue.reject(queue_item["queue_item_id"], decided_by="human:mike", decision_note="numbers look off")

    with pytest.raises(package.ApprovalNotYetGrantedError):
        package.attempt_seal(db_conn, queue, sandbox_config["roots"], worksheet["ifta_worksheet_id"])


def test_worksheets_cannot_be_deleted(ifta_engine, db_conn):
    import sqlite3

    worksheet = _seeded_worksheet(ifta_engine, db_conn)
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            "DELETE FROM ifta_worksheets WHERE ifta_worksheet_id = ?", (worksheet["ifta_worksheet_id"],)
        )


def test_sealed_bundle_includes_real_evidence_for_each_line(ifta_engine, db_conn, queue, sandbox_config):
    """Closes the evidence-refs gap: the bundle's own docstring has
    always promised 'worksheet + lines + evidence refs' -- this proves
    it, not just the presence of a lines list."""
    mileage_id = insert_mileage_record(
        db_conn, unit_number="T-100", jurisdiction="TX",
        period_start="2026-04-01", period_end="2026-06-30", miles=1000.0,
    )
    fuel_id = insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0, unit_number="T-100")
    db_conn.execute(
        """
        INSERT INTO evidence_records (
            evidence_record_id, archive_path, file_hash, document_type,
            document_date, capture_date, extraction_status, schema_version
        ) VALUES ('ev_fixture', 'Evidence/2026/04/ev_fixture.jpg', 'deadbeef', 'pump_receipt',
                  '2026-04-15', '2026-04-15T00:00:00Z', 'complete', '1.1')
        """
    )
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    worksheet = ifta_engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")

    queue_item = package.submit_for_approval(db_conn, queue, worksheet)
    queue.approve(queue_item["queue_item_id"], decided_by="human:mike", decision_note="checked")
    package.attempt_seal(db_conn, queue, sandbox_config["roots"], worksheet["ifta_worksheet_id"])

    bundle_path = Path(sandbox_config["roots"]["archive"]) / "IFTA" / "2026-Q2" / f"{worksheet['ifta_worksheet_id']}.json"
    bundle = json.loads(bundle_path.read_text())
    line = bundle["lines"][0]

    assert line["jurisdiction"] == "TX"
    evidence = line["evidence"]
    assert [r["mileage_record_id"] for r in evidence["mileage_records"]] == [mileage_id]
    assert evidence["mileage_records"][0]["entered_by"] == "human:mike"
    assert [r["fuel_record_id"] for r in evidence["fuel_records"]] == [fuel_id]
    assert evidence["fuel_records"][0]["evidence_record"]["archive_path"] == "Evidence/2026/04/ev_fixture.jpg"
    assert evidence["fuel_records"][0]["evidence_record"]["file_hash"] == "deadbeef"


def test_sealed_bundle_skips_a_fuel_record_whose_evidence_row_is_missing(ifta_engine, db_conn, queue, sandbox_config):
    """tests/lane_c/conftest.py's insert_fuel_record fixture points
    evidence_record_id at a placeholder ('ev_fixture') that most tests
    never actually insert -- this is exactly the 'no longer resolves'
    path _resolve_line_evidence must degrade gracefully on, real evidence
    row or not."""
    insert_mileage_record(
        db_conn, unit_number="T-100", jurisdiction="TX",
        period_start="2026-04-01", period_end="2026-06-30", miles=1000.0,
    )
    fuel_id = insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0, unit_number="T-100")
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    worksheet = ifta_engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")

    queue_item = package.submit_for_approval(db_conn, queue, worksheet)
    queue.approve(queue_item["queue_item_id"], decided_by="human:mike")
    package.attempt_seal(db_conn, queue, sandbox_config["roots"], worksheet["ifta_worksheet_id"])

    bundle_path = Path(sandbox_config["roots"]["archive"]) / "IFTA" / "2026-Q2" / f"{worksheet['ifta_worksheet_id']}.json"
    bundle = json.loads(bundle_path.read_text())
    fuel_record = bundle["lines"][0]["evidence"]["fuel_records"][0]

    assert fuel_record["fuel_record_id"] == fuel_id
    assert fuel_record["evidence_record"] is None  # missing evidence row -- skipped, not raised


def test_worksheet_lines_are_fully_immutable(ifta_engine, db_conn):
    import sqlite3

    worksheet = _seeded_worksheet(ifta_engine, db_conn)
    line_id = worksheet["lines"][0]["ifta_worksheet_line_id"]
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            "UPDATE ifta_worksheet_lines SET miles = 9999 WHERE ifta_worksheet_line_id = ?", (line_id,)
        )
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            "DELETE FROM ifta_worksheet_lines WHERE ifta_worksheet_line_id = ?", (line_id,)
        )
