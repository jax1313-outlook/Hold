"""One parameterized fuel-card statement format.

A vendor_profile is data, not code: `{"column_map": {<logical field>:
<raw column name>}, "total_row_marker_column": ..., "total_row_marker_value":
...}`. Adding a new vendor is a new profile dict, never a new branch of
inference — RECEIPT_CONSTITUTION_v1's exception list names "unknown
vendor format" as a thing this parser detects and hands to the review
queue, not something it guesses its way past.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import csv

from dispatch.receipt.parsers.common import build_line

# One example vendor profile, built for this lane's own golden fixtures.
# A real second vendor is a second profile dict, added wherever this lane's
# build session decides profiles should live (e.g. a config file) — not
# addressed further here since exactly one is in scope per the launch
# package ("one fuel-card statement format (parameterized)").
EXAMPLE_FUEL_CARD_PROFILE: dict[str, Any] = {
    "vendor_profile_name": "example_fuel_card_co",
    "column_map": {
        "vendor_name": "Merchant",
        "vendor_address": "Merchant Address",
        "purchase_date": "Trans Date",
        "purchase_time": "Trans Time",
        "category": "Category",
        "amount": "Amount",
        "tax_amount": "Tax",
        "currency": "Currency",
        "line_description": "Description",
        "fuel_type": "Fuel Type",
        "tractor_or_reefer": "Reefer Flag",
        "volume_as_received": "Gallons",
        "volume_as_received_unit": "Unit",
        "unit_price": "Price Per Gallon",
        "taxes_included": "Tax Included",
        "unit_number": "Unit Number",
        "driver": "Driver Name",
        "odometer": "Odometer",
        "payment_method": "Payment Method",
        "card_last4": "Card Last 4",
        "receipt_number": "Invoice Number",
    },
    "total_row_marker_column": "Merchant",
    "total_row_marker_value": "TOTAL",
}


def parse(
    path: Path | str, vendor_profile: dict[str, Any]
) -> tuple[list[dict[str, Any]], float | None]:
    column_map = vendor_profile["column_map"]
    marker_column = vendor_profile.get("total_row_marker_column")
    marker_value = (vendor_profile.get("total_row_marker_value") or "").upper()

    lines: list[dict[str, Any]] = []
    document_total: float | None = None

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if marker_column and (row.get(marker_column) or "").strip().upper() == marker_value:
                amount_column = column_map["amount"]
                document_total = float(row[amount_column])
                continue
            lines.append(
                build_line(lambda field, row=row: row.get(column_map.get(field, "")))
            )

    return lines, document_total
