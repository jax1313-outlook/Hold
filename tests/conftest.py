"""Shared fixtures for tests/conformance and tests/lane_a.

Every fixture here builds a throwaway sandbox rooted under pytest's tmp_path
— never anything resembling a D:\\ production path — so the config-schema's
sandbox-refusal rule is trivially satisfied and every test is isolated from
every other.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dispatch.common.db import bootstrap
from dispatch.evidence.interface import EvidenceSpine

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS_DIR = REPO_ROOT / "contracts"


@pytest.fixture
def sandbox_config(tmp_path) -> dict:
    roots = {
        "operations": str(tmp_path / "Operations"),
        "library": str(tmp_path / "Library"),
        "archive": str(tmp_path / "Archive"),
    }
    return {
        "environment": "sandbox",
        "roots": roots,
        "database": str(Path(roots["operations"]) / "Data" / "dispatch.db"),
        "schema_versions": {
            "fuel_record": "1.0",
            "expense_record": "1.0",
            "evidence_record": "1.0",
            "mileage_record": "1.0",
            "queue_item": "1.0",
            "audit_entry": "1.0",
        },
    }


@pytest.fixture
def sandbox_config_path(tmp_path, sandbox_config) -> Path:
    path = tmp_path / "sandbox.config.json"
    path.write_text(json.dumps(sandbox_config), encoding="utf-8")
    return path


@pytest.fixture
def db_conn(sandbox_config):
    conn = bootstrap(sandbox_config["database"])
    yield conn
    conn.close()


@pytest.fixture
def spine(db_conn, sandbox_config) -> EvidenceSpine:
    return EvidenceSpine(db_conn, sandbox_config["roots"])


@pytest.fixture
def sample_file(tmp_path) -> Path:
    path = tmp_path / "sample_pump_receipt.txt"
    path.write_text("PUMP RECEIPT\nVendor: Flying J\nTotal: $42.17\n", encoding="utf-8")
    return path


@pytest.fixture
def sample_metadata() -> dict:
    return {
        "document_date": "2026-08-01",
        "capture_date": "2026-08-04T12:00:00Z",
        "vendor": "Flying J",
    }


def load_contract_schema(name: str) -> dict:
    """name is a contract file's stem, e.g. 'evidence_record'."""
    with open(CONTRACTS_DIR / f"{name}.schema.json", "r", encoding="utf-8") as f:
        return json.load(f)
