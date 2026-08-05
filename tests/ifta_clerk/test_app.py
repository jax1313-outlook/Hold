"""dispatch.ifta_clerk.app -- routes, real data end to end, error
handling, and the same static/no-write-path guards every other lane's
tests already use."""
from __future__ import annotations

from pathlib import Path

import pytest

from dispatch.ifta import rates
from tests.ifta_clerk.conftest import insert_fuel_record, insert_mileage_record


def test_dashboard_reachable_on_a_genuinely_fresh_database(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"IFTA Clerk" in resp.data


def test_dashboard_defaults_to_the_current_quarter_when_none_given(client):
    resp = client.get("/")
    assert resp.status_code == 200
    # A well-formed quarter string appears in the quarter input's value.
    body = resp.data.decode()
    assert "-Q" in body


def test_dashboard_accepts_an_explicit_quarter_and_fuel_type(client):
    resp = client.get("/?quarter=2026-Q2&fuel_type=diesel")
    assert resp.status_code == 200
    assert b"2026-Q2" in resp.data


def test_dashboard_rejects_a_malformed_quarter_cleanly(client):
    resp = client.get("/?quarter=not-a-quarter&fuel_type=diesel")
    assert resp.status_code == 400
    assert b"IFTA Clerk" in resp.data  # renders the page, not a raw 500


def test_dashboard_shows_real_seeded_data_end_to_end(client, db_conn, sandbox_config):
    from dispatch.receipt.db import install_schema as install_receipt_schema

    install_receipt_schema(db_conn)
    insert_mileage_record(db_conn, unit_number="T-104", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1200.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=80.0)
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    db_conn.commit()

    resp = client.get("/?quarter=2026-Q2&fuel_type=diesel")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert "TX" in body
    assert "1200.0" in body
    assert "CURRENT ESTIMATE" in body


# --- Prepare This Quarter / Submit for Approval, real end to end --------


def test_prepare_route_builds_a_real_worksheet_and_redirects(client, db_conn, sandbox_config):
    from dispatch.receipt.db import install_schema as install_receipt_schema

    install_receipt_schema(db_conn)
    insert_mileage_record(db_conn, unit_number="T-104", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1200.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=80.0)
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    db_conn.commit()

    resp = client.post("/prepare", data={"quarter": "2026-Q2", "fuel_type": "diesel"})
    assert resp.status_code == 302
    assert "prepared=1" in resp.headers["Location"]

    follow = client.get(resp.headers["Location"])
    body = follow.data.decode()
    assert "Prepared: worksheet built" in body
    assert "DRAFT" in body  # the real worksheet's status, not the preview badge

    row = db_conn.execute("SELECT COUNT(*) FROM ifta_worksheets WHERE quarter = '2026-Q2'").fetchone()[0]
    assert row == 1


def test_prepare_route_never_submits_for_approval(client, db_conn, sandbox_config):
    from dispatch.receipt.db import install_schema as install_receipt_schema

    install_receipt_schema(db_conn)
    insert_mileage_record(db_conn, unit_number="T-104", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1200.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=80.0)
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    db_conn.commit()

    client.post("/prepare", data={"quarter": "2026-Q2", "fuel_type": "diesel"})

    approval_rows = db_conn.execute("SELECT COUNT(*) FROM queue_items WHERE type = 'approval'").fetchone()[0]
    assert approval_rows == 0

    follow = client.get("/?quarter=2026-Q2&fuel_type=diesel&prepared=1&exceptions=0")
    assert "Submit for Approval" in follow.data.decode()


def test_prepare_route_with_no_rate_shows_a_clean_error(client, db_conn, sandbox_config):
    from dispatch.receipt.db import install_schema as install_receipt_schema

    install_receipt_schema(db_conn)
    insert_mileage_record(db_conn, unit_number="T-104", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1200.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=80.0)
    db_conn.commit()

    resp = client.post("/prepare", data={"quarter": "2026-Q2", "fuel_type": "diesel"})
    assert resp.status_code == 400
    assert "Could not prepare this quarter" in resp.data.decode()


def test_submit_route_after_a_real_prepare(client, db_conn, sandbox_config):
    from dispatch.receipt.db import install_schema as install_receipt_schema

    install_receipt_schema(db_conn)
    insert_mileage_record(db_conn, unit_number="T-104", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1200.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=80.0)
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    db_conn.commit()

    client.post("/prepare", data={"quarter": "2026-Q2", "fuel_type": "diesel"})

    resp = client.post("/submit", data={"quarter": "2026-Q2", "fuel_type": "diesel"})
    assert resp.status_code == 302
    assert "submitted=1" in resp.headers["Location"]

    approval_rows = db_conn.execute("SELECT COUNT(*) FROM queue_items WHERE type = 'approval'").fetchone()[0]
    assert approval_rows == 1

    follow = client.get(resp.headers["Location"])
    assert "Submitted for approval" in follow.data.decode()
    assert "Already submitted for approval" in follow.data.decode()


def test_submit_route_without_a_prepare_shows_a_clean_error(client):
    resp = client.post("/submit", data={"quarter": "2026-Q2", "fuel_type": "diesel"})
    assert resp.status_code == 400
    assert "Could not submit for approval" in resp.data.decode()


def test_submit_route_twice_is_refused(client, db_conn, sandbox_config):
    from dispatch.receipt.db import install_schema as install_receipt_schema

    install_receipt_schema(db_conn)
    insert_mileage_record(db_conn, unit_number="T-104", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1200.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=80.0)
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    db_conn.commit()

    client.post("/prepare", data={"quarter": "2026-Q2", "fuel_type": "diesel"})
    client.post("/submit", data={"quarter": "2026-Q2", "fuel_type": "diesel"})

    resp = client.post("/submit", data={"quarter": "2026-Q2", "fuel_type": "diesel"})
    assert resp.status_code == 400
    assert "Could not submit for approval" in resp.data.decode()

    approval_rows = db_conn.execute("SELECT COUNT(*) FROM queue_items WHERE type = 'approval'").fetchone()[0]
    assert approval_rows == 1


# --- static boundary-refusal guards, same technique every lane uses ------


def test_ifta_clerk_source_never_issues_a_raw_sql_write():
    src_dir = Path(__file__).resolve().parents[2] / "src" / "dispatch" / "ifta_clerk"
    forbidden = ["INSERT INTO", "UPDATE ", "DELETE FROM"]
    for path in sorted(src_dir.rglob("*.py")):
        text = path.read_text(encoding="utf-8").upper()
        for snippet in forbidden:
            assert snippet not in text, f"{path} contains a raw SQL write: {snippet!r}"


def test_ifta_clerk_app_has_exactly_two_post_routes():
    """/prepare and /submit are the app's only write actions, added
    2026-08-04 -- everything else, including / itself, stays GET-only."""
    from dispatch.ifta_clerk.app import create_app

    app = create_app({"database": ":memory:", "roots": {"operations": ".", "library": ".", "archive": "."}})
    post_endpoints = {
        rule.endpoint for rule in app.url_map.iter_rules()
        if rule.endpoint != "static" and "POST" in rule.methods
    }
    assert post_endpoints == {"prepare", "submit"}, f"unexpected POST-capable routes: {post_endpoints}"

    dashboard_rule = next(r for r in app.url_map.iter_rules() if r.endpoint == "dashboard")
    assert "POST" not in dashboard_rule.methods


def test_ifta_clerk_app_module_never_imports_queue_or_package_directly():
    """app.py reaches submit_for_approval() only through prepare.py's
    narrower functions -- it never constructs a QueueStore or imports
    dispatch.ifta.package itself."""
    import ast
    import inspect

    import dispatch.ifta_clerk.app as app_module

    tree = ast.parse(inspect.getsource(app_module))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
    assert "QueueStore" not in imported
    assert "dispatch.ifta.package" not in imported


def test_ifta_clerk_package_never_imports_attempt_seal():
    """The one invariant that must survive Prepare This Quarter/Submit for
    Approval existing at all: sealing stays completely unreachable from
    this app, anywhere in the package, not just in app.py. ast-parsed
    imports, not raw text search -- app.py's own docstring explains this
    guarantee by name, which would trip a plain substring check."""
    import ast

    src_dir = Path(__file__).resolve().parents[2] / "src" / "dispatch" / "ifta_clerk"
    for path in sorted(src_dir.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
        assert "attempt_seal" not in imported, f"{path} imports attempt_seal -- sealing must stay unreachable from ifta_clerk"


def test_dashboard_module_still_never_imports_queue_or_evidence_spine():
    """dashboard.py -- the read-only assembly module -- must stay exactly
    as read-only as before; all new write capability lives in prepare.py
    only."""
    import ast
    import inspect

    import dispatch.ifta_clerk.dashboard as dashboard_module

    tree = ast.parse(inspect.getsource(dashboard_module))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
    assert "QueueStore" not in imported
    assert "EvidenceSpine" not in imported
    assert "dispatch.ifta.package" not in imported
