"""Test fixtures and utilities."""

import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="function")
def test_client() -> Generator[TestClient, None, None]:
    """Create a test client with initialized database."""
    # Set test environment variables BEFORE importing app
    os.environ.setdefault("APP_SECRET", "test-secret")
    os.environ.setdefault("BYPASS_ZK_VERIFY", "1")
    os.environ.setdefault("ORIGIN", "http://localhost:5173")
    os.environ.setdefault("DB_URL", "sqlite:///./test.db")
    
    # Import after env vars are set
    from huproof.app import app
    from huproof.db.session import init_db
    
    # Initialize database
    init_db()
    
    # Create test client
    client = TestClient(app)
    
    yield client
    
    # Cleanup: remove test database
    try:
        os.remove("test.db")
    except FileNotFoundError:
        pass


@pytest.fixture
def test_headers() -> dict[str, str]:
    """Default test headers with Origin."""
    return {"Origin": "http://localhost:5173"}

