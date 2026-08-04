"""Golden regression: modify-after-archive fails.

Three independent layers, each tested directly (not just "the code looks
right"): the archived file's mode bits are actually read-only (risk #2 —
verify, don't assume the chmod call worked); a raw UPDATE/DELETE against
evidence_records, evidence_children, or audit_log is rejected by the
database's own triggers, independent of any application code; and (see
test_no_update_delete_sql.py) the module surface contains no UPDATE/DELETE
statement against those tables in the first place.

Note on root: this container runs as root, which bypasses POSIX permission
bits, so we can't prove "a write attempt is denied" by attempting to write
and catching PermissionError here. What we can and do prove is exactly what
LANE_A_LAUNCH_PACKAGE_v1 risk #2 asks for: that the chmod call actually
changed the file's mode bits, checked by reading them back — not assumed
because the syscall didn't raise.
"""
from __future__ import annotations

import stat

import pytest
import sqlite3


def test_archived_file_mode_bits_are_read_only(spine, sample_file, sample_metadata):
    record = spine.register(sample_file, "pump_receipt", sample_metadata)
    absolute_path = spine._archive_root / record["archive_path"]

    mode = absolute_path.stat().st_mode
    assert mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH) == 0


def test_direct_update_on_evidence_records_is_rejected(spine, sample_file, sample_metadata, db_conn):
    record = spine.register(sample_file, "pump_receipt", sample_metadata)

    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            "UPDATE evidence_records SET vendor = 'tampered' WHERE evidence_record_id = ?",
            (record["evidence_record_id"],),
        )


def test_direct_delete_on_evidence_records_is_rejected(spine, sample_file, sample_metadata, db_conn):
    record = spine.register(sample_file, "pump_receipt", sample_metadata)

    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            "DELETE FROM evidence_records WHERE evidence_record_id = ?",
            (record["evidence_record_id"],),
        )


def test_direct_update_on_audit_log_is_rejected(spine, sample_file, sample_metadata, db_conn):
    spine.register(sample_file, "pump_receipt", sample_metadata)

    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute("UPDATE audit_log SET outcome = 'tampered' WHERE audit_id = 1")


def test_direct_delete_on_audit_log_is_rejected(spine, sample_file, sample_metadata, db_conn):
    spine.register(sample_file, "pump_receipt", sample_metadata)

    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute("DELETE FROM audit_log WHERE audit_id = 1")


def test_direct_update_on_evidence_children_is_rejected(spine, sample_file, sample_metadata, db_conn):
    record = spine.register(sample_file, "pump_receipt", sample_metadata)
    spine.link_children(record["evidence_record_id"], ["fuel_rec_1"])

    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            "UPDATE evidence_children SET derived_record_id = 'tampered' "
            "WHERE evidence_record_id = ?",
            (record["evidence_record_id"],),
        )


def test_direct_delete_on_evidence_children_is_rejected(spine, sample_file, sample_metadata, db_conn):
    record = spine.register(sample_file, "pump_receipt", sample_metadata)
    spine.link_children(record["evidence_record_id"], ["fuel_rec_1"])

    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            "DELETE FROM evidence_children WHERE evidence_record_id = ?",
            (record["evidence_record_id"],),
        )
