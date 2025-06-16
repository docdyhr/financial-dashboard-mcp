"""Multi-provider market data service with fallback capabilities."""

import logging
import time
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import requests
import yfinance as yf
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.models.asset import Asset
from backend.models.price_history import PriceHistory

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class MarketDataResult:
    """Result from market data fetch."""

    ticker: str
    current_price: Optional[float] = None
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    volume: Optional[int] = None
    previous_close: Optional[float] = None
    day_change: Optional[float] = None
    day_change_percent: Optional[float] = None
    data_source: Optional[str] = None
    success: bool = False
    error: Optional[str] = None


class MarketDataProvider:
    """Base class for market data providers."""

    def __init__(self, name: str):
        self.name = name

    def fetch_quote(self, ticker: str) -> MarketDataResult:
        """Fetch current quote for a ticker."""
        raise NotImplementedError

    def fetch_multiple_quotes(self, tickers: List[str]) -> List[MarketDataResult]:
        """Fetch quotes for multiple tickers."""
        results = []
        for ticker in tickers:
            result = self.fetch_quote(ticker)
            results.append(result)
            # Add small delay to respect rate limits
            time.sleep(0.1)
        return results


class YFinanceProvider(MarketDataProvider):
    """Yahoo Finance provider using yfinance library."""

    def __init__(self):
        super().__init__("yfinance")

    def fetch_quote(self, ticker: str) -> MarketDataResult:
        """Fetch quote using yfinance."""
        try:
            stock = yf.Ticker(ticker)

            # Get historical data
            hist = stock.history(period="2d")

            if hist.empty:
                return MarketDataResult(
                    ticker=ticker,
                    success=False,
                    error="No historical data available",
                    data_source=self.name,
                )

            # Get the most recent price
            current_price = float(hist["Close"].iloc[-1])
            open_price = float(hist["Open"].iloc[-1])
            high_price = float(hist["High"].iloc[-1])
            low_price = float(hist["Low"].iloc[-1])
            volume = int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else None

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
            logger.warning(f"yFinance failed for {ticker}: {e}")
            return MarketDataResult(
                ticker=ticker, success=False, error=str(e), data_source=self.name
            )


class AlphaVantageProvider(MarketDataProvider):
    """Alpha Vantage provider."""

    def __init__(self, api_key: str):
        super().__init__("alpha_vantage")
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limit_delay = 12  # 5 calls per minute = 12 seconds between calls
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

            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": ticker,
                "apikey": self.api_key,
            }

            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            # Check for API error messages
            if "Error Message" in data:
                return MarketDataResult(
                    ticker=ticker,
                    success=False,
                    error=data["Error Message"],
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
                return MarketDataResult(
                    ticker=ticker,
                    success=False,
                    error="No quote data in response",
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
            logger.warning(f"Alpha Vantage failed for {ticker}: {e}")
            return MarketDataResult(
                ticker=ticker, success=False, error=str(e), data_source=self.name
            )


class FinnhubProvider(MarketDataProvider):
    """Finnhub provider."""

    def __init__(self, api_key: str):
        super().__init__("finnhub")
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1"
        self.rate_limit_delay = 1  # 60 calls per minute = 1 second between calls
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

            # Get current quote
            quote_url = f"{self.base_url}/quote"
            params = {"symbol": ticker, "token": self.api_key}

            response = requests.get(quote_url, params=params, timeout=10)
            response.raise_for_status()

            quote_data = response.json()

            # Check for errors
            if "error" in quote_data:
                return MarketDataResult(
                    ticker=ticker,
                    success=False,
                    error=quote_data["error"],
                    data_source=self.name,
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
                return MarketDataResult(
                    ticker=ticker,
                    success=False,
                    error="No valid price data",
                    data_source=self.name,
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
            return MarketDataResult(
                ticker=ticker, success=False, error=str(e), data_source=self.name
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

    def fetch_quote(self, ticker: str) -> MarketDataResult:
        """Fetch quote with fallback across providers."""
        last_error = None

        for provider in self.providers:
            logger.debug(f"Trying {provider.name} for {ticker}")

            result = provider.fetch_quote(ticker)

            if result.success:
                logger.info(
                    f"Successfully fetched {ticker} from {provider.name}: ${result.current_price}"
                )
                return result
            else:
                logger.warning(f"{provider.name} failed for {ticker}: {result.error}")
                last_error = result.error

        # All providers failed
        logger.error(f"All providers failed for {ticker}. Last error: {last_error}")
        return MarketDataResult(
            ticker=ticker,
            success=False,
            error=f"All providers failed. Last error: {last_error}",
            data_source="multi_provider",
        )

    def fetch_multiple_quotes(self, tickers: List[str]) -> List[MarketDataResult]:
        """Fetch quotes for multiple tickers with intelligent provider selection."""
        results = []
        provider_stats = {
            provider.name: {"success": 0, "total": 0} for provider in self.providers
        }

        for ticker in tickers:
            result = self.fetch_quote(ticker)
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

    def update_asset_prices(self, db: Session, tickers: List[str]) -> Dict[str, Any]:
        """Update asset prices in the database."""
        logger.info(f"Updating prices for {len(tickers)} tickers")

        results = self.fetch_multiple_quotes(tickers)

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
                    price_record = PriceHistory(
                        asset_id=asset.id,
                        price_date=today,
                        open_price=(
                            Decimal(str(result.open_price))
                            if result.open_price
                            else None
                        ),
                        high_price=(
                            Decimal(str(result.high_price))
                            if result.high_price
                            else None
                        ),
                        low_price=(
                            Decimal(str(result.low_price)) if result.low_price else None
                        ),
                        close_price=Decimal(str(result.current_price)),
                        volume=result.volume,
                    )
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
