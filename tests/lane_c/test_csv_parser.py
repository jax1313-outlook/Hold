import pytest

from dispatch.receipt.parsers import csv_parser

_HEADER = (
    "vendor_name,vendor_address,purchase_date,purchase_time,line_description,category,"
    "amount,tax_amount,currency,fuel_type,tractor_or_reefer,volume_as_received,"
    "volume_as_received_unit,unit_price,taxes_included,unit_number,driver,odometer,"
    "payment_method,card_last4,receipt_number\n"
)


def _row(**overrides):
    base = {
        "vendor_name": "Flying J Travel Center",
        "vendor_address": "123 Main St Amarillo TX 79101",
        "purchase_date": "2026-07-15",
        "purchase_time": "14:30",
        "line_description": "Diesel fuel",
        "category": "fuel",
        "amount": "350.00",
        "tax_amount": "0",
        "currency": "USD",
        "fuel_type": "diesel",
        "tractor_or_reefer": "tractor",
        "volume_as_received": "87.5",
        "volume_as_received_unit": "gallons",
        "unit_price": "4.00",
        "taxes_included": "true",
        "unit_number": "T-104",
        "driver": "J. Smith",
        "odometer": "145302",
        "payment_method": "fuel_card",
        "card_last4": "4321",
        "receipt_number": "RCT-001",
    }
    base.update(overrides)
    return ",".join(base[k] for k in base)


def test_parses_lines_and_total(tmp_path):
    path = tmp_path / "export.csv"
    path.write_text(
        _HEADER
        + _row() + "\n"
        + _row(category="meals", amount="18.50", line_description="Dinner", fuel_type="",
               tractor_or_reefer="", volume_as_received="", volume_as_received_unit="",
               unit_price="") + "\n"
        + "TOTAL,,,,,,368.50,,,,,,,,,,,,,,\n",
        encoding="utf-8",
    )

    lines, total = csv_parser.parse(path)
    assert len(lines) == 2
    assert total == 368.50
    assert lines[0]["extraction_confidence"] == 1.0
    assert lines[0]["vendor_name"] == "Flying J Travel Center"
    assert lines[1]["category"] == "meals"


def test_missing_required_column_raises(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text(_HEADER + _row(vendor_name="") + "\n", encoding="utf-8")

    with pytest.raises(ValueError):
        csv_parser.parse(path)


def test_no_total_row_is_fine(tmp_path):
    path = tmp_path / "no_total.csv"
    path.write_text(_HEADER + _row() + "\n", encoding="utf-8")

    lines, total = csv_parser.parse(path)
    assert len(lines) == 1
    assert total is None
