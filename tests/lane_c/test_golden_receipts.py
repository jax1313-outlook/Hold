"""Golden regression: the golden receipt set's extractions match blessed
output through routing (LANE_C_LAUNCH_PACKAGE_v1 §6 — further than the
old Packet C's classified-line-only ceiling, since the router is no
longer blocked).

See tests/golden/receipts/*.expected.json's own "blessed": false marker —
this suite proves the pipeline is internally consistent against
fixtures this build session constructed itself, not that Mike has
certified extraction accuracy against real documents. That's a distinct,
later step (LANE_C_LAUNCH_PACKAGE_v1 risk #4).
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from dispatch.receipt.intake import IntakePipeline

GOLDEN_DIR = Path(__file__).resolve().parents[1] / "golden" / "receipts"


def _load_expected(name: str) -> dict:
    with open(GOLDEN_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def test_csv_export_001_routes_as_expected(sandbox_config):
    expected = _load_expected("csv_export_001.expected.json")
    assert expected["blessed"] is False  # sanity check on the fixture itself

    drop_dir = Path(sandbox_config["roots"]["operations"]) / "Intake" / "Drop"
    drop_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(GOLDEN_DIR / expected["source_csv"], drop_dir / expected["source_csv"])

    pipeline = IntakePipeline(sandbox_config)
    summary = pipeline.process_drop()

    assert len(summary["quarantined_lines"]) == expected["expected_quarantined_lines"]
    assert len(summary["routed"]) == len(expected["expected_routed"])

    conn = pipeline._conn
    for expected_line in expected["expected_routed"]:
        if expected_line["creates_fuel_record"]:
            row = conn.execute(
                "SELECT * FROM fuel_records WHERE vendor_name = ?", (expected_line["vendor_name"],)
            ).fetchone()
            assert row is not None
            assert row["jurisdiction"] == expected_line["jurisdiction"]
            assert row["gallons_normalized"] == expected_line["gallons_normalized"]
            assert row["total_amount"] == expected_line["amount"]
            assert row["unit_number"] == expected_line["unit_number"]

            expense_row = conn.execute(
                "SELECT * FROM expense_records WHERE fuel_record_id = ?", (row["fuel_record_id"],)
            ).fetchone()
            assert expense_row is not None
            assert expense_row["category"] == "fuel"
        else:
            row = conn.execute(
                "SELECT * FROM expense_records WHERE vendor_name = ?", (expected_line["vendor_name"],)
            ).fetchone()
            assert row is not None
            assert row["category"] == expected_line["category"]
            assert row["amount"] == expected_line["amount"]
            assert row["fuel_record_id"] is None
