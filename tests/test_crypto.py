"""Tests for crypto utilities."""

from huproof.core.crypto import sha256_hex


def test_sha256_consistency() -> None:
    """Test SHA256 hashing consistency."""
    text = "test string"
    hash1 = sha256_hex(text)
    hash2 = sha256_hex(text)
    assert hash1 == hash2  # Deterministic


def test_sha256_format() -> None:
    """Test SHA256 output format."""
    text = "test"
    hash_value = sha256_hex(text)
    assert isinstance(hash_value, str)
    assert len(hash_value) == 64  # SHA256 hex = 64 chars
    assert all(c in "0123456789abcdef" for c in hash_value.lower())


def test_sha256_different_inputs() -> None:
    """Test that different inputs produce different hashes."""
    hash1 = sha256_hex("input1")
    hash2 = sha256_hex("input2")
    assert hash1 != hash2


def test_sha256_origin_hash() -> None:
    """Test origin hash generation."""
    origin = "http://localhost:5173"
    hash_value = sha256_hex(origin)
    assert len(hash_value) == 64
    # Should be consistent
    assert sha256_hex(origin) == hash_value

