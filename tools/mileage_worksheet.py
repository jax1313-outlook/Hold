#!/usr/bin/env python3
"""Manual mileage entry — writes MileageRecords (source=manual_worksheet).

v1 reality (contracts/mileage_record.schema.json): entered by Mike via
this tool; the schema is identical when Dispatch Ops automates it later.

Usage:
    python tools/mileage_worksheet.py --config path/to/config.json \
        --unit T-104 --jurisdiction TX --period-start 2026-04-01 \
        --period-end 2026-06-30 --miles 1000 --entered-by human:mike
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dispatch.common.config import load_config  # noqa: E402
from dispatch.common.db import bootstrap  # noqa: E402
from dispatch.common.ids import new_ulid  # noqa: E402


def record_mileage(
    config: dict,
    *,
    unit_number: str,
    jurisdiction: str,
    period_start: str,
    period_end: str,
    miles: float,
    entered_by: str,
    odometer_start: int | None = None,
    odometer_end: int | None = None,
    source: str = "manual_worksheet",
) -> str:
    conn = bootstrap(config["database"])
    mileage_record_id = new_ulid()
    conn.execute(
        """
        INSERT INTO mileage_records (
            mileage_record_id, unit_number, period_start, period_end,
            jurisdiction, miles, source, odometer_start, odometer_end,
            entered_by, schema_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '1.0')
        """,
        (
            mileage_record_id, unit_number, period_start, period_end,
            jurisdiction, miles, source, odometer_start, odometer_end, entered_by,
        ),
    )
    return mileage_record_id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="path to a dispatch config JSON file")
    parser.add_argument("--unit", required=True, dest="unit_number")
    parser.add_argument("--jurisdiction", required=True, help="2-char state/province code")
    parser.add_argument("--period-start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--period-end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--miles", required=True, type=float)
    parser.add_argument("--entered-by", required=True, help='e.g. "human:mike"')
    parser.add_argument("--odometer-start", type=int, default=None)
    parser.add_argument("--odometer-end", type=int, default=None)
    args = parser.parse_args()

    config = load_config(args.config)
    mileage_record_id = record_mileage(
        config,
        unit_number=args.unit_number,
        jurisdiction=args.jurisdiction,
        period_start=args.period_start,
        period_end=args.period_end,
        miles=args.miles,
        entered_by=args.entered_by,
        odometer_start=args.odometer_start,
        odometer_end=args.odometer_end,
    )
    print(mileage_record_id)


if __name__ == "__main__":
    main()
