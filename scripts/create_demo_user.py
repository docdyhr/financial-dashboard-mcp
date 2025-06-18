#!/usr/bin/env python3
"""Create or update demo user with known credentials."""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.auth.password import get_password_hash
from backend.database import get_db_session
from backend.models.user import User


def create_demo_user():
    """Create or update demo user with known credentials."""
    print("🔧 Setting up demo user credentials...")

    with get_db_session() as db:
        # Check if user exists
        user = db.query(User).filter(User.email == "user@example.com").first()

        if user:
            print(f"✅ Found existing user: {user.email}")
            # Update password
            user.hashed_password = get_password_hash("demo123")
            user.is_active = True
            user.is_verified = True
            print("🔑 Updated password to 'demo123'")
        else:
            # Create new user
            user = User(
                email="user@example.com",
                username="demo",
                full_name="Demo User",
                hashed_password=get_password_hash("demo123"),
                is_active=True,
                is_verified=True,
                is_superuser=False,
                preferred_currency="USD",
                timezone="UTC",
            )
            db.add(user)
            print("✅ Created new demo user")

        db.commit()

        print("\n📋 Demo User Credentials:")
        print(f"   Email: {user.email}")
        print(f"   Username: {user.username}")
        print("   Password: demo123")
        print(f"   Full Name: {user.full_name}")
        print(f"   Active: {user.is_active}")
        print(f"   Verified: {user.is_verified}")


if __name__ == "__main__":
    create_demo_user()
