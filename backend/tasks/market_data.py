"""Market data fetching tasks."""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

import yfinance as yf
from celery import current_task

from backend.database import get_db_session
from backend.models.asset import Asset
from backend.models.position import Position
from backend.models.price_history import PriceHistory
from backend.tasks import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="fetch_market_data")  # type: ignore[misc]
def fetch_market_data(self, symbols: list[str], period: str = "1d") -> dict[str, Any]:
    """Fetch market data for given symbols.

    Args:
        symbols: List of ticker symbols to fetch
        period: Period for data (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)

    Returns:
        Dict with status and results
    """
    try:
        logger.info(f"Fetching market data for symbols: {symbols}")

        # Update task state
        current_task.update_state(
            state="PROGRESS",
            meta={
                "current": 0,
                "total": len(symbols),
                "status": "Starting data fetch...",
            },
        )

        results = {}
        failed_symbols = []

        for i, symbol in enumerate(symbols):
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)

                if hist.empty:
                    logger.warning(f"No data found for symbol: {symbol}")
                    failed_symbols.append(symbol)
                    continue

                # Convert to dict for JSON serialization
                results[symbol] = {
                    "data": hist.to_dict("records"),
                    "info": ticker.info,
                    "last_updated": datetime.now().isoformat(),
                }

                # Update progress
                current_task.update_state(
                    state="PROGRESS",
                    meta={
                        "current": i + 1,
                        "total": len(symbols),
                        "status": f"Processed {symbol}",
                    },
                )

                logger.info(f"Successfully fetched data for {symbol}")

            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e!s}")
                failed_symbols.append(symbol)

        return {
            "status": "completed",
            "results": results,
            "failed_symbols": failed_symbols,
            "total_processed": len(results),
            "total_failed": len(failed_symbols),
        }

    except Exception as e:
        logger.error(f"Error in fetch_market_data task: {e!s}")
        current_task.update_state(state="FAILURE", meta={"error": str(e)})
        raise


@celery_app.task(bind=True, name="update_portfolio_prices")  # type: ignore[misc]
def update_portfolio_prices(self, user_id: int | None = None) -> dict[str, Any]:
    """Update prices for all assets in user portfolio(s).

    Args:
        user_id: Specific user ID to update, or None for all users

    Returns:
        Dict with update status
    """
    try:
        logger.info(f"Updating portfolio prices for user_id: {user_id}")

        with get_db_session() as db:
            # Get all unique asset tickers from positions
            query = db.query(Asset.ticker).join(Position).distinct()
            if user_id:
                query = query.filter(Position.user_id == user_id)

            tickers = [row[0] for row in query.all()]

            if not tickers:
                return {
                    "status": "completed",
                    "message": "No tickers found to update",
                    "updated_count": 0,
                }

            logger.info(f"Found {len(tickers)} unique tickers to update")

            current_task.update_state(
                state="PROGRESS",
                meta={
                    "current": 0,
                    "total": len(tickers),
                    "status": "Starting price updates...",
                },
            )

            updated_count = 0
            failed_count = 0

            for i, ticker in enumerate(tickers):
                try:
                    yf_ticker = yf.Ticker(ticker)
                    hist = yf_ticker.history(period="2d")  # Get last 2 days

                    if hist.empty:
                        logger.warning(f"No recent data for {ticker}")
                        failed_count += 1
                        continue

                    # Get the most recent price
                    latest_price = hist["Close"].iloc[-1]
                    latest_date = hist.index[-1].date()

                    # Update asset current price
                    asset = db.query(Asset).filter(Asset.ticker == ticker).first()
                    if asset:
                        asset.current_price = Decimal(str(latest_price))
                        asset.updated_at = datetime.now()

                    # Update or create price history record
                    price_record = (
                        db.query(PriceHistory)
                        .filter(
                            PriceHistory.asset_id == asset.id,
                            PriceHistory.price_date == latest_date,
                        )
                        .first()
                    )

                    if price_record:
                        price_record.close_price = Decimal(str(latest_price))
                        price_record.updated_at = datetime.now()
                    else:
                        price_record = PriceHistory(
                            asset_id=asset.id,
                            price_date=latest_date,
                            open_price=Decimal(str(hist["Open"].iloc[-1])),
                            high_price=Decimal(str(hist["High"].iloc[-1])),
                            low_price=Decimal(str(hist["Low"].iloc[-1])),
                            close_price=Decimal(str(latest_price)),
                            volume=(
                                int(hist["Volume"].iloc[-1])
                                if "Volume" in hist
                                else None
                            ),
                        )  # type: ignore[call-arg]
                        db.add(price_record)

                    updated_count += 1

                    current_task.update_state(
                        state="PROGRESS",
                        meta={
                            "current": i + 1,
                            "total": len(tickers),
                            "status": f"Updated {ticker}: ${latest_price:.2f}",
                        },
                    )

                except Exception as e:
                    logger.error(f"Error updating price for {ticker}: {e!s}")
                    failed_count += 1

            # Commit all changes
            db.commit()

            logger.info(
                f"Price update completed. Updated: {updated_count}, Failed: {failed_count}"
            )

            return {
                "status": "completed",
                "updated_count": updated_count,
                "failed_count": failed_count,
                "total_tickers": len(tickers),
                "user_id": user_id,
            }

    except Exception as e:
        logger.error(f"Error in update_portfolio_prices task: {e!s}")
        current_task.update_state(state="FAILURE", meta={"error": str(e)})
        raise


@celery_app.task(bind=True, name="fetch_asset_info")  # type: ignore[misc]
def fetch_asset_info(self, ticker: str) -> dict[str, Any]:
    """Fetch detailed information for a single asset.

    Args:
        ticker: Ticker symbol

    Returns:
        Dict with asset information
    """
    try:
        logger.info(f"Fetching asset info for: {ticker}")

        yf_ticker = yf.Ticker(ticker)
        info = yf_ticker.info

        # Get recent price history
        hist = yf_ticker.history(period="1mo")

        result = {
            "ticker": ticker,
            "info": info,
            "current_price": float(hist["Close"].iloc[-1]) if not hist.empty else None,
            "price_change_1d": None,
            "price_change_1w": None,
            "price_change_1m": None,
            "last_updated": datetime.now().isoformat(),
        }

        # Calculate price changes
        if not hist.empty and len(hist) > 1:
            current_price = hist["Close"].iloc[-1]

            # 1 day change
            if len(hist) >= 2:
                prev_price = hist["Close"].iloc[-2]
                result["price_change_1d"] = float(
                    (current_price - prev_price) / prev_price * 100
                )

            # 1 week change (5 trading days)
            if len(hist) >= 6:
                week_ago_price = hist["Close"].iloc[-6]
                result["price_change_1w"] = float(
                    (current_price - week_ago_price) / week_ago_price * 100
                )

            # 1 month change
            month_ago_price = hist["Close"].iloc[0]
            result["price_change_1m"] = float(
                (current_price - month_ago_price) / month_ago_price * 100
            )

        return result

    except Exception as e:
        logger.error(f"Error fetching asset info for {ticker}: {e!s}")
        current_task.update_state(state="FAILURE", meta={"error": str(e)})
        raise
