"""Boundary refusal, verified by grep of the module surface: no UPDATE or
DELETE SQL statement exists anywhere in src/dispatch against
evidence_records, evidence_children, or audit_log.

This is deliberately independent of test_immutability.py's behavioral
tests — a static check that the forbidden statement text is not merely
non-functional but literally absent from the source, per
LANE_A_LAUNCH_PACKAGE_v1 §6.3.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src" / "dispatch"

_IMMUTABLE_TABLES = ("evidence_records", "evidence_children", "audit_log")

# Matches real DML against the table name — e.g. "UPDATE evidence_records"
# or "DELETE FROM audit_log" — while deliberately NOT matching the trigger
# *definitions* in db.py ("BEFORE UPDATE ON evidence_records", "BEFORE
# DELETE ON audit_log"), which exist precisely to forbid those statements.
_FORBIDDEN_PATTERNS = [
    re.compile(rf"\bUPDATE\s+{table}\b", re.IGNORECASE) for table in _IMMUTABLE_TABLES
] + [
    re.compile(rf"\bDELETE\s+FROM\s+{table}\b", re.IGNORECASE) for table in _IMMUTABLE_TABLES
]


def _iter_source_files():
    return sorted(SRC_DIR.rglob("*.py"))


def test_trigger_definitions_do_not_false_positive_on_the_forbidden_patterns(sandbox_config):
    # Sanity check on the check itself: the actual installed trigger SQL
    # (table names substituted in) must not accidentally match what we're
    # searching for, or test_no_update_or_delete_statement_against_immutable_tables
    # would be vacuous. db.py builds these from an f-string template, so we
    # check the live sqlite_master text rather than db.py's own source (which
    # contains the unsubstituted "{table}" placeholder, not a table name).
    from dispatch.common.db import bootstrap

    conn = bootstrap(sandbox_config["database"])
    trigger_sql = "\n".join(
        row[0]
        for row in conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'trigger'"
        ).fetchall()
    )
    assert "BEFORE UPDATE ON evidence_records" in trigger_sql
    assert "BEFORE DELETE ON evidence_records" in trigger_sql
    for pattern in _FORBIDDEN_PATTERNS:
        assert not pattern.search(trigger_sql), f"{pattern.pattern} unexpectedly matched trigger SQL"


def test_no_update_or_delete_statement_against_immutable_tables():
    offenders = []
    for path in _iter_source_files():
        text = path.read_text(encoding="utf-8")
        for pattern in _FORBIDDEN_PATTERNS:
            if pattern.search(text):
                offenders.append((str(path.relative_to(REPO_ROOT)), pattern.pattern))

    assert offenders == [], f"forbidden UPDATE/DELETE statements found: {offenders}"
