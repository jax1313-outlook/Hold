import pytest

from dispatch.receipt.extraction.vision import (
    ClaudeVisionExtractor,
    VisionExtractionUnavailable,
    _parse_response_text,
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


# --- _parse_response_text(): real model output wraps JSON in a markdown
# fence despite the prompt saying "no other text" -- found via a live
# call against a real pump receipt image, 2026-08-05. Quarantined every
# real receipt unconditionally until fixed. ---------------------------


def test_parse_response_text_handles_plain_json():
    text = '{"document_total": 42.0, "lines": [{"amount": 42.0}]}'
    lines, total = _parse_response_text(text)
    assert total == 42.0
    assert lines == [{"amount": 42.0}]


def test_parse_response_text_strips_a_json_language_tagged_fence():
    # The exact shape returned by a real live call, reproduced verbatim.
    text = (
        "```json\n"
        "{\n"
        '  "document_total": 438.24,\n'
        '  "lines": [\n'
        "    {\n"
        '      "vendor_name": "Love\'s Travel Stop #327",\n'
        '      "amount": 438.24,\n'
        '      "extraction_confidence": 0.97\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "```"
    )
    lines, total = _parse_response_text(text)
    assert total == 438.24
    assert lines[0]["vendor_name"] == "Love's Travel Stop #327"
    assert lines[0]["extraction_confidence"] == 0.97


def test_parse_response_text_strips_a_bare_fence_with_no_language_tag():
    text = '```\n{"document_total": 10.0, "lines": []}\n```'
    lines, total = _parse_response_text(text)
    assert total == 10.0
    assert lines == []


def test_parse_response_text_still_raises_on_genuinely_malformed_output():
    with pytest.raises(VisionExtractionUnavailable):
        _parse_response_text("```json\nnot actually json\n```")


def test_parse_response_text_still_raises_on_prose_with_no_json_at_all():
    with pytest.raises(VisionExtractionUnavailable):
        _parse_response_text("I could not read this receipt clearly.")
