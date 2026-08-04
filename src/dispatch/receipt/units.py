"""Unit normalization — FuelRecord.gallons_normalized: liters × 0.264172
when needed (DISPATCH_BUILD_BLUEPRINT_v1 Part 1.2).

Both validators.py (computing a dedup key to check for an existing
duplicate before a record exists) and router.py (computing the same key
to store on the record it creates) must normalize identically, or dedup
silently breaks for every liter-denominated purchase — one function, both
call sites.
"""
from __future__ import annotations

LITERS_TO_GALLONS = 0.264172


def normalize_gallons(volume_as_received: float | None, unit: str | None) -> float:
    if volume_as_received is None:
        return 0.0
    if unit == "liters":
        return volume_as_received * LITERS_TO_GALLONS
    return volume_as_received
