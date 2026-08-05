"""dispatch.shell -- mounted-app routing, real dashboard state, the
Process Inbox button end to end, and the same static/no-write-path
guards every other lane's tests already use."""
from __future__ import annotations

from pathlib import Path

import pytest

from dispatch.pilot.intake import PilotIntake
from dispatch.queue.store import QueueStore
from dispatch.reports.snapshot import ReportSnapshotWriter


# --- mounting: the one real technical risk this package carries --------


def test_queue_is_mounted_and_reachable(client):
    resp = client.get("/queue/")
    assert resp.status_code == 200
    assert b"Dispatch Queue" in resp.data


def test_reports_is_mounted_and_reachable(client):
    resp = client.get("/reports/")
    assert resp.status_code == 200


def test_queue_static_asset_resolves_under_the_mount_prefix(client):
    resp = client.get("/queue/static/style.css")
    assert resp.status_code == 200
    assert b"font-family" in resp.data


def test_reports_static_asset_resolves_under_the_mount_prefix(client):
    resp = client.get("/reports/static/style.css")
    assert resp.status_code == 200
    assert b"font-family" in resp.data


def test_ifta_clerk_is_mounted_and_reachable(client):
    resp = client.get("/ifta-clerk/")
    assert resp.status_code == 200
    assert b"IFTA Clerk" in resp.data


def test_ifta_clerk_static_asset_resolves_under_the_mount_prefix(client):
    resp = client.get("/ifta-clerk/static/style.css")
    assert resp.status_code == 200
    assert b"font-family" in resp.data


def test_ifta_clerk_internal_link_generated_by_its_own_template_is_correctly_prefixed(client):
    """Same url_for/SCRIPT_NAME risk as Queue's and Reports' own mounts:
    the dashboard's own quarter-switcher form posts back to its own
    index route via url_for('dashboard') -- must resolve under
    /ifta-clerk, not the bare root."""
    resp = client.get("/ifta-clerk/")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert 'action="/ifta-clerk/"' in body, "IFTA Clerk's own template did not generate a /ifta-clerk/-prefixed form action"


def test_queue_internal_link_generated_by_its_own_template_is_correctly_prefixed(client, sandbox_config, db_conn):
    """The actual url_for/SCRIPT_NAME risk: a link Queue's own index.html
    generates via url_for('item_detail', ...) must resolve to
    /queue/items/<id>, not /items/<id> -- and following it must actually
    work, not just look right."""
    queue = QueueStore(db_conn)
    item = queue.create(
        type="review", source_worker="test", priority="today", subject="mounted link test",
    )

    resp = client.get("/queue/")
    assert resp.status_code == 200
    body = resp.data.decode()
    expected_link = f"/queue/items/{item['queue_item_id']}"
    assert expected_link in body, "Queue's own template did not generate a /queue/-prefixed link"

    detail_resp = client.get(expected_link)
    assert detail_resp.status_code == 200
    assert item["subject"].encode() in detail_resp.data


# --- dashboard reflects real state, not a mock ---------------------------


def test_dashboard_links_to_ifta_clerk_prominently(client):
    """IFTA Clerk is the primary user experience (IFTA_CLERK_BLUEPRINT_v1
    section 7) -- its card renders first among the summary cards, styled
    distinctly (card-primary), not just present somewhere on the page."""
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert "card-primary" in body
    assert '/ifta-clerk/' in body
    # Compare card order specifically (not the nav bar, which also links
    # to /queue/ and appears earlier in the document regardless).
    assert body.index("card-primary") < body.index('class="card" href="/queue/"')


def test_dashboard_shows_real_queue_counts_by_priority(client, db_conn):
    queue = QueueStore(db_conn)
    queue.create(type="review", source_worker="test", priority="urgent", subject="urgent one")
    queue.create(type="review", source_worker="test", priority="today", subject="today one")
    queue.create(type="review", source_worker="test", priority="today", subject="today two")
    queue.create(type="review", source_worker="test", priority="whenever", subject="whenever one")

    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert "4" in body  # total_open
    assert "priority-urgent" in body
    assert "priority-today" in body


def test_dashboard_shows_real_pilot_inbox_and_folder_state(client, sandbox_config):
    pilot = PilotIntake(sandbox_config)
    (pilot.inbox / "fuel.csv").write_text("dummy")
    (pilot.inbox / "receipt.csv").write_text("dummy")
    pilot.close()

    resp = client.get("/")
    body = resp.data.decode()
    assert "2" in body  # inbox_count


def test_dashboard_shows_real_recent_reports(client, sandbox_config, db_conn):
    writer = ReportSnapshotWriter(db_conn, sandbox_config["roots"]["archive"])
    template = {"report_type": "fuel_spend", "version": "1", "title": "Fuel Spend",
                "big_number": {"field": "total_amount", "label": "Total", "format": "currency"}}
    writer.save_snapshot(
        report_type="fuel_spend", template=template, template_version="1",
        data={"total_amount": 100.0}, period_label="This Month",
    )

    resp = client.get("/")
    body = resp.data.decode()
    assert "Fuel Spend" in body
    assert "This Month" in body


def test_dashboard_with_nothing_seeded_does_not_crash(client):
    resp = client.get("/")
    assert resp.status_code == 200


# --- Pilot page + Process Inbox button, real end to end ------------------


def test_pilot_page_shows_folder_contents(client, sandbox_config):
    pilot = PilotIntake(sandbox_config)
    (pilot.inbox / "notes.docx").write_text("dummy")
    pilot.close()

    resp = client.get("/pilot")
    assert resp.status_code == 200
    assert "notes.docx" in resp.data.decode()


def test_process_inbox_button_runs_the_real_pipeline(client, sandbox_config, db_conn):
    pilot = PilotIntake(sandbox_config)
    (pilot.inbox / "ratecon_test.pdf").write_text("dummy")
    pilot.close()

    resp = client.post("/pilot/process")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert "ratecon_test.pdf" in body
    assert "RateCons" in body

    # Real, governed evidence -- not just a page saying so.
    row = db_conn.execute(
        "SELECT document_type FROM evidence_records WHERE document_type = 'rate_confirmation'"
    ).fetchone()
    assert row is not None

    # The file actually moved out of Inbox into RateCons.
    assert not (pilot.folders["Inbox"] / "ratecon_test.pdf").exists()
    assert (pilot.folders["RateCons"] / "ratecon_test.pdf").exists()


def test_process_inbox_on_empty_inbox_shows_nothing_to_process(client):
    resp = client.post("/pilot/process")
    assert resp.status_code == 200
    assert "nothing to process" in resp.data.decode().lower()


def test_process_inbox_failure_renders_a_clear_error_not_a_raw_crash(client, monkeypatch):
    def _raise(self):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(PilotIntake, "process_inbox", _raise)

    resp = client.post("/pilot/process")
    assert resp.status_code == 500
    assert "simulated failure" in resp.data.decode()


# --- static boundary-refusal guards, same technique every lane uses ------


def test_shell_source_never_issues_a_raw_sql_write():
    shell_src = Path(__file__).resolve().parents[2] / "src" / "dispatch" / "shell"
    forbidden = ["INSERT INTO", "UPDATE ", "DELETE FROM"]
    for path in sorted(shell_src.rglob("*.py")):
        text = path.read_text(encoding="utf-8").upper()
        for snippet in forbidden:
            assert snippet not in text, f"{path} contains a raw SQL write: {snippet!r}"


def test_shell_imports_only_create_app_from_the_three_mounted_apps():
    """From dispatch.queue.app, dispatch.reports.app, and
    dispatch.ifta_clerk.app specifically -- their own Flask modules --
    the shell imports exactly one name: create_app. Everything else it
    uses (QueueStore, the reports read functions) comes from those
    lanes' own separate, legitimate public modules (store.py,
    snapshot.py, queries.py, readonly.py), not from reaching into the
    .app module's internals."""
    import ast

    app_py = Path(__file__).resolve().parents[2] / "src" / "dispatch" / "shell" / "app.py"
    tree = ast.parse(app_py.read_text(encoding="utf-8"))

    mounted_app_modules = ("dispatch.queue.app", "dispatch.reports.app", "dispatch.ifta_clerk.app")
    seen_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in mounted_app_modules:
            seen_modules.add(node.module)
            imported_names = {alias.name for alias in node.names}
            assert imported_names == {"create_app"}, (
                f"{node.module} import pulls in more than create_app: {imported_names}"
            )
    assert seen_modules == set(mounted_app_modules), f"expected imports from all three, got {seen_modules}"
