"""dispatch.ifta_clerk.dashboard.build_dashboard() -- all seven Review
Dashboard panels, assembled from real data, structurally read-only."""
from __future__ import annotations

import inspect
import sqlite3

import pytest

from dispatch.common.ids import new_ulid
from dispatch.ifta import rates
from dispatch.ifta.db import install_schema as install_ifta_schema
from dispatch.ifta.worksheet import WorksheetEngine
from dispatch.ifta_clerk.dashboard import DEFAULT_CONFIDENCE_THRESHOLD, build_dashboard
from tests.ifta_clerk.conftest import insert_evidence_record, insert_fuel_record, insert_mileage_record


def _install_receipt_schema(conn):
    from dispatch.receipt.db import install_schema as install_receipt_schema

    install_receipt_schema(conn)


# --- fresh install: no crash, clean empty state --------------------------


def test_fresh_database_returns_empty_panels_not_a_crash(ro_conn):
    data = build_dashboard(ro_conn, quarter="2026-Q2", fuel_type="diesel")

    assert data["miles_by_jurisdiction"] == {}
    assert data["fuel_by_jurisdiction"] == {}
    assert data["confirmed_exceptions"] == []
    assert data["live_indicator_findings"] == []
    assert data["suspect_entries"] == []
    assert data["evidence_links"] == []
    assert data["tax_position"]["source"] == "preview"
    assert data["tax_position"]["worksheet"] is None
    assert data["tax_position"]["estimate"] is None
    assert "no rate" in data["tax_position"]["error"]
    assert data["readiness_status"] == "no mileage recorded yet this quarter"


# --- panels 2 and 3: miles/fuel by jurisdiction ---------------------------


def test_miles_and_fuel_by_jurisdiction_reflect_real_seeded_data(db_conn, ro_conn):
    _install_receipt_schema(db_conn)
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1000.0)
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="OK", period_start="2026-04-01", period_end="2026-06-30", miles=500.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0)
    db_conn.commit()

    data = build_dashboard(ro_conn, quarter="2026-Q2", fuel_type="diesel")

    assert data["miles_by_jurisdiction"] == {"TX": 1000.0, "OK": 500.0}
    assert data["fuel_by_jurisdiction"] == {"TX": 100.0}


# --- panel 4: Category 1 vs Category 2, never conflated ------------------


def test_category_1_confirmed_exceptions_come_from_a_real_built_worksheet(db_conn, sandbox_config, ro_conn):
    from dispatch.evidence.interface import EvidenceSpine
    from dispatch.ifta import exceptions
    from dispatch.queue.store import QueueStore
    from dispatch.ifta.readonly import open_read_only as open_ifta_ro

    _install_receipt_schema(db_conn)
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1000.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0)
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    db_conn.commit()

    ifta_ro = open_ifta_ro(sandbox_config["database"])
    engine = WorksheetEngine(db_conn, ifta_ro)
    worksheet = engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")

    spine = EvidenceSpine(db_conn, sandbox_config["roots"])
    queue = QueueStore(db_conn)
    exceptions.run_all_detectors(db_conn, ifta_ro, spine, queue, worksheet)
    db_conn.commit()
    ifta_ro.close()

    data = build_dashboard(ro_conn, quarter="2026-Q2", fuel_type="diesel")

    assert len(data["confirmed_exceptions"]) > 0
    assert data["tax_position"]["source"] == "worksheet"
    assert data["tax_position"]["worksheet"]["ifta_worksheet_id"] == worksheet["ifta_worksheet_id"]


def test_category_2_live_indicators_never_appear_in_confirmed_exceptions(db_conn, ro_conn):
    """A real reefer-flagged fuel_record with no worksheet ever built --
    live_indicators() finds it, but it must never leak into
    confirmed_exceptions (which requires a real worksheet + a real
    run_all_detectors() call)."""
    _install_receipt_schema(db_conn)
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

    data = build_dashboard(ro_conn, quarter="2026-Q2", fuel_type="diesel")

    assert data["confirmed_exceptions"] == []
    live_reefer = [f for f in data["live_indicator_findings"] if f["exception_type"] == "reefer_in_propulsion"]
    assert len(live_reefer) == 1
    assert live_reefer[0]["severity"] == "critical"


# --- panel 5: suspect entries ---------------------------------------------


def test_suspect_entries_below_confidence_threshold(db_conn, ro_conn):
    _install_receipt_schema(db_conn)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0, extraction_confidence=0.5)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-20", gallons_normalized=50.0, extraction_confidence=0.99)
    db_conn.commit()

    data = build_dashboard(ro_conn, quarter="2026-Q2", fuel_type="diesel")

    # 2, not 1: the Dual-Record Fuel Doctrine (DECISION_LOG.md #2) means
    # one low-confidence purchase emits BOTH a fuel_record and an
    # expense_record -- both are real, separately governed, and both
    # correctly surface as suspect. The 0.99-confidence purchase's pair
    # is correctly excluded from both.
    assert len(data["suspect_entries"]) == 2
    assert all(e["extraction_confidence"] == 0.5 for e in data["suspect_entries"])
    record_types = {e["record_type"] for e in data["suspect_entries"]}
    assert record_types == {"fuel", "expense"}
    assert data["confidence_threshold"] == DEFAULT_CONFIDENCE_THRESHOLD


# --- panel 6: evidence links, no retrieve() call --------------------------


def test_evidence_links_are_plain_references_not_a_retrieve_call(db_conn, sandbox_config, ro_conn):
    _install_receipt_schema(db_conn)
    evidence_id = "ev_" + new_ulid()
    insert_evidence_record(db_conn, evidence_record_id=evidence_id, document_type="fuel_receipt")
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0, evidence_record_id=evidence_id)
    db_conn.commit()

    before_audit = db_conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

    data = build_dashboard(ro_conn, quarter="2026-Q2", fuel_type="diesel")

    after_audit = db_conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

    assert len(data["evidence_links"]) == 1
    assert data["evidence_links"][0]["evidence_record_id"] == evidence_id
    assert data["evidence_links"][0]["document_type"] == "fuel_receipt"
    assert after_audit == before_audit  # no audit entry from merely viewing


def test_evidence_links_module_never_imports_evidence_spine():
    import ast

    import dispatch.ifta_clerk.dashboard as dashboard_module

    tree = ast.parse(inspect.getsource(dashboard_module))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
    assert "EvidenceSpine" not in imported


# --- panel 7: tax position -- worksheet vs preview, never both -----------


def test_tax_position_shows_preview_when_no_worksheet_exists(db_conn, ro_conn):
    _install_receipt_schema(db_conn)
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1000.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0)
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    db_conn.commit()

    data = build_dashboard(ro_conn, quarter="2026-Q2", fuel_type="diesel")

    assert data["tax_position"]["source"] == "preview"
    assert data["tax_position"]["worksheet"] is None
    assert data["tax_position"]["estimate"] is not None
    assert data["tax_position"]["estimate"]["status"] == "preview"


def test_tax_position_shows_ambiguous_error_with_multiple_rate_versions(db_conn, ro_conn):
    _install_receipt_schema(db_conn)
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1000.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0)
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.22, source_version="fixture-v2")
    db_conn.commit()

    data = build_dashboard(ro_conn, quarter="2026-Q2", fuel_type="diesel")

    assert data["tax_position"]["estimate"] is None
    assert "ambiguous" in data["tax_position"]["error"]


def test_tax_position_shows_the_real_worksheet_once_one_is_built(db_conn, sandbox_config, ro_conn):
    from dispatch.ifta.readonly import open_read_only as open_ifta_ro

    _install_receipt_schema(db_conn)
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1000.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0)
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    db_conn.commit()

    ifta_ro = open_ifta_ro(sandbox_config["database"])
    engine = WorksheetEngine(db_conn, ifta_ro)
    built = engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
    ifta_ro.close()

    data = build_dashboard(ro_conn, quarter="2026-Q2", fuel_type="diesel")

    assert data["tax_position"]["source"] == "worksheet"
    assert data["tax_position"]["estimate"] is None
    assert data["tax_position"]["worksheet"]["ifta_worksheet_id"] == built["ifta_worksheet_id"]
    assert data["tax_position"]["worksheet"]["total_net_tax"] == built["total_net_tax"]


# --- panel 1: readiness status --------------------------------------------


def test_readiness_status_reflects_the_most_significant_signal(db_conn, ro_conn):
    _install_receipt_schema(db_conn)
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1000.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0)
    db_conn.commit()

    data = build_dashboard(ro_conn, quarter="2026-Q2", fuel_type="diesel")
    assert "ready to prepare" in data["readiness_status"] or "live indicator" in data["readiness_status"]


# --- structural protections: read only, no writer anywhere ---------------


def test_build_dashboard_takes_only_a_read_only_connection():
    sig = inspect.signature(build_dashboard)
    params = list(sig.parameters)
    assert params[0] == "read_only_conn"
    assert "write" not in params
    assert "conn" not in params[1:]


def test_dashboard_module_source_never_issues_a_raw_sql_write():
    import dispatch.ifta_clerk.dashboard as dashboard_module

    source = inspect.getsource(dashboard_module)
    forbidden = ["INSERT INTO", "UPDATE ", "DELETE FROM"]
    for snippet in forbidden:
        assert snippet not in source, f"dashboard.py contains a raw SQL write: {snippet!r}"


def test_dashboard_module_never_imports_queue_or_package():
    import ast

    import dispatch.ifta_clerk.dashboard as dashboard_module

    tree = ast.parse(inspect.getsource(dashboard_module))
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
    assert "submit_for_approval" not in imported
    assert "attempt_seal" not in imported


def test_calling_build_dashboard_repeatedly_writes_nothing(db_conn, ro_conn):
    _install_receipt_schema(db_conn)
    install_ifta_schema(db_conn)
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1000.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0)
    db_conn.commit()

    before_exceptions = db_conn.execute("SELECT COUNT(*) FROM ifta_exceptions").fetchone()[0]
    before_worksheets = db_conn.execute("SELECT COUNT(*) FROM ifta_worksheets").fetchone()[0]
    before_queue = db_conn.execute("SELECT COUNT(*) FROM queue_items").fetchone()[0]
    before_audit = db_conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

    for _ in range(5):
        build_dashboard(ro_conn, quarter="2026-Q2", fuel_type="diesel")

    assert db_conn.execute("SELECT COUNT(*) FROM ifta_exceptions").fetchone()[0] == before_exceptions
    assert db_conn.execute("SELECT COUNT(*) FROM ifta_worksheets").fetchone()[0] == before_worksheets
    assert db_conn.execute("SELECT COUNT(*) FROM queue_items").fetchone()[0] == before_queue
    assert db_conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0] == before_audit
