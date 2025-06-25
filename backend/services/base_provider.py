"""Base classes and utilities for market data providers."""

from abc import ABC, abstractmethod
import logging
import time
from typing import Any

import requests

from backend.services.market_data import MarketDataResult
from backend.services.ticker_utils import TickerUtils

logger = logging.getLogger(__name__)


class RateLimiter:
    """Reusable rate limiter for API calls."""

    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.last_call_time = 0

    def wait_if_needed(self):
        """Wait if necessary to respect rate limits."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        if time_since_last_call < self.delay:
            sleep_time = self.delay - time_since_last_call
            logger.debug(f"Rate limit: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        self.last_call_time = time.time()


class BaseMarketDataProvider(ABC):
    """Base class for all market data providers with common functionality."""

    def __init__(self, name: str, rate_limit_delay: float = 1.0):
        self.name = name
        self.rate_limiter = RateLimiter(rate_limit_delay)
        self.timeout = 10
        self.headers = {
            "User-Agent": "Financial-Dashboard/1.0 (https://github.com/yourusername/financial-dashboard)"
        }

    def _make_request(self, url: str, params: dict | None = None) -> dict | None:
        """Make HTTP request with error handling."""
        try:
            self.rate_limiter.wait_if_needed()
            response = requests.get(
                url, params=params, headers=self.headers, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.warning(f"{self.name}: Request timed out for {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"{self.name}: Request failed - {e}")
            return None
        except ValueError as e:
            logger.warning(f"{self.name}: Failed to parse JSON - {e}")
            return None

    def _create_error_result(
        self, ticker: str, error: str, suggestions: list[str] | None = None
    ) -> MarketDataResult:
        """Create standardized error result."""
        return MarketDataResult(
            ticker=ticker,
            success=False,
            error=error,
            data_source=self.name,
            suggestions=suggestions,
        )

    def _get_ticker_suggestions(self, ticker: str) -> list[str]:
        """Get suggestions for international ticker formats."""
        ticker_info = TickerUtils.parse_ticker(ticker)
        suggestions = []

        if ticker_info.exchange_suffix:
            # Already has exchange suffix
            base = ticker_info.base_ticker
            suggestions.extend(
                [
                    base,  # Try without exchange
                    f"{base}.L",  # London
                    f"{base}.DE",  # XETRA
                    f"{base}.PA",  # Paris
                ]
            )
        else:
            # No exchange suffix
            suggestions.extend(
                [
                    f"{ticker}.L",  # London
                    f"{ticker}.DE",  # XETRA
                    f"{ticker}.PA",  # Paris
                    f"{ticker}.AS",  # Amsterdam
                    f"{ticker}.MI",  # Milan
                ]
            )

        # Remove the original ticker and duplicates
        suggestions = [s for s in suggestions if s != ticker]
        return list(
            dict.fromkeys(suggestions)
        )  # Remove duplicates while preserving order

    @abstractmethod
    def fetch_quote(self, ticker: str) -> MarketDataResult:
        """Fetch current quote for a ticker. Must be implemented by subclasses."""

    def fetch_multiple_quotes(self, tickers: list[str]) -> list[MarketDataResult]:
        """Fetch quotes for multiple tickers with rate limiting."""
        results = []
        for ticker in tickers:
            result = self.fetch_quote(ticker)
            results.append(result)
        return results


class BaseHTTPProvider(BaseMarketDataProvider):
    """Base class for HTTP-based market data providers."""

    def __init__(
        self, name: str, api_key: str | None = None, rate_limit_delay: float = 1.0
    ):
        super().__init__(name, rate_limit_delay)
        self.api_key = api_key

    def _build_request_params(self, **kwargs) -> dict:
        """Build request parameters including API key if available."""
        params = kwargs.copy()
        if self.api_key:
            params["apikey"] = self.api_key
        return params

    def _extract_price_data(
        self, data: dict, mappings: dict[str, str]
    ) -> dict[str, Any]:
        """Extract price data from response using field mappings."""
        result = {}
        for result_field, data_path in mappings.items():
            value = data
            for key in data_path.split("."):
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    value = None
                    break
            result[result_field] = value
        return result
