"""Contract conformance, extended by Lane B: every status the queue's
state machine can reach validates against contracts/queue_item.schema.json,
byte-for-byte. (Lane A's test_queue_item_conformance.py already covers the
shape of the one queue_item Lane A itself produces -- an `exception` item
from a hash mismatch. This file covers the rest of the lifecycle, which
only exists once Lane B's store does.)
"""
from __future__ import annotations

import jsonschema
import pytest

from dispatch.queue.store import QueueStore
from tests.conftest import load_contract_schema

SCHEMA = load_contract_schema("queue_item")
FORMAT_CHECKER = jsonschema.FormatChecker()


def assert_conforms(instance: dict) -> None:
    jsonschema.validate(instance=instance, schema=SCHEMA, format_checker=FORMAT_CHECKER)


@pytest.fixture
def store(db_conn) -> QueueStore:
    return QueueStore(db_conn)


def test_freshly_created_item_conforms(store):
    item = store.create(type="review", source_worker="receipt", priority="today", subject="x")
    assert_conforms(item)


def test_approved_item_conforms(store):
    item = store.create(type="approval", source_worker="ifta", priority="urgent", subject="x")
    approved = store.approve(item["queue_item_id"], decided_by="human:mike", decision_note="ok")
    assert_conforms(approved)


def test_rejected_item_conforms(store):
    item = store.create(type="review", source_worker="receipt", priority="today", subject="x")
    rejected = store.reject(item["queue_item_id"], decided_by="human:mike")
    assert_conforms(rejected)


def test_resolved_item_conforms(store):
    item = store.create(type="decision", source_worker="manager", priority="whenever", subject="x")
    store.start_review(item["queue_item_id"])
    resolved = store.resolve(item["queue_item_id"], decided_by="human:mike", decision_note="handled")
    assert_conforms(resolved)


def test_item_with_payload_refs_conforms(store):
    item = store.create(
        type="review",
        source_worker="receipt",
        priority="today",
        subject="x",
        payload_refs=["fuel_rec_1", "expense_rec_1"],
    )
    assert_conforms(item)
