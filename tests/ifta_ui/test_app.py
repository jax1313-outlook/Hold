"""dispatch.ifta.app -- build+exceptions together, real error handling,
seal genuinely blocked/unblocked, append-only rates, and mileage entry
matching the CLI tool's own schema. Same rigor every other lane's tests
already use."""
from __future__ import annotations

from pathlib import Path

import pytest

from dispatch.queue.store import QueueStore
from tests.ifta_ui.conftest import insert_mileage


def _build(client, *, quarter, fuel_type, rate_table_version):
    return client.post("/build", data={
        "quarter": quarter, "fuel_type": fuel_type, "rate_table_version": rate_table_version,
    })


# --- Build produces the worksheet and its exceptions together ------------


def test_build_creates_worksheet_and_persists_it(client, db_conn, sandbox_config, seeded_fuel_and_mileage):
    from dispatch.ifta import rates
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q3", fuel_type="diesel", rate=0.20, source_version="fixture-v1")

    resp = _build(client, quarter="2026-Q3", fuel_type="diesel", rate_table_version="fixture-v1")
    assert resp.status_code == 302

    row = db_conn.execute("SELECT * FROM ifta_worksheets WHERE quarter = '2026-Q3'").fetchone()
    assert row is not None
    assert row["status"] == "draft"
    assert row["fleet_mpg"] == pytest.approx(7.0)

    detail = client.get(resp.headers["Location"])
    assert detail.status_code == 200
    body = detail.data.decode()
    assert "7.00" in body  # fleet mpg shown
    assert "Exceptions (0)" in body  # 100gal/700mi is well within the plausible band


def test_build_also_runs_exception_detectors_and_shows_them_on_the_same_page(client, db_conn, sandbox_config, tmp_path):
    """Deliberately implausible mileage vs. fuel -- exercises the real
    fleet_mpg_out_of_band detector, shown alongside the worksheet."""
    from dispatch.evidence.interface import EvidenceSpine
    from dispatch.ifta import rates
    from dispatch.receipt.router import Router

    spine = EvidenceSpine(db_conn, sandbox_config["roots"])
    router = Router(db_conn)
    doc = tmp_path / "receipt.txt"
    doc.write_text("fuel receipt")
    record = spine.register(doc, "pump_receipt", {"document_date": "2026-08-01"})
    router.route_line(record["evidence_record_id"], {
        "vendor_name": "Flying J", "vendor_address": "1 Main St, Amarillo, TX 79101",
        "purchase_date": "2026-08-01", "purchase_time": "09:00:00", "line_description": "Diesel",
        "category": "fuel", "amount": 400.0, "tax_amount": 0.0, "currency": "USD",
        "fuel_type": "diesel", "tractor_or_reefer": "tractor", "volume_as_received": 100.0,
        "volume_as_received_unit": "gallons", "unit_price": 4.0, "taxes_included": True,
        "unit_number": "T-104", "driver": "J. Smith", "odometer": 100000,
        "payment_method": "fuel_card", "card_last4": "4321", "receipt_number": "RCT-1",
        "extraction_confidence": 1.0,
    })
    insert_mileage(db_conn, jurisdiction="TX", period_start="2026-07-01", period_end="2026-09-30", miles=50.0)
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q3", fuel_type="diesel", rate=0.20, source_version="fixture-v1")

    resp = _build(client, quarter="2026-Q3", fuel_type="diesel", rate_table_version="fixture-v1")
    detail = client.get(resp.headers["Location"])
    body = detail.data.decode()
    assert "fleet_mpg_out_of_band" in body

    findings = db_conn.execute("SELECT exception_type FROM ifta_exceptions").fetchall()
    assert any(f["exception_type"] == "fleet_mpg_out_of_band" for f in findings)
    queue_exceptions = db_conn.execute(
        "SELECT subject FROM queue_items WHERE type = 'exception'"
    ).fetchall()
    assert any("fleet_mpg_out_of_band" in q["subject"] for q in queue_exceptions)


# --- Errors render clearly, never a raw 500 -------------------------------


def test_build_with_missing_rate_shows_a_clear_error(client, seeded_fuel_and_mileage):
    resp = _build(client, quarter="2026-Q3", fuel_type="diesel", rate_table_version="no-such-version")
    assert resp.status_code == 400
    assert "no rate found" in resp.data.decode().lower()


def test_build_with_no_data_at_all_shows_a_clear_error(client):
    resp = _build(client, quarter="2026-Q1", fuel_type="diesel", rate_table_version="fixture-v1")
    assert resp.status_code == 400
    body = resp.data.decode()
    assert "cannot compute fleet_mpg" in body or "no tractor" in body.lower()


def test_build_on_a_genuinely_fresh_install_does_not_crash(client, db_conn):
    """Regression test: on a database where no receipt has ever been
    processed, fuel_records doesn't exist at all yet (WorksheetEngine's
    own _aggregate_fuel() has no table-existence guard -- a real,
    pre-existing gap this UI build found and worked around, not fixed at
    the source; see docs/ifta-ui/NOTES.md). Confirm the table genuinely
    doesn't exist, then confirm Build still renders a clear error, not a
    raw 500."""
    exists = db_conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'fuel_records'"
    ).fetchone()
    assert exists is None

    resp = _build(client, quarter="2026-Q3", fuel_type="diesel", rate_table_version="fixture-v1")
    assert resp.status_code == 400
    assert "no fuel or mileage data recorded yet" in resp.data.decode()


def test_build_with_malformed_quarter_shows_a_clear_error(client):
    resp = _build(client, quarter="not-a-quarter", fuel_type="diesel", rate_table_version="fixture-v1")
    assert resp.status_code == 400
    assert "quarter" in resp.data.decode().lower()


# --- Seal genuinely blocked before approval, works after -----------------


def test_seal_is_blocked_before_approval_and_the_page_says_why(client, db_conn, sandbox_config, seeded_fuel_and_mileage):
    from dispatch.ifta import rates
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q3", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    build_resp = _build(client, quarter="2026-Q3", fuel_type="diesel", rate_table_version="fixture-v1")
    worksheet_url = build_resp.headers["Location"]
    worksheet_id = worksheet_url.rstrip("/").split("/")[-1]

    detail = client.get(worksheet_url)
    assert "not submitted for approval yet" in detail.data.decode()

    seal_resp = client.post(f"/worksheets/{worksheet_id}/seal")
    assert seal_resp.status_code == 302
    row = db_conn.execute("SELECT status FROM ifta_worksheets WHERE ifta_worksheet_id = ?", (worksheet_id,)).fetchone()
    assert row["status"] == "draft"  # the real refusal held -- did not seal


def test_submit_then_approve_through_the_real_queue_then_seal_works(client, db_conn, sandbox_config, seeded_fuel_and_mileage):
    from dispatch.ifta import rates
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q3", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    build_resp = _build(client, quarter="2026-Q3", fuel_type="diesel", rate_table_version="fixture-v1")
    worksheet_id = build_resp.headers["Location"].rstrip("/").split("/")[-1]

    submit_resp = client.post(f"/worksheets/{worksheet_id}/submit")
    assert submit_resp.status_code == 302

    detail = client.get(f"/worksheets/{worksheet_id}")
    assert "waiting on approval" in detail.data.decode()

    row = db_conn.execute(
        "SELECT queue_item_id FROM ifta_worksheets WHERE ifta_worksheet_id = ?", (worksheet_id,)
    ).fetchone()
    QueueStore(db_conn).approve(row["queue_item_id"], decided_by="human:mike", decision_note="looks right")

    detail_after_approval = client.get(f"/worksheets/{worksheet_id}")
    assert "waiting on approval" not in detail_after_approval.data.decode()

    seal_resp = client.post(f"/worksheets/{worksheet_id}/seal")
    assert seal_resp.status_code == 302
    sealed_row = db_conn.execute(
        "SELECT status, sealed_at FROM ifta_worksheets WHERE ifta_worksheet_id = ?", (worksheet_id,)
    ).fetchone()
    assert sealed_row["status"] == "sealed"
    assert sealed_row["sealed_at"] is not None

    archive_root = Path(sandbox_config["roots"]["archive"])
    bundle_path = archive_root / "IFTA" / "2026-Q3" / f"{worksheet_id}.json"
    assert bundle_path.is_file()


def test_seal_button_missing_worksheet_is_404(client):
    resp = client.post("/worksheets/does-not-exist/seal")
    assert resp.status_code == 404


# --- Rates: append-only ----------------------------------------------------


def test_rate_entry_creates_a_new_row(client, db_conn):
    resp = client.post("/rates", data={
        "jurisdiction": "TX", "quarter": "2026-Q3", "fuel_type": "diesel",
        "rate": "0.20", "surcharge": "", "source_version": "2026Q3-official",
    })
    assert resp.status_code == 302
    row = db_conn.execute(
        "SELECT * FROM rate_tables WHERE jurisdiction = 'TX' AND source_version = '2026Q3-official'"
    ).fetchone()
    assert row is not None
    assert row["rate"] == 0.20


def test_rate_entry_with_bad_input_shows_a_clear_error(client):
    resp = client.post("/rates", data={
        "jurisdiction": "TX", "quarter": "2026-Q3", "fuel_type": "diesel",
        "rate": "not-a-number", "source_version": "2026Q3-official",
    })
    assert resp.status_code == 400
    assert "could not add rate" in resp.data.decode().lower()


def test_rates_page_lists_existing_rates(client, db_conn):
    from dispatch.ifta import rates
    rates.insert_rate(db_conn, jurisdiction="MO", quarter="2026-Q3", fuel_type="diesel", rate=0.19, source_version="fixture-v1")
    resp = client.get("/rates")
    body = resp.data.decode()
    assert "MO" in body and "0.19" in body


def test_ifta_source_never_issues_update_or_delete_on_rate_tables():
    app_py = (Path(__file__).resolve().parents[2] / "src" / "dispatch" / "ifta" / "app.py").read_text().upper()
    assert "UPDATE RATE_TABLES" not in app_py
    assert "DELETE FROM RATE_TABLES" not in app_py


# --- Mileage entry matches the CLI tool's own schema ----------------------


def test_mileage_entry_creates_a_record_matching_the_cli_tools_shape(client, db_conn):
    resp = client.post("/mileage", data={
        "unit_number": "T-104", "jurisdiction": "TX",
        "period_start": "2026-07-01", "period_end": "2026-09-30",
        "miles": "1000", "entered_by": "human:mike",
    })
    assert resp.status_code == 302
    row = db_conn.execute(
        "SELECT * FROM mileage_records WHERE unit_number = 'T-104' AND jurisdiction = 'TX'"
    ).fetchone()
    assert row is not None
    assert row["miles"] == 1000.0
    assert row["source"] == "manual_worksheet"
    assert row["schema_version"] == "1.0"
    assert row["entered_by"] == "human:mike"


def test_mileage_entry_requires_entered_by(client):
    resp = client.post("/mileage", data={
        "unit_number": "T-104", "jurisdiction": "TX",
        "period_start": "2026-07-01", "period_end": "2026-09-30",
        "miles": "1000", "entered_by": "",
    })
    assert resp.status_code == 400
    assert "entered_by is required" in resp.data.decode()


def test_mileage_page_lists_existing_records(client, db_conn):
    insert_mileage(db_conn, jurisdiction="OK", period_start="2026-07-01", period_end="2026-09-30", miles=500.0)
    resp = client.get("/mileage")
    body = resp.data.decode()
    assert "OK" in body and "500.0" in body


# --- Fresh install doesn't crash -------------------------------------------


def test_index_does_not_crash_on_a_brand_new_database(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_worksheet_detail_for_unknown_id_is_404(client):
    resp = client.get("/worksheets/does-not-exist")
    assert resp.status_code == 404
