"""Flask queue UI — the human interface to the queue store.

Server-rendered HTML, no JS framework, per DISPATCH_BUILD_BLUEPRINT_v1
Part 3.1's stack rationale: big numbers, big touch targets, tablet-
friendly. Every mutating action is a real HTTP POST tied to an explicit
`decided_by` field a human typed — there is no route, no query
parameter, and no background task anywhere in this module that
transitions an item on its own.

Connection lifetime: sqlite3 connections are thread-local, and Flask's
request-handling threads are not guaranteed to be the thread create_app()
ran on (confirmed directly: the real dev server raised
"SQLite objects created in a thread can only be used in that same thread"
on the very first request during manual testing, even though every
automated test using Flask's synchronous test client passed — the test
client never actually changes threads, so it couldn't have caught this).
Each request therefore opens its own connection via flask.g, closed in
teardown_appcontext, rather than sharing one connection built at app-
creation time across every request.
"""
from __future__ import annotations

from flask import Flask, abort, g, redirect, render_template, request, url_for

from dispatch.common.db import bootstrap
from dispatch.evidence.interface import (
    EvidenceIntegrityError,
    EvidenceNotFoundError,
    EvidenceSpine,
)
from dispatch.queue.store import InvalidTransitionError, QueueItemNotFoundError, QueueStore

_PRIORITIES_IN_DISPLAY_ORDER = ("urgent", "today", "whenever")


def _evidence_previews(spine: EvidenceSpine, payload_refs: list[str]) -> list[dict]:
    """Best-effort evidence preview for each payload ref. payload_refs is
    generic ("record/evidence ids" per contract 1.3) — a ref that isn't an
    evidence record, or one whose archive failed its hash check, must show
    a clear message, never an unhandled exception on this page (launch
    package risk #4)."""
    previews = []
    for ref in payload_refs:
        try:
            record, _path = spine.retrieve(ref)
            previews.append({"ref": ref, "status": "ok", "record": record})
        except EvidenceNotFoundError:
            previews.append({"ref": ref, "status": "not_evidence", "record": None})
        except EvidenceIntegrityError:
            previews.append({"ref": ref, "status": "integrity_failed", "record": None})
    return previews


def create_app(config: dict) -> Flask:
    app = Flask(__name__)
    app.config["DISPATCH_CONFIG"] = config

    def get_db():
        if "db_conn" not in g:
            g.db_conn = bootstrap(config["database"])
        return g.db_conn

    def get_store() -> QueueStore:
        if "queue_store" not in g:
            g.queue_store = QueueStore(get_db())
        return g.queue_store

    def get_spine() -> EvidenceSpine:
        if "evidence_spine" not in g:
            g.evidence_spine = EvidenceSpine(get_db(), config["roots"])
        return g.evidence_spine

    @app.teardown_appcontext
    def close_db(exception=None):
        conn = g.pop("db_conn", None)
        if conn is not None:
            conn.close()

    @app.route("/")
    def index():
        status_filter = request.args.get("status") or None
        items = get_store().list_all(status=status_filter)
        grouped = {priority: [] for priority in _PRIORITIES_IN_DISPLAY_ORDER}
        for item in items:
            grouped[item["priority"]].append(item)
        return render_template(
            "index.html",
            grouped=grouped,
            priorities=_PRIORITIES_IN_DISPLAY_ORDER,
            status_filter=status_filter,
        )

    @app.route("/items/<queue_item_id>")
    def item_detail(queue_item_id):
        try:
            item = get_store().get(queue_item_id)
        except QueueItemNotFoundError:
            abort(404)
        previews = _evidence_previews(get_spine(), item["payload_refs"])
        return render_template("detail.html", item=item, previews=previews)

    @app.route("/items/<queue_item_id>/start_review", methods=["POST"])
    def start_review(queue_item_id):
        try:
            get_store().start_review(queue_item_id)
        except (QueueItemNotFoundError, InvalidTransitionError) as exc:
            abort(400, description=str(exc))
        return redirect(url_for("item_detail", queue_item_id=queue_item_id))

    def _decide(queue_item_id: str, method_name: str):
        decided_by = request.form.get("decided_by", "").strip()
        decision_note = request.form.get("decision_note", "").strip() or None
        if not decided_by:
            abort(400, description="decided_by is required")
        method = getattr(get_store(), method_name)
        try:
            method(queue_item_id, decided_by=decided_by, decision_note=decision_note)
        except (QueueItemNotFoundError, InvalidTransitionError) as exc:
            abort(400, description=str(exc))
        return redirect(url_for("item_detail", queue_item_id=queue_item_id))

    @app.route("/items/<queue_item_id>/approve", methods=["POST"])
    def approve(queue_item_id):
        return _decide(queue_item_id, "approve")

    @app.route("/items/<queue_item_id>/reject", methods=["POST"])
    def reject(queue_item_id):
        return _decide(queue_item_id, "reject")

    @app.route("/items/<queue_item_id>/resolve", methods=["POST"])
    def resolve(queue_item_id):
        return _decide(queue_item_id, "resolve")

    return app


if __name__ == "__main__":
    import sys

    from dispatch.common.config import load_config

    if len(sys.argv) != 2:
        print("usage: python -m dispatch.queue.app <config.json>")
        sys.exit(1)

    cfg = load_config(sys.argv[1])
    create_app(cfg).run(host="0.0.0.0", port=8484, debug=False)
