"""The closed expense vocabulary — one source of truth.

RECEIPT_CONSTITUTION_v1's boundary clause (#12): "its classification
vocabulary is closed." No worker may extend it, and this lane never
embeds a second copy of the list anywhere else in its own code — every
category check in this package imports CLOSED_VOCABULARY from here.
"""
from __future__ import annotations

import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCHEMA_PATH = _REPO_ROOT / "contracts" / "expense_vocabulary.schema.json"


def load_vocabulary(schema_path: Path | str = _SCHEMA_PATH) -> frozenset[str]:
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    return frozenset(schema["const"])


CLOSED_VOCABULARY: frozenset[str] = load_vocabulary()

# The two categories with special routing behavior (RECEIPT_CONSTITUTION_v1's
# routing table) — named here so router.py never spells them as bare strings
# more than once.
FUEL_CATEGORY = "fuel"
REEFER_FUEL_CATEGORY = "reefer_fuel"
DEF_CATEGORY = "def"

assert {FUEL_CATEGORY, REEFER_FUEL_CATEGORY, DEF_CATEGORY} <= CLOSED_VOCABULARY
