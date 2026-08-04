"""Contract conformance for mileage_records.

Lane A only bootstraps this table (Lane C writes to it later per
LANE_A_LAUNCH_PACKAGE_v1 §5) — this suite proves the table Lane A creates
actually has the shape contracts/mileage_record.schema.json expects, so a
fixture row round-trips byte-for-byte.
"""
from __future__ import annotations

import jsonschema

from tests.conftest import load_contract_schema

SCHEMA = load_contract_schema("mileage_record")
FORMAT_CHECKER = jsonschema.FormatChecker()

FIXTURE = {
    "mileage_record_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
    "unit_number": "T-104",
    "period_start": "2026-07-01",
    "period_end": "2026-09-30",
    "jurisdiction": "TX",
    "miles": 4213.5,
    "source": "manual_worksheet",
    "odometer_start": 102934.0,
    "odometer_end": 107148.0,
    "entered_by": "human:mike",
    "schema_version": "1.0",
}


def test_fixture_conforms_to_schema():
    jsonschema.validate(instance=FIXTURE, schema=SCHEMA, format_checker=FORMAT_CHECKER)


def test_table_round_trips_fixture_byte_for_byte(db_conn):
    db_conn.execute(
        """
        INSERT INTO mileage_records (
            mileage_record_id, unit_number, period_start, period_end,
            jurisdiction, miles, source, odometer_start, odometer_end,
            entered_by, schema_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            FIXTURE["mileage_record_id"],
            FIXTURE["unit_number"],
            FIXTURE["period_start"],
            FIXTURE["period_end"],
            FIXTURE["jurisdiction"],
            FIXTURE["miles"],
            FIXTURE["source"],
            FIXTURE["odometer_start"],
            FIXTURE["odometer_end"],
            FIXTURE["entered_by"],
            FIXTURE["schema_version"],
        ),
    )
    row = db_conn.execute(
        "SELECT * FROM mileage_records WHERE mileage_record_id = ?",
        (FIXTURE["mileage_record_id"],),
    ).fetchone()
    assert dict(row) == FIXTURE
    jsonschema.validate(instance=dict(row), schema=SCHEMA, format_checker=FORMAT_CHECKER)
