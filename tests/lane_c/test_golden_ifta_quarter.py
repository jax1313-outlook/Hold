"""Golden regression: the hand-computed golden quarter reproduces exactly
from fixture fuel + entered mileage data (LANE_C_LAUNCH_PACKAGE_v1 §6).

See tests/golden/ifta/quarter_2026_Q3.json's own "blessed": false marker:
this proves the worksheet engine's arithmetic matches computation spec
3.5 exactly, not that Mike has certified these numbers against a real
quarter — that requires real rate data this repository doesn't have yet
(library_seed/RateTables/README.md).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dispatch.ifta import rates
from tests.lane_c.conftest import insert_fuel_record, insert_mileage_record

GOLDEN_DIR = Path(__file__).resolve().parents[1] / "golden" / "ifta"


def _load_fixture() -> dict:
    with open(GOLDEN_DIR / "quarter_2026_Q3.json", encoding="utf-8") as f:
        return json.load(f)


def test_golden_quarter_reproduces_exactly(ifta_engine, db_conn):
    fixture = _load_fixture()
    assert fixture["blessed"] is False  # sanity check on the fixture itself

    for row in fixture["mileage"]:
        insert_mileage_record(
            db_conn, unit_number=fixture["unit_number"], jurisdiction=row["jurisdiction"],
            period_start="2026-07-01", period_end="2026-09-30", miles=row["miles"],
        )
    for row in fixture["fuel"]:
        insert_fuel_record(
            db_conn, jurisdiction=row["jurisdiction"], purchase_date=row["purchase_date"],
            gallons_normalized=row["gallons_normalized"], unit_number=fixture["unit_number"],
        )
    for row in fixture["rates"]:
        rates.insert_rate(
            db_conn, jurisdiction=row["jurisdiction"], quarter=fixture["quarter"],
            fuel_type=fixture["fuel_type"], rate=row["rate"],
            source_version=fixture["rate_table_version"],
        )

    worksheet = ifta_engine.build(
        quarter=fixture["quarter"], fuel_type=fixture["fuel_type"],
        rate_table_version=fixture["rate_table_version"],
    )

    assert worksheet["fleet_mpg"] == pytest.approx(fixture["expected"]["fleet_mpg"])
    assert worksheet["total_net_tax"] == pytest.approx(fixture["expected"]["total_net_tax"])

    for expected_line in fixture["expected"]["lines"]:
        actual_line = next(l for l in worksheet["lines"] if l["jurisdiction"] == expected_line["jurisdiction"])
        assert actual_line["taxable_gallons"] == pytest.approx(expected_line["taxable_gallons"])
        assert actual_line["net_tax"] == pytest.approx(expected_line["net_tax"])
