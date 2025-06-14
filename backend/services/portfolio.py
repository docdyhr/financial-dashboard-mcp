"""Portfolio service for portfolio operations and calculations."""

from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.models import (
    AssetCategory,
    AssetType,
    PortfolioSnapshot,
    Position,
    Transaction,
    TransactionType,
    User,
)
from backend.schemas.asset import AssetSummary
from backend.schemas.portfolio import (
    AllocationBreakdown,
    DiversificationMetrics,
    PerformanceMetrics,
    PortfolioSummary,
)
from backend.schemas.position import PositionSummary


class PortfolioService:
    """Service for portfolio operations and calculations."""

    def __init__(self) -> None:
        """Initialize portfolio service."""

    def get_portfolio_summary(self, db: Session, user_id: int) -> PortfolioSummary:
        """Get comprehensive portfolio summary for a user."""

        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=404, detail=f"User with ID {user_id} not found"
            )

        # Get all active positions with asset data
        positions = (
            db.query(Position)
            .options(joinedload(Position.asset))
            .filter(Position.user_id == user_id, Position.is_active.is_(True))
            .all()
        )

        # Calculate portfolio totals
        total_value = Decimal("0")
        total_cost_basis = Decimal("0")
        cash_balance = Decimal("5000")  # TODO: Get from user cash account

        position_summaries = []

        for position in positions:
            current_value = position.current_value or Decimal("0")
            total_value += current_value
            total_cost_basis += position.total_cost_basis

            # Create position summary
            position_summary = PositionSummary(
                id=position.id,
                asset=AssetSummary(
                    id=position.asset.id,
                    ticker=position.asset.ticker,
                    name=position.asset.name,
                    asset_type=position.asset.asset_type,
                    category=position.asset.category,
                    current_price=(
                        Decimal(str(position.asset.current_price))
                        if position.asset.current_price
                        else None
                    ),
                    currency=position.asset.currency,
                    is_active=position.asset.is_active,
                ),
                quantity=position.quantity,
                current_value=current_value,
                unrealized_gain_loss=position.unrealized_gain_loss,
                unrealized_gain_loss_percent=position.unrealized_gain_loss_percent,
            )
            position_summaries.append(position_summary)

        # Add cash to total value
        total_value += cash_balance
        invested_amount = total_value - cash_balance

        # Calculate performance metrics
        total_gain_loss = total_value - total_cost_basis - cash_balance
        total_gain_loss_percent = (
            (total_gain_loss / total_cost_basis * 100)
            if total_cost_basis > 0
            else Decimal("0")
        )

        # Get daily change (compare with yesterday's snapshot)
        yesterday = date.today() - timedelta(days=1)
        yesterday_snapshot = (
            db.query(PortfolioSnapshot)
            .filter(
                PortfolioSnapshot.user_id == user_id,
                PortfolioSnapshot.snapshot_date == yesterday,
            )
            .first()
        )

        daily_change = None
        daily_change_percent = None
        if yesterday_snapshot:
            daily_change = total_value - yesterday_snapshot.total_value
            if yesterday_snapshot.total_value > 0:
                daily_change_percent = (
                    daily_change / yesterday_snapshot.total_value * 100
                )

        # Sort positions by value for top positions
        position_summaries.sort(
            key=lambda x: x.current_value or Decimal("0"), reverse=True
        )
        top_positions = position_summaries[:5]

        return PortfolioSummary(
            user_id=user_id,
            total_value=total_value,
            total_cost_basis=total_cost_basis,
            cash_balance=cash_balance,
            invested_amount=invested_amount,
            total_gain_loss=total_gain_loss,
            total_gain_loss_percent=total_gain_loss_percent,
            daily_change=daily_change,
            daily_change_percent=daily_change_percent,
            total_positions=len(positions),
            total_assets=len(set(p.asset_id for p in positions)),
            top_positions=top_positions,
        )

    def get_allocation_breakdown(
        self, db: Session, user_id: int
    ) -> AllocationBreakdown:
        """Calculate asset allocation breakdown for a portfolio."""

        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=404, detail=f"User with ID {user_id} not found"
            )

        positions = (
            db.query(Position)
            .options(joinedload(Position.asset))
            .filter(Position.user_id == user_id, Position.is_active.is_(True))
            .all()
        )

        # Calculate total portfolio value
        total_value = Decimal("5000")  # Cash balance
        for position in positions:
            if position.current_value:
                total_value += position.current_value

        if total_value == 0:
            return AllocationBreakdown(
                equity_percent=Decimal("0"),
                fixed_income_percent=Decimal("0"),
                alternative_percent=Decimal("0"),
                cash_percent=Decimal("100"),
                commodity_percent=Decimal("0"),
                real_estate_percent=Decimal("0"),
            )

        # Calculate allocation by category
        category_values = {
            AssetCategory.EQUITY: Decimal("0"),
            AssetCategory.FIXED_INCOME: Decimal("0"),
            AssetCategory.ALTERNATIVE: Decimal("0"),
            AssetCategory.CASH_EQUIVALENT: Decimal("0"),
            AssetCategory.COMMODITY: Decimal("0"),
            AssetCategory.REAL_ESTATE: Decimal("0"),
        }

        allocation_by_category: dict[AssetCategory, Decimal] = {}
        allocation_by_sector: dict[str, Decimal] = {}
        allocation_by_asset_type: dict[AssetType, Decimal] = {}

        for position in positions:
            if position.current_value:
                category = position.asset.category
                if category in category_values:
                    category_values[category] += position.current_value

                # Track by category
                allocation_by_category[category] = (
                    allocation_by_category.get(category, Decimal("0"))
                    + position.current_value
                )

                # Track by sector
                if position.asset.sector:
                    allocation_by_sector[position.asset.sector] = (
                        allocation_by_sector.get(position.asset.sector, Decimal("0"))
                        + position.current_value
                    )

                # Track by asset type
                asset_type = position.asset.asset_type
                allocation_by_asset_type[asset_type] = (
                    allocation_by_asset_type.get(asset_type, Decimal("0"))
                    + position.current_value
                )

        # Convert to percentages
        cash_value = Decimal("5000")  # TODO: Get actual cash balance

        return AllocationBreakdown(
            equity_percent=(category_values[AssetCategory.EQUITY] / total_value * 100),
            fixed_income_percent=(
                category_values[AssetCategory.FIXED_INCOME] / total_value * 100
            ),
            alternative_percent=(
                category_values[AssetCategory.ALTERNATIVE] / total_value * 100
            ),
            cash_percent=(cash_value / total_value * 100),
            commodity_percent=(
                category_values[AssetCategory.COMMODITY] / total_value * 100
            ),
            real_estate_percent=(
                category_values[AssetCategory.REAL_ESTATE] / total_value * 100
            ),
            allocation_by_category={
                k: v / total_value * 100 for k, v in allocation_by_category.items()
            },
            allocation_by_sector={
                k: v / total_value * 100 for k, v in allocation_by_sector.items()
            },
            allocation_by_asset_type={
                k: v / total_value * 100 for k, v in allocation_by_asset_type.items()
            },
        )

    def calculate_performance_metrics(
        self,
        db: Session,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> PerformanceMetrics:
        """Calculate portfolio performance metrics."""

        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=404, detail=f"User with ID {user_id} not found"
            )

        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=365)  # Default to 1 year

        # Get portfolio snapshots for the period
        snapshots = (
            db.query(PortfolioSnapshot)
            .filter(
                PortfolioSnapshot.user_id == user_id,
                PortfolioSnapshot.snapshot_date >= start_date,
                PortfolioSnapshot.snapshot_date <= end_date,
            )
            .order_by(PortfolioSnapshot.snapshot_date)
            .all()
        )

        if not snapshots:
            return PerformanceMetrics(
                total_return=Decimal("0"),
                total_return_percent=Decimal("0"),
                annualized_return=None,
                daily_return=None,
                weekly_return=None,
                monthly_return=None,
                quarterly_return=None,
                ytd_return=None,
                one_year_return=None,
                volatility=None,
                sharpe_ratio=None,
                beta=None,
                alpha=None,
                max_drawdown=None,
                dividend_yield=None,
                annual_dividend_income=None,
            )

        start_value = snapshots[0].total_value
        end_value = snapshots[-1].total_value

        # Calculate total return
        total_return = end_value - start_value
        total_return_percent = (
            (total_return / start_value * 100) if start_value > 0 else Decimal("0")
        )

        # Calculate time-based returns
        daily_returns: list[Decimal] = []
        for i in range(1, len(snapshots)):
            prev_value = snapshots[i - 1].total_value
            curr_value = snapshots[i].total_value
            if prev_value > 0:
                return_rate = (curr_value - prev_value) / prev_value * 100
                daily_returns.append(return_rate)

        # Calculate volatility (standard deviation of daily returns)
        volatility = None
        if daily_returns:
            mean_return = sum(daily_returns) / len(daily_returns)
            variance = sum(
                (float(r) - float(mean_return)) ** 2 for r in daily_returns
            ) / len(daily_returns)
            volatility = Decimal(str(variance**0.5))

        # Calculate annualized return
        days_diff = (end_date - start_date).days
        annualized_return = None
        if days_diff > 0 and start_value > 0:
            annualized_return = (
                (end_value / start_value) ** (Decimal("365") / days_diff) - 1
            ) * 100

        # Get recent returns
        today = date.today()

        # Daily return
        daily_return: Decimal | None = None
        if len(snapshots) >= 2:
            yesterday_value = snapshots[-2].total_value
            today_value = snapshots[-1].total_value
            if yesterday_value > 0:
                daily_return = (today_value - yesterday_value) / yesterday_value * 100

        # Weekly return
        week_ago = today - timedelta(days=7)
        weekly_snapshot = next(
            (s for s in reversed(snapshots) if s.snapshot_date <= week_ago), None
        )
        weekly_return = None
        if weekly_snapshot and weekly_snapshot.total_value > 0:
            weekly_return = (
                (end_value - weekly_snapshot.total_value)
                / weekly_snapshot.total_value
                * 100
            )

        # Monthly return
        month_ago = today - timedelta(days=30)
        monthly_snapshot = next(
            (s for s in reversed(snapshots) if s.snapshot_date <= month_ago), None
        )
        monthly_return = None
        if monthly_snapshot and monthly_snapshot.total_value > 0:
            monthly_return = (
                (end_value - monthly_snapshot.total_value)
                / monthly_snapshot.total_value
                * 100
            )

        # YTD return
        year_start = date(today.year, 1, 1)
        ytd_snapshot = next(
            (s for s in snapshots if s.snapshot_date >= year_start), None
        )
        ytd_return = None
        if ytd_snapshot and ytd_snapshot.total_value > 0:
            ytd_return = (
                (end_value - ytd_snapshot.total_value) / ytd_snapshot.total_value * 100
            )

        # Calculate dividend yield and income
        dividend_transactions = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.transaction_type == TransactionType.DIVIDEND,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
            .all()
        )

        annual_dividend_income = sum(
            t.total_amount for t in dividend_transactions
        ) or Decimal("0")
        current_portfolio_value = end_value
        dividend_yield = (
            (annual_dividend_income / current_portfolio_value * 100)
            if current_portfolio_value > 0
            else Decimal("0")
        )

        return PerformanceMetrics(
            total_return=total_return,
            total_return_percent=total_return_percent,
            annualized_return=annualized_return,
            daily_return=daily_return,
            weekly_return=weekly_return,
            monthly_return=monthly_return,
            quarterly_return=None,
            ytd_return=ytd_return,
            one_year_return=None,
            volatility=volatility,
            sharpe_ratio=None,
            beta=None,
            alpha=None,
            max_drawdown=None,
            dividend_yield=dividend_yield,
            annual_dividend_income=annual_dividend_income,
        )

    def create_portfolio_snapshot(
        self, db: Session, user_id: int, snapshot_date: date | None = None
    ) -> PortfolioSnapshot:
        """Create a portfolio snapshot for a specific date."""

        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=404, detail=f"User with ID {user_id} not found"
            )

        if not snapshot_date:
            snapshot_date = date.today()

        # Get all active positions
        positions = (
            db.query(Position)
            .options(joinedload(Position.asset))
            .filter(Position.user_id == user_id, Position.is_active.is_(True))
            .all()
        )

        # Create snapshot using the model's factory method
        cash_balance = Decimal("5000")  # TODO: Get actual cash balance
        snapshot = PortfolioSnapshot.create_from_positions(
            user_id=user_id,
            snapshot_date=snapshot_date,
            positions=positions,
            cash_balance=cash_balance,
        )

        # Calculate daily change if previous snapshot exists
        previous_snapshot = (
            db.query(PortfolioSnapshot)
            .filter(
                PortfolioSnapshot.user_id == user_id,
                PortfolioSnapshot.snapshot_date < snapshot_date,
            )
            .order_by(PortfolioSnapshot.snapshot_date.desc())
            .first()
        )

        if previous_snapshot:
            snapshot.calculate_daily_change(previous_snapshot)

        # Save snapshot
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

        return snapshot

    def get_diversification_metrics(
        self, db: Session, user_id: int
    ) -> DiversificationMetrics:
        """Calculate portfolio diversification metrics."""

        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=404, detail=f"User with ID {user_id} not found"
            )

        positions = (
            db.query(Position)
            .options(joinedload(Position.asset))
            .filter(Position.user_id == user_id, Position.is_active.is_(True))
            .all()
        )

        if not positions:
            return DiversificationMetrics(
                concentration_risk=Decimal("100"),
                herfindahl_index=Decimal("1"),
                effective_number_of_assets=Decimal("0"),
                sector_concentration={},
                geographic_concentration={},
                overall_diversification_score=0,
                sector_diversification_score=0,
                asset_type_diversification_score=0,
            )

        # Calculate total portfolio value
        total_value = sum(p.current_value or Decimal("0") for p in positions)

        if total_value == 0:
            return DiversificationMetrics(
                concentration_risk=Decimal("100"),
                herfindahl_index=Decimal("1"),
                effective_number_of_assets=Decimal("0"),
                sector_concentration={},
                geographic_concentration={},
                overall_diversification_score=0,
                sector_diversification_score=0,
                asset_type_diversification_score=0,
            )

        # Calculate position weights
        weights = [(p.current_value or Decimal("0")) / total_value for p in positions]

        # Calculate Herfindahl-Hirschman Index
        hhi = sum(w**2 for w in weights) or Decimal("0")

        # Effective number of assets
        effective_assets = Decimal("1") / hhi if hhi > 0 else Decimal("0")

        # Concentration risk (percentage of portfolio in top position)
        max_weight = max(weights) if weights else Decimal("0")
        concentration_risk = max_weight * 100

        # Sector concentration
        sector_values: dict[str, Decimal] = {}
        for position in positions:
            sector = position.asset.sector or "Unknown"
            sector_values[sector] = sector_values.get(sector, Decimal("0")) + (
                position.current_value or Decimal("0")
            )

        sector_concentration = {
            sector: value / total_value * 100 for sector, value in sector_values.items()
        }

        # Calculate diversification scores (simplified scoring)
        overall_score = (
            min(100, int((effective_assets / len(positions)) * 100)) if positions else 0
        )

        # Sector diversification score based on number of sectors
        unique_sectors = len(set(p.asset.sector for p in positions if p.asset.sector))
        sector_score = min(100, unique_sectors * 20)  # Max score at 5+ sectors

        # Asset type diversification score
        unique_asset_types = len(set(p.asset.asset_type for p in positions))
        asset_type_score = min(
            100, unique_asset_types * 25
        )  # Max score at 4+ asset types

        return DiversificationMetrics(
            concentration_risk=concentration_risk,
            herfindahl_index=hhi,
            effective_number_of_assets=effective_assets,
            sector_concentration=sector_concentration,
            geographic_concentration={},
            overall_diversification_score=overall_score,
            sector_diversification_score=sector_score,
            asset_type_diversification_score=asset_type_score,
        )

    def calculate_position_weights(
        self, db: Session, user_id: int
    ) -> dict[int, Decimal]:
        """Calculate position weights in portfolio."""

        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=404, detail=f"User with ID {user_id} not found"
            )

        positions = (
            db.query(Position)
            .filter(Position.user_id == user_id, Position.is_active.is_(True))
            .all()
        )

        total_value = sum(p.current_value or Decimal("0") for p in positions)

        if total_value == 0:
            return {}

        return {
            position.id: (position.current_value or Decimal("0")) / total_value * 100
            for position in positions
        }

    def get_performance_comparison(
        self,
        db: Session,
        user_id: int,
        benchmark_ticker: str = "SPY",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Decimal]:
        """Compare portfolio performance to a benchmark."""

        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=404, detail=f"User with ID {user_id} not found"
            )

        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=365)

        # Get portfolio performance
        portfolio_metrics = self.calculate_performance_metrics(
            db, user_id, start_date, end_date
        )

        # Get benchmark performance (simplified - would need actual price data)
        # TODO: Implement actual benchmark comparison using price history
        benchmark_return = Decimal("10.5")  # Placeholder

        excess_return = portfolio_metrics.total_return_percent - benchmark_return

        return {
            "portfolio_return": portfolio_metrics.total_return_percent,
            "benchmark_return": benchmark_return,
            "excess_return": excess_return,
            "alpha": excess_return,  # Simplified alpha calculation
        }
