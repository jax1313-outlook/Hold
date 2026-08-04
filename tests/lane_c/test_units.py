from dispatch.receipt.units import normalize_gallons


def test_gallons_pass_through_unchanged():
    assert normalize_gallons(100.0, "gallons") == 100.0


def test_liters_convert_to_gallons():
    assert abs(normalize_gallons(100.0, "liters") - 26.4172) < 1e-9


def test_none_volume_normalizes_to_zero():
    assert normalize_gallons(None, "gallons") == 0.0
