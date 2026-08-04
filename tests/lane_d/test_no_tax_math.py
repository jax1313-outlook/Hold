"""Static boundary-refusal test, same technique tests/lane_c uses for its
own grep guards: REPORTS_CHARTER_v1.md bright line #2 ("arithmetic yes,
domain judgment never... it may never compute tax") means this package
must never reference rate_tables, and must never multiply a rate against
anything -- that computation belongs to Lane C's WorksheetEngine alone.
"""
from __future__ import annotations

from pathlib import Path

REPORTS_SRC = Path(__file__).resolve().parents[2] / "src" / "dispatch" / "reports"


def _source_files():
    return sorted(REPORTS_SRC.rglob("*.py"))


def test_reports_never_reference_rate_tables():
    for path in _source_files():
        text = path.read_text(encoding="utf-8")
        assert "rate_tables" not in text, f"{path} references rate_tables directly"


def test_reports_never_multiply_a_rate():
    forbidden_snippets = ["* rate", "rate *", "* surcharge", "surcharge *"]
    for path in _source_files():
        text = path.read_text(encoding="utf-8")
        for snippet in forbidden_snippets:
            assert snippet not in text, f"{path} contains rate arithmetic: {snippet!r}"


def test_reports_never_import_ifta_business_logic():
    forbidden_imports = [
        "from dispatch.ifta.worksheet",
        "from dispatch.ifta.rates",
        "from dispatch.ifta import worksheet",
        "from dispatch.ifta import rates",
        "import dispatch.ifta.worksheet",
    ]
    for path in _source_files():
        text = path.read_text(encoding="utf-8")
        for forbidden in forbidden_imports:
            assert forbidden not in text, f"{path} imports IFTA business logic: {forbidden!r}"
