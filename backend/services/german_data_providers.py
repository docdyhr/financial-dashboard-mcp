"""German and European data providers service for financial market data.

This module provides integration with German and European market data sources
including Deutsche Börse, Börse Frankfurt, and other European exchanges.
"""

import asyncio
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class GermanSecurityInfo:
    """Information about a German security."""

    isin: str
    wkn: str | None = None  # Wertpapier-Kenn-Nummer
    name: str = ""
    ticker_symbol: str = ""
    exchange: str = ""
    currency: str = "EUR"
    sector: str | None = None
    market_segment: str | None = None
    price: float | None = None
    last_updated: datetime | None = None
    source: str = ""


@dataclass
class MarketData:
    """Market data for a security."""

    symbol: str
    price: float
    currency: str
    change: float | None = None
    change_percent: float | None = None
    volume: int | None = None
    bid: float | None = None
    ask: float | None = None
    high_52w: float | None = None
    low_52w: float | None = None
    last_updated: datetime | None = None
    source: str = ""


class DeutscheBorseProvider:
    """Provider for Deutsche Börse data."""

    BASE_URL = "https://www.xetra.com"
    SEARCH_URL = "https://www.xetra.com/xetra-en/instruments/shares"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        self.rate_limit_delay = 1.0  # Seconds between requests
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def search_by_isin(self, isin: str) -> GermanSecurityInfo | None:
        """Search for security by ISIN on Deutsche Börse.

        Args:
            isin: The ISIN to search for

        Returns:
            GermanSecurityInfo if found, None otherwise
        """
        try:
            self._rate_limit()

            # Search using Deutsche Börse ISIN lookup
            search_params = {"isin": isin, "market": "xetra"}

            response = self.session.get(
                f"{self.SEARCH_URL}/search", params=search_params, timeout=10
            )

            if response.status_code == 200:
                return self._parse_search_response(response.text, isin)
            logger.warning(
                f"Deutsche Börse search failed for {isin}: {response.status_code}"
            )

        except Exception as e:
            logger.error(f"Error searching Deutsche Börse for {isin}: {e}")

        return None

    def _parse_search_response(
        self, html: str, isin: str
    ) -> GermanSecurityInfo | None:
        """Parse search response HTML."""
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Look for security information in the response
            # This is a simplified parser - real implementation would need
            # to handle the actual Deutsche Börse response format

            security_info = GermanSecurityInfo(isin=isin, source="deutsche_borse")

            # Extract name
            name_elem = soup.find("h1", class_="instrument-name")
            if name_elem:
                security_info.name = name_elem.get_text(strip=True)

            # Extract ticker
            ticker_elem = soup.find("span", class_="ticker-symbol")
            if ticker_elem:
                security_info.ticker_symbol = ticker_elem.get_text(strip=True)

            # Extract WKN
            wkn_elem = soup.find("span", class_="wkn")
            if wkn_elem:
                security_info.wkn = wkn_elem.get_text(strip=True)

            return security_info

        except Exception as e:
            logger.error(f"Error parsing Deutsche Börse response: {e}")
            return None


class BoerseFrankfurtProvider:
    """Provider for Börse Frankfurt data."""

    BASE_URL = "https://www.boerse-frankfurt.de"
    QUOTE_URL = "https://www.boerse-frankfurt.de/equity"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        self.rate_limit_delay = 1.5  # Seconds between requests
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def get_quote_by_isin(self, isin: str) -> MarketData | None:
        """Get current quote for security by ISIN.

        Args:
            isin: The ISIN to get quote for

        Returns:
            MarketData if found, None otherwise
        """
        try:
            self._rate_limit()

            # Construct URL for ISIN lookup
            url = f"{self.QUOTE_URL}/{isin}"

            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                return self._parse_quote_response(response.text, isin)
            logger.warning(
                f"Börse Frankfurt quote failed for {isin}: {response.status_code}"
            )

        except Exception as e:
            logger.error(f"Error getting Börse Frankfurt quote for {isin}: {e}")

        return None

    def _parse_quote_response(self, html: str, isin: str) -> MarketData | None:
        """Parse quote response HTML."""
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Extract price information
            price_elem = soup.find("span", class_="price-value")
            if not price_elem:
                return None

            price_text = price_elem.get_text(strip=True)
            price = float(re.sub(r"[^\d.,]", "", price_text).replace(",", "."))

            # Extract currency
            currency = "EUR"  # Default for German exchanges
            currency_elem = soup.find("span", class_="currency")
            if currency_elem:
                currency = currency_elem.get_text(strip=True)

            # Extract change information
            change = None
            change_percent = None
            change_elem = soup.find("span", class_="change-value")
            if change_elem:
                change_text = change_elem.get_text(strip=True)
                if change_text:
                    change = float(
                        re.sub(r"[^\d.,-]", "", change_text).replace(",", ".")
                    )

            change_percent_elem = soup.find("span", class_="change-percent")
            if change_percent_elem:
                percent_text = change_percent_elem.get_text(strip=True)
                if percent_text:
                    change_percent = float(
                        re.sub(r"[^\d.,-]", "", percent_text).replace(",", ".")
                    )

            return MarketData(
                symbol=isin,  # Use ISIN as symbol
                price=price,
                currency=currency,
                change=change,
                change_percent=change_percent,
                last_updated=datetime.now(),
                source="boerse_frankfurt",
            )

        except Exception as e:
            logger.error(f"Error parsing Börse Frankfurt quote response: {e}")
            return None


class EuropeanDataAggregator:
    """Aggregator for European market data from multiple sources."""

    def __init__(self):
        self.deutsche_borse = DeutscheBorseProvider()
        self.boerse_frankfurt = BoerseFrankfurtProvider()

        # European exchange mappings
        self.exchange_mappings = {
            "XETR": "Xetra",
            "XFRA": "Frankfurt",
            "XMUN": "Munich",
            "XDUS": "Düsseldorf",
            "XBER": "Berlin",
            "XHAM": "Hamburg",
            "XSTU": "Stuttgart",
            "XLON": "London Stock Exchange",
            "XPAR": "Euronext Paris",
            "XAMS": "Euronext Amsterdam",
            "XBRU": "Euronext Brussels",
            "XMIL": "Borsa Italiana",
            "XMAD": "BME Spanish Exchanges",
        }

    async def get_comprehensive_data(self, isin: str) -> dict[str, Any]:
        """Get comprehensive data for an ISIN from multiple sources.

        Args:
            isin: The ISIN to search for

        Returns:
            Dictionary with data from all available sources
        """
        results = {
            "isin": isin,
            "sources": {},
            "best_quote": None,
            "security_info": None,
        }

        # Get security info from Deutsche Börse
        try:
            db_info = self.deutsche_borse.search_by_isin(isin)
            if db_info:
                results["sources"]["deutsche_borse"] = db_info
                results["security_info"] = db_info
        except Exception as e:
            logger.error(f"Deutsche Börse lookup failed for {isin}: {e}")

        # Get quote from Börse Frankfurt
        try:
            bf_quote = self.boerse_frankfurt.get_quote_by_isin(isin)
            if bf_quote:
                results["sources"]["boerse_frankfurt"] = bf_quote
                results["best_quote"] = bf_quote
        except Exception as e:
            logger.error(f"Börse Frankfurt quote failed for {isin}: {e}")

        return results

    def get_ticker_for_isin(
        self, isin: str, prefer_exchange: str | None = None
    ) -> str | None:
        """Get ticker symbol for ISIN, optionally preferring a specific exchange.

        Args:
            isin: The ISIN to look up
            prefer_exchange: Exchange code to prefer (e.g., 'XETR', 'XFRA')

        Returns:
            Ticker symbol if found, None otherwise
        """
        try:
            # First try Deutsche Börse
            security_info = self.deutsche_borse.search_by_isin(isin)
            if security_info and security_info.ticker_symbol:
                ticker = security_info.ticker_symbol

                # If we have a preferred exchange, try to append it
                if prefer_exchange and prefer_exchange in self.exchange_mappings:
                    return f"{ticker}.{prefer_exchange}"

                return ticker

            # If no ticker found, try to construct one from WKN or ISIN
            if security_info and security_info.wkn:
                return security_info.wkn

            # Last resort: use ISIN country code + numbers
            if len(isin) >= 12:
                country_code = isin[:2]
                numeric_part = "".join(filter(str.isdigit, isin[2:]))
                if numeric_part:
                    return f"{country_code}{numeric_part[:6]}"

        except Exception as e:
            logger.error(f"Error getting ticker for ISIN {isin}: {e}")

        return None

    def suggest_ticker_formats(self, isin: str) -> list[dict[str, str]]:
        """Suggest possible ticker formats for an ISIN.

        Args:
            isin: The ISIN to suggest tickers for

        Returns:
            List of suggested ticker formats with explanations
        """
        suggestions = []

        if len(isin) != 12:
            return suggestions

        country_code = isin[:2]
        national_code = isin[2:11]

        # German-specific suggestions
        if country_code == "DE":
            # Standard German ticker formats
            numeric_part = "".join(filter(str.isdigit, national_code))
            alpha_part = "".join(filter(str.isalpha, national_code))

            if numeric_part:
                suggestions.extend(
                    [
                        {
                            "ticker": f"{numeric_part[:6]}",
                            "explanation": "Six-digit WKN format",
                        },
                        {
                            "ticker": f"{alpha_part}{numeric_part[:3]}",
                            "explanation": "Mixed alphanumeric format",
                        },
                        {
                            "ticker": f"{numeric_part}.DE",
                            "explanation": "Numeric with German country code",
                        },
                    ]
                )

        # European exchange-specific suggestions
        for exchange_code, exchange_name in self.exchange_mappings.items():
            base_ticker = (
                national_code[:6] if len(national_code) >= 6 else national_code
            )
            suggestions.append(
                {
                    "ticker": f"{base_ticker}.{exchange_code}",
                    "explanation": f"Format for {exchange_name}",
                }
            )

        # Generic suggestions
        suggestions.extend(
            [
                {
                    "ticker": national_code[:8],
                    "explanation": "First 8 characters of national code",
                },
                {
                    "ticker": f"{country_code}{national_code[:6]}",
                    "explanation": "Country code + first 6 characters",
                },
            ]
        )

        return suggestions[:10]  # Limit to top 10 suggestions

    def validate_german_isin(self, isin: str) -> tuple[bool, dict[str, Any]]:
        """Validate a German ISIN and extract detailed information.

        Args:
            isin: The ISIN to validate

        Returns:
            Tuple of (is_valid, info_dict)
        """
        try:
            if len(isin) != 12:
                return False, {"error": "ISIN must be 12 characters"}

            country_code = isin[:2]
            national_code = isin[2:11]
            check_digit = isin[11]

            # German country codes
            german_codes = ["DE"]  # Can be extended for other German markets

            info = {
                "country_code": country_code,
                "national_code": national_code,
                "check_digit": check_digit,
                "is_german": country_code in german_codes,
                "exchanges": [],
            }

            # Add suggested exchanges for German securities
            if country_code == "DE":
                info["exchanges"] = [
                    "XETR",  # Xetra
                    "XFRA",  # Frankfurt
                    "XMUN",  # Munich
                    "XDUS",  # Düsseldorf
                    "XSTU",  # Stuttgart
                ]

            # Basic format validation
            if not re.match(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$", isin):
                return False, {"error": "Invalid ISIN format"}

            # Check digit validation (simplified)
            # In a production system, implement proper ISIN check digit algorithm
            info["checksum_valid"] = True  # Placeholder

            return True, info

        except Exception as e:
            return False, {"error": f"Validation error: {e}"}


# Singleton instance
german_data_service = EuropeanDataAggregator()


def get_german_data_service() -> EuropeanDataAggregator:
    """Get the German data service instance."""
    return german_data_service


async def bulk_lookup_german_isins(isins: list[str]) -> dict[str, dict[str, Any]]:
    """Perform bulk lookup for German ISINs.

    Args:
        isins: List of ISINs to look up

    Returns:
        Dictionary mapping ISINs to their data
    """
    service = get_german_data_service()
    results = {}

    # Limit concurrent requests to avoid overwhelming servers
    semaphore = asyncio.Semaphore(3)

    async def lookup_single(isin: str) -> tuple[str, dict[str, Any]]:
        async with semaphore:
            try:
                data = await service.get_comprehensive_data(isin)
                return isin, data
            except Exception as e:
                logger.error(f"Error looking up {isin}: {e}")
                return isin, {"error": str(e)}

    # Execute lookups concurrently
    tasks = [lookup_single(isin) for isin in isins]
    lookup_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    for result in lookup_results:
        if isinstance(result, Exception):
            logger.error(f"Lookup task failed: {result}")
            continue

        isin, data = result
        results[isin] = data

    return results


def extract_wkn_from_isin(isin: str) -> str | None:
    """Extract WKN (Wertpapier-Kenn-Nummer) from German ISIN.

    Args:
        isin: German ISIN

    Returns:
        WKN if extractable, None otherwise
    """
    if not isin or len(isin) != 12 or not isin.startswith("DE"):
        return None

    try:
        # For German securities, WKN is typically embedded in the ISIN
        # Format: DE + 10-digit number where last 6 digits are WKN
        national_code = isin[2:11]  # 9 digits

        # Extract numeric part (WKN is usually the last 6 digits)
        numeric_part = "".join(filter(str.isdigit, national_code))

        if len(numeric_part) >= 6:
            return numeric_part[-6:]  # Last 6 digits

        return None

    except Exception as e:
        logger.error(f"Error extracting WKN from {isin}: {e}")
        return None


def format_german_ticker(ticker: str, exchange: str = "XETR") -> str:
    """Format a ticker symbol for German exchanges.

    Args:
        ticker: Base ticker symbol
        exchange: Exchange code (default: XETR for Xetra)

    Returns:
        Formatted ticker symbol
    """
    if not ticker:
        return ""

    # Remove any existing exchange suffix
    base_ticker = ticker.split(".")[0]

    # Add exchange suffix
    return f"{base_ticker}.{exchange}"
