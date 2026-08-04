"""Golden regression: retention class defaulting.
contracts/evidence_record.schema.json defaults retention_class to
'ifta_4yr' (the statutory minimum, DISPATCH_BASE_CONSTITUTION_v1 #6)."""
from __future__ import annotations


def test_retention_class_defaults_when_omitted(spine, sample_file):
    metadata = {"document_date": "2026-08-01"}  # no retention_class supplied
    record = spine.register(sample_file, "pump_receipt", metadata)
    assert record["retention_class"] == "ifta_4yr"


def test_explicit_retention_class_is_honored(spine, sample_file):
    metadata = {"document_date": "2026-08-01", "retention_class": "ifta_4yr"}
    record = spine.register(sample_file, "pump_receipt", metadata)
    assert record["retention_class"] == "ifta_4yr"
