"""Deterministic CSV parser — Lane C's own normalized export format.

A "csv_export" document is already a structured, machine-produced file
(unlike a scanned receipt), so parsing it is deterministic: no vision
call, no confidence below 1.0. A row whose `vendor_name` column reads
"TOTAL" (case-insensitive) is treated as the document's declared total
for sum validation, not a transaction line.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from dispatch.receipt.parsers.common import build_line

_TOTAL_MARKER = "TOTAL"


def parse(path: Path | str) -> tuple[list[dict[str, Any]], float | None]:
    lines: list[dict[str, Any]] = []
    document_total: float | None = None

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("vendor_name") or "").strip().upper() == _TOTAL_MARKER:
                document_total = float(row["amount"])
                continue
            lines.append(build_line(lambda field, row=row: row.get(field)))

    return lines, document_total
