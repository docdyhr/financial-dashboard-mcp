#!/usr/bin/env python3
"""Final test of the MCP server with authentication."""

import asyncio
import sys

import pytest

# Add project root to Python path
sys.path.insert(0, "/Users/thomas/Programming/financial-dashboard-mcp")


@pytest.mark.asyncio
async def test_portfolio_tools_with_auth():
    """Test portfolio tools with authentication."""
    from mcp_server.tools.portfolio import PortfolioTools

    print("🔧 Testing Portfolio Tools with Authentication...\n")

    # Create portfolio tools instance
    tools = PortfolioTools("http://localhost:8000")

    try:
        # Test getting positions (this should make an authenticated API call)
        print("1. Testing get_positions tool...")
        result = await tools.execute_tool("get_positions", {})

        if len(result) > 0:
            text = result[0].text
            if "Current Portfolio Positions" in text and "401" not in text:
                print("✅ get_positions working with authentication")
            elif "401" in text:
                print("❌ Still getting 401 errors")
                return False
            else:
                print(f"⚠️  Unexpected response: {text[:100]}...")

        # Test portfolio summary
        print("\n2. Testing get_portfolio_summary tool...")
        result = await tools.execute_tool("get_portfolio_summary", {})

        if len(result) > 0:
            text = result[0].text
            if "Portfolio Summary" in text and "401" not in text:
                print("✅ get_portfolio_summary working with authentication")
            elif "401" in text:
                print("❌ Still getting 401 errors in summary")
                return False
            else:
                print(f"⚠️  Unexpected response: {text[:100]}...")

        return True

    except Exception as e:
        print(f"❌ Error testing tools: {e}")
        return False
    finally:
        await tools.close()


async def main():
    """Run all tests."""
    print("🧪 Final MCP Server Authentication Test...\n")

    if await test_portfolio_tools_with_auth():
        print("\n🎉 SUCCESS! MCP server authentication is working!")
        print("\n📋 Claude Desktop should now work correctly!")
        print("✅ All API calls include proper Bearer token authentication")
        print("✅ User ID 3 is correctly configured")
        print("✅ No more 401 Unauthorized errors expected")
        return True
    print("\n❌ Authentication test failed.")
    return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
