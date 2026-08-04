import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from mileage_worksheet import record_mileage  # noqa: E402


def test_record_mileage_writes_a_row(sandbox_config, db_conn):
    mileage_record_id = record_mileage(
        sandbox_config,
        unit_number="T-104",
        jurisdiction="TX",
        period_start="2026-04-01",
        period_end="2026-06-30",
        miles=1234.5,
        entered_by="human:mike",
    )

    row = db_conn.execute(
        "SELECT * FROM mileage_records WHERE mileage_record_id = ?", (mileage_record_id,)
    ).fetchone()
    assert row["unit_number"] == "T-104"
    assert row["jurisdiction"] == "TX"
    assert row["miles"] == 1234.5
    assert row["source"] == "manual_worksheet"
    assert row["entered_by"] == "human:mike"


def test_record_mileage_accepts_optional_odometer(sandbox_config, db_conn):
    mileage_record_id = record_mileage(
        sandbox_config,
        unit_number="T-104",
        jurisdiction="OK",
        period_start="2026-04-01",
        period_end="2026-06-30",
        miles=500.0,
        entered_by="human:mike",
        odometer_start=100000,
        odometer_end=100500,
    )
    row = db_conn.execute(
        "SELECT odometer_start, odometer_end FROM mileage_records WHERE mileage_record_id = ?",
        (mileage_record_id,),
    ).fetchone()
    assert row["odometer_start"] == 100000
    assert row["odometer_end"] == 100500
