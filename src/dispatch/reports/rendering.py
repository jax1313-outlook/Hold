"""Deterministic HTML rendering, shared by the live UI and the immutable
snapshot writer. Same (template, data, as_of, period_label, filters) in
-> same bytes out, every time — REPORTS_CHARTER_v1.md's "identical inputs
must produce identical bytes, always," tested directly in
tests/lane_d/test_rendering.py.

All formatting happens in Python (`_build_view_model`), not inside the
Jinja templates — dynamic dict-key lookups driven by template JSON are
fragile and hard to reason about in Jinja syntax; building a plain view
model first keeps the .html files simple attribute/loop access only.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import jinja2

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=True,
    trim_blocks=True,
    lstrip_blocks=True,
)


def format_value(value: Any, fmt: str | None) -> str:
    if value is None:
        return "—"
    if fmt == "currency":
        return f"${value:,.2f}"
    if fmt == "number":
        return f"{value:,.1f}" if isinstance(value, float) else f"{value:,}"
    if fmt == "percent_delta":
        sign = "+" if value >= 0 else ""
        return f"{sign}{value:.1f}%"
    return str(value)


def build_view_model(template: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    view: dict[str, Any] = {
        "title": template["title"],
        "estimate_label": template.get("estimate_label"),
        "big_number": None,
        "secondary": None,
        "breakdown": None,
    }

    big = template.get("big_number")
    if big:
        view["big_number"] = {
            "label": big["label"],
            "value": format_value(data.get(big["field"]), big.get("format")),
        }

    secondary = template.get("secondary")
    if secondary:
        view["secondary"] = {
            "label": secondary["label"],
            "value": format_value(data.get(secondary["field"]), secondary.get("format")),
        }

    # breakdown is preferred; drilldown (e.g. Expense Summary's line items
    # once a category is chosen) is used only when breakdown has no rows.
    chosen = None
    breakdown_section = template.get("breakdown")
    if breakdown_section and data.get(breakdown_section["rows_field"]):
        chosen = breakdown_section
    drilldown_section = template.get("drilldown")
    if chosen is None and drilldown_section and data.get(drilldown_section["rows_field"]):
        chosen = drilldown_section

    if chosen:
        rows = data.get(chosen["rows_field"]) or []
        view["breakdown"] = {
            "label": chosen["label"],
            "headers": [col["label"] for col in chosen["columns"]],
            "rows": [
                [format_value(row.get(col["field"]), col.get("format")) for col in chosen["columns"]]
                for row in rows
            ],
        }

    return view


def render_answer_html(
    template: dict[str, Any],
    data: dict[str, Any],
    *,
    as_of: str,
    period_label: str,
    template_version: str,
    filters_desc: dict[str, str] | None = None,
    pending_review_count: int = 0,
    standalone: bool = False,
) -> str:
    view = build_view_model(template, data)
    jinja_template = _env.get_template("snapshot.html" if standalone else "answer_fragment.html")
    return jinja_template.render(
        view=view,
        as_of=as_of,
        period_label=period_label,
        template_version=template_version,
        filters_desc=filters_desc or {},
        pending_review_count=pending_review_count,
    )
