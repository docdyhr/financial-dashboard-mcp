#!/usr/bin/env python3
"""MCP Server Entry Point for Financial Dashboard

This script serves as the main entry point for the Financial Dashboard MCP server.
It ensures proper environment setup and handles graceful startup/shutdown.
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.main import main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),
    ],
)

logger = logging.getLogger(__name__)


def check_environment():
    """Check if the environment is properly configured."""
    required_modules = ["mcp", "fastapi", "sqlalchemy", "redis", "celery"]
    missing_modules = []

    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)

    if missing_modules:
        logger.error(f"Missing required modules: {', '.join(missing_modules)}")
        logger.error("Please install dependencies with: pip install -e .")
        return False

    return True


def main_entry():
    """Main entry point with error handling."""
    try:
        # Check environment
        if not check_environment():
            sys.exit(1)

        logger.info("Starting Financial Dashboard MCP Server...")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Project root: {project_root}")

        # Run the async main function
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main_entry()
