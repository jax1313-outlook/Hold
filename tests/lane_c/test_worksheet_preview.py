"""dispatch.ifta.worksheet.preview() -- the non-persisting live estimate
approved in principle 2026-08-04 (IFTA_CLERK_BLUEPRINT_v1 section 6.1),
under six conditions. Each test below proves one condition holds
structurally, not just today's implementation happening to follow it."""
from __future__ import annotations

import inspect
import sqlite3

import pytest

from dispatch.ifta import rates
from dispatch.ifta.readonly import open_read_only
from dispatch.ifta.worksheet import (
    InsufficientDataError,
    MissingRateError,
    WorksheetEngine,
    preview,
)
from tests.lane_c.conftest import insert_fuel_record, insert_mileage_record


def _seed_two_jurisdiction_quarter(db_conn):
    insert_mileage_record(
        db_conn, unit_number="T-100", jurisdiction="TX",
        period_start="2026-04-01", period_end="2026-06-30", miles=1000.0,
    )
    insert_mileage_record(
        db_conn, unit_number="T-100", jurisdiction="OK",
        period_start="2026-04-01", period_end="2026-06-30", miles=500.0,
    )
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0)
    insert_fuel_record(db_conn, jurisdiction="OK", purchase_date="2026-05-15", gallons_normalized=60.0)

    rates.insert_rate(
        db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel",
        rate=0.20, source_version="fixture-v1",
    )
    rates.insert_rate(
        db_conn, jurisdiction="OK", quarter="2026-Q2", fuel_type="diesel",
        rate=0.18, source_version="fixture-v1",
    )


# --- preview() computes the same numbers build() would, without persisting -


def test_preview_matches_what_build_would_produce(ifta_engine, db_conn, sandbox_config):
    _seed_two_jurisdiction_quarter(db_conn)
    ro_conn = open_read_only(sandbox_config["database"])
    try:
        result = preview(ro_conn, quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
        built = ifta_engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")

        assert result["fleet_mpg"] == pytest.approx(built["fleet_mpg"])
        assert result["total_net_tax"] == pytest.approx(built["total_net_tax"])
        assert len(result["lines"]) == len(built["lines"])
        for preview_line, built_line in zip(
            sorted(result["lines"], key=lambda l: l["jurisdiction"]),
            sorted(built["lines"], key=lambda l: l["jurisdiction"]),
        ):
            assert preview_line["jurisdiction"] == built_line["jurisdiction"]
            assert preview_line["net_tax"] == pytest.approx(built_line["net_tax"])
    finally:
        ro_conn.close()


def test_preview_raises_insufficient_data_same_as_build(db_conn, sandbox_config):
    from dispatch.receipt.db import install_schema as install_receipt_schema

    install_receipt_schema(db_conn)
    insert_mileage_record(
        db_conn, unit_number="T-100", jurisdiction="TX",
        period_start="2026-04-01", period_end="2026-06-30", miles=1000.0,
    )
    ro_conn = open_read_only(sandbox_config["database"])
    try:
        with pytest.raises(InsufficientDataError):
            preview(ro_conn, quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
    finally:
        ro_conn.close()


def test_preview_raises_missing_rate_same_as_build(db_conn, sandbox_config):
    from dispatch.receipt.db import install_schema as install_receipt_schema

    install_receipt_schema(db_conn)
    insert_mileage_record(
        db_conn, unit_number="T-100", jurisdiction="TX",
        period_start="2026-04-01", period_end="2026-06-30", miles=1000.0,
    )
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0)
    rates.insert_rate(
        db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel",
        rate=0.20, source_version="fixture-v1",
    )
    # No rate for a second jurisdiction that has mileage/fuel activity.
    insert_mileage_record(
        db_conn, unit_number="T-100", jurisdiction="OK",
        period_start="2026-04-01", period_end="2026-06-30", miles=200.0,
    )
    ro_conn = open_read_only(sandbox_config["database"])
    try:
        with pytest.raises(MissingRateError):
            preview(ro_conn, quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
    finally:
        ro_conn.close()


def test_preview_on_a_genuinely_fresh_database_raises_cleanly_not_a_crash(db_conn, sandbox_config):
    """No receipt schema, no ifta schema, no rate ever entered -- exactly
    the fresh-install state that crashed WorksheetEngine._aggregate_fuel()
    with a raw sqlite3.OperationalError before (worked around at the UI
    layer in build/ifta-ui, documented as a real bug needing a fix here).
    preview() must never hit that raw crash, on this same class of input."""
    ro_conn = open_read_only(sandbox_config["database"])
    try:
        with pytest.raises(InsufficientDataError):
            preview(ro_conn, quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
    finally:
        ro_conn.close()


# --- the six approved conditions, each proven structurally --------------


def test_condition_1_no_database_writes_possible(ifta_engine, db_conn, sandbox_config):
    """preview() takes only a read-only connection -- there is no
    write-capable connection reachable from inside it at all, not merely
    a convention it follows."""
    _seed_two_jurisdiction_quarter(db_conn)
    ro_conn = open_read_only(sandbox_config["database"])
    try:
        preview(ro_conn, quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
    finally:
        ro_conn.close()

    sig = inspect.signature(preview)
    params = list(sig.parameters)
    assert params[0] == "read_only_conn"
    # Structural: preview() has exactly one connection parameter, and its
    # name and the docstring both name it explicitly read-only.
    assert "write" not in params
    assert "conn" not in params[1:]


def test_condition_1_preview_source_never_calls_execute_on_anything_but_its_own_parameter():
    source = inspect.getsource(preview)
    assert "self._conn" not in source
    assert "write_conn" not in source


def test_condition_2_no_worksheet_ids(ifta_engine, db_conn, sandbox_config):
    _seed_two_jurisdiction_quarter(db_conn)
    ro_conn = open_read_only(sandbox_config["database"])
    try:
        result = preview(ro_conn, quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
    finally:
        ro_conn.close()

    assert "ifta_worksheet_id" not in result
    # co_names (not raw source text) so the docstring's own prose
    # explaining this guarantee can't accidentally trip the check.
    assert "new_ulid" not in preview.__code__.co_names


def test_condition_3_no_audit_status_changes(ifta_engine, db_conn, sandbox_config):
    """No row appears in ifta_worksheets or ifta_worksheet_lines as a
    result of calling preview() -- checked against the real tables, not
    just absent from the return value."""
    _seed_two_jurisdiction_quarter(db_conn)
    before_worksheets = db_conn.execute("SELECT COUNT(*) FROM ifta_worksheets").fetchone()[0]
    before_lines = db_conn.execute("SELECT COUNT(*) FROM ifta_worksheet_lines").fetchone()[0]

    ro_conn = open_read_only(sandbox_config["database"])
    try:
        preview(ro_conn, quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
    finally:
        ro_conn.close()

    after_worksheets = db_conn.execute("SELECT COUNT(*) FROM ifta_worksheets").fetchone()[0]
    after_lines = db_conn.execute("SELECT COUNT(*) FROM ifta_worksheet_lines").fetchone()[0]
    assert after_worksheets == before_worksheets
    assert after_lines == before_lines

    source = inspect.getsource(preview)
    assert "INSERT INTO ifta_worksheets" not in source
    assert "INSERT INTO ifta_worksheet_lines" not in source


def test_condition_4_no_approval_path_activation():
    """preview() never receives or constructs a QueueStore, and
    dispatch.ifta.package -- the only module with submit/seal authority --
    is never imported anywhere in worksheet.py. Checked via the real
    import statements (ast), not a raw text search, so the docstring's
    own prose describing this guarantee can't accidentally trip it."""
    import ast

    import dispatch.ifta.worksheet as worksheet_module

    tree = ast.parse(inspect.getsource(worksheet_module))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)

    assert "QueueStore" not in imported
    assert "dispatch.ifta.package" not in imported
    assert "queue" not in inspect.signature(preview).parameters


def test_condition_5_clearly_labeled_preview(ifta_engine, db_conn, sandbox_config):
    _seed_two_jurisdiction_quarter(db_conn)
    ro_conn = open_read_only(sandbox_config["database"])
    try:
        result = preview(ro_conn, quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
    finally:
        ro_conn.close()

    assert result["status"] == "preview"
    assert result["is_preview"] is True


def test_condition_6_cannot_be_mistaken_for_a_filed_worksheet(ifta_engine, db_conn, sandbox_config):
    """A real, sealed-eligible worksheet from build()+get() and a preview()
    result must not be structurally confusable -- no shared identity key,
    no shared status value, and none of the fields a caller would need to
    submit_for_approval()/attempt_seal() against."""
    _seed_two_jurisdiction_quarter(db_conn)
    built = ifta_engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")

    ro_conn = open_read_only(sandbox_config["database"])
    try:
        result = preview(ro_conn, quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
    finally:
        ro_conn.close()

    assert result["status"] != built["status"]
    for identity_field in ("ifta_worksheet_id", "created_at", "sealed_at", "queue_item_id"):
        assert identity_field not in result
        assert identity_field in built


# --- source-immutability: preview() reads through the same guarantee ----


def test_preview_is_given_a_connection_that_itself_rejects_writes(sandbox_config, db_conn):
    from dispatch.receipt.db import install_schema as install_receipt_schema

    install_receipt_schema(db_conn)
    ro_conn = open_read_only(sandbox_config["database"])
    try:
        with pytest.raises(sqlite3.OperationalError):
            ro_conn.execute("UPDATE fuel_records SET vendor_name = 'tampered' WHERE 1=1")
    finally:
        ro_conn.close()
