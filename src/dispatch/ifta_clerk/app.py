"""dispatch.ifta_clerk -- the Review Dashboard, the primary user
experience of the IFTA Clerk (IFTA_CLERK_BLUEPRINT_v1 section 7,
approved 2026-08-04).

Every route is GET. This app never imports QueueStore,
dispatch.ifta.package, or anything else with write/approval authority --
enforced by an ast-parsed import check in
tests/ifta_clerk/test_app.py, not just this docstring's promise.
flask.g per-request connection lifetime, the same pattern every other
app in this project already uses.

create_app() bootstraps the database file once at startup (same
precedent as dispatch.reports.app.create_app()) -- a genuinely fresh
install has no database file at all yet, and SQLite's mode=ro connection
fails outright to even open a file that doesn't exist, before any table
check can run. This is the one-time exception to "no write-capable
connection ever in scope": startup only, never per-request, and it only
ever creates the common tables (evidence_records, mileage_records,
queue_items, audit_log) bootstrap() already owns -- receipt/ifta schemas
stay this module's responsibility to read defensively (dashboard.py's
_table_exists() guards), not to install.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from flask import Flask, g, render_template, request

from dispatch.common.db import bootstrap
from dispatch.ifta.worksheet import InvalidQuarterError
from dispatch.ifta_clerk.dashboard import build_dashboard
from dispatch.ifta_clerk.readonly import open_read_only

DEFAULT_FUEL_TYPE = "diesel"


def _current_quarter() -> str:
    today = datetime.now(timezone.utc).date()
    q = (today.month - 1) // 3 + 1
    return f"{today.year}-Q{q}"


def create_app(config: dict[str, Any]) -> Flask:
    app = Flask(__name__)
    app.config["DISPATCH_CONFIG"] = config

    _startup_conn = bootstrap(config["database"])
    _startup_conn.close()

    def get_ro():
        if "ro_conn" not in g:
            g.ro_conn = open_read_only(config["database"])
        return g.ro_conn

    @app.teardown_appcontext
    def close_connections(exception=None):
        ro_conn = g.pop("ro_conn", None)
        if ro_conn is not None:
            ro_conn.close()

    @app.route("/")
    def dashboard():
        quarter = request.args.get("quarter") or _current_quarter()
        fuel_type = request.args.get("fuel_type") or DEFAULT_FUEL_TYPE

        try:
            data = build_dashboard(get_ro(), quarter=quarter, fuel_type=fuel_type)
        except InvalidQuarterError as exc:
            return render_template("dashboard.html", error=str(exc), quarter=quarter, fuel_type=fuel_type, data=None), 400

        return render_template("dashboard.html", error=None, quarter=quarter, fuel_type=fuel_type, data=data)

    return app


if __name__ == "__main__":
    import sys

    from dispatch.common.config import load_config

    if len(sys.argv) != 2:
        print("usage: python -m dispatch.ifta_clerk.app <config.json>")
        sys.exit(1)

    cfg = load_config(sys.argv[1])
    create_app(cfg).run(host="0.0.0.0", port=8486, debug=False)
