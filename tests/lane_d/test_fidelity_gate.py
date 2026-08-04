"""The deferred final-fidelity gate, made permanent -- REPORTS_CHARTER_v1.md:
"every displayed total equals independent SQL arithmetic... re-run
against real Lane C output on integration before merge 5." That one-time
manual run is recorded in docs/lanes/D/FIDELITY_GATE_REPORT_v1.md; this
file keeps the same rigor as a standing regression so a future change to
queries.py or the worksheet engine can't silently drift without a test
noticing.

Two things this file checks that tests/lane_d/test_queries.py and
test_ifta_position_display_only.py don't already cover:

1. A genuinely multi-jurisdiction, multi-fuel-type, multi-category
   dataset (3 states, 2 fuel types, 6 expense categories) built through
   the real Router -- not the 1-2-jurisdiction fixtures used elsewhere,
   to exercise the breakdown/group-by logic against something with real
   cardinality.
2. IFTA's fleet_mpg and net_tax independently RE-DERIVED from raw
   mileage_records/fuel_records per computation spec 3.5, from scratch,
   without importing anything from dispatch.ifta -- not just compared
   against the stored worksheet value (which test_ifta_position_display_only.py
   already does). This is the strongest form of the fidelity check: even
   if queries.py and WorksheetEngine agreed with each other by sharing a
   bug, this independent arithmetic wouldn't.
"""
from __future__ import annotations

from datetime import date

import pytest

from dispatch.reports import queries


@pytest.fixture
def multi_jurisdiction_data(db_conn, sandbox_config, tmp_path):
    from dispatch.evidence.interface import EvidenceSpine
    from dispatch.receipt.router import Router

    spine = EvidenceSpine(db_conn, sandbox_config["roots"])
    router = Router(db_conn)

    fuel_purchases = [
        # (vendor, address, jurisdiction, date, gallons, unit, price, fuel_type, receipt)
        ("Flying J", "1 Main St, Amarillo, TX 79101", "TX", "2026-07-05", 110.0, "gallons", 4.10, "diesel", "F1"),
        ("Flying J", "1 Main St, Amarillo, TX 79101", "TX", "2026-08-01", 95.0, "gallons", 4.05, "diesel", "F2"),
        ("Pilot", "1 Hwy 40, Joplin, MO 64801", "MO", "2026-07-20", 80.0, "gallons", 4.15, "diesel", "F3"),
        ("TA", "500 I-40, Oklahoma City, OK 73129", "OK", "2026-07-25", 300.0, "liters", 1.05, "diesel", "F4"),
        ("Buc-ee's", "200 N I-35, Waco, TX 76705", "TX", "2026-07-12", 20.0, "gallons", 3.20, "gasoline", "F5"),
    ]
    for vendor, address, _jurisdiction, purchase_date, volume, unit, price, fuel_type, receipt in fuel_purchases:
        doc = tmp_path / f"{receipt}.txt"
        doc.write_text(f"{vendor} receipt")
        record = spine.register(doc, "pump_receipt", {"document_date": purchase_date})
        router.route_line(record["evidence_record_id"], {
            "vendor_name": vendor, "vendor_address": address, "purchase_date": purchase_date,
            "purchase_time": "08:00:00", "line_description": f"{fuel_type} fuel", "category": "fuel",
            "amount": round(volume * price, 2), "tax_amount": 0.0, "currency": "USD",
            "fuel_type": fuel_type, "tractor_or_reefer": "tractor", "volume_as_received": volume,
            "volume_as_received_unit": unit, "unit_price": price, "taxes_included": True,
            "unit_number": "T-104", "driver": "J. Smith", "odometer": 150000,
            "payment_method": "fuel_card", "card_last4": "4321", "receipt_number": receipt,
            "extraction_confidence": 1.0,
        })

    expense_lines = [
        ("Truck Stop Diner", "2026-07-06", "meals", 18.50, "Dinner"),
        ("Truck Stop Diner", "2026-08-02", "meals", 22.75, "Dinner"),
        ("KTA", "2026-07-14", "tolls", 12.00, "Turnpike toll"),
        ("Blue Beacon", "2026-08-05", "truck_wash", 45.00, "Full wash"),
        ("Speedco", "2026-08-18", "parts_maintenance", 310.25, "Oil change"),
        ("City of Amarillo", "2026-09-01", "parking", 8.00, "Overnight parking"),
    ]
    for vendor, purchase_date, category, amount, desc in expense_lines:
        doc = tmp_path / f"exp_{vendor}_{purchase_date}.txt"
        doc.write_text(f"{vendor} receipt")
        record = spine.register(doc, "invoice", {"document_date": purchase_date})
        router.route_line(record["evidence_record_id"], {
            "vendor_name": vendor, "vendor_address": None, "purchase_date": purchase_date,
            "purchase_time": None, "line_description": desc, "category": category,
            "amount": amount, "tax_amount": 0.0, "currency": "USD", "fuel_type": None,
            "tractor_or_reefer": None, "volume_as_received": None, "volume_as_received_unit": None,
            "unit_price": None, "taxes_included": False, "unit_number": "T-104", "driver": "J. Smith",
            "odometer": None, "payment_method": "cash", "card_last4": None, "receipt_number": None,
            "extraction_confidence": 1.0,
        })

    return {"fuel_purchases": fuel_purchases, "expense_lines": expense_lines}


def test_fuel_spend_breakdown_fidelity_across_three_jurisdictions(reports_ro_conn, multi_jurisdiction_data):
    result = queries.fuel_spend_query(reports_ro_conn, date_from=date(2026, 7, 1), date_to=date(2026, 9, 30))

    indep_by_jurisdiction = {}
    for vendor, address, jurisdiction, purchase_date, volume, unit, price, fuel_type, receipt in multi_jurisdiction_data["fuel_purchases"]:
        gallons = volume * 0.264172 if unit == "liters" else volume
        amount = round(volume * price, 2)
        j = indep_by_jurisdiction.setdefault(jurisdiction, {"amount": 0.0, "gallons": 0.0})
        j["amount"] += amount
        j["gallons"] += gallons

    assert {row["jurisdiction"] for row in result["breakdown"]} == set(indep_by_jurisdiction)
    for row in result["breakdown"]:
        expected = indep_by_jurisdiction[row["jurisdiction"]]
        assert row["amount"] == pytest.approx(expected["amount"])
        assert row["gallons"] == pytest.approx(expected["gallons"])
    assert result["total_amount"] == pytest.approx(sum(v["amount"] for v in indep_by_jurisdiction.values()))


def test_expense_summary_breakdown_fidelity_across_six_categories(reports_ro_conn, multi_jurisdiction_data):
    result = queries.expense_summary_query(reports_ro_conn, date_from=date(2026, 7, 1), date_to=date(2026, 9, 30))

    indep_by_category = {}
    for _vendor, _date, category, amount, _desc in multi_jurisdiction_data["expense_lines"]:
        indep_by_category[category] = indep_by_category.get(category, 0.0) + amount
    # every fuel purchase also creates a "fuel"-category expense record (D1 dual-record)
    for vendor, address, jurisdiction, purchase_date, volume, unit, price, fuel_type, receipt in multi_jurisdiction_data["fuel_purchases"]:
        indep_by_category["fuel"] = indep_by_category.get("fuel", 0.0) + round(volume * price, 2)

    displayed_by_category = {row["category"]: row["amount"] for row in result["breakdown"]}
    assert set(displayed_by_category) == set(indep_by_category)
    for category, expected_amount in indep_by_category.items():
        assert displayed_by_category[category] == pytest.approx(expected_amount)


def test_ifta_fleet_mpg_and_net_tax_independently_rederived_from_spec_3_5(reports_ro_conn, seeded_ifta_worksheet, db_conn):
    """The strongest fidelity check: recompute fleet_mpg and net_tax from
    raw mileage_records/fuel_records using computation spec 3.5, entirely
    independently (no import of dispatch.ifta anything), and compare
    against what the read-only query layer returns."""
    result = queries.ifta_position_query(reports_ro_conn, quarter="2026-Q3")

    mileage_rows = db_conn.execute(
        "SELECT jurisdiction, miles FROM mileage_records WHERE period_start = '2026-07-01' AND period_end = '2026-09-30'"
    ).fetchall()
    fuel_rows = db_conn.execute(
        "SELECT jurisdiction, gallons_normalized FROM fuel_records "
        "WHERE fuel_type = 'diesel' AND tractor_or_reefer = 'tractor' "
        "AND purchase_date BETWEEN '2026-07-01' AND '2026-09-30'"
    ).fetchall()

    total_miles = sum(r["miles"] for r in mileage_rows)
    total_gallons = sum(r["gallons_normalized"] for r in fuel_rows)
    indep_fleet_mpg = total_miles / total_gallons

    assert result["worksheets"][0]["fleet_mpg"] == pytest.approx(indep_fleet_mpg)

    miles_by_j: dict[str, float] = {}
    gallons_by_j: dict[str, float] = {}
    for r in mileage_rows:
        miles_by_j[r["jurisdiction"]] = miles_by_j.get(r["jurisdiction"], 0.0) + r["miles"]
    for r in fuel_rows:
        gallons_by_j[r["jurisdiction"]] = gallons_by_j.get(r["jurisdiction"], 0.0) + r["gallons_normalized"]

    rate_by_jurisdiction = {line["jurisdiction"]: line["rate"] for line in result["lines"]}
    indep_total_net_tax = 0.0
    for line in result["lines"]:
        j = line["jurisdiction"]
        taxable_gallons = miles_by_j[j] / indep_fleet_mpg
        tax_paid_gallons = gallons_by_j.get(j, 0.0)
        indep_net_tax = taxable_gallons * rate_by_jurisdiction[j] - tax_paid_gallons * rate_by_jurisdiction[j]
        assert line["net_tax"] == pytest.approx(indep_net_tax)
        indep_total_net_tax += indep_net_tax

    assert result["total_net_tax"] == pytest.approx(indep_total_net_tax)


def test_rendered_html_contains_the_exact_independently_verified_total(reports_ro_conn, multi_jurisdiction_data, seeded_library):
    from dispatch.reports.rendering import render_answer_html
    from dispatch.reports.templates_engine import load_template

    result = queries.fuel_spend_query(reports_ro_conn, date_from=date(2026, 7, 1), date_to=date(2026, 9, 30))
    indep_total = sum(round(volume * price, 2) for _v, _a, _j, _d, volume, _u, price, _f, _r in multi_jurisdiction_data["fuel_purchases"])
    assert result["total_amount"] == pytest.approx(indep_total)

    template = load_template(seeded_library["roots"]["library"], "fuel_spend", "1")
    html = render_answer_html(
        template, result, as_of="2026-08-04T19:00:00Z", period_label="Q3 2026", template_version="1",
    )
    assert f"${result['total_amount']:,.2f}" in html
