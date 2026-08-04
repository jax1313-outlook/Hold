"""dispatch.ifta.app -- mileage entry, rate entry, worksheet build (with
exceptions computed together), submit for approval, and seal, all as
real browser actions. Every write here calls an existing, unmodified
function in dispatch.ifta.{rates,worksheet,exceptions,package} -- this
module adds no new business logic, no recomputation, no loosened check.

Approval itself is NOT here -- it already works today through the
mounted Queue (dispatch.queue.app), proved live in
docs/pilot/DISPATCH_PILOT_RUN_2_REPORT_v1.md. attempt_seal()'s real
refusal-before-approval is preserved exactly; this module only surfaces
it, never bypasses or duplicates it.

Two things duplicated rather than imported across a lane boundary, same
precedent every prior lane's own read-only helpers already set (Reports'
readonly.py, the Shell's style.css): a quarter-from-date formula (Reports
owns the canonical one in dispatch.reports.dates, but Reports is a
downstream consumer of IFTA, not a dependency IFTA should reach into),
and the mileage_records INSERT tools/mileage_worksheet.py's
record_mileage() already performs (that script lives outside src/dispatch,
not meant to be imported as a library).

Eagerly installs dispatch.ifta.db's schema at startup, same fix Reports'
own app.py already applies to print_queue: rate_tables/ifta_worksheets/
etc. are otherwise created lazily by WorksheetEngine/rates.py the first
time something real happens, so a genuinely fresh install would 500 on
its very first page load without this.

flask.g per-request connection lifetime, same pattern every other app in
this system uses, for the same documented reason (the dev server's
request threads are not guaranteed to be the thread create_app() ran
on).
"""
from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from typing import Any

from flask import Flask, abort, g, redirect, render_template, request, url_for

from dispatch.common.db import bootstrap
from dispatch.common.ids import new_ulid
from dispatch.evidence.interface import EvidenceSpine
from dispatch.ifta import rates
from dispatch.ifta.db import install_schema
from dispatch.ifta.exceptions import run_all_detectors
from dispatch.ifta.package import (
    ApprovalNotYetGrantedError,
    attempt_seal,
    submit_for_approval,
)
from dispatch.ifta.package import WorksheetNotFoundError as PackageWorksheetNotFoundError
from dispatch.ifta.readonly import open_read_only
from dispatch.ifta.worksheet import (
    InsufficientDataError,
    InvalidQuarterError,
    MissingRateError,
    WorksheetEngine,
    WorksheetNotFoundError,
)
from dispatch.queue.store import QueueStore

DEFAULT_FUEL_TYPE = "diesel"


def _quarter_label_for_date(d: date) -> str:
    return f"{d.year}-Q{(d.month - 1) // 3 + 1}"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def create_app(config: dict[str, Any]) -> Flask:
    app = Flask(__name__)
    app.config["DISPATCH_CONFIG"] = config

    _startup_conn = bootstrap(config["database"])
    install_schema(_startup_conn)
    _startup_conn.close()

    def get_conn():
        if "conn" not in g:
            g.conn = bootstrap(config["database"])
        return g.conn

    def get_ro():
        if "ro_conn" not in g:
            g.ro_conn = open_read_only(config["database"])
        return g.ro_conn

    def get_engine() -> WorksheetEngine:
        return WorksheetEngine(get_conn(), get_ro())

    def get_queue() -> QueueStore:
        return QueueStore(get_conn())

    def get_spine() -> EvidenceSpine:
        return EvidenceSpine(get_conn(), config["roots"])

    @app.teardown_appcontext
    def close_connections(exception=None):
        ro_conn = g.pop("ro_conn", None)
        if ro_conn is not None:
            ro_conn.close()
        conn = g.pop("conn", None)
        if conn is not None:
            conn.close()

    def _worksheets_and_defaults(**extra):
        conn = get_conn()
        worksheets = [dict(w) for w in conn.execute(
            "SELECT * FROM ifta_worksheets ORDER BY created_at DESC"
        ).fetchall()]
        default_quarter = _quarter_label_for_date(date.today())
        versions = [
            row[0] for row in conn.execute(
                "SELECT DISTINCT source_version FROM rate_tables WHERE quarter = ? AND fuel_type = ? "
                "ORDER BY source_version DESC",
                (default_quarter, DEFAULT_FUEL_TYPE),
            ).fetchall()
        ]
        context = dict(
            worksheets=worksheets,
            default_quarter=default_quarter,
            default_fuel_type=DEFAULT_FUEL_TYPE,
            available_versions=versions,
            build_error=None,
        )
        context.update(extra)
        return context

    @app.route("/")
    def index():
        return render_template("index.html", **_worksheets_and_defaults())

    @app.route("/build", methods=["POST"])
    def build():
        quarter = request.form.get("quarter", "").strip()
        fuel_type = request.form.get("fuel_type", "").strip()
        rate_table_version = request.form.get("rate_table_version", "").strip()

        engine = get_engine()
        try:
            worksheet = engine.build(
                quarter=quarter, fuel_type=fuel_type, rate_table_version=rate_table_version
            )
        except (InvalidQuarterError, MissingRateError, InsufficientDataError) as exc:
            return render_template("index.html", **_worksheets_and_defaults(build_error=str(exc))), 400
        except sqlite3.OperationalError as exc:
            # A genuinely fresh install where no receipt has ever been
            # processed has no fuel_records table at all yet -- a real,
            # pre-existing gap in WorksheetEngine._aggregate_fuel() (no
            # table-existence guard, the same bug class Lane D's own
            # queries.py had before it was fixed). Not fixed here --
            # worksheet.py is out of this package's scope -- but this
            # lane's own "no report/worksheet renders without complete
            # data" instinct still applies: treat it exactly like
            # InsufficientDataError instead of a raw crash. Flagged in
            # docs/ifta-ui/NOTES.md, not silently patched around forever.
            if "no such table" not in str(exc):
                raise
            build_error = "no fuel or mileage data recorded yet for this quarter -- cannot compute fleet_mpg"
            return render_template("index.html", **_worksheets_and_defaults(build_error=build_error)), 400

        run_all_detectors(get_conn(), get_ro(), get_spine(), get_queue(), worksheet)
        return redirect(url_for("worksheet_detail", ifta_worksheet_id=worksheet["ifta_worksheet_id"]))

    @app.route("/worksheets/<ifta_worksheet_id>")
    def worksheet_detail(ifta_worksheet_id):
        engine = get_engine()
        try:
            worksheet = engine.get(ifta_worksheet_id)
        except WorksheetNotFoundError:
            abort(404)

        conn = get_conn()
        findings = [dict(row) for row in conn.execute(
            "SELECT exception_type, detail, detected_at FROM ifta_exceptions "
            "WHERE ifta_worksheet_id = ? ORDER BY detected_at",
            (ifta_worksheet_id,),
        ).fetchall()]

        queue_item = None
        can_seal = False
        seal_blocked_reason = None
        if worksheet.get("queue_item_id"):
            queue_item = get_queue().get(worksheet["queue_item_id"])
            can_seal = queue_item["status"] == "approved"
            if not can_seal:
                seal_blocked_reason = f"waiting on approval -- queue item is {queue_item['status']!r}, see Queue"
        elif worksheet["status"] == "draft":
            seal_blocked_reason = "not submitted for approval yet"

        return render_template(
            "worksheet.html",
            worksheet=worksheet,
            findings=findings,
            queue_item=queue_item,
            can_submit=(worksheet["status"] == "draft" and not worksheet.get("queue_item_id")),
            can_seal=(can_seal and worksheet["status"] == "draft"),
            seal_blocked_reason=seal_blocked_reason,
        )

    @app.route("/worksheets/<ifta_worksheet_id>/submit", methods=["POST"])
    def submit(ifta_worksheet_id):
        conn = get_conn()
        row = conn.execute(
            "SELECT * FROM ifta_worksheets WHERE ifta_worksheet_id = ?", (ifta_worksheet_id,)
        ).fetchone()
        if row is None:
            abort(404)
        submit_for_approval(conn, get_queue(), dict(row))
        return redirect(url_for("worksheet_detail", ifta_worksheet_id=ifta_worksheet_id))

    @app.route("/worksheets/<ifta_worksheet_id>/seal", methods=["POST"])
    def seal(ifta_worksheet_id):
        try:
            attempt_seal(get_conn(), get_queue(), config["roots"], ifta_worksheet_id)
        except ApprovalNotYetGrantedError:
            pass  # the detail page already explains why; nothing hidden, nothing bypassed
        except PackageWorksheetNotFoundError:
            abort(404)
        return redirect(url_for("worksheet_detail", ifta_worksheet_id=ifta_worksheet_id))

    @app.route("/rates")
    def rates_page():
        conn = get_conn()
        rows = [dict(r) for r in conn.execute(
            "SELECT * FROM rate_tables ORDER BY quarter DESC, jurisdiction"
        ).fetchall()]
        return render_template("rates.html", rates=rows, error=None)

    @app.route("/rates", methods=["POST"])
    def rates_add():
        conn = get_conn()
        try:
            surcharge_raw = request.form.get("surcharge", "").strip()
            rates.insert_rate(
                conn,
                jurisdiction=request.form["jurisdiction"].strip().upper(),
                quarter=request.form["quarter"].strip(),
                fuel_type=request.form["fuel_type"].strip(),
                rate=float(request.form["rate"]),
                surcharge=float(surcharge_raw) if surcharge_raw else None,
                source_version=request.form["source_version"].strip(),
            )
        except (KeyError, ValueError) as exc:
            rows = [dict(r) for r in conn.execute(
                "SELECT * FROM rate_tables ORDER BY quarter DESC, jurisdiction"
            ).fetchall()]
            return render_template("rates.html", rates=rows, error=str(exc)), 400
        return redirect(url_for("rates_page"))

    @app.route("/mileage")
    def mileage_page():
        conn = get_conn()
        rows = [dict(r) for r in conn.execute(
            "SELECT * FROM mileage_records ORDER BY period_start DESC"
        ).fetchall()]
        return render_template("mileage.html", records=rows, error=None)

    @app.route("/mileage", methods=["POST"])
    def mileage_add():
        conn = get_conn()
        try:
            entered_by = request.form.get("entered_by", "").strip()
            if not entered_by:
                raise ValueError("entered_by is required -- who entered this mileage?")
            odometer_start_raw = request.form.get("odometer_start", "").strip()
            odometer_end_raw = request.form.get("odometer_end", "").strip()

            # Duplicates tools/mileage_worksheet.py's record_mileage() --
            # that script lives outside src/dispatch, not meant to be
            # imported as a library; both stay independently correct
            # against the same real mileage_record.schema.json shape.
            mileage_record_id = new_ulid()
            conn.execute(
                """
                INSERT INTO mileage_records (
                    mileage_record_id, unit_number, period_start, period_end,
                    jurisdiction, miles, source, odometer_start, odometer_end,
                    entered_by, schema_version
                ) VALUES (?, ?, ?, ?, ?, ?, 'manual_worksheet', ?, ?, ?, '1.0')
                """,
                (
                    mileage_record_id,
                    request.form["unit_number"].strip(),
                    request.form["period_start"].strip(),
                    request.form["period_end"].strip(),
                    request.form["jurisdiction"].strip().upper(),
                    float(request.form["miles"]),
                    int(odometer_start_raw) if odometer_start_raw else None,
                    int(odometer_end_raw) if odometer_end_raw else None,
                    entered_by,
                ),
            )
        except (KeyError, ValueError) as exc:
            rows = [dict(r) for r in conn.execute(
                "SELECT * FROM mileage_records ORDER BY period_start DESC"
            ).fetchall()]
            return render_template("mileage.html", records=rows, error=str(exc)), 400
        return redirect(url_for("mileage_page"))

    return app


if __name__ == "__main__":
    import sys

    from dispatch.common.config import load_config

    if len(sys.argv) != 2:
        print("usage: python -m dispatch.ifta.app <config.json>")
        sys.exit(1)

    cfg = load_config(sys.argv[1])
    create_app(cfg).run(host="0.0.0.0", port=8482, debug=False)
