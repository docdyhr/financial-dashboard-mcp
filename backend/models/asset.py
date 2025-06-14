"""Asset model for tracking stocks, bonds, ETFs, and other financial instruments."""

from enum import Enum

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class AssetType(str, Enum):
    """Enumeration of asset types."""

    STOCK = "stock"
    BOND = "bond"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    CRYPTO = "crypto"
    CASH = "cash"
    COMMODITY = "commodity"
    REAL_ESTATE = "real_estate"
    OTHER = "other"


class AssetCategory(str, Enum):
    """Asset category for allocation tracking."""

    EQUITY = "equity"
    FIXED_INCOME = "fixed_income"
    ALTERNATIVE = "alternative"
    CASH_EQUIVALENT = "cash_equivalent"
    COMMODITY = "commodity"
    REAL_ESTATE = "real_estate"


class Asset(Base):
    """Asset model for tracking financial instruments."""

    __tablename__ = "assets"

    # Basic asset information
    ticker: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Asset classification
    asset_type: Mapped[AssetType] = mapped_column(SQLEnum(AssetType), nullable=False)
    category: Mapped[AssetCategory] = mapped_column(
        SQLEnum(AssetCategory), nullable=False
    )
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Market information
    exchange: Mapped[str | None] = mapped_column(String(20), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    country: Mapped[str | None] = mapped_column(
        String(2), nullable=True
    )  # ISO country code

    # Current market data (will be updated by background tasks)
    current_price: Mapped[float | None] = mapped_column(
        Numeric(precision=12, scale=4), nullable=True
    )
    previous_close: Mapped[float | None] = mapped_column(
        Numeric(precision=12, scale=4), nullable=True
    )
    day_change: Mapped[float | None] = mapped_column(
        Numeric(precision=12, scale=4), nullable=True
    )
    day_change_percent: Mapped[float | None] = mapped_column(
        Numeric(precision=8, scale=4), nullable=True
    )

    # Market cap and financial metrics
    market_cap: Mapped[float | None] = mapped_column(
        Numeric(precision=20, scale=2), nullable=True
    )
    pe_ratio: Mapped[float | None] = mapped_column(
        Numeric(precision=8, scale=2), nullable=True
    )
    dividend_yield: Mapped[float | None] = mapped_column(
        Numeric(precision=8, scale=4), nullable=True
    )

    # Asset metadata
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    data_source: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # e.g., "yfinance", "alpha_vantage"

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, ticker={self.ticker}, name={self.name}, type={self.asset_type})>"

    @property
    def display_name(self) -> str:
        """Return a display-friendly name for the asset."""
        return f"{self.ticker} - {self.name}"

    @property
    def is_equity(self) -> bool:
        """Check if asset is an equity instrument."""
        return self.category == AssetCategory.EQUITY

    @property
    def is_fixed_income(self) -> bool:
        """Check if asset is a fixed income instrument."""
        return self.category == AssetCategory.FIXED_INCOME
