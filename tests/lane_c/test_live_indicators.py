"""dispatch.ifta.live_indicators.live_indicators() -- Category 2 of the
Exception Dashboard, approved in principle 2026-08-04
(IFTA_CLERK_BLUEPRINT_v1 section 8). Informational only: proves it
matches what the four detectors would find individually, carries a
severity classification, and structurally never writes, queues, audits,
or persists anything, no matter how many times it's called."""
from __future__ import annotations

import inspect
import sqlite3
from datetime import date

import pytest

from dispatch.common.ids import new_ulid
from dispatch.ifta import exceptions
from dispatch.ifta.live_indicators import SEVERITY_BY_EXCEPTION_TYPE, live_indicators
from dispatch.ifta.readonly import open_read_only
from tests.lane_c.conftest import insert_fuel_record, insert_mileage_record


def test_matches_the_four_detectors_called_individually(db_conn, sandbox_config):
    from dispatch.receipt.db import install_schema as install_receipt_schema

    install_receipt_schema(db_conn)
    insert_fuel_record(
        db_conn, jurisdiction="TX", purchase_date="2026-04-01", gallons_normalized=50.0,
        unit_number="T-100", odometer=100000,
    )
    second_id = insert_fuel_record(
        db_conn, jurisdiction="TX", purchase_date="2026-04-10", gallons_normalized=50.0,
        unit_number="T-100", odometer=99500,  # went backwards
    )
    db_conn.commit()

    ro_conn = open_read_only(sandbox_config["database"])
    try:
        result = live_indicators(ro_conn, quarter="2026-Q2", fuel_type="diesel")
        expected = exceptions.odometer_discontinuity(ro_conn, date(2026, 4, 1), date(2026, 6, 30))
    finally:
        ro_conn.close()

    live_odometer_findings = [f for f in result["findings"] if f["exception_type"] == "odometer_discontinuity"]
    assert len(live_odometer_findings) == len(expected)
    assert any(second_id in f["related_record_ids"] for f in live_odometer_findings)


def test_reefer_in_propulsion_surfaces_as_critical(db_conn, sandbox_config):
    from dispatch.receipt.db import install_schema as install_receipt_schema

    install_receipt_schema(db_conn)
    fuel_record_id = new_ulid()
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
        (fuel_record_id, new_ulid()),
    )
    db_conn.commit()

    ro_conn = open_read_only(sandbox_config["database"])
    try:
        result = live_indicators(ro_conn, quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()

    reefer_findings = [f for f in result["findings"] if f["exception_type"] == "reefer_in_propulsion"]
    assert len(reefer_findings) == 1
    assert reefer_findings[0]["severity"] == "critical"
    assert fuel_record_id in reefer_findings[0]["related_record_ids"]


def test_late_arrival_closed_quarter_surfaces_as_warning(db_conn, sandbox_config):
    from dispatch.ifta.db import install_schema as install_ifta_schema
    from dispatch.receipt.db import install_schema as install_receipt_schema

    install_receipt_schema(db_conn)
    install_ifta_schema(db_conn)
    db_conn.execute(
        """
        INSERT INTO ifta_worksheets (
            ifta_worksheet_id, quarter, fuel_type, fleet_mpg, rate_table_version,
            status, total_net_tax, created_at, sealed_at, queue_item_id, schema_version
        ) VALUES (?, '2026-Q1', 'diesel', 6.0, 'fixture-v1', 'sealed', 0.0, '2026-04-01T00:00:00Z',
                  '2026-04-05T00:00:00Z', NULL, '1.0')
        """,
        (new_ulid(),),
    )
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-02-15", gallons_normalized=40.0, unit_number="T-100")
    db_conn.commit()

    ro_conn = open_read_only(sandbox_config["database"])
    try:
        result = live_indicators(ro_conn, quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()

    findings = [f for f in result["findings"] if f["exception_type"] == "late_arrival_closed_quarter"]
    assert len(findings) == 1
    assert findings[0]["severity"] == "warning"
    assert "2026-Q1" in findings[0]["detail"]


def test_active_truck_days_no_mileage_surfaces_as_warning(db_conn, sandbox_config):
    from dispatch.receipt.db import install_schema as install_receipt_schema

    install_receipt_schema(db_conn)
    insert_fuel_record(db_conn, jurisdiction="NM", purchase_date="2026-04-25", gallons_normalized=30.0, unit_number="T-999")
    db_conn.commit()

    ro_conn = open_read_only(sandbox_config["database"])
    try:
        result = live_indicators(ro_conn, quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()

    findings = [f for f in result["findings"] if f["exception_type"] == "active_truck_days_no_mileage"]
    assert any("T-999" in f["detail"] for f in findings)
    assert all(f["severity"] == "warning" for f in findings)


def test_odometer_discontinuity_surfaces_as_notice(db_conn, sandbox_config):
    from dispatch.receipt.db import install_schema as install_receipt_schema

    install_receipt_schema(db_conn)
    insert_fuel_record(
        db_conn, jurisdiction="TX", purchase_date="2026-04-01", gallons_normalized=50.0,
        unit_number="T-100", odometer=100000,
    )
    insert_fuel_record(
        db_conn, jurisdiction="TX", purchase_date="2026-04-10", gallons_normalized=50.0,
        unit_number="T-100", odometer=99500,
    )
    db_conn.commit()

    ro_conn = open_read_only(sandbox_config["database"])
    try:
        result = live_indicators(ro_conn, quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()

    findings = [f for f in result["findings"] if f["exception_type"] == "odometer_discontinuity"]
    assert len(findings) >= 1
    assert all(f["severity"] == "notice" for f in findings)


def test_no_findings_and_no_crash_on_a_genuinely_fresh_database(db_conn, sandbox_config):
    """No receipt schema, no ifta schema, no mileage/fuel/worksheet ever
    recorded -- the same fresh-install class of input that used to crash
    WorksheetEngine._aggregate_fuel() with a raw sqlite3.OperationalError.
    live_indicators() must read this as nothing to find, not a crash."""
    ro_conn = open_read_only(sandbox_config["database"])
    try:
        result = live_indicators(ro_conn, quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()

    assert result["findings"] == []
    assert result["status"] == "live_indicator"


def test_clearly_labeled_as_a_live_indicator(db_conn, sandbox_config):
    ro_conn = open_read_only(sandbox_config["database"])
    try:
        result = live_indicators(ro_conn, quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()

    assert result["status"] == "live_indicator"
    assert result["is_live_indicator"] is True


def test_every_finding_carries_a_severity_from_the_closed_vocabulary(db_conn, sandbox_config):
    from dispatch.receipt.db import install_schema as install_receipt_schema

    install_receipt_schema(db_conn)
    insert_fuel_record(
        db_conn, jurisdiction="TX", purchase_date="2026-04-01", gallons_normalized=50.0,
        unit_number="T-100", odometer=100000,
    )
    insert_fuel_record(
        db_conn, jurisdiction="TX", purchase_date="2026-04-10", gallons_normalized=50.0,
        unit_number="T-100", odometer=99500,
    )
    insert_fuel_record(db_conn, jurisdiction="NM", purchase_date="2026-04-25", gallons_normalized=30.0, unit_number="T-999")
    db_conn.commit()

    ro_conn = open_read_only(sandbox_config["database"])
    try:
        result = live_indicators(ro_conn, quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()

    assert len(result["findings"]) > 0
    for finding in result["findings"]:
        assert finding["severity"] in SEVERITY_BY_EXCEPTION_TYPE.values()
        assert finding["severity"] not in ("urgent", "today", "whenever")  # never Queue's vocabulary


# --- the five structural protections, each proven, not just asserted ----


def test_protection_1_read_only(db_conn, sandbox_config):
    ro_conn = open_read_only(sandbox_config["database"])
    try:
        live_indicators(ro_conn, quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()

    sig = inspect.signature(live_indicators)
    params = list(sig.parameters)
    assert params[0] == "read_only_conn"
    assert "write" not in params
    assert "conn" not in params[1:]

    source = inspect.getsource(live_indicators)
    assert "self._conn" not in source
    assert "write_conn" not in source


def test_protection_2_non_persistent(db_conn, sandbox_config):
    from dispatch.ifta.db import install_schema as install_ifta_schema
    from dispatch.receipt.db import install_schema as install_receipt_schema

    install_receipt_schema(db_conn)
    install_ifta_schema(db_conn)  # so ifta_exceptions exists to assert a count against
    insert_fuel_record(
        db_conn, jurisdiction="TX", purchase_date="2026-04-01", gallons_normalized=50.0,
        unit_number="T-100", odometer=100000,
    )
    insert_fuel_record(
        db_conn, jurisdiction="TX", purchase_date="2026-04-10", gallons_normalized=50.0,
        unit_number="T-100", odometer=99500,
    )
    db_conn.commit()
    before = db_conn.execute("SELECT COUNT(*) FROM ifta_exceptions").fetchone()[0]

    ro_conn = open_read_only(sandbox_config["database"])
    try:
        result = live_indicators(ro_conn, quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()

    assert len(result["findings"]) > 0  # a real finding did fire...
    after = db_conn.execute("SELECT COUNT(*) FROM ifta_exceptions").fetchone()[0]
    assert after == before  # ...but nothing was persisted because of it

    # ast-parsed imports, not raw text search -- the module's own docstring
    # mentions run_all_detectors() by name to explain what it's NOT doing,
    # which would trip a plain substring check.
    import ast

    import dispatch.ifta.live_indicators as live_indicators_module

    tree = ast.parse(inspect.getsource(live_indicators_module))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
    assert "run_all_detectors" not in imported
    assert "INSERT INTO ifta_exceptions" not in inspect.getsource(live_indicators_module)


def test_protection_3_no_queue_activity(db_conn, sandbox_config):
    import ast

    import dispatch.ifta.live_indicators as live_indicators_module

    tree = ast.parse(inspect.getsource(live_indicators_module))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
    assert "QueueStore" not in imported
    assert "dispatch.queue.store" not in imported

    before = db_conn.execute("SELECT COUNT(*) FROM queue_items").fetchone()[0]
    ro_conn = open_read_only(sandbox_config["database"])
    try:
        live_indicators(ro_conn, quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()
    after = db_conn.execute("SELECT COUNT(*) FROM queue_items").fetchone()[0]
    assert after == before


def test_protection_4_no_approval_activity():
    import ast

    import dispatch.ifta.live_indicators as live_indicators_module

    tree = ast.parse(inspect.getsource(live_indicators_module))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
    assert "dispatch.ifta.package" not in imported
    assert "submit_for_approval" not in imported
    assert "attempt_seal" not in imported


def test_protection_5_no_audit_activity(db_conn, sandbox_config):
    """broken_evidence_linkage is deliberately excluded from this module
    specifically because it's the only worksheet-free detector that
    writes an audit_log row (via EvidenceSpine.retrieve()) -- this test
    proves both halves: the module never imports it or EvidenceSpine, and
    a real call leaves audit_log completely untouched."""
    import ast

    import dispatch.ifta.live_indicators as live_indicators_module

    tree = ast.parse(inspect.getsource(live_indicators_module))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
    assert "EvidenceSpine" not in imported
    assert "broken_evidence_linkage" not in imported
    assert "write_audit_entry" not in imported
    assert "dispatch.common.audit" not in imported

    from dispatch.receipt.db import install_schema as install_receipt_schema

    install_receipt_schema(db_conn)
    insert_fuel_record(
        db_conn, jurisdiction="TX", purchase_date="2026-04-01", gallons_normalized=50.0,
        unit_number="T-100", odometer=100000,
    )
    insert_fuel_record(
        db_conn, jurisdiction="TX", purchase_date="2026-04-10", gallons_normalized=50.0,
        unit_number="T-100", odometer=99500,
    )
    db_conn.commit()
    before = db_conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

    ro_conn = open_read_only(sandbox_config["database"])
    try:
        result = live_indicators(ro_conn, quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()

    assert len(result["findings"]) > 0
    after = db_conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    assert after == before


def test_calling_it_repeatedly_never_accumulates_anything(db_conn, sandbox_config):
    from dispatch.ifta.db import install_schema as install_ifta_schema
    from dispatch.receipt.db import install_schema as install_receipt_schema

    install_receipt_schema(db_conn)
    install_ifta_schema(db_conn)  # so ifta_exceptions exists to assert a count against
    fuel_record_id = new_ulid()
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
        (fuel_record_id, new_ulid()),
    )
    db_conn.commit()

    for _ in range(5):
        ro_conn = open_read_only(sandbox_config["database"])
        try:
            result = live_indicators(ro_conn, quarter="2026-Q2", fuel_type="diesel")
        finally:
            ro_conn.close()
        reefer_findings = [f for f in result["findings"] if f["exception_type"] == "reefer_in_propulsion"]
        assert len(reefer_findings) == 1  # same one finding every time, never duplicated

    exceptions_count = db_conn.execute("SELECT COUNT(*) FROM ifta_exceptions").fetchone()[0]
    queue_count = db_conn.execute("SELECT COUNT(*) FROM queue_items").fetchone()[0]
    audit_count = db_conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    assert exceptions_count == 0
    assert queue_count == 0
    assert audit_count == 0
