import pytest
from fastapi.testclient import TestClient


def test_health(test_client: TestClient) -> None:
    """Test health check endpoint."""
    resp = test_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


