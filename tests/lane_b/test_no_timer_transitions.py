"""Boundary refusal: no transition ever fires on a timer, scheduler, or
default (MANAGER_CONSTITUTION_v1's second closed door). Proven two ways:
a static grep for anything resembling scheduling/auto-approval in the
module surface, and a behavioral check that merely reading an old item
(simulated by backdating it directly in storage) never changes its
status."""
from __future__ import annotations

import re
from pathlib import Path

from dispatch.common import audit

REPO_ROOT = Path(__file__).resolve().parents[2]
QUEUE_SRC_DIR = REPO_ROOT / "src" / "dispatch" / "queue"

_FORBIDDEN_TOKENS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"auto[_ ]?approve",
        r"threading\.timer",
        r"sched(?:uler)?\.",
        r"\bcron\b",
        r"apscheduler",
        r"\bdefault_decision\b",
        r"\btimeout\b.{0,20}approve",
    )
]


def test_no_scheduling_or_auto_approval_tokens_in_source():
    offenders = []
    for path in sorted(QUEUE_SRC_DIR.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for pattern in _FORBIDDEN_TOKENS:
            if pattern.search(text):
                offenders.append((str(path.relative_to(REPO_ROOT)), pattern.pattern))

    assert offenders == [], f"scheduling/auto-approval tokens found: {offenders}"


def test_an_old_untouched_item_never_transitions_on_its_own(queue_store, db_conn):
    item = queue_store.create(
        type="approval", source_worker="ifta", priority="urgent", subject="Ancient item"
    )
    queue_item_id = item["queue_item_id"]

    # Simulate the passage of a long time by backdating created_at directly
    # in storage -- nothing about *reading* this item should ever act on
    # its age.
    db_conn.execute(
        "UPDATE queue_items SET created_at = '2000-01-01T00:00:00Z' WHERE queue_item_id = ?",
        (queue_item_id,),
    )

    for _ in range(10):
        fetched = queue_store.get(queue_item_id)
        assert fetched["status"] == "open"
        assert fetched["decided_by"] is None

    queue_store.list_all()
    queue_store.list_all(status="open")
    queue_store.list_all(priority="urgent")

    final = queue_store.get(queue_item_id)
    assert final["status"] == "open"

    # And no phantom decision audit entry was ever written for it.
    entries = audit.read_audit_entries(db_conn)
    decisions_on_item = [
        e for e in entries if queue_item_id in e["input_refs"] and e["action"] != "queue.create"
    ]
    assert decisions_on_item == []
