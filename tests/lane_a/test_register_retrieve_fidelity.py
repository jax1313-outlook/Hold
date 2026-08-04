"""Golden regression: register -> retrieve fidelity. What you get back from
retrieve() must exactly match what register() returned — not just an
overlapping subset of fields."""
from __future__ import annotations


def test_retrieved_record_matches_registered_record_exactly(spine, sample_file, sample_metadata):
    registered = spine.register(sample_file, "pump_receipt", sample_metadata)
    retrieved, _path = spine.retrieve(registered["evidence_record_id"])

    assert retrieved == registered


def test_retrieved_record_reflects_all_supplied_metadata(spine, sample_file):
    metadata = {
        "document_date": "2026-07-15",
        "capture_date": "2026-08-04T09:30:00Z",
        "vendor": "Pilot Flying J",
        "statement_period_start": "2026-07-01",
        "statement_period_end": "2026-07-31",
        "page_count": 3,
        "retention_class": "ifta_4yr",
    }
    registered = spine.register(sample_file, "credit_card_statement", metadata)
    retrieved, _path = spine.retrieve(registered["evidence_record_id"])

    for key, value in metadata.items():
        assert retrieved[key] == value


def test_retrieved_file_contents_match_source(spine, sample_file, sample_metadata):
    source_bytes = sample_file.read_bytes()
    registered = spine.register(sample_file, "pump_receipt", sample_metadata)
    _record, absolute_path = spine.retrieve(registered["evidence_record_id"])

    assert absolute_path.read_bytes() == source_bytes
