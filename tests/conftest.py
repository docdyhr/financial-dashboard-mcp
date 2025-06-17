"""Test configuration and fixtures."""

import os
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models import Base


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that test individual components in isolation"
    )
    config.addinivalue_line(
        "markers",
        "integration: Integration tests that test multiple components together",
    )
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "frontend: Frontend component tests")
    config.addinivalue_line(
        "markers", "slow: Tests that take more than 5 seconds to run"
    )
    config.addinivalue_line("markers", "fast: Tests that run quickly (under 1 second)")
    config.addinivalue_line("markers", "database: Tests that require database access")
    config.addinivalue_line("markers", "external: Tests that make external API calls")
    config.addinivalue_line("markers", "benchmark: Performance benchmark tests")
    config.addinivalue_line(
        "markers", "smoke: Basic smoke tests for critical functionality"
    )
    config.addinivalue_line(
        "markers", "financial: Tests for financial calculations and data tests"
    )
    config.addinivalue_line("markers", "security: Security-related tests")
    config.addinivalue_line(
        "markers", "isin: Tests specifically for ISIN functionality"
    )
    config.addinivalue_line("markers", "portfolio: Tests for portfolio functionality")
    config.addinivalue_line(
        "markers", "market_data: Tests for market data functionality"
    )
    config.addinivalue_line("markers", "auth: Authentication and authorization tests")
    config.addinivalue_line("markers", "performance: Performance and load tests")
    config.addinivalue_line("markers", "celery: Tests for Celery background tasks")
    config.addinivalue_line("markers", "redis: Tests that require Redis")
    config.addinivalue_line("markers", "cash: Tests for cash account functionality")
    config.addinivalue_line("markers", "e2e: End-to-end integration tests")


def pytest_addoption(parser):
    """Add custom command line options for pytest."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run integration tests that require external services",
    )


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


@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    return create_engine("sqlite:///:memory:", echo=False)


@pytest.fixture(scope="session")
def tables(engine):
    """Create all tables for testing."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(engine, tables):
    """Create a database session for testing."""
    connection = engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


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


@pytest.fixture
def sample_isin_data() -> dict[str, Any]:
    """Sample ISIN data for testing ISIN functionality."""
    return {
        "valid_isins": [
            "US0378331005",  # Apple Inc.
            "DE0007164600",  # SAP SE
            "GB0002162385",  # BP plc
            "FR0000120073",  # Airbus SE
            "NL0011794037",  # ASML Holding N.V.
            "CH0012005267",  # Nestlé S.A.
        ],
        "invalid_isins": [
            "US037833100",  # Too short
            "US0378331006",  # Invalid check digit
            "123456789012",  # Invalid format
            "US03783310AB",  # Invalid characters
            "",  # Empty string
            "INVALIDFORMAT",  # Wrong format
        ],
        "isin_mappings": {
            "US0378331005": {
                "ticker": "AAPL",
                "exchange": "XNAS",
                "name": "Apple Inc.",
                "country": "US",
                "currency": "USD",
            },
            "DE0007164600": {
                "ticker": "SAP",
                "exchange": "XETR",
                "name": "SAP SE",
                "country": "DE",
                "currency": "EUR",
            },
            "GB0002162385": {
                "ticker": "BP",
                "exchange": "XLON",
                "name": "BP plc",
                "country": "GB",
                "currency": "GBP",
            },
        },
    }


@pytest.fixture
def sample_european_exchanges() -> list[dict[str, Any]]:
    """Sample European exchange data for testing."""
    return [
        {
            "code": "XETR",
            "name": "Xetra",
            "country": "DE",
            "currency": "EUR",
            "timezone": "Europe/Berlin",
        },
        {
            "code": "XFRA",
            "name": "Frankfurt Stock Exchange",
            "country": "DE",
            "currency": "EUR",
            "timezone": "Europe/Berlin",
        },
        {
            "code": "XLON",
            "name": "London Stock Exchange",
            "country": "GB",
            "currency": "GBP",
            "timezone": "Europe/London",
        },
        {
            "code": "XPAR",
            "name": "Euronext Paris",
            "country": "FR",
            "currency": "EUR",
            "timezone": "Europe/Paris",
        },
        {
            "code": "XAMS",
            "name": "Euronext Amsterdam",
            "country": "NL",
            "currency": "EUR",
            "timezone": "Europe/Amsterdam",
        },
    ]


@pytest.fixture
def sample_sync_job_data() -> dict[str, Any]:
    """Sample sync job data for testing sync functionality."""
    return {
        "job_id": "sync_123456789_100",
        "source": "test_sync",
        "isins": ["US0378331005", "DE0007164600", "GB0002162385"],
        "status": "pending",
        "total": 3,
        "progress": 0,
        "created_at": "2024-01-15T10:30:00Z",
        "results": {},
        "errors": [],
    }


@pytest.fixture
def sample_market_quotes() -> dict[str, dict[str, Any]]:
    """Sample market quote data for testing market data services."""
    return {
        "US0378331005": {
            "symbol": "AAPL",
            "isin": "US0378331005",
            "price": 150.00,
            "currency": "USD",
            "change": 5.00,
            "change_percent": 3.45,
            "volume": 45678900,
            "bid": 149.95,
            "ask": 150.05,
            "source": "yahoo_finance",
            "timestamp": "2024-01-15T16:00:00Z",
        },
        "DE0007164600": {
            "symbol": "SAP",
            "isin": "DE0007164600",
            "price": 120.50,
            "currency": "EUR",
            "change": -2.30,
            "change_percent": -1.87,
            "volume": 1234567,
            "bid": 120.45,
            "ask": 120.55,
            "source": "deutsche_borse",
            "timestamp": "2024-01-15T16:00:00Z",
        },
    }


@pytest.fixture
def sample_conflict_data() -> dict[str, Any]:
    """Sample conflict data for testing conflict resolution."""
    return {
        "isin": "DE0007164600",
        "existing_mapping": {
            "ticker": "SAP",
            "exchange_code": "XETR",
            "security_name": "SAP SE",
            "confidence": 0.95,
            "source": "manual_verified",
        },
        "new_mapping": {
            "ticker": "SAP.DE",
            "exchange_code": "XFRA",
            "security_name": "SAP AG",
            "confidence": 0.87,
            "source": "german_data_providers",
        },
        "conflict_type": "ticker_mismatch",
    }


@pytest.fixture
def mock_external_apis():
    """Mock external API responses for testing."""
    return {
        "yahoo_finance": {
            "info": {
                "regularMarketPrice": 150.0,
                "currency": "USD",
                "marketCap": 2400000000000,
                "trailingPE": 28.5,
            }
        },
        "deutsche_borse": {
            "security_info": {
                "isin": "DE0007164600",
                "ticker_symbol": "SAP",
                "name": "SAP SE",
                "currency": "EUR",
                "exchange": "XETR",
            }
        },
        "boerse_frankfurt": {
            "quote": {
                "price": 120.50,
                "currency": "EUR",
                "change": -2.30,
                "volume": 1234567,
            }
        },
    }


@pytest.fixture
def sample_validation_cache() -> list[dict[str, Any]]:
    """Sample ISIN validation cache entries for testing."""
    return [
        {
            "isin": "US0378331005",
            "is_valid": True,
            "country_code": "US",
            "country_name": "United States",
            "cached_at": "2024-01-15T10:00:00Z",
        },
        {
            "isin": "DE0007164600",
            "is_valid": True,
            "country_code": "DE",
            "country_name": "Germany",
            "cached_at": "2024-01-15T10:00:00Z",
        },
        {
            "isin": "INVALID123",
            "is_valid": False,
            "validation_error": "Invalid ISIN format",
            "cached_at": "2024-01-15T10:00:00Z",
        },
    ]


@pytest.fixture
def isin_test_cases() -> dict[str, list[tuple[str, bool, str]]]:
    """Comprehensive ISIN test cases for validation testing."""
    return {
        "valid_cases": [
            ("US0378331005", True, "Apple Inc. - Valid US ISIN"),
            ("DE0007164600", True, "SAP SE - Valid German ISIN"),
            ("GB0002162385", True, "BP plc - Valid UK ISIN"),
            ("FR0000120073", True, "Airbus SE - Valid French ISIN"),
            ("NL0011794037", True, "ASML - Valid Dutch ISIN"),
            ("CH0012005267", True, "Nestlé - Valid Swiss ISIN"),
            ("JP3902900004", True, "Nintendo - Valid Japanese ISIN"),
            ("CA0679011084", True, "Barrick Gold - Valid Canadian ISIN"),
        ],
        "invalid_cases": [
            ("US037833100", False, "Too short - 11 characters"),
            ("US0378331006", False, "Invalid check digit"),
            ("123456789012", False, "Invalid country code"),
            ("US03783310AB", False, "Invalid characters in national code"),
            ("US03783310055", False, "Too long - 13 characters"),
            ("", False, "Empty string"),
            ("INVALIDFORMAT", False, "Completely wrong format"),
            ("us0378331005", False, "Lowercase characters"),
            ("US-378331005", False, "Invalid separator character"),
            ("US 378331005", False, "Space character in ISIN"),
        ],
        "edge_cases": [
            ("XS0000000000", True, "International ISIN"),
            ("EU0000000000", True, "European ISIN"),
            ("QS0000000000", False, "Non-existent country code"),
            ("US000000000A", False, "Letter in check digit position"),
        ],
    }


@pytest.fixture
def performance_test_data() -> dict[str, Any]:
    """Data for performance testing ISIN operations."""
    return {
        "small_batch": ["US0378331005", "DE0007164600", "GB0002162385"],
        "medium_batch": [f"US{str(i).zfill(9)}5" for i in range(100)],
        "large_batch": [f"DE{str(i).zfill(9)}0" for i in range(1000)],
        "expected_times": {
            "validation": 0.001,  # seconds per ISIN
            "mapping_lookup": 0.01,  # seconds per ISIN
            "sync_operation": 1.0,  # seconds per ISIN
        },
    }


@pytest.fixture
def integration_test_markers():
    """Pytest markers for integration tests."""
    return pytest.mark.skipif(
        not pytest.config.getoption("--run-integration"),
        reason="Integration tests require --run-integration flag",
    )
