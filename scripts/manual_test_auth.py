#!/usr/bin/env python3
"""Test authentication flow."""

from pathlib import Path
import sys

import requests

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.auth.password import get_password_hash, verify_password
from backend.database import get_db_session
from backend.models.user import User


def test_auth_flow():
    """Test the complete authentication flow."""
    print("🧪 Testing Authentication Flow")
    print("=" * 50)

    # 1. Create a clean test user
    email = "test@financial-dashboard.com"
    password = "testpass123"

    with get_db_session() as db:
        # Remove existing test user
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            db.delete(existing_user)
            db.commit()
            print("🗑️  Removed existing test user")

        # Create new test user
        user = User(
            email=email,
            username="testuser",
            full_name="Test User",
            hashed_password=get_password_hash(password),
            is_active=True,
            is_verified=True,
            is_superuser=False,
            preferred_currency="USD",
            timezone="UTC",
        )
        db.add(user)
        db.commit()
        print(f"✅ Created test user: {email}")

        # Verify password works
        is_valid = verify_password(password, user.hashed_password)
        print(f"🔑 Password verification: {'✅ Success' if is_valid else '❌ Failed'}")

    # 2. Test API login
    print("\n🌐 Testing API login...")

    try:
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            data={
                "username": email,
                "password": password,
                "grant_type": "password",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=5,
        )

        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")

        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            print("✅ Login successful!")
            print(f"Token: {access_token[:50]}...")

            # Test /me endpoint
            print("\n👤 Testing /me endpoint...")
            headers = {"Authorization": f"Bearer {access_token}"}
            me_response = requests.get(
                "http://localhost:8000/api/v1/auth/me",
                headers=headers,
                timeout=5,
            )

            print(f"Me response status: {me_response.status_code}")
            if me_response.status_code == 200:
                user_info = me_response.json()
                print(f"✅ User info retrieved: {user_info.get('full_name')}")
            else:
                print(f"❌ Me endpoint failed: {me_response.text}")

        else:
            print(f"❌ Login failed: {response.text}")

    except Exception as e:
        print(f"❌ API test failed: {e}")


if __name__ == "__main__":
    test_auth_flow()
