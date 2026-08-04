"""Golden regression + boundary refusal for the router. The most
safety-critical test file in this lane: reefer-flagged fuel and DEF must
never produce a FuelRecord, under any circumstance."""
from __future__ import annotations

import sqlite3

import pytest

from dispatch.receipt.router import (
    MissingUnitAttributionError,
    ReeferMisroutedError,
    Router,
    UnclassifiableCategoryError,
)


def test_propulsion_fuel_creates_both_records_cross_linked(router, db_conn, sample_fuel_line):
    result = router.route_line("ev_1", sample_fuel_line)

    fuel_row = db_conn.execute(
        "SELECT * FROM fuel_records WHERE fuel_record_id = ?", (result["fuel_record_id"],)
    ).fetchone()
    expense_row = db_conn.execute(
        "SELECT * FROM expense_records WHERE expense_record_id = ?", (result["expense_record_id"],)
    ).fetchone()

    assert fuel_row["expense_record_id"] == result["expense_record_id"]
    assert expense_row["fuel_record_id"] == result["fuel_record_id"]
    assert expense_row["category"] == "fuel"
    assert fuel_row["evidence_record_id"] == "ev_1"
    assert fuel_row["jurisdiction"] == "TX"
    assert fuel_row["gallons_normalized"] == 87.5


def test_reefer_fuel_creates_expense_record_only(router, db_conn, sample_reefer_fuel_line):
    result = router.route_line("ev_1", sample_reefer_fuel_line)

    assert "fuel_record_id" not in result
    row = db_conn.execute(
        "SELECT * FROM expense_records WHERE expense_record_id = ?", (result["expense_record_id"],)
    ).fetchone()
    assert row["category"] == "reefer_fuel"
    assert row["fuel_record_id"] is None

    count = db_conn.execute("SELECT COUNT(*) FROM fuel_records").fetchone()[0]
    assert count == 0  # never, under any circumstance


def test_def_creates_expense_record_only_never_fuel_record(router, db_conn, sample_def_line):
    result = router.route_line("ev_1", sample_def_line)

    assert "fuel_record_id" not in result
    row = db_conn.execute(
        "SELECT * FROM expense_records WHERE expense_record_id = ?", (result["expense_record_id"],)
    ).fetchone()
    assert row["category"] == "def"
    assert row["fuel_record_id"] is None

    count = db_conn.execute("SELECT COUNT(*) FROM fuel_records").fetchone()[0]
    assert count == 0


def test_meal_creates_expense_record_only(router, db_conn, sample_meal_line):
    result = router.route_line("ev_1", sample_meal_line)
    row = db_conn.execute(
        "SELECT * FROM expense_records WHERE expense_record_id = ?", (result["expense_record_id"],)
    ).fetchone()
    assert row["category"] == "meals"
    assert db_conn.execute("SELECT COUNT(*) FROM fuel_records").fetchone()[0] == 0


def test_unclassifiable_category_is_rejected(router, sample_fuel_line):
    line = dict(sample_fuel_line, category="not_a_real_category")
    with pytest.raises(UnclassifiableCategoryError):
        router.route_line("ev_1", line)


def test_fuel_line_without_unit_number_is_rejected(router, sample_fuel_line):
    line = dict(sample_fuel_line, unit_number=None)
    with pytest.raises(MissingUnitAttributionError):
        router.route_line("ev_1", line)


def test_reefer_flagged_line_miscategorized_as_fuel_is_refused(router, db_conn, sample_fuel_line):
    """The safety net: tractor_or_reefer == 'reefer' but category still
    says 'fuel' (an upstream classification bug) must never slip through."""
    line = dict(sample_fuel_line, tractor_or_reefer="reefer")
    with pytest.raises(ReeferMisroutedError):
        router.route_line("ev_1", line)

    assert db_conn.execute("SELECT COUNT(*) FROM fuel_records").fetchone()[0] == 0
    assert db_conn.execute("SELECT COUNT(*) FROM expense_records").fetchone()[0] == 0


def test_no_fuel_record_ever_has_tractor_or_reefer_reefer(
    router, db_conn, sample_fuel_line, sample_reefer_fuel_line, sample_def_line
):
    """Exhaustive sweep across every category this lane routes: after
    routing one of each, fuel_records must contain zero reefer rows."""
    router.route_line("ev_1", sample_fuel_line)
    try:
        router.route_line("ev_2", sample_reefer_fuel_line)
    except Exception:
        pass
    try:
        router.route_line("ev_3", sample_def_line)
    except Exception:
        pass

    reefer_fuel_rows = db_conn.execute(
        "SELECT COUNT(*) FROM fuel_records WHERE tractor_or_reefer = 'reefer'"
    ).fetchone()[0]
    assert reefer_fuel_rows == 0


def test_fuel_records_are_immutable(router, db_conn, sample_fuel_line):
    result = router.route_line("ev_1", sample_fuel_line)

    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            "UPDATE fuel_records SET vendor_name = 'tampered' WHERE fuel_record_id = ?",
            (result["fuel_record_id"],),
        )
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            "DELETE FROM fuel_records WHERE fuel_record_id = ?", (result["fuel_record_id"],)
        )


def test_expense_records_are_immutable(router, db_conn, sample_meal_line):
    result = router.route_line("ev_1", sample_meal_line)

    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            "UPDATE expense_records SET vendor_name = 'tampered' WHERE expense_record_id = ?",
            (result["expense_record_id"],),
        )
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            "DELETE FROM expense_records WHERE expense_record_id = ?",
            (result["expense_record_id"],),
        )
