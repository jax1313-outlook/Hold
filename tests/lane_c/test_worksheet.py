"""IFTA worksheet engine — computation spec 3.5, and the source-immutability
enforcement mechanism (a genuine mode=ro connection, not just "the code
doesn't happen to write here")."""
from __future__ import annotations

import json
import sqlite3

import pytest

from dispatch.ifta import rates
from dispatch.ifta.worksheet import (
    InsufficientDataError,
    InvalidQuarterError,
    MissingRateError,
    latest_worksheet_for,
    live_fleet_mpg_estimate,
    quarter_bounds,
)
from tests.lane_c.conftest import insert_fuel_record, insert_mileage_record


def test_quarter_bounds():
    from datetime import date

    assert quarter_bounds("2026-Q2") == (date(2026, 4, 1), date(2026, 6, 30))
    assert quarter_bounds("2026-Q1") == (date(2026, 1, 1), date(2026, 3, 31))
    assert quarter_bounds("2026-Q4") == (date(2026, 10, 1), date(2026, 12, 31))


def test_quarter_bounds_rejects_malformed_input():
    with pytest.raises(InvalidQuarterError):
        quarter_bounds("Q2-2026")


def _seed_two_jurisdiction_quarter(db_conn):
    insert_mileage_record(
        db_conn, unit_number="T-100", jurisdiction="TX",
        period_start="2026-04-01", period_end="2026-06-30", miles=1000.0,
    )
    insert_mileage_record(
        db_conn, unit_number="T-100", jurisdiction="OK",
        period_start="2026-04-01", period_end="2026-06-30", miles=500.0,
    )
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0)
    insert_fuel_record(db_conn, jurisdiction="OK", purchase_date="2026-05-15", gallons_normalized=60.0)

    rates.insert_rate(
        db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel",
        rate=0.20, source_version="fixture-v1",
    )
    rates.insert_rate(
        db_conn, jurisdiction="OK", quarter="2026-Q2", fuel_type="diesel",
        rate=0.18, source_version="fixture-v1",
    )


def test_build_worksheet_computes_fleet_mpg_and_per_jurisdiction_tax(ifta_engine, db_conn):
    _seed_two_jurisdiction_quarter(db_conn)

    worksheet = ifta_engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")

    assert worksheet["status"] == "draft"
    assert worksheet["fleet_mpg"] == pytest.approx(1500.0 / 160.0)
    assert len(worksheet["lines"]) == 2

    tx_line = next(l for l in worksheet["lines"] if l["jurisdiction"] == "TX")
    ok_line = next(l for l in worksheet["lines"] if l["jurisdiction"] == "OK")

    fleet_mpg = 1500.0 / 160.0
    expected_tx_taxable = 1000.0 / fleet_mpg
    expected_ok_taxable = 500.0 / fleet_mpg
    assert tx_line["taxable_gallons"] == pytest.approx(expected_tx_taxable)
    assert tx_line["net_tax"] == pytest.approx(expected_tx_taxable * 0.20 - 100.0 * 0.20)
    assert ok_line["net_tax"] == pytest.approx(expected_ok_taxable * 0.18 - 60.0 * 0.18)

    assert worksheet["total_net_tax"] == pytest.approx(tx_line["net_tax"] + ok_line["net_tax"])
    assert worksheet["rate_table_version"] == "fixture-v1"


def test_build_captures_which_records_fed_each_jurisdiction_line(ifta_engine, db_conn):
    """related_record_ids is provenance, not arithmetic -- captured
    alongside the sums at build() time so the Archive Package
    (package.py's sealed bundle) can trace a jurisdiction's numbers back
    to the real records behind them, frozen exactly like the numbers
    themselves rather than re-derived later."""
    tx_mileage_id = insert_mileage_record(
        db_conn, unit_number="T-100", jurisdiction="TX",
        period_start="2026-04-01", period_end="2026-06-30", miles=1000.0,
    )
    ok_mileage_id = insert_mileage_record(
        db_conn, unit_number="T-100", jurisdiction="OK",
        period_start="2026-04-01", period_end="2026-06-30", miles=500.0,
    )
    tx_fuel_id = insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0)
    ok_fuel_id = insert_fuel_record(db_conn, jurisdiction="OK", purchase_date="2026-05-15", gallons_normalized=60.0)
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    rates.insert_rate(db_conn, jurisdiction="OK", quarter="2026-Q2", fuel_type="diesel", rate=0.18, source_version="fixture-v1")

    worksheet = ifta_engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
    tx_line = next(l for l in worksheet["lines"] if l["jurisdiction"] == "TX")
    ok_line = next(l for l in worksheet["lines"] if l["jurisdiction"] == "OK")

    tx_related = json.loads(tx_line["related_record_ids"])
    ok_related = json.loads(ok_line["related_record_ids"])
    assert tx_related == {"mileage_record_ids": [tx_mileage_id], "fuel_record_ids": [tx_fuel_id]}
    assert ok_related == {"mileage_record_ids": [ok_mileage_id], "fuel_record_ids": [ok_fuel_id]}


def test_live_fleet_mpg_estimate_matches_a_real_build_with_no_rate_needed(ifta_engine, db_conn):
    """Deliberately does NOT call rates.insert_rate() at all -- proving
    the estimate needs no rate table, unlike preview()."""
    insert_mileage_record(
        db_conn, unit_number="T-100", jurisdiction="TX",
        period_start="2026-04-01", period_end="2026-06-30", miles=700.0,
    )
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0)

    estimate = live_fleet_mpg_estimate(ifta_engine._ro_conn, quarter="2026-Q2", fuel_type="diesel")
    assert estimate == pytest.approx(7.0)


def test_live_fleet_mpg_estimate_returns_none_with_no_data_at_all(ifta_engine):
    assert live_fleet_mpg_estimate(ifta_engine._ro_conn, quarter="2026-Q2", fuel_type="diesel") is None


def test_live_fleet_mpg_estimate_returns_none_with_mileage_but_no_fuel(ifta_engine, db_conn):
    insert_mileage_record(
        db_conn, unit_number="T-100", jurisdiction="TX",
        period_start="2026-04-01", period_end="2026-06-30", miles=700.0,
    )
    assert live_fleet_mpg_estimate(ifta_engine._ro_conn, quarter="2026-Q2", fuel_type="diesel") is None


def test_missing_rate_raises_rather_than_fabricating(ifta_engine, db_conn):
    insert_mileage_record(
        db_conn, unit_number="T-100", jurisdiction="TX",
        period_start="2026-04-01", period_end="2026-06-30", miles=1000.0,
    )
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0)
    # No rate inserted at all.

    with pytest.raises(MissingRateError) as exc_info:
        ifta_engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
    assert "TX" in exc_info.value.jurisdictions


def test_no_fuel_data_raises_insufficient_data(ifta_engine, db_conn):
    insert_mileage_record(
        db_conn, unit_number="T-100", jurisdiction="TX",
        period_start="2026-04-01", period_end="2026-06-30", miles=1000.0,
    )
    with pytest.raises(InsufficientDataError):
        ifta_engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")


def test_mileage_outside_quarter_bounds_is_excluded(ifta_engine, db_conn):
    insert_mileage_record(
        db_conn, unit_number="T-100", jurisdiction="TX",
        period_start="2026-01-01", period_end="2026-03-31", miles=1000.0,  # Q1, not Q2 -- excluded
    )
    insert_mileage_record(
        db_conn, unit_number="T-100", jurisdiction="OK",
        period_start="2026-04-01", period_end="2026-06-30", miles=200.0,  # in-quarter, keeps total_miles > 0
    )
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0)
    rates.insert_rate(
        db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel",
        rate=0.20, source_version="fixture-v1",
    )
    rates.insert_rate(
        db_conn, jurisdiction="OK", quarter="2026-Q2", fuel_type="diesel",
        rate=0.18, source_version="fixture-v1",
    )

    worksheet = ifta_engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
    tx_line = next(l for l in worksheet["lines"] if l["jurisdiction"] == "TX")
    assert tx_line["miles"] == 0.0  # the Q1 mileage never counted


def test_read_only_connection_rejects_any_write(ifta_engine):
    with pytest.raises(sqlite3.OperationalError):
        ifta_engine._ro_conn.execute(
            "UPDATE fuel_records SET vendor_name = 'tampered' WHERE 1=1"
        )
    with pytest.raises(sqlite3.OperationalError):
        ifta_engine._ro_conn.execute("DELETE FROM mileage_records WHERE 1=1")
    with pytest.raises(sqlite3.OperationalError):
        ifta_engine._ro_conn.execute(
            "INSERT INTO queue_items (queue_item_id, type, source_worker, created_at, "
            "priority, subject, status) VALUES ('x', 'exception', 'ifta', 'now', 'today', 'x', 'open')"
        )


def test_latest_worksheet_for_returns_none_when_none_exists(ifta_engine, db_conn):
    assert latest_worksheet_for(db_conn, quarter="2026-Q2", fuel_type="diesel") is None


def test_latest_worksheet_for_returns_none_on_a_genuinely_fresh_database(sandbox_config):
    from dispatch.common.db import bootstrap

    conn = bootstrap(sandbox_config["database"])
    try:
        assert latest_worksheet_for(conn, quarter="2026-Q2", fuel_type="diesel") is None
    finally:
        conn.close()


def test_latest_worksheet_for_finds_a_real_built_worksheet(ifta_engine, db_conn):
    _seed_two_jurisdiction_quarter(db_conn)
    built = ifta_engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")

    found = latest_worksheet_for(db_conn, quarter="2026-Q2", fuel_type="diesel")

    assert found is not None
    assert found["ifta_worksheet_id"] == built["ifta_worksheet_id"]
    assert found["total_net_tax"] == built["total_net_tax"]
    assert len(found["lines"]) == len(built["lines"])


def test_latest_worksheet_for_ignores_a_different_quarter_or_fuel_type(ifta_engine, db_conn):
    _seed_two_jurisdiction_quarter(db_conn)
    ifta_engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")

    assert latest_worksheet_for(db_conn, quarter="2026-Q3", fuel_type="diesel") is None
    assert latest_worksheet_for(db_conn, quarter="2026-Q2", fuel_type="gasoline") is None


def test_latest_worksheet_for_returns_the_most_recently_created_one(ifta_engine, db_conn):
    _seed_two_jurisdiction_quarter(db_conn)
    ifta_engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")

    # A second rate version, so a second build for the same quarter is
    # possible (real IFTA rate corrections are new-version rows, not
    # edits -- same pattern test_rate_version_mismatch_fires uses).
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.25, source_version="fixture-v2")
    rates.insert_rate(db_conn, jurisdiction="OK", quarter="2026-Q2", fuel_type="diesel", rate=0.19, source_version="fixture-v2")
    second_built = ifta_engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v2")

    found = latest_worksheet_for(db_conn, quarter="2026-Q2", fuel_type="diesel")
    assert found["ifta_worksheet_id"] == second_built["ifta_worksheet_id"]
    assert found["rate_table_version"] == "fixture-v2"
