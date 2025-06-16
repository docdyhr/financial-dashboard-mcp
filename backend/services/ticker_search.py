"""Ticker search and validation utilities for finding correct European ticker symbols."""

import logging
import time

import requests
import yfinance as yf

from backend.services.ticker_utils import TickerUtils

logger = logging.getLogger(__name__)


class TickerSearchService:
    """Service to search and validate ticker symbols, especially for European markets."""

    def __init__(self):
        self.rate_limit_delay = 2.0  # 2 seconds between API calls
        self.last_call_time = 0

    def _respect_rate_limit(self):
        """Ensure we don't exceed rate limits."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        if time_since_last_call < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_call
            time.sleep(sleep_time)
        self.last_call_time = time.time()

    def search_ticker(
        self, query: str, country_hint: str | None = None
    ) -> list[dict[str, str]]:
        """Search for ticker symbols using Yahoo Finance search.

        Args:
            query: Company name or partial ticker
            country_hint: Country code hint (e.g., 'DE', 'GB', 'FR')

        Returns:
            List of potential ticker matches with their details
        """
        try:
            self._respect_rate_limit()

            # Use Yahoo Finance search API
            search_url = "https://query2.finance.yahoo.com/v1/finance/search"
            params = {
                "q": query,
                "quotesCount": 10,
                "newsCount": 0,
                "enableFuzzyQuery": True,
                "quotesQueryId": "tss_match_phrase_query",
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(
                search_url, params=params, headers=headers, timeout=10
            )
            response.raise_for_status()

            data = response.json()
            results = []

            quotes = data.get("quotes", [])
            for quote in quotes:
                symbol = quote.get("symbol", "")
                short_name = quote.get("shortname", "")
                long_name = quote.get("longname", "")
                exchange = quote.get("exchange", "")
                quote_type = quote.get("quoteType", "")

                # Parse ticker info
                ticker_info = TickerUtils.parse_ticker(symbol)

                # Filter by country if hint provided
                if country_hint and ticker_info.country_code:
                    if ticker_info.country_code.upper() != country_hint.upper():
                        continue

                results.append(
                    {
                        "symbol": symbol,
                        "name": long_name or short_name,
                        "short_name": short_name,
                        "exchange": exchange,
                        "quote_type": quote_type,
                        "country": ticker_info.country_code,
                        "currency": ticker_info.default_currency,
                        "exchange_name": ticker_info.exchange_name,
                        "is_european": TickerUtils.is_european_ticker(symbol),
                    }
                )

            return results

        except Exception as e:
            logger.error(f"Error searching for ticker '{query}': {e}")
            return []

    def validate_ticker(
        self, ticker: str
    ) -> tuple[bool, str | None, dict[str, str] | None]:
        """Validate if a ticker symbol exists and can be fetched.

        Args:
            ticker: Ticker symbol to validate

        Returns:
            Tuple of (is_valid, error_message, ticker_info)
        """
        try:
            # First validate format
            is_valid_format, format_error = TickerUtils.validate_ticker_format(ticker)
            if not is_valid_format:
                return False, format_error, None

            self._respect_rate_limit()

            # Try to fetch basic info from Yahoo Finance
            stock = yf.Ticker(ticker)

            # Try to get recent history (minimal request)
            hist = stock.history(period="1d")

            if hist.empty:
                # Try info if history fails
                try:
                    info = stock.info
                    if info and len(info) > 1 and "regularMarketPrice" in info:
                        ticker_info = TickerUtils.parse_ticker(ticker)
                        return (
                            True,
                            None,
                            {
                                "symbol": ticker,
                                "name": info.get("longName", "Unknown"),
                                "exchange": info.get("exchange", ""),
                                "currency": info.get(
                                    "currency", ticker_info.default_currency
                                ),
                                "country": ticker_info.country_code,
                                "price": info.get("regularMarketPrice"),
                            },
                        )
                except Exception:
                    pass

                return False, f"No data available for ticker {ticker}", None

            # Success - ticker exists and has data
            ticker_info = TickerUtils.parse_ticker(ticker)
            latest_close = hist["Close"].iloc[-1]

            return (
                True,
                None,
                {
                    "symbol": ticker,
                    "name": "Unknown",  # Would need additional API call to get name
                    "exchange": ticker_info.exchange_name,
                    "currency": ticker_info.default_currency,
                    "country": ticker_info.country_code,
                    "price": float(latest_close),
                },
            )

        except Exception as e:
            return False, f"Error validating ticker {ticker}: {e!s}", None

    def suggest_alternatives(self, failed_ticker: str) -> list[dict[str, str]]:
        """Suggest alternative ticker symbols when one fails.

        Args:
            failed_ticker: The ticker that failed to fetch

        Returns:
            List of suggested alternative tickers
        """
        suggestions = []

        try:
            ticker_info = TickerUtils.parse_ticker(failed_ticker)
            base_ticker = ticker_info.base_ticker

            # If it's a European ticker, try different exchanges
            if ticker_info.is_international and ticker_info.exchange_suffix:
                # Try major European exchanges
                alternative_exchanges = [".L", ".PA", ".DE", ".MI", ".AS", ".SW"]

                for alt_exchange in alternative_exchanges:
                    if alt_exchange != f".{ticker_info.exchange_suffix}":
                        alt_ticker = f"{base_ticker}{alt_exchange}"
                        suggestions.append(
                            {
                                "symbol": alt_ticker,
                                "reason": f'Try {base_ticker} on {TickerUtils.EXCHANGE_INFO[alt_exchange]["name"]}',
                                "exchange": TickerUtils.EXCHANGE_INFO[alt_exchange][
                                    "name"
                                ],
                                "country": TickerUtils.EXCHANGE_INFO[alt_exchange][
                                    "country"
                                ],
                            }
                        )

            # If it's a failed European ticker, suggest US version
            if ticker_info.is_international:
                suggestions.append(
                    {
                        "symbol": base_ticker,
                        "reason": f"Try US-listed version of {base_ticker}",
                        "exchange": "US (NYSE/NASDAQ)",
                        "country": "US",
                    }
                )

            # Search for similar company names
            search_results = self.search_ticker(base_ticker)
            for result in search_results[:3]:  # Top 3 search results
                if result["symbol"] != failed_ticker:
                    suggestions.append(
                        {
                            "symbol": result["symbol"],
                            "reason": f'Similar: {result["name"]}',
                            "exchange": result["exchange_name"],
                            "country": result["country"],
                        }
                    )

        except Exception as e:
            logger.error(f"Error generating suggestions for {failed_ticker}: {e}")

        return suggestions

    def find_european_ticker(
        self, company_name: str, country: str | None = None
    ) -> list[dict[str, str]]:
        """Find European ticker symbols for a company name.

        Args:
            company_name: Name of the company to search for
            country: Optional country code to filter results

        Returns:
            List of European ticker matches
        """
        results = self.search_ticker(company_name, country)

        # Filter for European tickers only
        european_results = [
            result for result in results if result.get("is_european", False)
        ]

        return european_results

    def get_ticker_recommendations(self, user_input: str) -> dict[str, any]:
        """Get comprehensive ticker recommendations based on user input.

        Args:
            user_input: User's ticker or company name input

        Returns:
            Dictionary with validation results and recommendations
        """
        recommendations = {
            "input": user_input,
            "is_valid": False,
            "error": None,
            "ticker_info": None,
            "suggestions": [],
            "search_results": [],
        }

        # Clean the input
        cleaned_input = user_input.strip().upper()

        # First, try to validate as-is
        is_valid, error, ticker_info = self.validate_ticker(cleaned_input)
        recommendations["is_valid"] = is_valid
        recommendations["error"] = error
        recommendations["ticker_info"] = ticker_info

        # If not valid, provide suggestions
        if not is_valid:
            # Generate suggestions
            recommendations["suggestions"] = self.suggest_alternatives(cleaned_input)

            # If it looks like a company name (contains spaces or is >5 chars), search for it
            if " " in user_input or len(user_input) > 5:
                recommendations["search_results"] = self.search_ticker(user_input)[:5]

        return recommendations


# Global instance
ticker_search_service = TickerSearchService()
