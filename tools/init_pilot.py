#!/usr/bin/env python3
"""Creates the DispatchPilot\\{Inbox,Fuel,Receipts,RateCons,POD,ELD,Misc}
skeleton under the configured OPERATIONS root. Idempotent -- safe to
re-run. Mirrors tools/init_roots.py's pattern for the pilot's own tree.

Usage:
    python tools/init_pilot.py --config path/to/dispatch.config.json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dispatch.common.config import load_config  # noqa: E402
from dispatch.pilot.intake import PilotIntake  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="path to a dispatch config JSON file")
    args = parser.parse_args()

    config = load_config(args.config)
    pilot = PilotIntake(config)
    print(f"DispatchPilot ready at {pilot.pilot_root}")
    for name in sorted(pilot.folders):
        print(f"  {pilot.folders[name]}")


if __name__ == "__main__":
    main()
