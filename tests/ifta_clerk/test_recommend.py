"""dispatch.ifta_clerk.recommend -- Recommended Payment Amount, the
first of three named Recommendation Package types
(IFTA_CLERK_BLUEPRINT_v1 section 13, Phase 6). Applies only after
sealing; writes exactly one JSON file to Archive and nothing else."""
from __future__ import annotations

import inspect
import json

import pytest

from dispatch.evidence.interface import EvidenceSpine
from dispatch.ifta import exceptions as ifta_exceptions
from dispatch.ifta import rates
from dispatch.ifta.package import attempt_seal, submit_for_approval
from dispatch.ifta.readonly import open_read_only as open_ifta_ro
from dispatch.ifta.worksheet import WorksheetEngine
from dispatch.ifta_clerk.recommend import (
    WorksheetNotFoundForRecommendationError,
    WorksheetNotSealedError,
    compute_payment_recommendation,
    existing_recommendation,
    generate_payment_recommendation,
)
from dispatch.queue.store import QueueStore
from tests.ifta_clerk.conftest import insert_fuel_record, insert_mileage_record


def _install_receipt_schema(conn):
    from dispatch.receipt.db import install_schema as install_receipt_schema

    install_receipt_schema(conn)


def _seal_a_real_worksheet(db_conn, sandbox_config, *, tx_miles=1000.0, tx_gallons=100.0, tx_rate=0.20):
    """Full real pipeline: build -> submit -> approve -> seal, exactly
    the way any real quarter reaches sealed. Returns the sealed
    worksheet dict."""
    _install_receipt_schema(db_conn)
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=tx_miles)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=tx_gallons)
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=tx_rate, source_version="fixture-v1")
    db_conn.commit()

    ro_conn = open_ifta_ro(sandbox_config["database"])
    try:
        engine = WorksheetEngine(db_conn, ro_conn)
        worksheet = engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")

        spine = EvidenceSpine(db_conn, sandbox_config["roots"])
        queue = QueueStore(db_conn)
        ifta_exceptions.run_all_detectors(db_conn, ro_conn, spine, queue, worksheet)

        queue_item = submit_for_approval(db_conn, queue, worksheet)
        queue.approve(queue_item["queue_item_id"], decided_by="human:mike", decision_note="test approval")
        sealed = attempt_seal(db_conn, queue, sandbox_config["roots"], worksheet["ifta_worksheet_id"])
    finally:
        ro_conn.close()

    return sealed


# --- compute_payment_recommendation(): pure, no fabrication --------------


def test_compute_recommends_remit_for_a_positive_net_tax():
    worksheet = {
        "ifta_worksheet_id": "wid1", "quarter": "2026-Q2", "fuel_type": "diesel",
        "total_net_tax": 42.50, "sealed_at": "2026-08-01T00:00:00Z",
    }
    result = compute_payment_recommendation(worksheet)
    assert result["recommendation"] == "remit"
    assert result["amount"] == 42.50
    assert result["status"] == "recommendation"


def test_compute_recommends_credit_for_a_negative_net_tax_never_a_negative_amount():
    worksheet = {
        "ifta_worksheet_id": "wid2", "quarter": "2026-Q2", "fuel_type": "diesel",
        "total_net_tax": -15.0, "sealed_at": "2026-08-01T00:00:00Z",
    }
    result = compute_payment_recommendation(worksheet)
    assert result["recommendation"] == "credit"
    assert result["amount"] == 15.0  # positive, not -15.0
    assert result["amount"] >= 0


def test_compute_recommends_no_payment_due_for_zero_net_tax():
    worksheet = {
        "ifta_worksheet_id": "wid3", "quarter": "2026-Q2", "fuel_type": "diesel",
        "total_net_tax": 0.0, "sealed_at": "2026-08-01T00:00:00Z",
    }
    result = compute_payment_recommendation(worksheet)
    assert result["recommendation"] == "no_payment_due"
    assert result["amount"] == 0.0


# --- generate_payment_recommendation(): the one real write action -------


def test_generate_refuses_for_a_draft_worksheet(db_conn, sandbox_config):
    _install_receipt_schema(db_conn)
    insert_mileage_record(db_conn, unit_number="T-100", jurisdiction="TX", period_start="2026-04-01", period_end="2026-06-30", miles=1000.0)
    insert_fuel_record(db_conn, jurisdiction="TX", purchase_date="2026-04-15", gallons_normalized=100.0)
    rates.insert_rate(db_conn, jurisdiction="TX", quarter="2026-Q2", fuel_type="diesel", rate=0.20, source_version="fixture-v1")
    db_conn.commit()

    ro_conn = open_ifta_ro(sandbox_config["database"])
    try:
        WorksheetEngine(db_conn, ro_conn).build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
        with pytest.raises(WorksheetNotSealedError):
            generate_payment_recommendation(ro_conn, sandbox_config["roots"], quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()


def test_generate_refuses_when_nothing_has_been_built(db_conn, sandbox_config):
    from dispatch.ifta.db import install_schema as install_ifta_schema

    install_ifta_schema(db_conn)
    ro_conn = open_ifta_ro(sandbox_config["database"])
    try:
        with pytest.raises(WorksheetNotFoundForRecommendationError):
            generate_payment_recommendation(ro_conn, sandbox_config["roots"], quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()


def test_generate_writes_exactly_one_file_and_returns_it(db_conn, sandbox_config):
    sealed = _seal_a_real_worksheet(db_conn, sandbox_config, tx_miles=1000.0, tx_gallons=100.0, tx_rate=0.20)

    ro_conn = open_ifta_ro(sandbox_config["database"])
    try:
        result = generate_payment_recommendation(ro_conn, sandbox_config["roots"], quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()

    assert result["ifta_worksheet_id"] == sealed["ifta_worksheet_id"]
    assert result["total_net_tax"] == sealed["total_net_tax"]

    from pathlib import Path

    expected_path = Path(sandbox_config["roots"]["archive"]) / "IFTA" / "2026-Q2" / f"{sealed['ifta_worksheet_id']}_payment_recommendation.json"
    assert expected_path.is_file()
    on_disk = json.loads(expected_path.read_text(encoding="utf-8"))
    assert on_disk == result


def test_generate_is_idempotent_never_writes_a_second_file(db_conn, sandbox_config):
    _seal_a_real_worksheet(db_conn, sandbox_config, tx_miles=1000.0, tx_gallons=100.0, tx_rate=0.20)

    ro_conn = open_ifta_ro(sandbox_config["database"])
    try:
        first = generate_payment_recommendation(ro_conn, sandbox_config["roots"], quarter="2026-Q2", fuel_type="diesel")
        second = generate_payment_recommendation(ro_conn, sandbox_config["roots"], quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()

    assert first == second
    assert first["generated_at"] == second["generated_at"]  # not regenerated


def test_existing_recommendation_is_none_before_generation(db_conn, sandbox_config):
    sealed = _seal_a_real_worksheet(db_conn, sandbox_config)
    assert existing_recommendation(sandbox_config["roots"], "2026-Q2", sealed["ifta_worksheet_id"]) is None


def test_existing_recommendation_reads_back_after_generation(db_conn, sandbox_config):
    sealed = _seal_a_real_worksheet(db_conn, sandbox_config)

    ro_conn = open_ifta_ro(sandbox_config["database"])
    try:
        generated = generate_payment_recommendation(ro_conn, sandbox_config["roots"], quarter="2026-Q2", fuel_type="diesel")
    finally:
        ro_conn.close()

    found = existing_recommendation(sandbox_config["roots"], "2026-Q2", sealed["ifta_worksheet_id"])
    assert found == generated


# --- the boundary itself, proven structurally, not just asserted --------


def test_generate_payment_recommendation_takes_only_a_read_only_connection():
    sig = inspect.signature(generate_payment_recommendation)
    params = list(sig.parameters)
    assert params[0] == "read_only_conn"
    assert "write" not in params
    assert "conn" not in params[1:]


def test_recommend_module_never_imports_anything_with_send_capability():
    """No requests/smtplib/urllib/http.client -- and no
    QueueStore/EvidenceSpine/dispatch.ifta.package -- anywhere in this
    module. Generating a recommendation writes a file; it cannot send,
    approve, or seal anything."""
    import ast

    import dispatch.ifta_clerk.recommend as recommend_module

    tree = ast.parse(inspect.getsource(recommend_module))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)

    forbidden = {"requests", "smtplib", "urllib", "http.client", "QueueStore", "EvidenceSpine", "attempt_seal", "submit_for_approval"}
    overlap = forbidden & imported
    assert not overlap, f"recommend.py imports something with send/approval capability: {overlap}"
    assert "dispatch.ifta.package" not in imported


def test_recommend_module_never_issues_a_raw_sql_write():
    import dispatch.ifta_clerk.recommend as recommend_module

    source = inspect.getsource(recommend_module)
    forbidden = ["INSERT INTO", "UPDATE ", "DELETE FROM"]
    for snippet in forbidden:
        assert snippet not in source, f"recommend.py contains a raw SQL write: {snippet!r}"


def test_compute_payment_recommendation_does_no_file_io():
    """Pure function -- json/Path never appear inside its own body."""
    source = inspect.getsource(compute_payment_recommendation)
    assert "open(" not in source
    assert "write_text" not in source
    assert "Path(" not in source
