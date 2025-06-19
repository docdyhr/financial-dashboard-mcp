#!/usr/bin/env python3
"""Simple API helper for Claude Desktop to access Financial Dashboard."""

import json
import sys

import requests


def main():
    """Main function to handle API requests."""
    if len(sys.argv) < 2:
        print("Usage: python claude_desktop_api_helper.py <endpoint> [method] [data]")
        return

    # Configuration
    BASE_URL = "http://localhost:8000"
    TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzIiwiZXhwIjoxNzUyODcxOTM2fQ.ThyBQ0AMuRHb9H7QzoBFf04pRIfxcBrEJ501CxW5FX0"
    USER_ID = 3

    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

    endpoint = sys.argv[1]
    method = sys.argv[2] if len(sys.argv) > 2 else "GET"

    # Handle common endpoints
    if endpoint == "health":
        url = f"{BASE_URL}/health"
    elif endpoint == "assets":
        url = f"{BASE_URL}/api/v1/assets/"
    elif endpoint == "positions":
        url = f"{BASE_URL}/api/v1/positions/?user_id={USER_ID}"
    elif endpoint == "transactions":
        url = f"{BASE_URL}/api/v1/transactions/?user_id={USER_ID}"
    elif endpoint == "overview":
        url = f"{BASE_URL}/api/v1/portfolio/summary/{USER_ID}"
    elif endpoint == "me":
        url = f"{BASE_URL}/api/v1/auth/me"
    else:
        url = f"{BASE_URL}{endpoint}"

    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == "POST":
            data = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
            response = requests.post(url, headers=headers, json=data, timeout=10)
        else:
            print(f"Unsupported method: {method}")
            return

        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error {response.status_code}: {response.text}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
