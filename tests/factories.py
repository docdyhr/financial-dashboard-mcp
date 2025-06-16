"""Test data factories and utilities for generating consistent test data.

This module provides factory classes and utility functions for creating
test data for the ISIN system and financial dashboard components.
"""

# ruff: noqa: S311, B007, RUF009

import random
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import factory
from faker import Faker

fake = Faker()
fake.seed_instance(42)  # Deterministic data for tests


class ISINFactory:
    """Factory for generating test ISIN codes."""

    COUNTRY_CODES = [
        "US",
        "DE",
        "GB",
        "FR",
        "NL",
        "CH",
        "IT",
        "ES",
        "SE",
        "DK",
        "FI",
        "NO",
        "AT",
        "BE",
        "IE",
        "PT",
        "GR",
        "LU",
        "CZ",
        "PL",
    ]

    KNOWN_VALID_ISINS = [
        "US0378331005",  # Apple Inc.
        "DE0007164600",  # SAP SE
        "GB0002162385",  # BP plc
        "FR0000120073",  # Airbus SE
        "NL0011794037",  # ASML Holding N.V.
        "CH0012005267",  # Nestlé S.A.
        "IT0003128367",  # ENEL SpA
        "ES0113900J37",  # Banco Santander
        "SE0000108656",  # Volvo AB
        "DK0010274414",  # Novo Nordisk
    ]

    @classmethod
    def create_valid_isin(cls, country_code: str | None = None) -> str:
        """Create a valid ISIN with proper check digit."""
        if country_code is None:
            country_code = random.choice(cls.COUNTRY_CODES)

        # Generate 9-digit national code
        national_code = "".join([str(random.randint(0, 9)) for _ in range(9)])

        # Calculate check digit using Luhn algorithm (simplified)
        isin_base = country_code + national_code
        check_digit = cls._calculate_check_digit(isin_base)

        return isin_base + str(check_digit)

    @classmethod
    def create_invalid_isin(cls, error_type: str = "random") -> str:
        """Create an invalid ISIN for testing error handling."""
        if error_type == "too_short":
            return "US037833100"  # 11 characters instead of 12
        if error_type == "too_long":
            return "US03783310055"  # 13 characters instead of 12
        if error_type == "invalid_country":
            return "XY0378331005"  # Non-existent country code
        if error_type == "invalid_check_digit":
            return "US0378331006"  # Wrong check digit
        if error_type == "invalid_characters":
            return "US03783310@5"  # Invalid character
        if error_type == "empty":
            return ""
        # Random invalid format
        return random.choice(
            [
                "US037833100",
                "US03783310055",
                "XY0378331005",
                "US0378331006",
                "US03783310@5",
                "",
                "INVALIDFORMAT",
            ]
        )

    @classmethod
    def get_known_valid_isin(cls) -> str:
        """Get a known valid ISIN for testing."""
        return random.choice(cls.KNOWN_VALID_ISINS)

    @classmethod
    def _calculate_check_digit(cls, isin_base: str) -> int:
        """Calculate ISIN check digit using Luhn algorithm."""
        # Convert letters to numbers (A=10, B=11, ..., Z=35)
        converted = ""
        for char in isin_base:
            if char.isalpha():
                converted += str(ord(char) - ord("A") + 10)
            else:
                converted += char

        # Apply Luhn algorithm
        total = 0
        for i, digit in enumerate(reversed(converted)):
            n = int(digit)
            if i % 2 == 1:  # Every second digit from right
                n *= 2
                if n > 9:
                    n = (n // 10) + (n % 10)
            total += n

        return (10 - (total % 10)) % 10


class ExchangeFactory:
    """Factory for generating test exchange data."""

    EXCHANGES = {
        "XETR": {"name": "Xetra", "country": "DE", "currency": "EUR"},
        "XFRA": {
            "name": "Frankfurt Stock Exchange",
            "country": "DE",
            "currency": "EUR",
        },
        "XNAS": {"name": "NASDAQ", "country": "US", "currency": "USD"},
        "XNYS": {"name": "New York Stock Exchange", "country": "US", "currency": "USD"},
        "XLON": {"name": "London Stock Exchange", "country": "GB", "currency": "GBP"},
        "XPAR": {"name": "Euronext Paris", "country": "FR", "currency": "EUR"},
        "XAMS": {"name": "Euronext Amsterdam", "country": "NL", "currency": "EUR"},
        "XSWX": {"name": "SIX Swiss Exchange", "country": "CH", "currency": "CHF"},
        "XMIL": {"name": "Borsa Italiana", "country": "IT", "currency": "EUR"},
        "XMAD": {"name": "BME Spanish Exchanges", "country": "ES", "currency": "EUR"},
    }

    @classmethod
    def create_exchange_data(cls, exchange_code: str | None = None) -> dict[str, str]:
        """Create exchange data for testing."""
        if exchange_code is None:
            exchange_code = random.choice(list(cls.EXCHANGES.keys()))

        exchange_info = cls.EXCHANGES.get(
            exchange_code,
            {
                "name": f"Test Exchange {exchange_code}",
                "country": "XX",
                "currency": "XXX",
            },
        )

        return {
            "code": exchange_code,
            "name": exchange_info["name"],
            "country": exchange_info["country"],
            "currency": exchange_info["currency"],
            "timezone": f"Europe/{exchange_info['country']}",
        }

    @classmethod
    def get_random_exchange_code(cls) -> str:
        """Get a random exchange code."""
        return random.choice(list(cls.EXCHANGES.keys()))


@dataclass
class ISINMappingData:
    """Data structure for ISIN mapping test data."""

    isin: str
    ticker: str
    exchange_code: str
    exchange_name: str
    security_name: str
    currency: str
    source: str
    confidence: float
    is_active: bool = True
    wkn: str | None = None
    sedol: str | None = None
    sector: str | None = None
    created_at: datetime = factory.LazyFunction(datetime.now)
    last_updated: datetime | None = None


class ISINMappingFactory:
    """Factory for generating ISIN mapping test data."""

    SECTORS = [
        "Technology",
        "Financial Services",
        "Healthcare",
        "Consumer Cyclical",
        "Consumer Defensive",
        "Industrials",
        "Energy",
        "Utilities",
        "Basic Materials",
        "Communication Services",
        "Real Estate",
    ]

    SOURCES = [
        "manual_verified",
        "yahoo_finance",
        "bloomberg",
        "reuters",
        "german_data_providers",
        "european_mappings",
        "alpha_vantage",
        "auto_sync",
        "bulk_import",
        "test_data",
    ]

    @classmethod
    def create_mapping(
        cls,
        isin: str | None = None,
        ticker: str | None = None,
        exchange_code: str | None = None,
        confidence: float | None = None,
    ) -> ISINMappingData:
        """Create ISIN mapping test data."""

        if isin is None:
            isin = ISINFactory.create_valid_isin()

        if ticker is None:
            ticker = fake.lexify("????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")

        if exchange_code is None:
            exchange_code = ExchangeFactory.get_random_exchange_code()

        exchange_data = ExchangeFactory.create_exchange_data(exchange_code)

        if confidence is None:
            confidence = round(random.uniform(0.6, 1.0), 2)

        # Generate WKN for German securities
        wkn = None
        if isin.startswith("DE"):
            wkn = "".join([str(random.randint(0, 9)) for _ in range(6)])

        # Generate SEDOL for UK securities
        sedol = None
        if isin.startswith("GB"):
            sedol = "".join([str(random.randint(0, 9)) for _ in range(7)])

        return ISINMappingData(
            isin=isin,
            ticker=ticker,
            exchange_code=exchange_code,
            exchange_name=exchange_data["name"],
            security_name=fake.company(),
            currency=exchange_data["currency"],
            source=random.choice(cls.SOURCES),
            confidence=confidence,
            wkn=wkn,
            sedol=sedol,
            sector=random.choice(cls.SECTORS),
            last_updated=fake.date_time_between(start_date="-30d", end_date="now"),
        )

    @classmethod
    def create_batch(cls, count: int, **kwargs) -> list[ISINMappingData]:
        """Create a batch of ISIN mappings."""
        return [cls.create_mapping(**kwargs) for _ in range(count)]

    @classmethod
    def create_high_quality_mappings(cls, count: int) -> list[ISINMappingData]:
        """Create high-quality mappings with good confidence scores."""
        mappings = []
        for _ in range(count):
            mapping = cls.create_mapping(confidence=round(random.uniform(0.85, 1.0), 2))
            mapping.source = random.choice(["manual_verified", "bloomberg", "reuters"])
            mappings.append(mapping)
        return mappings

    @classmethod
    def create_conflicting_mappings(cls, isin: str) -> list[ISINMappingData]:
        """Create conflicting mappings for the same ISIN."""
        base_ticker = fake.lexify("????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")

        return [
            cls.create_mapping(
                isin=isin, ticker=base_ticker, exchange_code="XETR", confidence=0.95
            ),
            cls.create_mapping(
                isin=isin,
                ticker=f"{base_ticker}.DE",
                exchange_code="XFRA",
                confidence=0.87,
            ),
        ]


@dataclass
class MarketQuoteData:
    """Data structure for market quote test data."""

    symbol: str
    isin: str | None
    price: float
    currency: str
    change: float | None = None
    change_percent: float | None = None
    volume: int | None = None
    bid: float | None = None
    ask: float | None = None
    high_52w: float | None = None
    low_52w: float | None = None
    market_cap: float | None = None
    pe_ratio: float | None = None
    dividend_yield: float | None = None
    timestamp: datetime = factory.LazyFunction(datetime.now)
    source: str = "yahoo_finance"


class MarketQuoteFactory:
    """Factory for generating market quote test data."""

    CURRENCIES = ["USD", "EUR", "GBP", "CHF", "SEK", "DKK", "NOK"]
    SOURCES = ["yahoo_finance", "deutsche_borse", "boerse_frankfurt", "alpha_vantage"]

    @classmethod
    def create_quote(
        cls,
        symbol: str | None = None,
        isin: str | None = None,
        base_price: float | None = None,
        currency: str | None = None,
    ) -> MarketQuoteData:
        """Create market quote test data."""

        if symbol is None:
            symbol = fake.lexify("????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")

        if base_price is None:
            base_price = round(random.uniform(10.0, 500.0), 2)

        if currency is None:
            currency = random.choice(cls.CURRENCIES)

        # Generate realistic market data around base price
        change = round(random.uniform(-base_price * 0.05, base_price * 0.05), 2)
        change_percent = (
            round((change / base_price) * 100, 2) if base_price > 0 else 0.0
        )

        bid = round(base_price - random.uniform(0.01, 0.10), 2)
        ask = round(base_price + random.uniform(0.01, 0.10), 2)

        high_52w = round(base_price * random.uniform(1.1, 2.0), 2)
        low_52w = round(base_price * random.uniform(0.5, 0.9), 2)

        volume = random.randint(100000, 10000000)
        market_cap = random.randint(1000000000, 1000000000000)  # 1B to 1T
        pe_ratio = round(random.uniform(5.0, 50.0), 1)
        dividend_yield = round(random.uniform(0.0, 8.0), 2)

        return MarketQuoteData(
            symbol=symbol,
            isin=isin,
            price=base_price,
            currency=currency,
            change=change,
            change_percent=change_percent,
            volume=volume,
            bid=bid,
            ask=ask,
            high_52w=high_52w,
            low_52w=low_52w,
            market_cap=market_cap,
            pe_ratio=pe_ratio,
            dividend_yield=dividend_yield,
            source=random.choice(cls.SOURCES),
        )

    @classmethod
    def create_batch(cls, count: int, **kwargs) -> list[MarketQuoteData]:
        """Create a batch of market quotes."""
        return [cls.create_quote(**kwargs) for _ in range(count)]


@dataclass
class PortfolioData:
    """Data structure for portfolio test data."""

    id: int
    user_id: int
    name: str
    positions: list[dict[str, Any]]
    total_value: Decimal
    total_cost: Decimal
    created_at: datetime = factory.LazyFunction(datetime.now)
    updated_at: datetime = factory.LazyFunction(datetime.now)


class PortfolioFactory:
    """Factory for generating portfolio test data."""

    @classmethod
    def create_position(
        cls,
        ticker: str | None = None,
        isin: str | None = None,
        quantity: Decimal | None = None,
        purchase_price: Decimal | None = None,
        current_price: Decimal | None = None,
    ) -> dict[str, Any]:
        """Create a single portfolio position."""

        if ticker is None:
            ticker = fake.lexify("????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")

        if quantity is None:
            quantity = Decimal(str(random.randint(1, 1000)))

        if purchase_price is None:
            purchase_price = Decimal(str(round(random.uniform(10.0, 500.0), 2)))

        if current_price is None:
            # Current price varies from purchase price by -20% to +50%
            variation = random.uniform(-0.2, 0.5)
            current_price = purchase_price * (1 + Decimal(str(variation)))
            current_price = Decimal(str(round(float(current_price), 2)))

        total_cost = quantity * purchase_price
        total_value = quantity * current_price
        unrealized_pnl = total_value - total_cost
        unrealized_pnl_percent = (
            (unrealized_pnl / total_cost) * 100 if total_cost > 0 else Decimal("0")
        )

        return {
            "id": random.randint(1, 10000),
            "ticker": ticker,
            "isin": isin,
            "company_name": fake.company(),
            "quantity": quantity,
            "purchase_price": purchase_price,
            "current_price": current_price,
            "total_cost": total_cost,
            "total_value": total_value,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_percent": round(unrealized_pnl_percent, 2),
            "currency": random.choice(["USD", "EUR", "GBP"]),
            "sector": random.choice(ISINMappingFactory.SECTORS),
            "purchase_date": fake.date_between(start_date="-2y", end_date="now"),
        }

    @classmethod
    def create_portfolio(
        cls,
        user_id: int | None = None,
        position_count: int = 5,
        name: str | None = None,
    ) -> PortfolioData:
        """Create a complete portfolio with positions."""

        if user_id is None:
            user_id = random.randint(1, 1000)

        if name is None:
            name = f"{fake.word().title()} Portfolio"

        # Create positions
        positions = []
        total_cost = Decimal("0")
        total_value = Decimal("0")

        for i in range(position_count):
            # Some positions have ISINs, some don't
            isin = (
                ISINFactory.create_valid_isin()
                if random.choice([True, False])
                else None
            )

            position = cls.create_position(isin=isin)
            positions.append(position)

            total_cost += position["total_cost"]
            total_value += position["total_value"]

        return PortfolioData(
            id=random.randint(1, 10000),
            user_id=user_id,
            name=name,
            positions=positions,
            total_value=total_value,
            total_cost=total_cost,
        )

    @classmethod
    def create_diverse_portfolio(cls, user_id: int | None = None) -> PortfolioData:
        """Create a diverse portfolio with various asset types."""

        # Create positions across different regions and sectors
        european_isins = [
            ISINFactory.create_valid_isin("DE"),
            ISINFactory.create_valid_isin("GB"),
            ISINFactory.create_valid_isin("FR"),
        ]

        us_isins = [
            ISINFactory.create_valid_isin("US"),
            ISINFactory.create_valid_isin("US"),
        ]

        positions = []
        total_cost = Decimal("0")
        total_value = Decimal("0")

        # Add European positions
        for isin in european_isins:
            position = cls.create_position(isin=isin)
            positions.append(position)
            total_cost += position["total_cost"]
            total_value += position["total_value"]

        # Add US positions
        for isin in us_isins:
            position = cls.create_position(isin=isin)
            positions.append(position)
            total_cost += position["total_cost"]
            total_value += position["total_value"]

        # Add some positions without ISINs
        for _ in range(3):
            position = cls.create_position()
            positions.append(position)
            total_cost += position["total_cost"]
            total_value += position["total_value"]

        return PortfolioData(
            id=random.randint(1, 10000),
            user_id=user_id or random.randint(1, 1000),
            name="Diverse Global Portfolio",
            positions=positions,
            total_value=total_value,
            total_cost=total_cost,
        )


class SyncJobFactory:
    """Factory for generating sync job test data."""

    @classmethod
    def create_sync_job_data(
        cls,
        job_id: str | None = None,
        isins: list[str] | None = None,
        source: str = "test",
        status: str = "pending",
    ) -> dict[str, Any]:
        """Create sync job test data."""

        if job_id is None:
            timestamp = int(datetime.now(tz=UTC).timestamp())
            job_id = f"sync_{timestamp}_{random.randint(100, 999)}"

        if isins is None:
            count = random.randint(1, 10)
            isins = [ISINFactory.create_valid_isin() for _ in range(count)]

        return {
            "job_id": job_id,
            "source": source,
            "isins": isins,
            "status": status,
            "total": len(isins),
            "progress": 0 if status == "pending" else random.randint(0, len(isins)),
            "created_at": fake.date_time_between(
                start_date="-1d", end_date="now"
            ).isoformat(),
            "started_at": (
                None
                if status == "pending"
                else fake.date_time_between(
                    start_date="-1h", end_date="now"
                ).isoformat()
            ),
            "completed_at": (
                None
                if status in ["pending", "running"]
                else fake.date_time_between(
                    start_date="-30m", end_date="now"
                ).isoformat()
            ),
            "results": {},
            "errors": (
                []
                if status != "failed"
                else [f"Error processing {random.choice(isins)}"]
            ),
        }

    @classmethod
    def create_conflict_data(cls, isin: str | None = None) -> dict[str, Any]:
        """Create conflict data for testing."""

        if isin is None:
            isin = ISINFactory.create_valid_isin()

        ticker = fake.lexify("????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")

        return {
            "isin": isin,
            "conflict_type": random.choice(
                ["ticker_mismatch", "exchange_mismatch", "name_mismatch"]
            ),
            "existing_mapping": {
                "ticker": ticker,
                "exchange_code": "XETR",
                "security_name": fake.company(),
                "confidence": 0.95,
                "source": "manual_verified",
            },
            "new_mapping": {
                "ticker": f"{ticker}.DE",
                "exchange_code": "XFRA",
                "security_name": f"{fake.company()} AG",
                "confidence": 0.87,
                "source": "german_data_providers",
            },
        }


class TestDataGenerator:
    """Utility class for generating comprehensive test datasets."""

    @classmethod
    def generate_isin_test_dataset(cls) -> dict[str, list[str]]:
        """Generate a comprehensive ISIN test dataset."""
        return {
            "valid_isins": [ISINFactory.create_valid_isin() for _ in range(20)]
            + ISINFactory.KNOWN_VALID_ISINS,
            "invalid_isins": [
                ISINFactory.create_invalid_isin("too_short"),
                ISINFactory.create_invalid_isin("too_long"),
                ISINFactory.create_invalid_isin("invalid_country"),
                ISINFactory.create_invalid_isin("invalid_check_digit"),
                ISINFactory.create_invalid_isin("invalid_characters"),
                ISINFactory.create_invalid_isin("empty"),
            ],
            "edge_case_isins": [
                "XS0000000000",  # International securities
                "EU0000000000",  # European securities
                "QQ0000000000",  # Non-existent country
            ],
        }

    @classmethod
    def generate_mapping_test_dataset(cls, count: int = 50) -> list[ISINMappingData]:
        """Generate a dataset of ISIN mappings for testing."""
        mappings = []

        # High-quality mappings (70%)
        high_quality_count = int(count * 0.7)
        mappings.extend(
            ISINMappingFactory.create_high_quality_mappings(high_quality_count)
        )

        # Medium-quality mappings (20%)
        medium_quality_count = int(count * 0.2)
        for _ in range(medium_quality_count):
            mapping = ISINMappingFactory.create_mapping(
                confidence=round(random.uniform(0.6, 0.84), 2)
            )
            mappings.append(mapping)

        # Low-quality mappings (10%)
        low_quality_count = count - high_quality_count - medium_quality_count
        for _ in range(low_quality_count):
            mapping = ISINMappingFactory.create_mapping(
                confidence=round(random.uniform(0.3, 0.59), 2)
            )
            mapping.source = "auto_sync"
            mappings.append(mapping)

        return mappings

    @classmethod
    def generate_market_data_dataset(
        cls, symbol_count: int = 30
    ) -> list[MarketQuoteData]:
        """Generate market data for testing."""
        quotes = []

        # Major US stocks
        us_quotes = MarketQuoteFactory.create_batch(symbol_count // 3, currency="USD")
        quotes.extend(us_quotes)

        # European stocks
        european_quotes = MarketQuoteFactory.create_batch(
            symbol_count // 3, currency="EUR"
        )
        quotes.extend(european_quotes)

        # UK stocks
        uk_quotes = MarketQuoteFactory.create_batch(
            symbol_count - len(us_quotes) - len(european_quotes), currency="GBP"
        )
        quotes.extend(uk_quotes)

        return quotes

    @classmethod
    def generate_performance_test_data(cls) -> dict[str, Any]:
        """Generate data for performance testing."""
        return {
            "small_batch": [ISINFactory.create_valid_isin() for _ in range(10)],
            "medium_batch": [ISINFactory.create_valid_isin() for _ in range(100)],
            "large_batch": [ISINFactory.create_valid_isin() for _ in range(1000)],
            "mixed_quality_mappings": cls.generate_mapping_test_dataset(500),
            "bulk_quotes": cls.generate_market_data_dataset(200),
        }

    @classmethod
    def generate_integration_test_data(cls) -> dict[str, Any]:
        """Generate data for integration testing."""
        return {
            "portfolios": [
                PortfolioFactory.create_diverse_portfolio(user_id=i)
                for i in range(1, 6)
            ],
            "sync_jobs": [
                SyncJobFactory.create_sync_job_data(status=status)
                for status in ["pending", "running", "completed", "failed"]
            ],
            "conflicts": [SyncJobFactory.create_conflict_data() for _ in range(5)],
            "mappings": cls.generate_mapping_test_dataset(100),
            "quotes": cls.generate_market_data_dataset(50),
        }


def create_test_database_data():
    """Create comprehensive test data for database seeding."""
    return {
        "isins": TestDataGenerator.generate_isin_test_dataset(),
        "mappings": TestDataGenerator.generate_mapping_test_dataset(200),
        "portfolios": [PortfolioFactory.create_diverse_portfolio() for _ in range(10)],
        "market_quotes": TestDataGenerator.generate_market_data_dataset(100),
        "sync_jobs": [SyncJobFactory.create_sync_job_data() for _ in range(20)],
    }


def reset_test_data_seeds():
    """Reset all random seeds for deterministic test data."""
    random.seed(42)
    fake.seed_instance(42)
    factory.fuzzy.reseed_random(42)
