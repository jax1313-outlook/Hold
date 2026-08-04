"""Integration tests for the whole register -> extract -> validate -> route
pipeline, run the same way process_drop() actually runs it."""
from __future__ import annotations

import csv
from pathlib import Path

from dispatch.receipt.intake import IntakePipeline
from dispatch.receipt.parsers.statement_parser import EXAMPLE_FUEL_CARD_PROFILE

_CSV_COLUMNS = (
    "vendor_name", "vendor_address", "purchase_date", "purchase_time",
    "line_description", "category", "amount", "tax_amount", "currency",
    "fuel_type", "tractor_or_reefer", "volume_as_received",
    "volume_as_received_unit", "unit_price", "taxes_included", "unit_number",
    "driver", "odometer", "payment_method", "card_last4", "receipt_number",
)


def _fuel_row(**overrides) -> dict:
    base = {
        "vendor_name": "Flying J Travel Center",
        "vendor_address": "123 Main St, Amarillo, TX 79101",
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
    return base


def _write_csv(path: Path, rows: list[dict], *, columns=_CSV_COLUMNS, total: float | None = None) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        if total is not None:
            writer.writerow({"vendor_name": "TOTAL", "amount": total})


def _drop_dir(sandbox_config) -> Path:
    drop_dir = Path(sandbox_config["roots"]["operations"]) / "Intake" / "Drop"
    drop_dir.mkdir(parents=True, exist_ok=True)
    return drop_dir


def test_csv_drop_registers_extracts_and_routes(sandbox_config):
    drop_dir = _drop_dir(sandbox_config)
    csv_path = drop_dir / "export_001.csv"
    _write_csv(csv_path, [_fuel_row()])

    pipeline = IntakePipeline(sandbox_config)
    summary = pipeline.process_drop()

    assert len(summary["processed"]) == 1
    assert len(summary["routed"]) == 1
    assert "fuel_record_id" in summary["routed"][0]
    assert not csv_path.exists()  # moved out of Drop
    processed_path = Path(sandbox_config["roots"]["operations"]) / "Intake" / "Processing" / "export_001.csv"
    assert processed_path.exists()


def test_malformed_csv_quarantines_the_whole_file(sandbox_config):
    drop_dir = _drop_dir(sandbox_config)
    bad_path = drop_dir / "broken.csv"
    _write_csv(bad_path, [_fuel_row(vendor_name="")])

    pipeline = IntakePipeline(sandbox_config)
    summary = pipeline.process_drop()

    assert summary["processed"] == []
    assert len(summary["quarantined_files"]) == 1
    assert "evidence_record_id" in summary["quarantined_files"][0]  # registration DID succeed
    assert not bad_path.exists()
    quarantine_path = Path(sandbox_config["roots"]["operations"]) / "Intake" / "Quarantine" / "broken.csv"
    assert quarantine_path.exists()


def test_scanned_image_with_no_vision_credentials_quarantines(sandbox_config, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    drop_dir = _drop_dir(sandbox_config)
    scan_path = drop_dir / "scan_001.jpg"
    scan_path.write_bytes(b"pretend this is a scanned receipt image")

    pipeline = IntakePipeline(sandbox_config)
    summary = pipeline.process_drop()

    assert summary["processed"] == []
    assert len(summary["quarantined_files"]) == 1
    assert "no api key" in summary["quarantined_files"][0]["reason"].lower()
    assert not scan_path.exists()


def test_vendor_profile_routes_to_statement_parser(sandbox_config):
    drop_dir = _drop_dir(sandbox_config)
    columns = list(EXAMPLE_FUEL_CARD_PROFILE["column_map"].values())
    row = {
        "Merchant": "Pilot Travel Centers",
        "Merchant Address": "789 Hwy 40, Joplin, MO 64801",
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
    path = drop_dir / "pilotcard_2026-07.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerow(row)

    profile = dict(EXAMPLE_FUEL_CARD_PROFILE, filename_prefix="pilotcard_")
    pipeline = IntakePipeline(sandbox_config, vendor_profiles=[profile])
    summary = pipeline.process_drop()

    assert len(summary["routed"]) == 1
    assert summary["routed"][0]["fuel_record_id"]


def test_duplicate_transaction_across_two_separate_drops_is_suppressed_not_dropped(sandbox_config):
    drop_dir = _drop_dir(sandbox_config)

    _write_csv(drop_dir / "first.csv", [_fuel_row()])
    pipeline = IntakePipeline(sandbox_config)
    first_summary = pipeline.process_drop()
    assert len(first_summary["routed"]) == 1

    _write_csv(drop_dir / "second.csv", [_fuel_row()])
    second_summary = pipeline.process_drop()

    assert second_summary["routed"] == []
    assert len(second_summary["quarantined_lines"]) == 1
    assert second_summary["quarantined_lines"][0]["reason"] == "duplicate_transaction"

    # Evidence-level: two distinct documents were still both archived (that's
    # Lane A's own file-hash dedup, a different layer) -- but only ONE
    # transaction-level fuel_record exists.
    count = pipeline._conn.execute("SELECT COUNT(*) FROM fuel_records").fetchone()[0]
    assert count == 1


def test_exception_queue_items_are_created_for_every_quarantine(sandbox_config):
    from dispatch.common import audit

    drop_dir = _drop_dir(sandbox_config)
    _write_csv(drop_dir / "broken.csv", [_fuel_row(vendor_name="")])

    pipeline = IntakePipeline(sandbox_config)
    pipeline.process_drop()

    rows = pipeline._conn.execute("SELECT * FROM queue_items WHERE type = 'exception'").fetchall()
    assert len(rows) == 1
    assert rows[0]["status"] == "open"

    entries = audit.read_audit_entries(pipeline._conn)
    receipt_entries = [e for e in entries if e["actor"] == "receipt"]
    assert any(e["outcome"] == "quarantined" for e in receipt_entries)
