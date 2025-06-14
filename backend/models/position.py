"""Position model for tracking user portfolio holdings."""

from decimal import Decimal
from typing import TYPE_CHECKING, Any, List  # Add List, TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.asset import Asset  # noqa: F401
    from backend.models.transaction import Transaction  # noqa: F401
    from backend.models.user import User  # noqa: F401


class Position(Base):
    """Position model for tracking user holdings in their portfolio."""

    __tablename__ = "positions"

    # Foreign key relationships
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id"), nullable=False, index=True
    )

    # Position details
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False
    )  # Support fractional shares and crypto

    # Cost basis information
    average_cost_per_share: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=4), nullable=False
    )
    total_cost_basis: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=4), nullable=False
    )

    # Position metadata
    account_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Tax information
    tax_lot_method: Mapped[str] = mapped_column(
        String(20), default="FIFO", nullable=False
    )  # FIFO, LIFO, SpecificID

    # Status
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="positions")
    asset: Mapped[Asset] = relationship("Asset", back_populates="positions")
    transactions: Mapped[List[Transaction]] = relationship(
        "Transaction",
        back_populates="position",
        cascade="all, delete-orphan",
    )

    def __init__(self, **kwargs: Any) -> None:  # Add explicit __init__
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Position(id={self.id}, user_id={self.user_id}, asset_id={self.asset_id}, quantity={self.quantity})>"

    @property
    def current_value(self) -> Decimal | None:
        """Calculate current market value of the position."""
        if self.asset and self.asset.current_price:
            return Decimal(str(self.asset.current_price)) * self.quantity
        return None

    @property
    def unrealized_gain_loss(self) -> Decimal | None:
        """Calculate unrealized gain/loss."""
        current_val = self.current_value
        if current_val is not None:
            return current_val - self.total_cost_basis
        return None

    @property
    def unrealized_gain_loss_percent(self) -> Decimal | None:
        """Calculate unrealized gain/loss percentage."""
        unrealized = self.unrealized_gain_loss
        if unrealized is not None and self.total_cost_basis > 0:
            return (unrealized / self.total_cost_basis) * 100
        return None

    @property
    def weight_in_portfolio(self) -> Decimal | None:
        """Calculate position weight in total portfolio (requires portfolio context)."""
        # This would need to be calculated with portfolio total value
        # Implementation depends on how we calculate total portfolio value
        return None

    def update_cost_basis(self, new_quantity: Decimal, new_cost: Decimal) -> None:
        """Update cost basis when adding to position."""
        if new_quantity <= 0:
            return

        total_new_cost = self.total_cost_basis + new_cost
        total_new_quantity = self.quantity + new_quantity

        self.quantity = total_new_quantity
        self.total_cost_basis = total_new_cost

        if total_new_quantity > 0:
            self.average_cost_per_share = total_new_cost / total_new_quantity

    def reduce_position(self, quantity_to_sell: Decimal) -> Decimal:
        """Reduce position size and return the cost basis of sold shares."""
        if quantity_to_sell <= 0 or quantity_to_sell > self.quantity:
            raise ValueError("Invalid quantity to sell")

        # Calculate cost basis of shares being sold
        cost_basis_per_share = self.average_cost_per_share
        sold_cost_basis = cost_basis_per_share * quantity_to_sell

        # Update position
        self.quantity -= quantity_to_sell
        self.total_cost_basis -= sold_cost_basis

        # If position is closed, mark as inactive
        if self.quantity == 0:
            self.is_active = False

        return sold_cost_basis
