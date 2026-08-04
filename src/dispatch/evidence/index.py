"""Library evidence index.

DISPATCH_BASE_CONSTITUTION_v1 #1 places "evidence index" under LIBRARY (approved
truth), separate from the immutable originals under ARCHIVE. This module is
that index: one JSON file per evidence record, under
LIBRARY/EvidenceIndex/<evidence_record_id>.json, mirroring the record so it
can be browsed/queried without touching ARCHIVE. It is a read-optimized
pointer store, not a second system of record — evidence_records in
dispatch.db remains authoritative; the index is derived from it.

Scope note (LIBRARIAN_CONSTITUTION_v1 "Explicitly NOT in Group 1"): this is
the evidence index only. Truth promotion, retrieval governance, and Library
metadata beyond this index are a later lane.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_INDEX_SUBDIR = "EvidenceIndex"


def _index_dir(library_root: Path | str) -> Path:
    return Path(library_root) / _INDEX_SUBDIR


def _index_path(library_root: Path | str, evidence_record_id: str) -> Path:
    return _index_dir(library_root) / f"{evidence_record_id}.json"


def write_index_entry(library_root: Path | str, record: dict[str, Any]) -> Path:
    """Write (or overwrite) the index entry for one evidence record. Called
    once per newly-registered record; never called for a duplicate hit,
    since no new record is created in that case."""
    index_dir = _index_dir(library_root)
    index_dir.mkdir(parents=True, exist_ok=True)
    path = _index_path(library_root, record["evidence_record_id"])
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def read_index_entry(library_root: Path | str, evidence_record_id: str) -> dict[str, Any] | None:
    path = _index_path(library_root, evidence_record_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def iter_index(library_root: Path | str):
    """Yield every indexed record, for tools/tests that need the whole set."""
    index_dir = _index_dir(library_root)
    if not index_dir.exists():
        return
    for path in sorted(index_dir.glob("*.json")):
        yield json.loads(path.read_text(encoding="utf-8"))
