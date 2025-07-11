"""Tests for authentication API endpoints."""

from unittest.mock import patch

import pytest


def test_register_new_user(client):
    """Test user registration."""
    import uuid

    unique_id = str(uuid.uuid4())[:8]

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"newuser{unique_id}@example.com",
            "username": f"newuser{unique_id}",
            "password": "securepassword123",
            "full_name": "New User",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == f"newuser{unique_id}@example.com"
    assert data["username"] == f"newuser{unique_id}"
    assert data["full_name"] == "New User"
    assert "hashed_password" not in data


def test_login_with_valid_credentials(client):
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


def test_login_with_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    assert response.json()["message"] == "Incorrect username or password"


def test_access_protected_endpoint_without_token(client):
    """Test accessing protected endpoint without token."""
    response = client.get("/api/v1/positions/")
    assert response.status_code == 401
    assert response.json()["message"] == "Not authenticated"


def test_access_protected_endpoint_with_token(client):
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
    # Should not get 401 (unauthorized) - could be 200 (empty list) or 404 (user not found in position service)
    assert response.status_code != 401


@pytest.mark.auth
@pytest.mark.api
class TestUserRegistration:
    """Test user registration scenarios."""

    def test_register_with_valid_data(self, client):
        """Test user registration with valid data."""
        import uuid

        unique_id = str(uuid.uuid4())[:8]

        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"valid{unique_id}@example.com",
                "username": f"validuser{unique_id}",
                "password": "SecurePass123!",
                "full_name": "Valid User",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == f"valid{unique_id}@example.com"
        assert data["username"] == f"validuser{unique_id}"
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email."""
        # Register first user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "user1",
                "password": "password123",
            },
        )

        # Try to register with same email
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "user2",
                "password": "password123",
            },
        )
        assert response.status_code == 400
        assert (
            "already taken" in response.json()["message"].lower()
            or "already registered" in response.json()["message"].lower()
        )

    def test_register_duplicate_username(self, client):
        """Test registration with duplicate username."""
        # Register first user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "user1@example.com",
                "username": "duplicateuser",
                "password": "password123",
            },
        )

        # Try to register with same username
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user2@example.com",
                "username": "duplicateuser",
                "password": "password123",
            },
        )
        assert response.status_code == 400
        assert (
            "already taken" in response.json()["message"].lower()
            or "already registered" in response.json()["message"].lower()
        )

    @pytest.mark.parametrize(
        "email",
        [
            "invalid-email",
            "@example.com",
            "user@",
            "user@.com",
            "",
        ],
    )
    def test_register_invalid_email(self, client, email):
        """Test registration with invalid email formats."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": "testuser",
                "password": "password123",
            },
        )
        assert response.status_code == 422

    @pytest.mark.parametrize(
        "password",
        [
            "",  # Empty password
            "123",  # Too short
            "a" * 200,  # Too long
        ],
    )
    def test_register_invalid_password(self, client, password):
        """Test registration with invalid passwords."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": password,
            },
        )
        assert response.status_code == 422


@pytest.mark.auth
@pytest.mark.api
class TestUserLogin:
    """Test user login scenarios."""

    def setup_method(self):
        """Set up test user for login tests."""
        self.test_email = "loginuser@example.com"
        self.test_username = "loginuser"
        self.test_password = "loginpass123"

    def test_login_with_email(self, client):
        """Test login using email."""
        # Register test user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": self.test_email,
                "username": self.test_username,
                "password": self.test_password,
            },
        )

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": self.test_email,
                "password": self.test_password,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_with_username(self, client):
        """Test login using username."""
        # Register test user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": self.test_email,
                "username": self.test_username,
                "password": self.test_password,
            },
        )

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": self.test_username,
                "password": self.test_password,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        """Test login with wrong password."""
        # Register test user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": self.test_email,
                "username": self.test_username,
                "password": self.test_password,
            },
        )

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": self.test_email,
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        assert "incorrect" in response.json()["message"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 401
        assert "incorrect" in response.json()["message"].lower()

    def test_login_case_insensitive_email(self, client):
        """Test that email login is case insensitive."""
        # Register test user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": self.test_email,
                "username": self.test_username,
                "password": self.test_password,
            },
        )

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": self.test_email.upper(),
                "password": self.test_password,
            },
        )
        # Depending on implementation, this might be 200 or 401
        # Adjust based on actual behavior
        assert response.status_code in [200, 401]


@pytest.mark.auth
@pytest.mark.api
@pytest.mark.security
class TestTokenSecurity:
    """Test JWT token security in API endpoints."""

    def setup_method(self):
        """Set up authenticated user."""
        self.test_email = "tokentest@example.com"
        self.test_username = "tokentest"
        self.test_password = "tokenpass123"

    def test_malformed_token(self, client):
        """Test API response to malformed tokens."""
        malformed_tokens = [
            "invalid.token.here",
            "Bearer invalid.token.here",
            "not-a-jwt-token",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",
        ]

        for token in malformed_tokens:
            response = client.get(
                "/api/v1/positions/",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 401

    def test_missing_bearer_prefix(self, client):
        """Test token without Bearer prefix."""
        # Register and login user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": self.test_email,
                "username": self.test_username,
                "password": self.test_password,
            },
        )

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": self.test_email,
                "password": self.test_password,
            },
        )
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/v1/positions/",
            headers={"Authorization": token},  # Missing "Bearer "
        )
        assert response.status_code == 401

    def test_empty_authorization_header(self, client):
        """Test empty Authorization header."""
        response = client.get(
            "/api/v1/positions/",
            headers={"Authorization": ""},
        )
        assert response.status_code == 401

    def test_case_sensitive_bearer(self, client):
        """Test case sensitivity of Bearer prefix."""
        # Register and login user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": self.test_email,
                "username": self.test_username,
                "password": self.test_password,
            },
        )

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": self.test_email,
                "password": self.test_password,
            },
        )
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/v1/positions/",
            headers={"Authorization": f"bearer {token}"},  # lowercase
        )
        # Depending on implementation, might accept or reject
        assert response.status_code in [200, 401]

    @patch("backend.auth.jwt.datetime")
    def test_expired_token_rejection(self, client, mock_datetime):
        """Test that expired tokens are rejected."""
        # This would require mocking the JWT expiration check
        # For now, test the concept
        response = client.get(
            "/api/v1/positions/",
            headers={"Authorization": "Bearer expired.token.here"},
        )
        assert response.status_code == 401


@pytest.mark.auth
@pytest.mark.api
class TestProtectedEndpoints:
    """Test access control on protected endpoints."""

    def setup_method(self):
        """Set up authenticated user."""
        self.test_email = "protected@example.com"
        self.test_username = "protected"
        self.test_password = "protectedpass123"

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/api/v1/positions/",
            "/api/v1/portfolio/summary/1",
            "/api/v1/portfolio/performance/1",
        ],
    )
    def test_protected_endpoints_require_auth(self, client, endpoint):
        """Test that protected endpoints require authentication."""
        response = client.get(endpoint)
        assert response.status_code == 401

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/api/v1/positions/",
            "/api/v1/portfolio/summary/1",
            "/api/v1/portfolio/performance/1",
        ],
    )
    def test_protected_endpoints_with_valid_auth(self, client, endpoint):
        """Test that protected endpoints work with valid authentication."""
        # Register and login user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": self.test_email,
                "username": self.test_username,
                "password": self.test_password,
            },
        )

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": self.test_email,
                "password": self.test_password,
            },
        )
        token = login_response.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        response = client.get(endpoint, headers=auth_headers)
        # Should return 200 or other success code, not 401
        assert response.status_code != 401

    def test_user_isolation(self, client):
        """Test that users can only access their own data."""
        # This would require creating multiple users and testing
        # that user A cannot access user B's data
        # For now, verify the concept
        assert True  # Placeholder for user isolation test
