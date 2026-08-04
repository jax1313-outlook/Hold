"""DispatchPilot's Inbox sorter -- exercised end to end through the real
Evidence Spine and the real, unmodified Lane C intake pipeline, the same
rigor every other lane's tests use in this repo."""
from __future__ import annotations

from pathlib import Path

import pytest

from dispatch.pilot.intake import PILOT_FOLDERS, classify
from tests.pilot.conftest import drop, fuel_csv_row, meal_csv_row, write_csv

# --- classify() unit tests: deterministic, token-bounded, no inference ----


@pytest.mark.parametrize(
    "filename, expected_route, expected_type",
    [
        ("ratecon_acme_load44.pdf", "RateCons", "rate_confirmation"),
        ("RateCon_Acme_Load44.PDF", "RateCons", "rate_confirmation"),
        ("2026-08-04_ratecons_batch.csv", "RateCons", "rate_confirmation"),
        ("load44_rc.pdf", "RateCons", "rate_confirmation"),
        ("pod_load44.jpg", "POD", "proof_of_delivery"),
        ("proof_pod_signed.png", "POD", "proof_of_delivery"),
        ("eld_export_july.csv", "ELD", "eld_export"),
        ("driver_eld_logs.pdf", "ELD", "eld_export"),
    ],
)
def test_classify_keyword_routes(tmp_path, filename, expected_route, expected_type):
    path = tmp_path / filename
    path.write_text("dummy")
    route, document_type = classify(path)
    assert (route, document_type) == (expected_route, expected_type)


def test_classify_does_not_false_match_substring_inside_a_longer_word(tmp_path):
    """'tripod.pdf' must NOT match the 'pod' keyword route -- token-bounded
    matching, not a raw substring search."""
    path = tmp_path / "tripod_mount.pdf"
    path.write_text("dummy")
    route, document_type = classify(path)
    assert route == "receipt"  # falls through to the .pdf receipt-candidate path instead
    assert document_type is None


@pytest.mark.parametrize("filename", ["fuel_export.csv", "receipt.pdf", "scan.jpg", "photo.PNG"])
def test_classify_receipt_candidate_extensions_with_no_keyword(tmp_path, filename):
    path = tmp_path / filename
    path.write_text("dummy")
    assert classify(path) == ("receipt", None)


@pytest.mark.parametrize("filename", ["notes.docx", "readme.txt", "spreadsheet.xlsx", "data"])
def test_classify_unrecognized_extension_falls_to_misc(tmp_path, filename):
    path = tmp_path / filename
    path.write_text("dummy")
    assert classify(path) == ("Misc", "unclassified")


def test_pilot_folders_are_exactly_the_seven_named(pilot):
    assert PILOT_FOLDERS == ("Inbox", "Fuel", "Receipts", "RateCons", "POD", "ELD", "Misc")
    for name in PILOT_FOLDERS:
        assert pilot.folders[name].is_dir()


# --- end-to-end: a real fuel receipt through the real Lane C pipeline -----


def test_fuel_csv_routes_through_real_pipeline_and_lands_in_fuel_folder(pilot, db_conn):
    write_csv(pilot, "fuel_export.csv", [fuel_csv_row()], document_total=400.0)

    summary = pilot.process_inbox()

    assert len(summary["receipt_batch"]) == 1
    outcome = summary["receipt_batch"][0]
    assert outcome["destination_folder"] == "Fuel"
    assert (pilot.folders["Fuel"] / "fuel_export.csv").is_file()
    assert not (pilot.inbox / "fuel_export.csv").exists()

    fuel_rows = db_conn.execute("SELECT * FROM fuel_records").fetchall()
    assert len(fuel_rows) == 1
    assert fuel_rows[0]["total_amount"] == 400.0


def test_meal_only_csv_lands_in_receipts_folder_not_fuel(pilot, db_conn):
    write_csv(pilot, "meal_receipt.csv", [meal_csv_row()], document_total=23.5)  # amount 22.0 + tax_amount 1.5

    summary = pilot.process_inbox()

    outcome = summary["receipt_batch"][0]
    assert outcome["destination_folder"] == "Receipts"
    assert (pilot.folders["Receipts"] / "meal_receipt.csv").is_file()
    assert not (pilot.folders["Fuel"] / "meal_receipt.csv").exists()

    fuel_rows = db_conn.execute("SELECT * FROM fuel_records").fetchall()
    assert len(fuel_rows) == 0


def test_mixed_fuel_and_expense_csv_lands_in_fuel_folder_not_split(pilot, db_conn):
    """Documented simplification: a single file with both fuel and
    non-fuel lines is filed wherever its most notable outcome is (fuel),
    not split across two folders."""
    write_csv(
        pilot, "mixed_export.csv",
        [fuel_csv_row(receipt_number="RCT-A"), meal_csv_row(receipt_number="RCT-B")],
        document_total=423.5,  # fuel (400.0 + 0.0 tax) + meal (22.0 + 1.5 tax)
    )

    summary = pilot.process_inbox()

    outcome = summary["receipt_batch"][0]
    assert outcome["destination_folder"] == "Fuel"
    assert (pilot.folders["Fuel"] / "mixed_export.csv").is_file()


def test_malformed_csv_quarantines_and_is_not_copied_into_any_pilot_folder(pilot, db_conn):
    """The real failure path: a document total that doesn't match its
    lines fails the real validators and quarantines exactly the way Lane
    C's own tests already prove -- no new quarantine path invented."""
    write_csv(pilot, "broken_export.csv", [fuel_csv_row()], document_total=99999.0)

    summary = pilot.process_inbox()

    # registered + extracted, but the only line quarantined on the sum
    # mismatch -- no fuel/expense record, and nothing copied anywhere in
    # DispatchPilot's tree (it's visible through the real Queue instead).
    outcome = summary["receipt_batch"][0]
    assert outcome["destination_folder"] is None
    for folder_name in ("Fuel", "Receipts", "RateCons", "POD", "ELD", "Misc"):
        assert not (pilot.folders[folder_name] / "broken_export.csv").exists()

    queue_items = db_conn.execute(
        "SELECT subject, priority FROM queue_items WHERE priority = 'today'"
    ).fetchall()
    assert any("quarantined" in item["subject"] for item in queue_items)


# --- end-to-end: document types this system can't process yet ------------


@pytest.mark.parametrize(
    "filename, folder, document_type",
    [
        ("ratecon_acme_load44.pdf", "RateCons", "rate_confirmation"),
        ("pod_load44_signed.jpg", "POD", "proof_of_delivery"),
        ("eld_export_2026_07.csv", "ELD", "eld_export"),
        ("some_random_thing.docx", "Misc", "unclassified"),
    ],
)
def test_unprocessable_types_register_as_real_evidence_and_file_correctly(
    pilot, db_conn, filename, folder, document_type
):
    drop(pilot, filename, "not a real document, just pilot test content")

    summary = pilot.process_inbox()

    assert len(summary["held_for_review"]) == 1
    entry = summary["held_for_review"][0]
    assert entry["folder"] == folder
    assert entry["document_type"] == document_type

    # Real, governed evidence -- not a lesser/secondary path.
    evidence_row = db_conn.execute(
        "SELECT * FROM evidence_records WHERE evidence_record_id = ?", (entry["evidence_record_id"],)
    ).fetchone()
    assert evidence_row is not None
    assert evidence_row["document_type"] == document_type
    assert len(evidence_row["file_hash"]) == 64  # real SHA-256, not a placeholder

    assert (pilot.folders[folder] / filename).is_file()
    assert not (pilot.inbox / filename).exists()


def test_held_for_review_queue_item_is_whenever_priority_not_urgent(pilot, db_conn):
    """Distinguishable from a genuine intake failure (Lane C's quarantine
    is 'urgent'/'exception') -- nothing is wrong with a RateCon, it's just
    a type this system doesn't process yet."""
    drop(pilot, "ratecon_test.pdf", "content")
    summary = pilot.process_inbox()

    queue_item_id = summary["held_for_review"][0]["queue_item_id"]
    item = db_conn.execute(
        "SELECT type, priority, subject FROM queue_items WHERE queue_item_id = ?", (queue_item_id,)
    ).fetchone()
    assert item["type"] == "review"
    assert item["priority"] == "whenever"
    assert "awaiting future processing" in item["subject"]


def test_held_for_review_writes_both_librarian_and_pilot_audit_entries(pilot, db_conn):
    drop(pilot, "pod_test.jpg", "content")
    pilot.process_inbox()

    actions = {row["actor"]: row["action"] for row in db_conn.execute(
        "SELECT actor, action FROM audit_log ORDER BY audit_id"
    ).fetchall()}
    assert actions.get("librarian") == "evidence.register"
    assert actions.get("manager") == "queue.create"
    assert actions.get("pilot") == "pilot.hold_for_review"


# --- batch behavior --------------------------------------------------------


def test_mixed_batch_in_one_inbox_all_route_correctly_in_a_single_call(pilot, db_conn):
    write_csv(pilot, "fuel_export.csv", [fuel_csv_row()], document_total=400.0)
    drop(pilot, "ratecon_load1.pdf", "content")
    drop(pilot, "pod_load1.jpg", "content")
    drop(pilot, "eld_july.csv", "content")
    drop(pilot, "weird_file.docx", "content")

    summary = pilot.process_inbox()

    assert len(summary["receipt_batch"]) == 1
    assert summary["receipt_batch"][0]["destination_folder"] == "Fuel"
    assert len(summary["held_for_review"]) == 4

    assert not any(pilot.inbox.iterdir())  # every file left the Inbox


def test_inbox_empty_after_processing_and_second_call_is_a_safe_no_op(pilot):
    drop(pilot, "pod_only.jpg", "content")
    first = pilot.process_inbox()
    assert len(first["held_for_review"]) == 1

    second = pilot.process_inbox()
    assert second == {"receipt_batch": [], "held_for_review": []}
