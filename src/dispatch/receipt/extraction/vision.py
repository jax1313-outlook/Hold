"""Vision extraction for scanned/photographed receipts — this lane's one
sanctioned network call.

DISPATCH_BUILD_BLUEPRINT_v1 Part 3.1: "the LLM call is the only network
dependency, and extraction degrades to the review queue when offline."
`ClaudeVisionExtractor.extract()` raises `VisionExtractionUnavailable` for
both "no API key configured" and "the call itself failed" — one code
path, two occasions to use it. Nothing in this lane's own test suite
exercises a live call: there are no real credentials in this build
environment, and a deterministic test suite shouldn't depend on a live
external service regardless. See docs/lanes/C/NOTES.md.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol


class VisionExtractionUnavailable(Exception):
    """No working vision path exists for this document right now — no
    credentials configured, or the call failed. Callers treat both cases
    identically: quarantine the document to the review queue. This is the
    correct behavior for a genuine production outage, not a workaround
    for this sandbox's lack of credentials."""


class VisionExtractor(Protocol):
    def extract(self, path: Path | str) -> tuple[list[dict[str, Any]], float | None]:
        """Returns (lines, document_total) in the same normalized shape
        the deterministic parsers use. Must raise
        VisionExtractionUnavailable rather than return a low-confidence
        guess when it cannot genuinely attempt extraction."""
        ...


_EXTRACTION_PROMPT = """\
You are extracting structured line items from a trucking-related receipt
or invoice image. Return ONLY a JSON object with this exact shape, no
other text:

{
  "document_total": <number or null>,
  "lines": [
    {
      "vendor_name": <string>, "vendor_address": <string or null>,
      "purchase_date": <"YYYY-MM-DD">, "purchase_time": <string or null>,
      "line_description": <string>, "category": <string>,
      "amount": <number>, "tax_amount": <number or null>,
      "currency": <"USD" or "CAD">,
      "fuel_type": <"diesel"|"gasoline"|null>,
      "tractor_or_reefer": <"tractor"|"reefer"|null>,
      "volume_as_received": <number or null>,
      "volume_as_received_unit": <"gallons"|"liters"|null>,
      "unit_price": <number or null>, "taxes_included": <bool>,
      "unit_number": <string or null>, "driver": <string or null>,
      "odometer": <integer or null>, "payment_method": <string or null>,
      "card_last4": <string or null>, "receipt_number": <string or null>,
      "extraction_confidence": <0.0-1.0>
    }
  ]
}

"category" must be one of the closed vocabulary categories you have been
told about separately. If you cannot read a field, use null rather than
guessing. extraction_confidence should reflect your actual certainty for
that specific line, not a blanket high score.
"""


class ClaudeVisionExtractor:
    """Real implementation, backed by the Anthropic API. Lazily imports
    `anthropic` so its absence doesn't break importing this module — only
    instantiating this class and calling extract() with no key configured
    ever touches that boundary, and even then only to raise
    VisionExtractionUnavailable cleanly."""

    def __init__(self, api_key: str | None, model: str = "claude-opus-4-6"):
        self._api_key = api_key
        self._model = model

    def extract(self, path: Path | str) -> tuple[list[dict[str, Any]], float | None]:
        if not self._api_key:
            raise VisionExtractionUnavailable("no API key configured")

        try:
            import anthropic
        except ImportError as exc:
            raise VisionExtractionUnavailable("anthropic package not installed") from exc

        try:
            client = anthropic.Anthropic(api_key=self._api_key)
            image_bytes = Path(path).read_bytes()
            media_type = _guess_media_type(path)
            response = client.messages.create(
                model=self._model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": _base64(image_bytes),
                                },
                            },
                            {"type": "text", "text": _EXTRACTION_PROMPT},
                        ],
                    }
                ],
            )
            return _parse_response_text(response.content[0].text)
        except VisionExtractionUnavailable:
            raise
        except Exception as exc:  # noqa: BLE001 — any network/API/parse failure degrades identically
            raise VisionExtractionUnavailable(str(exc)) from exc


def _guess_media_type(path: Path | str) -> str:
    suffix = Path(path).suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(suffix, "image/jpeg")


def _base64(data: bytes) -> str:
    import base64

    return base64.b64encode(data).decode("ascii")


def _strip_markdown_fence(text: str) -> str:
    """Real model output routinely wraps the JSON object in a ```json ...
    ``` fence despite being told to return no other text -- strip one
    leading/trailing fence, nothing else, so a genuinely malformed
    response still fails loudly rather than being coerced into parsing."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return text
    first_newline = stripped.find("\n")
    if first_newline == -1:
        return text
    body = stripped[first_newline + 1 :]
    if body.endswith("```"):
        body = body[: -len("```")]
    return body.strip()


def _parse_response_text(text: str) -> tuple[list[dict[str, Any]], float | None]:
    try:
        payload = json.loads(_strip_markdown_fence(text))
    except json.JSONDecodeError as exc:
        raise VisionExtractionUnavailable(f"model did not return valid JSON: {exc}") from exc
    return payload.get("lines", []), payload.get("document_total")


def build_extractor(config: dict[str, Any]) -> ClaudeVisionExtractor:
    """config may set "anthropic_api_key" directly; falls back to the
    ANTHROPIC_API_KEY environment variable. Neither being set is a normal,
    expected state in this build environment — it's what makes
    VisionExtractionUnavailable's degrade-to-queue path exercise for
    real, not a mock of one."""
    import os

    api_key = config.get("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY")
    return ClaudeVisionExtractor(api_key=api_key)
