"""Tests for logout endpoint."""

import os

from fastapi.testclient import TestClient


def test_logout_with_invalid_token() -> None:
    """Test logout with invalid token."""
    os.environ.setdefault("APP_SECRET", "test-secret")
    os.environ.setdefault("BYPASS_ZK_VERIFY", "1")

    from huproof.app import app

    client = TestClient(app)

    # Try logout without token
    resp = client.post("/api/logout")
    assert resp.status_code == 422  # Missing header

    # Try logout with invalid token format
    resp = client.post("/api/logout", headers={"Authorization": "Invalid token"})
    assert resp.status_code == 401

    # Try logout with malformed Bearer token
    resp = client.post("/api/logout", headers={"Authorization": "Bearer invalid.jwt.token"})
    assert resp.status_code == 401

