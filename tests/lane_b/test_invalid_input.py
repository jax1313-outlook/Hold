"""create() must never invent a triage label or accept a nonsense type;
decisions must never proceed without an explicit decided_by."""
from __future__ import annotations

import pytest


def test_create_rejects_invalid_type(queue_store):
    with pytest.raises(ValueError):
        queue_store.create(
            type="not_a_real_type", source_worker="receipt", priority="today", subject="x"
        )


def test_create_rejects_invalid_priority(queue_store):
    with pytest.raises(ValueError):
        queue_store.create(
            type="review", source_worker="receipt", priority="asap", subject="x"
        )


def test_create_has_no_default_priority(queue_store):
    with pytest.raises(TypeError):
        queue_store.create(type="review", source_worker="receipt", subject="x")  # missing priority


@pytest.mark.parametrize("decided_by", ["", "   ", None])
def test_approve_rejects_missing_decided_by(queue_store, decided_by):
    item = queue_store.create(
        type="approval", source_worker="ifta", priority="urgent", subject="x"
    )
    with pytest.raises((ValueError, TypeError)):
        queue_store.approve(item["queue_item_id"], decided_by=decided_by)

    # And the item must be untouched by the rejected attempt.
    assert queue_store.get(item["queue_item_id"])["status"] == "open"
