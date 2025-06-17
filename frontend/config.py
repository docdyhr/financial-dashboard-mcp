"""Centralized configuration for frontend components."""

import os

# Backend API configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_VERSION = "v1"
API_BASE_URL = f"{BACKEND_URL}/api/{API_VERSION}"

# Common API endpoints
ENDPOINTS = {
    "auth": {
        "login": f"{API_BASE_URL}/auth/login",
        "register": f"{API_BASE_URL}/auth/register",
        "me": f"{API_BASE_URL}/auth/me",
    },
    "portfolio": {
        "summary": f"{API_BASE_URL}/portfolio/summary",
        "positions": f"{API_BASE_URL}/positions",
        "transactions": f"{API_BASE_URL}/transactions",
        "cash_accounts": f"{API_BASE_URL}/cash-accounts",
    },
    "market_data": {
        "quote": f"{API_BASE_URL}/market-data/quote",
        "batch": f"{API_BASE_URL}/market-data/batch",
        "history": f"{API_BASE_URL}/market-data/history",
    },
    "isin": {
        "validate": f"{API_BASE_URL}/isin/validate",
        "search": f"{API_BASE_URL}/isin/search",
        "sync": f"{API_BASE_URL}/isin/sync",
    },
    "tasks": {
        "list": f"{API_BASE_URL}/tasks",
        "status": f"{API_BASE_URL}/tasks/status",
    },
}

# Request configuration
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Session configuration
SESSION_TIMEOUT = 3600  # 1 hour


def get_endpoint(category: str, action: str) -> str:
    """Get API endpoint URL."""
    return ENDPOINTS.get(category, {}).get(
        action, f"{API_BASE_URL}/{category}/{action}"
    )


def get_headers(token: str | None = None) -> dict:
    """Get common request headers."""
    headers = {
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers
