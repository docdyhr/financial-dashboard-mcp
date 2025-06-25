"""Tests for FastAPI backend."""

from fastapi.testclient import TestClient
import pytest

from backend.main import app

client = TestClient(app)


def test_root_endpoint() -> None:
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200  # nosec
    data = response.json()
    assert "message" in data  # nosec
    assert "version" in data  # nosec
    assert "environment" in data  # nosec


def test_health_check() -> None:
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200  # nosec
    data = response.json()
    assert data["status"] == "healthy"  # nosec
    assert data["service"] == "backend"  # nosec


def test_api_status() -> None:
    """Test the API status endpoint."""
    response = client.get("/api/v1/status")
    assert response.status_code == 200  # nosec
    data = response.json()
    assert data["status"] == "operational"  # nosec
    assert data["api_version"] == "v1"  # nosec
    assert "services" in data  # nosec


@pytest.mark.asyncio
async def test_app_startup() -> None:
    """Test that the app starts up correctly."""
    # This is a placeholder test - in a real app you might test database connections
    # or other startup procedures
    assert app.title == "Financial Dashboard API"  # nosec
