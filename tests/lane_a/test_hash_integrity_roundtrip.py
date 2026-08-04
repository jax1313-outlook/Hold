"""Golden regression: hash integrity round-trip.

retrieve() must succeed on an untouched archive and re-verify the hash on
every call (not just trust the stored value); a tampered archive file must
be caught, not silently served.
"""
from __future__ import annotations

import pytest

from dispatch.common.hashing import sha256_file
from dispatch.evidence.interface import EvidenceIntegrityError


def test_round_trip_hash_matches(spine, sample_file, sample_metadata):
    registered = spine.register(sample_file, "pump_receipt", sample_metadata)
    record, absolute_path = spine.retrieve(registered["evidence_record_id"])

    assert record["file_hash"] == registered["file_hash"]
    assert sha256_file(absolute_path) == record["file_hash"]


def test_retrieve_re_verifies_hash_every_call(spine, sample_file, sample_metadata):
    registered = spine.register(sample_file, "pump_receipt", sample_metadata)

    for _ in range(3):
        record, _path = spine.retrieve(registered["evidence_record_id"])
        assert record["file_hash"] == registered["file_hash"]


def test_tampered_archive_raises_and_does_not_return_bad_data(spine, sample_file, sample_metadata):
    registered = spine.register(sample_file, "pump_receipt", sample_metadata)
    absolute_path = spine._archive_root / registered["archive_path"]

    absolute_path.chmod(0o600)
    absolute_path.write_bytes(b"someone tampered with this after archiving")

    with pytest.raises(EvidenceIntegrityError):
        spine.retrieve(registered["evidence_record_id"])


def test_missing_archived_file_raises_integrity_error(spine, sample_file, sample_metadata):
    registered = spine.register(sample_file, "pump_receipt", sample_metadata)
    absolute_path = spine._archive_root / registered["archive_path"]
    absolute_path.chmod(0o600)
    absolute_path.unlink()

    with pytest.raises(EvidenceIntegrityError):
        spine.retrieve(registered["evidence_record_id"])
