"""Cash account model for tracking cash balances."""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.user import User


class CashAccount(Base):
    """Cash account model for tracking user cash balances by currency."""

    __tablename__ = "cash_accounts"

    # Foreign key to user
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Currency for this cash account (USD, EUR, etc.)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    # Current balance
    balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), nullable=False, default=Decimal("0")
    )

    # Account name/description
    account_name: Mapped[str] = mapped_column(
        String(100), nullable=False, default="Main Cash"
    )

    # Whether this is the primary cash account for this currency
    is_primary: Mapped[bool] = mapped_column(nullable=False, default=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="cash_accounts")

    def __repr__(self) -> str:
        return f"<CashAccount(id={self.id}, user_id={self.user_id}, currency={self.currency}, balance={self.balance})>"

    @property
    def formatted_balance(self) -> str:
        """Return formatted balance with currency symbol."""
        currency_symbols = {"USD": "$", "EUR": "€", "GBP": "£"}
        symbol = currency_symbols.get(self.currency, self.currency)
        return f"{symbol}{self.balance:,.2f}"
