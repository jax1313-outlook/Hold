"""dispatch.ifta_clerk.prepare -- the IFTA Clerk's first two write
actions: Prepare This Quarter and Submit for Approval
(IFTA_CLERK_BLUEPRINT_v1 section 13, Phase 5, as modified 2026-08-04).

Deliberately a separate module from dashboard.py, which stays exactly as
read-only as it always was -- every write action this app has lives
here, and only here, so "is this module allowed to write?" stays a
one-file question.

**Three distinct stages, three distinct actions -- by direction, not
convention:**

1. **Preparation** (`prepare_quarter()`) -- calls the real
   `WorksheetEngine.build()` then the real `run_all_detectors()`, in
   sequence. Real persistence, real Category 1 exceptions, real
   exception Queue items -- exactly what a real build already does
   today, called together instead of one click at a time.
2. **Review** -- no code here at all. The moment `prepare_quarter()`
   succeeds, `dashboard.build_dashboard()` already shows the real
   worksheet and its real exceptions the next time it's read
   (`latest_worksheet_for()` finds it automatically) -- the dashboard
   *is* the review package, assembled live, not a second artifact this
   module builds and maintains.
3. **Approval Routing** (`submit_quarter_for_approval()`) -- a
   deliberately separate action, calling only `submit_for_approval()`.
   **`prepare_quarter()` never calls this** -- submission is a distinct
   human decision, not bundled into preparation, per direction
   2026-08-04: "Maintain clear separation between Preparation / Review /
   Approval Routing."

Neither function ever reaches `attempt_seal()` -- sealing a worksheet
stays exactly where it already was, reachable only after a real Queue
approval, unchanged by this module.
"""
from __future__ import annotations

import sqlite3
from typing import Any

from dispatch.evidence.interface import EvidenceSpine
from dispatch.ifta import exceptions as ifta_exceptions
from dispatch.ifta.package import WorksheetNotDraftError, submit_for_approval
from dispatch.ifta.worksheet import WorksheetEngine, latest_worksheet_for
from dispatch.ifta_clerk.dashboard import distinct_rate_versions_for_quarter
from dispatch.queue.store import QueueStore


class PrepareError(ValueError):
    """Base class for Prepare This Quarter failures -- never a database
    write happens if one of these is raised."""


class AmbiguousRateVersionError(PrepareError):
    def __init__(self, versions: list[str], quarter: str, fuel_type: str):
        super().__init__(
            f"{len(versions)} rate versions on file for {quarter}/{fuel_type} "
            f"({', '.join(versions)}) -- ambiguous, refusing to pick one"
        )
        self.versions = versions


class NoRateEnteredError(PrepareError):
    pass


class NothingToSubmitError(ValueError):
    pass


class AlreadySubmittedError(ValueError):
    pass


def prepare_quarter(
    write_conn: sqlite3.Connection,
    read_only_conn: sqlite3.Connection,
    roots: dict[str, str],
    *,
    quarter: str,
    fuel_type: str,
) -> dict[str, Any]:
    """Build + run all detectors, real and persisted, exactly as today's
    real build already does -- never submits for approval. Same
    no-fabrication rate-version resolution preview() already uses: a
    quarter with zero or multiple distinct rate versions on file refuses
    rather than guessing."""
    rate_versions = distinct_rate_versions_for_quarter(read_only_conn, quarter=quarter, fuel_type=fuel_type)
    if len(rate_versions) == 0:
        raise NoRateEnteredError(f"no rate has been entered for {quarter}/{fuel_type} yet")
    if len(rate_versions) > 1:
        raise AmbiguousRateVersionError(rate_versions, quarter, fuel_type)

    engine = WorksheetEngine(write_conn, read_only_conn)
    worksheet = engine.build(quarter=quarter, fuel_type=fuel_type, rate_table_version=rate_versions[0])

    spine = EvidenceSpine(write_conn, roots)
    queue = QueueStore(write_conn)
    persisted_exceptions = ifta_exceptions.run_all_detectors(write_conn, read_only_conn, spine, queue, worksheet)

    return {"worksheet": worksheet, "exception_count": len(persisted_exceptions)}


def submit_quarter_for_approval(
    write_conn: sqlite3.Connection, *, quarter: str, fuel_type: str
) -> dict[str, Any]:
    """Submits the real, already-built worksheet for this quarter for
    approval -- a distinct human action from prepare_quarter(), never
    called by it. Refuses if no worksheet exists yet, or if this
    worksheet was already submitted (queue_item_id already set) --
    calling this twice never creates a second approval queue item."""
    worksheet = latest_worksheet_for(write_conn, quarter=quarter, fuel_type=fuel_type)
    if worksheet is None:
        raise NothingToSubmitError(f"no worksheet has been built for {quarter}/{fuel_type} yet")
    if worksheet["queue_item_id"]:
        raise AlreadySubmittedError(
            f"worksheet {worksheet['ifta_worksheet_id']} was already submitted "
            f"(queue item {worksheet['queue_item_id']})"
        )

    queue = QueueStore(write_conn)
    try:
        queue_item = submit_for_approval(write_conn, queue, worksheet)
    except WorksheetNotDraftError:
        raise AlreadySubmittedError(f"worksheet {worksheet['ifta_worksheet_id']} is no longer draft")

    return {"worksheet": worksheet, "queue_item": queue_item}
