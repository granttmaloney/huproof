import os

from fastapi.testclient import TestClient


def test_health() -> None:
    # Ensure settings load with defaults
    os.environ.setdefault("APP_SECRET", "test-secret")
    from huproof.app import app  # import after env set

    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


