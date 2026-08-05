"""dispatch.ifta_clerk -- the Review Dashboard, the primary user
experience of the IFTA Clerk (IFTA_CLERK_BLUEPRINT_v1 section 7,
approved 2026-08-04).

Three deliberate write actions: `POST /prepare` and `POST /submit`
(2026-08-04, Phase 5), and `POST /recommend-payment` (2026-08-04, Phase
6's first named package -- Recommended Payment Amount), all thin
wrappers around dispatch.ifta_clerk.prepare's and .recommend's real
functions. Every other route is GET. This module (app.py) is the only
place in this app that ever imports
QueueStore/EvidenceSpine/dispatch.ifta.package -- dashboard.py stays
exactly as read-only as it always was, and prepare.py/recommend.py are
the only other modules allowed to write, so "can this write?" stays a
small, explicit surface, checked by ast-parsed import tests in
tests/ifta_clerk/test_app.py, not just this docstring's promise. No
route ever reaches attempt_seal() -- sealing a worksheet is unchanged,
reachable only after a real Queue approval. recommend_payment() itself
never touches the database at all -- it's the only write route backed
solely by a read-only connection, since generating a payment
recommendation only ever writes a file to Archive.

flask.g per-request connection lifetime, the same pattern every other
app in this project already uses.

create_app() bootstraps the database file once at startup (same
precedent as dispatch.reports.app.create_app()) -- a genuinely fresh
install has no database file at all yet, and SQLite's mode=ro connection
fails outright to even open a file that doesn't exist, before any table
check can run. This is a startup-only exception to "no write-capable
connection ever in scope by default": it only ever creates the common
tables (evidence_records, mileage_records, queue_items, audit_log)
bootstrap() already owns.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from flask import Flask, g, redirect, render_template, request, url_for

from dispatch.common.db import bootstrap
from dispatch.ifta.worksheet import InsufficientDataError, InvalidQuarterError, MissingRateError
from dispatch.ifta_clerk.dashboard import build_dashboard
from dispatch.ifta_clerk.prepare import (
    AlreadySubmittedError,
    AmbiguousRateVersionError,
    NoRateEnteredError,
    NothingToSubmitError,
    prepare_quarter,
    submit_quarter_for_approval,
)
from dispatch.ifta_clerk.readonly import open_read_only
from dispatch.ifta_clerk.recommend import (
    WorksheetNotFoundForRecommendationError,
    WorksheetNotSealedError,
    existing_recommendation,
    generate_payment_recommendation,
)

DEFAULT_FUEL_TYPE = "diesel"


def _current_quarter() -> str:
    today = datetime.now(timezone.utc).date()
    q = (today.month - 1) // 3 + 1
    return f"{today.year}-Q{q}"


def _payment_recommendation_for(config: dict[str, Any], data: dict[str, Any], quarter: str):
    """None unless the tax position is a real, sealed worksheet -- a
    payment recommendation is meaningless for a draft or a live
    estimate."""
    worksheet = data["tax_position"].get("worksheet")
    if worksheet is None or worksheet["status"] != "sealed":
        return None
    return existing_recommendation(config["roots"], quarter, worksheet["ifta_worksheet_id"])


def create_app(config: dict[str, Any]) -> Flask:
    app = Flask(__name__)
    app.config["DISPATCH_CONFIG"] = config

    _startup_conn = bootstrap(config["database"])
    _startup_conn.close()

    def get_ro():
        if "ro_conn" not in g:
            g.ro_conn = open_read_only(config["database"])
        return g.ro_conn

    def get_write_conn():
        if "write_conn" not in g:
            g.write_conn = bootstrap(config["database"])
        return g.write_conn

    @app.teardown_appcontext
    def close_connections(exception=None):
        ro_conn = g.pop("ro_conn", None)
        if ro_conn is not None:
            ro_conn.close()
        write_conn = g.pop("write_conn", None)
        if write_conn is not None:
            write_conn.close()

    @app.route("/")
    def dashboard():
        quarter = request.args.get("quarter") or _current_quarter()
        fuel_type = request.args.get("fuel_type") or DEFAULT_FUEL_TYPE

        try:
            data = build_dashboard(get_ro(), quarter=quarter, fuel_type=fuel_type)
        except InvalidQuarterError as exc:
            return render_template(
                "dashboard.html", error=str(exc), quarter=quarter, fuel_type=fuel_type,
                data=None, banner=None, payment_recommendation=None,
            ), 400

        banner = None
        if request.args.get("prepared"):
            banner = {"kind": "prepared", "exception_count": request.args.get("exceptions", "0")}
        elif request.args.get("submitted"):
            banner = {"kind": "submitted"}
        elif request.args.get("recommended"):
            banner = {"kind": "recommended"}

        payment_recommendation = _payment_recommendation_for(config, data, quarter)

        return render_template(
            "dashboard.html", error=None, quarter=quarter, fuel_type=fuel_type,
            data=data, banner=banner, payment_recommendation=payment_recommendation,
        )

    @app.route("/prepare", methods=["POST"])
    def prepare():
        quarter = request.form.get("quarter") or _current_quarter()
        fuel_type = request.form.get("fuel_type") or DEFAULT_FUEL_TYPE

        try:
            result = prepare_quarter(get_write_conn(), get_ro(), config["roots"], quarter=quarter, fuel_type=fuel_type)
        except (NoRateEnteredError, AmbiguousRateVersionError, InsufficientDataError, MissingRateError) as exc:
            data = build_dashboard(get_ro(), quarter=quarter, fuel_type=fuel_type)
            return render_template(
                "dashboard.html", error=f"Could not prepare this quarter: {exc}",
                quarter=quarter, fuel_type=fuel_type, data=data, banner=None,
                payment_recommendation=_payment_recommendation_for(config, data, quarter),
            ), 400

        return redirect(url_for("dashboard", quarter=quarter, fuel_type=fuel_type, prepared=1, exceptions=result["exception_count"]))

    @app.route("/submit", methods=["POST"])
    def submit():
        quarter = request.form.get("quarter") or _current_quarter()
        fuel_type = request.form.get("fuel_type") or DEFAULT_FUEL_TYPE

        try:
            submit_quarter_for_approval(get_write_conn(), quarter=quarter, fuel_type=fuel_type)
        except (NothingToSubmitError, AlreadySubmittedError) as exc:
            data = build_dashboard(get_ro(), quarter=quarter, fuel_type=fuel_type)
            return render_template(
                "dashboard.html", error=f"Could not submit for approval: {exc}",
                quarter=quarter, fuel_type=fuel_type, data=data, banner=None,
                payment_recommendation=_payment_recommendation_for(config, data, quarter),
            ), 400

        return redirect(url_for("dashboard", quarter=quarter, fuel_type=fuel_type, submitted=1))

    @app.route("/recommend-payment", methods=["POST"])
    def recommend_payment():
        quarter = request.form.get("quarter") or _current_quarter()
        fuel_type = request.form.get("fuel_type") or DEFAULT_FUEL_TYPE

        try:
            generate_payment_recommendation(get_ro(), config["roots"], quarter=quarter, fuel_type=fuel_type)
        except (WorksheetNotFoundForRecommendationError, WorksheetNotSealedError) as exc:
            data = build_dashboard(get_ro(), quarter=quarter, fuel_type=fuel_type)
            return render_template(
                "dashboard.html", error=f"Could not generate payment recommendation: {exc}",
                quarter=quarter, fuel_type=fuel_type, data=data, banner=None,
                payment_recommendation=_payment_recommendation_for(config, data, quarter),
            ), 400

        return redirect(url_for("dashboard", quarter=quarter, fuel_type=fuel_type, recommended=1))

    return app


if __name__ == "__main__":
    import sys

    from dispatch.common.config import load_config

    if len(sys.argv) != 2:
        print("usage: python -m dispatch.ifta_clerk.app <config.json>")
        sys.exit(1)

    cfg = load_config(sys.argv[1])
    create_app(cfg).run(host="0.0.0.0", port=8486, debug=False)
