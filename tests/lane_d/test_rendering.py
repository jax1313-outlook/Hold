"""render_answer_html determinism -- REPORTS_CHARTER_v1.md: "identical
inputs must produce identical bytes, always." One code path serves the
live fragment and the immutable snapshot, so both are exercised here."""
from __future__ import annotations

from dispatch.reports.rendering import build_view_model, format_value, render_answer_html

TEMPLATE = {
    "report_type": "fuel_spend",
    "version": "1",
    "title": "Fuel Spend",
    "big_number": {"field": "total_amount", "label": "Total Fuel Spend", "format": "currency"},
    "secondary": {"field": "total_gallons", "label": "Gallons", "format": "number"},
    "breakdown": {
        "label": "By State",
        "rows_field": "breakdown",
        "columns": [
            {"field": "jurisdiction", "label": "State"},
            {"field": "amount", "label": "Amount", "format": "currency"},
            {"field": "gallons", "label": "Gallons", "format": "number"},
        ],
    },
}

DATA = {
    "total_amount": 1234.567,
    "total_gallons": 320.75,
    "breakdown": [
        {"jurisdiction": "MO", "amount": 250.0, "gallons": 60.0},
        {"jurisdiction": "TX", "amount": 400.0, "gallons": 100.0},
    ],
}


def test_format_value_none_is_em_dash():
    assert format_value(None, "currency") == "—"


def test_format_value_currency():
    assert format_value(1234.5, "currency") == "$1,234.50"


def test_format_value_number_float():
    assert format_value(320.75, "number") == "320.8"


def test_format_value_number_int():
    assert format_value(4200, "number") == "4,200"


def test_format_value_percent_delta_positive_and_negative():
    assert format_value(3.2, "percent_delta") == "+3.2%"
    assert format_value(-1.5, "percent_delta") == "-1.5%"


def test_format_value_unknown_format_falls_back_to_str():
    assert format_value("fuel", None) == "fuel"


def test_build_view_model_prefers_breakdown_over_drilldown_when_both_have_rows():
    template = dict(TEMPLATE, drilldown={"label": "Lines", "rows_field": "line_items", "columns": []})
    data = dict(DATA, line_items=[{"a": 1}])
    view = build_view_model(template, data)
    assert view["breakdown"]["label"] == "By State"


def test_build_view_model_falls_back_to_drilldown_when_breakdown_empty():
    template = dict(TEMPLATE)
    template["drilldown"] = {
        "label": "Line items",
        "rows_field": "line_items",
        "columns": [{"field": "amount", "label": "Amount", "format": "currency"}],
    }
    data = dict(DATA, breakdown=[], line_items=[{"amount": 22.0}])
    view = build_view_model(template, data)
    assert view["breakdown"]["label"] == "Line items"
    assert view["breakdown"]["rows"] == [["$22.00"]]


def test_build_view_model_no_rows_at_all_yields_no_breakdown_section():
    data = dict(DATA, breakdown=[])
    view = build_view_model(TEMPLATE, data)
    assert view["breakdown"] is None


def test_render_answer_html_is_byte_identical_across_repeated_calls():
    kwargs = dict(
        as_of="2026-08-04T12:00:00Z",
        period_label="This Month",
        template_version="1",
        filters_desc={"State": "TX"},
        pending_review_count=2,
    )
    first = render_answer_html(TEMPLATE, DATA, **kwargs)
    second = render_answer_html(TEMPLATE, DATA, **kwargs)
    third = render_answer_html(TEMPLATE, DATA, standalone=True, **kwargs)
    fourth = render_answer_html(TEMPLATE, DATA, standalone=True, **kwargs)
    assert first == second
    assert third == fourth
    assert first != third  # fragment vs standalone snapshot are genuinely different documents


def test_render_answer_html_reflects_the_actual_data():
    html = render_answer_html(
        TEMPLATE, DATA, as_of="2026-08-04T12:00:00Z", period_label="This Month", template_version="1",
    )
    assert "$1,234.57" in html
    assert "320.8" in html
    assert "TX" in html and "MO" in html


def test_render_answer_html_estimate_label_only_shown_when_template_has_one():
    plain_html = render_answer_html(
        TEMPLATE, DATA, as_of="2026-08-04T12:00:00Z", period_label="This Month", template_version="1",
    )
    assert "estimate-label" not in plain_html

    estimate_template = dict(TEMPLATE, estimate_label="Prepared — estimate, not filed")
    estimate_html = render_answer_html(
        estimate_template, DATA, as_of="2026-08-04T12:00:00Z", period_label="This Month", template_version="1",
    )
    assert "estimate-label" in estimate_html
    assert "Prepared" in estimate_html


def test_snapshot_html_is_self_contained_with_no_external_asset_references():
    html = render_answer_html(
        TEMPLATE, DATA, as_of="2026-08-04T12:00:00Z", period_label="This Month",
        template_version="1", standalone=True,
    )
    assert "<style>" in html
    assert "url_for" not in html
    assert "/static/" not in html
    assert "immutable archive copy" in html
