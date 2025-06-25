#!/usr/bin/env python3
"""MCP Server __main__.py module for Financial Dashboard

This module allows the MCP server to be executed with:
python -m mcp_server

It provides a clean entry point with proper error handling and logging.
"""

import asyncio
import logging
import os
from pathlib import Path
import sys

# Ensure the project root is in the Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configure logging to stderr so it doesn't interfere with MCP protocol
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)

logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if all required dependencies are available."""
    required_packages = [
        ("mcp", "MCP protocol library"),
        ("fastapi", "FastAPI web framework"),
        ("sqlalchemy", "SQLAlchemy ORM"),
        ("redis", "Redis client"),
        ("celery", "Celery task queue"),
        ("streamlit", "Streamlit framework"),
        ("yfinance", "Yahoo Finance data"),
        ("psycopg2", "PostgreSQL adapter"),
    ]

    missing_packages = []

    for package, description in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(f"{package} ({description})")

    if missing_packages:
        logger.error("Missing required dependencies:")
        for package in missing_packages:
            logger.error(f"  - {package}")
        logger.error("Please install dependencies with: pip install -e .")
        return False

    return True


def setup_environment():
    """Setup environment variables and configuration."""
    # Load .env file if it exists
    env_file = project_root / ".env"
    if env_file.exists():
        logger.info(f"Loading environment from {env_file}")
        try:
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ.setdefault(key.strip(), value.strip())
        except Exception as e:
            logger.warning(f"Error loading .env file: {e}")

    # Set default values
    os.environ.setdefault("BACKEND_URL", "http://localhost:8000")
    os.environ.setdefault("MCP_SERVER_HOST", "localhost")
    os.environ.setdefault("MCP_SERVER_PORT", "8502")
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ.setdefault("LOG_LEVEL", "INFO")

    # Add project root to Python path
    pythonpath = os.environ.get("PYTHONPATH", "")
    if str(project_root) not in pythonpath:
        os.environ["PYTHONPATH"] = (
            f"{project_root}:{pythonpath}" if pythonpath else str(project_root)
        )


async def main():
    """Main entry point for the MCP server."""
    try:
        logger.info("=" * 60)
        logger.info("Financial Dashboard MCP Server Starting")
        logger.info("=" * 60)
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Project root: {project_root}")
        logger.info(f"Working directory: {os.getcwd()}")

        # Check dependencies
        logger.info("Checking dependencies...")
        if not check_dependencies():
            logger.error("Dependency check failed. Exiting.")
            return 1

        # Setup environment
        logger.info("Setting up environment...")
        setup_environment()

        logger.info(f"Backend URL: {os.getenv('BACKEND_URL')}")
        logger.info(f"Environment: {os.getenv('ENVIRONMENT')}")
        logger.info(f"Log level: {os.getenv('LOG_LEVEL')}")

        # Import and run the main MCP server
        logger.info("Importing MCP server components...")
        from mcp_server.main import main as mcp_main

        logger.info("Starting MCP server...")
        await mcp_main()

        return 0

    except KeyboardInterrupt:
        logger.info("Received interrupt signal. Shutting down gracefully...")
        return 0
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error(
            "Make sure all dependencies are installed and the project is properly set up."
        )
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


def run():
    """Synchronous wrapper for the async main function."""
    try:
        return asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = run()
    sys.exit(exit_code)
