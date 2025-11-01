"""Test fixtures and utilities."""

import os
import tempfile
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
    
    # Use unique temp file for each test
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_path = db_file.name
    db_file.close()
    os.environ["DB_URL"] = f"sqlite:///{db_path}"
    
    # Import after env vars are set
    from huproof.app import app
    from huproof.db.session import init_db
    
    # Force reinitialize the engine with new DB URL
    from sqlalchemy import create_engine
    from huproof.config.settings import get_settings
    from huproof.db import session as db_session
    
    settings = get_settings()
    
    # Dispose old engine if it exists and reset global
    if hasattr(db_session, '_engine') and db_session._engine is not None:
        try:
            db_session._engine.dispose()
        except Exception:
            pass
    db_session._engine = None
    
    # Initialize database (will create new engine with new DB URL)
    init_db()
    
    # Create test client
    client = TestClient(app)
    
    yield client
    
    # Cleanup
    try:
        # Close all connections
        if hasattr(db_session, '_engine') and db_session._engine is not None:
            db_session._engine.dispose()
        # Remove database file
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass


@pytest.fixture
def test_headers() -> dict[str, str]:
    """Default test headers with Origin."""
    return {"Origin": "http://localhost:5173"}

