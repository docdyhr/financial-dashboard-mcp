#!/usr/bin/env python3
"""Test script to verify Claude Desktop can access the Financial Dashboard API."""

import json

import requests
from rich.console import Console

console = Console()

# Load configuration
with open("claude_desktop_config.json") as f:
    config = json.load(f)

api_config = config["financial_dashboard"]
base_url = api_config["base_url"]
token = api_config["auth"]["token"]
user_id = api_config["auth"]["user_id"]

# Set up session with authentication
session = requests.Session()
session.headers.update(
    {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
)


def test_endpoints():
    """Test all available endpoints."""
    console.print("🧪 Testing Claude Desktop API Access", style="bold blue")

    tests = [
        ("Health Check", "GET", "/health", None),
        ("User Info", "GET", "/api/v1/auth/me", None),
        ("List Assets", "GET", "/api/v1/assets/", None),
        ("Get Positions", "GET", f"/api/v1/positions/?user_id={user_id}", None),
        ("Get Transactions", "GET", f"/api/v1/transactions/?user_id={user_id}", None),
    ]

    results = []

    for test_name, method, endpoint, data in tests:
        try:
            url = f"{base_url}{endpoint}"

            if method == "GET":
                response = session.get(url)
            elif method == "POST":
                response = session.post(url, json=data)

            if response.status_code == 200:
                console.print(f"✅ {test_name}: SUCCESS", style="green")
                results.append((test_name, True, response.json()))
            else:
                console.print(
                    f"❌ {test_name}: FAILED ({response.status_code})", style="red"
                )
                results.append((test_name, False, response.text))

        except Exception as e:
            console.print(f"❌ {test_name}: ERROR ({e})", style="red")
            results.append((test_name, False, str(e)))

    # Summary
    successful = sum(1 for _, success, _ in results if success)
    total = len(results)

    console.print(f"\n📊 Test Results: {successful}/{total} passed", style="bold")

    if successful == total:
        console.print(
            "🎉 Claude Desktop API access is working perfectly!", style="bold green"
        )

        # Show sample data
        console.print("\n📋 Sample API Responses:", style="bold")
        for test_name, success, data in results:
            if success and test_name == "List Assets":
                assets = data.get("data", [])
                console.print(f"  Assets available: {len(assets)}")
                if assets:
                    console.print(
                        f"  First asset: {assets[0].get('ticker')} - {assets[0].get('name')}"
                    )

            elif success and test_name == "Get Positions":
                positions = data.get("data", [])
                console.print(f"  Positions: {len(positions)}")

    else:
        console.print("⚠️ Some tests failed. Check the errors above.", style="yellow")

    return successful == total


if __name__ == "__main__":
    success = test_endpoints()

    if success:
        console.print("\n🔗 Claude Desktop Connection Info:", style="bold blue")
        console.print(f"  Base URL: {base_url}")
        console.print(f"  User ID: {user_id}")
        console.print(f"  Token: {token[:50]}...")

        console.print(
            "\n💡 You can now use these endpoints in Claude Desktop:", style="bold"
        )
        console.print("  - Ask about portfolio performance")
        console.print("  - Request asset information")
        console.print("  - Create transactions")
        console.print("  - Get portfolio analytics")
