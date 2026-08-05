"""tools/mileage_worksheet.py is a thin CLI wrapper around
dispatch.ifta.mileage.record_mileage() (full coverage in
tests/lane_c/test_mileage.py) -- this just proves the re-export
actually resolves to a working function, not a broken import."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from mileage_worksheet import record_mileage  # noqa: E402


def test_tool_reexport_writes_a_real_row(db_conn):
    mileage_record_id = record_mileage(
        db_conn,
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
    assert row["miles"] == 1234.5
    assert row["source"] == "manual_worksheet"
