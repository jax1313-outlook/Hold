#!/usr/bin/env python3
"""Creates the OPERATIONS/LIBRARY/ARCHIVE directory skeleton from config.

Per DISPATCH_BUILD_BLUEPRINT_v1 Part 3.4. Only creates the static parts of
the skeleton — subdirectories keyed by a date or quarter (Evidence\\YYYY\\MM,
IFTA\\<quarter>, ReportSnapshots\\YYYY) are created lazily, on demand, by the
code that first needs them (e.g. dispatch.evidence.interface.register()).

Usage: python tools/init_roots.py --config path/to/dispatch.config.json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dispatch.common.config import load_config  # noqa: E402

_STATIC_SKELETON = {
    "operations": [
        "Data",
        "Intake/Drop",
        "Intake/Processing",
        "Intake/Quarantine",
        "PrintQueue",
        "Workers/Manager/TradeMemory",
        "Workers/Receipt/TradeMemory",
        "Workers/IFTA/TradeMemory",
        "Workers/Librarian/TradeMemory",
        "Testing/GoldenSet",
    ],
    "library": [
        "Constitutions",
        "Templates/Reports",
        "Vocabulary",
        "RateTables",
        "EvidenceIndex",
    ],
    "archive": [
        "Evidence",
        "IFTA",
        "ReportSnapshots",
        "AuditRolls",
    ],
}


def init_roots(config: dict) -> list[Path]:
    """Create every static skeleton directory for the given config. Returns
    the list of directories created or already present."""
    created: list[Path] = []
    for tier, subdirs in _STATIC_SKELETON.items():
        root = Path(config["roots"][tier])
        for subdir in subdirs:
            path = root / subdir
            path.mkdir(parents=True, exist_ok=True)
            created.append(path)
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="path to a dispatch config JSON file")
    args = parser.parse_args()

    config = load_config(args.config)
    created = init_roots(config)
    for path in created:
        print(path)


if __name__ == "__main__":
    main()
