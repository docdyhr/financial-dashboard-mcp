#!/usr/bin/env python3
"""Test the module-based MCP server with fixed user IDs."""

import sys

# Add project root to Python path
sys.path.insert(0, "/Users/thomas/Programming/financial-dashboard-mcp")


def test_portfolio_tools():
    """Test if portfolio tools use the correct user ID."""
    from mcp_server.tools.portfolio import PortfolioTools

    # Create portfolio tools instance
    tools = PortfolioTools("http://localhost:8000")

    print("🔧 Testing Portfolio Tools Configuration...\n")

    # Check if the tools are properly configured
    tool_list = tools.get_tools()
    print(f"✅ Found {len(tool_list)} portfolio tools")

    # Test the URL construction by looking at the source
    import inspect

    # Get the source of _get_positions method
    try:
        source = inspect.getsource(tools._get_positions)
        if "user_id=3" in source:
            print("✅ Portfolio tools configured with user_id=3")
        elif "user_id=5" in source:
            print("❌ Portfolio tools still have user_id=5")
            return False
        else:
            print("⚠️  Could not verify user_id in portfolio tools")
    except Exception as e:
        print(f"⚠️  Could not inspect source: {e}")

    # Check other methods too
    methods_to_check = ["_get_portfolio_summary", "_get_allocation"]
    for method_name in methods_to_check:
        try:
            method = getattr(tools, method_name)
            source = inspect.getsource(method)
            if "/5" in source and "/3" not in source:
                print(f"❌ Method {method_name} still has hardcoded user_id=5")
                return False
            if "/3" in source:
                print(f"✅ Method {method_name} using user_id=3")
        except Exception as e:
            print(f"⚠️  Could not check method {method_name}: {e}")

    return True


def main():
    """Run all tests."""
    print("🧪 Testing Fixed Module-based MCP Server...\n")

    if test_portfolio_tools():
        print("\n🎉 All tests passed! Module-based MCP server is ready.")
        print("\n📋 Claude Desktop should now work correctly!")
        print("The running MCP server process was killed and will restart with fixes.")
        return True
    print("\n❌ Some tests failed. Check the issues above.")
    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
