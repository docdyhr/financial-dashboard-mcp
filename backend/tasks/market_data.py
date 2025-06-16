"""Market data fetching tasks with multi-provider fallback."""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from celery import current_task

from backend.database import get_db_session
from backend.models.asset import Asset
from backend.models.position import Position
from backend.services.market_data import market_data_service
from backend.tasks import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="fetch_market_data")  # type: ignore[misc]
def fetch_market_data(self, symbols: list[str], period: str = "1d") -> dict[str, Any]:
    """
    Fetch market data for given symbols using multi-provider service.

    Args:
        symbols: List of ticker symbols to fetch
        period: Period for data (currently not used in multi-provider service)

    Returns:
        Dict with status and results
    """
    try:
        logger.info(
            f"Fetching market data for {len(symbols)} symbols using multi-provider service"
        )

        # Update task state
        current_task.update_state(
            state="PROGRESS",
            meta={
                "current": 0,
                "total": len(symbols),
                "status": "Starting multi-provider data fetch...",
            },
        )

        # Use the multi-provider service
        results = market_data_service.fetch_multiple_quotes(symbols)

        # Process results
        successful_results = {}
        failed_symbols = []

        for i, result in enumerate(results):
            if result.success and result.current_price:
                successful_results[result.ticker] = {
                    "current_price": result.current_price,
                    "open_price": result.open_price,
                    "high_price": result.high_price,
                    "low_price": result.low_price,
                    "volume": result.volume,
                    "previous_close": result.previous_close,
                    "day_change": result.day_change,
                    "day_change_percent": result.day_change_percent,
                    "data_source": result.data_source,
                    "last_updated": datetime.now().isoformat(),
                }
                logger.info(
                    f"Successfully fetched {result.ticker} from {result.data_source}: ${result.current_price}"
                )
            else:
                failed_symbols.append(result.ticker)
                logger.warning(f"Failed to fetch {result.ticker}: {result.error}")

            # Update progress
            current_task.update_state(
                state="PROGRESS",
                meta={
                    "current": i + 1,
                    "total": len(symbols),
                    "status": f"Processed {result.ticker} via {result.data_source or 'unknown'}",
                },
            )

        return {
            "status": "completed",
            "results": successful_results,
            "failed_symbols": failed_symbols,
            "total_processed": len(successful_results),
            "total_failed": len(failed_symbols),
            "provider_info": "Multi-provider service (yFinance -> Alpha Vantage -> Finnhub)",
        }

    except Exception as e:
        logger.error(f"Error in fetch_market_data task: {e!s}")
        current_task.update_state(state="FAILURE", meta={"error": str(e)})
        raise


@celery_app.task(bind=True, name="update_portfolio_prices")  # type: ignore[misc]
def update_portfolio_prices(self, user_id: int | None = None) -> dict[str, Any]:
    """
    Update prices for all assets in user portfolio(s) using multi-provider service.

    Args:
        user_id: Specific user ID to update, or None for all users

    Returns:
        Dict with update status
    """
    try:
        logger.info(
            f"Updating portfolio prices for user_id: {user_id} using multi-provider service"
        )

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
                    "status": "Starting multi-provider price updates...",
                },
            )

            # Use the multi-provider service to update prices
            result = market_data_service.update_asset_prices(db, tickers)

            # Update task progress to completion
            current_task.update_state(
                state="PROGRESS",
                meta={
                    "current": len(tickers),
                    "total": len(tickers),
                    "status": f"Completed: {result['updated_count']} updated, {result['failed_count']} failed",
                },
            )

            logger.info(
                f"Multi-provider price update completed. "
                f"Updated: {result['updated_count']}, Failed: {result['failed_count']}"
            )

            # Add user_id to result
            result["user_id"] = user_id
            return result

    except Exception as e:
        logger.error(f"Error in update_portfolio_prices task: {e!s}")
        current_task.update_state(state="FAILURE", meta={"error": str(e)})
        raise


@celery_app.task(bind=True, name="fetch_asset_info")  # type: ignore[misc]
def fetch_asset_info(self, ticker: str) -> dict[str, Any]:
    """
    Fetch detailed information for a single asset using multi-provider service.

    Args:
        ticker: Ticker symbol

    Returns:
        Dict with asset information
    """
    try:
        logger.info(f"Fetching asset info for: {ticker} using multi-provider service")

        # Use the multi-provider service to get current quote
        result = market_data_service.fetch_quote(ticker)

        if not result.success:
            logger.error(f"Failed to fetch asset info for {ticker}: {result.error}")
            return {
                "ticker": ticker,
                "error": result.error,
                "success": False,
                "last_updated": datetime.now().isoformat(),
            }

        # Format the response
        response = {
            "ticker": ticker,
            "current_price": result.current_price,
            "open_price": result.open_price,
            "high_price": result.high_price,
            "low_price": result.low_price,
            "volume": result.volume,
            "previous_close": result.previous_close,
            "day_change": result.day_change,
            "day_change_percent": result.day_change_percent,
            "data_source": result.data_source,
            "success": True,
            "last_updated": datetime.now().isoformat(),
        }

        logger.info(
            f"Successfully fetched asset info for {ticker} from {result.data_source}"
        )
        return response

    except Exception as e:
        logger.error(f"Error fetching asset info for {ticker}: {e!s}")
        current_task.update_state(state="FAILURE", meta={"error": str(e)})
        raise
