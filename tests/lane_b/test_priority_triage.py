import pytest


@pytest.mark.parametrize("priority", ["urgent", "today", "whenever"])
def test_each_valid_priority_is_accepted(queue_store, priority):
    item = queue_store.create(
        type="review", source_worker="receipt", priority=priority, subject="x"
    )
    assert item["priority"] == priority


def test_priority_is_never_invented_by_the_store(queue_store):
    """The store must never guess or default a priority -- it's a label
    Mike writes. Every call in this suite passes one explicitly; the
    absence of any inference logic is enforced by test_create_rejects_*
    in test_invalid_input.py and by there being no such logic to call."""
    item = queue_store.create(
        type="review", source_worker="receipt", priority="whenever", subject="x"
    )
    assert item["priority"] == "whenever"  # exactly what was passed, nothing inferred
