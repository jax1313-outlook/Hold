"""Boundary refusal, verified by grep of the module surface: no UPDATE or
DELETE SQL statement exists anywhere in src/dispatch/receipt against
fuel_records or expense_records — the same static-check pattern Lanes A
and B used for their own immutable tables.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RECEIPT_SRC_DIR = REPO_ROOT / "src" / "dispatch" / "receipt"

_IMMUTABLE_TABLES = ("fuel_records", "expense_records")

_FORBIDDEN_PATTERNS = [
    re.compile(rf"\bUPDATE\s+{table}\b", re.IGNORECASE) for table in _IMMUTABLE_TABLES
] + [
    re.compile(rf"\bDELETE\s+FROM\s+{table}\b", re.IGNORECASE) for table in _IMMUTABLE_TABLES
]


def test_trigger_definitions_do_not_false_positive(db_conn):
    from dispatch.receipt.db import install_schema

    install_schema(db_conn)
    trigger_sql = "\n".join(
        row[0]
        for row in db_conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'trigger'"
        ).fetchall()
        if row[0] and ("fuel_records" in row[0] or "expense_records" in row[0])
    )
    assert "BEFORE UPDATE ON fuel_records" in trigger_sql
    assert "BEFORE DELETE ON fuel_records" in trigger_sql
    for pattern in _FORBIDDEN_PATTERNS:
        assert not pattern.search(trigger_sql), f"{pattern.pattern} unexpectedly matched trigger SQL"


def test_no_update_or_delete_statement_against_immutable_tables():
    offenders = []
    for path in sorted(RECEIPT_SRC_DIR.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for pattern in _FORBIDDEN_PATTERNS:
            if pattern.search(text):
                offenders.append((str(path.relative_to(REPO_ROOT)), pattern.pattern))

    assert offenders == [], f"forbidden UPDATE/DELETE statements found: {offenders}"
