"""Lane D fixtures. See tests/fixtures/README.md: fuel/expense data is
built by actually running Lane A's register() and Lane C's router, not
hand-typed SQL rows -- Lane C is real and merged now.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from seed_library import seed_library  # noqa: E402


@pytest.fixture
def seeded_library(sandbox_config) -> dict:
    """Installs library_seed/** (including the three Reports templates)
    into the sandbox's LIBRARY root, the same way every other lane's
    tests do -- see tests/lane_a/test_seed_library.py."""
    seed_library(sandbox_config)
    return sandbox_config


@pytest.fixture
def reports_ro_conn(db_conn, sandbox_config):
    from dispatch.reports.readonly import open_read_only

    conn = open_read_only(sandbox_config["database"])
    yield conn
    conn.close()


@pytest.fixture
def reports_writer(db_conn, sandbox_config):
    from dispatch.reports.snapshot import ReportSnapshotWriter

    return ReportSnapshotWriter(db_conn, sandbox_config["roots"]["archive"])


@pytest.fixture
def seeded_pipeline_data(db_conn, sandbox_config, tmp_path):
    """Two fuel purchases (different states) and one meal expense, all
    routed through the real EvidenceSpine + Router -- genuine
    fuel_records/expense_records, not an approximation of their shape."""
    from dispatch.evidence.interface import EvidenceSpine
    from dispatch.receipt.router import Router

    spine = EvidenceSpine(db_conn, sandbox_config["roots"])
    router = Router(db_conn)

    doc1 = tmp_path / "receipt1.txt"
    doc1.write_text("Flying J fuel receipt")
    record1 = spine.register(doc1, "pump_receipt", {"document_date": "2026-08-01"})
    fuel_line_tx = {
        "vendor_name": "Flying J Travel Center", "vendor_address": "123 Main St, Amarillo, TX 79101",
        "purchase_date": "2026-08-01", "purchase_time": "09:00:00",
        "line_description": "Diesel fuel", "category": "fuel", "amount": 400.0, "tax_amount": 0.0,
        "currency": "USD", "fuel_type": "diesel", "tractor_or_reefer": "tractor",
        "volume_as_received": 100.0, "volume_as_received_unit": "gallons", "unit_price": 4.0,
        "taxes_included": True, "unit_number": "T-104", "driver": "J. Smith", "odometer": 100000,
        "payment_method": "fuel_card", "card_last4": "4321", "receipt_number": "RCT-100",
        "extraction_confidence": 1.0,
    }
    fuel_result_1 = router.route_line(record1["evidence_record_id"], fuel_line_tx)

    doc2 = tmp_path / "receipt2.txt"
    doc2.write_text("Pilot fuel receipt")
    record2 = spine.register(doc2, "pump_receipt", {"document_date": "2026-08-05"})
    fuel_line_mo = dict(
        fuel_line_tx,
        vendor_name="Pilot Travel Centers",
        vendor_address="1 Hwy 40, Joplin, MO 64801",
        purchase_date="2026-08-05",
        amount=250.0,
        volume_as_received=60.0,
        receipt_number="RCT-101",
    )
    fuel_result_2 = router.route_line(record2["evidence_record_id"], fuel_line_mo)

    doc3 = tmp_path / "receipt3.txt"
    doc3.write_text("meal receipt")
    record3 = spine.register(doc3, "invoice", {"document_date": "2026-08-02"})
    meal_line = {
        "vendor_name": "Truck Stop Diner", "vendor_address": "456 Elm St, Joplin, MO 64801",
        "purchase_date": "2026-08-02", "purchase_time": None, "line_description": "Dinner",
        "category": "meals", "amount": 22.0, "tax_amount": 1.5, "currency": "USD",
        "fuel_type": None, "tractor_or_reefer": None, "volume_as_received": None,
        "volume_as_received_unit": None, "unit_price": None, "taxes_included": False,
        "unit_number": "T-104", "driver": "J. Smith", "odometer": None, "payment_method": "cash",
        "card_last4": None, "receipt_number": None, "extraction_confidence": 1.0,
    }
    expense_result = router.route_line(record3["evidence_record_id"], meal_line)

    return {
        "fuel_results": [fuel_result_1, fuel_result_2],
        "expense_results": [expense_result],
    }


@pytest.fixture
def seeded_ifta_worksheet(db_conn, sandbox_config, seeded_pipeline_data):
    """A real worksheet built via Lane C's actual WorksheetEngine, against
    the fuel fixtures above plus matching mileage and a fixture rate."""
    from dispatch.ifta import rates
    from dispatch.ifta.readonly import open_read_only
    from dispatch.ifta.worksheet import WorksheetEngine

    conn = db_conn
    conn.execute(
        """
        INSERT INTO mileage_records (
            mileage_record_id, unit_number, period_start, period_end,
            jurisdiction, miles, source, entered_by, schema_version
        ) VALUES ('mr_tx', 'T-104', '2026-07-01', '2026-09-30', 'TX', 1500.0, 'manual_worksheet', 'human:mike', '1.0')
        """
    )
    conn.execute(
        """
        INSERT INTO mileage_records (
            mileage_record_id, unit_number, period_start, period_end,
            jurisdiction, miles, source, entered_by, schema_version
        ) VALUES ('mr_mo', 'T-104', '2026-07-01', '2026-09-30', 'MO', 900.0, 'manual_worksheet', 'human:mike', '1.0')
        """
    )
    rates.insert_rate(conn, jurisdiction="TX", quarter="2026-Q3", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    rates.insert_rate(conn, jurisdiction="MO", quarter="2026-Q3", fuel_type="diesel", rate=0.19, source_version="fixture-v1")

    ro_conn = open_read_only(sandbox_config["database"])
    engine = WorksheetEngine(conn, ro_conn)
    worksheet = engine.build(quarter="2026-Q3", fuel_type="diesel", rate_table_version="fixture-v1")
    ro_conn.close()
    return worksheet
