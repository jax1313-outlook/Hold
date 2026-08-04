#!/usr/bin/env python3
"""Exports audit_log to ARCHIVE\\AuditRolls\\YYYY-MM.jsonl, monthly.

Per DISPATCH_BUILD_BLUEPRINT_v1 Part 1.6. Groups every row in audit_log by
the month of its `ts` field and (re)writes one JSONL file per month —
one JSON object per line, contract-shaped (array fields decoded, not the raw
SQLite TEXT). Each run fully rewrites the months it touches from the
database's current state, so reruns are idempotent rather than appending
duplicate lines.

Usage:
    python tools/export_audit_rolls.py --config path/to/dispatch.config.json
    python tools/export_audit_rolls.py --config ... --month 2026-08
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dispatch.common import audit  # noqa: E402
from dispatch.common.config import load_config  # noqa: E402
from dispatch.common.db import bootstrap  # noqa: E402


def export_audit_rolls(config: dict, *, month: str | None = None) -> dict[str, Path]:
    """Write one AuditRolls/YYYY-MM.jsonl file per month present in
    audit_log (or just `month`, if given). Returns {month: path_written}."""
    archive_root = Path(config["roots"]["archive"])
    conn = bootstrap(config["database"])
    entries = audit.read_audit_entries(conn)

    by_month: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        entry_month = entry["ts"][:7]  # "YYYY-MM-DD..." -> "YYYY-MM"
        if month is not None and entry_month != month:
            continue
        by_month[entry_month].append(entry)

    rolls_dir = archive_root / "AuditRolls"
    rolls_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}
    for entry_month, month_entries in sorted(by_month.items()):
        path = rolls_dir / f"{entry_month}.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for entry in month_entries:
                f.write(json.dumps(entry, sort_keys=True) + "\n")
        written[entry_month] = path

    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="path to a dispatch config JSON file")
    parser.add_argument(
        "--month", default=None, help="restrict export to one YYYY-MM (default: all months)"
    )
    args = parser.parse_args()

    config = load_config(args.config)
    written = export_audit_rolls(config, month=args.month)

    if not written:
        print("no audit_log entries matched; nothing written")
    for entry_month, path in sorted(written.items()):
        print(f"{entry_month} -> {path}")


if __name__ == "__main__":
    main()
