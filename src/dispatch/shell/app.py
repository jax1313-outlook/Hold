"""dispatch.shell -- Mike's one bookmark.

Mounts Queue's and Reports' existing, completely unmodified Flask apps
at /queue and /reports via Werkzeug's DispatcherMiddleware -- their
route definitions, templates, and static files change not at all; this
module never imports their internals, only their public create_app().
Adds two things neither existing app has: a home dashboard (real open
queue by priority, real DispatchPilot folder state, real recent saved
reports) and a /pilot page with a real "Process Inbox" button.

Zero new tables, zero new contracts, zero writes of its own -- the only
write action calls dispatch.pilot.intake.PilotIntake.process_inbox(),
the same real, already-governed pipeline the pilot module always ran.
Every read goes through another lane's own real public read API
(QueueStore.list_all, dispatch.reports.snapshot.recent_reports) rather
than raw SQL or reimplemented logic.

flask.g per-request connection lifetime, same pattern Lane B's and Lane
D's own apps already use (and the same real threading bug those two
docstrings describe is exactly why: the dev server's request threads are
not guaranteed to be the thread create_app() ran on).
"""
from __future__ import annotations

from typing import Any

from flask import Flask, g, render_template
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from dispatch.common.db import bootstrap
from dispatch.ifta.app import create_app as create_ifta_app
from dispatch.pilot.intake import PilotIntake
from dispatch.queue.app import create_app as create_queue_app
from dispatch.queue.store import QueueStore
from dispatch.reports.app import create_app as create_reports_app
from dispatch.reports.readonly import open_read_only
from dispatch.reports.snapshot import recent_reports

_PRIORITIES_IN_DISPLAY_ORDER = ("urgent", "today", "whenever")


def _list_folder(path) -> list[str]:
    return sorted(entry.name for entry in path.iterdir() if entry.is_file())


def _build_shell_app(config: dict[str, Any]) -> Flask:
    app = Flask(__name__)
    app.config["DISPATCH_CONFIG"] = config

    def get_queue() -> QueueStore:
        if "queue_store" not in g:
            g.queue_conn = bootstrap(config["database"])
            g.queue_store = QueueStore(g.queue_conn)
        return g.queue_store

    def get_pilot() -> PilotIntake:
        if "pilot" not in g:
            g.pilot = PilotIntake(config)
        return g.pilot

    def get_reports_ro():
        if "reports_ro_conn" not in g:
            g.reports_ro_conn = open_read_only(config["database"])
        return g.reports_ro_conn

    @app.teardown_appcontext
    def close_connections(exception=None):
        pilot = g.pop("pilot", None)
        if pilot is not None:
            pilot.close()
        queue_conn = g.pop("queue_conn", None)
        if queue_conn is not None:
            queue_conn.close()
        reports_ro_conn = g.pop("reports_ro_conn", None)
        if reports_ro_conn is not None:
            reports_ro_conn.close()

    @app.route("/")
    def dashboard():
        queue = get_queue()
        open_items = queue.list_all(status="open") + queue.list_all(status="in_review")
        priority_counts = {p: 0 for p in _PRIORITIES_IN_DISPLAY_ORDER}
        for item in open_items:
            priority_counts[item["priority"]] = priority_counts.get(item["priority"], 0) + 1

        pilot = get_pilot()
        inbox_count = len(_list_folder(pilot.inbox))
        folder_counts = {
            name: len(_list_folder(path))
            for name, path in pilot.folders.items()
            if name != "Inbox"
        }

        recents = recent_reports(get_reports_ro(), limit=3)

        return render_template(
            "dashboard.html",
            priorities=_PRIORITIES_IN_DISPLAY_ORDER,
            priority_counts=priority_counts,
            total_open=len(open_items),
            inbox_count=inbox_count,
            folder_counts=folder_counts,
            recents=recents,
        )

    @app.route("/pilot")
    def pilot_page():
        pilot = get_pilot()
        contents = {name: _list_folder(path) for name, path in pilot.folders.items()}
        return render_template("pilot.html", contents=contents, error=None, summary=None)

    @app.route("/pilot/process", methods=["POST"])
    def pilot_process():
        pilot = get_pilot()
        try:
            summary = pilot.process_inbox()
        except Exception as exc:  # noqa: BLE001 -- a write action must never 500 with no explanation
            contents = {name: _list_folder(path) for name, path in pilot.folders.items()}
            return render_template("pilot.html", contents=contents, error=str(exc), summary=None), 500

        contents = {name: _list_folder(path) for name, path in pilot.folders.items()}
        return render_template("pilot.html", contents=contents, error=None, summary=summary)

    return app


def create_app(config: dict[str, Any]) -> Flask:
    shell = _build_shell_app(config)
    queue_app = create_queue_app(config)
    reports_app = create_reports_app(config)
    ifta_app = create_ifta_app(config)

    shell.wsgi_app = DispatcherMiddleware(
        shell.wsgi_app,
        {
            "/queue": queue_app,
            "/reports": reports_app,
            "/ifta": ifta_app,
        },
    )
    return shell


if __name__ == "__main__":
    import sys

    from dispatch.common.config import load_config

    if len(sys.argv) != 2:
        print("usage: python -m dispatch.shell.app <config.json>")
        sys.exit(1)

    cfg = load_config(sys.argv[1])
    create_app(cfg).run(host="0.0.0.0", port=8483, debug=False)
