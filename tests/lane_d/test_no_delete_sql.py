"""Static boundary-refusal test: LANE_D_LAUNCH_PACKAGE_v1.md risk #1 --
print_queue never gets a DELETE code path, ever. "Clearing" is the status
transition queued -> printed -> cleared (snapshot.py's clear()); the SQL
string 'DELETE FROM print_queue' must never appear anywhere in this
package's source, and no source file may issue a bare DELETE against any
table at all -- this lane only ever writes via INSERT/UPDATE."""
from __future__ import annotations

from pathlib import Path

REPORTS_SRC = Path(__file__).resolve().parents[2] / "src" / "dispatch" / "reports"


def _source_files():
    return sorted(REPORTS_SRC.rglob("*.py"))


def test_no_delete_from_print_queue_anywhere():
    for path in _source_files():
        text = path.read_text(encoding="utf-8")
        assert "DELETE FROM print_queue" not in text.upper().replace("\n", " "), (
            f"{path} contains a DELETE against print_queue"
        )


def test_no_delete_statement_anywhere_in_reports_source():
    for path in _source_files():
        text = path.read_text(encoding="utf-8")
        assert "DELETE FROM" not in text.upper(), f"{path} issues a DELETE statement"
