"""Audit writer — INSERT-only, per contracts/audit_entry.schema.json.

There is no update or delete function in this module, and none will ever be
added: audit_log's immutability triggers (installed by db.bootstrap) make one
unenforceable at the database layer even if a caller tried to write it.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any

_REQUIRED_FIELDS = (
    "ts",
    "actor",
    "actor_version",
    "constitution_version",
    "action",
    "outcome",
)
_VALID_OUTCOMES = {"completed", "flagged", "quarantined"}


class AuditEntryError(ValueError):
    """The entry doesn't conform to contracts/audit_entry.schema.json."""


def write_audit_entry(conn: sqlite3.Connection, entry: dict[str, Any]) -> None:
    """INSERT one row into audit_log. Raises AuditEntryError instead of
    writing anything if the entry is missing a required field or has an
    invalid outcome — a malformed audit entry must never silently land."""
    missing = [f for f in _REQUIRED_FIELDS if entry.get(f) is None]
    if missing:
        raise AuditEntryError(f"audit entry missing required field(s): {missing}")
    if entry["outcome"] not in _VALID_OUTCOMES:
        raise AuditEntryError(
            f"invalid outcome {entry['outcome']!r}; must be one of {sorted(_VALID_OUTCOMES)}"
        )

    conn.execute(
        """
        INSERT INTO audit_log (
            ts, actor, actor_version, constitution_version, action,
            input_refs, output_refs, gate_ref, trade_memory_refs, outcome, note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entry["ts"],
            entry["actor"],
            entry["actor_version"],
            entry["constitution_version"],
            entry["action"],
            json.dumps(entry.get("input_refs", [])),
            json.dumps(entry.get("output_refs", [])),
            json.dumps(entry["gate_ref"]) if entry.get("gate_ref") is not None else None,
            json.dumps(entry.get("trade_memory_refs", [])),
            entry["outcome"],
            entry.get("note"),
        ),
    )


def read_audit_entries(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Read back audit_log rows as contract-shaped dicts (JSON fields
    decoded). Used by tools/export_audit_rolls.py and by tests verifying
    audit completeness."""
    rows = conn.execute(
        """
        SELECT ts, actor, actor_version, constitution_version, action,
               input_refs, output_refs, gate_ref, trade_memory_refs, outcome, note
        FROM audit_log
        ORDER BY audit_id
        """
    ).fetchall()
    entries = []
    for row in rows:
        entry = dict(row)
        entry["input_refs"] = json.loads(entry["input_refs"]) if entry["input_refs"] else []
        entry["output_refs"] = json.loads(entry["output_refs"]) if entry["output_refs"] else []
        entry["gate_ref"] = json.loads(entry["gate_ref"]) if entry["gate_ref"] else None
        entry["trade_memory_refs"] = (
            json.loads(entry["trade_memory_refs"]) if entry["trade_memory_refs"] else []
        )
        entries.append(entry)
    return entries
