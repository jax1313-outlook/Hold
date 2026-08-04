"""Contract conformance: every audit entry written by dispatch.evidence
validates against contracts/audit_entry.schema.json."""
from __future__ import annotations

import jsonschema
import pytest

from dispatch.common import audit
from tests.conftest import load_contract_schema

SCHEMA = load_contract_schema("audit_entry")
FORMAT_CHECKER = jsonschema.FormatChecker()


def assert_conforms(instance: dict) -> None:
    jsonschema.validate(instance=instance, schema=SCHEMA, format_checker=FORMAT_CHECKER)


def test_register_and_retrieve_audit_entries_conform(spine, sample_file, sample_metadata, db_conn):
    registered = spine.register(sample_file, "pump_receipt", sample_metadata)
    spine.retrieve(registered["evidence_record_id"])

    entries = audit.read_audit_entries(db_conn)
    assert len(entries) == 2
    for entry in entries:
        assert_conforms(entry)


def test_link_children_audit_entry_conforms(spine, sample_file, sample_metadata, db_conn):
    registered = spine.register(sample_file, "pump_receipt", sample_metadata)
    spine.link_children(registered["evidence_record_id"], ["fuel_rec_1"])

    entries = audit.read_audit_entries(db_conn)
    link_entries = [e for e in entries if e["action"] == "evidence.link_children"]
    assert len(link_entries) == 1
    assert_conforms(link_entries[0])
    assert link_entries[0]["outcome"] == "completed"


def test_manual_entry_missing_required_field_is_rejected():
    incomplete = {"ts": "2026-08-04T00:00:00Z", "actor": "librarian"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=incomplete, schema=SCHEMA)


def test_write_audit_entry_rejects_malformed_entry(db_conn):
    with pytest.raises(audit.AuditEntryError):
        audit.write_audit_entry(db_conn, {"ts": "2026-08-04T00:00:00Z", "outcome": "completed"})
