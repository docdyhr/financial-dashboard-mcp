"""Portfolio analytics and calculation tasks."""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from celery import current_task

from backend.database import get_db_session
from backend.models.asset import Asset
from backend.models.portfolio_snapshot import PortfolioSnapshot
from backend.models.position import Position
from backend.models.user import User
from backend.services.cash_account import CashAccountService
from backend.tasks import celery_app

logger = logging.getLogger(__name__)

# Initialize cash account service
cash_account_service = CashAccountService()


def _get_user_cash_balance(db, user_id: int) -> Decimal:
    """Get total cash balance for a user across all currencies converted to USD."""
    try:
        # For now, get balance in USD (primary currency)
        # In the future, this could convert all currencies to user's preferred currency
        usd_balance = cash_account_service.get_cash_balance(db, user_id, "USD")
        return usd_balance
    except Exception as e:
        logger.warning(f"Error getting cash balance for user {user_id}: {e}")
        return Decimal("0")


@celery_app.task(bind=True, name="calculate_portfolio_performance")  # type: ignore[misc]
def calculate_portfolio_performance(
    self, user_id: int, days_back: int = 30
) -> dict[str, Any]:
    """Calculate portfolio performance metrics for a user.

    Args:
        user_id: User ID to calculate performance for
        days_back: Number of days to look back for performance calculations

    Returns:
        Dict with performance metrics
    """
    try:
        logger.info(f"Calculating portfolio performance for user {user_id}")

        with get_db_session() as db:
            # Get user's active positions
            positions = (
                db.query(Position)
                .join(Asset)
                .filter(
                    Position.user_id == user_id,
                    Position.is_active.is_(True),
                    Asset.current_price.isnot(None),
                )
                .all()
            )

            if not positions:
                return {
                    "status": "completed",
                    "message": "No active positions found",
                    "metrics": {},
                }

            current_task.update_state(
                state="PROGRESS",
                meta={
                    "current": 0,
                    "total": len(positions),
                    "status": "Calculating metrics...",
                },
            )

            # Calculate current portfolio value
            total_current_value = Decimal("0")
            total_cost_basis = Decimal("0")
            positions_data = []

            for i, position in enumerate(positions):
                current_value = position.current_value or Decimal("0")
                total_current_value += current_value
                total_cost_basis += position.total_cost_basis

                positions_data.append(
                    {
                        "ticker": position.asset.ticker,
                        "quantity": float(position.quantity),
                        "current_price": float(position.asset.current_price or 0),
                        "current_value": float(current_value),
                        "cost_basis": float(position.total_cost_basis),
                        "unrealized_gain_loss": float(
                            position.unrealized_gain_loss or 0
                        ),
                        "unrealized_gain_loss_percent": float(
                            position.unrealized_gain_loss_percent or 0
                        ),
                        "weight": float(
                            (current_value / total_current_value * 100)
                            if total_current_value > 0
                            else 0
                        ),
                    }
                )

                current_task.update_state(
                    state="PROGRESS",
                    meta={
                        "current": i + 1,
                        "total": len(positions),
                        "status": f"Processed {position.asset.ticker}",
                    },
                )

            # Calculate overall performance metrics
            total_unrealized_gain_loss = total_current_value - total_cost_basis
            total_unrealized_percent = float(
                (total_unrealized_gain_loss / total_cost_basis * 100)
                if total_cost_basis > 0
                else 0
            )

            # Get historical portfolio snapshots for trend analysis
            start_date = datetime.now() - timedelta(days=days_back)
            historical_snapshots = (
                db.query(PortfolioSnapshot)
                .filter(
                    PortfolioSnapshot.user_id == user_id,
                    PortfolioSnapshot.snapshot_date >= start_date.date(),
                )
                .order_by(PortfolioSnapshot.snapshot_date)
                .all()
            )

            # Calculate performance trend
            performance_trend = []
            if historical_snapshots:
                for snapshot in historical_snapshots:
                    performance_trend.append(
                        {
                            "date": snapshot.snapshot_date.isoformat(),
                            "total_value": float(snapshot.total_value),
                            "total_gain_loss": float(snapshot.total_gain_loss),
                            "total_gain_loss_percent": float(
                                snapshot.total_gain_loss_percent
                            ),
                        }
                    )

            metrics = {
                "portfolio_summary": {
                    "total_current_value": float(total_current_value),
                    "total_cost_basis": float(total_cost_basis),
                    "total_unrealized_gain_loss": float(total_unrealized_gain_loss),
                    "total_unrealized_percent": total_unrealized_percent,
                    "total_positions": len(positions),
                    "calculation_date": datetime.now().isoformat(),
                },
                "positions": positions_data,
                "performance_trend": performance_trend,
                "allocation": {"by_asset_type": {}, "by_sector": {}},
            }

            # Calculate allocation breakdowns
            asset_type_allocation: dict[str, float] = {}
            sector_allocation: dict[str, float] = {}

            for position in positions:
                current_value = position.current_value or Decimal("0")
                weight = float(
                    (current_value / total_current_value * 100)
                    if total_current_value > 0
                    else 0
                )

                # By asset type
                asset_type = position.asset.asset_type.value
                if asset_type not in asset_type_allocation:
                    asset_type_allocation[asset_type] = 0.0
                asset_type_allocation[asset_type] += weight

                # By sector
                sector = position.asset.sector or "Unknown"
                if sector not in sector_allocation:
                    sector_allocation[sector] = 0.0
                sector_allocation[sector] += weight

            metrics["allocation"]["by_asset_type"] = asset_type_allocation
            metrics["allocation"]["by_sector"] = sector_allocation

            return {"status": "completed", "user_id": user_id, "metrics": metrics}

    except Exception as e:
        logger.error(f"Error calculating portfolio performance: {e!s}")
        current_task.update_state(state="FAILURE", meta={"error": str(e)})
        raise


@celery_app.task(bind=True, name="create_portfolio_snapshot")  # type: ignore[misc]
def create_portfolio_snapshot(self, user_id: int | None = None) -> dict[str, Any]:
    """Create daily portfolio snapshot(s) for tracking historical performance.

    Args:
        user_id: Specific user ID, or None for all users

    Returns:
        Dict with snapshot creation status
    """
    try:
        logger.info(f"Creating portfolio snapshot for user_id: {user_id}")

        with get_db_session() as db:
            # Get users to process
            if user_id:
                users = db.query(User).filter(User.id == user_id).all()
            else:
                users = db.query(User).filter(User.is_active.is_(True)).all()

            if not users:
                return {
                    "status": "completed",
                    "message": "No users found",
                    "snapshots_created": 0,
                }

            current_task.update_state(
                state="PROGRESS",
                meta={
                    "current": 0,
                    "total": len(users),
                    "status": "Creating snapshots...",
                },
            )

            snapshots_created = 0
            today = datetime.now().date()

            for i, user in enumerate(users):
                try:
                    # Check if snapshot already exists for today
                    existing_snapshot = (
                        db.query(PortfolioSnapshot)
                        .filter(
                            PortfolioSnapshot.user_id == user.id,
                            PortfolioSnapshot.snapshot_date == today,
                        )
                        .first()
                    )

                    if existing_snapshot:
                        logger.info(
                            f"Snapshot already exists for user {user.id} on {today}"
                        )
                        continue

                    # Get user's active positions
                    positions = (
                        db.query(Position)
                        .join(Asset)
                        .filter(
                            Position.user_id == user.id,
                            Position.is_active.is_(True),
                            Asset.current_price.isnot(None),
                        )
                        .all()
                    )

                    if not positions:
                        logger.info(f"No active positions for user {user.id}")
                        continue

                    # Calculate portfolio totals
                    total_value = Decimal("0")
                    total_cost_basis = Decimal("0")
                    total_positions = len(positions)

                    for position in positions:
                        total_value += position.current_value or Decimal("0")
                        total_cost_basis += position.total_cost_basis

                    total_gain_loss = total_value - total_cost_basis
                    total_gain_loss_percent = float(
                        (total_gain_loss / total_cost_basis * 100)
                        if total_cost_basis > 0
                        else 0
                    )

                    # Create snapshot
                    snapshot = PortfolioSnapshot(
                        user_id=user.id,
                        snapshot_date=today,
                        total_value=total_value,
                        total_cost_basis=total_cost_basis,
                        total_gain_loss=total_gain_loss,
                        total_gain_loss_percent=Decimal(str(total_gain_loss_percent)),
                        total_positions=total_positions,
                        cash_balance=_get_user_cash_balance(db, user.id),
                    )  # type: ignore[call-arg]

                    db.add(snapshot)
                    snapshots_created += 1

                    logger.info(
                        f"Created snapshot for user {user.id}: ${total_value:.2f}"
                    )

                except Exception as e:
                    logger.error(f"Error creating snapshot for user {user.id}: {e!s}")
                    continue

                current_task.update_state(
                    state="PROGRESS",
                    meta={
                        "current": i + 1,
                        "total": len(users),
                        "status": f"Processed user {user.id}",
                    },
                )

            # Commit all snapshots
            db.commit()

            return {
                "status": "completed",
                "snapshots_created": snapshots_created,
                "total_users_processed": len(users),
                "snapshot_date": today.isoformat(),
            }

    except Exception as e:
        logger.error(f"Error creating portfolio snapshots: {e!s}")
        current_task.update_state(state="FAILURE", meta={"error": str(e)})
        raise


@celery_app.task(bind=True, name="generate_portfolio_report")  # type: ignore[misc]
def generate_portfolio_report(
    self, user_id: int, report_type: str = "monthly"
) -> dict[str, Any]:
    """Generate comprehensive portfolio report.

    Args:
        user_id: User ID to generate report for
        report_type: Type of report (daily, weekly, monthly, quarterly, yearly)

    Returns:
        Dict with report data
    """
    try:
        logger.info(f"Generating {report_type} portfolio report for user {user_id}")

        # Define lookback periods
        lookback_days = {
            "daily": 1,
            "weekly": 7,
            "monthly": 30,
            "quarterly": 90,
            "yearly": 365,
        }

        days_back = lookback_days.get(report_type, 30)

        # Get current portfolio performance
        performance_result = calculate_portfolio_performance(user_id, days_back)

        if performance_result["status"] != "completed":
            return performance_result

        metrics = performance_result["metrics"]

        # Get top performers and worst performers
        positions = metrics.get("positions", [])
        top_performers = sorted(
            positions, key=lambda x: x["unrealized_gain_loss_percent"], reverse=True
        )[:5]
        worst_performers = sorted(
            positions, key=lambda x: x["unrealized_gain_loss_percent"]
        )[:5]

        # Calculate additional metrics
        start_date = datetime.now() - timedelta(days=days_back)

        report = {
            "report_info": {
                "user_id": user_id,
                "report_type": report_type,
                "period_days": days_back,
                "generated_at": datetime.now().isoformat(),
                "start_date": start_date.date().isoformat(),
                "end_date": datetime.now().date().isoformat(),
            },
            "portfolio_summary": metrics["portfolio_summary"],
            "performance_highlights": {
                "top_performers": top_performers,
                "worst_performers": worst_performers,
                "most_valuable_positions": sorted(
                    positions, key=lambda x: x["current_value"], reverse=True
                )[:5],
            },
            "allocation_analysis": metrics["allocation"],
            "historical_performance": metrics["performance_trend"],
            "risk_metrics": {
                "concentration_risk": (
                    max([pos["weight"] for pos in positions]) if positions else 0
                ),
                "diversification_score": (
                    len(set([pos["ticker"][:2] for pos in positions]))
                    if positions
                    else 0
                ),  # Simple sector diversity
            },
        }

        return {"status": "completed", "report": report}

    except Exception as e:
        logger.error(f"Error generating portfolio report: {e!s}")
        current_task.update_state(state="FAILURE", meta={"error": str(e)})
        raise
