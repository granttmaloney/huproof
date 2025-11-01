"""Tests for challenge generation."""

import pytest
from fastapi.testclient import TestClient

from huproof.core.challenge import generate_challenge, generate_nonce


def test_challenge_generation() -> None:
    """Test challenge generation."""
    challenge = generate_challenge()
    assert isinstance(challenge, str)
    assert len(challenge) > 0
    # Should be alphanumeric
    assert challenge.replace(" ", "").isalnum() or any(c in challenge for c in "-_")


def test_challenge_uniqueness() -> None:
    """Test that challenges are unique."""
    challenges = [generate_challenge() for _ in range(10)]
    assert len(challenges) == len(set(challenges))  # All unique


def test_nonce_generation() -> None:
    """Test nonce generation."""
    nonce = generate_nonce()
    assert isinstance(nonce, str)
    assert len(nonce) > 0
    # Should be URL-safe base64-like
    assert all(c.isalnum() or c in "-_" for c in nonce)


def test_nonce_uniqueness() -> None:
    """Test that nonces are unique."""
    nonces = [generate_nonce() for _ in range(10)]
    assert len(nonces) == len(set(nonces))  # All unique


def test_challenge_format() -> None:
    """Test challenge format consistency."""
    challenges = [generate_challenge() for _ in range(5)]
    # All should be strings
    assert all(isinstance(c, str) for c in challenges)
    # All should have reasonable length
    assert all(5 <= len(c) <= 50 for c in challenges)

