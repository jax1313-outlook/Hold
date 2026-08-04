"""Shared line-building logic for the deterministic parsers.

Both csv_parser.py and statement_parser.py produce the same normalized
line shape (Lane C's own internal working shape — not a frozen contract;
validators.py and router.py are what actually turn it into a real
FuelRecord/ExpenseRecord). They differ only in how a logical field name
maps to a raw column, which is why this module takes a `get` callable
rather than a row dict directly.
"""
from __future__ import annotations

from typing import Any, Callable

REQUIRED_LINE_FIELDS = (
    "vendor_name",
    "purchase_date",
    "category",
    "amount",
    "currency",
    "line_description",
)


def _to_float(value: str | None) -> float | None:
    return float(value) if value not in (None, "") else None


def _to_int(value: str | None) -> int | None:
    return int(value) if value not in (None, "") else None


def _to_bool(value: str | None) -> bool:
    return (value or "").strip().lower() in ("true", "1", "yes")


def build_line(get: Callable[[str], str | None]) -> dict[str, Any]:
    """get(field) returns the raw string value for a logical field name, or
    None/empty if absent. Raises ValueError listing every missing required
    field at once, rather than failing on the first one — a caller
    quarantining a bad row wants the whole picture."""
    missing = [f for f in REQUIRED_LINE_FIELDS if not get(f)]
    if missing:
        raise ValueError(f"row missing required field(s): {missing}")

    return {
        "vendor_name": get("vendor_name"),
        "vendor_address": get("vendor_address") or None,
        "purchase_date": get("purchase_date"),
        "purchase_time": get("purchase_time") or None,
        "line_description": get("line_description"),
        "category": get("category"),
        "amount": _to_float(get("amount")),
        "tax_amount": _to_float(get("tax_amount")),
        "currency": get("currency"),
        "fuel_type": get("fuel_type") or None,
        "tractor_or_reefer": get("tractor_or_reefer") or None,
        "volume_as_received": _to_float(get("volume_as_received")),
        "volume_as_received_unit": get("volume_as_received_unit") or None,
        "unit_price": _to_float(get("unit_price")),
        "taxes_included": _to_bool(get("taxes_included")),
        "unit_number": get("unit_number") or None,
        "driver": get("driver") or None,
        "odometer": _to_int(get("odometer")),
        "payment_method": get("payment_method") or None,
        "card_last4": get("card_last4") or None,
        "receipt_number": get("receipt_number") or None,
        "extraction_confidence": 1.0,  # deterministic parse: always exact
    }
