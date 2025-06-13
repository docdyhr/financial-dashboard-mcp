#!/usr/bin/env python3
"""Start the Financial Dashboard MCP Server."""

import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.main import main

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    import asyncio

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMCP Server stopped.")
    except Exception as e:
        print(f"Error starting MCP server: {e}")
        sys.exit(1)
