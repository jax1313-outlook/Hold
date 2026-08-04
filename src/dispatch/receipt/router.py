"""Router — converts validated, classified line items into real
FuelRecord/ExpenseRecord rows, per RECEIPT_CONSTITUTION_v1's routing
table.

The one thing this module must never get backwards: reefer-flagged fuel
and DEF must never produce a FuelRecord, under any circumstance, even
though both are "fuel" in casual language. tests/lane_c has a dedicated
negative test for exactly this (LANE_C_LAUNCH_PACKAGE_v1 risk #6).
"""
from __future__ import annotations

import sqlite3
from typing import Any

from dispatch.common.ids import new_ulid
from dispatch.receipt import dedup
from dispatch.receipt.address import derive_jurisdiction
from dispatch.receipt.db import install_schema
from dispatch.receipt.units import normalize_gallons
from dispatch.receipt.vocabulary import CLOSED_VOCABULARY, FUEL_CATEGORY

DEFAULT_RETENTION_REVIEW_STATUS = "auto"


class RoutingError(ValueError):
    """Base class for reasons a line can't be routed. Callers (intake.py)
    catch this broadly and quarantine the line with the message as
    detail — there is no need for per-subclass handling upstream."""


class UnclassifiableCategoryError(RoutingError):
    def __init__(self, category: str):
        super().__init__(f"category {category!r} is not in the closed vocabulary")
        self.category = category


class MissingUnitAttributionError(RoutingError):
    def __init__(self):
        super().__init__("fuel line has no unit_number — never guess which truck")


class ReeferMisroutedError(RoutingError):
    def __init__(self):
        super().__init__(
            "a reefer-flagged line was categorized 'fuel' instead of 'reefer_fuel' — "
            "refusing to create a FuelRecord for it"
        )


class Router:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        install_schema(conn)

    def route_line(self, evidence_record_id: str, line: dict[str, Any]) -> dict[str, Any]:
        category = line["category"]
        if category not in CLOSED_VOCABULARY:
            raise UnclassifiableCategoryError(category)

        if category == FUEL_CATEGORY:
            return self._route_propulsion_fuel(evidence_record_id, line)
        return self._route_expense_only(evidence_record_id, line)

    # -- propulsion fuel: BOTH FuelRecord + ExpenseRecord, cross-linked ------

    def _route_propulsion_fuel(self, evidence_record_id: str, line: dict[str, Any]) -> dict[str, Any]:
        if (line.get("tractor_or_reefer") or "tractor") == "reefer":
            # Belt-and-suspenders: correctly classified reefer fuel should
            # already carry category == "reefer_fuel", not "fuel". Reaching
            # here means something upstream misclassified it — refuse
            # outright rather than create the one record type this routing
            # table exists to prevent.
            raise ReeferMisroutedError()

        if not line.get("unit_number"):
            raise MissingUnitAttributionError()

        jurisdiction = derive_jurisdiction(line.get("vendor_address"))
        gallons_normalized = normalize_gallons(
            line.get("volume_as_received"), line.get("volume_as_received_unit")
        )
        fuel_key = dedup.fuel_dedup_key(
            vendor_name=line["vendor_name"],
            purchase_date=line["purchase_date"],
            total_amount=line["amount"],
            gallons_normalized=gallons_normalized,
            card_last4=line.get("card_last4"),
        )
        expense_key = dedup.expense_dedup_key(
            vendor_name=line["vendor_name"],
            purchase_date=line["purchase_date"],
            amount=line["amount"],
            line_description=line["line_description"],
        )

        expense_record_id = new_ulid()
        fuel_record_id = new_ulid()

        self._conn.execute(
            """
            INSERT INTO expense_records (
                expense_record_id, evidence_record_id, fuel_record_id,
                purchase_date, vendor_name, vendor_location, line_description,
                category, amount, tax_amount, currency, payment_method,
                card_last4, unit_number, driver, load_id, dedup_key, status,
                quickbooks_ref, extraction_confidence, review_status, schema_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                expense_record_id,
                evidence_record_id,
                fuel_record_id,
                line["purchase_date"],
                line["vendor_name"],
                line.get("vendor_address"),
                line["line_description"],
                FUEL_CATEGORY,
                line["amount"],
                line.get("tax_amount"),
                line["currency"],
                line.get("payment_method"),
                line.get("card_last4"),
                line.get("unit_number"),
                line.get("driver"),
                None,
                expense_key,
                "staged",
                None,
                line["extraction_confidence"],
                DEFAULT_RETENTION_REVIEW_STATUS,
                "1.0",
            ),
        )

        self._conn.execute(
            """
            INSERT INTO fuel_records (
                fuel_record_id, evidence_record_id, expense_record_id,
                purchase_date, purchase_time, vendor_name, vendor_address,
                jurisdiction, fuel_type, tractor_or_reefer, volume_as_received,
                volume_as_received_unit, gallons_normalized, unit_price,
                total_amount, currency, taxes_included, unit_number, driver,
                odometer, payment_method, card_last4, receipt_number,
                dedup_key, extraction_confidence, review_status, schema_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fuel_record_id,
                evidence_record_id,
                expense_record_id,
                line["purchase_date"],
                line.get("purchase_time"),
                line["vendor_name"],
                line["vendor_address"],
                jurisdiction,
                line.get("fuel_type") or "diesel",
                "tractor",
                line.get("volume_as_received") or 0.0,
                line.get("volume_as_received_unit") or "gallons",
                gallons_normalized,
                line.get("unit_price") or 0.0,
                line["amount"],
                line["currency"],
                1 if line.get("taxes_included") else 0,
                line["unit_number"],
                line.get("driver"),
                line.get("odometer"),
                line.get("payment_method"),
                line.get("card_last4"),
                line.get("receipt_number"),
                fuel_key,
                line["extraction_confidence"],
                DEFAULT_RETENTION_REVIEW_STATUS,
                "1.0",
            ),
        )

        return {"fuel_record_id": fuel_record_id, "expense_record_id": expense_record_id}

    # -- everything else: ExpenseRecord only ---------------------------------

    def _route_expense_only(self, evidence_record_id: str, line: dict[str, Any]) -> dict[str, Any]:
        expense_key = dedup.expense_dedup_key(
            vendor_name=line["vendor_name"],
            purchase_date=line["purchase_date"],
            amount=line["amount"],
            line_description=line["line_description"],
        )
        expense_record_id = new_ulid()

        self._conn.execute(
            """
            INSERT INTO expense_records (
                expense_record_id, evidence_record_id, fuel_record_id,
                purchase_date, vendor_name, vendor_location, line_description,
                category, amount, tax_amount, currency, payment_method,
                card_last4, unit_number, driver, load_id, dedup_key, status,
                quickbooks_ref, extraction_confidence, review_status, schema_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                expense_record_id,
                evidence_record_id,
                None,
                line["purchase_date"],
                line["vendor_name"],
                line.get("vendor_address"),
                line["line_description"],
                line["category"],
                line["amount"],
                line.get("tax_amount"),
                line["currency"],
                line.get("payment_method"),
                line.get("card_last4"),
                line.get("unit_number"),
                line.get("driver"),
                None,
                expense_key,
                "staged",
                None,
                line["extraction_confidence"],
                DEFAULT_RETENTION_REVIEW_STATUS,
                "1.0",
            ),
        )
        return {"expense_record_id": expense_record_id}
