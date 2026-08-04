"""SHA-256 hashing utilities.

Used as both the integrity proof and the document-level dedup key for
evidence records (contracts/evidence_record.schema.json, file_hash).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

_CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path | str) -> str:
    """Hex-digest SHA-256 of a file's contents, read in chunks so file size
    doesn't matter."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK_SIZE), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
