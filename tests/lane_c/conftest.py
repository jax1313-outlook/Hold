import pytest

from dispatch.receipt.router import Router


@pytest.fixture
def router(db_conn) -> Router:
    return Router(db_conn)


@pytest.fixture
def ifta_queue_store(db_conn):
    from dispatch.queue.store import QueueStore

    return QueueStore(db_conn)


@pytest.fixture
def ifta_engine(db_conn, sandbox_config):
    from dispatch.ifta.readonly import open_read_only
    from dispatch.ifta.worksheet import WorksheetEngine
    from dispatch.receipt.db import install_schema as install_receipt_schema

    install_receipt_schema(db_conn)  # fuel_records must exist before the ro connection reads it
    ro_conn = open_read_only(sandbox_config["database"])
    engine = WorksheetEngine(db_conn, ro_conn)
    yield engine
    ro_conn.close()


def insert_mileage_record(conn, *, unit_number, jurisdiction, period_start, period_end, miles):
    from dispatch.common.ids import new_ulid

    mileage_record_id = new_ulid()
    conn.execute(
        """
        INSERT INTO mileage_records (
            mileage_record_id, unit_number, period_start, period_end,
            jurisdiction, miles, source, entered_by, schema_version
        ) VALUES (?, ?, ?, ?, ?, ?, 'manual_worksheet', 'human:mike', '1.0')
        """,
        (mileage_record_id, unit_number, period_start, period_end, jurisdiction, miles),
    )
    return mileage_record_id


def insert_fuel_record(
    conn, *, jurisdiction, purchase_date, gallons_normalized, fuel_type="diesel",
    tractor_or_reefer="tractor", unit_number="T-100", odometer=None,
):
    from dispatch.common.ids import new_ulid

    fuel_record_id = new_ulid()
    expense_record_id = new_ulid()
    conn.execute(
        """
        INSERT INTO expense_records (
            expense_record_id, evidence_record_id, fuel_record_id, purchase_date,
            vendor_name, line_description, category, amount, currency, unit_number,
            dedup_key, status, extraction_confidence, review_status, schema_version
        ) VALUES (?, 'ev_fixture', ?, ?, 'Fixture Vendor', 'fixture fuel', 'fuel', 100.0,
                  'USD', ?, ?, 'staged', 1.0, 'auto', '1.0')
        """,
        (expense_record_id, fuel_record_id, purchase_date, unit_number, new_ulid()),
    )
    conn.execute(
        """
        INSERT INTO fuel_records (
            fuel_record_id, evidence_record_id, expense_record_id, purchase_date,
            vendor_name, vendor_address, jurisdiction, fuel_type, tractor_or_reefer,
            volume_as_received, volume_as_received_unit, gallons_normalized, unit_price,
            total_amount, currency, taxes_included, unit_number, odometer, dedup_key,
            extraction_confidence, review_status, schema_version
        ) VALUES (?, 'ev_fixture', ?, ?, 'Fixture Vendor', '1 Fixture Rd', ?, ?, ?, ?,
                  'gallons', ?, 4.0, ?, 'USD', 1, ?, ?, ?, 1.0, 'auto', '1.0')
        """,
        (
            fuel_record_id, expense_record_id, purchase_date, jurisdiction, fuel_type,
            tractor_or_reefer, gallons_normalized, gallons_normalized,
            gallons_normalized * 4.0, unit_number, odometer, new_ulid(),
        ),
    )
    return fuel_record_id


@pytest.fixture
def sample_fuel_line() -> dict:
    return {
        "vendor_name": "Flying J Travel Center",
        "vendor_address": "123 Main St, Amarillo, TX 79101",
        "purchase_date": "2026-07-15",
        "purchase_time": "14:30:00",
        "line_description": "Diesel fuel purchase",
        "category": "fuel",
        "amount": 350.00,
        "tax_amount": 0.0,
        "currency": "USD",
        "fuel_type": "diesel",
        "tractor_or_reefer": "tractor",
        "volume_as_received": 87.5,
        "volume_as_received_unit": "gallons",
        "unit_price": 4.00,
        "taxes_included": True,
        "unit_number": "T-104",
        "driver": "J. Smith",
        "odometer": 145302,
        "payment_method": "fuel_card",
        "card_last4": "4321",
        "receipt_number": "RCT-001",
        "extraction_confidence": 1.0,
    }


@pytest.fixture
def sample_reefer_fuel_line(sample_fuel_line) -> dict:
    line = dict(sample_fuel_line)
    line["category"] = "reefer_fuel"
    line["tractor_or_reefer"] = "reefer"
    line["line_description"] = "Reefer diesel fuel"
    return line


@pytest.fixture
def sample_def_line(sample_fuel_line) -> dict:
    line = dict(sample_fuel_line)
    line["category"] = "def"
    line["line_description"] = "DEF fluid"
    line["fuel_type"] = None
    line["tractor_or_reefer"] = None
    line["volume_as_received"] = 5.0
    line["volume_as_received_unit"] = "gallons"
    return line


@pytest.fixture
def sample_meal_line() -> dict:
    return {
        "vendor_name": "Truck Stop Diner",
        "vendor_address": "456 Elm St, Joplin, MO 64801",
        "purchase_date": "2026-07-15",
        "purchase_time": None,
        "line_description": "Dinner",
        "category": "meals",
        "amount": 18.50,
        "tax_amount": 1.20,
        "currency": "USD",
        "fuel_type": None,
        "tractor_or_reefer": None,
        "volume_as_received": None,
        "volume_as_received_unit": None,
        "unit_price": None,
        "taxes_included": False,
        "unit_number": "T-104",
        "driver": "J. Smith",
        "odometer": None,
        "payment_method": "cash",
        "card_last4": None,
        "receipt_number": None,
        "extraction_confidence": 1.0,
    }
