import os

from fastapi.testclient import TestClient


def test_enroll_start_and_finish() -> None:
    os.environ.setdefault("APP_SECRET", "test-secret")
    os.environ.setdefault("BYPASS_ZK_VERIFY", "1")

    from huproof.app import app

    client = TestClient(app)

    # Start enrollment
    rs = client.get("/api/enroll/start")
    assert rs.status_code == 200
    data = rs.json()
    assert "challenge" in data and "nonce" in data

    # Finish enrollment with dummy public inputs and proof
    payload = {
        "commitment": "C",
        "public_inputs": {
            "nonce": data["nonce"],
            "origin_hash": data["origin_hash"],
            "tau": data["tau"],
            "timestamp": data["timestamp"],
            "C": "C",
            "sig": "S",
        },
        "proof": {"pi_a": [], "pi_b": [], "pi_c": []},
    }
    rf = client.post("/api/enroll/finish", json=payload)
    assert rf.status_code == 200
    out = rf.json()
    assert out["success"] is True
    assert isinstance(out["user_id"], str) and out["user_id"]


