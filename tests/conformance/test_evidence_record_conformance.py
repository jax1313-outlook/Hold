"""Contract conformance: dispatch.evidence's real outputs validate against
contracts/evidence_record.schema.json, byte-for-byte on shared fixtures.
This suite is generated once here (Lane A) and reused by every later lane.
"""
from __future__ import annotations

import jsonschema
import pytest

from dispatch.evidence.interface import EvidenceIntegrityError, EvidenceSpine
from tests.conftest import load_contract_schema

SCHEMA = load_contract_schema("evidence_record")
FORMAT_CHECKER = jsonschema.FormatChecker()


def assert_conforms(instance: dict) -> None:
    jsonschema.validate(instance=instance, schema=SCHEMA, format_checker=FORMAT_CHECKER)


def test_register_output_conforms(spine, sample_file, sample_metadata):
    record = spine.register(sample_file, "pump_receipt", sample_metadata)
    assert_conforms(record)


def test_retrieve_output_conforms(spine, sample_file, sample_metadata):
    registered = spine.register(sample_file, "pump_receipt", sample_metadata)
    retrieved, _path = spine.retrieve(registered["evidence_record_id"])
    assert_conforms(retrieved)


def test_duplicate_register_output_conforms(spine, sample_file, sample_metadata):
    spine.register(sample_file, "pump_receipt", sample_metadata)
    duplicate = spine.register(sample_file, "pump_receipt", sample_metadata)
    assert_conforms(duplicate)
    assert duplicate["extraction_status"] == "duplicate_document"


def test_link_children_output_conforms(spine, sample_file, sample_metadata):
    registered = spine.register(sample_file, "pump_receipt", sample_metadata)
    updated = spine.link_children(registered["evidence_record_id"], ["fuel_rec_1", "exp_rec_1"])
    assert_conforms(updated)
    assert updated["derived_record_ids"] == ["fuel_rec_1", "exp_rec_1"]


def test_schema_rejects_missing_required_field():
    incomplete = {"evidence_record_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=incomplete, schema=SCHEMA)


def test_schema_rejects_additional_properties(spine, sample_file, sample_metadata):
    record = spine.register(sample_file, "pump_receipt", sample_metadata)
    record["unexpected_field"] = "not part of the contract"
    with pytest.raises(jsonschema.ValidationError):
        assert_conforms(record)
