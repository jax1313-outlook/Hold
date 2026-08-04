import pytest

from dispatch.receipt.parsers.statement_parser import EXAMPLE_FUEL_CARD_PROFILE, parse

_HEADER = (
    "Merchant,Merchant Address,Trans Date,Trans Time,Category,Amount,Tax,Currency,"
    "Description,Fuel Type,Reefer Flag,Gallons,Unit,Price Per Gallon,Tax Included,"
    "Unit Number,Driver Name,Odometer,Payment Method,Card Last 4,Invoice Number\n"
)


def _row(**overrides):
    base = {
        "Merchant": "Pilot Travel Centers",
        "Merchant Address": "789 Hwy 40 Joplin MO 64801",
        "Trans Date": "2026-07-16",
        "Trans Time": "09:15",
        "Category": "fuel",
        "Amount": "410.00",
        "Tax": "0",
        "Currency": "USD",
        "Description": "Diesel",
        "Fuel Type": "diesel",
        "Reefer Flag": "tractor",
        "Gallons": "102.5",
        "Unit": "gallons",
        "Price Per Gallon": "4.00",
        "Tax Included": "true",
        "Unit Number": "T-201",
        "Driver Name": "R. Alvarez",
        "Odometer": "88210",
        "Payment Method": "fuel_card",
        "Card Last 4": "1199",
        "Invoice Number": "INV-9001",
    }
    base.update(overrides)
    return ",".join(base[k] for k in base)


def test_parses_statement_with_vendor_profile(tmp_path):
    path = tmp_path / "statement.csv"
    path.write_text(
        _HEADER
        + _row() + "\n"
        + "TOTAL,,,,,410.00,,,,,,,,,,,,,,,\n",
        encoding="utf-8",
    )

    lines, total = parse(path, EXAMPLE_FUEL_CARD_PROFILE)
    assert len(lines) == 1
    assert total == 410.00
    assert lines[0]["vendor_name"] == "Pilot Travel Centers"
    assert lines[0]["unit_number"] == "T-201"


def test_missing_required_field_raises(tmp_path):
    path = tmp_path / "bad_statement.csv"
    path.write_text(_HEADER + _row(Merchant="") + "\n", encoding="utf-8")

    with pytest.raises(ValueError):
        parse(path, EXAMPLE_FUEL_CARD_PROFILE)
