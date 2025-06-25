#!/usr/bin/env python3
"""Create Default User for MCP Integration

This script creates a default user (ID=1) for single-user MCP integration.
The Financial Dashboard MCP expects a user_id=1 to exist for API calls.

Usage:
    python scripts/create_default_user.py
"""

from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime
import hashlib
import logging
import secrets
import string

from backend.database import get_db_session
from backend.models.user import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_secure_password(length: int = 16) -> str:
    """Generate a cryptographically secure password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_default_user():
    """Create a default user for MCP integration."""
    try:
        with get_db_session() as db:
            # Check if user with ID 1 already exists
            existing_user = db.query(User).filter(User.id == 1).first()

            if existing_user:
                logger.info(
                    f"Default user already exists: {existing_user.username} ({existing_user.email})"
                )
                logger.info("MCP integration can now use user_id=1")
                return existing_user

            # Check if any user with the default email exists
            existing_email_user = (
                db.query(User)
                .filter(User.email == "mcp@financial-dashboard.local")
                .first()
            )

            if existing_email_user:
                logger.info(
                    f"User with MCP email already exists with ID {existing_email_user.id}"
                )
                logger.info("MCP integration should use this user_id")
                return existing_email_user

            # Generate secure password
            password = generate_secure_password()
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            # Create the user directly
            new_user = User(
                email="mcp@financial-dashboard.local",
                username="mcp_user",
                full_name="MCP Integration User",
                hashed_password=hashed_password,
                is_active=True,
                is_verified=True,
                preferred_currency="USD",
                timezone="UTC",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            # Add to database
            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            logger.info("✅ Created default user:")
            logger.info(f"   ID: {new_user.id}")
            logger.info(f"   Username: {new_user.username}")
            logger.info(f"   Email: {new_user.email}")
            logger.info(f"   Active: {new_user.is_active}")
            logger.info("")
            logger.info("🎉 MCP integration can now use this user for API calls!")
            logger.info("")
            logger.info("🔒 SECURITY NOTE:")
            logger.info(f"   Generated secure password: {password}")
            logger.info("   Store this password securely - it won't be shown again.")
            logger.info("   Password is hashed in the database for security.")

            return new_user

    except ImportError as e:
        logger.error("❌ Import error: %s", e)
        logger.error(
            "Make sure you have run 'make install-dev' to install dependencies"
        )
        return None
    except Exception as e:
        logger.error(f"❌ Error creating default user: {e}")
        logger.error("Make sure the database is running and migrations are applied")
        logger.error("Try running: make migrate-up")
        return None


def check_user_access():
    """Check if the default user can be accessed by the API."""
    try:
        import httpx

        # Test the API endpoint that MCP will use
        with httpx.Client() as client:
            response = client.get("http://localhost:8000/api/v1/positions/?user_id=1")

            if response.status_code == 200:
                logger.info("✅ API access test passed - MCP integration should work!")
                return True
            if (
                response.status_code == 404
                and "User with ID 1 not found" in response.text
            ):
                logger.warning("⚠️  User exists in database but API can't find it")
                logger.warning("This might be a database/API connection issue")
                return False
            logger.info(f"📊 API response: {response.status_code}")
            logger.info("This is expected if the user has no positions yet")
            return True

    except Exception as e:
        logger.warning(f"⚠️  Could not test API access: {e}")
        logger.warning("Make sure the backend is running: make run-backend")
        return False


if __name__ == "__main__":
    print("🚀 Creating default user for MCP integration...\n")

    user = create_default_user()

    if user:
        print("\n🧪 Testing API access...")
        check_user_access()

        print("\n✨ Setup complete!")
        print(f"MCP tools can now access the API using user_id={user.id}")
        print("\nNext steps:")
        print("1. Restart Claude Desktop to reload MCP server")
        print("2. Try: 'Show me my current portfolio'")
        print("3. Add positions: 'Add 100 shares of AAPL at $180'")
    else:
        print("\n❌ Failed to create default user")
        print("Check the error messages above for troubleshooting steps")
        sys.exit(1)
