"""Date range presets — REPORTS_CHARTER_v1.md: exactly six, no Sort By,
no compound filtering ("every dropdown removed is a gift to the person
in the truck"). Resolving "Today" does read the clock, but only once,
here — everything downstream (queries, rendering) operates on the fixed
`(date_from, date_to)` pair this returns, which is what actually needs
to be deterministic for the "identical inputs -> identical bytes" test.
"""
from __future__ import annotations

from datetime import date, timedelta

PRESETS = ("today", "yesterday", "this_week", "this_month", "last_month", "custom")


class InvalidDateRangeError(ValueError):
    pass


def resolve_date_range(
    preset: str,
    *,
    today: date | None = None,
    custom_from: date | None = None,
    custom_to: date | None = None,
) -> tuple[date, date]:
    today = today or date.today()

    if preset == "today":
        return today, today
    if preset == "yesterday":
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday
    if preset == "this_week":
        start = today - timedelta(days=today.weekday())  # Monday
        return start, today
    if preset == "this_month":
        return today.replace(day=1), today
    if preset == "last_month":
        first_of_this_month = today.replace(day=1)
        last_day_of_last_month = first_of_this_month - timedelta(days=1)
        first_day_of_last_month = last_day_of_last_month.replace(day=1)
        return first_day_of_last_month, last_day_of_last_month
    if preset == "custom":
        if not custom_from or not custom_to:
            raise InvalidDateRangeError("custom range requires both custom_from and custom_to")
        if custom_from > custom_to:
            raise InvalidDateRangeError("custom_from must not be after custom_to")
        return custom_from, custom_to

    raise InvalidDateRangeError(f"unknown preset {preset!r}; must be one of {PRESETS}")


def quarter_label_for_date(d: date) -> str:
    """'2026-08-04' -> '2026-Q3'. Used to derive which IFTA quarter a
    selected date range falls in, so IFTA Position can share the same
    Date Range control as the other report types rather than needing its
    own quarter picker."""
    quarter_number = (d.month - 1) // 3 + 1
    return f"{d.year}-Q{quarter_number}"
