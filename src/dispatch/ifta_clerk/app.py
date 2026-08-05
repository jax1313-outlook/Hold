"""dispatch.ifta_clerk -- the Review Dashboard, the primary user
experience of the IFTA Clerk (IFTA_CLERK_BLUEPRINT_v1 section 7,
approved 2026-08-04).

Four deliberate write actions: `POST /prepare` and `POST /submit`
(2026-08-04, Phase 5), `POST /recommend-payment` (2026-08-04, Phase 6's
first named package -- Recommended Payment Amount), and
`POST /record-mileage` (2026-08-05 -- mileage source strategy, see
docs/decisions/DECISION_LOG.md). Every other route is GET. This module
(app.py) is the only place in this app that ever imports
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

record_mileage() (the /record-mileage route) is manual entry's real
write path, shared with tools/mileage_worksheet.py -- mileage source
strategy is decided (manual, permanent, no ELD/GPS/odometer-device
integration; see docs/decisions/DECISION_LOG.md), so this route is
mileage's normal front door now, not a stopgap. After a successful
entry it computes a live, rate-independent fleet_mpg estimate
(worksheet.live_fleet_mpg_estimate()) and, if it falls outside
exceptions.DEFAULT_MPG_BAND, shows a non-blocking warning banner on the
redirect -- the entry is never refused; mileage is a human's own
attestation, and this route doesn't get to reject it, only flag it
early instead of only after a full worksheet build.

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
from dispatch.ifta.exceptions import DEFAULT_MPG_BAND
from dispatch.ifta.mileage import record_mileage
from dispatch.ifta.worksheet import (
    InsufficientDataError,
    InvalidQuarterError,
    MissingRateError,
    live_fleet_mpg_estimate,
)
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
                data=None, banner=None, payment_recommendation=None, mileage_warning=None,
            ), 400

        banner = None
        if request.args.get("prepared"):
            banner = {"kind": "prepared", "exception_count": request.args.get("exceptions", "0")}
        elif request.args.get("submitted"):
            banner = {"kind": "submitted"}
        elif request.args.get("recommended"):
            banner = {"kind": "recommended"}
        elif request.args.get("mileage_recorded"):
            banner = {"kind": "mileage_recorded"}

        payment_recommendation = _payment_recommendation_for(config, data, quarter)
        mileage_warning = request.args.get("mpg_warning")

        return render_template(
            "dashboard.html", error=None, quarter=quarter, fuel_type=fuel_type,
            data=data, banner=banner, payment_recommendation=payment_recommendation,
            mileage_warning=mileage_warning,
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
                mileage_warning=None,
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
                mileage_warning=None,
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
                mileage_warning=None,
            ), 400

        return redirect(url_for("dashboard", quarter=quarter, fuel_type=fuel_type, recommended=1))

    @app.route("/record-mileage", methods=["POST"])
    def record_mileage_route():
        quarter = request.form.get("quarter") or _current_quarter()
        fuel_type = request.form.get("fuel_type") or DEFAULT_FUEL_TYPE

        unit_number = request.form.get("unit_number", "").strip()
        jurisdiction = request.form.get("jurisdiction", "").strip().upper()
        period_start = request.form.get("period_start", "").strip()
        period_end = request.form.get("period_end", "").strip()
        entered_by = request.form.get("entered_by", "").strip()
        miles_raw = request.form.get("miles", "").strip()

        errors = []
        if not unit_number:
            errors.append("unit is required")
        if not jurisdiction:
            errors.append("jurisdiction is required")
        if not period_start:
            errors.append("period start is required")
        if not period_end:
            errors.append("period end is required")
        if not entered_by:
            errors.append("entered by is required")
        miles = None
        if not miles_raw:
            errors.append("miles is required")
        else:
            try:
                miles = float(miles_raw)
            except ValueError:
                errors.append("miles must be a number")

        if errors:
            data = build_dashboard(get_ro(), quarter=quarter, fuel_type=fuel_type)
            return render_template(
                "dashboard.html", error=f"Could not record mileage: {'; '.join(errors)}",
                quarter=quarter, fuel_type=fuel_type, data=data, banner=None,
                payment_recommendation=_payment_recommendation_for(config, data, quarter),
                mileage_warning=None,
            ), 400

        record_mileage(
            get_write_conn(), unit_number=unit_number, jurisdiction=jurisdiction,
            period_start=period_start, period_end=period_end, miles=miles, entered_by=entered_by,
        )

        redirect_args = {"quarter": quarter, "fuel_type": fuel_type, "mileage_recorded": 1}
        estimate = live_fleet_mpg_estimate(get_ro(), quarter=quarter, fuel_type=fuel_type)
        low, high = DEFAULT_MPG_BAND
        if estimate is not None and not (low <= estimate <= high):
            redirect_args["mpg_warning"] = f"{estimate:.2f}"

        return redirect(url_for("dashboard", **redirect_args))

    return app


if __name__ == "__main__":
    import sys

    from dispatch.common.config import load_config

    if len(sys.argv) != 2:
        print("usage: python -m dispatch.ifta_clerk.app <config.json>")
        sys.exit(1)

    cfg = load_config(sys.argv[1])
    create_app(cfg).run(host="0.0.0.0", port=8486, debug=False)
