"""Portfolio snapshot model for tracking portfolio performance over time."""
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


class PortfolioSnapshot(Base):
    """Portfolio snapshot model for tracking portfolio value and performance over time."""

    __tablename__ = "portfolio_snapshots"

    # Foreign key relationships
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    # Snapshot date
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Portfolio values
    total_value: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=4), nullable=False
    )
    total_cost_basis: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=4), nullable=False
    )
    cash_balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=4), default=0, nullable=False
    )
    invested_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=4), nullable=False
    )

    # Performance metrics
    total_gain_loss: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=4), nullable=False
    )
    total_gain_loss_percent: Mapped[Decimal] = mapped_column(
        Numeric(precision=8, scale=4), nullable=False
    )
    daily_change: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=20, scale=4), nullable=True
    )
    daily_change_percent: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=8, scale=4), nullable=True
    )

    # Asset allocation breakdown
    equity_value: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=4), default=0, nullable=False
    )
    fixed_income_value: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=4), default=0, nullable=False
    )
    alternative_value: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=4), default=0, nullable=False
    )
    cash_equivalent_value: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=4), default=0, nullable=False
    )
    commodity_value: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=4), default=0, nullable=False
    )
    real_estate_value: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=4), default=0, nullable=False
    )

    # Portfolio metrics
    number_of_positions: Mapped[int] = mapped_column(default=0, nullable=False)
    number_of_assets: Mapped[int] = mapped_column(default=0, nullable=False)

    # Risk metrics (calculated periodically)
    portfolio_beta: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=8, scale=4), nullable=True
    )
    sharpe_ratio: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=8, scale=4), nullable=True
    )
    volatility: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=8, scale=4), nullable=True
    )

    # Benchmark comparison
    benchmark_return: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=8, scale=4), nullable=True
    )
    alpha: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=8, scale=4), nullable=True
    )

    # Metadata
    calculation_method: Mapped[str] = mapped_column(
        String(50), default="market_value", nullable=False
    )
    data_quality_score: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=3, scale=2), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    user = relationship("User", back_populates="portfolio_snapshots")

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "snapshot_date", name="unique_user_snapshot_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<PortfolioSnapshot(id={self.id}, user_id={self.user_id}, "
            f"date={self.snapshot_date}, total_value={self.total_value})>"
        )

    @property
    def equity_allocation_percent(self) -> Decimal:
        """Calculate equity allocation as percentage of total portfolio."""
        if self.total_value > 0:
            return (self.equity_value / self.total_value) * 100
        return Decimal("0")

    @property
    def fixed_income_allocation_percent(self) -> Decimal:
        """Calculate fixed income allocation as percentage of total portfolio."""
        if self.total_value > 0:
            return (self.fixed_income_value / self.total_value) * 100
        return Decimal("0")

    @property
    def cash_allocation_percent(self) -> Decimal:
        """Calculate cash allocation as percentage of total portfolio."""
        if self.total_value > 0:
            return (self.cash_balance / self.total_value) * 100
        return Decimal("0")

    @property
    def alternative_allocation_percent(self) -> Decimal:
        """Calculate alternative investments allocation as percentage of total portfolio."""
        if self.total_value > 0:
            return (self.alternative_value / self.total_value) * 100
        return Decimal("0")

    @property
    def total_invested_value(self) -> Decimal:
        """Calculate total invested value (excluding cash)."""
        return self.total_value - self.cash_balance

    @property
    def is_profitable(self) -> bool:
        """Check if portfolio is currently profitable."""
        return self.total_gain_loss > 0

    @property
    def allocation_summary(self) -> dict:
        """Get allocation summary as percentages."""
        return {
            "equity": float(self.equity_allocation_percent),
            "fixed_income": float(self.fixed_income_allocation_percent),
            "alternative": float(self.alternative_allocation_percent),
            "cash": float(self.cash_allocation_percent),
            "commodity": float(
                (self.commodity_value / self.total_value * 100)
                if self.total_value > 0
                else 0
            ),
            "real_estate": float(
                (self.real_estate_value / self.total_value * 100)
                if self.total_value > 0
                else 0
            ),
        }

    def calculate_daily_change(
        self, previous_snapshot: Optional["PortfolioSnapshot"]
    ) -> None:
        """Calculate daily change based on previous snapshot."""
        if previous_snapshot:
            self.daily_change = self.total_value - previous_snapshot.total_value
            if previous_snapshot.total_value > 0:
                self.daily_change_percent = (
                    self.daily_change / previous_snapshot.total_value
                ) * 100
            else:
                self.daily_change_percent = Decimal("0")
        else:
            self.daily_change = None
            self.daily_change_percent = None

    @classmethod
    def create_from_positions(
        cls,
        user_id: int,
        snapshot_date: date,
        positions: list,
        cash_balance: Decimal = Decimal("0"),
        **kwargs,
    ) -> "PortfolioSnapshot":
        """Factory method to create portfolio snapshot from current positions."""
        total_value = cash_balance
        total_cost_basis = Decimal("0")
        equity_value = Decimal("0")
        fixed_income_value = Decimal("0")
        alternative_value = Decimal("0")
        cash_equivalent_value = Decimal("0")
        commodity_value = Decimal("0")
        real_estate_value = Decimal("0")

        for position in positions:
            if position.current_value:
                total_value += position.current_value
                total_cost_basis += position.total_cost_basis

                # Categorize by asset category
                if position.asset.category == "equity":
                    equity_value += position.current_value
                elif position.asset.category == "fixed_income":
                    fixed_income_value += position.current_value
                elif position.asset.category == "alternative":
                    alternative_value += position.current_value
                elif position.asset.category == "cash_equivalent":
                    cash_equivalent_value += position.current_value
                elif position.asset.category == "commodity":
                    commodity_value += position.current_value
                elif position.asset.category == "real_estate":
                    real_estate_value += position.current_value

        total_gain_loss = total_value - total_cost_basis - cash_balance
        total_gain_loss_percent = (
            (total_gain_loss / total_cost_basis * 100)
            if total_cost_basis > 0
            else Decimal("0")
        )

        return cls(
            user_id=user_id,
            snapshot_date=snapshot_date,
            total_value=total_value,
            total_cost_basis=total_cost_basis,
            cash_balance=cash_balance,
            invested_amount=total_value - cash_balance,
            total_gain_loss=total_gain_loss,
            total_gain_loss_percent=total_gain_loss_percent,
            equity_value=equity_value,
            fixed_income_value=fixed_income_value,
            alternative_value=alternative_value,
            cash_equivalent_value=cash_equivalent_value,
            commodity_value=commodity_value,
            real_estate_value=real_estate_value,
            number_of_positions=len(positions),
            number_of_assets=len(set(p.asset_id for p in positions)),
            **kwargs,
        )
