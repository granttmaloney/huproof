import os

import pytest
from fastapi.testclient import TestClient


def test_enroll_start_and_finish(test_client: TestClient, test_headers: dict[str, str]) -> None:
    """Test complete enrollment flow."""
    # Start enrollment
    rs = test_client.get("/api/enroll/start", headers=test_headers)
    assert rs.status_code == 200
    data = rs.json()
    assert "challenge" in data and "nonce" in data

    # Finish enrollment with dummy public inputs and proof
    # Use valid decimal strings for C and sig
    payload = {
        "commitment": "123456789",
        "public_inputs": {
            "nonce": data["nonce"],
            "origin_hash": data["origin_hash"],
            "tau": data["tau"],
            "timestamp": data["timestamp"],
            "C": "123456789",
            "sig": "987654321",
        },
        "proof": {"pi_a": [], "pi_b": [], "pi_c": []},
    }
    rf = test_client.post("/api/enroll/finish", json=payload, headers=test_headers)
    if rf.status_code != 200:
        print(f"Response status: {rf.status_code}")
        print(f"Response body: {rf.text}")
    assert rf.status_code == 200
    out = rf.json()
    assert out["success"] is True
    assert isinstance(out["user_id"], str) and out["user_id"]


