"""Test configuration and fixtures."""
import os
from unittest.mock import MagicMock

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment."""
    # Set test environment variables
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ[
        "REDIS_URL"
    ] = "redis://localhost:6379/15"  # Use separate Redis DB for tests
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["MCP_AUTH_TOKEN"] = "test-token"


@pytest.fixture
def mock_database():
    """Mock database connection for tests."""
    return MagicMock()


@pytest.fixture
def mock_redis():
    """Mock Redis connection for tests."""
    return MagicMock()


@pytest.fixture
def sample_portfolio_data():
    """Sample portfolio data for testing."""
    return {
        "positions": [
            {
                "id": 1,
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "quantity": 100,
                "purchase_price": 140.00,
                "current_price": 150.00,
                "total_value": 15000.00,
            },
            {
                "id": 2,
                "ticker": "GOOGL",
                "name": "Alphabet Inc.",
                "quantity": 50,
                "purchase_price": 130.00,
                "current_price": 140.00,
                "total_value": 7000.00,
            },
        ],
        "total_value": 22000.00,
        "total_cost": 20000.00,
        "total_gain": 2000.00,
        "total_gain_percent": 10.0,
    }


@pytest.fixture
def sample_asset_prices():
    """Sample asset price data for testing."""
    return {
        "AAPL": {"price": 150.00, "change": 5.00, "change_percent": 3.45},
        "GOOGL": {"price": 140.00, "change": -2.50, "change_percent": -1.75},
        "MSFT": {"price": 380.00, "change": 10.00, "change_percent": 2.70},
    }
