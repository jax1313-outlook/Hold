"""Contract conformance, extended by Lane C: every FuelRecord/ExpenseRecord
the router actually creates validates against its FROZEN v1.0 schema,
byte-for-byte."""
from __future__ import annotations

import jsonschema
import pytest

from dispatch.receipt.router import Router
from tests.conftest import load_contract_schema

FUEL_SCHEMA = load_contract_schema("fuel_record")
EXPENSE_SCHEMA = load_contract_schema("expense_record")
FORMAT_CHECKER = jsonschema.FormatChecker()


@pytest.fixture
def router(db_conn) -> Router:
    return Router(db_conn)


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


def _fuel_row_as_dict(conn, fuel_record_id) -> dict:
    row = conn.execute(
        "SELECT * FROM fuel_records WHERE fuel_record_id = ?", (fuel_record_id,)
    ).fetchone()
    record = dict(row)
    record["taxes_included"] = bool(record["taxes_included"])
    return record


def _expense_row_as_dict(conn, expense_record_id) -> dict:
    return dict(
        conn.execute(
            "SELECT * FROM expense_records WHERE expense_record_id = ?", (expense_record_id,)
        ).fetchone()
    )


def test_propulsion_fuel_produces_conforming_records(router, db_conn, sample_fuel_line):
    result = router.route_line("ev_1", sample_fuel_line)

    fuel_record = _fuel_row_as_dict(db_conn, result["fuel_record_id"])
    jsonschema.validate(instance=fuel_record, schema=FUEL_SCHEMA, format_checker=FORMAT_CHECKER)

    expense_record = _expense_row_as_dict(db_conn, result["expense_record_id"])
    jsonschema.validate(instance=expense_record, schema=EXPENSE_SCHEMA, format_checker=FORMAT_CHECKER)


def test_reefer_fuel_produces_conforming_expense_record_only(router, db_conn, sample_reefer_fuel_line):
    result = router.route_line("ev_1", sample_reefer_fuel_line)
    expense_record = _expense_row_as_dict(db_conn, result["expense_record_id"])
    jsonschema.validate(instance=expense_record, schema=EXPENSE_SCHEMA, format_checker=FORMAT_CHECKER)


def test_meal_produces_conforming_expense_record(router, db_conn, sample_meal_line):
    result = router.route_line("ev_1", sample_meal_line)
    expense_record = _expense_row_as_dict(db_conn, result["expense_record_id"])
    jsonschema.validate(instance=expense_record, schema=EXPENSE_SCHEMA, format_checker=FORMAT_CHECKER)
