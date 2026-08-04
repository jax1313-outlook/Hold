import pytest

from dispatch.evidence.interface import EvidenceNotFoundError


def test_retrieve_unknown_id_raises(spine):
    with pytest.raises(EvidenceNotFoundError):
        spine.retrieve("01UNKNOWNULIDDOESNOTEXIST0")


def test_link_children_unknown_id_raises(spine):
    with pytest.raises(EvidenceNotFoundError):
        spine.link_children("01UNKNOWNULIDDOESNOTEXIST0", ["fuel_rec_1"])


def test_register_rejects_invalid_document_type(spine, sample_file, sample_metadata):
    with pytest.raises(ValueError):
        spine.register(sample_file, "not_a_real_document_type", sample_metadata)


def test_register_rejects_missing_document_date(spine, sample_file):
    with pytest.raises(ValueError):
        spine.register(sample_file, "pump_receipt", {})
