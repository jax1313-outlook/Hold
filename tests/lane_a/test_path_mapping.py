"""Golden regression: path mapping honored — writes land only under
configured roots, and only under those roots (no leakage elsewhere, no
hardcoded root)."""
from __future__ import annotations

from pathlib import Path


def test_archived_file_lands_under_configured_archive_root(spine, sample_file, sample_metadata):
    record = spine.register(sample_file, "pump_receipt", sample_metadata)
    absolute_path = (spine._archive_root / record["archive_path"]).resolve()

    assert absolute_path.is_relative_to(spine._archive_root.resolve())
    assert absolute_path.is_file()


def test_library_index_entry_lands_under_configured_library_root(spine, sample_file, sample_metadata):
    record = spine.register(sample_file, "pump_receipt", sample_metadata)
    index_path = (spine._library_root / "EvidenceIndex" / f"{record['evidence_record_id']}.json").resolve()

    assert index_path.is_relative_to(spine._library_root.resolve())
    assert index_path.is_file()


def test_two_sandboxes_never_cross_write(tmp_path):
    from dispatch.common.db import bootstrap
    from dispatch.evidence.interface import EvidenceSpine

    sandbox_a = tmp_path / "sandbox_a"
    sandbox_b = tmp_path / "sandbox_b"
    for base in (sandbox_a, sandbox_b):
        (base / "Archive").mkdir(parents=True)
        (base / "Library").mkdir(parents=True)

    source = tmp_path / "doc.txt"
    source.write_text("cross-sandbox isolation check")

    conn_a = bootstrap(sandbox_a / "Operations" / "Data" / "dispatch.db")
    spine_a = EvidenceSpine(
        conn_a, {"archive": str(sandbox_a / "Archive"), "library": str(sandbox_a / "Library")}
    )
    spine_a.register(source, "pump_receipt", {"document_date": "2026-08-01"})

    assert any((sandbox_a / "Archive").rglob("*.txt"))
    assert not any((sandbox_b / "Archive").rglob("*.txt"))
