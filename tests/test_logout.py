"""Tests for logout endpoint."""

import pytest
from fastapi.testclient import TestClient


def test_logout_with_invalid_token(test_client: TestClient, test_headers: dict[str, str]) -> None:
    """Test logout with invalid token."""
    # Try logout without token
    resp = test_client.post("/api/logout", headers=test_headers)
    assert resp.status_code == 422  # Missing header

    # Try logout with invalid token format
    resp = test_client.post("/api/logout", headers={**test_headers, "Authorization": "Invalid token"})
    assert resp.status_code == 401

    # Try logout with malformed Bearer token
    resp = test_client.post("/api/logout", headers={**test_headers, "Authorization": "Bearer invalid.jwt.token"})
    assert resp.status_code == 401

