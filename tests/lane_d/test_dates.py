"""Date range preset resolution -- REPORTS_CHARTER_v1.md: exactly six
presets, no compound filtering. today= is always pinned in these tests so
the assertions never depend on the wall clock."""
from __future__ import annotations

from datetime import date

import pytest

from dispatch.reports.dates import (
    InvalidDateRangeError,
    PRESETS,
    quarter_label_for_date,
    resolve_date_range,
)

FIXED_TODAY = date(2026, 8, 4)  # a Tuesday


def test_presets_tuple_is_exactly_six():
    assert PRESETS == ("today", "yesterday", "this_week", "this_month", "last_month", "custom")


def test_today():
    assert resolve_date_range("today", today=FIXED_TODAY) == (FIXED_TODAY, FIXED_TODAY)


def test_yesterday():
    assert resolve_date_range("yesterday", today=FIXED_TODAY) == (date(2026, 8, 3), date(2026, 8, 3))


def test_this_week_starts_monday():
    start, end = resolve_date_range("this_week", today=FIXED_TODAY)
    assert start == date(2026, 8, 3)  # Monday of that week
    assert end == FIXED_TODAY


def test_this_month():
    start, end = resolve_date_range("this_month", today=FIXED_TODAY)
    assert start == date(2026, 8, 1)
    assert end == FIXED_TODAY


def test_last_month():
    start, end = resolve_date_range("last_month", today=FIXED_TODAY)
    assert start == date(2026, 7, 1)
    assert end == date(2026, 7, 31)


def test_last_month_crosses_year_boundary():
    start, end = resolve_date_range("last_month", today=date(2026, 1, 15))
    assert start == date(2025, 12, 1)
    assert end == date(2025, 12, 31)


def test_custom_requires_both_bounds():
    with pytest.raises(InvalidDateRangeError):
        resolve_date_range("custom", today=FIXED_TODAY, custom_from=date(2026, 8, 1))
    with pytest.raises(InvalidDateRangeError):
        resolve_date_range("custom", today=FIXED_TODAY, custom_to=date(2026, 8, 1))


def test_custom_rejects_inverted_range():
    with pytest.raises(InvalidDateRangeError):
        resolve_date_range(
            "custom", today=FIXED_TODAY, custom_from=date(2026, 8, 10), custom_to=date(2026, 8, 1)
        )


def test_custom_accepts_valid_range():
    result = resolve_date_range(
        "custom", today=FIXED_TODAY, custom_from=date(2026, 6, 1), custom_to=date(2026, 6, 30)
    )
    assert result == (date(2026, 6, 1), date(2026, 6, 30))


def test_unknown_preset_raises():
    with pytest.raises(InvalidDateRangeError):
        resolve_date_range("this_decade", today=FIXED_TODAY)


@pytest.mark.parametrize(
    "d, expected",
    [
        (date(2026, 1, 1), "2026-Q1"),
        (date(2026, 3, 31), "2026-Q1"),
        (date(2026, 4, 1), "2026-Q2"),
        (date(2026, 8, 4), "2026-Q3"),
        (date(2026, 10, 1), "2026-Q4"),
        (date(2026, 12, 31), "2026-Q4"),
    ],
)
def test_quarter_label_for_date(d, expected):
    assert quarter_label_for_date(d) == expected
