from __future__ import annotations

from datetime import date

import pytest

from dispatch.common.ids import new_ulid
from dispatch.ifta_clerk.app import create_app
from dispatch.ifta_clerk.readonly import open_read_only


@pytest.fixture
def client(sandbox_config):
    app = create_app(sandbox_config)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def ro_conn(sandbox_config, db_conn):
    """A genuine read-only connection to the same sandbox database
    db_conn writes to -- db_conn is the fixture dependency so this
    fixture runs after the database file actually exists."""
    conn = open_read_only(sandbox_config["database"])
    yield conn
    conn.close()


def insert_mileage_record(conn, *, unit_number, jurisdiction, period_start, period_end, miles):
    conn.execute(
        """
        INSERT INTO mileage_records (
            mileage_record_id, unit_number, period_start, period_end,
            jurisdiction, miles, source, entered_by, schema_version
        ) VALUES (?, ?, ?, ?, ?, ?, 'manual_worksheet', 'human:mike', '1.0')
        """,
        (new_ulid(), unit_number, period_start, period_end, jurisdiction, miles),
    )


def insert_fuel_record(
    conn, *, jurisdiction, purchase_date, gallons_normalized, fuel_type="diesel",
    tractor_or_reefer="tractor", unit_number="T-100", odometer=None,
    extraction_confidence=1.0, evidence_record_id="ev_fixture",
):
    fuel_record_id = new_ulid()
    expense_record_id = new_ulid()
    conn.execute(
        """
        INSERT INTO expense_records (
            expense_record_id, evidence_record_id, fuel_record_id, purchase_date,
            vendor_name, line_description, category, amount, currency, unit_number,
            dedup_key, status, extraction_confidence, review_status, schema_version
        ) VALUES (?, ?, ?, ?, 'Fixture Vendor', 'fixture fuel', 'fuel', 100.0,
                  'USD', ?, ?, 'staged', ?, 'auto', '1.0')
        """,
        (expense_record_id, evidence_record_id, fuel_record_id, purchase_date, unit_number, new_ulid(), extraction_confidence),
    )
    conn.execute(
        """
        INSERT INTO fuel_records (
            fuel_record_id, evidence_record_id, expense_record_id, purchase_date,
            vendor_name, vendor_address, jurisdiction, fuel_type, tractor_or_reefer,
            volume_as_received, volume_as_received_unit, gallons_normalized, unit_price,
            total_amount, currency, taxes_included, unit_number, odometer, dedup_key,
            extraction_confidence, review_status, schema_version
        ) VALUES (?, ?, ?, ?, 'Fixture Vendor', '1 Fixture Rd', ?, ?, ?, ?,
                  'gallons', ?, 4.0, ?, 'USD', 1, ?, ?, ?, ?, 'auto', '1.0')
        """,
        (
            fuel_record_id, evidence_record_id, expense_record_id, purchase_date, jurisdiction, fuel_type,
            tractor_or_reefer, gallons_normalized, gallons_normalized,
            gallons_normalized * 4.0, unit_number, odometer, new_ulid(), extraction_confidence,
        ),
    )
    return fuel_record_id


def insert_evidence_record(conn, *, evidence_record_id, document_type="fuel_receipt"):
    conn.execute(
        """
        INSERT INTO evidence_records (
            evidence_record_id, archive_path, file_hash, document_type, document_date,
            capture_date, extraction_status, schema_version
        ) VALUES (?, ?, ?, ?, ?, ?, 'complete', '1.1')
        """,
        (evidence_record_id, f"Evidence/2026/04/{evidence_record_id}.txt", f"hash_{evidence_record_id}",
         document_type, "2026-04-01", "2026-04-01T00:00:00Z"),
    )
