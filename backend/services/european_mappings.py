"""Enhanced European stock mappings service.

This module provides comprehensive mapping functionality for European stocks
including major exchanges like Deutsche Börse, Euronext, LSE, and others.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EuropeanExchange(Enum):
    """European stock exchanges."""

    # German Exchanges
    XETR = ("XETR", "Xetra", "DE", "EUR")
    XFRA = ("XFRA", "Frankfurt Stock Exchange", "DE", "EUR")
    XMUN = ("XMUN", "Munich Stock Exchange", "DE", "EUR")
    XDUS = ("XDUS", "Düsseldorf Stock Exchange", "DE", "EUR")
    XBER = ("XBER", "Berlin Stock Exchange", "DE", "EUR")
    XHAM = ("XHAM", "Hamburg Stock Exchange", "DE", "EUR")
    XSTU = ("XSTU", "Stuttgart Stock Exchange", "DE", "EUR")

    # UK Exchanges
    XLON = ("XLON", "London Stock Exchange", "GB", "GBP")
    XAIM = ("XAIM", "AIM London", "GB", "GBP")

    # French Exchanges
    XPAR = ("XPAR", "Euronext Paris", "FR", "EUR")

    # Dutch Exchanges
    XAMS = ("XAMS", "Euronext Amsterdam", "NL", "EUR")

    # Belgian Exchanges
    XBRU = ("XBRU", "Euronext Brussels", "BE", "EUR")

    # Italian Exchanges
    XMIL = ("XMIL", "Borsa Italiana", "IT", "EUR")

    # Spanish Exchanges
    XMAD = ("XMAD", "BME Spanish Exchanges", "ES", "EUR")

    # Swiss Exchanges
    XSWX = ("XSWX", "SIX Swiss Exchange", "CH", "CHF")

    # Austrian Exchanges
    XWBO = ("XWBO", "Wiener Börse", "AT", "EUR")

    # Nordic Exchanges
    XSTO = ("XSTO", "Nasdaq Stockholm", "SE", "SEK")
    XCSE = ("XCSE", "Nasdaq Copenhagen", "DK", "DKK")
    XHEL = ("XHEL", "Nasdaq Helsinki", "FI", "EUR")
    XICE = ("XICE", "Nasdaq Iceland", "IS", "ISK")
    XOSL = ("XOSL", "Oslo Børs", "NO", "NOK")

    # Portuguese Exchanges
    XLIS = ("XLIS", "Euronext Lisbon", "PT", "EUR")

    def __init__(self, code: str, display_name: str, country: str, currency: str):
        self.code = code
        self.display_name = display_name
        self.country = country
        self.currency = currency


@dataclass
class EuropeanStockMapping:
    """Enhanced European stock mapping with comprehensive metadata."""

    isin: str
    ticker: str
    exchange: EuropeanExchange
    company_name: str = ""

    # Additional identifiers
    wkn: str | None = None  # German WKN
    sedol: str | None = None  # UK SEDOL
    cusip: str | None = None  # International CUSIP
    lei: str | None = None  # Legal Entity Identifier

    # Market data
    currency: str = "EUR"
    sector: str | None = None
    industry: str | None = None
    market_cap: float | None = None

    # Trading information
    lot_size: int = 1
    trading_hours: str | None = None
    settlement_days: int = 2

    # Quality indicators
    confidence: float = 1.0
    source: str = "manual"
    is_primary_listing: bool = False
    is_active: bool = True

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    last_verified: datetime | None = None

    def __post_init__(self):
        """Post-initialization validation and setup."""
        # Set currency from exchange if not provided
        if not self.currency and self.exchange:
            self.currency = self.exchange.currency

        # Validate ISIN format
        if not self._validate_isin():
            raise ValueError(f"Invalid ISIN format: {self.isin}")

    def _validate_isin(self) -> bool:
        """Validate ISIN format."""
        if not self.isin or len(self.isin) != 12:
            return False
        return re.match(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$", self.isin) is not None

    @property
    def country_code(self) -> str:
        """Extract country code from ISIN."""
        return self.isin[:2] if len(self.isin) >= 2 else ""

    @property
    def national_code(self) -> str:
        """Extract national code from ISIN."""
        return self.isin[2:11] if len(self.isin) >= 11 else ""

    @property
    def check_digit(self) -> str:
        """Extract check digit from ISIN."""
        return self.isin[11] if len(self.isin) == 12 else ""

    @property
    def ticker_with_exchange(self) -> str:
        """Get ticker with exchange suffix."""
        return f"{self.ticker}.{self.exchange.code}"

    @property
    def display_name(self) -> str:
        """Get display-friendly name."""
        return (
            f"{self.company_name} ({self.ticker})" if self.company_name else self.ticker
        )


class EuropeanMappingService:
    """Service for managing European stock mappings."""

    def __init__(self):
        self.mappings: dict[str, list[EuropeanStockMapping]] = {}
        self.ticker_to_isin: dict[str, set[str]] = {}
        self.exchange_mappings: dict[EuropeanExchange, set[str]] = {}

        # Initialize with known high-quality mappings
        self._load_default_mappings()

    def _load_default_mappings(self):
        """Load default high-quality mappings for major European stocks."""
        default_mappings = [
            # German Blue Chips (DAX)
            EuropeanStockMapping(
                isin="DE0007164600",
                ticker="SAP",
                exchange=EuropeanExchange.XETR,
                company_name="SAP SE",
                sector="Technology",
                confidence=1.0,
                is_primary_listing=True,
                source="manual_verified",
            ),
            EuropeanStockMapping(
                isin="DE0008404005",
                ticker="ALV",
                exchange=EuropeanExchange.XETR,
                company_name="Allianz SE",
                sector="Financial Services",
                confidence=1.0,
                is_primary_listing=True,
                source="manual_verified",
            ),
            EuropeanStockMapping(
                isin="DE0005190003",
                ticker="BMW",
                exchange=EuropeanExchange.XETR,
                company_name="Bayerische Motoren Werke AG",
                sector="Consumer Cyclical",
                confidence=1.0,
                is_primary_listing=True,
                source="manual_verified",
            ),
            EuropeanStockMapping(
                isin="DE0007236101",
                ticker="SIE",
                exchange=EuropeanExchange.XETR,
                company_name="Siemens AG",
                sector="Industrials",
                confidence=1.0,
                is_primary_listing=True,
                source="manual_verified",
            ),
            # UK Blue Chips (FTSE 100)
            EuropeanStockMapping(
                isin="GB0002374006",
                ticker="SHEL",
                exchange=EuropeanExchange.XLON,
                company_name="Shell plc",
                sector="Energy",
                confidence=1.0,
                is_primary_listing=True,
                source="manual_verified",
                currency="GBP",
            ),
            EuropeanStockMapping(
                isin="GB0007980591",
                ticker="BP",
                exchange=EuropeanExchange.XLON,
                company_name="BP p.l.c.",
                sector="Energy",
                confidence=1.0,
                is_primary_listing=True,
                source="manual_verified",
                currency="GBP",
            ),
            EuropeanStockMapping(
                isin="GB00B03MLX29",
                ticker="RDSA",
                exchange=EuropeanExchange.XLON,
                company_name="Royal Dutch Shell",
                sector="Energy",
                confidence=1.0,
                is_primary_listing=True,
                source="manual_verified",
                currency="GBP",
            ),
            # French Blue Chips (CAC 40)
            EuropeanStockMapping(
                isin="FR0000120073",
                ticker="AIR",
                exchange=EuropeanExchange.XPAR,
                company_name="Airbus SE",
                sector="Industrials",
                confidence=1.0,
                is_primary_listing=True,
                source="manual_verified",
            ),
            EuropeanStockMapping(
                isin="FR0000120628",
                ticker="AXA",
                exchange=EuropeanExchange.XPAR,
                company_name="AXA SA",
                sector="Financial Services",
                confidence=1.0,
                is_primary_listing=True,
                source="manual_verified",
            ),
            EuropeanStockMapping(
                isin="FR0000125486",
                ticker="VIE",
                exchange=EuropeanExchange.XPAR,
                company_name="Veolia Environnement SA",
                sector="Utilities",
                confidence=1.0,
                is_primary_listing=True,
                source="manual_verified",
            ),
            # Dutch Blue Chips
            EuropeanStockMapping(
                isin="NL0011794037",
                ticker="ASML",
                exchange=EuropeanExchange.XAMS,
                company_name="ASML Holding N.V.",
                sector="Technology",
                confidence=1.0,
                is_primary_listing=True,
                source="manual_verified",
            ),
            EuropeanStockMapping(
                isin="NL0000009538",
                ticker="UNA",
                exchange=EuropeanExchange.XAMS,
                company_name="Unilever N.V.",
                sector="Consumer Defensive",
                confidence=1.0,
                is_primary_listing=True,
                source="manual_verified",
            ),
            # Swiss Blue Chips
            EuropeanStockMapping(
                isin="CH0012005267",
                ticker="NESN",
                exchange=EuropeanExchange.XSWX,
                company_name="Nestlé S.A.",
                sector="Consumer Defensive",
                confidence=1.0,
                is_primary_listing=True,
                source="manual_verified",
                currency="CHF",
            ),
            EuropeanStockMapping(
                isin="CH0244767585",
                ticker="ROG",
                exchange=EuropeanExchange.XSWX,
                company_name="Roche Holding AG",
                sector="Healthcare",
                confidence=1.0,
                is_primary_listing=True,
                source="manual_verified",
                currency="CHF",
            ),
        ]

        for mapping in default_mappings:
            self.add_mapping(mapping)

    def add_mapping(self, mapping: EuropeanStockMapping) -> bool:
        """Add a new mapping to the service.

        Args:
            mapping: The mapping to add

        Returns:
            True if added successfully, False otherwise
        """
        try:
            # Add to ISIN index
            if mapping.isin not in self.mappings:
                self.mappings[mapping.isin] = []
            self.mappings[mapping.isin].append(mapping)

            # Add to ticker index
            ticker_key = mapping.ticker_with_exchange
            if ticker_key not in self.ticker_to_isin:
                self.ticker_to_isin[ticker_key] = set()
            self.ticker_to_isin[ticker_key].add(mapping.isin)

            # Add to exchange index
            if mapping.exchange not in self.exchange_mappings:
                self.exchange_mappings[mapping.exchange] = set()
            self.exchange_mappings[mapping.exchange].add(mapping.isin)

            logger.info(
                f"Added mapping: {mapping.isin} -> {mapping.ticker_with_exchange}"
            )
            return True

        except Exception as e:
            logger.error(f"Error adding mapping for {mapping.isin}: {e}")
            return False

    def get_mappings_by_isin(self, isin: str) -> list[EuropeanStockMapping]:
        """Get all mappings for an ISIN."""
        return self.mappings.get(isin, [])

    def get_mappings_by_ticker(
        self, ticker: str, exchange: EuropeanExchange | None = None
    ) -> list[EuropeanStockMapping]:
        """Get mappings by ticker, optionally filtered by exchange."""
        results = []

        if exchange:
            ticker_key = f"{ticker}.{exchange.code}"
            isins = self.ticker_to_isin.get(ticker_key, set())
            for isin in isins:
                results.extend(self.get_mappings_by_isin(isin))
        else:
            # Search all exchanges
            for ticker_key, isins in self.ticker_to_isin.items():
                if ticker_key.startswith(f"{ticker}."):
                    for isin in isins:
                        results.extend(self.get_mappings_by_isin(isin))

        return results

    def get_best_mapping(
        self, isin: str, prefer_exchange: EuropeanExchange | None = None
    ) -> EuropeanStockMapping | None:
        """Get the best mapping for an ISIN.

        Args:
            isin: The ISIN to look up
            prefer_exchange: Preferred exchange

        Returns:
            Best mapping or None
        """
        mappings = self.get_mappings_by_isin(isin)
        if not mappings:
            return None

        # Filter by preferred exchange
        if prefer_exchange:
            exchange_mappings = [m for m in mappings if m.exchange == prefer_exchange]
            if exchange_mappings:
                mappings = exchange_mappings

        # Sort by quality indicators
        mappings.sort(
            key=lambda m: (
                m.is_primary_listing,
                m.confidence,
                m.is_active,
                -len(m.source),  # Prefer longer source descriptions (more detailed)
            ),
            reverse=True,
        )

        return mappings[0]

    def suggest_ticker_for_isin(
        self, isin: str, prefer_exchange: str | None = None
    ) -> str | None:
        """Suggest a ticker symbol for an ISIN.

        Args:
            isin: The ISIN to suggest ticker for
            prefer_exchange: Preferred exchange code

        Returns:
            Suggested ticker or None
        """
        # Try exact mapping first
        best_mapping = self.get_best_mapping(isin)
        if best_mapping:
            return best_mapping.ticker_with_exchange

        # Try to generate ticker from ISIN structure
        return self._generate_ticker_from_isin(isin, prefer_exchange)

    def _generate_ticker_from_isin(
        self, isin: str, prefer_exchange: str | None = None
    ) -> str | None:
        """Generate potential ticker from ISIN structure."""
        if len(isin) != 12:
            return None

        country_code = isin[:2]
        national_code = isin[2:11]

        # Country-specific ticker generation
        if country_code == "DE":  # Germany
            # Extract WKN (usually last 6 digits)
            wkn = self._extract_wkn_from_german_isin(isin)
            if wkn:
                exchange = prefer_exchange or "XETR"
                return f"{wkn}.{exchange}"

        elif country_code == "GB":  # United Kingdom
            # Extract SEDOL-like identifier
            alpha_part = "".join(filter(str.isalpha, national_code))
            if alpha_part and len(alpha_part) >= 3:
                exchange = prefer_exchange or "XLON"
                return f"{alpha_part[:4]}.{exchange}"

        elif country_code in ["FR", "NL", "BE"]:  # Euronext countries
            # Use numeric part
            numeric_part = "".join(filter(str.isdigit, national_code))
            if numeric_part and len(numeric_part) >= 4:
                exchange_map = {"FR": "XPAR", "NL": "XAMS", "BE": "XBRU"}
                exchange = prefer_exchange or exchange_map.get(country_code, "XPAR")
                return f"{numeric_part[:6]}.{exchange}"

        return None

    def _extract_wkn_from_german_isin(self, isin: str) -> str | None:
        """Extract WKN from German ISIN."""
        if not isin.startswith("DE") or len(isin) != 12:
            return None

        try:
            national_code = isin[2:11]
            # WKN is typically the numeric part, last 6 digits
            numeric_part = "".join(filter(str.isdigit, national_code))
            if len(numeric_part) >= 6:
                return numeric_part[-6:]
            return None
        except Exception:
            return None

    def get_exchange_coverage(self) -> dict[str, dict[str, Any]]:
        """Get coverage statistics by exchange."""
        coverage = {}

        for exchange in EuropeanExchange:
            exchange_isins = self.exchange_mappings.get(exchange, set())
            coverage[exchange.code] = {
                "name": exchange.display_name,
                "country": exchange.country,
                "currency": exchange.currency,
                "mapped_securities": len(exchange_isins),
                "primary_listings": len(
                    [
                        isin
                        for isin in exchange_isins
                        for mapping in self.get_mappings_by_isin(isin)
                        if mapping.exchange == exchange and mapping.is_primary_listing
                    ]
                ),
            }

        return coverage

    def search_mappings(
        self, query: str, limit: int = 20
    ) -> list[EuropeanStockMapping]:
        """Search mappings by various criteria.

        Args:
            query: Search query (ISIN, ticker, company name)
            limit: Maximum results to return

        Returns:
            List of matching mappings
        """
        results = []
        query_upper = query.upper()

        # Search in all mappings
        for isin, mappings in self.mappings.items():
            for mapping in mappings:
                if (
                    query_upper in isin
                    or query_upper in mapping.ticker
                    or query_upper in mapping.company_name.upper()
                    or (mapping.wkn and query_upper in mapping.wkn)
                ):
                    results.append(mapping)

                    if len(results) >= limit:
                        break

            if len(results) >= limit:
                break

        # Sort by relevance
        results.sort(
            key=lambda m: (
                m.confidence,
                m.is_primary_listing,
                -len(m.company_name),  # Prefer more detailed entries
            ),
            reverse=True,
        )

        return results[:limit]

    def validate_mapping_quality(self, mapping: EuropeanStockMapping) -> dict[str, Any]:
        """Validate the quality of a mapping.

        Args:
            mapping: The mapping to validate

        Returns:
            Validation report
        """
        issues = []
        score = 1.0

        # Check ISIN format
        if not mapping._validate_isin():
            issues.append("Invalid ISIN format")
            score -= 0.3

        # Check ticker format
        if not mapping.ticker or len(mapping.ticker) < 2:
            issues.append("Invalid ticker format")
            score -= 0.2

        # Check company name
        if not mapping.company_name or len(mapping.company_name) < 3:
            issues.append("Missing or incomplete company name")
            score -= 0.1

        # Check exchange compatibility
        if mapping.exchange and mapping.country_code:
            if mapping.exchange.country != mapping.country_code:
                issues.append("Exchange country mismatch with ISIN country")
                score -= 0.2

        # Check currency consistency
        if mapping.currency != mapping.exchange.currency:
            issues.append("Currency mismatch with exchange")
            score -= 0.1

        # Check for duplicates
        existing_mappings = self.get_mappings_by_isin(mapping.isin)
        duplicates = [
            m
            for m in existing_mappings
            if m.ticker == mapping.ticker and m.exchange == mapping.exchange
        ]
        if duplicates:
            issues.append("Duplicate mapping exists")
            score -= 0.1

        return {
            "score": max(0.0, score),
            "issues": issues,
            "is_valid": score > 0.5 and len(issues) == 0,
        }

    def export_mappings(
        self, exchange: EuropeanExchange | None = None
    ) -> list[dict[str, Any]]:
        """Export mappings to a list of dictionaries."""
        results = []

        for mappings in self.mappings.values():
            for mapping in mappings:
                if exchange is None or mapping.exchange == exchange:
                    results.append(
                        {
                            "isin": mapping.isin,
                            "ticker": mapping.ticker,
                            "exchange_code": mapping.exchange.code,
                            "exchange_name": mapping.exchange.display_name,
                            "company_name": mapping.company_name,
                            "currency": mapping.currency,
                            "sector": mapping.sector,
                            "confidence": mapping.confidence,
                            "is_primary_listing": mapping.is_primary_listing,
                            "is_active": mapping.is_active,
                            "source": mapping.source,
                            "created_at": mapping.created_at.isoformat(),
                            "wkn": mapping.wkn,
                            "sedol": mapping.sedol,
                        }
                    )

        return results


# Singleton instance
european_mapping_service = EuropeanMappingService()


def get_european_mapping_service() -> EuropeanMappingService:
    """Get the European mapping service instance."""
    return european_mapping_service


def is_european_isin(isin: str) -> bool:
    """Check if an ISIN is from a European country."""
    if len(isin) < 2:
        return False

    european_countries = {
        "AD",
        "AL",
        "AM",
        "AT",
        "AZ",
        "BA",
        "BE",
        "BG",
        "BY",
        "CH",
        "CY",
        "CZ",
        "DE",
        "DK",
        "EE",
        "ES",
        "FI",
        "FR",
        "GB",
        "GE",
        "GR",
        "HR",
        "HU",
        "IE",
        "IS",
        "IT",
        "LI",
        "LT",
        "LU",
        "LV",
        "MC",
        "MD",
        "ME",
        "MK",
        "MT",
        "NL",
        "NO",
        "PL",
        "PT",
        "RO",
        "RS",
        "RU",
        "SE",
        "SI",
        "SK",
        "SM",
        "UA",
        "VA",
    }

    return isin[:2] in european_countries


def get_country_exchanges(country_code: str) -> list[EuropeanExchange]:
    """Get all exchanges for a specific country."""
    return [
        exchange for exchange in EuropeanExchange if exchange.country == country_code
    ]


def suggest_exchange_for_isin(isin: str) -> EuropeanExchange | None:
    """Suggest the most appropriate exchange for an ISIN."""
    if len(isin) < 2:
        return None

    country_code = isin[:2]
    country_exchanges = get_country_exchanges(country_code)

    if not country_exchanges:
        return None

    # Return primary exchange for each country
    primary_exchanges = {
        "DE": EuropeanExchange.XETR,
        "GB": EuropeanExchange.XLON,
        "FR": EuropeanExchange.XPAR,
        "NL": EuropeanExchange.XAMS,
        "BE": EuropeanExchange.XBRU,
        "IT": EuropeanExchange.XMIL,
        "ES": EuropeanExchange.XMAD,
        "CH": EuropeanExchange.XSWX,
        "AT": EuropeanExchange.XWBO,
        "SE": EuropeanExchange.XSTO,
        "DK": EuropeanExchange.XCSE,
        "FI": EuropeanExchange.XHEL,
        "NO": EuropeanExchange.XOSL,
        "PT": EuropeanExchange.XLIS,
    }

    return primary_exchanges.get(country_code, country_exchanges[0])


# Service instance management
_european_mappings_service: "EuropeanMappingsService | None" = None


class EuropeanMappingsService:
    """Service for managing European stock mappings."""

    def __init__(self):
        self.mappings: list[EuropeanStockMapping] = []
        self._last_updated = datetime.now()

    def get_mapping_by_isin(self, isin: str) -> EuropeanStockMapping | None:
        """Get mapping by ISIN."""
        for mapping in self.mappings:
            if mapping.isin == isin:
                return mapping
        return None

    def search_by_ticker(self, ticker: str) -> list[EuropeanStockMapping]:
        """Search mappings by ticker."""
        results = []
        for mapping in self.mappings:
            if ticker.upper() in mapping.ticker.upper():
                results.append(mapping)
        return results

    def add_mapping(self, mapping: EuropeanStockMapping) -> None:
        """Add a new mapping."""
        # Remove existing mapping with same ISIN
        self.mappings = [m for m in self.mappings if m.isin != mapping.isin]
        self.mappings.append(mapping)
        self._last_updated = datetime.now()

    def get_all_mappings(self) -> list[EuropeanStockMapping]:
        """Get all mappings."""
        return self.mappings.copy()

    def update_mapping(self, isin: str, **kwargs) -> bool:
        """Update an existing mapping."""
        for mapping in self.mappings:
            if mapping.isin == isin:
                for key, value in kwargs.items():
                    if hasattr(mapping, key):
                        setattr(mapping, key, value)
                self._last_updated = datetime.now()
                return True
        return False

    def remove_mapping(self, isin: str) -> bool:
        """Remove a mapping by ISIN."""
        original_count = len(self.mappings)
        self.mappings = [m for m in self.mappings if m.isin != isin]
        return len(self.mappings) < original_count


def get_european_mappings_service() -> EuropeanMappingsService:
    """Get the singleton European mappings service instance."""
    global _european_mappings_service
    if _european_mappings_service is None:
        _european_mappings_service = EuropeanMappingsService()
    return _european_mappings_service
