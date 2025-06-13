"""Tests for FastAPI backend."""
import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "environment" in data


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "backend"


def test_api_status():
    """Test the API status endpoint."""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["api_version"] == "v1"
    assert "services" in data


@pytest.mark.asyncio
async def test_app_startup():
    """Test that the app starts up correctly."""
    # This is a placeholder test - in a real app you might test database connections
    # or other startup procedures
    assert app.title == "Financial Dashboard API"
