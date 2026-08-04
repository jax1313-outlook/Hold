"""Boundary refusal: no delete of a queue item, ever — proven by a direct
SQL attempt (the trigger QueueStore installs) AND by a static grep of the
module surface (the code never issues DELETE against queue_items either)."""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
QUEUE_SRC_DIR = REPO_ROOT / "src" / "dispatch" / "queue"

_FORBIDDEN_DELETE = re.compile(r"\bDELETE\s+FROM\s+queue_items\b", re.IGNORECASE)


def test_direct_delete_on_queue_items_is_rejected(queue_store, db_conn):
    item = queue_store.create(
        type="review", source_worker="receipt", priority="today", subject="x"
    )
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            "DELETE FROM queue_items WHERE queue_item_id = ?", (item["queue_item_id"],)
        )


def test_delete_on_a_decided_item_is_also_rejected(queue_store, db_conn):
    item = queue_store.create(
        type="approval", source_worker="ifta", priority="urgent", subject="x"
    )
    queue_store.reject(item["queue_item_id"], decided_by="human:mike")

    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            "DELETE FROM queue_items WHERE queue_item_id = ?", (item["queue_item_id"],)
        )


def test_trigger_definition_sanity_check(queue_store, db_conn):
    # The forbidden-pattern search below must not vacuously pass because it
    # also matches the trigger's own definition ("BEFORE DELETE ON
    # queue_items", not "DELETE FROM queue_items").
    trigger_sql = "\n".join(
        row[0]
        for row in db_conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'trigger' AND name = 'trg_queue_items_no_delete'"
        ).fetchall()
    )
    assert "BEFORE DELETE ON queue_items" in trigger_sql
    assert not _FORBIDDEN_DELETE.search(trigger_sql)


def test_no_delete_statement_against_queue_items_in_source():
    offenders = []
    for path in sorted(QUEUE_SRC_DIR.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if _FORBIDDEN_DELETE.search(text):
            offenders.append(str(path.relative_to(REPO_ROOT)))

    assert offenders == [], f"forbidden DELETE statements found: {offenders}"
