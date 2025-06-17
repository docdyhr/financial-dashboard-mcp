"""Security utilities for configuration and secret management."""

import secrets
import string
from pathlib import Path


def generate_secret_key(length: int = 32) -> str:
    """Generate a cryptographically secure secret key."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_simple_password(length: int = 16) -> str:
    """Generate a secure password without ambiguous characters."""
    # Exclude ambiguous characters: 0, O, l, I
    alphabet = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ123456789!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_env_file(env_path: Path = Path(".env")) -> None:
    """Create a secure .env file with generated secrets."""
    if env_path.exists():
        print(f"Warning: {env_path} already exists. Skipping creation.")
        return

    secret_key = generate_secret_key(64)
    flower_password = generate_simple_password(20)
    mcp_auth_token = generate_secret_key(32)

    env_content = f"""# Financial Dashboard Environment Configuration
# Generated automatically - DO NOT COMMIT TO VERSION CONTROL

# Environment
ENVIRONMENT=development

# Security
SECRET_KEY={secret_key}

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/financial_dashboard

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# API Keys (obtain from providers)
ALPHA_VANTAGE_API_KEY=
FINNHUB_API_KEY=

# Flower UI
FLOWER_USERNAME=admin
FLOWER_PASSWORD={flower_password}

# MCP Server
MCP_AUTH_TOKEN={mcp_auth_token}

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:8501,http://localhost:3000
"""

    env_path.write_text(env_content)
    env_path.chmod(0o600)  # Restrict permissions to owner only
    print(f"Created {env_path} with secure defaults")
    print("Please update DATABASE_URL and API keys as needed")


def validate_production_config() -> list[str]:
    """Validate configuration for production deployment."""
    import os

    errors = []

    # Check critical environment variables
    if not os.getenv("SECRET_KEY"):
        errors.append("SECRET_KEY environment variable is not set")

    if os.getenv("SECRET_KEY") and len(os.getenv("SECRET_KEY", "")) < 32:
        errors.append("SECRET_KEY is too short (minimum 32 characters)")

    if not os.getenv("DATABASE_URL"):
        errors.append("DATABASE_URL environment variable is not set")

    if os.getenv("ENVIRONMENT") == "production":
        if os.getenv("DEBUG", "false").lower() == "true":
            errors.append("DEBUG must be false in production")

        if not os.getenv("FLOWER_PASSWORD"):
            errors.append("FLOWER_PASSWORD must be set in production")

        # Check for insecure defaults
        if "localhost" in os.getenv("DATABASE_URL", ""):
            errors.append("DATABASE_URL contains 'localhost' in production")

        if "localhost" in os.getenv("REDIS_URL", ""):
            errors.append("REDIS_URL contains 'localhost' in production")

    return errors


if __name__ == "__main__":
    # Generate example configuration
    create_env_file(Path(".env.example"))
    print("\nExample secret key:", generate_secret_key())
    print("Example password:", generate_simple_password())
