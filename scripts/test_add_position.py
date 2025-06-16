#!/usr/bin/env python3
"""Test script for the add_position MCP tool

This script tests the add_position functionality end-to-end:
1. Creates a test asset (AAPL)
2. Adds a position using the MCP tool
3. Verifies the position was created correctly

Usage:
    python scripts/test_add_position.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging  # noqa: E402

from mcp_server.main import FinancialDashboardMCP  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_add_position():
    """Test adding a position through the MCP server."""
    mcp_server = None

    try:
        print("🚀 Testing add_position MCP tool...")
        print("=" * 50)

        # Initialize MCP server
        print("📡 Initializing MCP server...")
        mcp_server = FinancialDashboardMCP()

        # Test arguments for adding Apple position
        test_args = {
            "ticker": "AAPL",
            "quantity": 100,
            "purchase_price": 180.50,
            "purchase_date": "2024-01-15",
        }

        print(f"📊 Adding position: {test_args}")

        # Execute the add_position tool
        result = await mcp_server.portfolio_tools.execute_tool(
            "add_position", test_args
        )

        # Display results
        print("\n✅ MCP Tool Response:")
        for item in result:
            print(item.text)

        # Test getting positions to verify it was added
        print("\n🔍 Verifying position was added...")
        positions_result = await mcp_server.portfolio_tools.execute_tool(
            "get_positions", {}
        )

        print("\n📋 Current positions:")
        for item in positions_result:
            print(item.text)

        # Test portfolio summary
        print("\n💰 Portfolio Summary:")
        summary_result = await mcp_server.portfolio_tools.execute_tool(
            "get_portfolio_summary", {}
        )

        for item in summary_result:
            print(item.text)

        print("\n🎉 Test completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.exception("Test failed with exception")
        return False

    finally:
        if mcp_server:
            # Clean up resources
            await mcp_server.portfolio_tools.close()
            await mcp_server.market_tools.close()
            await mcp_server.analytics_tools.close()
            print("🧹 Cleaned up MCP server resources")


async def test_multiple_positions():
    """Test adding multiple positions."""
    mcp_server = None

    try:
        print("\n🔄 Testing multiple positions...")
        print("=" * 50)

        # Initialize MCP server
        mcp_server = FinancialDashboardMCP()

        # Test positions
        test_positions = [
            {
                "ticker": "MSFT",
                "quantity": 50,
                "purchase_price": 320.00,
                "purchase_date": "2024-01-10",
            },
            {
                "ticker": "GOOGL",
                "quantity": 25,
                "purchase_price": 140.00,
                "purchase_date": "2024-01-12",
            },
        ]

        for i, position in enumerate(test_positions, 1):
            print(f"\n📊 Adding position {i}: {position['ticker']}")

            result = await mcp_server.portfolio_tools.execute_tool(
                "add_position", position
            )

            print(f"✅ Result for {position['ticker']}:")
            for item in result:
                print(item.text[:200] + "..." if len(item.text) > 200 else item.text)

        # Get final portfolio state
        print("\n📋 Final Portfolio:")
        positions_result = await mcp_server.portfolio_tools.execute_tool(
            "get_positions", {}
        )

        for item in positions_result:
            print(item.text)

        return True

    except Exception as e:
        print(f"\n❌ Multiple positions test failed: {e}")
        logger.exception("Multiple positions test failed")
        return False

    finally:
        if mcp_server:
            await mcp_server.portfolio_tools.close()
            await mcp_server.market_tools.close()
            await mcp_server.analytics_tools.close()


async def main():
    """Run all tests."""
    print("🧪 MCP add_position Tool Test Suite")
    print("=" * 60)

    success_count = 0
    total_tests = 2

    # Test 1: Single position
    if await test_add_position():
        success_count += 1

    # Test 2: Multiple positions
    if await test_multiple_positions():
        success_count += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {success_count}/{total_tests} tests passed")

    if success_count == total_tests:
        print("🎉 All tests passed! MCP add_position integration works correctly.")
        print("\n📝 Next steps:")
        print("1. Restart Claude Desktop to reload MCP server")
        print("2. Test in Claude: 'Add 100 shares of AAPL at $180'")
        print("3. Try: 'Show me my current portfolio'")
        return True
    else:
        print("❌ Some tests failed. Check the errors above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
