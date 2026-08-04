from dispatch.receipt import validators


def test_structural_check_passes_complete_line(sample_fuel_line):
    assert validators.structural_check(sample_fuel_line) is None


def test_structural_check_flags_missing_field(sample_fuel_line):
    line = dict(sample_fuel_line)
    del line["amount"]
    assert "amount" in validators.structural_check(line)


def test_sum_matches_within_tolerance():
    lines = [{"amount": 10.0, "tax_amount": 0.5}, {"amount": 20.0, "tax_amount": None}]
    assert validators.sum_matches(lines, 30.50)
    assert validators.sum_matches(lines, 30.505)  # within default tolerance


def test_sum_matches_flags_real_mismatch():
    lines = [{"amount": 10.0, "tax_amount": 0.0}]
    assert not validators.sum_matches(lines, 999.0)


def test_sum_matches_skips_check_when_no_total_known():
    assert validators.sum_matches([{"amount": 1.0, "tax_amount": None}], None)


def test_validate_document_accepts_clean_lines(db_conn, sample_fuel_line, sample_meal_line):
    from dispatch.receipt.db import install_schema

    install_schema(db_conn)
    result = validators.validate_document(
        db_conn, [sample_fuel_line, sample_meal_line], document_total=None
    )
    assert len(result.accepted) == 2
    assert result.quarantined == []


def test_validate_document_quarantines_structurally_bad_line_only(
    db_conn, sample_fuel_line, sample_meal_line
):
    from dispatch.receipt.db import install_schema

    install_schema(db_conn)
    bad_line = dict(sample_meal_line)
    del bad_line["amount"]

    result = validators.validate_document(db_conn, [sample_fuel_line, bad_line], document_total=None)
    assert len(result.accepted) == 1
    assert len(result.quarantined) == 1
    assert result.quarantined[0].reason == "structural"


def test_validate_document_sum_mismatch_quarantines_whole_document(
    db_conn, sample_fuel_line, sample_meal_line
):
    from dispatch.receipt.db import install_schema

    install_schema(db_conn)
    result = validators.validate_document(
        db_conn, [sample_fuel_line, sample_meal_line], document_total=999999.0
    )
    assert result.accepted == []
    assert len(result.quarantined) == 2
    assert all(q.reason == "sum_mismatch" for q in result.quarantined)


def test_validate_document_low_confidence_is_line_level(db_conn, sample_fuel_line, sample_meal_line):
    from dispatch.receipt.db import install_schema

    install_schema(db_conn)
    low_conf = dict(sample_fuel_line, extraction_confidence=0.2)

    result = validators.validate_document(db_conn, [low_conf, sample_meal_line], document_total=None)
    assert len(result.accepted) == 1
    assert result.accepted[0]["vendor_name"] == sample_meal_line["vendor_name"]
    assert len(result.quarantined) == 1
    assert result.quarantined[0].reason == "low_confidence"


def test_validate_document_flags_duplicate_against_existing_record(
    db_conn, router, sample_fuel_line
):
    router.route_line("ev_1", sample_fuel_line)  # creates the first record

    result = validators.validate_document(db_conn, [dict(sample_fuel_line)], document_total=None)
    assert result.accepted == []
    assert len(result.quarantined) == 1
    assert result.quarantined[0].reason == "duplicate_transaction"


def test_dedup_key_computed_by_validators_matches_what_router_actually_stores(
    db_conn, router, sample_fuel_line
):
    key_before_routing = validators.line_dedup_key(sample_fuel_line)
    result = router.route_line("ev_1", sample_fuel_line)

    row = db_conn.execute(
        "SELECT dedup_key FROM fuel_records WHERE fuel_record_id = ?", (result["fuel_record_id"],)
    ).fetchone()
    assert row["dedup_key"] == key_before_routing
