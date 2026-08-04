"""Golden regression + boundary refusal: the full queue is always visible.
Filtered/grouped views are read-only projections over the same storage —
they never narrow what's actually in the queue."""
from __future__ import annotations


def _make_mixed_items(queue_store):
    items = []
    items.append(
        queue_store.create(type="review", source_worker="receipt", priority="urgent", subject="A")
    )
    items.append(
        queue_store.create(type="approval", source_worker="ifta", priority="today", subject="B")
    )
    items.append(
        queue_store.create(type="decision", source_worker="manager", priority="whenever", subject="C")
    )
    queue_store.approve(items[1]["queue_item_id"], decided_by="human:mike")
    return items


def test_filtered_call_does_not_shrink_the_unfiltered_queue(queue_store):
    items = _make_mixed_items(queue_store)

    filtered = queue_store.list_all(status="open")
    assert len(filtered) == 2  # A and C are still open; B was approved

    everything = queue_store.list_all()
    assert len(everything) == len(items)
    ids_everything = {item["queue_item_id"] for item in everything}
    for item in items:
        assert item["queue_item_id"] in ids_everything


def test_priority_filter_is_a_view_not_a_deletion(queue_store):
    _make_mixed_items(queue_store)

    urgent_only = queue_store.list_all(priority="urgent")
    assert len(urgent_only) == 1

    everything = queue_store.list_all()
    assert len(everything) == 3


def test_repeated_filtering_never_reduces_total_count(queue_store):
    _make_mixed_items(queue_store)

    for _ in range(5):
        queue_store.list_all(status="approved")
        queue_store.list_all(priority="today")

    assert len(queue_store.list_all()) == 3


def test_decided_items_remain_visible_in_the_full_queue(queue_store):
    items = _make_mixed_items(queue_store)
    approved_id = items[1]["queue_item_id"]

    everything = queue_store.list_all()
    assert any(item["queue_item_id"] == approved_id for item in everything)
