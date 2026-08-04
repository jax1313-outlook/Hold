"""Contract conformance for queue_items.

Lane A doesn't own the queue (Lane B does), but retrieve()'s hash-mismatch
path must enqueue a contract-shaped exception item — this proves it does.
"""
from __future__ import annotations

import json

import jsonschema

from dispatch.evidence.interface import EvidenceIntegrityError
from tests.conftest import load_contract_schema

SCHEMA = load_contract_schema("queue_item")
FORMAT_CHECKER = jsonschema.FormatChecker()


def _row_to_queue_item(row) -> dict:
    item = dict(row)
    item["payload_refs"] = json.loads(item["payload_refs"]) if item["payload_refs"] else []
    return item


def test_integrity_exception_queue_item_conforms(spine, sample_file, sample_metadata, db_conn):
    registered = spine.register(sample_file, "pump_receipt", sample_metadata)

    absolute_path = spine._archive_root / registered["archive_path"]
    absolute_path.chmod(0o600)
    absolute_path.write_bytes(b"tampered contents")

    try:
        spine.retrieve(registered["evidence_record_id"])
    except EvidenceIntegrityError:
        pass

    rows = db_conn.execute("SELECT * FROM queue_items").fetchall()
    assert len(rows) == 1
    item = _row_to_queue_item(rows[0])
    jsonschema.validate(instance=item, schema=SCHEMA, format_checker=FORMAT_CHECKER)
    assert item["type"] == "exception"
    assert item["status"] == "open"
    assert registered["evidence_record_id"] in item["payload_refs"]
