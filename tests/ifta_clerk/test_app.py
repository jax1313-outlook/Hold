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


# --- static boundary-refusal guards, same technique every lane uses ------


def test_ifta_clerk_source_never_issues_a_raw_sql_write():
    src_dir = Path(__file__).resolve().parents[2] / "src" / "dispatch" / "ifta_clerk"
    forbidden = ["INSERT INTO", "UPDATE ", "DELETE FROM"]
    for path in sorted(src_dir.rglob("*.py")):
        text = path.read_text(encoding="utf-8").upper()
        for snippet in forbidden:
            assert snippet not in text, f"{path} contains a raw SQL write: {snippet!r}"


def test_ifta_clerk_app_has_no_post_routes():
    """Every route is GET -- no write action exists anywhere in this app."""
    from dispatch.ifta_clerk.app import create_app

    app = create_app({"database": ":memory:", "roots": {"operations": ".", "library": ".", "archive": "."}})
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        assert "POST" not in rule.methods, f"{rule} allows POST -- ifta_clerk must be GET-only"


def test_ifta_clerk_app_module_never_imports_queue_or_package():
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
