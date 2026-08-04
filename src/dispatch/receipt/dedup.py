"""Transaction-level dedup — contract 1.2's dedup_key.

Two dedup layers, two owners (LIBRARIAN_CONSTITUTION_v1): Lane A's
file_hash catches the same *document* arriving twice; this module catches
the same *transaction* arriving twice on two different documents (a pump
receipt and a fuel-card statement line for the same purchase). A
collision here means "don't create a second record," never "discard the
evidence" — the underlying document is still archived and its line still
visible via the exception this module's caller raises.
"""
from __future__ import annotations

import hashlib
import sqlite3
from typing import Any


def fuel_dedup_key(
    *,
    vendor_name: str,
    purchase_date: str,
    total_amount: float,
    gallons_normalized: float,
    card_last4: str | None,
) -> str:
    """Verbatim formula, DISPATCH_BUILD_BLUEPRINT_v1 Part 1.2:
    sha256(vendor_name + purchase_date + total_amount + gallons_normalized + card_last4)."""
    raw = f"{vendor_name}|{purchase_date}|{total_amount}|{gallons_normalized}|{card_last4 or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def expense_dedup_key(
    *, vendor_name: str, purchase_date: str, amount: float, line_description: str
) -> str:
    """The contract lists dedup_key as required on ExpenseRecord but gives
    no formula (unlike FuelRecord's verbatim one) — this is Lane C's own
    choice, flagged in docs/lanes/C/NOTES.md, built on the same fields
    the FuelRecord formula uses where an ExpenseRecord equivalent exists."""
    raw = f"{vendor_name}|{purchase_date}|{amount}|{line_description}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def find_fuel_record_by_dedup_key(conn: sqlite3.Connection, dedup_key: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM fuel_records WHERE dedup_key = ?", (dedup_key,)
    ).fetchone()
    return dict(row) if row is not None else None


def find_expense_record_by_dedup_key(
    conn: sqlite3.Connection, dedup_key: str
) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM expense_records WHERE dedup_key = ?", (dedup_key,)
    ).fetchone()
    return dict(row) if row is not None else None
