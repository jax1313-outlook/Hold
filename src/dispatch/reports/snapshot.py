"""The single writer this lane is permitted.

REPORTS_CHARTER_v1.md's first bright line, exactly bounded: Save For
Printing writes an immutable HTML snapshot to
`ARCHIVE\\ReportSnapshots\\YYYY\\` and a `print_queue` row referencing it.
Nothing else in this package ever opens a writable connection — every
query in `queries.py` runs against `dispatch.reports.readonly`'s
`mode=ro` connection instead.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dispatch.common import audit
from dispatch.common.ids import new_ulid
from dispatch.reports.db import install_schema
from dispatch.reports.rendering import render_answer_html

ACTOR_NAME = "reports"
ACTOR_VERSION = "1.0.0"
CONSTITUTION_VERSION = "REPORTS_CHARTER_v1"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class PrintQueueItemNotFoundError(LookupError):
    pass


class ReportSnapshotWriter:
    """Constructed with a normal read-write connection (via
    dispatch.common.db.bootstrap) and the config's archive root. This is
    the one place in the whole lane that writes anything."""

    def __init__(self, conn: sqlite3.Connection, archive_root: Path | str):
        self._conn = conn
        self._archive_root = Path(archive_root)
        install_schema(conn)

    def save_snapshot(
        self,
        *,
        report_type: str,
        template: dict[str, Any],
        template_version: str,
        data: dict[str, Any],
        period_label: str,
        filters_desc: dict[str, str] | None = None,
        pending_review_count: int = 0,
        as_of: str | None = None,
    ) -> dict[str, Any]:
        as_of = as_of or _utc_now_iso()
        html = render_answer_html(
            template,
            data,
            as_of=as_of,
            period_label=period_label,
            template_version=template_version,
            filters_desc=filters_desc,
            pending_review_count=pending_review_count,
            standalone=True,
        )

        print_queue_id = new_ulid()
        year = as_of[:4]
        snapshot_dir = self._archive_root / "ReportSnapshots" / year
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = snapshot_dir / f"{print_queue_id}.html"
        snapshot_path.write_text(html, encoding="utf-8")

        relative_path = str(snapshot_path.relative_to(self._archive_root))
        saved_at = _utc_now_iso()
        self._conn.execute(
            """
            INSERT INTO print_queue (
                print_queue_id, report_type, template_version, as_of,
                period_label, filters, snapshot_path, status, saved_at, schema_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', ?, '1.0')
            """,
            (
                print_queue_id, report_type, template_version, as_of, period_label,
                json.dumps(filters_desc or {}), relative_path, saved_at,
            ),
        )

        self._write_audit(
            action="reports.save_snapshot",
            outcome="completed",
            input_refs=[report_type],
            output_refs=[print_queue_id],
        )

        return self.get(print_queue_id)

    def get(self, print_queue_id: str) -> dict[str, Any]:
        row = self._conn.execute(
            "SELECT * FROM print_queue WHERE print_queue_id = ?", (print_queue_id,)
        ).fetchone()
        if row is None:
            raise PrintQueueItemNotFoundError(print_queue_id)
        item = dict(row)
        item["filters"] = json.loads(item["filters"]) if item["filters"] else {}
        return item

    def mark_printed(self, print_queue_id: str) -> dict[str, Any]:
        self.get(print_queue_id)  # raises PrintQueueItemNotFoundError if missing
        self._conn.execute(
            "UPDATE print_queue SET status = 'printed' WHERE print_queue_id = ?", (print_queue_id,)
        )
        self._write_audit(action="reports.mark_printed", outcome="completed", output_refs=[print_queue_id])
        return self.get(print_queue_id)

    def clear(self, print_queue_id: str) -> dict[str, Any]:
        """A status transition, not a DELETE — see db.py's docstring and
        LANE_D_LAUNCH_PACKAGE_v1.md risk #1. The Archive snapshot file is
        never touched either way."""
        self.get(print_queue_id)
        self._conn.execute(
            "UPDATE print_queue SET status = 'cleared' WHERE print_queue_id = ?", (print_queue_id,)
        )
        self._write_audit(
            action="reports.clear_print_queue_item", outcome="completed", output_refs=[print_queue_id]
        )
        return self.get(print_queue_id)

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


def list_queue(conn: sqlite3.Connection, *, status: str | None = None) -> list[dict[str, Any]]:
    """Read the queue — safe on either the writer's connection or a
    read-only one, since it's just a SELECT."""
    query = "SELECT * FROM print_queue"
    params: list[Any] = []
    if status:
        query += " WHERE status = ?"
        params.append(status)
    query += " ORDER BY saved_at DESC"

    items = []
    for row in conn.execute(query, params).fetchall():
        item = dict(row)
        item["filters"] = json.loads(item["filters"]) if item["filters"] else {}
        items.append(item)
    return items


def recent_reports(conn: sqlite3.Connection, *, limit: int = 3) -> list[dict[str, Any]]:
    """Recents chips: the last N distinct (report_type, period_label,
    filters) combinations among *saved* reports. Deliberately not
    tracking every live/ephemeral view — the charter's bright line is
    "writes nothing except the print queue," so recents is derived from
    what's already written there, not a second write path invented for
    convenience."""
    rows = conn.execute(
        """
        SELECT report_type, period_label, filters, MAX(saved_at) AS last_saved_at
        FROM print_queue
        GROUP BY report_type, period_label, filters
        ORDER BY last_saved_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]
