"""IFTA UI fixtures. Fuel data comes from the real Router (same
real-pipeline-fixture pattern tests/pilot/ and tests/lane_d/ already use)
rather than hand-typed rows."""
from __future__ import annotations

import pytest

from dispatch.ifta.app import create_app


@pytest.fixture
def client(sandbox_config):
    app = create_app(sandbox_config)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def insert_mileage(conn, *, unit_number="T-104", jurisdiction, period_start, period_end, miles, entered_by="human:mike"):
    from dispatch.common.ids import new_ulid

    conn.execute(
        """
        INSERT INTO mileage_records (
            mileage_record_id, unit_number, period_start, period_end,
            jurisdiction, miles, source, entered_by, schema_version
        ) VALUES (?, ?, ?, ?, ?, ?, 'manual_worksheet', ?, '1.0')
        """,
        (new_ulid(), unit_number, period_start, period_end, jurisdiction, miles, entered_by),
    )


@pytest.fixture
def seeded_fuel_and_mileage(db_conn, sandbox_config, tmp_path):
    """One real TX fuel purchase, routed through the real Router, plus
    real TX mileage for the same quarter -- enough for a real, buildable
    worksheet with no exceptions expected in the plausible band."""
    from dispatch.evidence.interface import EvidenceSpine
    from dispatch.receipt.router import Router

    spine = EvidenceSpine(db_conn, sandbox_config["roots"])
    router = Router(db_conn)

    doc = tmp_path / "receipt.txt"
    doc.write_text("Flying J fuel receipt")
    record = spine.register(doc, "pump_receipt", {"document_date": "2026-08-01"})
    fuel_line = {
        "vendor_name": "Flying J Travel Center", "vendor_address": "123 Main St, Amarillo, TX 79101",
        "purchase_date": "2026-08-01", "purchase_time": "09:00:00",
        "line_description": "Diesel fuel", "category": "fuel", "amount": 400.0, "tax_amount": 0.0,
        "currency": "USD", "fuel_type": "diesel", "tractor_or_reefer": "tractor",
        "volume_as_received": 100.0, "volume_as_received_unit": "gallons", "unit_price": 4.0,
        "taxes_included": True, "unit_number": "T-104", "driver": "J. Smith", "odometer": 100000,
        "payment_method": "fuel_card", "card_last4": "4321", "receipt_number": "RCT-100",
        "extraction_confidence": 1.0,
    }
    router.route_line(record["evidence_record_id"], fuel_line)

    insert_mileage(db_conn, jurisdiction="TX", period_start="2026-07-01", period_end="2026-09-30", miles=700.0)
    return {"quarter": "2026-Q3", "fuel_type": "diesel"}
