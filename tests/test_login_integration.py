"""Tests for login flow."""

import pytest
from fastapi.testclient import TestClient


def test_login_start_with_valid_user(test_client: TestClient, test_headers: dict[str, str]) -> None:
    """Test login start with valid user_id."""
    # First enroll a user
    enroll_resp = test_client.get("/api/enroll/start", headers=test_headers)
    assert enroll_resp.status_code == 200
    enroll_data = enroll_resp.json()
    
    payload = {
        "commitment": "123456789",
        "public_inputs": {
            "nonce": enroll_data["nonce"],
            "origin_hash": enroll_data["origin_hash"],
            "tau": enroll_data["tau"],
            "timestamp": enroll_data["timestamp"],
            "C": "123456789",
            "sig": "987654321",
        },
        "proof": {"pi_a": [], "pi_b": [], "pi_c": []},
    }
    finish_resp = test_client.post("/api/enroll/finish", json=payload, headers=test_headers)
    assert finish_resp.status_code == 200
    user_id = finish_resp.json()["user_id"]
    
    # Now test login start
    login_resp = test_client.get(f"/api/login/start?user_id={user_id}", headers=test_headers)
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "challenge" in data
    assert "nonce" in data
    assert "commitment" in data
    assert data["commitment"] == "123456789"


def test_login_start_with_invalid_user(test_client: TestClient, test_headers: dict[str, str]) -> None:
    """Test login start with invalid user_id returns 404."""
    invalid_user_id = "nonexistent-user-id"
    resp = test_client.get(f"/api/login/start?user_id={invalid_user_id}", headers=test_headers)
    assert resp.status_code == 404


def test_login_finish_flow(test_client: TestClient, test_headers: dict[str, str]) -> None:
    """Test complete login flow."""
    # Enroll first
    enroll_resp = test_client.get("/api/enroll/start", headers=test_headers)
    assert enroll_resp.status_code == 200
    enroll_data = enroll_resp.json()
    
    payload = {
        "commitment": "123456789",
        "public_inputs": {
            "nonce": enroll_data["nonce"],
            "origin_hash": enroll_data["origin_hash"],
            "tau": enroll_data["tau"],
            "timestamp": enroll_data["timestamp"],
            "C": "123456789",
            "sig": "987654321",
        },
        "proof": {"pi_a": [], "pi_b": [], "pi_c": []},
    }
    finish_resp = test_client.post("/api/enroll/finish", json=payload, headers=test_headers)
    assert finish_resp.status_code == 200
    user_id = finish_resp.json()["user_id"]
    
    # Login start
    login_start_resp = test_client.get(f"/api/login/start?user_id={user_id}", headers=test_headers)
    assert login_start_resp.status_code == 200
    login_data = login_start_resp.json()
    
    # Login finish
    login_finish_payload = {
        "public_inputs": {
            "nonce": login_data["nonce"],
            "origin_hash": login_data["origin_hash"],
            "tau": login_data["tau"],
            "timestamp": login_data["timestamp"],
            "C": login_data["commitment"],
            "sig": "987654321",
        },
        "proof": {"pi_a": [], "pi_b": [], "pi_c": []},
    }
    login_finish_resp = test_client.post("/api/login/finish", json=login_finish_payload, headers=test_headers)
    assert login_finish_resp.status_code == 200
    result = login_finish_resp.json()
    assert result["success"] is True
    assert "token" in result
    assert isinstance(result["token"], str)
    assert len(result["token"]) > 0

