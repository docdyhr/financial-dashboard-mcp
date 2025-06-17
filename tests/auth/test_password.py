"""Tests for password hashing and validation functionality."""

import pytest

from backend.auth.password import get_password_hash, verify_password


@pytest.mark.auth
@pytest.mark.security
@pytest.mark.unit
class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_password_hashing_basic(self):
        """Test basic password hashing functionality."""
        password = "test_password_123"
        hashed = get_password_hash(password)

        # Hash should be different from original password
        assert hashed != password

        # Hash should be verifiable
        assert verify_password(password, hashed) is True

    def test_password_verification_correct(self):
        """Test verification with correct password."""
        password = "correct_password"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_password_verification_incorrect(self):
        """Test verification with incorrect password."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_empty_password_handling(self):
        """Test handling of empty passwords."""
        empty_password = ""
        hashed = get_password_hash(empty_password)

        # Empty password should still hash
        assert hashed != ""
        assert verify_password(empty_password, hashed) is True
        assert verify_password("not_empty", hashed) is False

    def test_unicode_password_handling(self):
        """Test handling of unicode passwords."""
        unicode_password = "пароль123_测试"
        hashed = get_password_hash(unicode_password)

        assert verify_password(unicode_password, hashed) is True
        assert verify_password("different_unicode", hashed) is False

    def test_long_password_handling(self):
        """Test handling of long passwords within bcrypt limits."""
        # bcrypt has a 72-byte limit - test with password close to but under this limit
        long_password = "a" * 70  # Safe length for bcrypt
        hashed = get_password_hash(long_password)

        assert verify_password(long_password, hashed) is True
        assert verify_password(long_password + "b", hashed) is False

    def test_bcrypt_length_limit_awareness(self):
        """Test awareness of bcrypt's 72-byte limit."""
        # Test passwords at and beyond bcrypt's 72-byte limit
        password_72 = "a" * 72
        password_73 = "a" * 73

        hash_72 = get_password_hash(password_72)
        hash_73 = get_password_hash(password_73)

        # Both should verify correctly with their original passwords
        assert verify_password(password_72, hash_72) is True
        assert verify_password(password_73, hash_73) is True

        # Due to bcrypt's 72-byte limit, passwords longer than 72 bytes
        # might be truncated, so we can't guarantee different behavior
        # This test just ensures we can handle long passwords without crashing

    def test_special_characters_password(self):
        """Test passwords with special characters."""
        special_password = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        hashed = get_password_hash(special_password)

        assert verify_password(special_password, hashed) is True
        assert verify_password(special_password[:-1], hashed) is False

    def test_case_sensitive_passwords(self):
        """Test that password verification is case sensitive."""
        password = "CaseSensitive123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True
        assert verify_password(password.lower(), hashed) is False
        assert verify_password(password.upper(), hashed) is False

    def test_hash_determinism(self):
        """Test that same password produces different hashes (salt)."""
        password = "same_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different due to salt
        assert hash1 != hash2

        # Both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_hash_length_consistency(self):
        """Test that hash length is consistent."""
        passwords = [
            "short",
            "medium_length_password",
            "very_long_password_" + "x" * 100,
        ]
        hashes = [get_password_hash(pwd) for pwd in passwords]

        # All hashes should have the same length
        hash_lengths = [len(hash) for hash in hashes]
        assert len(set(hash_lengths)) == 1  # All lengths are the same

    def test_invalid_hash_handling(self):
        """Test verification with invalid hash format."""
        password = "test_password"
        invalid_hash = "not_a_valid_hash"

        # passlib raises an exception for invalid hash formats
        # This is expected behavior, so we test for the exception
        with pytest.raises(Exception):  # passlib raises UnknownHashError
            verify_password(password, invalid_hash)

    @pytest.mark.parametrize(
        "password",
        [
            "simple",
            "Complex123!",
            "with spaces",
            "with\ttabs\nand\nnewlines",
            "emoji_password_🔒",
            "123456789",
            "ALLUPPERCASE",
            "alllowercase",
        ],
    )
    def test_various_password_formats(self, password):
        """Test various password formats."""
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
        assert verify_password(password + "_modified", hashed) is False


@pytest.mark.auth
@pytest.mark.security
class TestPasswordSecurity:
    """Test password security aspects."""

    def test_timing_attack_resistance(self):
        """Test that verification time is consistent (basic timing attack resistance)."""
        import time

        password = "test_password"
        hashed = get_password_hash(password)
        wrong_password = "wrong_password"

        # Time correct verification
        start = time.time()
        verify_password(password, hashed)
        correct_time = time.time() - start

        # Time incorrect verification
        start = time.time()
        verify_password(wrong_password, hashed)
        incorrect_time = time.time() - start

        # Times should be relatively similar (within an order of magnitude)
        # This is a basic check - real timing attack resistance requires more sophisticated testing
        ratio = max(correct_time, incorrect_time) / min(correct_time, incorrect_time)
        assert (
            ratio < 10
        ), f"Timing difference too large: {correct_time:.6f} vs {incorrect_time:.6f}"

    def test_hash_strength(self):
        """Test that generated hashes appear random and strong."""
        password = "test_password"
        hashes = [get_password_hash(password) for _ in range(10)]

        # All hashes should be different
        assert len(set(hashes)) == 10

        # Hashes should contain various characters
        combined_hash = "".join(hashes)
        assert any(c.islower() for c in combined_hash)
        assert any(c.isupper() for c in combined_hash)
        assert any(c.isdigit() for c in combined_hash)

    def test_no_password_leakage_in_hash(self):
        """Test that password is not contained in the hash."""
        passwords = ["password123", "secret", "admin", "test"]

        for password in passwords:
            hashed = get_password_hash(password)
            # Password should not appear in hash
            assert password not in hashed
            assert password.upper() not in hashed.upper()
            assert password.lower() not in hashed.lower()
