#!/usr/bin/env python3
"""Check user credentials in database."""

from pathlib import Path
import sys

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.auth.password import verify_password
from backend.database import get_db_session
from backend.models.user import User


def check_user():
    """Check user in database."""
    with get_db_session() as db:
        user = db.query(User).filter(User.email == "user@example.com").first()

        if user:
            print("✅ User found:")
            print(f"   Email: {user.email}")
            print(f"   Username: {user.username}")
            print(f"   Full Name: {user.full_name}")
            print(f"   Active: {user.is_active}")
            print(f"   Hash: {user.hashed_password[:50]}...")

            # Test password verification
            test_passwords = ["demo123", "testpassword123", "password"]
            for password in test_passwords:
                is_valid = verify_password(password, user.hashed_password)
                print(
                    f"   Password '{password}': {'✅ Valid' if is_valid else '❌ Invalid'}"
                )
        else:
            print("❌ User not found!")


if __name__ == "__main__":
    check_user()
