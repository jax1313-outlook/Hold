"""dispatch.ifta_clerk.recommend -- Recommended Payment Amount, the first
of three named Recommendation Package types (IFTA_CLERK_BLUEPRINT_v1
section 13, Phase 6: "a prepared DocuSign package, a drafted accounting
notification, a recommended payment amount -- proposals, never live
sends"). The other two remain named-only, undesigned -- neither has a
real external format to design against in this codebase (no DocuSign
integration, no accounting/QuickBooks integration exists anywhere).

Applies only to a real, sealed worksheet -- matches section 2's "after
sealing" placement; nothing here touches a draft.

**The boundary that matters.** This module writes exactly one artifact
type, to exactly one place: a JSON file under
`ARCHIVE\\IFTA\\<quarter>\\<id>_payment_recommendation.json`, the same
root `attempt_seal()` already writes its own sealed bundle to. No
payment API, no bank integration, no accounting write exists anywhere in
this codebase, and this module doesn't add one -- there is nothing here
*to* send the recommendation to. Generating it is the entire action,
proven structurally: no `requests`/`smtplib`/`urllib` import anywhere in
this file (tests/ifta_clerk/test_recommend.py checks this), and
`generate_payment_recommendation()` never touches the database at all --
its only connection parameter is `read_only_conn`, the same structural
guarantee `preview()` and `live_indicators()` already use. No number is
invented: the recommendation is a label wrapped around
`total_net_tax`, a figure that was already computed, already approved,
and already sealed before this module ever runs.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dispatch.ifta.worksheet import latest_worksheet_for


class RecommendationError(ValueError):
    """Base class for payment recommendation failures."""


class WorksheetNotFoundForRecommendationError(RecommendationError):
    pass


class WorksheetNotSealedError(RecommendationError):
    pass


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def compute_payment_recommendation(worksheet: dict[str, Any]) -> dict[str, Any]:
    """Pure -- no file I/O, no database access. Assumes the caller has
    already confirmed worksheet["status"] == "sealed"; wraps its
    already-approved total_net_tax in a recommendation label, inventing
    no new number. A negative total_net_tax (a net credit) is reported
    as a positive "credit" amount, never a negative figure."""
    total_net_tax = worksheet["total_net_tax"]
    if total_net_tax > 0:
        recommendation, amount = "remit", total_net_tax
    elif total_net_tax < 0:
        recommendation, amount = "credit", abs(total_net_tax)
    else:
        recommendation, amount = "no_payment_due", 0.0

    return {
        "status": "recommendation",
        "recommendation": recommendation,
        "amount": amount,
        "ifta_worksheet_id": worksheet["ifta_worksheet_id"],
        "quarter": worksheet["quarter"],
        "fuel_type": worksheet["fuel_type"],
        "total_net_tax": total_net_tax,
        "sealed_at": worksheet["sealed_at"],
        "generated_at": _utc_now_iso(),
    }


def recommendation_path(roots: dict[str, str], quarter: str, ifta_worksheet_id: str) -> Path:
    return Path(roots["archive"]) / "IFTA" / quarter / f"{ifta_worksheet_id}_payment_recommendation.json"


def existing_recommendation(roots: dict[str, str], quarter: str, ifta_worksheet_id: str) -> dict[str, Any] | None:
    """Read-only lookup -- None if no recommendation has been generated
    for this worksheet yet."""
    path = recommendation_path(roots, quarter, ifta_worksheet_id)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def generate_payment_recommendation(
    read_only_conn: sqlite3.Connection, roots: dict[str, str], *, quarter: str, fuel_type: str
) -> dict[str, Any]:
    """The one write action this module has: writes exactly one JSON
    file to Archive, never the database. Idempotent -- a worksheet that
    already has a recommendation returns the existing one rather than
    regenerating it; the sealed numbers it's computed from can never
    change, so there is nothing a second generation could produce that
    the first one didn't already."""
    worksheet = latest_worksheet_for(read_only_conn, quarter=quarter, fuel_type=fuel_type)
    if worksheet is None:
        raise WorksheetNotFoundForRecommendationError(f"no worksheet has been built for {quarter}/{fuel_type} yet")
    if worksheet["status"] != "sealed":
        raise WorksheetNotSealedError(
            f"worksheet {worksheet['ifta_worksheet_id']} is {worksheet['status']!r}, not sealed -- "
            "payment recommendations only apply after sealing"
        )

    existing = existing_recommendation(roots, quarter, worksheet["ifta_worksheet_id"])
    if existing is not None:
        return existing

    recommendation = compute_payment_recommendation(worksheet)
    path = recommendation_path(roots, quarter, worksheet["ifta_worksheet_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(recommendation, indent=2, sort_keys=True), encoding="utf-8")
    return recommendation
