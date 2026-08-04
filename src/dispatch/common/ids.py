"""ULID generator.

ULID = 48-bit millisecond timestamp + 80-bit randomness, Crockford Base32
encoded to a fixed 26-character string that sorts lexicographically by
creation time. No external dependency: the format is small enough to
implement directly rather than pull in a package for it.

Reference: https://github.com/ulid/spec
"""
from __future__ import annotations

import os
import time

_CROCKFORD_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_TIMESTAMP_CHARS = 10  # 10 * 5 = 50 bits, enough to hold the 48-bit timestamp
_RANDOMNESS_CHARS = 16  # 16 * 5 = 80 bits, exactly the randomness component
_TIMESTAMP_MAX = (1 << 48) - 1


def _encode_base32(value: int, length: int) -> str:
    chars = ["0"] * length
    for i in range(length - 1, -1, -1):
        chars[i] = _CROCKFORD_ALPHABET[value & 0x1F]
        value >>= 5
    return "".join(chars)


def new_ulid(timestamp_ms: int | None = None) -> str:
    """Return a new ULID string. Pass timestamp_ms only in tests that need a
    fixed clock; production callers always omit it and get wall-clock time."""
    if timestamp_ms is None:
        timestamp_ms = int(time.time() * 1000)
    if not 0 <= timestamp_ms <= _TIMESTAMP_MAX:
        raise ValueError(f"timestamp_ms {timestamp_ms} out of ULID's 48-bit range")
    randomness = int.from_bytes(os.urandom(10), "big")
    return _encode_base32(timestamp_ms, _TIMESTAMP_CHARS) + _encode_base32(
        randomness, _RANDOMNESS_CHARS
    )


def is_valid_ulid(value: str) -> bool:
    return (
        isinstance(value, str)
        and len(value) == _TIMESTAMP_CHARS + _RANDOMNESS_CHARS
        and all(c in _CROCKFORD_ALPHABET for c in value)
    )
