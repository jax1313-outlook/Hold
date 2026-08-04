"""Template loading -- REPORTS_CHARTER_v1.md: a report is a versioned JSON
file under LIBRARY\\Templates\\Reports\\, loaded by name+version."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dispatch.reports.templates_engine import (
    TemplateMismatchError,
    TemplateNotFoundError,
    load_template,
)


def test_loads_all_three_seeded_templates(seeded_library):
    library_root = seeded_library["roots"]["library"]
    for report_type in ("fuel_spend", "expense_summary", "ifta_position"):
        template = load_template(library_root, report_type, "1")
        assert template["report_type"] == report_type
        assert template["version"] == "1"
        assert "title" in template


def test_missing_template_raises(seeded_library):
    library_root = seeded_library["roots"]["library"]
    with pytest.raises(TemplateNotFoundError):
        load_template(library_root, "fuel_spend", "99")


def test_mismatched_report_type_in_file_raises(seeded_library, tmp_path):
    library_root = Path(seeded_library["roots"]["library"])
    reports_dir = library_root / "Templates" / "Reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    bad_path = reports_dir / "expense_summary.v2.json"
    bad_path.write_text(
        json.dumps({"report_type": "fuel_spend", "version": "2", "title": "Wrong"}),
        encoding="utf-8",
    )
    with pytest.raises(TemplateMismatchError):
        load_template(library_root, "expense_summary", "2")


def test_mismatched_version_in_file_raises(seeded_library, tmp_path):
    library_root = Path(seeded_library["roots"]["library"])
    reports_dir = library_root / "Templates" / "Reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    bad_path = reports_dir / "fuel_spend.v3.json"
    bad_path.write_text(
        json.dumps({"report_type": "fuel_spend", "version": "1", "title": "Stale"}),
        encoding="utf-8",
    )
    with pytest.raises(TemplateMismatchError):
        load_template(library_root, "fuel_spend", "3")
