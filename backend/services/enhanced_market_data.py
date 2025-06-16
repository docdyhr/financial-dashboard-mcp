"""Enhanced market data service with ISIN-based data fetching.

This module provides advanced market data capabilities leveraging the ISIN
infrastructure for European and international securities.
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf

from backend.database import get_db_session
from backend.models.isin import ISINTickerMapping
from backend.services.european_mappings import get_european_mapping_service
from backend.services.german_data_providers import get_german_data_service
from backend.services.isin_utils import get_isin_service

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Available market data sources."""

    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    DEUTSCHE_BORSE = "deutsche_borse"
    BOERSE_FRANKFURT = "boerse_frankfurt"
    FINNHUB = "finnhub"
    TWELVE_DATA = "twelve_data"


class QuoteType(Enum):
    """Types of market quotes."""

    REAL_TIME = "real_time"
    DELAYED = "delayed"
    END_OF_DAY = "end_of_day"
    HISTORICAL = "historical"


@dataclass
class MarketQuote:
    """Enhanced market quote with metadata."""

    symbol: str
    isin: str | None = None
    price: float | None = None
    currency: str = "EUR"

    # Price data
    open_price: float | None = None
    high_price: float | None = None
    low_price: float | None = None
    close_price: float | None = None
    previous_close: float | None = None

    # Volume and trading
    volume: int | None = None
    avg_volume: int | None = None

    # Change metrics
    change: float | None = None
    change_percent: float | None = None

    # Bid/Ask
    bid: float | None = None
    ask: float | None = None
    bid_size: int | None = None
    ask_size: int | None = None

    # 52-week range
    week_52_high: float | None = None
    week_52_low: float | None = None

    # Market data
    market_cap: float | None = None
    pe_ratio: float | None = None
    dividend_yield: float | None = None

    # Metadata
    source: DataSource = DataSource.YAHOO_FINANCE
    quote_type: QuoteType = QuoteType.DELAYED
    timestamp: datetime = field(default_factory=datetime.now)
    exchange: str | None = None
    exchange_timezone: str | None = None

    # Quality indicators
    confidence: float = 1.0
    is_tradeable: bool = True
    market_state: str | None = None  # REGULAR, CLOSED, PRE, POST

    @property
    def is_fresh(self, max_age_minutes: int = 15) -> bool:
        """Check if quote is fresh."""
        age = datetime.now() - self.timestamp
        return age.total_seconds() < (max_age_minutes * 60)

    @property
    def formatted_change(self) -> str:
        """Get formatted change string."""
        if self.change is None:
            return "N/A"

        sign = "+" if self.change >= 0 else ""
        change_str = f"{sign}{self.change:.2f}"

        if self.change_percent is not None:
            change_str += f" ({sign}{self.change_percent:.2f}%)"

        return change_str


@dataclass
class HistoricalData:
    """Historical market data."""

    symbol: str
    isin: str | None = None
    data: pd.DataFrame = field(default_factory=pd.DataFrame)
    period: str = "1y"
    interval: str = "1d"
    source: DataSource = DataSource.YAHOO_FINANCE
    retrieved_at: datetime = field(default_factory=datetime.now)

    @property
    def latest_price(self) -> float | None:
        """Get latest closing price."""
        if self.data.empty:
            return None
        return float(self.data["Close"].iloc[-1])

    @property
    def price_change_1d(self) -> tuple[float, float] | None:
        """Get 1-day price change (absolute, percent)."""
        if len(self.data) < 2:
            return None

        current = float(self.data["Close"].iloc[-1])
        previous = float(self.data["Close"].iloc[-2])

        change = current - previous
        change_percent = (change / previous) * 100

        return change, change_percent

    @property
    def volatility(self) -> float | None:
        """Calculate annualized volatility."""
        if self.data.empty or "Close" not in self.data.columns:
            return None

        returns = self.data["Close"].pct_change().dropna()
        if len(returns) < 10:
            return None

        # Annualize based on interval
        multiplier = (
            252 if self.interval == "1d" else 252 * 24
        )  # Assume hourly for intraday
        return float(returns.std() * np.sqrt(multiplier))


class EnhancedMarketDataService:
    """Enhanced market data service with ISIN support."""

    def __init__(self):
        self.german_service = get_german_data_service()
        self.european_service = get_european_mapping_service()
        self.isin_service = get_isin_service()

        # Caching
        self.quote_cache: dict[str, MarketQuote] = {}
        self.cache_ttl = 300  # 5 minutes

        # Rate limiting
        self.rate_limits = {
            DataSource.YAHOO_FINANCE: 1.0,  # 1 second between requests
            DataSource.ALPHA_VANTAGE: 12.0,  # 12 seconds (5 requests per minute)
            DataSource.DEUTSCHE_BORSE: 2.0,
            DataSource.BOERSE_FRANKFURT: 1.5,
        }
        self.last_request_times: dict[DataSource, float] = {}

        # Thread pool for concurrent requests
        self.executor = ThreadPoolExecutor(max_workers=5)

    def _rate_limit(self, source: DataSource):
        """Enforce rate limiting for data source."""
        if source not in self.rate_limits:
            return

        delay = self.rate_limits[source]
        last_time = self.last_request_times.get(source, 0)
        elapsed = time.time() - last_time

        if elapsed < delay:
            time.sleep(delay - elapsed)

        self.last_request_times[source] = time.time()

    async def get_quote_by_isin(
        self,
        isin: str,
        prefer_source: DataSource | None = None,
        use_cache: bool = True,
    ) -> MarketQuote | None:
        """Get market quote for an ISIN.

        Args:
            isin: The ISIN to get quote for
            prefer_source: Preferred data source
            use_cache: Whether to use cached data

        Returns:
            MarketQuote if found, None otherwise
        """
        # Check cache first
        if use_cache and isin in self.quote_cache:
            cached_quote = self.quote_cache[isin]
            if cached_quote.is_fresh():
                logger.debug(f"Using cached quote for {isin}")
                return cached_quote

        # Get ticker mapping for ISIN
        ticker = await self._resolve_isin_to_ticker(isin)
        if not ticker:
            logger.warning(f"No ticker found for ISIN {isin}")
            return None

        # Try multiple sources in order of preference
        sources = (
            [prefer_source]
            if prefer_source
            else [
                DataSource.YAHOO_FINANCE,
                DataSource.DEUTSCHE_BORSE,
                DataSource.BOERSE_FRANKFURT,
            ]
        )

        for source in sources:
            if source is None:
                continue

            try:
                quote = await self._fetch_quote_from_source(ticker, source, isin)
                if quote:
                    # Cache the result
                    self.quote_cache[isin] = quote
                    logger.debug(f"Retrieved quote for {isin} from {source.value}")
                    return quote
            except Exception as e:
                logger.warning(
                    f"Failed to get quote from {source.value} for {isin}: {e}"
                )
                continue

        logger.error(f"Failed to get quote for ISIN {isin} from all sources")
        return None

    async def get_quotes_batch(
        self, isins: list[str], max_concurrent: int = 5
    ) -> dict[str, MarketQuote | None]:
        """Get quotes for multiple ISINs concurrently.

        Args:
            isins: List of ISINs to get quotes for
            max_concurrent: Maximum concurrent requests

        Returns:
            Dictionary mapping ISINs to quotes
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def get_quote_with_semaphore(
            isin: str,
        ) -> tuple[str, MarketQuote | None]:
            async with semaphore:
                quote = await self.get_quote_by_isin(isin)
                return isin, quote

        # Execute all requests concurrently
        tasks = [get_quote_with_semaphore(isin) for isin in isins]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        quotes = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error in batch quote request: {result}")
                continue

            isin, quote = result
            quotes[isin] = quote

        return quotes

    async def get_historical_data(
        self,
        isin: str,
        period: str = "1y",
        interval: str = "1d",
        source: DataSource = DataSource.YAHOO_FINANCE,
    ) -> HistoricalData | None:
        """Get historical data for an ISIN.

        Args:
            isin: The ISIN to get data for
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            source: Data source to use

        Returns:
            HistoricalData if found, None otherwise
        """
        # Get ticker mapping
        ticker = await self._resolve_isin_to_ticker(isin)
        if not ticker:
            return None

        try:
            if source == DataSource.YAHOO_FINANCE:
                return await self._fetch_yahoo_historical(
                    ticker, isin, period, interval
                )
            logger.warning(
                f"Historical data not supported for source {source.value}"
            )
            return None
        except Exception as e:
            logger.error(f"Error fetching historical data for {isin}: {e}")
            return None

    async def _resolve_isin_to_ticker(self, isin: str) -> str | None:
        """Resolve ISIN to ticker symbol."""
        try:
            # First check our ISIN mapping service
            with get_db_session() as db:
                mapping = (
                    db.query(ISINTickerMapping)
                    .filter(
                        ISINTickerMapping.isin == isin,
                        ISINTickerMapping.is_active,
                    )
                    .order_by(ISINTickerMapping.confidence.desc())
                    .first()
                )

                if mapping:
                    # Format ticker with exchange if needed
                    ticker = mapping.ticker
                    if mapping.exchange_code and not ticker.endswith(
                        f".{mapping.exchange_code}"
                    ):
                        ticker = f"{ticker}.{mapping.exchange_code}"
                    return ticker

            # Try European mapping service
            best_mapping = self.european_service.get_best_mapping(isin)
            if best_mapping:
                return best_mapping.ticker_with_exchange

            # Try to suggest ticker from ISIN structure
            suggested = self.european_service.suggest_ticker_for_isin(isin)
            if suggested:
                return suggested

            return None

        except Exception as e:
            logger.error(f"Error resolving ISIN {isin} to ticker: {e}")
            return None

    async def _fetch_quote_from_source(
        self, ticker: str, source: DataSource, isin: str | None = None
    ) -> MarketQuote | None:
        """Fetch quote from specific data source."""
        if source == DataSource.YAHOO_FINANCE:
            return await self._fetch_yahoo_quote(ticker, isin)
        if source == DataSource.DEUTSCHE_BORSE:
            return await self._fetch_deutsche_borse_quote(ticker, isin)
        if source == DataSource.BOERSE_FRANKFURT:
            return await self._fetch_boerse_frankfurt_quote(ticker, isin)
        logger.warning(f"Data source {source.value} not implemented")
        return None

    async def _fetch_yahoo_quote(
        self, ticker: str, isin: str | None = None
    ) -> MarketQuote | None:
        """Fetch quote from Yahoo Finance."""
        try:
            self._rate_limit(DataSource.YAHOO_FINANCE)

            # Use thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            stock = await loop.run_in_executor(self.executor, yf.Ticker, ticker)
            info = await loop.run_in_executor(self.executor, lambda: stock.info)

            if not info or "regularMarketPrice" not in info:
                return None

            # Extract quote data
            quote = MarketQuote(
                symbol=ticker,
                isin=isin,
                price=info.get("regularMarketPrice"),
                currency=info.get("currency", "USD"),
                open_price=info.get("regularMarketOpen"),
                high_price=info.get("regularMarketDayHigh"),
                low_price=info.get("regularMarketDayLow"),
                close_price=info.get("previousClose"),
                previous_close=info.get("previousClose"),
                volume=info.get("regularMarketVolume"),
                avg_volume=info.get("averageVolume"),
                change=info.get("regularMarketChange"),
                change_percent=info.get("regularMarketChangePercent"),
                bid=info.get("bid"),
                ask=info.get("ask"),
                bid_size=info.get("bidSize"),
                ask_size=info.get("askSize"),
                week_52_high=info.get("fiftyTwoWeekHigh"),
                week_52_low=info.get("fiftyTwoWeekLow"),
                market_cap=info.get("marketCap"),
                pe_ratio=info.get("trailingPE"),
                dividend_yield=info.get("dividendYield"),
                source=DataSource.YAHOO_FINANCE,
                quote_type=QuoteType.DELAYED,
                exchange=info.get("exchange"),
                exchange_timezone=info.get("exchangeTimezoneName"),
                market_state=info.get("marketState"),
            )

            return quote

        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance quote for {ticker}: {e}")
            return None

    async def _fetch_deutsche_borse_quote(
        self, ticker: str, isin: str | None = None
    ) -> MarketQuote | None:
        """Fetch quote from Deutsche Börse."""
        try:
            if not isin:
                return None

            self._rate_limit(DataSource.DEUTSCHE_BORSE)

            # Use German data service
            data = await self.german_service.get_comprehensive_data(isin)
            if not data or not data.get("best_quote"):
                return None

            quote_data = data["best_quote"]

            quote = MarketQuote(
                symbol=ticker,
                isin=isin,
                price=quote_data.price,
                currency=quote_data.currency,
                change=quote_data.change,
                change_percent=quote_data.change_percent,
                volume=quote_data.volume,
                source=DataSource.DEUTSCHE_BORSE,
                quote_type=QuoteType.REAL_TIME,
                exchange="XETR",
            )

            return quote

        except Exception as e:
            logger.error(f"Error fetching Deutsche Börse quote for {ticker}: {e}")
            return None

    async def _fetch_boerse_frankfurt_quote(
        self, ticker: str, isin: str | None = None
    ) -> MarketQuote | None:
        """Fetch quote from Börse Frankfurt."""
        try:
            if not isin:
                return None

            self._rate_limit(DataSource.BOERSE_FRANKFURT)

            # This would use the Börse Frankfurt provider
            # Implementation would depend on their specific API
            logger.info(
                f"Börse Frankfurt quote fetch not fully implemented for {ticker}"
            )
            return None

        except Exception as e:
            logger.error(f"Error fetching Börse Frankfurt quote for {ticker}: {e}")
            return None

    async def _fetch_yahoo_historical(
        self, ticker: str, isin: str | None, period: str, interval: str
    ) -> HistoricalData | None:
        """Fetch historical data from Yahoo Finance."""
        try:
            self._rate_limit(DataSource.YAHOO_FINANCE)

            loop = asyncio.get_event_loop()
            stock = await loop.run_in_executor(self.executor, yf.Ticker, ticker)

            # Fetch historical data
            hist_data = await loop.run_in_executor(
                self.executor, lambda: stock.history(period=period, interval=interval)
            )

            if hist_data.empty:
                return None

            return HistoricalData(
                symbol=ticker,
                isin=isin,
                data=hist_data,
                period=period,
                interval=interval,
                source=DataSource.YAHOO_FINANCE,
            )

        except Exception as e:
            logger.error(f"Error fetching Yahoo historical data for {ticker}: {e}")
            return None

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self.quote_cache)
        fresh_entries = sum(
            1 for quote in self.quote_cache.values() if quote.is_fresh()
        )

        return {
            "total_cached_quotes": total_entries,
            "fresh_quotes": fresh_entries,
            "stale_quotes": total_entries - fresh_entries,
            "cache_hit_ratio": fresh_entries / max(total_entries, 1),
            "supported_sources": [source.value for source in DataSource],
            "rate_limits": {
                source.value: limit for source, limit in self.rate_limits.items()
            },
        }

    def clear_cache(self, older_than_minutes: int | None = None):
        """Clear quote cache."""
        if older_than_minutes is None:
            self.quote_cache.clear()
            logger.info("Cleared entire quote cache")
        else:
            cutoff = datetime.now() - timedelta(minutes=older_than_minutes)
            to_remove = [
                isin
                for isin, quote in self.quote_cache.items()
                if quote.timestamp < cutoff
            ]

            for isin in to_remove:
                del self.quote_cache[isin]

            logger.info(f"Removed {len(to_remove)} stale quotes from cache")

    async def get_market_status(self, exchange: str = "XETR") -> dict[str, Any]:
        """Get market status for an exchange."""
        try:
            # This would typically call exchange-specific APIs
            # For now, return a basic status based on time
            now = datetime.now()

            # Simple market hours check (European markets)
            market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
            market_close = now.replace(hour=17, minute=30, second=0, microsecond=0)

            is_trading_day = now.weekday() < 5  # Monday = 0, Sunday = 6
            is_trading_hours = market_open <= now <= market_close

            market_state = "CLOSED"
            if is_trading_day and is_trading_hours:
                market_state = "OPEN"
            elif is_trading_day and now < market_open:
                market_state = "PRE"
            elif is_trading_day and now > market_close:
                market_state = "POST"

            return {
                "exchange": exchange,
                "market_state": market_state,
                "is_trading_day": is_trading_day,
                "local_time": now.isoformat(),
                "next_open": (
                    market_open.isoformat() if market_state == "CLOSED" else None
                ),
                "next_close": (
                    market_close.isoformat() if market_state == "OPEN" else None
                ),
            }

        except Exception as e:
            logger.error(f"Error getting market status for {exchange}: {e}")
            return {"exchange": exchange, "error": str(e)}


# Singleton instance
enhanced_market_data_service = EnhancedMarketDataService()


def get_enhanced_market_data_service() -> EnhancedMarketDataService:
    """Get the enhanced market data service instance."""
    return enhanced_market_data_service


async def get_portfolio_quotes(portfolio_isins: list[str]) -> dict[str, MarketQuote]:
    """Get quotes for all ISINs in a portfolio.

    Args:
        portfolio_isins: List of ISINs in the portfolio

    Returns:
        Dictionary mapping ISINs to their quotes
    """
    service = get_enhanced_market_data_service()
    return await service.get_quotes_batch(portfolio_isins)


async def get_market_summary(region: str = "europe") -> dict[str, Any]:
    """Get market summary for a region.

    Args:
        region: Market region (europe, germany, uk, etc.)

    Returns:
        Market summary data
    """
    service = get_enhanced_market_data_service()

    # Sample ISINs for major indices
    major_isins = {
        "europe": [
            "DE0007164600",  # SAP
            "NL0011794037",  # ASML
            "CH0012005267",  # Nestlé
            "FR0000120073",  # Airbus
        ],
        "germany": [
            "DE0007164600",  # SAP
            "DE0008404005",  # Allianz
            "DE0005190003",  # BMW
            "DE0007236101",  # Siemens
        ],
    }

    isins = major_isins.get(region, major_isins["europe"])
    quotes = await service.get_quotes_batch(isins)

    # Calculate summary metrics
    total_quotes = len([q for q in quotes.values() if q is not None])
    positive_changes = len(
        [
            q
            for q in quotes.values()
            if q is not None and q.change is not None and q.change > 0
        ]
    )

    return {
        "region": region,
        "total_securities": len(isins),
        "successful_quotes": total_quotes,
        "positive_movers": positive_changes,
        "negative_movers": total_quotes - positive_changes,
        "quotes": {isin: quote for isin, quote in quotes.items() if quote is not None},
        "timestamp": datetime.now().isoformat(),
    }
