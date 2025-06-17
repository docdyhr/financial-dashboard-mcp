"""Tests for authentication API endpoints."""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_register_new_user():
    """Test user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "securepassword123",
            "full_name": "New User",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert data["full_name"] == "New User"
    assert "hashed_password" not in data


def test_login_with_valid_credentials():
    """Test login with valid credentials."""
    # First register a user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "logintest@example.com",
            "username": "logintest",
            "password": "testpassword123",
        },
    )

    # Then login
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "logintest@example.com",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_with_invalid_credentials():
    """Test login with invalid credentials."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_access_protected_endpoint_without_token():
    """Test accessing protected endpoint without token."""
    response = client.get("/api/v1/positions/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_access_protected_endpoint_with_token():
    """Test accessing protected endpoint with valid token."""
    # First register and login
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "protectedtest@example.com",
            "username": "protectedtest",
            "password": "testpassword123",
        },
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "protectedtest@example.com",
            "password": "testpassword123",
        },
    )
    token = login_response.json()["access_token"]

    # Then access protected endpoint
    response = client.get(
        "/api/v1/positions/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
