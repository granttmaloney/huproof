"""Tests for security utilities (JWT, JTI)."""

import pytest
from fastapi.testclient import TestClient

from huproof.core.security import create_access_token, decode_token, generate_jti


def test_jti_generation() -> None:
    """Test JTI generation."""
    jti1 = generate_jti()
    jti2 = generate_jti()
    assert isinstance(jti1, str)
    assert len(jti1) > 0
    assert jti1 != jti2  # Should be unique


def test_jwt_creation() -> None:
    """Test JWT token creation."""
    secret = "test-secret"
    token, jti = create_access_token("user123", secret=secret)
    assert isinstance(token, str)
    assert isinstance(jti, str)
    assert len(token) > 0
    assert len(jti) > 0


def test_jwt_decoding() -> None:
    """Test JWT token decoding."""
    secret = "test-secret"
    token, jti = create_access_token("user123", secret=secret)
    payload = decode_token(token, secret=secret)
    assert payload["sub"] == "user123"
    assert payload["jti"] == jti
    assert "iat" in payload
    assert "exp" in payload


def test_jwt_expiration() -> None:
    """Test JWT token expiration."""
    import time
    secret = "test-secret"
    token, _ = create_access_token("user123", secret=secret, expires_in_seconds=1)
    payload = decode_token(token, secret=secret)
    assert "exp" in payload
    
    # Wait for expiration
    time.sleep(2)
    import jwt
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token, secret=secret)


def test_jwt_invalid_secret() -> None:
    """Test JWT with wrong secret."""
    secret1 = "secret1"
    secret2 = "secret2"
    token, _ = create_access_token("user123", secret=secret1)
    import jwt
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(token, secret=secret2)


def test_jwt_custom_claims() -> None:
    """Test JWT with custom claims."""
    secret = "test-secret"
    claims = {"role": "admin", "extra": "data"}
    token, _ = create_access_token("user123", secret=secret, claims=claims)
    payload = decode_token(token, secret=secret)
    assert payload["sub"] == "user123"
    assert payload["role"] == "admin"
    assert payload["extra"] == "data"

