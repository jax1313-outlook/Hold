"""Golden regression: all ten IFTA exception detectors fire from seeded
data (IFTA_CONSTITUTION_v1's exception list)."""
from __future__ import annotations

import json

from dispatch.common.ids import new_ulid
from dispatch.ifta import exceptions, rates
from tests.lane_c.conftest import insert_fuel_record, insert_mileage_record


def _base_two_jurisdiction_seed(db_conn):
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1000.0)
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="OK", period_start="2026-04-01", period_end="2026-06-30", miles=500.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0, unit_number="T-100")
    insert_fuel_record(db_conn, jurisdiction="OK", purchase_date="2026-05-15", gallons_normalized=60.0, unit_number="T-100")
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    rates.insert_rate(db_conn, jurisdiction="OK", quarter="2026-Q2", fuel_type="diesel", rate=0.18, source_version="fixture-v1")


def test_fuel_no_miles_fires(ifta_engine, db_conn):
    _base_two_jurisdiction_seed(db_conn)
    insert_fuel_record(db_conn, jurisdiction="LA", purchase_date="2026-04-20", gallons_normalized=20.0, unit_number="T-100")
    rates.insert_rate(db_conn, jurisdiction="LA", quarter="2026-Q2", fuel_type="diesel", rate=0.19, source_version="fixture-v1")

    worksheet = ifta_engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
    findings = exceptions.fuel_no_miles(worksheet)
    assert any(f["detail"].startswith("LA:") for f in findings)


def test_miles_no_fuel_gap_fires(ifta_engine, db_conn):
    _base_two_jurisdiction_seed(db_conn)
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="AR", period_start="2026-04-01", period_end="2026-06-30", miles=200.0)
    rates.insert_rate(db_conn, jurisdiction="AR", quarter="2026-Q2", fuel_type="diesel", rate=0.22, source_version="fixture-v1")

    worksheet = ifta_engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
    findings = exceptions.miles_no_fuel_gap(worksheet, miles_threshold=50.0)
    assert any(f["detail"].startswith("AR:") for f in findings)


def test_fleet_mpg_out_of_band_fires_when_too_high(ifta_engine, db_conn):
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=10000.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=10.0, unit_number="T-100")
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.20, source_version="fixture-v1")

    worksheet = ifta_engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
    assert worksheet["fleet_mpg"] == 1000.0  # absurdly high, well outside [4.0, 9.5]
    findings = exceptions.fleet_mpg_out_of_band(worksheet)
    assert len(findings) == 1


def test_odometer_discontinuity_fires(ifta_engine, db_conn):
    from datetime import date

    insert_fuel_record(
        db_conn, jurisdiction="TX", purchase_date="2026-04-01", gallons_normalized=50.0,
        unit_number="T-100", odometer=100000,
    )
    second_id = insert_fuel_record(
        db_conn, jurisdiction="TX", purchase_date="2026-04-10", gallons_normalized=50.0,
        unit_number="T-100", odometer=99500,  # went backwards
    )

    findings = exceptions.odometer_discontinuity(ifta_engine._ro_conn, date(2026, 4, 1), date(2026, 6, 30))
    assert any(second_id in f["related_record_ids"] for f in findings)


def test_active_truck_days_no_mileage_fires(ifta_engine, db_conn):
    _base_two_jurisdiction_seed(db_conn)
    insert_fuel_record(db_conn, jurisdiction="NM", purchase_date="2026-04-25", gallons_normalized=30.0, unit_number="T-999")
    rates.insert_rate(db_conn, jurisdiction="NM", quarter="2026-Q2", fuel_type="diesel", rate=0.21, source_version="fixture-v1")

    ifta_engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
    from datetime import date

    findings = exceptions.active_truck_days_no_mileage(ifta_engine._ro_conn, date(2026, 4, 1), date(2026, 6, 30))
    assert any("T-999" in f["detail"] for f in findings)


def test_broken_evidence_linkage_fires(ifta_engine, db_conn, spine):
    from datetime import date

    fuel_record_id = new_ulid()
    expense_record_id = new_ulid()
    db_conn.execute(
        """
        INSERT INTO expense_records (
            expense_record_id, evidence_record_id, fuel_record_id, purchase_date,
            vendor_name, line_description, category, amount, currency, unit_number,
            dedup_key, status, extraction_confidence, review_status, schema_version
        ) VALUES (?, 'nonexistent_evidence_id', ?, '2026-04-15', 'Vendor', 'x', 'fuel', 100.0,
                  'USD', 'T-100', ?, 'staged', 1.0, 'auto', '1.0')
        """,
        (expense_record_id, fuel_record_id, new_ulid()),
    )
    db_conn.execute(
        """
        INSERT INTO fuel_records (
            fuel_record_id, evidence_record_id, expense_record_id, purchase_date,
            vendor_name, vendor_address, jurisdiction, fuel_type, tractor_or_reefer,
            volume_as_received, volume_as_received_unit, gallons_normalized, unit_price,
            total_amount, currency, taxes_included, unit_number, dedup_key,
            extraction_confidence, review_status, schema_version
        ) VALUES (?, 'nonexistent_evidence_id', ?, '2026-04-15', 'Vendor', '1 Rd', 'TX', 'diesel',
                  'tractor', 25.0, 'gallons', 25.0, 4.0, 100.0, 'USD', 1, 'T-100', ?, 1.0, 'auto', '1.0')
        """,
        (fuel_record_id, expense_record_id, new_ulid()),
    )

    findings = exceptions.broken_evidence_linkage(ifta_engine._ro_conn, spine, date(2026, 4, 1), date(2026, 6, 30))
    assert any(fuel_record_id in f["related_record_ids"] for f in findings)


def test_rate_version_mismatch_fires(ifta_engine, db_conn):
    _base_two_jurisdiction_seed(db_conn)
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.25, source_version="fixture-v2")

    worksheet = ifta_engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
    findings = exceptions.rate_version_mismatch(db_conn, worksheet)
    assert any(f["detail"].startswith("TX:") for f in findings)


def test_reefer_in_propulsion_fires(ifta_engine, db_conn):
    # Direct SQL bypassing the router -- simulating the one way this could
    # ever happen (a bug elsewhere, or bad manual data entry), since the
    # router itself refuses this outright (router.ReeferMisroutedError).
    fuel_record_id = new_ulid()
    db_conn.execute(
        """
        INSERT INTO fuel_records (
            fuel_record_id, evidence_record_id, expense_record_id, purchase_date,
            vendor_name, vendor_address, jurisdiction, fuel_type, tractor_or_reefer,
            volume_as_received, volume_as_received_unit, gallons_normalized, unit_price,
            total_amount, currency, taxes_included, unit_number, dedup_key,
            extraction_confidence, review_status, schema_version
        ) VALUES (?, 'ev_x', 'exp_x', '2026-04-15', 'Vendor', '1 Rd', 'TX', 'diesel',
                  'reefer', 25.0, 'gallons', 25.0, 4.0, 100.0, 'USD', 1, 'T-100', ?, 1.0, 'auto', '1.0')
        """,
        (fuel_record_id, new_ulid()),
    )
    findings = exceptions.reefer_in_propulsion(ifta_engine._ro_conn)
    assert any(fuel_record_id in f["related_record_ids"] for f in findings)


def test_corner_clipping_fires(ifta_engine, db_conn):
    _base_two_jurisdiction_seed(db_conn)
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="NM", period_start="2026-04-01", period_end="2026-06-30", miles=2.0)
    rates.insert_rate(db_conn, jurisdiction="NM", quarter="2026-Q2", fuel_type="diesel", rate=0.23, source_version="fixture-v1")

    worksheet = ifta_engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
    findings = exceptions.corner_clipping(worksheet)
    assert any(f["detail"].startswith("NM:") for f in findings)


def test_late_arrival_closed_quarter_fires(ifta_engine, db_conn):
    # Simulate an already-sealed Q1 worksheet directly (bypassing the full
    # package.py seal flow, which is tested separately).
    db_conn.execute(
        """
        INSERT INTO ifta_worksheets (
            ifta_worksheet_id, quarter, fuel_type, fleet_mpg, rate_table_version,
            status, total_net_tax, created_at, sealed_at, queue_item_id, schema_version
        ) VALUES (?, '2026-Q1', 'diesel', 6.0, 'fixture-v1', 'sealed', 0.0, '2026-04-01T00:00:00Z',
                  '2026-04-05T00:00:00Z', NULL, '1.0')
        """,
        (new_ulid(),),
    )
    # A fuel record dated inside that already-sealed Q1, discovered later.
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-02-15", gallons_normalized=40.0, unit_number="T-100")

    findings = exceptions.late_arrival_closed_quarter(db_conn, ifta_engine._ro_conn, "diesel")
    assert len(findings) == 1
    assert "2026-Q1" in findings[0]["detail"]


def test_run_all_detectors_persists_and_queues_findings(ifta_engine, db_conn, spine, ifta_queue_store):
    _base_two_jurisdiction_seed(db_conn)
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="NM", period_start="2026-04-01", period_end="2026-06-30", miles=2.0)  # corner clip
    rates.insert_rate(db_conn, jurisdiction="NM", quarter="2026-Q2", fuel_type="diesel", rate=0.23, source_version="fixture-v1")

    worksheet = ifta_engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
    persisted = exceptions.run_all_detectors(db_conn, ifta_engine._ro_conn, spine, ifta_queue_store, worksheet)

    assert len(persisted) > 0
    rows = db_conn.execute("SELECT COUNT(*) FROM ifta_exceptions").fetchone()[0]
    assert rows == len(persisted)

    queue_rows = db_conn.execute("SELECT COUNT(*) FROM queue_items WHERE source_worker = 'ifta'").fetchone()[0]
    assert queue_rows == len(persisted)
