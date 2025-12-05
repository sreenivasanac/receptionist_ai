"""Pytest fixtures for tests."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import init_db


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Initialize database for tests."""
    init_db()


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)
