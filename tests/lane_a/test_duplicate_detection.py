"""Golden regression: duplicate-hash registration returns the existing
record flagged duplicate_document — never a second copy, neither as a
database row nor as a second archived file."""
from __future__ import annotations

from dispatch.common.hashing import sha256_file


def test_duplicate_returns_same_evidence_record_id(spine, sample_file, sample_metadata):
    first = spine.register(sample_file, "pump_receipt", sample_metadata)
    second = spine.register(sample_file, "pump_receipt", sample_metadata)

    assert second["evidence_record_id"] == first["evidence_record_id"]
    assert second["extraction_status"] == "duplicate_document"


def test_duplicate_does_not_insert_a_second_row(spine, sample_file, sample_metadata, db_conn):
    spine.register(sample_file, "pump_receipt", sample_metadata)
    spine.register(sample_file, "pump_receipt", sample_metadata)
    spine.register(sample_file, "pump_receipt", sample_metadata)

    count = db_conn.execute(
        "SELECT COUNT(*) FROM evidence_records WHERE file_hash = ?",
        (sha256_file(sample_file),),
    ).fetchone()[0]
    assert count == 1


def test_duplicate_does_not_write_a_second_archived_file(spine, sample_file, sample_metadata):
    spine.register(sample_file, "pump_receipt", sample_metadata)
    spine.register(sample_file, "pump_receipt", sample_metadata)

    archived_files = list((spine._archive_root / "Evidence").rglob("*.txt"))
    assert len(archived_files) == 1


def test_original_record_extraction_status_is_never_mutated_to_duplicate(
    spine, sample_file, sample_metadata, db_conn
):
    first = spine.register(sample_file, "pump_receipt", sample_metadata)
    spine.register(sample_file, "pump_receipt", sample_metadata)

    row = db_conn.execute(
        "SELECT extraction_status FROM evidence_records WHERE evidence_record_id = ?",
        (first["evidence_record_id"],),
    ).fetchone()
    assert row["extraction_status"] == "complete"


def test_duplicate_registration_writes_flagged_audit_entry(spine, sample_file, sample_metadata, db_conn):
    from dispatch.common import audit

    spine.register(sample_file, "pump_receipt", sample_metadata)
    spine.register(sample_file, "pump_receipt", sample_metadata)

    entries = audit.read_audit_entries(db_conn)
    flagged = [e for e in entries if e["outcome"] == "flagged"]
    assert len(flagged) == 1
    assert flagged[0]["action"] == "evidence.register"
