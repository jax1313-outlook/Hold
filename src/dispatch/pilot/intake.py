"""DispatchPilot's Inbox sorter.

Mike drops files into DispatchPilot\\Inbox. process_inbox(config) scans it
once per call (same "no daemon, an external trigger calls this" pattern
as dispatch.receipt.intake.process_drop — a cron job, a manual trigger,
or a scheduled task outside this codebase turns this into a "watcher"
operationally) and, per file, deterministically decides one of two paths:

1. **A real receipt** (fuel/expense-shaped): staged into the real
   OPERATIONS\\Intake\\Drop and run through Lane C's actual, unmodified
   dispatch.receipt.intake.IntakePipeline — the same code every prior
   walkthrough has proven. On success, a copy of the source lands in
   DispatchPilot\\Fuel (if it produced a FuelRecord) or \\Receipts
   (expense-only). A file that fails outright stays exactly where Lane
   C's own pipeline already puts it (Intake\\Quarantine), surfaced
   through the real Queue — no second quarantine path invented here.

2. **A document type this system doesn't have processing logic for yet**
   (RateCon, POD, ELD) or genuinely unrecognized (Misc): registered as
   real governed evidence via the real, unmodified EvidenceSpine.register
   -- the Evidence First Doctrine (docs/decisions/DECISION_LOG.md,
   2026-08-04): a legitimate business artifact is evidence whether or not
   this system can process its contents yet. No secondary or
   reduced-trust path -- same EvidenceSpine every other lane uses. Filed
   into the matching folder, with a non-urgent ("whenever") review queue
   item -- distinguishable from a genuine intake failure, which is
   "urgent."

Classification is deterministic and auditable, never inferred: a
filename-token match (the same "data, not inference" philosophy Lane C's
own vendor-profile matcher already uses) takes priority, then a bounded
set of extensions Dispatch actually knows how to attempt extraction on.
Nothing here guesses at a document's contents.
"""
from __future__ import annotations

import os
import shutil
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from dispatch.common import audit
from dispatch.common.db import bootstrap
from dispatch.evidence.interface import EvidenceSpine
from dispatch.queue.store import QueueStore
from dispatch.receipt.intake import IntakePipeline

ACTOR_NAME = "pilot"
ACTOR_VERSION = "1.0.0"
# There is no dedicated pilot constitution -- this module's authority is
# the base constitution plus the Evidence First Doctrine decision
# (docs/decisions/DECISION_LOG.md, 2026-08-04), not a bespoke new one.
CONSTITUTION_VERSION = "DISPATCH_BASE_CONSTITUTION_v1"

PILOT_FOLDERS = ("Inbox", "Fuel", "Receipts", "RateCons", "POD", "ELD", "Misc")

# Filename-token match wins over everything else -- the human's own label
# on the file is the strongest signal this system has, and matches the
# existing vendor-profile-matching precedent (exact match on data the
# human provided, never an inference about document contents).
_KEYWORD_ROUTES: dict[str, tuple[str, str]] = {
    "ratecon": ("RateCons", "rate_confirmation"),
    "ratecons": ("RateCons", "rate_confirmation"),
    "rc": ("RateCons", "rate_confirmation"),
    "pod": ("POD", "proof_of_delivery"),
    "eld": ("ELD", "eld_export"),
}

# Extensions Dispatch actually has a real extraction attempt for today:
# .csv through the deterministic CSV parser, the rest through vision
# extraction (which honestly quarantines without live credentials --
# exercising the real designed failure path, not a fabricated one).
_RECEIPT_CANDIDATE_EXTENSIONS = {".csv", ".pdf", ".jpg", ".jpeg", ".png"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _fallback_document_date(path: Path) -> str:
    return date.fromtimestamp(os.path.getmtime(path)).isoformat()


def _filename_tokens(path: Path) -> set[str]:
    """Split the filename stem on anything non-alphanumeric, lowercased --
    'RateCon_Acme_Load44.pdf' -> {'ratecon', 'acme', 'load44'}. A bounded
    token match (not a raw substring search) so 'tripod' doesn't
    false-match the 'pod' route."""
    stem = path.stem.lower()
    token = ""
    tokens: set[str] = set()
    for ch in stem:
        if ch.isalnum():
            token += ch
        else:
            if token:
                tokens.add(token)
            token = ""
    if token:
        tokens.add(token)
    return tokens


def classify(path: Path) -> tuple[str, str | None]:
    """Returns (route, document_type). route is one of "receipt" (send
    through the real Lane C pipeline) or a PILOT_FOLDERS name to file
    directly under (document_type is the evidence_record.document_type to
    register with; None only for "receipt", since Lane C's own _classify
    decides that)."""
    tokens = _filename_tokens(path)
    for token in tokens:
        if token in _KEYWORD_ROUTES:
            return _KEYWORD_ROUTES[token]

    if path.suffix.lower() in _RECEIPT_CANDIDATE_EXTENSIONS:
        return "receipt", None

    return "Misc", "unclassified"


class PilotIntake:
    def __init__(self, config: dict[str, Any]):
        self._config = config
        self._conn = bootstrap(config["database"])
        self._spine = EvidenceSpine(self._conn, config["roots"])
        self._queue = QueueStore(self._conn)

        operations_root = Path(config["roots"]["operations"])
        self._pilot_root = operations_root / "DispatchPilot"
        self._folders = {name: self._pilot_root / name for name in PILOT_FOLDERS}
        for folder in self._folders.values():
            folder.mkdir(parents=True, exist_ok=True)

    @property
    def inbox(self) -> Path:
        return self._folders["Inbox"]

    @property
    def pilot_root(self) -> Path:
        return self._pilot_root

    @property
    def folders(self) -> dict[str, Path]:
        return dict(self._folders)

    def close(self) -> None:
        """Closes the connection this instance opened in __init__. A
        caller that constructs a PilotIntake per request (the shell app's
        flask.g pattern -- same as every other lane's own per-request
        connection lifetime) needs a public way to close it in
        teardown_appcontext without reaching into a private attribute."""
        self._conn.close()

    def process_inbox(self) -> dict[str, list]:
        summary: dict[str, list] = {
            "receipt_batch": [],
            "held_for_review": [],
        }
        if not self.inbox.is_dir():
            return summary

        receipt_candidates: list[Path] = []
        for path in sorted(self.inbox.iterdir()):
            if not path.is_file():
                continue
            route, document_type = classify(path)
            if route == "receipt":
                receipt_candidates.append(path)
            else:
                self._hold_for_review(path, folder_name=route, document_type=document_type, summary=summary)

        if receipt_candidates:
            self._process_receipt_batch(receipt_candidates, summary)

        return summary

    def _hold_for_review(
        self, path: Path, *, folder_name: str, document_type: str, summary: dict[str, list]
    ) -> None:
        record = self._spine.register(
            path, document_type, {"document_date": _fallback_document_date(path)}
        )
        evidence_record_id = record["evidence_record_id"]

        destination = self._folders[folder_name] / path.name
        shutil.move(str(path), str(destination))

        queue_item = self._queue.create(
            type="review",
            source_worker=ACTOR_NAME,
            priority="whenever",
            subject=f"New {document_type.replace('_', ' ')} awaiting future processing: {path.name}",
            payload_refs=[evidence_record_id],
        )

        self._write_audit(
            action="pilot.hold_for_review",
            outcome="completed",
            input_refs=[path.name],
            output_refs=[evidence_record_id, queue_item["queue_item_id"]],
            note=f"filed under DispatchPilot/{folder_name}",
        )

        summary["held_for_review"].append(
            {
                "file": path.name,
                "folder": folder_name,
                "document_type": document_type,
                "evidence_record_id": evidence_record_id,
                "queue_item_id": queue_item["queue_item_id"],
            }
        )

    def _process_receipt_batch(self, candidates: list[Path], summary: dict[str, list]) -> None:
        drop_dir = Path(self._config["roots"]["operations"]) / "Intake" / "Drop"
        drop_dir.mkdir(parents=True, exist_ok=True)

        staged_names = set()
        for path in candidates:
            shutil.move(str(path), str(drop_dir / path.name))
            staged_names.add(path.name)

        pipeline = IntakePipeline(self._config)
        result = pipeline.process_drop()

        produced_fuel = {r["evidence_record_id"] for r in result["routed"] if "fuel_record_id" in r}
        produced_expense_only = {
            r["evidence_record_id"] for r in result["routed"] if "fuel_record_id" not in r
        } - produced_fuel

        processing_dir = Path(self._config["roots"]["operations"]) / "Intake" / "Processing"
        for entry in result["processed"]:
            filename = entry["file"]
            if filename not in staged_names:
                continue  # not this batch's file -- don't misattribute someone else's drop
            evidence_record_id = entry["evidence_record_id"]
            if evidence_record_id in produced_fuel:
                destination_folder = "Fuel"
            elif evidence_record_id in produced_expense_only:
                destination_folder = "Receipts"
            else:
                destination_folder = None  # registered + extracted, but every line quarantined

            outcome = {
                "file": filename,
                "evidence_record_id": evidence_record_id,
                "destination_folder": destination_folder,
            }
            if destination_folder:
                source = processing_dir / filename
                if source.is_file():
                    shutil.copy2(source, self._folders[destination_folder] / filename)
            summary["receipt_batch"].append(outcome)

        for entry in result["quarantined_files"]:
            if entry["file"] not in staged_names:
                continue
            summary["receipt_batch"].append(
                {"file": entry["file"], "evidence_record_id": entry.get("evidence_record_id"),
                 "destination_folder": None, "quarantined": True, "reason": entry["reason"]}
            )

        self._write_audit(
            action="pilot.process_receipt_batch",
            outcome="completed",
            input_refs=sorted(staged_names),
            output_refs=[e["evidence_record_id"] for e in result["processed"]],
            note=f"{len(result['processed'])} processed, {len(result['quarantined_files'])} quarantined",
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


def process_inbox(config: dict[str, Any]) -> dict[str, list]:
    """Convenience wrapper -- build a PilotIntake and run it once."""
    return PilotIntake(config).process_inbox()
