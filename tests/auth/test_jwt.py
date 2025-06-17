"""Tests for JWT authentication functionality."""

from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt

from backend.auth.jwt import ALGORITHM, create_access_token, verify_token
from backend.config import get_settings

settings = get_settings()


@pytest.mark.auth
@pytest.mark.unit
class TestJWTFunctionality:
    """Test JWT token creation and verification."""

    def test_create_access_token_default_expiry(self):
        """Test creating access token with default expiry."""
        data = {"sub": "test@example.com", "user_id": 1}
        token = create_access_token(data)

        # Verify token can be decoded
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        assert payload["sub"] == "test@example.com"
        assert payload["user_id"] == 1
        assert "exp" in payload

        # Verify expiry is set correctly (within 1 minute of expected)
        expected_exp = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
        actual_exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        assert abs((expected_exp - actual_exp).total_seconds()) < 60

    def test_create_access_token_custom_expiry(self):
        """Test creating access token with custom expiry."""
        data = {"sub": "test@example.com"}
        custom_expiry = timedelta(hours=2)
        token = create_access_token(data, expires_delta=custom_expiry)

        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        expected_exp = datetime.now(UTC) + custom_expiry
        actual_exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        assert abs((expected_exp - actual_exp).total_seconds()) < 60

    def test_verify_valid_token(self):
        """Test verifying a valid token."""
        data = {"sub": "test@example.com", "user_id": 1}
        token = create_access_token(data)

        payload = verify_token(token)
        assert payload["sub"] == "test@example.com"
        assert payload["user_id"] == 1

    def test_verify_expired_token(self):
        """Test verifying an expired token."""
        data = {"sub": "test@example.com"}
        # Create token that expires immediately
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        with pytest.raises(ValueError, match="Invalid token"):
            verify_token(token)

    def test_verify_invalid_token(self):
        """Test verifying a malformed token."""
        invalid_token = "invalid.token.here"

        with pytest.raises(ValueError, match="Invalid token"):
            verify_token(invalid_token)

    def test_verify_token_wrong_secret(self):
        """Test verifying token with wrong secret."""
        data = {"sub": "test@example.com"}
        # Create token with different secret
        wrong_token = jwt.encode(data, "wrong_secret", algorithm=ALGORITHM)

        with pytest.raises(ValueError, match="Invalid token"):
            verify_token(wrong_token)

    def test_verify_token_missing_username(self):
        """Test verifying token without username."""
        data = {"user_id": 1}  # Missing "sub" field
        token = create_access_token(data)

        # This should still work - the actual validation happens in dependencies
        payload = verify_token(token)
        assert payload["user_id"] == 1

    @pytest.mark.parametrize("algorithm", ["HS256", "HS512"])
    def test_different_algorithms(self, algorithm):
        """Test JWT with different algorithms."""
        data = {"sub": "test@example.com"}
        token = jwt.encode(data, settings.secret_key, algorithm=algorithm)

        # Should fail with wrong algorithm expectation if using different algorithm
        if algorithm != ALGORITHM:
            with pytest.raises(ValueError):
                verify_token(token)
        else:
            # Should work with correct algorithm
            payload = verify_token(token)
            assert payload["sub"] == "test@example.com"


@pytest.mark.auth
@pytest.mark.security
class TestJWTSecurity:
    """Test JWT security aspects."""

    def test_token_contains_no_sensitive_data(self):
        """Test that tokens don't contain sensitive data."""
        data = {"sub": "test@example.com", "user_id": 1}
        token = create_access_token(data)

        # Decode without verification to check payload
        payload = jwt.decode(
            token, key="", algorithms=[ALGORITHM], options={"verify_signature": False}
        )

        # Ensure no sensitive fields are in the payload
        sensitive_fields = ["password", "hashed_password", "secret", "key"]
        for field in sensitive_fields:
            assert field not in payload

    def test_token_uniqueness(self):
        """Test that identical data produces different tokens due to timestamps."""
        data = {"sub": "test@example.com"}
        token1 = create_access_token(data)

        # Small delay to ensure different timestamp
        import time

        time.sleep(1)  # Increase delay to 1 second to ensure different timestamps

        token2 = create_access_token(data)
        assert token1 != token2

    def test_token_cannot_be_modified(self):
        """Test that modifying token payload invalidates it."""
        data = {"sub": "test@example.com", "user_id": 1}
        token = create_access_token(data)

        # Attempt to modify the payload
        parts = token.split(".")
        modified_payload = parts[1].replace("1", "2")  # Change user_id
        modified_token = f"{parts[0]}.{modified_payload}.{parts[2]}"

        with pytest.raises(Exception):
            verify_token(modified_token, credentials_exception=Exception("Invalid"))
