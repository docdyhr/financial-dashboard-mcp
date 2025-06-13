"""Transaction model for tracking all portfolio transactions."""
from datetime import date
from decimal import Decimal
from enum import Enum

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


class TransactionType(str, Enum):
    """Enumeration of transaction types."""

    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    SPLIT = "split"
    MERGER = "merger"
    SPINOFF = "spinoff"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    CASH_DEPOSIT = "cash_deposit"
    CASH_WITHDRAWAL = "cash_withdrawal"
    FEE = "fee"
    INTEREST = "interest"
    OTHER = "other"


class Transaction(Base):
    """Transaction model for tracking all portfolio transactions."""

    __tablename__ = "transactions"

    # Foreign key relationships
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id"), nullable=False, index=True
    )
    position_id: Mapped[int | None] = mapped_column(
        ForeignKey("positions.id"), nullable=True, index=True
    )

    # Transaction details
    transaction_type: Mapped[TransactionType] = mapped_column(
        SQLEnum(TransactionType), nullable=False, index=True
    )
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    settlement_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Quantity and pricing
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False
    )  # Can be negative for sells
    price_per_share: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=4), nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=4), nullable=False
    )  # Gross amount before fees

    # Fees and taxes
    commission: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=4), default=0, nullable=False
    )
    regulatory_fees: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=4), default=0, nullable=False
    )
    other_fees: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=4), default=0, nullable=False
    )
    tax_withheld: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=4), default=0, nullable=False
    )

    # Transaction metadata
    account_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    order_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confirmation_number: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    # Additional information
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Split/merger specific fields
    split_ratio: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=10, scale=6), nullable=True
    )  # For stock splits (e.g., 2.0 for 2:1 split)

    # Currency information
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=6), default=1.0, nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="transactions")
    asset = relationship("Asset", back_populates="transactions")
    position = relationship("Position", back_populates="transactions")

    def __repr__(self) -> str:
        return (
            f"<Transaction(id={self.id}, type={self.transaction_type}, "
            f"asset_id={self.asset_id}, quantity={self.quantity}, "
            f"date={self.transaction_date})>"
        )

    @property
    def net_amount(self) -> Decimal:
        """Calculate net amount after all fees."""
        total_fees = self.commission + self.regulatory_fees + self.other_fees
        return self.total_amount - total_fees

    @property
    def is_buy_transaction(self) -> bool:
        """Check if this is a buy transaction."""
        return self.transaction_type in [
            TransactionType.BUY,
            TransactionType.TRANSFER_IN,
            TransactionType.CASH_DEPOSIT,
        ]

    @property
    def is_sell_transaction(self) -> bool:
        """Check if this is a sell transaction."""
        return self.transaction_type in [
            TransactionType.SELL,
            TransactionType.TRANSFER_OUT,
            TransactionType.CASH_WITHDRAWAL,
        ]

    @property
    def is_income_transaction(self) -> bool:
        """Check if this is an income transaction."""
        return self.transaction_type in [
            TransactionType.DIVIDEND,
            TransactionType.INTEREST,
        ]

    @property
    def affects_position(self) -> bool:
        """Check if this transaction affects position quantity."""
        return self.transaction_type in [
            TransactionType.BUY,
            TransactionType.SELL,
            TransactionType.SPLIT,
            TransactionType.TRANSFER_IN,
            TransactionType.TRANSFER_OUT,
        ]

    def calculate_realized_gain_loss(self, cost_basis_sold: Decimal) -> Decimal:
        """Calculate realized gain/loss for a sell transaction."""
        if not self.is_sell_transaction:
            return Decimal("0")

        proceeds = self.net_amount
        return proceeds - cost_basis_sold

    @classmethod
    def create_buy_transaction(
        cls,
        user_id: int,
        asset_id: int,
        quantity: Decimal,
        price_per_share: Decimal,
        transaction_date: date,
        commission: Decimal = Decimal("0"),
        **kwargs,
    ) -> "Transaction":
        """Factory method to create a buy transaction."""
        total_amount = quantity * price_per_share

        return cls(
            user_id=user_id,
            asset_id=asset_id,
            transaction_type=TransactionType.BUY,
            quantity=quantity,
            price_per_share=price_per_share,
            total_amount=total_amount,
            transaction_date=transaction_date,
            commission=commission,
            **kwargs,
        )

    @classmethod
    def create_sell_transaction(
        cls,
        user_id: int,
        asset_id: int,
        position_id: int,
        quantity: Decimal,
        price_per_share: Decimal,
        transaction_date: date,
        commission: Decimal = Decimal("0"),
        **kwargs,
    ) -> "Transaction":
        """Factory method to create a sell transaction."""
        total_amount = quantity * price_per_share

        return cls(
            user_id=user_id,
            asset_id=asset_id,
            position_id=position_id,
            transaction_type=TransactionType.SELL,
            quantity=-quantity,  # Negative for sells
            price_per_share=price_per_share,
            total_amount=total_amount,
            transaction_date=transaction_date,
            commission=commission,
            **kwargs,
        )

    @classmethod
    def create_dividend_transaction(
        cls,
        user_id: int,
        asset_id: int,
        position_id: int,
        dividend_amount: Decimal,
        transaction_date: date,
        shares_held: Decimal,
        **kwargs,
    ) -> "Transaction":
        """Factory method to create a dividend transaction."""
        price_per_share = (
            dividend_amount / shares_held if shares_held > 0 else Decimal("0")
        )

        return cls(
            user_id=user_id,
            asset_id=asset_id,
            position_id=position_id,
            transaction_type=TransactionType.DIVIDEND,
            quantity=shares_held,
            price_per_share=price_per_share,
            total_amount=dividend_amount,
            transaction_date=transaction_date,
            **kwargs,
        )
