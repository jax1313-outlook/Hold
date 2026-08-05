"""dispatch.ifta_clerk.prepare -- Prepare This Quarter and Submit for
Approval, the IFTA Clerk's first two write actions, kept strictly
separate per direction 2026-08-04: preparation never submits, submission
never seals."""
from __future__ import annotations

import inspect

import pytest

from dispatch.common.ids import new_ulid
from dispatch.ifta import rates
from dispatch.ifta.db import install_schema as install_ifta_schema
from dispatch.ifta.readonly import open_read_only as open_ifta_ro
from dispatch.ifta.worksheet import InsufficientDataError, MissingRateError
from dispatch.ifta_clerk.prepare import (
    AlreadySubmittedError,
    AmbiguousRateVersionError,
    NoRateEnteredError,
    NothingToSubmitError,
    prepare_quarter,
    submit_quarter_for_approval,
)
from tests.ifta_clerk.conftest import insert_fuel_record, insert_mileage_record


def _install_receipt_schema(conn):
    from dispatch.receipt.db import install_schema as install_receipt_schema

    install_receipt_schema(conn)


# --- prepare_quarter(): build + detectors, never submits -----------------


def test_prepare_quarter_builds_and_persists_a_real_worksheet(db_conn, sandbox_config):
    _install_receipt_schema(db_conn)
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1000.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0)
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    db_conn.commit()

    ro_conn = open_ifta_ro(sandbox_config["database"])
    try:
        result = prepare_quarter(db_conn, ro_conn, sandbox_config["roots"], quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()

    assert result["worksheet"]["status"] == "draft"
    assert result["worksheet"]["quarter"] == "2026-Q2"

    row = db_conn.execute(
        "SELECT * FROM ifta_worksheets WHERE ifta_worksheet_id = ?", (result["worksheet"]["ifta_worksheet_id"],)
    ).fetchone()
    assert row is not None
    assert row["status"] == "draft"
    assert row["queue_item_id"] is None  # never submitted


def test_prepare_quarter_runs_detectors_and_persists_real_exceptions(db_conn, sandbox_config):
    _install_receipt_schema(db_conn)
    # A real reefer-in-propulsion row -- a real exception this worksheet's
    # own run_all_detectors() call should find and persist.
    reefer_id = new_ulid()
    db_conn.execute(
        """
        INSERT INTO fuel_records (
            fuel_record_id, evidence_record_id, expense_record_id, purchase_date,
            vendor_name, vendor_address, jurisdiction, fuel_type, tractor_or_reefer,
            volume_as_received, volume_as_received_unit, gallons_normalized, unit_price,
            total_amount, currency, taxes_included, unit_number, dedup_key,
            extraction_confidence, review_status, schema_version
        ) VALUES (?, 'ev_x', 'exp_x', '2026-04-15', 'Vendor', '1 Rd', 'TX', 'diesel',
                  'reefer', 25.0, 'gallons', 25.0, 4.0, 100.0, 'USD', 1, 'T-100', ?, 1.0, 'auto', '1.0')
        """,
        (reefer_id, new_ulid()),
    )
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1000.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0)
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    db_conn.commit()

    ro_conn = open_ifta_ro(sandbox_config["database"])
    try:
        result = prepare_quarter(db_conn, ro_conn, sandbox_config["roots"], quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()

    assert result["exception_count"] > 0
    exception_rows = db_conn.execute(
        "SELECT * FROM ifta_exceptions WHERE ifta_worksheet_id = ?", (result["worksheet"]["ifta_worksheet_id"],)
    ).fetchall()
    assert len(exception_rows) == result["exception_count"]

    # Real exception Queue items exist -- but only type='exception', never
    # type='approval': prepare_quarter() must never submit for approval.
    exception_queue_rows = db_conn.execute("SELECT * FROM queue_items WHERE type = 'exception'").fetchall()
    assert len(exception_queue_rows) > 0
    approval_queue_rows = db_conn.execute("SELECT * FROM queue_items WHERE type = 'approval'").fetchall()
    assert len(approval_queue_rows) == 0


def test_prepare_quarter_refuses_with_no_rate_entered(db_conn, sandbox_config):
    _install_receipt_schema(db_conn)
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1000.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0)
    db_conn.commit()

    ro_conn = open_ifta_ro(sandbox_config["database"])
    try:
        with pytest.raises(NoRateEnteredError):
            prepare_quarter(db_conn, ro_conn, sandbox_config["roots"], quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()

    # No rate table exists at all -- the check refused before
    # WorksheetEngine (and its install_schema()) was ever constructed.
    table_exists = db_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='ifta_worksheets'"
    ).fetchone()
    assert table_exists is None


def test_prepare_quarter_refuses_with_ambiguous_rate_versions(db_conn, sandbox_config):
    _install_receipt_schema(db_conn)
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1000.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0)
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.22, source_version="fixture-v2")
    db_conn.commit()

    ro_conn = open_ifta_ro(sandbox_config["database"])
    try:
        with pytest.raises(AmbiguousRateVersionError) as exc_info:
            prepare_quarter(db_conn, ro_conn, sandbox_config["roots"], quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()

    assert set(exc_info.value.versions) == {"fixture-v1", "fixture-v2"}
    assert db_conn.execute("SELECT COUNT(*) FROM ifta_worksheets").fetchone()[0] == 0


def test_prepare_quarter_propagates_insufficient_data(db_conn, sandbox_config):
    _install_receipt_schema(db_conn)
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1000.0)
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    db_conn.commit()  # no fuel data at all

    ro_conn = open_ifta_ro(sandbox_config["database"])
    try:
        with pytest.raises(InsufficientDataError):
            prepare_quarter(db_conn, ro_conn, sandbox_config["roots"], quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()


# --- submit_quarter_for_approval(): the separate, second action ---------


def test_submit_refuses_when_nothing_has_been_prepared(db_conn):
    install_ifta_schema(db_conn)
    with pytest.raises(NothingToSubmitError):
        submit_quarter_for_approval(db_conn, quarter="2026-Q2", fuel_type="diesel")


def test_submit_creates_exactly_one_approval_queue_item(db_conn, sandbox_config):
    _install_receipt_schema(db_conn)
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1000.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0)
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    db_conn.commit()

    ro_conn = open_ifta_ro(sandbox_config["database"])
    try:
        prepare_quarter(db_conn, ro_conn, sandbox_config["roots"], quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()

    result = submit_quarter_for_approval(db_conn, quarter="2026-Q2", fuel_type="diesel")

    assert result["queue_item"]["type"] == "approval"
    approval_rows = db_conn.execute("SELECT * FROM queue_items WHERE type = 'approval'").fetchall()
    assert len(approval_rows) == 1

    worksheet_row = db_conn.execute(
        "SELECT queue_item_id FROM ifta_worksheets WHERE ifta_worksheet_id = ?",
        (result["worksheet"]["ifta_worksheet_id"],),
    ).fetchone()
    assert worksheet_row["queue_item_id"] == result["queue_item"]["queue_item_id"]


def test_submit_twice_is_refused_not_a_second_queue_item(db_conn, sandbox_config):
    _install_receipt_schema(db_conn)
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1000.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0)
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    db_conn.commit()

    ro_conn = open_ifta_ro(sandbox_config["database"])
    try:
        prepare_quarter(db_conn, ro_conn, sandbox_config["roots"], quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()

    submit_quarter_for_approval(db_conn, quarter="2026-Q2", fuel_type="diesel")

    with pytest.raises(AlreadySubmittedError):
        submit_quarter_for_approval(db_conn, quarter="2026-Q2", fuel_type="diesel")

    approval_rows = db_conn.execute("SELECT * FROM queue_items WHERE type = 'approval'").fetchall()
    assert len(approval_rows) == 1  # still exactly one, not two


# --- the separation itself, proven structurally, not just asserted ------


def test_prepare_quarter_never_calls_submit_for_approval():
    """ast-parsed, not just 'it doesn't happen to be in the source' --
    prepare_quarter's own function body must never reference
    submit_for_approval at all."""
    import dispatch.ifta_clerk.prepare as prepare_module

    source = inspect.getsource(prepare_module.prepare_quarter)
    assert "submit_for_approval" not in source
    assert "submit_quarter_for_approval" not in source


def test_submit_quarter_for_approval_never_calls_build_or_run_all_detectors():
    import dispatch.ifta_clerk.prepare as prepare_module

    source = inspect.getsource(prepare_module.submit_quarter_for_approval)
    assert ".build(" not in source
    assert "run_all_detectors" not in source


def test_neither_function_ever_calls_attempt_seal():
    import ast

    import dispatch.ifta_clerk.prepare as prepare_module

    tree = ast.parse(inspect.getsource(prepare_module))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
    assert "attempt_seal" not in imported
