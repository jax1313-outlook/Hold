"""DispatchPilot fixtures. Builds a real PilotIntake against the shared
sandbox_config fixture (tests/conftest.py) -- same throwaway-sandbox
pattern every other lane's tests use."""
from __future__ import annotations

import pytest

from dispatch.pilot.intake import PilotIntake


@pytest.fixture
def pilot(sandbox_config) -> PilotIntake:
    return PilotIntake(sandbox_config)


def drop(pilot: PilotIntake, filename: str, content: str) -> None:
    (pilot.inbox / filename).write_text(content, encoding="utf-8")


def fuel_csv_row(**overrides) -> dict:
    row = {
        "vendor_name": "Flying J Travel Center", "vendor_address": "123 Main St, Amarillo, TX 79101",
        "purchase_date": "2026-08-04", "purchase_time": "09:00:00",
        "line_description": "Diesel fuel", "category": "fuel", "amount": "400.0", "tax_amount": "0.0",
        "currency": "USD", "fuel_type": "diesel", "tractor_or_reefer": "tractor",
        "volume_as_received": "100.0", "volume_as_received_unit": "gallons", "unit_price": "4.0",
        "taxes_included": "True", "unit_number": "T-104", "driver": "J. Smith", "odometer": "100000",
        "payment_method": "fuel_card", "card_last4": "4321", "receipt_number": "RCT-100",
        "extraction_confidence": "1.0",
    }
    row.update(overrides)
    return row


def meal_csv_row(**overrides) -> dict:
    row = {
        "vendor_name": "Truck Stop Diner", "vendor_address": "456 Elm St, Joplin, MO 64801",
        "purchase_date": "2026-08-04", "purchase_time": "",
        "line_description": "Dinner", "category": "meals", "amount": "22.0", "tax_amount": "1.5",
        "currency": "USD", "fuel_type": "", "tractor_or_reefer": "", "volume_as_received": "",
        "volume_as_received_unit": "", "unit_price": "", "taxes_included": "False",
        "unit_number": "T-104", "driver": "J. Smith", "odometer": "", "payment_method": "cash",
        "card_last4": "", "receipt_number": "", "extraction_confidence": "1.0",
    }
    row.update(overrides)
    return row


CSV_FIELDNAMES = [
    "vendor_name", "vendor_address", "purchase_date", "purchase_time",
    "line_description", "category", "amount", "tax_amount", "currency",
    "fuel_type", "tractor_or_reefer", "volume_as_received",
    "volume_as_received_unit", "unit_price", "taxes_included",
    "unit_number", "driver", "odometer", "payment_method", "card_last4",
    "receipt_number", "extraction_confidence",
]


def write_csv(pilot: PilotIntake, filename: str, rows: list[dict], *, document_total: float | None = None) -> None:
    import csv

    path = pilot.inbox / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
        if document_total is not None:
            total_row = {name: "" for name in CSV_FIELDNAMES}
            total_row["vendor_name"] = "TOTAL"
            total_row["amount"] = str(document_total)
            writer.writerow(total_row)
