"""Asset schemas for API requests and responses."""

from decimal import Decimal

from pydantic import Field, field_validator

from backend.models.asset import AssetCategory, AssetType
from backend.schemas.base import BaseSchema, TimestampMixin


class AssetBase(BaseSchema):
    """Base asset schema with common fields."""

    ticker: str = Field(
        ..., min_length=1, max_length=20, description="Asset ticker symbol"
    )
    name: str = Field(..., min_length=1, max_length=255, description="Asset name")
    description: str | None = Field(
        None, max_length=1000, description="Asset description"
    )
    asset_type: AssetType = Field(..., description="Type of asset")
    category: AssetCategory = Field(..., description="Asset category for allocation")
    sector: str | None = Field(
        None, max_length=100, description="Sector classification"
    )
    industry: str | None = Field(
        None, max_length=100, description="Industry classification"
    )
    exchange: str | None = Field(
        None, max_length=20, description="Exchange where asset is traded"
    )
    currency: str = Field(
        default="USD", max_length=3, description="Currency denomination"
    )
    country: str | None = Field(
        None, max_length=2, description="Country code (ISO 2-letter)"
    )

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Validate ticker format."""
        if not v or not v.strip():
            raise ValueError("Ticker cannot be empty")
        return v.upper().strip()

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency format."""
        return v.upper()

    @field_validator("asset_type", mode="before")
    @classmethod
    def validate_asset_type(cls, v: str | AssetType) -> str:
        """Validate asset type, accepting both upper and lower case."""
        if isinstance(v, str):
            # Convert to lowercase to match enum values
            return v.lower()
        return v.value if hasattr(v, "value") else str(v)

    @field_validator("category", mode="before")
    @classmethod
    def validate_category(cls, v: str | AssetCategory) -> str:
        """Validate category, accepting both upper and lower case."""
        if isinstance(v, str):
            # Convert to lowercase to match enum values
            return v.lower()
        return v.value if hasattr(v, "value") else str(v)


class AssetCreate(AssetBase):
    """Schema for creating a new asset."""


class AssetUpdate(BaseSchema):
    """Schema for updating an asset."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    sector: str | None = Field(None, max_length=100)
    industry: str | None = Field(None, max_length=100)
    exchange: str | None = Field(None, max_length=20)
    currency: str | None = Field(None, max_length=3)
    country: str | None = Field(None, max_length=2)
    is_active: bool | None = None

    @field_validator("currency", mode="before")
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        """Validate currency format."""
        if v is not None:
            return v.upper()
        return v


class AssetMarketData(BaseSchema):
    """Schema for asset market data."""

    current_price: Decimal | None = Field(
        None, ge=0, description="Current market price"
    )
    previous_close: Decimal | None = Field(
        None, ge=0, description="Previous close price"
    )
    day_change: Decimal | None = Field(None, description="Absolute price change")
    day_change_percent: Decimal | None = Field(
        None, description="Percentage price change"
    )
    market_cap: Decimal | None = Field(None, ge=0, description="Market capitalization")
    pe_ratio: Decimal | None = Field(None, ge=0, description="Price-to-earnings ratio")
    dividend_yield: Decimal | None = Field(
        None, ge=0, le=100, description="Dividend yield percentage"
    )
    data_source: str | None = Field(None, max_length=50, description="Data source")


class AssetResponse(AssetBase, AssetMarketData, TimestampMixin):
    """Schema for asset response."""

    id: int = Field(..., description="Asset ID")
    is_active: bool = Field(default=True, description="Whether asset is active")

    @property
    def display_name(self) -> str:
        """Display-friendly name for the asset."""
        return f"{self.ticker} - {self.name}"

    @property
    def is_equity(self) -> bool:
        """Check if asset is an equity instrument."""
        return self.category == AssetCategory.EQUITY

    @property
    def is_fixed_income(self) -> bool:
        """Check if asset is a fixed income instrument."""
        return self.category == AssetCategory.FIXED_INCOME


class AssetSummary(BaseSchema):
    """Simplified asset schema for lists and references."""

    id: int
    ticker: str
    name: str
    asset_type: AssetType
    category: AssetCategory
    current_price: Decimal | None = None
    currency: str = "USD"
    is_active: bool = True


class AssetSearchParams(BaseSchema):
    """Parameters for asset search."""

    query: str | None = Field(None, description="Search query (ticker or name)")
    asset_type: AssetType | None = Field(None, description="Filter by asset type")
    category: AssetCategory | None = Field(None, description="Filter by category")
    sector: str | None = Field(None, description="Filter by sector")
    exchange: str | None = Field(None, description="Filter by exchange")
    currency: str | None = Field(None, description="Filter by currency")
    is_active: bool = Field(True, description="Filter by active status")


class AssetPriceUpdate(BaseSchema):
    """Schema for updating asset prices."""

    current_price: Decimal = Field(..., ge=0, description="New current price")
    previous_close: Decimal | None = Field(
        None, ge=0, description="Previous close price"
    )
    data_source: str = Field(..., max_length=50, description="Source of price data")

    @property
    def day_change(self) -> Decimal | None:
        """Calculate absolute price change."""
        if self.previous_close:
            return self.current_price - self.previous_close
        return None

    @property
    def day_change_percent(self) -> Decimal | None:
        """Calculate percentage price change."""
        if self.previous_close and self.previous_close > 0:
            return (
                (self.current_price - self.previous_close) / self.previous_close
            ) * 100
        return None


class Update(BaseSchema):
    ticker: str
    current_price: Decimal
    previous_close: Decimal | None = None


class BulkAssetPriceUpdate(BaseSchema):
    """Schema for bulk asset price updates."""

    updates: list[Update] = Field(..., description="List of price updates")
    data_source: str = Field(..., max_length=50, description="Source of price data")
