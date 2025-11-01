"""Tests for security input validation."""

import pytest
from fastapi.testclient import TestClient


def test_sql_injection_attempts(test_client: TestClient, test_headers: dict[str, str]) -> None:
    """Test SQL injection attempts are sanitized."""
    # Try SQL injection in user_id
    malicious_user_id = "'; DROP TABLE users; --"
    resp = test_client.get(f"/api/login/start?user_id={malicious_user_id}", headers=test_headers)
    # Should return 404 (user not found) or 400, not 500 (SQL error)
    assert resp.status_code in [400, 404], "Should not execute SQL injection"


def test_oversized_payload(test_client: TestClient, test_headers: dict[str, str]) -> None:
    """Test oversized payload rejection."""
    enroll_resp = test_client.get("/api/enroll/start", headers=test_headers)
    assert enroll_resp.status_code == 200
    enroll_data = enroll_resp.json()
    
    # Create oversized payload
    huge_string = "x" * 100000
    payload = {
        "commitment": huge_string,
        "public_inputs": {
            "nonce": enroll_data["nonce"],
            "origin_hash": enroll_data["origin_hash"],
            "tau": enroll_data["tau"],
            "timestamp": enroll_data["timestamp"],
            "C": huge_string,
            "sig": huge_string,
        },
        "proof": {"pi_a": [], "pi_b": [], "pi_c": []},
    }
    resp = test_client.post("/api/enroll/finish", json=payload, headers=test_headers)
    # Should reject due to validation (max_length in schema)
    assert resp.status_code == 422


def test_malformed_json(test_client: TestClient, test_headers: dict[str, str]) -> None:
    """Test malformed JSON rejection."""
    resp = test_client.post(
        "/api/enroll/finish",
        data="not valid json{",
        headers={**test_headers, "Content-Type": "application/json"},
    )
    assert resp.status_code == 422


def test_invalid_field_types(test_client: TestClient, test_headers: dict[str, str]) -> None:
    """Test invalid field types are rejected."""
    enroll_resp = test_client.get("/api/enroll/start", headers=test_headers)
    assert enroll_resp.status_code == 200
    enroll_data = enroll_resp.json()
    
    # Send wrong types
    payload = {
        "commitment": "123",
        "public_inputs": {
            "nonce": enroll_data["nonce"],
            "origin_hash": enroll_data["origin_hash"],
            "tau": "not a number",  # Should be int
            "timestamp": enroll_data["timestamp"],
            "C": "123",
            "sig": "456",
        },
        "proof": {"pi_a": [], "pi_b": [], "pi_c": []},
    }
    resp = test_client.post("/api/enroll/finish", json=payload, headers=test_headers)
    assert resp.status_code == 422  # Validation error

