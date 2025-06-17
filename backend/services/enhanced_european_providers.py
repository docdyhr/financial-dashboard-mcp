"""Enhanced European market data providers using base provider classes.

This module provides updated European market data providers that utilize the new
BaseMarketDataProvider architecture for reduced code duplication and standardized
error handling.
"""

import logging
import re

from backend.services.base_provider import BaseHTTPProvider, BaseMarketDataProvider
from backend.services.market_data import MarketDataResult

logger = logging.getLogger(__name__)


class EnhancedDeutscheBorseProvider(BaseHTTPProvider):
    """Enhanced Deutsche Börse provider using base provider architecture."""

    def __init__(self):
        super().__init__(
            name="Deutsche Börse (Enhanced)",
            rate_limit_delay=1.0,  # 1 second between requests
        )
        self.base_url = "https://www.xetra.com"
        self.search_url = f"{self.base_url}/xetra-en/instruments/shares"

        # Deutsche Börse specific headers
        self.headers.update(
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",
            }
        )

    def fetch_quote(self, ticker: str) -> MarketDataResult:
        """Fetch quote from Deutsche Börse."""
        try:
            # Handle ISIN vs ticker format
            if self._is_isin(ticker):
                return self._fetch_by_isin(ticker)
            return self._fetch_by_ticker(ticker)

        except Exception as e:
            logger.error(f"Error fetching quote for {ticker}: {e}")
            return self._create_error_result(
                ticker,
                f"Deutsche Börse fetch failed: {e!s}",
                self._get_ticker_suggestions(ticker),
            )

    def _is_isin(self, identifier: str) -> bool:
        """Check if identifier is an ISIN."""
        return bool(re.match(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$", identifier))

    def _fetch_by_isin(self, isin: str) -> MarketDataResult:
        """Fetch quote using ISIN."""
        search_params = {"isin": isin, "market": "xetra"}

        # Use base class request method
        response_data = self._make_request(f"{self.search_url}/search", search_params)

        if not response_data:
            return self._create_error_result(
                isin,
                "No data returned from Deutsche Börse",
                [f"{isin}.DE", f"{isin}.XETR"],
            )

        # Parse the response and create result
        return self._parse_deutsche_borse_response(isin, response_data)

    def _fetch_by_ticker(self, ticker: str) -> MarketDataResult:
        """Fetch quote using ticker symbol."""
        # Deutsche Börse often requires specific formatting
        formatted_tickers = self._format_ticker_for_deutsche_borse(ticker)

        for formatted_ticker in formatted_tickers:
            search_params = {"symbol": formatted_ticker, "market": "xetr"}

            response_data = self._make_request(
                f"{self.search_url}/quote", search_params
            )

            if response_data:
                result = self._parse_deutsche_borse_response(ticker, response_data)
                if result.success:
                    return result

        return self._create_error_result(
            ticker,
            "Ticker not found on Deutsche Börse",
            self._get_ticker_suggestions(ticker),
        )

    def _format_ticker_for_deutsche_borse(self, ticker: str) -> list[str]:
        """Format ticker for Deutsche Börse searches."""
        formatted = []

        # Remove common suffixes and try different formats
        base_ticker = ticker.replace(".DE", "").replace(".XETR", "")

        formatted.extend(
            [
                base_ticker,
                f"{base_ticker}.DE",
                f"{base_ticker}.XETR",
                f"{base_ticker}.F",  # Frankfurt
                base_ticker.upper(),
                base_ticker.lower(),
            ]
        )

        return list(dict.fromkeys(formatted))  # Remove duplicates

    def _parse_deutsche_borse_response(
        self, ticker: str, data: dict
    ) -> MarketDataResult:
        """Parse Deutsche Börse API response."""
        try:
            # This is a simplified parser - actual implementation would depend
            # on the real Deutsche Börse API response format

            if "quote" in data:
                quote_data = data["quote"]

                return MarketDataResult(
                    ticker=ticker,
                    success=True,
                    current_price=float(quote_data.get("price", 0)),
                    day_change=float(quote_data.get("change", 0)),
                    day_change_percent=float(quote_data.get("changePercent", 0)),
                    volume=(
                        int(quote_data.get("volume", 0))
                        if quote_data.get("volume")
                        else None
                    ),
                    data_source=self.name,
                )

            return self._create_error_result(
                ticker, "Invalid response format from Deutsche Börse"
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Error parsing Deutsche Börse response: {e}")
            return self._create_error_result(
                ticker, f"Response parsing error: {e!s}"
            )


class EnhancedEuronextProvider(BaseHTTPProvider):
    """Enhanced Euronext provider for Paris, Amsterdam, Brussels, and Lisbon."""

    def __init__(self):
        super().__init__(
            name="Euronext (Enhanced)",
            rate_limit_delay=0.5,  # Faster rate limit for Euronext
        )
        self.base_url = "https://live.euronext.com"
        self.api_url = f"{self.base_url}/api"

        # Euronext markets
        self.markets = {
            "XPAR": "PA",  # Paris
            "XAMS": "AS",  # Amsterdam
            "XBRU": "BR",  # Brussels
            "XLIS": "LS",  # Lisbon
        }

    def fetch_quote(self, ticker: str) -> MarketDataResult:
        """Fetch quote from Euronext."""
        try:
            # Try different market formats
            for market_code, suffix in self.markets.items():
                formatted_ticker = self._format_ticker_for_market(ticker, suffix)

                result = self._fetch_from_euronext_api(formatted_ticker, market_code)
                if result.success:
                    return result

            # If no success, return error with suggestions
            return self._create_error_result(
                ticker,
                "Ticker not found on any Euronext market",
                self._get_euronext_suggestions(ticker),
            )

        except Exception as e:
            logger.error(f"Error fetching Euronext quote for {ticker}: {e}")
            return self._create_error_result(ticker, f"Euronext fetch failed: {e!s}")

    def _format_ticker_for_market(self, ticker: str, market_suffix: str) -> str:
        """Format ticker for specific Euronext market."""
        # Remove existing suffixes
        base_ticker = re.sub(r"\.(PA|AS|BR|LS|XPAR|XAMS|XBRU|XLIS)$", "", ticker)

        # Add market suffix if not already present
        if not ticker.endswith(f".{market_suffix}"):
            return f"{base_ticker}.{market_suffix}"

        return ticker

    def _fetch_from_euronext_api(
        self, ticker: str, market_code: str
    ) -> MarketDataResult:
        """Fetch from Euronext API for specific market."""
        # Simplified API call - actual implementation would use real Euronext API
        params = {"symbol": ticker, "market": market_code, "format": "json"}

        response_data = self._make_request(f"{self.api_url}/quote", params)

        if not response_data:
            return self._create_error_result(
                ticker, f"No data from Euronext {market_code}"
            )

        return self._parse_euronext_response(ticker, response_data, market_code)

    def _parse_euronext_response(
        self, ticker: str, data: dict, market_code: str
    ) -> MarketDataResult:
        """Parse Euronext API response."""
        try:
            # Simplified parsing - adjust based on actual Euronext API format
            if data.get("data"):
                quote = data["data"]

                return MarketDataResult(
                    ticker=ticker,
                    success=True,
                    current_price=float(quote.get("last", 0)),
                    day_change=float(quote.get("change", 0)),
                    day_change_percent=float(quote.get("changePercent", 0)),
                    volume=int(quote.get("volume", 0)) if quote.get("volume") else None,
                    high_price=(
                        float(quote.get("high", 0)) if quote.get("high") else None
                    ),
                    low_price=float(quote.get("low", 0)) if quote.get("low") else None,
                    data_source=self.name,
                )

            return self._create_error_result(
                ticker, "No quote data in Euronext response"
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Error parsing Euronext response: {e}")
            return self._create_error_result(
                ticker, f"Euronext parsing error: {e!s}"
            )

    def _get_euronext_suggestions(self, ticker: str) -> list[str]:
        """Get suggestions for Euronext ticker formats."""
        base_ticker = re.sub(r"\.(PA|AS|BR|LS)$", "", ticker)

        return [
            f"{base_ticker}.PA",  # Paris
            f"{base_ticker}.AS",  # Amsterdam
            f"{base_ticker}.BR",  # Brussels
            f"{base_ticker}.LS",  # Lisbon
        ]


class EnhancedLondonStockExchangeProvider(BaseHTTPProvider):
    """Enhanced London Stock Exchange provider."""

    def __init__(self):
        super().__init__(name="London Stock Exchange (Enhanced)", rate_limit_delay=1.0)
        self.base_url = "https://www.londonstockexchange.com"
        self.api_url = f"{self.base_url}/api"

        # LSE specific headers
        self.headers.update(
            {
                "Accept": "application/json, text/plain, */*",
                "Referer": self.base_url,
            }
        )

    def fetch_quote(self, ticker: str) -> MarketDataResult:
        """Fetch quote from London Stock Exchange."""
        try:
            formatted_tickers = self._format_ticker_for_lse(ticker)

            for formatted_ticker in formatted_tickers:
                result = self._fetch_from_lse_api(formatted_ticker)
                if result.success:
                    return result

            return self._create_error_result(
                ticker,
                "Ticker not found on London Stock Exchange",
                self._get_lse_suggestions(ticker),
            )

        except Exception as e:
            logger.error(f"Error fetching LSE quote for {ticker}: {e}")
            return self._create_error_result(ticker, f"LSE fetch failed: {e!s}")

    def _format_ticker_for_lse(self, ticker: str) -> list[str]:
        """Format ticker for LSE searches."""
        base_ticker = ticker.replace(".L", "").replace(".LON", "")

        return [
            f"{base_ticker}.L",
            f"{base_ticker}.LON",
            base_ticker,
            f"{base_ticker}.LSE",
        ]

    def _fetch_from_lse_api(self, ticker: str) -> MarketDataResult:
        """Fetch from LSE API."""
        params = {"symbol": ticker, "market": "XLON"}

        response_data = self._make_request(f"{self.api_url}/securities/quote", params)

        if not response_data:
            return self._create_error_result(ticker, "No data from LSE")

        return self._parse_lse_response(ticker, response_data)

    def _parse_lse_response(self, ticker: str, data: dict) -> MarketDataResult:
        """Parse LSE API response."""
        try:
            # Simplified LSE response parsing
            if "quote" in data:
                quote = data["quote"]

                return MarketDataResult(
                    ticker=ticker,
                    success=True,
                    current_price=float(quote.get("price", 0)),
                    day_change=float(quote.get("change", 0)),
                    day_change_percent=float(quote.get("changePercent", 0)),
                    volume=int(quote.get("volume", 0)) if quote.get("volume") else None,
                    data_source=self.name,
                )

            return self._create_error_result(ticker, "Invalid LSE response format")

        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Error parsing LSE response: {e}")
            return self._create_error_result(ticker, f"LSE parsing error: {e!s}")

    def _get_lse_suggestions(self, ticker: str) -> list[str]:
        """Get suggestions for LSE ticker formats."""
        base_ticker = ticker.replace(".L", "").replace(".LON", "")

        return [
            f"{base_ticker}.L",
            f"{base_ticker}.LON",
            f"{base_ticker}.LSE",
        ]


class EuropeanMarketDataAggregator(BaseMarketDataProvider):
    """Aggregator for European market data providers."""

    def __init__(self):
        super().__init__(name="European Markets Aggregator", rate_limit_delay=0.1)

        # Initialize enhanced providers
        self.providers = {
            "deutsche_borse": EnhancedDeutscheBorseProvider(),
            "euronext": EnhancedEuronextProvider(),
            "lse": EnhancedLondonStockExchangeProvider(),
        }

        # Provider priority based on ticker format
        self.provider_priority = {
            "DE": ["deutsche_borse", "euronext"],
            "GB": ["lse", "euronext"],
            "FR": ["euronext", "deutsche_borse"],
            "NL": ["euronext", "deutsche_borse"],
            "BE": ["euronext", "deutsche_borse"],
            "IT": ["euronext", "deutsche_borse"],
            "ES": ["euronext", "deutsche_borse"],
        }

    def fetch_quote(self, ticker: str) -> MarketDataResult:
        """Fetch quote using the most appropriate provider."""
        try:
            # Determine provider order based on ticker
            provider_order = self._get_provider_order(ticker)

            last_error = None
            for provider_name in provider_order:
                provider = self.providers[provider_name]

                try:
                    result = provider.fetch_quote(ticker)
                    if result.success:
                        # Add aggregator info
                        result.data_source = f"{self.name} -> {result.data_source}"
                        return result
                    last_error = result.error
                except Exception as e:
                    last_error = str(e)
                    continue

            # All providers failed
            all_suggestions = []
            for provider in self.providers.values():
                all_suggestions.extend(provider._get_ticker_suggestions(ticker))

            return self._create_error_result(
                ticker,
                f"All European providers failed. Last error: {last_error}",
                list(dict.fromkeys(all_suggestions)),  # Remove duplicates
            )

        except Exception as e:
            logger.error(f"Error in European aggregator for {ticker}: {e}")
            return self._create_error_result(ticker, f"Aggregator error: {e!s}")

    def _get_provider_order(self, ticker: str) -> list[str]:
        """Determine provider order based on ticker characteristics."""
        # Analyze ticker format to prioritize providers
        ticker_upper = ticker.upper()

        # Check for exchange suffixes
        if any(suffix in ticker_upper for suffix in [".DE", ".XETR", ".F"]):
            return ["deutsche_borse", "euronext", "lse"]
        if any(suffix in ticker_upper for suffix in [".L", ".LON", ".LSE"]):
            return ["lse", "euronext", "deutsche_borse"]
        if any(suffix in ticker_upper for suffix in [".PA", ".AS", ".BR"]):
            return ["euronext", "deutsche_borse", "lse"]

        # Check for country patterns in ISIN
        if re.match(r"^DE", ticker):
            return ["deutsche_borse", "euronext", "lse"]
        if re.match(r"^GB", ticker):
            return ["lse", "euronext", "deutsche_borse"]
        if re.match(r"^(FR|NL|BE|IT|ES)", ticker):
            return ["euronext", "deutsche_borse", "lse"]

        # Default order
        return ["euronext", "deutsche_borse", "lse"]

    def get_provider_status(self) -> dict[str, dict]:
        """Get status of all providers."""
        status = {}

        for name, provider in self.providers.items():
            # Test provider with a dummy request
            test_result = provider._create_error_result("TEST", "Status check")

            status[name] = {
                "name": provider.name,
                "rate_limit_delay": provider.rate_limiter.delay,
                "available": True,  # Would check actual availability in real implementation
                "last_error": None,
            }

        return status


# Singleton instances
enhanced_deutsche_borse_provider = EnhancedDeutscheBorseProvider()
enhanced_euronext_provider = EnhancedEuronextProvider()
enhanced_lse_provider = EnhancedLondonStockExchangeProvider()
european_market_aggregator = EuropeanMarketDataAggregator()


def get_enhanced_deutsche_borse_provider() -> EnhancedDeutscheBorseProvider:
    """Get the enhanced Deutsche Börse provider instance."""
    return enhanced_deutsche_borse_provider


def get_enhanced_euronext_provider() -> EnhancedEuronextProvider:
    """Get the enhanced Euronext provider instance."""
    return enhanced_euronext_provider


def get_enhanced_lse_provider() -> EnhancedLondonStockExchangeProvider:
    """Get the enhanced LSE provider instance."""
    return enhanced_lse_provider


def get_european_market_aggregator() -> EuropeanMarketDataAggregator:
    """Get the European market data aggregator instance."""
    return european_market_aggregator
