"""Flask UI — Recents chips, Report Type / Date Range / Filter, one
big-number answer, Save For Printing, and a print-queue view.

Every request opens its own connection via flask.g, closed in
teardown_appcontext. Lane B's real threading bug (the dev server doesn't
guarantee a request runs on the thread create_app() ran on) taught this
the hard way — see src/dispatch/queue/app.py's docstring for the story.
Every query route uses the read-only connection; only /save and the
print-queue actions ever touch the writer.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from flask import Flask, abort, g, redirect, render_template, request, url_for

from dispatch.common.db import bootstrap
from dispatch.reports import queries, snapshot
from dispatch.reports.dates import InvalidDateRangeError, quarter_label_for_date, resolve_date_range
from dispatch.reports.db import install_schema
from dispatch.reports.readonly import open_read_only
from dispatch.reports.rendering import render_answer_html
from dispatch.reports.templates_engine import TemplateNotFoundError, load_template

REPORT_TYPES = ("fuel_spend", "expense_summary", "ifta_position")
TEMPLATE_VERSIONS = {"fuel_spend": "1", "expense_summary": "1", "ifta_position": "1"}
REPORT_LABELS = {"fuel_spend": "Fuel", "expense_summary": "Expenses", "ifta_position": "IFTA"}
DATE_RANGE_LABELS = {
    "today": "Today", "yesterday": "Yesterday", "this_week": "This Week",
    "this_month": "This Month", "last_month": "Last Month", "custom": "Custom",
}


def _filters_desc(unit_number, jurisdiction, category) -> dict[str, str]:
    desc = {}
    if unit_number:
        desc["Truck"] = unit_number
    if jurisdiction:
        desc["State"] = jurisdiction
    if category:
        desc["Category"] = category
    return desc


def _compute(conn, report_type: str, date_from: date, date_to: date, *, unit_number, jurisdiction, category):
    if report_type == "fuel_spend":
        return queries.fuel_spend_query(
            conn, date_from=date_from, date_to=date_to, unit_number=unit_number, jurisdiction=jurisdiction
        )
    if report_type == "expense_summary":
        return queries.expense_summary_query(
            conn, date_from=date_from, date_to=date_to, unit_number=unit_number, category=category
        )
    if report_type == "ifta_position":
        # IFTA is inherently quarterly -- the standard Date Range control
        # picks a quarter (the one containing its end date) rather than an
        # arbitrary range. State filtering isn't applied here: filtering
        # ifta_worksheet_lines without also re-deriving total_net_tax would
        # make the big number and the breakdown table visibly disagree,
        # which is exactly the "divergent numbers" risk this lane exists
        # to avoid (LANE_D_LAUNCH_PACKAGE_v1.md risk #3) -- so IFTA Position
        # ignores State/Truck filters entirely in v1. Flagged in NOTES.md.
        quarter = quarter_label_for_date(date_to)
        return queries.ifta_position_query(conn, quarter=quarter)
    raise ValueError(f"unknown report_type {report_type!r}")


def create_app(config: dict) -> Flask:
    app = Flask(__name__)
    app.config["DISPATCH_CONFIG"] = config

    # print_queue otherwise only gets created the first time someone saves
    # a report (ReportSnapshotWriter.__init__ installs it) -- on a fresh
    # database, the very first visit to "/" opens a mode=ro connection via
    # get_ro() before that's ever happened, and recent_reports() 500s with
    # "no such table: print_queue". Installing it here, once, up front,
    # the same way bootstrap() guarantees Lane A's tables exist, closes
    # that gap without changing who's allowed to write to it.
    _startup_conn = bootstrap(config["database"])
    install_schema(_startup_conn)
    _startup_conn.close()

    def get_ro():
        if "ro_conn" not in g:
            g.ro_conn = open_read_only(config["database"])
        return g.ro_conn

    def get_writer() -> snapshot.ReportSnapshotWriter:
        if "writer" not in g:
            g.write_conn = bootstrap(config["database"])
            g.writer = snapshot.ReportSnapshotWriter(g.write_conn, config["roots"]["archive"])
        return g.writer

    @app.teardown_appcontext
    def close_connections(exception=None):
        ro_conn = g.pop("ro_conn", None)
        if ro_conn is not None:
            ro_conn.close()
        write_conn = g.pop("write_conn", None)
        if write_conn is not None:
            write_conn.close()

    def _parse_request_params():
        report_type = request.values.get("report_type", "fuel_spend")
        date_range = request.values.get("date_range", "today")
        unit_number = request.values.get("unit_number") or None
        jurisdiction = request.values.get("jurisdiction") or None
        category = request.values.get("category") or None
        custom_from = request.values.get("custom_from") or None
        custom_to = request.values.get("custom_to") or None
        return report_type, date_range, unit_number, jurisdiction, category, custom_from, custom_to

    def _build_answer(report_type, date_range, unit_number, jurisdiction, category, custom_from, custom_to):
        if report_type not in REPORT_TYPES:
            abort(400, description=f"unknown report_type {report_type!r}")

        custom_from_date = date.fromisoformat(custom_from) if custom_from else None
        custom_to_date = date.fromisoformat(custom_to) if custom_to else None
        try:
            date_from, date_to = resolve_date_range(
                date_range, custom_from=custom_from_date, custom_to=custom_to_date
            )
        except InvalidDateRangeError as exc:
            abort(400, description=str(exc))

        try:
            template = load_template(config["roots"]["library"], report_type, TEMPLATE_VERSIONS[report_type])
        except TemplateNotFoundError as exc:
            abort(500, description=str(exc))

        data = _compute(
            get_ro(), report_type, date_from, date_to,
            unit_number=unit_number, jurisdiction=jurisdiction, category=category,
        )
        return template, data, date_from, date_to

    @app.route("/")
    def index():
        recents = snapshot.recent_reports(get_ro(), limit=3)
        return render_template(
            "index.html", recents=recents, report_types=REPORT_TYPES,
            report_labels=REPORT_LABELS, date_range_labels=DATE_RANGE_LABELS,
        )

    @app.route("/run")
    def run_report():
        (report_type, date_range, unit_number, jurisdiction, category,
         custom_from, custom_to) = _parse_request_params()
        template, data, date_from, date_to = _build_answer(
            report_type, date_range, unit_number, jurisdiction, category, custom_from, custom_to
        )

        if data is None:  # e.g. IFTA Position with no worksheet for the quarter
            return render_template(
                "no_data.html", title=template["title"], period_label=DATE_RANGE_LABELS.get(date_range, date_range),
            )

        from datetime import datetime, timezone

        as_of = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        html_fragment = render_answer_html(
            template, data, as_of=as_of, period_label=DATE_RANGE_LABELS.get(date_range, date_range),
            template_version=TEMPLATE_VERSIONS[report_type],
            filters_desc=_filters_desc(unit_number, jurisdiction, category),
            pending_review_count=queries.pending_review_count(get_ro()),
            standalone=False,
        )
        return render_template(
            "answer.html", answer_html=html_fragment, report_type=report_type, date_range=date_range,
            unit_number=unit_number or "", jurisdiction=jurisdiction or "", category=category or "",
        )

    @app.route("/save", methods=["POST"])
    def save_report():
        (report_type, date_range, unit_number, jurisdiction, category,
         custom_from, custom_to) = _parse_request_params()
        template, data, date_from, date_to = _build_answer(
            report_type, date_range, unit_number, jurisdiction, category, custom_from, custom_to
        )
        if data is None:
            abort(400, description="no data behind this report yet; nothing to save")

        writer = get_writer()
        saved = writer.save_snapshot(
            report_type=report_type,
            template=template,
            template_version=TEMPLATE_VERSIONS[report_type],
            data=data,
            period_label=DATE_RANGE_LABELS.get(date_range, date_range),
            filters_desc=_filters_desc(unit_number, jurisdiction, category),
            pending_review_count=queries.pending_review_count(get_ro()),
        )
        return redirect(url_for("print_queue_view"))

    @app.route("/print-queue")
    def print_queue_view():
        items = snapshot.list_queue(get_ro())
        return render_template("print_queue.html", items=items)

    @app.route("/print-queue/<print_queue_id>/mark-printed", methods=["POST"])
    def mark_printed(print_queue_id):
        try:
            get_writer().mark_printed(print_queue_id)
        except snapshot.PrintQueueItemNotFoundError:
            abort(404)
        return redirect(url_for("print_queue_view"))

    @app.route("/print-queue/<print_queue_id>/clear", methods=["POST"])
    def clear_item(print_queue_id):
        try:
            get_writer().clear(print_queue_id)
        except snapshot.PrintQueueItemNotFoundError:
            abort(404)
        return redirect(url_for("print_queue_view"))

    @app.route("/print-queue/<print_queue_id>/view")
    def view_snapshot(print_queue_id):
        try:
            item = snapshot.list_queue(get_ro())
        except Exception:
            abort(404)
        match = next((i for i in item if i["print_queue_id"] == print_queue_id), None)
        if match is None:
            abort(404)
        from pathlib import Path

        snapshot_path = Path(config["roots"]["archive"]) / match["snapshot_path"]
        if not snapshot_path.is_file():
            abort(404)
        return snapshot_path.read_text(encoding="utf-8")

    return app


if __name__ == "__main__":
    import sys

    from dispatch.common.config import load_config

    if len(sys.argv) != 2:
        print("usage: python -m dispatch.reports.app <config.json>")
        sys.exit(1)

    cfg = load_config(sys.argv[1])
    create_app(cfg).run(host="0.0.0.0", port=8485, debug=False)
