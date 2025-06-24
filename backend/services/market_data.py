"""Multi-provider market data service with fallback capabilities."""

import logging
import time
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import requests
import yfinance as yf
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.models.asset import Asset
from backend.models.price_history import PriceHistory
from backend.services.isin_utils import ISINUtils, isin_service
from backend.services.ticker_utils import TickerUtils

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class MarketDataResult:
    """Result from market data fetch operation."""

    ticker: str
    current_price: float | None = None
    open_price: float | None = None
    high_price: float | None = None
    low_price: float | None = None
    volume: int | None = None
    previous_close: float | None = None
    day_change: float | None = None
    day_change_percent: float | None = None
    data_source: str | None = None
    success: bool = False
    error: str | None = None
    suggestions: list[str] | None = None


class MarketDataProvider:
    """Base class for market data providers."""

    def __init__(self, name: str):
        self.name = name

    def fetch_quote(self, ticker: str) -> MarketDataResult:
        """Fetch current quote for a ticker."""
        raise NotImplementedError

    def fetch_multiple_quotes(self, tickers: list[str]) -> list[MarketDataResult]:
        """Fetch quotes for multiple tickers."""
        results = []
        for ticker in tickers:
            result = self.fetch_quote(ticker)
            results.append(result)
            # Add small delay to respect rate limits
            time.sleep(0.1)
        return results


class YFinanceProvider(MarketDataProvider):
    """Yahoo Finance provider with international ticker support."""

    def __init__(self):
        super().__init__("yfinance")
        self.rate_limit_delay = 1.0  # 1 second between calls
        self.last_call_time = 0

    def _respect_rate_limit(self):
        """Ensure we don't exceed rate limits."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        if time_since_last_call < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_call
            logger.debug(f"YFinance rate limit: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        self.last_call_time = time.time()

    def fetch_quote(self, ticker: str) -> MarketDataResult:
        """Fetch quote using yfinance."""
        try:
            self._respect_rate_limit()
            # Format ticker for Yahoo Finance (handles European and international formats)
            yf_ticker = TickerUtils.format_for_yfinance(ticker)
            ticker_info = TickerUtils.parse_ticker(ticker)

            logger.debug(
                f"Fetching {ticker} (formatted as {yf_ticker}) from Yahoo Finance"
            )

            stock = yf.Ticker(yf_ticker)

            # Get historical data - try different periods for better reliability
            hist = None
            for period in ["2d", "5d", "1mo"]:
                try:
                    hist = stock.history(period=period)
                    if not hist.empty:
                        break
                except Exception as period_error:
                    logger.debug(
                        f"Failed to get {period} data for {yf_ticker}: {period_error}"
                    )
                    continue

            if hist is None or hist.empty:
                # Try to get basic info from Yahoo Finance
                try:
                    info = stock.info
                    if info and "regularMarketPrice" in info:
                        current_price = float(info["regularMarketPrice"])
                        return MarketDataResult(
                            ticker=ticker,
                            current_price=current_price,
                            data_source=self.name,
                            success=True,
                        )
                except Exception as e:
                    # Continue to try alternative data sources, but log the error
                    logger.debug(f"Failed to get basic info for {yf_ticker}: {e}")

                error_msg = "No historical data available"
                if ticker_info.is_international:
                    error_msg += f" for international ticker {ticker} (exchange: {ticker_info.exchange_name})"

                return MarketDataResult(
                    ticker=ticker,
                    success=False,
                    error=error_msg,
                    data_source=self.name,
                )

            # Get the most recent price
            current_price = float(hist["Close"].iloc[-1])
            open_price = float(hist["Open"].iloc[-1])
            high_price = float(hist["High"].iloc[-1])
            low_price = float(hist["Low"].iloc[-1])
            volume = (
                int(hist["Volume"].iloc[-1])
                if "Volume" in hist.columns and hist["Volume"].iloc[-1] > 0
                else None
            )

            # Calculate previous close and changes
            previous_close = None
            day_change = None
            day_change_percent = None

            if len(hist) > 1:
                previous_close = float(hist["Close"].iloc[-2])
                day_change = current_price - previous_close
                day_change_percent = (
                    (day_change / previous_close) * 100 if previous_close != 0 else 0
                )

            success_msg = f"Successfully fetched {ticker}"
            if ticker_info.is_international:
                success_msg += f" from {ticker_info.exchange_name} ({ticker_info.default_currency})"
            logger.debug(success_msg)

            return MarketDataResult(
                ticker=ticker,
                current_price=current_price,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                volume=volume,
                previous_close=previous_close,
                day_change=day_change,
                day_change_percent=day_change_percent,
                data_source=self.name,
                success=True,
            )

        except Exception as e:
            error_msg = f"yFinance failed for {ticker}: {e}"
            ticker_info = TickerUtils.parse_ticker(ticker)
            suggestions = []

            if ticker_info.is_international:
                error_msg += f" (Exchange: {ticker_info.exchange_name}, try format: {TickerUtils.format_for_yfinance(ticker)})"
                # Add suggestions for European tickers
                base_ticker = ticker_info.base_ticker
                if ticker_info.exchange_suffix:
                    alternative_exchanges = [".L", ".PA", ".DE", ".MI", ".AS"]
                    for alt_ex in alternative_exchanges:
                        if alt_ex != f".{ticker_info.exchange_suffix}":
                            suggestions.append(f"{base_ticker}{alt_ex}")
                # Also suggest US version
                suggestions.append(base_ticker)

            logger.warning(error_msg)
            return MarketDataResult(
                ticker=ticker,
                success=False,
                error=str(e),
                data_source=self.name,
                suggestions=suggestions,
            )


class AlphaVantageProvider(MarketDataProvider):
    """Alpha Vantage provider."""

    def __init__(self, api_key: str):
        super().__init__("alpha_vantage")
        settings = get_settings()
        self.api_key = api_key
        self.base_url = settings.alpha_vantage_base_url
        self.rate_limit_delay = settings.alpha_vantage_rate_limit_delay
        self.last_call_time = 0

    def _respect_rate_limit(self):
        """Ensure we don't exceed rate limits."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        if time_since_last_call < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_call
            logger.info(f"Alpha Vantage rate limit: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        self.last_call_time = time.time()

    def fetch_quote(self, ticker: str) -> MarketDataResult:
        """Fetch quote using Alpha Vantage."""
        try:
            self._respect_rate_limit()

            # Format ticker for Alpha Vantage
            av_ticker = TickerUtils.format_for_alpha_vantage(ticker)
            ticker_info = TickerUtils.parse_ticker(ticker)

            logger.debug(
                f"Fetching {ticker} (formatted as {av_ticker}) from Alpha Vantage"
            )

            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": av_ticker,
                "apikey": self.api_key,
            }

            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            # Check for API error messages
            if "Error Message" in data:
                error_msg = data["Error Message"]
                if ticker_info.is_international:
                    error_msg += f" (International ticker: {ticker}, Exchange: {ticker_info.exchange_name})"
                return MarketDataResult(
                    ticker=ticker,
                    success=False,
                    error=error_msg,
                    data_source=self.name,
                )

            if "Note" in data:
                return MarketDataResult(
                    ticker=ticker,
                    success=False,
                    error="API rate limit exceeded",
                    data_source=self.name,
                )

            quote = data.get("Global Quote", {})
            if not quote:
                error_msg = "No quote data in response"
                if ticker_info.is_international:
                    error_msg += f" for {ticker} ({ticker_info.exchange_name})"
                return MarketDataResult(
                    ticker=ticker,
                    success=False,
                    error=error_msg,
                    data_source=self.name,
                )

            # Parse Alpha Vantage response
            current_price = float(quote.get("05. price", 0))
            open_price = float(quote.get("02. open", 0))
            high_price = float(quote.get("03. high", 0))
            low_price = float(quote.get("04. low", 0))
            volume = (
                int(quote.get("06. volume", 0)) if quote.get("06. volume") else None
            )
            previous_close = float(quote.get("08. previous close", 0))
            change = float(quote.get("09. change", 0))
            change_percent = quote.get("10. change percent", "0%").replace("%", "")
            change_percent = float(change_percent) if change_percent else 0

            success_msg = f"Successfully fetched {ticker} from Alpha Vantage"
            if ticker_info.is_international:
                success_msg += (
                    f" ({ticker_info.exchange_name}, {ticker_info.default_currency})"
                )
            logger.debug(success_msg)

            return MarketDataResult(
                ticker=ticker,
                current_price=current_price if current_price > 0 else None,
                open_price=open_price if open_price > 0 else None,
                high_price=high_price if high_price > 0 else None,
                low_price=low_price if low_price > 0 else None,
                volume=volume,
                previous_close=previous_close if previous_close > 0 else None,
                day_change=change if change != 0 else None,
                day_change_percent=change_percent if change_percent != 0 else None,
                data_source=self.name,
                success=True,
            )

        except Exception as e:
            error_msg = f"Alpha Vantage failed for {ticker}: {e}"
            ticker_info = TickerUtils.parse_ticker(ticker)
            suggestions = []

            if ticker_info.is_international:
                error_msg += f" (Exchange: {ticker_info.exchange_name})"
                # Add suggestions for European tickers
                base_ticker = ticker_info.base_ticker
                suggestions.append(base_ticker)  # Try US version

            logger.warning(error_msg)
            return MarketDataResult(
                ticker=ticker,
                success=False,
                error=str(e),
                data_source=self.name,
                suggestions=suggestions,
            )


class FinnhubProvider(MarketDataProvider):
    """Finnhub provider."""

    def __init__(self, api_key: str):
        super().__init__("finnhub")
        settings = get_settings()
        self.api_key = api_key
        self.base_url = settings.finnhub_base_url
        self.rate_limit_delay = settings.finnhub_rate_limit_delay
        self.last_call_time = 0

    def _respect_rate_limit(self):
        """Ensure we don't exceed rate limits."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        if time_since_last_call < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_call
            time.sleep(sleep_time)
        self.last_call_time = time.time()

    def fetch_quote(self, ticker: str) -> MarketDataResult:
        """Fetch quote using Finnhub."""
        try:
            self._respect_rate_limit()

            # For European tickers, try the base symbol first (Finnhub often has US listings)
            ticker_info = TickerUtils.parse_ticker(ticker)
            finnhub_ticker = (
                ticker_info.base_ticker if ticker_info.is_international else ticker
            )

            # Get current quote
            quote_url = f"{self.base_url}/quote"
            params = {"symbol": finnhub_ticker, "token": self.api_key}

            response = requests.get(quote_url, params=params, timeout=10)
            response.raise_for_status()

            quote_data = response.json()

            # Check for errors
            if "error" in quote_data:
                suggestions = []
                if ticker_info.is_international:
                    suggestions.append(ticker_info.base_ticker)
                return MarketDataResult(
                    ticker=ticker,
                    success=False,
                    error=quote_data["error"],
                    data_source=self.name,
                    suggestions=suggestions,
                )

            # Parse Finnhub response
            current_price = quote_data.get("c")  # Current price
            high_price = quote_data.get("h")  # High price of the day
            low_price = quote_data.get("l")  # Low price of the day
            open_price = quote_data.get("o")  # Open price of the day
            previous_close = quote_data.get("pc")  # Previous close price

            # Calculate changes
            day_change = None
            day_change_percent = None
            if current_price and previous_close:
                day_change = current_price - previous_close
                day_change_percent = (
                    (day_change / previous_close) * 100 if previous_close != 0 else 0
                )

            # Validate that we got meaningful data
            if not current_price or current_price <= 0:
                suggestions = []
                if ticker_info.is_international:
                    suggestions.append(
                        f"Try searching for '{ticker_info.base_ticker}' or check if ticker exists"
                    )
                return MarketDataResult(
                    ticker=ticker,
                    success=False,
                    error="No valid price data - ticker may not exist or be delisted",
                    data_source=self.name,
                    suggestions=suggestions,
                )

            return MarketDataResult(
                ticker=ticker,
                current_price=current_price,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                volume=None,  # Finnhub quote doesn't include volume
                previous_close=previous_close,
                day_change=day_change,
                day_change_percent=day_change_percent,
                data_source=self.name,
                success=True,
            )

        except Exception as e:
            logger.warning(f"Finnhub failed for {ticker}: {e}")
            ticker_info = TickerUtils.parse_ticker(ticker)
            suggestions = []

            if ticker_info.is_international:
                suggestions.append(ticker_info.base_ticker)

            return MarketDataResult(
                ticker=ticker,
                success=False,
                error=str(e),
                data_source=self.name,
                suggestions=suggestions,
            )


class MultiProviderMarketDataService:
    """Market data service with multiple provider fallback."""

    def __init__(self):
        self.providers = []

        # Initialize providers based on available API keys
        # 1. yFinance (free, no API key needed)
        self.providers.append(YFinanceProvider())

        # 2. Alpha Vantage (if API key available)
        if settings.alpha_vantage_api_key:
            self.providers.append(AlphaVantageProvider(settings.alpha_vantage_api_key))
            logger.info("Alpha Vantage provider initialized")

        # 3. Finnhub (if API key available)
        if settings.finnhub_api_key:
            self.providers.append(FinnhubProvider(settings.finnhub_api_key))
            logger.info("Finnhub provider initialized")

        logger.info(f"Initialized {len(self.providers)} market data providers")

    def fetch_quote(self, ticker: str, db: Session | None = None) -> MarketDataResult:
        """Fetch quote with fallback across providers and ISIN support."""
        # First, try to resolve ISIN to ticker if needed
        resolved_ticker = ticker
        identifier_type = "ticker"

        if db and ISINUtils.is_isin_format(ticker):
            try:
                (
                    resolved_ticker,
                    identifier_type,
                    isin_info,
                ) = isin_service.resolve_identifier(db, ticker)
                logger.info(f"Resolved ISIN {ticker} to ticker {resolved_ticker}")
            except Exception as e:
                logger.warning(f"Failed to resolve ISIN {ticker}: {e}")
                # Continue with original identifier

        last_error = None

        for provider in self.providers:
            logger.debug(f"Trying {provider.name} for {resolved_ticker}")

            result = provider.fetch_quote(resolved_ticker)

            if result.success:
                # Update result with original identifier if it was an ISIN
                if identifier_type == "isin":
                    result.ticker = ticker  # Keep original ISIN in result
                logger.info(
                    f"Successfully fetched {ticker} from {provider.name}: ${result.current_price}"
                )
                return result
            logger.warning(
                f"{provider.name} failed for {resolved_ticker}: {result.error}"
            )
            last_error = result.error

        # All providers failed
        logger.error(f"All providers failed for {ticker}. Last error: {last_error}")
        return MarketDataResult(
            ticker=ticker,
            success=False,
            error=f"All providers failed. Last error: {last_error}",
            data_source="multi_provider",
        )

    def fetch_quote_by_isin(self, db: Session, isin: str) -> MarketDataResult:
        """Fetch quote specifically by ISIN with ticker resolution."""
        try:
            # Validate ISIN
            is_valid, error = ISINUtils.validate_isin(isin)
            if not is_valid:
                return MarketDataResult(
                    ticker=isin,
                    success=False,
                    error=f"Invalid ISIN: {error}",
                    data_source="isin_validation",
                )

            # Try to resolve ISIN to ticker
            resolved_ticker, _, isin_info = isin_service.resolve_identifier(db, isin)

            if resolved_ticker == isin:
                # No ticker mapping found
                return MarketDataResult(
                    ticker=isin,
                    success=False,
                    error=f"No ticker mapping found for ISIN {isin}",
                    data_source="isin_mapping",
                )

            # Fetch quote using resolved ticker
            result = self.fetch_quote(resolved_ticker)

            # Update result to show original ISIN
            if result.success:
                result.ticker = isin

            return result

        except Exception as e:
            logger.error(f"Error fetching quote by ISIN {isin}: {e}")
            return MarketDataResult(
                ticker=isin,
                success=False,
                error=str(e),
                data_source="isin_service",
            )

    def fetch_multiple_quotes(
        self, tickers: list[str], db: Session | None = None
    ) -> list[MarketDataResult]:
        """Fetch quotes for multiple tickers with intelligent provider selection and ISIN support."""
        results = []
        provider_stats = {
            provider.name: {"success": 0, "total": 0} for provider in self.providers
        }

        for ticker in tickers:
            result = self.fetch_quote(ticker, db)
            results.append(result)

            # Update provider statistics
            if result.data_source and result.data_source in provider_stats:
                provider_stats[result.data_source]["total"] += 1
                if result.success:
                    provider_stats[result.data_source]["success"] += 1

        # Log provider performance
        for provider_name, stats in provider_stats.items():
            if stats["total"] > 0:
                success_rate = (stats["success"] / stats["total"]) * 100
                logger.info(
                    f"{provider_name}: {stats['success']}/{stats['total']} ({success_rate:.1f}% success)"
                )

        return results

    def update_asset_prices(self, db: Session, tickers: list[str]) -> dict[str, Any]:
        """Update asset prices in the database with ISIN support."""
        logger.info(f"Updating prices for {len(tickers)} assets")

        # Fetch all quotes with ISIN support
        results = self.fetch_multiple_quotes(tickers, db)

        updated_count = 0
        failed_count = 0
        failed_tickers = []

        for result in results:
            try:
                if not result.success or not result.current_price:
                    failed_count += 1
                    failed_tickers.append(result.ticker)
                    continue

                # Update asset in database
                asset = db.query(Asset).filter(Asset.ticker == result.ticker).first()
                if not asset:
                    logger.warning(f"Asset not found for ticker {result.ticker}")
                    continue

                # Update asset fields
                asset.current_price = result.current_price
                asset.previous_close = result.previous_close
                asset.day_change = result.day_change
                asset.day_change_percent = result.day_change_percent
                asset.data_source = result.data_source
                asset.updated_at = datetime.now()

                # Create or update price history record
                today = date.today()
                price_record = (
                    db.query(PriceHistory)
                    .filter(
                        PriceHistory.asset_id == asset.id,
                        PriceHistory.price_date == today,
                    )
                    .first()
                )

                if price_record:
                    # Update existing record
                    price_record.close_price = Decimal(str(result.current_price))
                    if result.open_price:
                        price_record.open_price = Decimal(str(result.open_price))
                    if result.high_price:
                        price_record.high_price = Decimal(str(result.high_price))
                    if result.low_price:
                        price_record.low_price = Decimal(str(result.low_price))
                    if result.volume:
                        price_record.volume = result.volume
                    price_record.updated_at = datetime.now()
                else:
                    # Create new record
                    price_record = PriceHistory()
                    price_record.asset_id = asset.id
                    price_record.price_date = today
                    price_record.open_price = (
                        Decimal(str(result.open_price)) if result.open_price else None
                    )
                    price_record.high_price = (
                        Decimal(str(result.high_price)) if result.high_price else None
                    )
                    price_record.low_price = (
                        Decimal(str(result.low_price)) if result.low_price else None
                    )
                    price_record.close_price = Decimal(str(result.current_price))
                    price_record.volume = result.volume
                    price_record.data_source = result.data_source
                    db.add(price_record)

                updated_count += 1
                logger.debug(
                    f"Updated {result.ticker}: ${result.current_price} from {result.data_source}"
                )

            except Exception as e:
                logger.error(f"Error updating {result.ticker}: {e}")
                failed_count += 1
                failed_tickers.append(result.ticker)

        # Commit all changes
        try:
            db.commit()
            logger.info(
                f"Successfully committed price updates: {updated_count} updated, {failed_count} failed"
            )
        except Exception as e:
            logger.error(f"Error committing price updates: {e}")
            db.rollback()
            raise

        return {
            "status": "completed",
            "updated_count": updated_count,
            "failed_count": failed_count,
            "total_tickers": len(tickers),
            "failed_tickers": failed_tickers,
            "provider_stats": {
                provider.name: {
                    "available": True,
                    "api_key_configured": getattr(provider, "api_key", None)
                    is not None,
                }
                for provider in self.providers
            },
        }


# Global instance
market_data_service = MultiProviderMarketDataService()
