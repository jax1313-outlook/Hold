import pytest

from dispatch.receipt.extraction.vision import (
    ClaudeVisionExtractor,
    VisionExtractionUnavailable,
    build_extractor,
)


def test_no_api_key_raises_unavailable(tmp_path):
    extractor = ClaudeVisionExtractor(api_key=None)
    doc = tmp_path / "scan.jpg"
    doc.write_bytes(b"not a real image")

    with pytest.raises(VisionExtractionUnavailable):
        extractor.extract(doc)


def test_build_extractor_reads_config_key():
    extractor = build_extractor({"anthropic_api_key": "sk-test-123"})
    assert extractor._api_key == "sk-test-123"


def test_build_extractor_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-from-env")
    extractor = build_extractor({})
    assert extractor._api_key == "sk-from-env"


def test_build_extractor_with_nothing_configured_degrades_cleanly(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    extractor = build_extractor({})
    doc = tmp_path / "scan.jpg"
    doc.write_bytes(b"not a real image")

    with pytest.raises(VisionExtractionUnavailable):
        extractor.extract(doc)
