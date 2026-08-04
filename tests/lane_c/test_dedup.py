from dispatch.receipt import dedup


def test_fuel_dedup_key_is_deterministic():
    kwargs = dict(
        vendor_name="Flying J", purchase_date="2026-07-15",
        total_amount=350.0, gallons_normalized=87.5, card_last4="4321",
    )
    assert dedup.fuel_dedup_key(**kwargs) == dedup.fuel_dedup_key(**kwargs)


def test_fuel_dedup_key_changes_with_any_input():
    base = dict(
        vendor_name="Flying J", purchase_date="2026-07-15",
        total_amount=350.0, gallons_normalized=87.5, card_last4="4321",
    )
    key = dedup.fuel_dedup_key(**base)
    changed = dict(base, total_amount=350.01)
    assert dedup.fuel_dedup_key(**changed) != key


def test_expense_dedup_key_is_deterministic():
    kwargs = dict(
        vendor_name="Truck Stop Diner", purchase_date="2026-07-15",
        amount=18.50, line_description="Dinner",
    )
    assert dedup.expense_dedup_key(**kwargs) == dedup.expense_dedup_key(**kwargs)


def test_find_by_dedup_key_returns_none_when_absent(db_conn):
    from dispatch.receipt.db import install_schema

    install_schema(db_conn)
    assert dedup.find_fuel_record_by_dedup_key(db_conn, "nonexistent") is None
    assert dedup.find_expense_record_by_dedup_key(db_conn, "nonexistent") is None
