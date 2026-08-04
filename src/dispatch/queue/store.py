"""The queue store — contract 1.3 (contracts/queue_item.schema.json).

Builds on the `queue_items` table dispatch.common.db.bootstrap() already
creates. That bootstrap deliberately does not install a delete-revoking
trigger on this table (Lane A's allowed files covered
evidence_records/evidence_children/audit_log only) — "no delete of a
queue item, ever" is Manager's own constitutional requirement
(MANAGER_CONSTITUTION_v1), not Lane A's, so this module installs that
trigger itself, idempotently, whenever a QueueStore is constructed.
UPDATE is not similarly forbidden: transitions are legitimate updates to
status/decided_by/decided_at/decision_note, required by the lifecycle
itself.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from dispatch.common import audit
from dispatch.common.ids import new_ulid

VALID_TYPES = frozenset({"approval", "review", "exception", "decision"})
VALID_PRIORITIES = frozenset({"urgent", "today", "whenever"})

OPEN = "open"
IN_REVIEW = "in_review"
APPROVED = "approved"
REJECTED = "rejected"
RESOLVED = "resolved"
_DECISION_STATUSES = frozenset({APPROVED, REJECTED, RESOLVED})

ACTOR_NAME = "manager"
ACTOR_VERSION = "1.0.0"
CONSTITUTION_VERSION = "MANAGER_CONSTITUTION_v1"


class QueueError(Exception):
    """Base class for queue store failures."""


class QueueItemNotFoundError(QueueError):
    def __init__(self, queue_item_id: str):
        super().__init__(f"no queue item with id {queue_item_id!r}")
        self.queue_item_id = queue_item_id


class InvalidTransitionError(QueueError):
    """Raised when a transition is attempted from a status that doesn't
    allow it. There is no path from a decided status back to open/in_review
    — decisions are final, per "rejected/resolved items are retained,
    permanently"."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def install_immutability(conn: sqlite3.Connection) -> None:
    """No delete of a queue item, ever. Safe to call repeatedly."""
    conn.execute(
        """
        CREATE TRIGGER IF NOT EXISTS trg_queue_items_no_delete
        BEFORE DELETE ON queue_items
        BEGIN
            SELECT RAISE(ABORT, 'queue_items is immutable: DELETE is not permitted');
        END;
        """
    )


class QueueStore:
    """Constructed with a live sqlite3.Connection (from
    dispatch.common.db.bootstrap()). One instance is enough for a whole
    process."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        install_immutability(conn)

    # -- creation -----------------------------------------------------------

    def create(
        self,
        *,
        type: str,
        source_worker: str,
        priority: str,
        subject: str,
        payload_refs: list[str] | None = None,
    ) -> dict[str, Any]:
        """priority is required, with no default: it is a triage label Mike
        writes, never one the Manager invents (MANAGER_CONSTITUTION_v1, "the
        three doors")."""
        if type not in VALID_TYPES:
            raise ValueError(f"type {type!r} not in {sorted(VALID_TYPES)}")
        if priority not in VALID_PRIORITIES:
            raise ValueError(f"priority {priority!r} not in {sorted(VALID_PRIORITIES)}")

        queue_item_id = new_ulid()
        created_at = _utc_now_iso()
        self._conn.execute(
            """
            INSERT INTO queue_items (
                queue_item_id, type, source_worker, created_at, priority,
                subject, payload_refs, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                queue_item_id,
                type,
                source_worker,
                created_at,
                priority,
                subject,
                json.dumps(payload_refs or []),
                OPEN,
            ),
        )
        self._write_audit(
            action="queue.create",
            outcome="completed",
            input_refs=[source_worker],
            output_refs=[queue_item_id],
        )
        return self.get(queue_item_id)

    # -- reads ---------------------------------------------------------------

    def get(self, queue_item_id: str) -> dict[str, Any]:
        row = self._conn.execute(
            "SELECT * FROM queue_items WHERE queue_item_id = ?", (queue_item_id,)
        ).fetchone()
        if row is None:
            raise QueueItemNotFoundError(queue_item_id)
        return self._row_to_item(row)

    def list_all(
        self, *, status: str | None = None, priority: str | None = None
    ) -> list[dict[str, Any]]:
        """The full queue, always available with no filter. status/priority
        are read-only projections over this same storage — never a second,
        smaller source of truth, and never a way to make an item
        disappear (MANAGER_CONSTITUTION_v1: "the full queue is always
        visible; filtered items are deferred and logged, never discarded")."""
        query = "SELECT * FROM queue_items"
        conditions = []
        params: list[str] = []
        if status is not None:
            conditions.append("status = ?")
            params.append(status)
        if priority is not None:
            conditions.append("priority = ?")
            params.append(priority)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_at, queue_item_id"
        rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_item(row) for row in rows]

    def _row_to_item(self, row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        item["payload_refs"] = json.loads(item["payload_refs"]) if item["payload_refs"] else []
        return item

    # -- transitions ----------------------------------------------------------

    def start_review(self, queue_item_id: str) -> dict[str, Any]:
        return self._transition(
            queue_item_id,
            from_statuses={OPEN},
            to_status=IN_REVIEW,
            action="queue.start_review",
        )

    def approve(
        self, queue_item_id: str, *, decided_by: str, decision_note: str | None = None
    ) -> dict[str, Any]:
        return self._decide(
            queue_item_id,
            to_status=APPROVED,
            decided_by=decided_by,
            decision_note=decision_note,
            action="queue.approve",
        )

    def reject(
        self, queue_item_id: str, *, decided_by: str, decision_note: str | None = None
    ) -> dict[str, Any]:
        return self._decide(
            queue_item_id,
            to_status=REJECTED,
            decided_by=decided_by,
            decision_note=decision_note,
            action="queue.reject",
        )

    def resolve(
        self, queue_item_id: str, *, decided_by: str, decision_note: str | None = None
    ) -> dict[str, Any]:
        return self._decide(
            queue_item_id,
            to_status=RESOLVED,
            decided_by=decided_by,
            decision_note=decision_note,
            action="queue.resolve",
        )

    def _decide(
        self,
        queue_item_id: str,
        *,
        to_status: str,
        decided_by: str,
        decision_note: str | None,
        action: str,
    ) -> dict[str, Any]:
        # Silence is never consent: every decision requires an explicit
        # human identifier. There is no default and no way to omit this --
        # whitespace-only input counts as omitted, not as a name.
        if not decided_by or not decided_by.strip():
            raise ValueError("decided_by is required for a decision")
        return self._transition(
            queue_item_id,
            from_statuses={OPEN, IN_REVIEW},
            to_status=to_status,
            action=action,
            decided_by=decided_by.strip(),
            decision_note=decision_note,
        )

    def _transition(
        self,
        queue_item_id: str,
        *,
        from_statuses: frozenset[str],
        to_status: str,
        action: str,
        decided_by: str | None = None,
        decision_note: str | None = None,
    ) -> dict[str, Any]:
        current = self.get(queue_item_id)
        if current["status"] not in from_statuses:
            raise InvalidTransitionError(
                f"cannot move {queue_item_id} from {current['status']!r} to "
                f"{to_status!r} (allowed from: {sorted(from_statuses)})"
            )

        decided_at = _utc_now_iso() if to_status in _DECISION_STATUSES else None
        self._conn.execute(
            """
            UPDATE queue_items
            SET status = ?,
                decided_by = COALESCE(?, decided_by),
                decided_at = COALESCE(?, decided_at),
                decision_note = COALESCE(?, decision_note)
            WHERE queue_item_id = ?
            """,
            (to_status, decided_by, decided_at, decision_note, queue_item_id),
        )
        self._write_audit(
            action=action,
            outcome="completed",
            input_refs=[queue_item_id],
            output_refs=[queue_item_id],
            note=decision_note,
        )
        return self.get(queue_item_id)

    # -- audit -----------------------------------------------------------------

    def _write_audit(
        self,
        *,
        action: str,
        outcome: str,
        input_refs: list[str] | None = None,
        output_refs: list[str] | None = None,
        note: str | None = None,
    ) -> None:
        audit.write_audit_entry(
            self._conn,
            {
                "ts": _utc_now_iso(),
                "actor": ACTOR_NAME,
                "actor_version": ACTOR_VERSION,
                "constitution_version": CONSTITUTION_VERSION,
                "action": action,
                "input_refs": input_refs or [],
                "output_refs": output_refs or [],
                "gate_ref": None,
                "trade_memory_refs": [],
                "outcome": outcome,
                "note": note,
            },
        )
