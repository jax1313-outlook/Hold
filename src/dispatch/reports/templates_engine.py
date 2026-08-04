"""The template engine — REPORTS_CHARTER_v1.md: "A report = a versioned
JSON template (query definition + layout) loaded from
LIBRARY\\Templates\\Reports\\... Identical inputs must produce identical
bytes, always."

A template file is pure data: which field is the big number, which
breakdown table to show, how to format each column. Adding a report type
later is a template file + a fixture; this engine and rendering.py never
change for it — only queries.py needs a new function to actually compute
that report type's numbers, since aggregation SQL is still code, not
data. Named `templates_engine` (not `templates`) to avoid colliding with
this package's own `templates/` directory of Jinja HTML files.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class TemplateNotFoundError(FileNotFoundError):
    pass


class TemplateMismatchError(ValueError):
    pass


def template_path(library_root: Path | str, report_type: str, version: str) -> Path:
    return Path(library_root) / "Templates" / "Reports" / f"{report_type}.v{version}.json"


def load_template(library_root: Path | str, report_type: str, version: str) -> dict[str, Any]:
    path = template_path(library_root, report_type, version)
    if not path.is_file():
        raise TemplateNotFoundError(f"no template at {path}")
    with open(path, "r", encoding="utf-8") as f:
        template = json.load(f)
    if template.get("report_type") != report_type or str(template.get("version")) != str(version):
        raise TemplateMismatchError(
            f"template file {path} declares report_type={template.get('report_type')!r} "
            f"version={template.get('version')!r}, expected {report_type!r}/{version!r}"
        )
    return template
