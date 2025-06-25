#!/usr/bin/env python3
"""Test script for MCP server validation."""

import sys

import pytest
import requests


@pytest.mark.integration
def test_api_availability():
    """Test if the Financial Dashboard API is available."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Financial Dashboard API is running")
            assert True
            return
        print(f"❌ API returned status {response.status_code}")
        assert False, f"API returned status {response.status_code}"
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        assert False, f"Cannot connect to API: {e}"


@pytest.mark.integration
def test_mcp_server_import():
    """Test if MCP server can be imported."""
    try:
        import mcp_server.financial_dashboard_server  # noqa: F401

        print("✅ MCP server imports successfully")
        assert True
        return
    except ImportError as e:
        print(f"❌ MCP server import failed: {e}")
        assert False, f"MCP server import failed: {e}"


@pytest.mark.integration
def test_dependencies():
    """Test if required dependencies are available."""
    try:
        import httpx  # noqa: F401
        import mcp  # noqa: F401

        print("✅ All MCP dependencies available")
        assert True
        return
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        assert False, f"Missing dependencies: {e}"


def main():
    """Run all tests."""
    print("🧪 Testing MCP Server Setup...\n")

    tests = [
        ("Dependencies", test_dependencies),
        ("API Availability", test_api_availability),
        ("MCP Server Import", test_mcp_server_import),
    ]

    results = []
    for name, test_func in tests:
        print(f"Testing {name}...")
        result = test_func()
        results.append(result)
        print()

    if all(results):
        print("🎉 All tests passed! MCP server is ready for Claude Desktop.")
        print("\n📋 Next steps:")
        print("1. Copy claude_desktop_safe_mcp_config.json to Claude Desktop config")
        print("2. Restart Claude Desktop")
        print("3. Try: 'Show me my portfolio overview'")
    else:
        print("❌ Some tests failed. Check the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
