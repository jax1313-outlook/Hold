"""Jurisdiction derivation from a vendor address — "derived from
vendor_address, never guessed" (contracts/fuel_record.schema.json).

Deterministic pattern match only: a 2-letter state/province code
immediately before a 5-digit ZIP, or at the end of the address string. No
inference, no lookup against a location database. If neither pattern
matches, this raises rather than returning a plausible-looking guess — a
line whose jurisdiction can't be determined this way quarantines instead
of routing.
"""
from __future__ import annotations

import re

_BEFORE_ZIP = re.compile(r",\s*([A-Za-z]{2})\s+\d{5}(-\d{4})?\b")
_TRAILING = re.compile(r",\s*([A-Za-z]{2})\s*$")


class JurisdictionDerivationError(ValueError):
    def __init__(self, vendor_address: str | None):
        super().__init__(f"could not derive a jurisdiction from vendor_address {vendor_address!r}")
        self.vendor_address = vendor_address


def derive_jurisdiction(vendor_address: str | None) -> str:
    if vendor_address:
        for pattern in (_BEFORE_ZIP, _TRAILING):
            match = pattern.search(vendor_address)
            if match:
                return match.group(1).upper()
    raise JurisdictionDerivationError(vendor_address)
