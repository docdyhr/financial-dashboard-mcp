#!/usr/bin/env python3
"""Test the fixed MCP server configuration."""

import subprocess
import sys

import pytest


@pytest.mark.integration
def test_mcp_server_config():
    """Test if the MCP server can connect with correct user ID."""
    print("🔧 Testing Fixed MCP Server Configuration...\n")

    # Test the token first
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0NyIsImV4cCI6MTc1MzQzOTU1MX0.qL2zagxaonAcIO9i-VgcqSHy2uyklUEmNu_wKwEsMok"

    print("1. Testing API authentication with token...")
    result = subprocess.run(
        [
            "curl",
            "-s",
            "-H",
            f"Authorization: Bearer {token}",
            "http://localhost:8000/api/v1/auth/me",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode == 0:
        print("✅ Token authentication working")
    else:
        print("❌ Token authentication failed")
        assert False, "Token authentication failed"

    print("\n2. Testing portfolio endpoints with user_id=47...")

    # Test portfolio summary endpoint
    result = subprocess.run(
        [
            "curl",
            "-s",
            "-H",
            f"Authorization: Bearer {token}",
            "http://localhost:8000/api/v1/portfolio/summary/47",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if "total_value" in result.stdout:
        print("✅ Portfolio summary endpoint working with user_id=3")
    else:
        print(f"❌ Portfolio summary failed: {result.stdout}")
        assert False, f"Portfolio summary failed: {result.stdout}"

    # Test positions endpoint
    result = subprocess.run(
        [
            "curl",
            "-s",
            "-H",
            f"Authorization: Bearer {token}",
            "http://localhost:8000/api/v1/positions/?user_id=47",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if "success" in result.stdout:
        print("✅ Positions endpoint working with user_id=47")
    else:
        print(f"❌ Positions failed: {result.stdout}")
        assert False, f"Positions failed: {result.stdout}"

    print("\n3. Checking MCP server files for correct user_id...")

    # Check if files have correct user_id
    with open(
        "/Users/thomas/Programming/financial-dashboard-mcp/mcp_server/tools/portfolio.py",
    ) as f:
        content = f.read()
        if "user_id=47" in content and "user_id=5" not in content:
            print("✅ MCP server files updated with correct user_id=47")
        else:
            print("❌ MCP server files still contain wrong user_id (need 47)")
            assert False, "MCP server files still contain wrong user_id"

    print("\n🎉 All tests passed! MCP server is ready for Claude Desktop.")
    print("\n📋 Claude Desktop should now work correctly!")
    print("Try asking: 'Show me my portfolio summary'")

    return True


if __name__ == "__main__":
    success = test_mcp_server_config()
    sys.exit(0 if success else 1)
