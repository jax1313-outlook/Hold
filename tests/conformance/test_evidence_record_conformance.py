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


# --- v1.1 amendment (2026-08-04, Evidence First Doctrine): document_type
# gained rate_confirmation, proof_of_delivery, eld_export, unclassified.
# Additive only -- both the new values and every pre-existing value must
# keep working, registered through the same real EvidenceSpine.register(),
# no secondary path.

NEW_DOCUMENT_TYPES = ("rate_confirmation", "proof_of_delivery", "eld_export", "unclassified")
PRE_EXISTING_DOCUMENT_TYPES = (
    "pump_receipt", "fuel_card_statement", "credit_card_statement",
    "invoice", "csv_export", "email_attachment",
)


@pytest.mark.parametrize("document_type", NEW_DOCUMENT_TYPES)
def test_register_conforms_for_each_new_v1_1_document_type(spine, sample_file, sample_metadata, document_type):
    record = spine.register(sample_file, document_type, sample_metadata)
    assert_conforms(record)
    assert record["document_type"] == document_type
    assert record["schema_version"] == "1.1"


@pytest.mark.parametrize("document_type", PRE_EXISTING_DOCUMENT_TYPES)
def test_register_still_conforms_for_every_pre_existing_document_type(spine, sample_file, sample_metadata, document_type):
    """The amendment is additive -- none of the six original values were
    renamed, removed, or reinterpreted."""
    record = spine.register(sample_file, document_type, sample_metadata)
    assert_conforms(record)
    assert record["document_type"] == document_type


def test_schema_still_rejects_a_type_outside_the_now_ten_value_enum():
    incomplete_but_otherwise_shaped = {
        "evidence_record_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "archive_path": "Evidence\\2026\\08\\x.pdf",
        "file_hash": "a" * 64,
        "document_type": "made_up_type_not_in_the_enum",
        "document_date": "2026-08-04",
        "capture_date": "2026-08-04T00:00:00Z",
        "derived_record_ids": [],
        "extraction_status": "complete",
        "retention_class": "ifta_4yr",
        "schema_version": "1.1",
    }
    with pytest.raises(jsonschema.ValidationError):
        assert_conforms(incomplete_but_otherwise_shaped)
