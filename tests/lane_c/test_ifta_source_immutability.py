"""Boundary refusal, verified by grep of the module surface: no UPDATE or
DELETE SQL statement against fuel_records or mileage_records exists
anywhere in src/dispatch/ifta — the IFTA Agent reads them only through a
mode=ro connection (behavioral proof is in test_worksheet.py's
test_read_only_connection_rejects_any_write); this is the complementary
static proof, same pattern as every other lane's immutable-table checks.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
IFTA_SRC_DIR = REPO_ROOT / "src" / "dispatch" / "ifta"

_SOURCE_TABLES = ("fuel_records", "mileage_records")

_FORBIDDEN_PATTERNS = [
    re.compile(rf"\bUPDATE\s+{table}\b", re.IGNORECASE) for table in _SOURCE_TABLES
] + [
    re.compile(rf"\bDELETE\s+FROM\s+{table}\b", re.IGNORECASE) for table in _SOURCE_TABLES
]


def test_no_update_or_delete_against_source_records():
    offenders = []
    for path in sorted(IFTA_SRC_DIR.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for pattern in _FORBIDDEN_PATTERNS:
            if pattern.search(text):
                offenders.append((str(path.relative_to(REPO_ROOT)), pattern.pattern))

    assert offenders == [], f"forbidden UPDATE/DELETE against source records found: {offenders}"


def test_worksheet_engine_reads_source_tables_through_the_read_only_connection():
    text = (IFTA_SRC_DIR / "worksheet.py").read_text(encoding="utf-8")
    assert "self._ro_conn.execute" in text
    for table in _SOURCE_TABLES:
        assert f"FROM {table}" in text
