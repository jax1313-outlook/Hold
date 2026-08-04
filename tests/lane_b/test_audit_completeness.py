"""Audit completeness: every store operation writes exactly one well-formed
audit entry."""
from __future__ import annotations

import jsonschema

from dispatch.common import audit
from tests.conftest import load_contract_schema

SCHEMA = load_contract_schema("audit_entry")
FORMAT_CHECKER = jsonschema.FormatChecker()


def test_every_operation_in_a_mixed_sequence_is_audited(queue_store, db_conn):
    a = queue_store.create(type="review", source_worker="receipt", priority="today", subject="A")
    b = queue_store.create(type="approval", source_worker="ifta", priority="urgent", subject="B")
    queue_store.start_review(a["queue_item_id"])
    queue_store.reject(a["queue_item_id"], decided_by="human:mike", decision_note="no good")
    queue_store.approve(b["queue_item_id"], decided_by="human:mike")

    entries = audit.read_audit_entries(db_conn)
    assert len(entries) == 5  # 2 creates, 1 start_review, 1 reject, 1 approve

    actions = [e["action"] for e in entries]
    assert actions.count("queue.create") == 2
    assert actions.count("queue.start_review") == 1
    assert actions.count("queue.reject") == 1
    assert actions.count("queue.approve") == 1

    for entry in entries:
        jsonschema.validate(instance=entry, schema=SCHEMA, format_checker=FORMAT_CHECKER)
        assert entry["actor"] == "manager"
        assert entry["outcome"] == "completed"


def test_reject_audit_entry_carries_the_decision_note(queue_store, db_conn):
    item = queue_store.create(type="review", source_worker="receipt", priority="today", subject="x")
    queue_store.reject(item["queue_item_id"], decided_by="human:mike", decision_note="bad category")

    entries = audit.read_audit_entries(db_conn)
    reject_entries = [e for e in entries if e["action"] == "queue.reject"]
    assert len(reject_entries) == 1
    assert reject_entries[0]["note"] == "bad category"
