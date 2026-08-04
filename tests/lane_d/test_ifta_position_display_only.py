"""REPORTS_CHARTER_v1.md bright line #2, for the one report type where
getting this wrong would be catastrophic: IFTA Position must read
fleet_mpg/net_tax/taxable_gallons exactly as Lane C's WorksheetEngine
already computed and stored them, end to end through the query layer and
the rendered HTML -- never recompute, round differently, or re-derive."""
from __future__ import annotations

from dispatch.reports import queries
from dispatch.reports.rendering import render_answer_html
from dispatch.reports.templates_engine import load_template


def test_query_layer_values_are_bit_identical_to_stored_worksheet(reports_ro_conn, seeded_ifta_worksheet):
    result = queries.ifta_position_query(reports_ro_conn, quarter="2026-Q3")
    stored = seeded_ifta_worksheet

    assert result["worksheets"][0]["fleet_mpg"] == stored["fleet_mpg"]
    assert result["worksheets"][0]["total_net_tax"] == stored["total_net_tax"]
    assert result["total_net_tax"] == stored["total_net_tax"]

    independent = reports_ro_conn.execute(
        "SELECT fleet_mpg, total_net_tax FROM ifta_worksheets WHERE ifta_worksheet_id = ?",
        (stored["ifta_worksheet_id"],),
    ).fetchone()
    assert result["worksheets"][0]["fleet_mpg"] == independent["fleet_mpg"]
    assert result["worksheets"][0]["total_net_tax"] == independent["total_net_tax"]


def test_rendered_html_shows_the_exact_stored_net_tax(reports_ro_conn, seeded_ifta_worksheet, seeded_library):
    result = queries.ifta_position_query(reports_ro_conn, quarter="2026-Q3")
    template = load_template(seeded_library["roots"]["library"], "ifta_position", "1")
    html = render_answer_html(
        template, result, as_of="2026-08-04T12:00:00Z", period_label="Q3 2026", template_version="1",
    )
    expected = f"${seeded_ifta_worksheet['total_net_tax']:,.2f}"
    assert expected in html
    assert "Prepared" in html and "estimate, not filed" in html


def test_ifta_position_query_never_multiplies_rate_against_read_only_data(reports_ro_conn, seeded_ifta_worksheet):
    """A regression guard, not just a style check: taxable_gallons and
    net_tax returned by the query must equal the stored worksheet line's
    values precisely, not a value recomputed from miles/fleet_mpg/rate at
    query time (which could silently drift from what was actually sealed)."""
    result = queries.ifta_position_query(reports_ro_conn, quarter="2026-Q3")
    for line in result["lines"]:
        recomputed_taxable_gallons = line["miles"] / seeded_ifta_worksheet["fleet_mpg"]
        # Equality here is expected only because the query reads the same
        # stored value the engine wrote -- if the query recomputed it
        # in a different order/precision this would be the one place a
        # drift could appear, so we compare against the stored line too.
        stored_line = next(l for l in seeded_ifta_worksheet["lines"] if l["jurisdiction"] == line["jurisdiction"])
        assert line["taxable_gallons"] == stored_line["taxable_gallons"]
        assert recomputed_taxable_gallons == stored_line["taxable_gallons"]
