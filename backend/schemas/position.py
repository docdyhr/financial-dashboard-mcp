"""Position schemas for portfolio holdings API."""
from decimal import Decimal

from pydantic import Field, validator

from backend.schemas.asset import AssetSummary
from backend.schemas.base import BaseSchema, TimestampMixin


class PositionBase(BaseSchema):
    """Base position schema with common fields."""

    quantity: Decimal = Field(..., gt=0, description="Number of shares/units held")
    average_cost_per_share: Decimal = Field(
        ..., ge=0, description="Average cost per share"
    )
    total_cost_basis: Decimal = Field(
        ..., ge=0, description="Total cost basis of position"
    )
    account_name: str | None = Field(
        None, max_length=100, description="Account name"
    )
    notes: str | None = Field(None, max_length=500, description="Position notes")
    tax_lot_method: str = Field(
        default="FIFO", max_length=20, description="Tax lot method"
    )

    @validator("tax_lot_method")
    def validate_tax_lot_method(cls, v):
        """Validate tax lot method."""
        allowed_methods = ["FIFO", "LIFO", "SpecificID"]
        if v not in allowed_methods:
            raise ValueError(f"Tax lot method must be one of: {allowed_methods}")
        return v


class PositionCreate(PositionBase):
    """Schema for creating a new position."""

    asset_id: int = Field(..., gt=0, description="Asset ID")
    user_id: int = Field(..., gt=0, description="User ID")


class PositionUpdate(BaseSchema):
    """Schema for updating a position."""

    quantity: Decimal | None = Field(
        None, gt=0, description="Number of shares/units held"
    )
    account_name: str | None = Field(
        None, max_length=100, description="Account name"
    )
    notes: str | None = Field(None, max_length=500, description="Position notes")
    tax_lot_method: str | None = Field(
        None, max_length=20, description="Tax lot method"
    )
    is_active: bool | None = None

    @validator("tax_lot_method")
    def validate_tax_lot_method(cls, v):
        """Validate tax lot method."""
        if v is not None:
            allowed_methods = ["FIFO", "LIFO", "SpecificID"]
            if v not in allowed_methods:
                raise ValueError(f"Tax lot method must be one of: {allowed_methods}")
        return v


class PositionResponse(PositionBase, TimestampMixin):
    """Schema for position response."""

    id: int = Field(..., description="Position ID")
    user_id: int = Field(..., description="User ID")
    asset_id: int = Field(..., description="Asset ID")
    asset: AssetSummary = Field(..., description="Asset information")
    is_active: bool = Field(default=True, description="Whether position is active")

    # Calculated fields
    current_value: Decimal | None = Field(None, description="Current market value")
    unrealized_gain_loss: Decimal | None = Field(
        None, description="Unrealized gain/loss"
    )
    unrealized_gain_loss_percent: Decimal | None = Field(
        None, description="Unrealized gain/loss percentage"
    )
    weight_in_portfolio: Decimal | None = Field(
        None, description="Weight in portfolio percentage"
    )


class PositionSummary(BaseSchema):
    """Simplified position schema for portfolio summaries."""

    id: int
    asset: AssetSummary
    quantity: Decimal
    current_value: Decimal | None = None
    unrealized_gain_loss: Decimal | None = None
    unrealized_gain_loss_percent: Decimal | None = None
    weight_in_portfolio: Decimal | None = None


class PositionFilters(BaseSchema):
    """Filters for position queries."""

    user_id: int | None = None
    asset_type: str | None = None
    category: str | None = None
    account_name: str | None = None
    is_active: bool = True
    min_value: Decimal | None = Field(
        None, ge=0, description="Minimum position value"
    )
    max_value: Decimal | None = Field(
        None, ge=0, description="Maximum position value"
    )


class PositionAdjustment(BaseSchema):
    """Schema for position adjustments (buy more or sell)."""

    quantity: Decimal = Field(
        ..., description="Quantity to add (positive) or remove (negative)"
    )
    price_per_share: Decimal = Field(
        ..., ge=0, description="Price per share for adjustment"
    )
    commission: Decimal = Field(
        default=Decimal("0"), ge=0, description="Commission paid"
    )
    notes: str | None = Field(None, max_length=500, description="Adjustment notes")


class BulkPositionUpdate(BaseSchema):
    """Schema for bulk position updates."""

    positions: list[dict] = Field(..., description="List of position updates")

    class PositionUpdateItem(BaseSchema):
        position_id: int
        quantity: Decimal | None = None
        current_value: Decimal | None = None
        notes: str | None = None


class PositionPerformanceMetrics(BaseSchema):
    """Position performance metrics."""

    total_return: Decimal = Field(..., description="Total return amount")
    total_return_percent: Decimal = Field(..., description="Total return percentage")
    annualized_return: Decimal | None = Field(
        None, description="Annualized return percentage"
    )
    days_held: int = Field(
        ..., ge=0, description="Number of days position has been held"
    )
    dividend_income: Decimal = Field(
        default=Decimal("0"), description="Total dividend income"
    )
    realized_gains: Decimal = Field(
        default=Decimal("0"), description="Realized gains from sales"
    )


class PositionAllocation(BaseSchema):
    """Position allocation within portfolio."""

    position_id: int
    asset_ticker: str
    asset_name: str
    category: str
    current_value: Decimal
    weight_percent: Decimal
    target_weight_percent: Decimal | None = None
    deviation_from_target: Decimal | None = None
