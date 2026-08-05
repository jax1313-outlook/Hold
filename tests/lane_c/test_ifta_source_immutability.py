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
    """_aggregate_mileage/_aggregate_fuel are module-level and generic over
    whichever connection they're handed (build() and preview() share them)
    -- so the read-only guarantee is no longer one literal
    'self._ro_conn.execute' substring, it's that every call site in this
    file passes a read-only connection, never the write one. Checked
    exhaustively rather than by example."""
    text = (IFTA_SRC_DIR / "worksheet.py").read_text(encoding="utf-8")
    for table in _SOURCE_TABLES:
        assert f"FROM {table}" in text

    call_sites = re.findall(r"(?<!def )_aggregate_(?:mileage|fuel)\(\s*([\w\.]+)", text)
    assert len(call_sites) >= 2, f"expected calls to both aggregators, found {call_sites}"
    for first_arg in call_sites:
        assert first_arg in ("self._ro_conn", "read_only_conn"), (
            f"_aggregate_mileage/_aggregate_fuel called with {first_arg!r} instead of a "
            "read-only connection -- source-immutability would no longer be enforced"
        )
