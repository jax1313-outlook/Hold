"""Audit completeness: every action in a test run produces a well-formed
audit entry; sampled and verified here across a mixed sequence of
operations, including failure paths."""
from __future__ import annotations

import jsonschema

from dispatch.common import audit
from dispatch.evidence.interface import EvidenceIntegrityError
from tests.conftest import load_contract_schema

SCHEMA = load_contract_schema("audit_entry")
FORMAT_CHECKER = jsonschema.FormatChecker()


def test_every_operation_in_a_mixed_sequence_is_audited(spine, sample_file, sample_metadata, db_conn):
    registered = spine.register(sample_file, "pump_receipt", sample_metadata)  # completed
    spine.register(sample_file, "pump_receipt", sample_metadata)  # flagged (duplicate)
    spine.retrieve(registered["evidence_record_id"])  # completed
    spine.link_children(registered["evidence_record_id"], ["fuel_rec_1"])  # completed

    absolute_path = spine._archive_root / registered["archive_path"]
    absolute_path.chmod(0o600)
    absolute_path.write_bytes(b"tampered")
    try:
        spine.retrieve(registered["evidence_record_id"])  # quarantined
    except EvidenceIntegrityError:
        pass

    entries = audit.read_audit_entries(db_conn)
    assert len(entries) == 5

    outcomes = [e["outcome"] for e in entries]
    assert outcomes.count("completed") == 3
    assert outcomes.count("flagged") == 1
    assert outcomes.count("quarantined") == 1

    for entry in entries:
        jsonschema.validate(instance=entry, schema=SCHEMA, format_checker=FORMAT_CHECKER)
        assert entry["actor"] == "librarian"
        assert entry["action"].startswith("evidence.")
