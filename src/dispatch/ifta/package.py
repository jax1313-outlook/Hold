"""Quarterly IFTA package builder — DRAFT status, seal-on-approval via
the queue interface.

Computation spec 3.5: "Worksheet is DRAFT until a human approves it
through the queue; approval seals the bundle (worksheet + records +
evidence refs) to ARCHIVE\\IFTA\\<quarter>\\." No persistent watcher polls
for approval, consistent with the rest of this codebase's "no background
process" pattern — `attempt_seal()` is a callable a human or a scheduled
task invokes explicitly, after the worksheet's approval queue item has
actually been approved. There is no other way for a worksheet to reach
`sealed`.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dispatch.queue.store import QueueStore


class PackageError(Exception):
    """Base class for package-builder failures."""


class WorksheetNotFoundError(PackageError):
    pass


class WorksheetNotDraftError(PackageError):
    pass


class ApprovalNotYetGrantedError(PackageError):
    pass


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def submit_for_approval(
    conn: sqlite3.Connection, queue: QueueStore, worksheet: dict[str, Any]
) -> dict[str, Any]:
    """Creates the approval queue item and links it to the worksheet. Call
    once per worksheet, while it's still draft."""
    if worksheet["status"] != "draft":
        raise WorksheetNotDraftError(
            f"worksheet {worksheet['ifta_worksheet_id']} is {worksheet['status']!r}, not draft"
        )

    queue_item = queue.create(
        type="approval",
        source_worker="ifta",
        priority="today",
        subject=(
            f"Approve IFTA worksheet {worksheet['quarter']} ({worksheet['fuel_type']}): "
            f"net tax {worksheet['total_net_tax']:.2f}"
        ),
        payload_refs=[worksheet["ifta_worksheet_id"]],
    )
    conn.execute(
        "UPDATE ifta_worksheets SET queue_item_id = ? WHERE ifta_worksheet_id = ?",
        (queue_item["queue_item_id"], worksheet["ifta_worksheet_id"]),
    )
    return queue_item


def attempt_seal(
    conn: sqlite3.Connection, queue: QueueStore, roots: dict[str, str], ifta_worksheet_id: str
) -> dict[str, Any]:
    """If the worksheet's linked queue item has been approved, seals it:
    writes the bundle (worksheet + lines + evidence refs) to
    ARCHIVE\\IFTA\\<quarter>\\ and flips status to sealed. Raises
    ApprovalNotYetGrantedError otherwise. Idempotent if already sealed."""
    row = conn.execute(
        "SELECT * FROM ifta_worksheets WHERE ifta_worksheet_id = ?", (ifta_worksheet_id,)
    ).fetchone()
    if row is None:
        raise WorksheetNotFoundError(f"no worksheet {ifta_worksheet_id!r}")
    worksheet = dict(row)

    if worksheet["status"] == "sealed":
        return worksheet
    if worksheet["status"] != "draft":
        raise WorksheetNotDraftError(f"worksheet is {worksheet['status']!r}")
    if not worksheet["queue_item_id"]:
        raise ApprovalNotYetGrantedError("worksheet was never submitted for approval")

    queue_item = queue.get(worksheet["queue_item_id"])
    if queue_item["status"] != "approved":
        raise ApprovalNotYetGrantedError(
            f"queue item {queue_item['queue_item_id']} is {queue_item['status']!r}, not approved"
        )

    lines = conn.execute(
        "SELECT * FROM ifta_worksheet_lines WHERE ifta_worksheet_id = ? ORDER BY jurisdiction",
        (ifta_worksheet_id,),
    ).fetchall()
    sealed_at = _utc_now_iso()

    conn.execute(
        "UPDATE ifta_worksheets SET status = 'sealed', sealed_at = ? WHERE ifta_worksheet_id = ?",
        (sealed_at, ifta_worksheet_id),
    )
    sealed_row = conn.execute(
        "SELECT * FROM ifta_worksheets WHERE ifta_worksheet_id = ?", (ifta_worksheet_id,)
    ).fetchone()
    sealed_worksheet = dict(sealed_row)

    bundle = {
        "worksheet": sealed_worksheet,
        "lines": [dict(line) for line in lines],
        "sealed_at": sealed_at,
        "approved_by": queue_item["decided_by"],
        "approval_note": queue_item["decision_note"],
    }
    bundle_dir = Path(roots["archive"]) / "IFTA" / sealed_worksheet["quarter"]
    bundle_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = bundle_dir / f"{ifta_worksheet_id}.json"
    bundle_path.write_text(json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8")

    return sealed_worksheet
