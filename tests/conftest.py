"""Test configuration and fixtures."""

import os
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from faker import Faker


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment."""
    # Set test environment variables
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["REDIS_URL"] = "redis://localhost:6379/15"
    os.environ["SECRET_KEY"] = "test-secret-key-for-financial-dashboard"  # nosec
    os.environ["MCP_AUTH_TOKEN"] = "test-mcp-token"  # nosec
    os.environ["DEBUG"] = "true"


@pytest.fixture
def fake() -> Faker:
    """Faker instance for generating test data."""
    fake = Faker()
    fake.seed_instance(42)  # Deterministic data for consistent tests
    return fake


@pytest.fixture
def mock_database():
    """Mock database connection for tests."""
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    mock_db.fetch = AsyncMock()
    mock_db.fetchval = AsyncMock()
    mock_db.fetchrow = AsyncMock()
    return mock_db


@pytest.fixture
def mock_redis():
    """Mock Redis connection for tests."""
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock()
    mock_redis.set = AsyncMock()
    mock_redis.delete = AsyncMock()
    mock_redis.exists = AsyncMock()
    mock_redis.expire = AsyncMock()
    return mock_redis


@pytest.fixture
def mock_celery_task():
    """Mock Celery task for testing."""
    mock_task = MagicMock()
    mock_task.delay = MagicMock()
    mock_task.apply_async = MagicMock()
    mock_task.apply = MagicMock()
    return mock_task


@pytest.fixture
def sample_portfolio_data() -> dict[str, Any]:
    """Sample portfolio data for testing financial calculations."""
    return {
        "id": 1,
        "user_id": 1,
        "name": "Test Portfolio",
        "positions": [
            {
                "id": 1,
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "quantity": Decimal("100.00"),
                "purchase_price": Decimal("140.00"),
                "current_price": Decimal("150.00"),
                "total_value": Decimal("15000.00"),
                "total_cost": Decimal("14000.00"),
                "gain_loss": Decimal("1000.00"),
                "gain_loss_percent": Decimal("7.14"),
            },
            {
                "id": 2,
                "ticker": "GOOGL",
                "name": "Alphabet Inc.",
                "quantity": Decimal("50.00"),
                "purchase_price": Decimal("130.00"),
                "current_price": Decimal("140.00"),
                "total_value": Decimal("7000.00"),
                "total_cost": Decimal("6500.00"),
                "gain_loss": Decimal("500.00"),
                "gain_loss_percent": Decimal("7.69"),
            },
        ],
        "total_value": Decimal("22000.00"),
        "total_cost": Decimal("20500.00"),
        "total_gain": Decimal("1500.00"),
        "total_gain_percent": Decimal("7.32"),
    }


@pytest.fixture
def sample_asset_prices() -> dict[str, dict[str, Any]]:
    """Sample asset price data for testing market data functionality."""
    return {
        "AAPL": {
            "price": Decimal("150.00"),
            "change": Decimal("5.00"),
            "change_percent": Decimal("3.45"),
            "volume": 45678900,
            "market_cap": 2400000000000,
            "pe_ratio": Decimal("28.5"),
        },
        "GOOGL": {
            "price": Decimal("140.00"),
            "change": Decimal("-2.50"),
            "change_percent": Decimal("-1.75"),
            "volume": 23456700,
            "market_cap": 1800000000000,
            "pe_ratio": Decimal("22.1"),
        },
        "MSFT": {
            "price": Decimal("380.00"),
            "change": Decimal("10.00"),
            "change_percent": Decimal("2.70"),
            "volume": 34567800,
            "market_cap": 2800000000000,
            "pe_ratio": Decimal("31.2"),
        },
    }


@pytest.fixture
def sample_user_data(fake: Faker) -> dict[str, Any]:
    """Sample user data for testing authentication and authorization."""
    return {
        "id": 1,
        "email": fake.email(),
        "username": fake.user_name(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "is_active": True,
        "is_verified": True,
        "created_at": fake.date_time_this_year(),
        "last_login": fake.date_time_this_month(),
    }


@pytest.fixture
def sample_market_data_response() -> dict[str, Any]:
    """Sample market data API response for testing external integrations."""
    return {
        "status": "success",
        "data": {
            "AAPL": {
                "regularMarketPrice": 150.00,
                "regularMarketChange": 5.00,
                "regularMarketChangePercent": 3.45,
                "regularMarketVolume": 45678900,
                "marketCap": 2400000000000,
                "trailingPE": 28.5,
                "dividendYield": 0.52,
                "52WeekHigh": 199.62,
                "52WeekLow": 124.17,
            }
        },
        "timestamp": "2024-01-15T16:00:00Z",
    }


@pytest.fixture
def financial_calculation_test_cases() -> list[tuple[float, float, int, float]]:
    """Test cases for financial calculations with edge cases."""
    return [
        # (principal, rate, time, expected_compound_interest)
        (1000, 0.05, 1, 1050.0),
        (1000, 0.05, 2, 1102.5),
        (0, 0.05, 1, 0),  # Zero principal
        (1000, 0, 1, 1000),  # Zero interest rate
        (1000, 0.05, 0, 1000),  # Zero time
        (1000, -0.02, 1, 980.0),  # Negative interest rate
        (1000000, 0.001, 10, 1010045.02),  # Large principal, small rate
        (0.01, 1.0, 1, 0.02),  # Very small principal, high rate
    ]


@pytest.fixture
def mock_yfinance_response() -> MagicMock:
    """Mock yfinance API response for testing market data integration."""
    mock_ticker = MagicMock()
    mock_ticker.info = {
        "regularMarketPrice": 150.0,
        "regularMarketChange": 5.0,
        "regularMarketChangePercent": 3.45,
        "volume": 45678900,
        "marketCap": 2400000000000,
        "trailingPE": 28.5,
    }
    mock_ticker.history.return_value = MagicMock()
    return mock_ticker


@pytest.fixture
def error_test_cases() -> dict[str, dict[str, Any]]:
    """Test cases for error handling scenarios."""
    return {
        "invalid_ticker": {
            "ticker": "INVALID",
            "expected_error": "InvalidTickerError",
        },
        "negative_quantity": {
            "quantity": -10,
            "expected_error": "ValueError",
        },
        "zero_price": {
            "price": 0,
            "expected_error": "ValueError",
        },
        "invalid_date": {
            "date": "invalid-date",
            "expected_error": "ValueError",
        },
    }
