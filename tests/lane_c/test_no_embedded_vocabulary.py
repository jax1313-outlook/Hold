"""Boundary refusal: no second copy of the closed vocabulary anywhere in
this lane's code — RECEIPT_CONSTITUTION_v1: "its classification
vocabulary is closed... no worker may extend it." vocabulary.py is the
one place the list is allowed to exist; every other file imports from it.
"""
from __future__ import annotations

from pathlib import Path

from dispatch.receipt.vocabulary import CLOSED_VOCABULARY

REPO_ROOT = Path(__file__).resolve().parents[2]
RECEIPT_SRC_DIR = REPO_ROOT / "src" / "dispatch" / "receipt"
_VOCABULARY_FILE = RECEIPT_SRC_DIR / "vocabulary.py"


def test_only_vocabulary_module_contains_the_full_closed_list():
    offenders = []
    for path in sorted(RECEIPT_SRC_DIR.rglob("*.py")):
        if path == _VOCABULARY_FILE:
            continue
        text = path.read_text(encoding="utf-8")
        present = [category for category in CLOSED_VOCABULARY if f'"{category}"' in text or f"'{category}'" in text]
        if len(present) == len(CLOSED_VOCABULARY):
            offenders.append(str(path.relative_to(REPO_ROOT)))

    assert offenders == [], f"a second full copy of the vocabulary was found in: {offenders}"


def test_router_and_validators_import_from_vocabulary_module():
    router_text = (RECEIPT_SRC_DIR / "router.py").read_text(encoding="utf-8")
    validators_text = (RECEIPT_SRC_DIR / "validators.py").read_text(encoding="utf-8")
    assert "from dispatch.receipt.vocabulary import" in router_text
    assert "from dispatch.receipt.vocabulary import" in validators_text
