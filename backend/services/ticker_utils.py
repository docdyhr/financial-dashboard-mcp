"""Utility functions for handling ticker symbols, especially European and international tickers."""

from dataclasses import dataclass
import re


@dataclass
class TickerInfo:
    """Information about a ticker symbol."""

    base_ticker: str
    exchange_suffix: str | None
    exchange_name: str | None
    country_code: str | None
    default_currency: str | None
    market_timezone: str | None
    is_international: bool


class TickerUtils:
    """Utility class for handling ticker symbols and exchange information."""

    # Exchange suffix mappings with detailed information
    EXCHANGE_INFO = {
        # European Exchanges
        ".L": {
            "name": "London Stock Exchange",
            "country": "GB",
            "currency": "GBP",
            "timezone": "Europe/London",
            "yfinance_format": "{base}.L",
        },
        ".PA": {
            "name": "Euronext Paris",
            "country": "FR",
            "currency": "EUR",
            "timezone": "Europe/Paris",
            "yfinance_format": "{base}.PA",
        },
        ".DE": {
            "name": "Frankfurt/XETRA",
            "country": "DE",
            "currency": "EUR",
            "timezone": "Europe/Berlin",
            "yfinance_format": "{base}.DE",
        },
        ".MI": {
            "name": "Borsa Italiana (Milan)",
            "country": "IT",
            "currency": "EUR",
            "timezone": "Europe/Rome",
            "yfinance_format": "{base}.MI",
        },
        ".AS": {
            "name": "Euronext Amsterdam",
            "country": "NL",
            "currency": "EUR",
            "timezone": "Europe/Amsterdam",
            "yfinance_format": "{base}.AS",
        },
        ".BR": {
            "name": "Euronext Brussels",
            "country": "BE",
            "currency": "EUR",
            "timezone": "Europe/Brussels",
            "yfinance_format": "{base}.BR",
        },
        ".LS": {
            "name": "Euronext Lisbon",
            "country": "PT",
            "currency": "EUR",
            "timezone": "Europe/Lisbon",
            "yfinance_format": "{base}.LS",
        },
        ".MC": {
            "name": "Bolsa de Madrid",
            "country": "ES",
            "currency": "EUR",
            "timezone": "Europe/Madrid",
            "yfinance_format": "{base}.MC",
        },
        ".VI": {
            "name": "Wiener Börse (Vienna)",
            "country": "AT",
            "currency": "EUR",
            "timezone": "Europe/Vienna",
            "yfinance_format": "{base}.VI",
        },
        ".SW": {
            "name": "SIX Swiss Exchange",
            "country": "CH",
            "currency": "CHF",
            "timezone": "Europe/Zurich",
            "yfinance_format": "{base}.SW",
        },
        # Nordic Exchanges
        ".ST": {
            "name": "Nasdaq Stockholm",
            "country": "SE",
            "currency": "SEK",
            "timezone": "Europe/Stockholm",
            "yfinance_format": "{base}.ST",
        },
        ".HE": {
            "name": "Nasdaq Helsinki",
            "country": "FI",
            "currency": "EUR",
            "timezone": "Europe/Helsinki",
            "yfinance_format": "{base}.HE",
        },
        ".OL": {
            "name": "Oslo Børs",
            "country": "NO",
            "currency": "NOK",
            "timezone": "Europe/Oslo",
            "yfinance_format": "{base}.OL",
        },
        ".CO": {
            "name": "Nasdaq Copenhagen",
            "country": "DK",
            "currency": "DKK",
            "timezone": "Europe/Copenhagen",
            "yfinance_format": "{base}.CO",
        },
        ".IC": {
            "name": "Nasdaq Iceland",
            "country": "IS",
            "currency": "ISK",
            "timezone": "Atlantic/Reykjavik",
            "yfinance_format": "{base}.IC",
        },
        # North American Exchanges
        ".TO": {
            "name": "Toronto Stock Exchange",
            "country": "CA",
            "currency": "CAD",
            "timezone": "America/Toronto",
            "yfinance_format": "{base}.TO",
        },
        ".V": {
            "name": "TSX Venture Exchange",
            "country": "CA",
            "currency": "CAD",
            "timezone": "America/Toronto",
            "yfinance_format": "{base}.V",
        },
        # Asia-Pacific Exchanges
        ".AX": {
            "name": "Australian Securities Exchange",
            "country": "AU",
            "currency": "AUD",
            "timezone": "Australia/Sydney",
            "yfinance_format": "{base}.AX",
        },
        ".T": {
            "name": "Tokyo Stock Exchange",
            "country": "JP",
            "currency": "JPY",
            "timezone": "Asia/Tokyo",
            "yfinance_format": "{base}.T",
        },
        ".HK": {
            "name": "Hong Kong Stock Exchange",
            "country": "HK",
            "currency": "HKD",
            "timezone": "Asia/Hong_Kong",
            "yfinance_format": "{base}.HK",
        },
        ".SG": {
            "name": "Singapore Exchange",
            "country": "SG",
            "currency": "SGD",
            "timezone": "Asia/Singapore",
            "yfinance_format": "{base}.SI",  # Note: Yahoo uses .SI for Singapore
        },
        ".KS": {
            "name": "Korea Stock Exchange",
            "country": "KR",
            "currency": "KRW",
            "timezone": "Asia/Seoul",
            "yfinance_format": "{base}.KS",
        },
        ".SS": {
            "name": "Shanghai Stock Exchange",
            "country": "CN",
            "currency": "CNY",
            "timezone": "Asia/Shanghai",
            "yfinance_format": "{base}.SS",
        },
        ".SZ": {
            "name": "Shenzhen Stock Exchange",
            "country": "CN",
            "currency": "CNY",
            "timezone": "Asia/Shanghai",
            "yfinance_format": "{base}.SZ",
        },
        # Indian Exchanges
        ".NS": {
            "name": "National Stock Exchange of India",
            "country": "IN",
            "currency": "INR",
            "timezone": "Asia/Kolkata",
            "yfinance_format": "{base}.NS",
        },
        ".BO": {
            "name": "Bombay Stock Exchange",
            "country": "IN",
            "currency": "INR",
            "timezone": "Asia/Kolkata",
            "yfinance_format": "{base}.BO",
        },
        # South American Exchanges
        ".SA": {
            "name": "B3 (Brazil Stock Exchange)",
            "country": "BR",
            "currency": "BRL",
            "timezone": "America/Sao_Paulo",
            "yfinance_format": "{base}.SA",
        },
    }

    # US Exchange patterns (no suffix)
    US_EXCHANGES = {
        "NYSE": {
            "name": "New York Stock Exchange",
            "country": "US",
            "currency": "USD",
            "timezone": "America/New_York",
        },
        "NASDAQ": {
            "name": "NASDAQ",
            "country": "US",
            "currency": "USD",
            "timezone": "America/New_York",
        },
    }

    @classmethod
    def parse_ticker(cls, ticker: str) -> TickerInfo:
        """Parse a ticker symbol and return detailed information."""
        ticker = ticker.upper().strip()

        if "." in ticker:
            base_ticker, suffix = ticker.rsplit(".", 1)
            suffix_key = "." + suffix

            if suffix_key in cls.EXCHANGE_INFO:
                exchange_info = cls.EXCHANGE_INFO[suffix_key]
                return TickerInfo(
                    base_ticker=base_ticker,
                    exchange_suffix=suffix,
                    exchange_name=exchange_info["name"],
                    country_code=exchange_info["country"],
                    default_currency=exchange_info["currency"],
                    market_timezone=exchange_info["timezone"],
                    is_international=True,
                )
            # Unknown suffix
            return TickerInfo(
                base_ticker=base_ticker,
                exchange_suffix=suffix,
                exchange_name=f"Unknown Exchange (.{suffix})",
                country_code=None,
                default_currency=None,
                market_timezone=None,
                is_international=True,
            )
        # Assume US ticker
        return TickerInfo(
            base_ticker=ticker,
            exchange_suffix=None,
            exchange_name="US Exchange (NYSE/NASDAQ)",
            country_code="US",
            default_currency="USD",
            market_timezone="America/New_York",
            is_international=False,
        )

    @classmethod
    def format_for_yfinance(cls, ticker: str) -> str:
        """Format a ticker for Yahoo Finance API."""
        ticker_info = cls.parse_ticker(ticker)

        if not ticker_info.is_international:
            return ticker_info.base_ticker

        suffix_key = (
            "." + ticker_info.exchange_suffix if ticker_info.exchange_suffix else ""
        )

        if suffix_key in cls.EXCHANGE_INFO:
            exchange_info = cls.EXCHANGE_INFO[suffix_key]
            return exchange_info["yfinance_format"].format(base=ticker_info.base_ticker)
        # Return as-is for unknown suffixes
        return ticker

    @classmethod
    def format_for_alpha_vantage(cls, ticker: str) -> str:
        """Format a ticker for Alpha Vantage API."""
        ticker_info = cls.parse_ticker(ticker)

        if not ticker_info.is_international:
            return ticker_info.base_ticker

        # Alpha Vantage typically uses the original format for international tickers
        return ticker

    @classmethod
    def validate_ticker_format(cls, ticker: str) -> tuple[bool, str | None]:
        """Validate a ticker format and return (is_valid, error_message)."""
        if not ticker or not ticker.strip():
            return False, "Ticker cannot be empty"

        ticker = ticker.upper().strip()

        # Check for valid characters (alphanumeric, dots, and hyphens)
        if not re.match(r"^[A-Z0-9.-]+$", ticker):
            return False, "Ticker can only contain letters, numbers, dots, and hyphens"

        # Check format
        if "." in ticker:
            parts = ticker.split(".")
            if len(parts) != 2:
                return (
                    False,
                    "International tickers must have exactly one dot separator",
                )

            base_ticker, suffix = parts
            if not base_ticker or not suffix:
                return False, "Both base ticker and exchange suffix are required"

            if len(base_ticker) < 1 or len(base_ticker) > 15:
                return False, "Base ticker must be between 1 and 15 characters"

            if len(suffix) < 1 or len(suffix) > 3:
                return False, "Exchange suffix must be between 1 and 3 characters"
        # US ticker
        elif len(ticker) < 1 or len(ticker) > 10:
            return False, "US ticker must be between 1 and 10 characters"

        return True, None

    @classmethod
    def get_supported_exchanges(cls) -> dict[str, dict[str, str]]:
        """Get list of all supported exchanges."""
        result = {}

        # Add international exchanges
        for suffix, info in cls.EXCHANGE_INFO.items():
            result[suffix] = {
                "name": info["name"],
                "country": info["country"],
                "currency": info["currency"],
                "timezone": info["timezone"],
            }

        # Add US exchanges
        result["US"] = {
            "name": "US Exchanges (NYSE/NASDAQ)",
            "country": "US",
            "currency": "USD",
            "timezone": "America/New_York",
        }

        return result

    @classmethod
    def suggest_ticker_format(
        cls, ticker: str, exchange_hint: str | None = None
    ) -> str:
        """Suggest proper ticker format based on exchange hint."""
        ticker = ticker.upper().strip()

        if not exchange_hint:
            return ticker

        exchange_hint = exchange_hint.upper()

        # Map exchange names to suffixes
        exchange_mapping = {
            "LONDON": ".L",
            "LSE": ".L",
            "PARIS": ".PA",
            "EURONEXT PARIS": ".PA",
            "FRANKFURT": ".DE",
            "XETRA": ".DE",
            "MILAN": ".MI",
            "AMSTERDAM": ".AS",
            "BRUSSELS": ".BR",
            "MADRID": ".MC",
            "VIENNA": ".VI",
            "SWISS": ".SW",
            "ZURICH": ".SW",
            "STOCKHOLM": ".ST",
            "HELSINKI": ".HE",
            "OSLO": ".OL",
            "COPENHAGEN": ".CO",
            "TORONTO": ".TO",
            "TSX": ".TO",
            "AUSTRALIA": ".AX",
            "ASX": ".AX",
            "TOKYO": ".T",
            "HONG KONG": ".HK",
            "SINGAPORE": ".SG",
            "KOREA": ".KS",
            "SHANGHAI": ".SS",
            "SHENZHEN": ".SZ",
            "NSE": ".NS",
            "BSE": ".BO",
            "BRAZIL": ".SA",
        }

        for name, suffix in exchange_mapping.items():
            if name in exchange_hint:
                if not ticker.endswith(suffix):
                    return f"{ticker}{suffix}"
                break

        return ticker

    @classmethod
    def is_european_ticker(cls, ticker: str) -> bool:
        """Check if a ticker is from a European exchange."""
        ticker_info = cls.parse_ticker(ticker)

        if not ticker_info.is_international:
            return False

        european_countries = {
            "GB",
            "FR",
            "DE",
            "IT",
            "NL",
            "BE",
            "PT",
            "ES",
            "AT",
            "CH",
            "SE",
            "FI",
            "NO",
            "DK",
            "IS",
        }
        return ticker_info.country_code in european_countries

    @classmethod
    def get_market_hours_info(cls, ticker: str) -> dict[str, str] | None:
        """Get market hours information for a ticker's exchange."""
        ticker_info = cls.parse_ticker(ticker)

        if ticker_info.market_timezone:
            return {
                "timezone": ticker_info.market_timezone,
                "exchange": ticker_info.exchange_name or "Unknown",
                "country": ticker_info.country_code or "Unknown",
            }

        return None
