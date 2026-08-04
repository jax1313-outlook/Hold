#!/usr/bin/env python3
"""Installs library_seed/** into the configured LIBRARY root.

Idempotent and non-destructive by default (LANE_A_LAUNCH_PACKAGE_v1 risk #5):
an existing destination file is left alone unless --force is passed. Safe to
re-run against a LIBRARY root that already has content, e.g. re-running in an
existing sandbox.

Usage:
    python tools/seed_library.py --config path/to/dispatch.config.json
    python tools/seed_library.py --config ... --force
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dispatch.common.config import load_config  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SEED_ROOT = _REPO_ROOT / "library_seed"
_SKIP_NAMES = {".gitkeep"}


def seed_library(config: dict, *, force: bool = False) -> tuple[list[Path], list[Path]]:
    """Copy every file under library_seed/ into config's library root,
    preserving relative structure. Returns (written, skipped) path lists."""
    library_root = Path(config["roots"]["library"])
    written: list[Path] = []
    skipped: list[Path] = []

    for source in sorted(_SEED_ROOT.rglob("*")):
        if source.is_dir():
            continue
        if source.name in _SKIP_NAMES:
            continue
        relative = source.relative_to(_SEED_ROOT)
        destination = library_root / relative

        if destination.exists() and not force:
            skipped.append(destination)
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        written.append(destination)

    return written, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="path to a dispatch config JSON file")
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing destination files instead of skipping them",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    written, skipped = seed_library(config, force=args.force)

    for path in written:
        print(f"wrote {path}")
    for path in skipped:
        print(f"skipped (already exists): {path}")


if __name__ == "__main__":
    main()
