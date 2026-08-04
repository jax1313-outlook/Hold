import hashlib

from dispatch.common.hashing import sha256_bytes, sha256_file


def test_sha256_file_matches_hashlib_reference(tmp_path):
    content = b"a" * (2 * 1024 * 1024) + b"tail bytes"  # spans multiple chunks
    path = tmp_path / "big.bin"
    path.write_bytes(content)

    assert sha256_file(path) == hashlib.sha256(content).hexdigest()


def test_sha256_bytes_matches_hashlib_reference():
    content = b"hello evidence spine"
    assert sha256_bytes(content) == hashlib.sha256(content).hexdigest()


def test_different_content_hashes_differ(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("content A")
    b.write_text("content B")
    assert sha256_file(a) != sha256_file(b)
