#!/usr/bin/env python3
"""Manual mileage entry — writes MileageRecords (source=manual_worksheet).

v1 reality (contracts/mileage_record.schema.json): entered by Mike via
this tool (or, since 2026-08-05, dispatch.ifta_clerk's mileage-entry
route); the schema is identical when Dispatch Ops automates it later.
The real write lives in dispatch.ifta.mileage.record_mileage() so this
CLI and the UI route share one path rather than two copies of the same
INSERT — this file is a thin argparse wrapper around it.

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
from dispatch.ifta.mileage import record_mileage  # noqa: E402


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
    conn = bootstrap(config["database"])
    mileage_record_id = record_mileage(
        conn,
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
