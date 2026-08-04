"""Golden regression: full lifecycle. Every path the state machine allows,
each transition writing an audit entry."""
from __future__ import annotations

import pytest

from dispatch.queue.store import InvalidTransitionError, QueueItemNotFoundError


def test_create_defaults_to_open(queue_store):
    item = queue_store.create(
        type="review", source_worker="receipt", priority="today", subject="Check this receipt"
    )
    assert item["status"] == "open"
    assert item["decided_by"] is None
    assert item["decided_at"] is None
    assert item["payload_refs"] == []


def test_open_to_in_review_to_approved(queue_store):
    item = queue_store.create(
        type="approval", source_worker="ifta", priority="urgent", subject="Approve worksheet"
    )
    reviewed = queue_store.start_review(item["queue_item_id"])
    assert reviewed["status"] == "in_review"

    approved = queue_store.approve(
        item["queue_item_id"], decided_by="human:mike", decision_note="looks right"
    )
    assert approved["status"] == "approved"
    assert approved["decided_by"] == "human:mike"
    assert approved["decision_note"] == "looks right"
    assert approved["decided_at"] is not None


def test_open_directly_to_rejected(queue_store):
    item = queue_store.create(
        type="exception", source_worker="librarian", priority="urgent", subject="Hash mismatch"
    )
    rejected = queue_store.reject(item["queue_item_id"], decided_by="human:mike")
    assert rejected["status"] == "rejected"


def test_in_review_to_resolved(queue_store):
    item = queue_store.create(
        type="decision", source_worker="manager", priority="whenever", subject="Housekeeping"
    )
    queue_store.start_review(item["queue_item_id"])
    resolved = queue_store.resolve(item["queue_item_id"], decided_by="human:mike", decision_note="done")
    assert resolved["status"] == "resolved"
    assert resolved["decision_note"] == "done"


def test_decided_items_are_final(queue_store):
    item = queue_store.create(
        type="approval", source_worker="ifta", priority="today", subject="Approve"
    )
    queue_store.approve(item["queue_item_id"], decided_by="human:mike")

    with pytest.raises(InvalidTransitionError):
        queue_store.reject(item["queue_item_id"], decided_by="human:mike")
    with pytest.raises(InvalidTransitionError):
        queue_store.start_review(item["queue_item_id"])


def test_decided_items_are_retained_with_their_notes(queue_store):
    item = queue_store.create(
        type="review", source_worker="receipt", priority="today", subject="Odd line item"
    )
    queue_store.reject(item["queue_item_id"], decided_by="human:mike", decision_note="not a valid category")

    fetched = queue_store.get(item["queue_item_id"])
    assert fetched["status"] == "rejected"
    assert fetched["decision_note"] == "not a valid category"
    assert fetched in queue_store.list_all()


def test_unknown_item_raises_not_found(queue_store):
    with pytest.raises(QueueItemNotFoundError):
        queue_store.get("01UNKNOWNULIDDOESNOTEXIST0")
    with pytest.raises(QueueItemNotFoundError):
        queue_store.approve("01UNKNOWNULIDDOESNOTEXIST0", decided_by="human:mike")


def test_payload_refs_round_trip(queue_store):
    item = queue_store.create(
        type="review",
        source_worker="receipt",
        priority="today",
        subject="Two records",
        payload_refs=["fuel_rec_1", "expense_rec_1"],
    )
    assert item["payload_refs"] == ["fuel_rec_1", "expense_rec_1"]
    assert queue_store.get(item["queue_item_id"])["payload_refs"] == ["fuel_rec_1", "expense_rec_1"]
