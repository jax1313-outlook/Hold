"""SQLite bootstrap: WAL mode, foreign keys, and concurrent access
(LANE_A_LAUNCH_PACKAGE_v1 risk #3 — test concurrent read/write explicitly,
not just the single-threaded happy path)."""
from __future__ import annotations

import sqlite3
import threading

from dispatch.common.db import bootstrap


def test_wal_mode_enabled(sandbox_config):
    conn = bootstrap(sandbox_config["database"])
    mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
    assert mode.lower() == "wal"


def test_foreign_keys_enabled(sandbox_config):
    conn = bootstrap(sandbox_config["database"])
    enabled = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
    assert enabled == 1


def test_expected_tables_exist(sandbox_config):
    conn = bootstrap(sandbox_config["database"])
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    assert {
        "evidence_records",
        "evidence_children",
        "mileage_records",
        "queue_items",
        "audit_log",
    } <= tables
    # Out of Lane A's scope, deliberately: Lane C's router tables.
    assert "fuel_records" not in tables
    assert "expense_records" not in tables


def test_bootstrap_is_idempotent(sandbox_config):
    first = bootstrap(sandbox_config["database"])
    first.execute(
        "INSERT INTO queue_items (queue_item_id, type, source_worker, created_at, priority, subject, status)"
        " VALUES ('q1', 'exception', 'librarian', '2026-08-04T00:00:00Z', 'urgent', 'test', 'open')"
    )
    first.close()

    second = bootstrap(sandbox_config["database"])
    row = second.execute("SELECT * FROM queue_items WHERE queue_item_id = 'q1'").fetchone()
    assert row is not None


def test_concurrent_reader_and_writer_do_not_deadlock(sandbox_config):
    """Two independent connections against the same file, each opened in the
    thread that uses it (sqlite3 connections are thread-local): one writes
    while the other reads. With WAL + busy_timeout this must complete
    without raising 'database is locked'."""
    errors: list[Exception] = []

    def write_many():
        try:
            writer = bootstrap(sandbox_config["database"])
            for i in range(50):
                writer.execute(
                    "INSERT INTO queue_items (queue_item_id, type, source_worker, created_at, priority, subject, status)"
                    " VALUES (?, 'exception', 'librarian', '2026-08-04T00:00:00Z', 'urgent', 'test', 'open')",
                    (f"writer-{i}",),
                )
            writer.close()
        except sqlite3.OperationalError as exc:
            errors.append(exc)

    def read_many():
        try:
            reader = bootstrap(sandbox_config["database"])
            for _ in range(50):
                reader.execute("SELECT COUNT(*) FROM queue_items").fetchone()
            reader.close()
        except sqlite3.OperationalError as exc:
            errors.append(exc)

    t1 = threading.Thread(target=write_many)
    t2 = threading.Thread(target=read_many)
    t1.start()
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)

    assert not errors, f"concurrent access raised: {errors}"
    verifier = bootstrap(sandbox_config["database"])
    count = verifier.execute("SELECT COUNT(*) FROM queue_items").fetchone()[0]
    assert count == 50
