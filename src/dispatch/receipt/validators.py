"""Deterministic validators — every extraction path, deterministic or
vision, passes through all four before a single record gets created.

Each quarantine reason here maps to one of RECEIPT_CONSTITUTION_v1's
named exceptions: structural -> "missing required field on a fuel line";
sum_mismatch -> "sum mismatch"; duplicate_transaction -> "suspected
duplicate transaction (suppress + flag, never silently drop)";
low_confidence -> the confidence-threshold rule from the stack rationale.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Any

from dispatch.receipt import dedup
from dispatch.receipt.parsers.common import REQUIRED_LINE_FIELDS
from dispatch.receipt.units import normalize_gallons
from dispatch.receipt.vocabulary import FUEL_CATEGORY

DEFAULT_CONFIDENCE_THRESHOLD = 0.75
DEFAULT_SUM_TOLERANCE = 0.01


@dataclass
class QuarantinedLine:
    line: dict[str, Any]
    reason: str
    detail: str


@dataclass
class ValidationResult:
    accepted: list[dict[str, Any]] = field(default_factory=list)
    quarantined: list[QuarantinedLine] = field(default_factory=list)


def structural_check(line: dict[str, Any]) -> str | None:
    missing = [f for f in REQUIRED_LINE_FIELDS if not line.get(f)]
    return f"missing required field(s): {missing}" if missing else None


def sum_matches(
    lines: list[dict[str, Any]],
    document_total: float | None,
    *,
    tolerance: float = DEFAULT_SUM_TOLERANCE,
) -> bool:
    """No document_total to compare against means nothing to check — not
    every source format supplies one, and the absence of a total is not
    itself an exception this validator raises."""
    if document_total is None:
        return True
    computed = sum(line["amount"] + (line.get("tax_amount") or 0.0) for line in lines)
    return abs(computed - document_total) <= tolerance


def line_dedup_key(line: dict[str, Any]) -> str:
    """Must compute identically to whatever router.py stores on the real
    record, or a genuine duplicate would never be found (see
    src/dispatch/receipt/units.py's docstring)."""
    if line["category"] == FUEL_CATEGORY:
        gallons_normalized = normalize_gallons(
            line.get("volume_as_received"), line.get("volume_as_received_unit")
        )
        return dedup.fuel_dedup_key(
            vendor_name=line["vendor_name"],
            purchase_date=line["purchase_date"],
            total_amount=line["amount"],
            gallons_normalized=gallons_normalized,
            card_last4=line.get("card_last4"),
        )
    return dedup.expense_dedup_key(
        vendor_name=line["vendor_name"],
        purchase_date=line["purchase_date"],
        amount=line["amount"],
        line_description=line["line_description"],
    )


def find_duplicate(conn: sqlite3.Connection, line: dict[str, Any]) -> dict[str, Any] | None:
    key = line_dedup_key(line)
    if line["category"] == FUEL_CATEGORY:
        return dedup.find_fuel_record_by_dedup_key(conn, key)
    return dedup.find_expense_record_by_dedup_key(conn, key)


def validate_document(
    conn: sqlite3.Connection,
    lines: list[dict[str, Any]],
    document_total: float | None,
    *,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    sum_tolerance: float = DEFAULT_SUM_TOLERANCE,
) -> ValidationResult:
    """Runs the whole document through all four validators in order.
    A structural failure is line-level. A sum mismatch is whole-document
    (nothing in an internally-inconsistent document is trustworthy enough
    to route on its own) — everything that passed the structural check
    quarantines together, rather than silently accepting some lines from
    a document whose numbers don't add up. Confidence and dedup are
    line-level again, since they only make sense once the document's own
    arithmetic already checks out."""
    result = ValidationResult()

    structurally_ok: list[dict[str, Any]] = []
    for line in lines:
        problem = structural_check(line)
        if problem:
            result.quarantined.append(QuarantinedLine(line, "structural", problem))
        else:
            structurally_ok.append(line)

    if not sum_matches(structurally_ok, document_total, tolerance=sum_tolerance):
        computed = sum(l["amount"] + (l.get("tax_amount") or 0.0) for l in structurally_ok)
        for line in structurally_ok:
            result.quarantined.append(
                QuarantinedLine(
                    line,
                    "sum_mismatch",
                    f"lines+tax sum to {computed:.2f}, document total is {document_total:.2f}",
                )
            )
        return result

    for line in structurally_ok:
        if line["extraction_confidence"] < confidence_threshold:
            result.quarantined.append(
                QuarantinedLine(
                    line,
                    "low_confidence",
                    f"confidence {line['extraction_confidence']} < {confidence_threshold}",
                )
            )
            continue

        if find_duplicate(conn, line) is not None:
            result.quarantined.append(
                QuarantinedLine(
                    line, "duplicate_transaction", "matches an existing record's dedup_key"
                )
            )
            continue

        result.accepted.append(line)

    return result
