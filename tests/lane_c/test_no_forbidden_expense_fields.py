"""Boundary refusal: no GL codes, deductibility, tax treatment, or
reimbursement status anywhere — RECEIPT_CONSTITUTION_v1's boundary
clause names these explicitly as accounting judgments the Receipt Agent
must never render."""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RECEIPT_SRC_DIR = REPO_ROOT / "src" / "dispatch" / "receipt"

_FORBIDDEN_TERMS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (r"gl[_ ]?code", r"gl[_ ]?account", r"deductib", r"tax[_ ]?treatment", r"reimburs")
]


def test_expense_record_schema_has_no_forbidden_fields():
    schema_path = REPO_ROOT / "contracts" / "expense_record.schema.json"
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)
    for field_name in schema["properties"]:
        for pattern in _FORBIDDEN_TERMS:
            assert not pattern.search(field_name), f"forbidden field {field_name!r} found in schema"


def test_no_forbidden_terms_anywhere_in_receipt_source():
    offenders = []
    for path in sorted(RECEIPT_SRC_DIR.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for pattern in _FORBIDDEN_TERMS:
            if pattern.search(text):
                offenders.append((str(path.relative_to(REPO_ROOT)), pattern.pattern))

    assert offenders == [], f"forbidden accounting-judgment terms found: {offenders}"
