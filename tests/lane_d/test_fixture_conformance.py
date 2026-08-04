"""LANE_D_LAUNCH_PACKAGE_v1.md §6 gate 1: conformance of fixtures vs
in-force schemas. Because seeded_pipeline_data is produced by Lane C's
real Router rather than hand-typed rows (see tests/fixtures/README.md),
this validates the rows actually sitting in the sandbox database after
the fixture runs -- not just the router's own unit tests -- against the
same FROZEN v1.0 contracts tests/conformance uses."""
from __future__ import annotations

import jsonschema

from tests.conftest import load_contract_schema

FUEL_SCHEMA = load_contract_schema("fuel_record")
EXPENSE_SCHEMA = load_contract_schema("expense_record")
FORMAT_CHECKER = jsonschema.FormatChecker()


def test_seeded_fuel_records_conform_to_frozen_schema(db_conn, seeded_pipeline_data):
    rows = db_conn.execute("SELECT * FROM fuel_records").fetchall()
    assert len(rows) == 2
    for row in rows:
        record = dict(row)
        record["taxes_included"] = bool(record["taxes_included"])
        jsonschema.validate(record, FUEL_SCHEMA, format_checker=FORMAT_CHECKER)


def test_seeded_expense_records_conform_to_frozen_schema(db_conn, seeded_pipeline_data):
    rows = db_conn.execute("SELECT * FROM expense_records").fetchall()
    assert len(rows) == 3  # 2 fuel-linked + 1 meal
    for row in rows:
        record = dict(row)
        jsonschema.validate(record, EXPENSE_SCHEMA, format_checker=FORMAT_CHECKER)
