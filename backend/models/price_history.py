"""Price history model for tracking historical asset prices."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.asset import Asset


class PriceHistory(Base):
    """Price history model for tracking historical asset prices."""

    __tablename__ = "price_history"

    # Foreign key relationships
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id"), nullable=False, index=True
    )

    # Date and price information
    price_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # OHLCV data
    open_price: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=12, scale=4), nullable=True
    )
    high_price: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=12, scale=4), nullable=True
    )
    low_price: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=12, scale=4), nullable=True
    )
    close_price: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=4), nullable=False
    )
    adjusted_close: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=12, scale=4), nullable=True
    )
    volume: Mapped[int | None] = mapped_column(nullable=True)

    # Calculated fields
    daily_return: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=8, scale=6), nullable=True
    )  # Daily return percentage

    # Metadata
    data_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_adjusted: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    asset: Mapped["Asset"] = relationship("Asset", back_populates="price_history")

    # Constraints
    __table_args__ = (
        UniqueConstraint("asset_id", "price_date", name="unique_asset_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<PriceHistory(id={self.id}, asset_id={self.asset_id}, "
            f"date={self.price_date}, close={self.close_price})>"
        )

    @property
    def price_change(self) -> Decimal | None:
        """Calculate absolute price change from open to close."""
        if self.open_price and self.close_price:
            return self.close_price - self.open_price
        return None

    @property
    def price_change_percent(self) -> Decimal | None:
        """Calculate percentage price change from open to close."""
        if self.open_price and self.close_price and self.open_price > 0:
            return ((self.close_price - self.open_price) / self.open_price) * 100
        return None

    @property
    def day_range(self) -> Decimal | None:
        """Calculate the day's trading range (high - low)."""
        if self.high_price and self.low_price:
            return self.high_price - self.low_price
        return None

    @classmethod
    def create_from_yahoo_data(
        cls,
        asset_id: int,
        price_date: date,
        yahoo_data: dict[str, float | int | str],
        data_source: str = "yfinance",
    ) -> "PriceHistory":
        """Factory method to create price history from Yahoo Finance data."""
        return cls(  # type: ignore[call-arg]
            asset_id=asset_id,
            price_date=price_date,
            open_price=(
                Decimal(str(yahoo_data.get("Open", 0)))
                if yahoo_data.get("Open") is not None
                else None
            ),
            high_price=(
                Decimal(str(yahoo_data.get("High", 0)))
                if yahoo_data.get("High") is not None
                else None
            ),
            low_price=(
                Decimal(str(yahoo_data.get("Low", 0)))
                if yahoo_data.get("Low") is not None
                else None
            ),
            close_price=Decimal(
                str(yahoo_data.get("Close", 0))
            ),  # Assuming Close is always present and non-null
            adjusted_close=(
                Decimal(str(yahoo_data.get("Adj Close", 0)))
                if yahoo_data.get("Adj Close") is not None
                else None
            ),
            volume=(
                int(yahoo_data.get("Volume", 0))
                if yahoo_data.get("Volume") is not None
                else None
            ),
            data_source=data_source,
            is_adjusted=True,  # Assuming Yahoo data is typically adjusted
        )

    @classmethod
    def create_placeholder(
        cls, asset_id: int, price_date: date, close_price: Decimal
    ) -> "PriceHistory":
        """Factory method to create a placeholder price history entry."""
        return cls(  # type: ignore[call-arg]
            asset_id=asset_id,
            price_date=price_date,
            close_price=close_price,
            data_source="placeholder",
            is_adjusted=False,
        )

    def calculate_daily_return(self, previous_close: Decimal | None) -> None:
        """Calculate and set daily return based on previous day's close."""
        if previous_close and previous_close > 0:
            self.daily_return = (
                (self.close_price - previous_close) / previous_close
            ) * 100
        else:
            self.daily_return = None
