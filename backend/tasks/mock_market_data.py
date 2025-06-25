"""Mock market data task for demonstration when yfinance is unavailable."""

from datetime import datetime
from decimal import Decimal
import logging
import random
from typing import Any

from celery import current_task

from backend.database import get_db_session
from backend.models.asset import Asset
from backend.models.position import Position
from backend.tasks import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="update_portfolio_prices_mock")
def update_portfolio_prices_mock(self, user_id: int | None = None) -> dict[str, Any]:
    """Update prices with mock data for demonstration."""
    try:
        logger.info(f"Updating portfolio prices with mock data for user_id: {user_id}")

        with get_db_session() as db:
            # Get all unique assets from positions
            query = db.query(Asset).join(Position).distinct()
            if user_id:
                query = query.filter(Position.user_id == user_id)

            assets = query.all()

            if not assets:
                return {
                    "status": "completed",
                    "message": "No assets found to update",
                    "updated_count": 0,
                }

            logger.info(f"Found {len(assets)} unique assets to update")

            current_task.update_state(
                state="PROGRESS",
                meta={
                    "current": 0,
                    "total": len(assets),
                    "status": "Starting mock price updates...",
                },
            )

            updated_count = 0

            for i, asset in enumerate(assets):
                try:
                    if asset.current_price is None:
                        continue

                    # Generate mock price change (-2% to +2%)
                    old_price = float(asset.current_price)
                    change_percent = random.uniform(-0.02, 0.02)
                    new_price = old_price * (1 + change_percent)

                    # Update asset price
                    asset.current_price = Decimal(str(round(new_price, 2)))
                    asset.updated_at = datetime.now()

                    updated_count += 1

                    current_task.update_state(
                        state="PROGRESS",
                        meta={
                            "current": i + 1,
                            "total": len(assets),
                            "status": f"Updated {asset.ticker}: ${new_price:.2f} ({change_percent*100:+.2f}%)",
                        },
                    )

                    logger.info(
                        f"Updated {asset.ticker}: ${old_price:.2f} → ${new_price:.2f}"
                    )

                except Exception as e:
                    logger.error(f"Error updating price for {asset.ticker}: {e!s}")

            # Commit all changes
            db.commit()

            logger.info(f"Mock price update completed. Updated: {updated_count} assets")

            return {
                "status": "completed",
                "updated_count": updated_count,
                "failed_count": 0,
                "total_assets": len(assets),
                "user_id": user_id,
                "mock_data": True,
            }

    except Exception as e:
        logger.error(f"Error in update_portfolio_prices_mock task: {e!s}")
        current_task.update_state(state="FAILURE", meta={"error": str(e)})
        raise
