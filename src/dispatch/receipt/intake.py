"""Intake pipeline: process_drop(config) scans OPERATIONS\\Intake\\Drop
once per call and drives every file it finds through
register -> extract -> validate -> route.

No persistent watcher/daemon lives in this module — see
docs/lanes/C/LANE_C_LAUNCH_PACKAGE_v1.md risk #1. `process_drop` is
idempotent to call repeatedly (each file is moved out of Drop once
handled), so a cron job, a manual trigger, or a scheduled task outside
this codebase is what turns this into a "watcher" operationally.

Registration-vs-extraction ordering note: contract 1.4 requires archiving
to happen BEFORE any extraction, and requires a real, non-fabricated
document_date at registration time. For a freshly dropped file, the real
document date (what's printed on it) is only known *after* extraction —
which can't run yet. This module resolves that by registering with the
file's own filesystem mtime as document_date (a true, non-fabricated fact
about the file, just not necessarily the same date as what's printed on
it) and treating the *extracted* per-transaction purchase_date on the
resulting FuelRecord/ExpenseRecord as the actually-trustworthy business
date. Flagged in docs/lanes/C/NOTES.md, not hidden.
"""
from __future__ import annotations

import shutil
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from dispatch.common import audit
from dispatch.common.db import bootstrap
from dispatch.evidence.interface import EvidenceSpine
from dispatch.queue.store import QueueStore
from dispatch.receipt import validators
from dispatch.receipt.extraction.vision import VisionExtractionUnavailable, build_extractor
from dispatch.receipt.parsers import csv_parser, statement_parser
from dispatch.receipt.router import Router, RoutingError

ACTOR_NAME = "receipt"
ACTOR_VERSION = "1.0.0"
CONSTITUTION_VERSION = "RECEIPT_CONSTITUTION_v1"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _fallback_document_date(path: Path) -> str:
    import os

    return date.fromtimestamp(os.path.getmtime(path)).isoformat()


def _classify(path: Path, vendor_profiles: list[dict[str, Any]]) -> tuple[str, str, dict | None]:
    """Returns (document_type, parse_kind, vendor_profile). Matching a
    vendor profile is an exact filename-prefix match — data, not
    inference; RECEIPT_CONSTITUTION_v1 lists "unknown vendor format" as
    something to detect, never guess past."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        for profile in vendor_profiles:
            prefix = profile.get("filename_prefix")
            if prefix and path.name.startswith(prefix):
                return "fuel_card_statement", "statement", profile
        return "csv_export", "csv", None
    return "pump_receipt", "vision", None


def _extract(
    path: Path, parse_kind: str, profile: dict | None, extractor
) -> tuple[list[dict[str, Any]], float | None]:
    if parse_kind == "csv":
        return csv_parser.parse(path)
    if parse_kind == "statement":
        return statement_parser.parse(path, profile)
    return extractor.extract(path)


class IntakePipeline:
    def __init__(self, config: dict[str, Any], *, vendor_profiles: list[dict] | None = None):
        self._config = config
        self._vendor_profiles = vendor_profiles or []
        self._conn = bootstrap(config["database"])
        self._spine = EvidenceSpine(self._conn, config["roots"])
        self._queue = QueueStore(self._conn)
        self._router = Router(self._conn)
        self._extractor = build_extractor(config)

        operations_root = Path(config["roots"]["operations"])
        self._drop_dir = operations_root / "Intake" / "Drop"
        self._processing_dir = operations_root / "Intake" / "Processing"
        self._quarantine_dir = operations_root / "Intake" / "Quarantine"
        self._processing_dir.mkdir(parents=True, exist_ok=True)
        self._quarantine_dir.mkdir(parents=True, exist_ok=True)

    def process_drop(self, *, confidence_threshold: float | None = None) -> dict[str, Any]:
        summary: dict[str, list] = {
            "processed": [],
            "quarantined_files": [],
            "quarantined_lines": [],
            "routed": [],
        }
        if not self._drop_dir.is_dir():
            return summary

        for path in sorted(self._drop_dir.iterdir()):
            if path.is_file():
                self._process_one_file(path, confidence_threshold, summary)

        return summary

    def _process_one_file(
        self, path: Path, confidence_threshold: float | None, summary: dict[str, list]
    ) -> None:
        document_type, parse_kind, profile = _classify(path, self._vendor_profiles)

        try:
            record = self._spine.register(
                path, document_type, {"document_date": _fallback_document_date(path)}
            )
        except Exception as exc:  # noqa: BLE001 — any registration failure quarantines the file
            self._quarantine_file(path, evidence_record_id=None, reason=f"registration failed: {exc}")
            summary["quarantined_files"].append({"file": path.name, "reason": str(exc)})
            self._write_audit(
                action="receipt.process_file", outcome="quarantined",
                input_refs=[path.name], note=f"registration failed: {exc}",
            )
            return

        evidence_record_id = record["evidence_record_id"]

        try:
            lines, document_total = _extract(path, parse_kind, profile, self._extractor)
        except (ValueError, VisionExtractionUnavailable) as exc:
            self._quarantine_file(path, evidence_record_id=evidence_record_id, reason=f"extraction failed: {exc}")
            summary["quarantined_files"].append(
                {"file": path.name, "reason": str(exc), "evidence_record_id": evidence_record_id}
            )
            self._write_audit(
                action="receipt.process_file", outcome="quarantined",
                input_refs=[evidence_record_id], note=f"extraction failed: {exc}",
            )
            return

        kwargs = {} if confidence_threshold is None else {"confidence_threshold": confidence_threshold}
        result = validators.validate_document(self._conn, lines, document_total, **kwargs)

        for quarantined in result.quarantined:
            self._quarantine_line(evidence_record_id, quarantined)
            summary["quarantined_lines"].append(
                {"evidence_record_id": evidence_record_id, "reason": quarantined.reason}
            )

        for line in result.accepted:
            try:
                routed = self._router.route_line(evidence_record_id, line)
                summary["routed"].append({"evidence_record_id": evidence_record_id, **routed})
            except RoutingError as exc:
                self._quarantine_line(
                    evidence_record_id, validators.QuarantinedLine(line, "routing_error", str(exc))
                )
                summary["quarantined_lines"].append(
                    {"evidence_record_id": evidence_record_id, "reason": "routing_error"}
                )

        shutil.move(str(path), str(self._processing_dir / path.name))
        summary["processed"].append({"file": path.name, "evidence_record_id": evidence_record_id})

        outcome = "flagged" if (result.quarantined) else "completed"
        self._write_audit(
            action="receipt.process_file",
            outcome=outcome,
            input_refs=[evidence_record_id],
            output_refs=[r["evidence_record_id"] for r in summary["routed"] if r["evidence_record_id"] == evidence_record_id],
        )

    def _quarantine_file(self, path: Path, *, evidence_record_id: str | None, reason: str) -> None:
        destination = self._quarantine_dir / path.name
        shutil.move(str(path), str(destination))
        self._queue.create(
            type="exception",
            source_worker=ACTOR_NAME,
            priority="urgent",
            subject=f"Intake failure: {path.name}",
            payload_refs=[evidence_record_id] if evidence_record_id else [],
        )

    def _quarantine_line(self, evidence_record_id: str, quarantined: validators.QuarantinedLine) -> None:
        description = (quarantined.line.get("line_description") or "")[:60]
        self._queue.create(
            type="exception",
            source_worker=ACTOR_NAME,
            priority="today",
            subject=f"Line quarantined ({quarantined.reason}): {description}",
            payload_refs=[evidence_record_id],
        )

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


def process_drop(
    config: dict[str, Any],
    *,
    vendor_profiles: list[dict] | None = None,
    confidence_threshold: float | None = None,
) -> dict[str, Any]:
    """Convenience wrapper — build a pipeline and run it once. Prefer
    constructing IntakePipeline directly when calling process_drop
    repeatedly against the same config, to avoid re-bootstrapping."""
    return IntakePipeline(config, vendor_profiles=vendor_profiles).process_drop(
        confidence_threshold=confidence_threshold
    )
