#!/usr/bin/env python3
"""Start the Financial Dashboard MCP Server."""

import argparse
import logging
import sys
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.main import FinancialDashboardMCP, main  # noqa: E402


def test_mcp_server():
    """Test if MCP server can initialize properly."""
    try:
        mcp_server = FinancialDashboardMCP()
        tool_count = len(mcp_server.all_tools)
        print(f"✅ MCP Server test successful: {tool_count} tools loaded")
        return True
    except Exception as e:
        print(f"❌ MCP Server test failed: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start Financial Dashboard MCP Server")
    parser.add_argument(
        "--test", action="store_true", help="Test MCP server initialization and exit"
    )
    args = parser.parse_args()

    if args.test:
        # Test mode - just verify MCP server can initialize
        success = test_mcp_server()
        time.sleep(1)  # Brief pause to allow service manager to detect
        sys.exit(0 if success else 1)

    # Normal mode - start MCP server
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
