"""The archive/evidence interface — contract 1.4.

Three operations, exactly per contracts/evidence_record.schema.json's
interface_note: register / retrieve / link_children. No update, no delete,
permanently. See src/dispatch/evidence/README.md for the full write-up of
how each one behaves and why.

Dependency injection, not hardcoding: EvidenceSpine takes a live DB
connection and the config's `roots` dict at construction time. Nothing in
this module ever writes a literal filesystem root — DISPATCH_BASE_CONSTITUTION_v1
#1 requires every path to come from dispatch.config.json, and a bare
module-level register(file_path, document_type, metadata) function would
have nowhere non-hardcoded to get roots/a connection from.
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dispatch.common import audit
from dispatch.common.hashing import sha256_file
from dispatch.common.ids import new_ulid

VALID_DOCUMENT_TYPES = frozenset(
    {
        "pump_receipt",
        "fuel_card_statement",
        "credit_card_statement",
        "invoice",
        "csv_export",
        "email_attachment",
        # Added in contract v1.1 (2026-08-04, Evidence First Doctrine —
        # see docs/decisions/DECISION_LOG.md): a document's evidence status
        # never depends on whether this system yet knows how to process
        # it. "unclassified" is the honest label for a real dropped file
        # that doesn't match any known type — never a guess at one of the
        # others.
        "rate_confirmation",
        "proof_of_delivery",
        "eld_export",
        "unclassified",
    }
)

DEFAULT_RETENTION_CLASS = "ifta_4yr"
SCHEMA_VERSION = "1.1"

ACTOR_NAME = "librarian"
ACTOR_VERSION = "1.0.0"
CONSTITUTION_VERSION = "LIBRARIAN_CONSTITUTION_v1"


class EvidenceSpineError(Exception):
    """Base class for archive/evidence interface failures."""


class EvidenceNotFoundError(EvidenceSpineError):
    def __init__(self, evidence_record_id: str):
        super().__init__(f"no evidence record with id {evidence_record_id!r}")
        self.evidence_record_id = evidence_record_id


class EvidenceIntegrityError(EvidenceSpineError):
    """Raised by retrieve() when the archived file's hash no longer matches
    the recorded file_hash. The mismatch is also queued as an exception
    queue_item before this is raised — callers see both the exception and
    the queue entry that resulted from it."""


class ArchiveWriteError(EvidenceSpineError):
    """The archive copy or its read-only attribute did not verifiably take
    effect. Raised instead of silently proceeding (LANE_A_LAUNCH_PACKAGE_v1
    risk #2: verify, don't assume)."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_date_component(date_or_datetime: str) -> tuple[str, str]:
    """Return (YYYY, MM) from an ISO date or date-time string."""
    value = date_or_datetime.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(value)
    return f"{parsed.year:04d}", f"{parsed.month:02d}"


class EvidenceSpine:
    """Constructed with a live sqlite3.Connection (from
    dispatch.common.db.bootstrap) and a config's `roots` dict. One instance
    is enough for a whole process; the three interface methods are safe to
    call repeatedly."""

    def __init__(self, conn: sqlite3.Connection, roots: dict[str, str]):
        self._conn = conn
        self._archive_root = Path(roots["archive"])
        self._library_root = Path(roots["library"])

    # -- register --------------------------------------------------------

    def register(
        self,
        file_path: Path | str,
        document_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if document_type not in VALID_DOCUMENT_TYPES:
            raise ValueError(
                f"document_type {document_type!r} not in {sorted(VALID_DOCUMENT_TYPES)}"
            )
        metadata = dict(metadata or {})
        if not metadata.get("document_date"):
            # Rule 11 (No Fabrication): Lane A never invents a document_date.
            raise ValueError("metadata['document_date'] is required and was not provided")

        source_path = Path(file_path)
        if not source_path.is_file():
            raise FileNotFoundError(source_path)

        source_hash = sha256_file(source_path)

        existing = self._find_by_hash(source_hash)
        if existing is not None:
            self._write_audit(
                action="evidence.register",
                outcome="flagged",
                input_refs=[str(source_path)],
                output_refs=[existing["evidence_record_id"]],
                note="duplicate file_hash; returning existing record, no new copy made",
            )
            duplicate_view = dict(existing)
            duplicate_view["extraction_status"] = "duplicate_document"
            return duplicate_view

        evidence_record_id = new_ulid()
        capture_date = metadata.get("capture_date") or _utc_now_iso()
        year, month = _parse_date_component(capture_date)
        suffix = source_path.suffix
        archive_relative = f"Evidence/{year}/{month}/{evidence_record_id}{suffix}"
        archive_absolute = self._archive_root / archive_relative

        archive_absolute.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, archive_absolute)

        # Integrity check on the copy itself, before it's ever trusted as the
        # archived original.
        archived_hash = sha256_file(archive_absolute)
        if archived_hash != source_hash:
            raise ArchiveWriteError(
                f"hash mismatch immediately after archiving {source_path} -> "
                f"{archive_absolute}; refusing to register"
            )

        self._set_read_only(archive_absolute)

        record = {
            "evidence_record_id": evidence_record_id,
            "archive_path": archive_relative,
            "file_hash": source_hash,
            "document_type": document_type,
            "vendor": metadata.get("vendor"),
            "document_date": metadata["document_date"],
            "capture_date": capture_date,
            "statement_period_start": metadata.get("statement_period_start"),
            "statement_period_end": metadata.get("statement_period_end"),
            "page_count": metadata.get("page_count"),
            "extraction_status": "complete",
            "duplicate_of": None,
            "reviewed_by": None,
            "review_date": None,
            "retention_class": metadata.get("retention_class") or DEFAULT_RETENTION_CLASS,
            "schema_version": SCHEMA_VERSION,
        }
        self._insert_record(record)

        full_record = dict(record)
        full_record["derived_record_ids"] = []

        from dispatch.evidence import index as evidence_index

        evidence_index.write_index_entry(self._library_root, full_record)

        self._write_audit(
            action="evidence.register",
            outcome="completed",
            input_refs=[str(source_path)],
            output_refs=[evidence_record_id],
        )
        return full_record

    def _set_read_only(self, path: Path) -> None:
        os.chmod(path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        mode = path.stat().st_mode
        if mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH):
            raise ArchiveWriteError(
                f"read-only attribute did not take effect on {path} (mode {oct(mode)})"
            )

    # -- retrieve ---------------------------------------------------------

    def retrieve(self, evidence_record_id: str) -> tuple[dict[str, Any], Path]:
        record = self._get_record(evidence_record_id)
        if record is None:
            raise EvidenceNotFoundError(evidence_record_id)

        absolute_path = self._archive_root / record["archive_path"]
        actual_hash = sha256_file(absolute_path) if absolute_path.is_file() else None

        if actual_hash != record["file_hash"]:
            self._enqueue_integrity_exception(record, actual_hash)
            self._write_audit(
                action="evidence.retrieve",
                outcome="quarantined",
                input_refs=[evidence_record_id],
                output_refs=[],
                note=(
                    f"hash mismatch or missing file: expected {record['file_hash']}, "
                    f"got {actual_hash!r}"
                ),
            )
            raise EvidenceIntegrityError(
                f"evidence_record_id {evidence_record_id}: expected hash "
                f"{record['file_hash']}, got {actual_hash!r}"
            )

        self._write_audit(
            action="evidence.retrieve",
            outcome="completed",
            input_refs=[evidence_record_id],
            output_refs=[evidence_record_id],
        )
        return record, absolute_path

    def _enqueue_integrity_exception(
        self, record: dict[str, Any], actual_hash: str | None
    ) -> str:
        queue_item_id = new_ulid()
        self._conn.execute(
            """
            INSERT INTO queue_items (
                queue_item_id, type, source_worker, created_at, priority,
                subject, payload_refs, status
            ) VALUES (?, 'exception', ?, ?, 'urgent', ?, ?, 'open')
            """,
            (
                queue_item_id,
                ACTOR_NAME,
                _utc_now_iso(),
                f"Evidence hash mismatch: {record['evidence_record_id']}",
                json.dumps([record["evidence_record_id"]]),
            ),
        )
        return queue_item_id

    # -- link_children -----------------------------------------------------

    def link_children(
        self, evidence_record_id: str, derived_record_ids: list[str]
    ) -> dict[str, Any]:
        record = self._get_record(evidence_record_id)
        if record is None:
            raise EvidenceNotFoundError(evidence_record_id)

        now = _utc_now_iso()
        for child_id in derived_record_ids:
            self._conn.execute(
                """
                INSERT OR IGNORE INTO evidence_children (
                    evidence_record_id, derived_record_id, linked_at
                ) VALUES (?, ?, ?)
                """,
                (evidence_record_id, child_id, now),
            )

        updated = self._get_record(evidence_record_id)
        self._write_audit(
            action="evidence.link_children",
            outcome="completed",
            input_refs=[evidence_record_id, *derived_record_ids],
            output_refs=[evidence_record_id],
        )
        return updated

    # -- shared read helpers ------------------------------------------------

    def _row_to_record(self, row: sqlite3.Row) -> dict[str, Any]:
        record = dict(row)
        record["derived_record_ids"] = self._children_of(record["evidence_record_id"])
        return record

    def _children_of(self, evidence_record_id: str) -> list[str]:
        # ORDER BY rowid (SQLite's implicit insertion-order column), not
        # linked_at: two children linked in the same link_children() call
        # share one timestamp (second resolution), so linked_at alone can't
        # distinguish insertion order between them.
        rows = self._conn.execute(
            """
            SELECT derived_record_id FROM evidence_children
            WHERE evidence_record_id = ?
            ORDER BY rowid
            """,
            (evidence_record_id,),
        ).fetchall()
        return [row["derived_record_id"] for row in rows]

    def _get_record(self, evidence_record_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM evidence_records WHERE evidence_record_id = ?",
            (evidence_record_id,),
        ).fetchone()
        return None if row is None else self._row_to_record(row)

    def _find_by_hash(self, file_hash: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM evidence_records WHERE file_hash = ?",
            (file_hash,),
        ).fetchone()
        return None if row is None else self._row_to_record(row)

    def _insert_record(self, record: dict[str, Any]) -> None:
        self._conn.execute(
            """
            INSERT INTO evidence_records (
                evidence_record_id, archive_path, file_hash, document_type,
                vendor, document_date, capture_date, statement_period_start,
                statement_period_end, page_count, extraction_status,
                duplicate_of, reviewed_by, review_date, retention_class,
                schema_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["evidence_record_id"],
                record["archive_path"],
                record["file_hash"],
                record["document_type"],
                record["vendor"],
                record["document_date"],
                record["capture_date"],
                record["statement_period_start"],
                record["statement_period_end"],
                record["page_count"],
                record["extraction_status"],
                record["duplicate_of"],
                record["reviewed_by"],
                record["review_date"],
                record["retention_class"],
                record["schema_version"],
            ),
        )

    # -- audit ---------------------------------------------------------------

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
