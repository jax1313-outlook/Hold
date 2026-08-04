"""Flask route tests for dispatch.reports.app -- exercises the actual
create_app() the same way the real dev server would (Lane B's real
threading bug was only caught by running the actual server, not by unit
tests against the store directly, so these use Flask's test client
against the real app rather than calling view functions in isolation)."""
from __future__ import annotations

import pytest

from dispatch.reports.app import create_app


@pytest.fixture
def client(seeded_library, seeded_pipeline_data):
    app = create_app(seeded_library)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_index_does_not_crash_on_a_brand_new_database_with_nothing_saved(seeded_library):
    # Regression test: print_queue is created lazily by ReportSnapshotWriter,
    # but "/" reads it via recent_reports() on the read-only connection
    # before any save has necessarily happened. create_app() must install
    # the schema itself at startup so this doesn't 500 on a fresh install.
    app = create_app(seeded_library)
    with app.test_client() as c:
        resp = c.get("/")
    assert resp.status_code == 200


def test_index_lists_report_types(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Fuel" in body and "Expenses" in body and "IFTA" in body


_FULL_AUGUST = {"date_range": "custom", "custom_from": "2026-08-01", "custom_to": "2026-08-31"}


def test_run_fuel_spend_shows_the_answer(client):
    resp = client.get("/run", query_string={"report_type": "fuel_spend", **_FULL_AUGUST})
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Total Fuel Spend" in body
    assert "$650.00" in body


def test_run_expense_summary_shows_the_answer(client):
    resp = client.get("/run", query_string={"report_type": "expense_summary", **_FULL_AUGUST})
    assert resp.status_code == 200
    assert "Total Expenses" in resp.get_data(as_text=True)


def test_run_unknown_report_type_is_400(client):
    resp = client.get("/run", query_string={"report_type": "profit_and_loss"})
    assert resp.status_code == 400


def test_run_invalid_custom_range_is_400(client):
    resp = client.get(
        "/run",
        query_string={"report_type": "fuel_spend", "date_range": "custom", "custom_from": "2026-08-10", "custom_to": "2026-08-01"},
    )
    assert resp.status_code == 400


def test_save_then_print_queue_lists_it_and_actions_work(client):
    resp = client.post("/save", data={"report_type": "fuel_spend", "date_range": "this_month"})
    assert resp.status_code in (302, 303)

    queue_resp = client.get("/print-queue")
    assert queue_resp.status_code == 200
    body = queue_resp.get_data(as_text=True)
    assert "Fuel" in body
    assert "Mark printed" in body

    import re

    match = re.search(r"print-queue/([^/]+)/view", body)
    assert match is not None
    print_queue_id = match.group(1)

    view_resp = client.get(f"/print-queue/{print_queue_id}/view")
    assert view_resp.status_code == 200
    assert "immutable archive copy" in view_resp.get_data(as_text=True)

    mark_resp = client.post(f"/print-queue/{print_queue_id}/mark-printed")
    assert mark_resp.status_code in (302, 303)

    clear_resp = client.post(f"/print-queue/{print_queue_id}/clear")
    assert clear_resp.status_code in (302, 303)

    # Only one item was ever saved in this test, and it's now cleared --
    # the template hides the action buttons for a cleared item, and never
    # offers a delete affordance at all.
    final_body = client.get("/print-queue").get_data(as_text=True)
    assert "status-cleared" in final_body
    assert "Mark printed" not in final_body
    assert "Clear" not in final_body


def test_actions_on_unknown_print_queue_id_are_404(client):
    assert client.post("/print-queue/does-not-exist/mark-printed").status_code == 404
    assert client.post("/print-queue/does-not-exist/clear").status_code == 404
    assert client.get("/print-queue/does-not-exist/view").status_code == 404


def test_index_shows_recent_chip_after_a_save(client):
    client.post("/save", data={"report_type": "fuel_spend", "date_range": "this_month"})
    body = client.get("/").get_data(as_text=True)
    assert "This Month" in body
