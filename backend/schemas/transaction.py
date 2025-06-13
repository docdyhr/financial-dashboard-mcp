"""Transaction schemas for transaction history API."""
from datetime import date
from decimal import Decimal

from pydantic import Field, validator

from backend.models.transaction import TransactionType
from backend.schemas.asset import AssetSummary
from backend.schemas.base import BaseSchema, TimestampMixin


class TransactionBase(BaseSchema):
    """Base transaction schema with common fields."""

    transaction_type: TransactionType = Field(..., description="Type of transaction")
    transaction_date: date = Field(..., description="Date of transaction")
    settlement_date: date | None = Field(None, description="Settlement date")
    quantity: Decimal = Field(..., description="Quantity (negative for sells)")
    price_per_share: Decimal = Field(..., ge=0, description="Price per share")
    total_amount: Decimal = Field(..., description="Total transaction amount")
    commission: Decimal = Field(
        default=Decimal("0"), ge=0, description="Commission paid"
    )
    regulatory_fees: Decimal = Field(
        default=Decimal("0"), ge=0, description="Regulatory fees"
    )
    other_fees: Decimal = Field(default=Decimal("0"), ge=0, description="Other fees")
    tax_withheld: Decimal = Field(
        default=Decimal("0"), ge=0, description="Tax withheld"
    )
    account_name: str | None = Field(
        None, max_length=100, description="Account name"
    )
    notes: str | None = Field(None, description="Transaction notes")
    currency: str = Field(default="USD", max_length=3, description="Currency")
    exchange_rate: Decimal = Field(
        default=Decimal("1.0"), gt=0, description="Exchange rate"
    )

    @validator("currency")
    def validate_currency(cls, v):
        """Validate currency format."""
        return v.upper()


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction."""

    user_id: int = Field(..., gt=0, description="User ID")
    asset_id: int = Field(..., gt=0, description="Asset ID")
    position_id: int | None = Field(
        None, gt=0, description="Position ID (for sells/dividends)"
    )
    order_id: str | None = Field(None, max_length=100, description="Order ID")
    confirmation_number: str | None = Field(
        None, max_length=100, description="Confirmation number"
    )
    split_ratio: Decimal | None = Field(
        None, gt=0, description="Split ratio for stock splits"
    )
    data_source: str | None = Field(None, max_length=50, description="Data source")
    external_id: str | None = Field(None, max_length=100, description="External ID")


class TransactionUpdate(BaseSchema):
    """Schema for updating a transaction."""

    transaction_date: date | None = None
    settlement_date: date | None = None
    commission: Decimal | None = Field(None, ge=0)
    regulatory_fees: Decimal | None = Field(None, ge=0)
    other_fees: Decimal | None = Field(None, ge=0)
    tax_withheld: Decimal | None = Field(None, ge=0)
    account_name: str | None = Field(None, max_length=100)
    notes: str | None = None
    confirmation_number: str | None = Field(None, max_length=100)


class TransactionResponse(TransactionBase, TimestampMixin):
    """Schema for transaction response."""

    id: int = Field(..., description="Transaction ID")
    user_id: int = Field(..., description="User ID")
    asset_id: int = Field(..., description="Asset ID")
    position_id: int | None = Field(None, description="Position ID")
    asset: AssetSummary = Field(..., description="Asset information")
    order_id: str | None = Field(None, description="Order ID")
    confirmation_number: str | None = Field(None, description="Confirmation number")
    split_ratio: Decimal | None = Field(None, description="Split ratio")
    data_source: str | None = Field(None, description="Data source")
    external_id: str | None = Field(None, description="External ID")

    # Calculated fields
    net_amount: Decimal = Field(..., description="Net amount after fees")
    realized_gain_loss: Decimal | None = Field(
        None, description="Realized gain/loss for sells"
    )


class TransactionSummary(BaseSchema):
    """Simplified transaction schema for summaries."""

    id: int
    transaction_type: TransactionType
    transaction_date: date
    asset: AssetSummary
    quantity: Decimal
    total_amount: Decimal
    net_amount: Decimal


class TransactionFilters(BaseSchema):
    """Filters for transaction queries."""

    user_id: int | None = None
    asset_id: int | None = None
    position_id: int | None = None
    transaction_type: TransactionType | None = None
    account_name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    min_amount: Decimal | None = Field(None, ge=0)
    max_amount: Decimal | None = Field(None, ge=0)


class BuyTransactionRequest(BaseSchema):
    """Schema for creating a buy transaction."""

    asset_id: int = Field(..., gt=0, description="Asset ID")
    quantity: Decimal = Field(..., gt=0, description="Quantity to buy")
    price_per_share: Decimal = Field(..., ge=0, description="Price per share")
    transaction_date: date = Field(..., description="Transaction date")
    commission: Decimal = Field(default=Decimal("0"), ge=0, description="Commission")
    account_name: str | None = Field(
        None, max_length=100, description="Account name"
    )
    notes: str | None = Field(None, description="Transaction notes")


class SellTransactionRequest(BaseSchema):
    """Schema for creating a sell transaction."""

    position_id: int = Field(..., gt=0, description="Position ID to sell from")
    quantity: Decimal = Field(..., gt=0, description="Quantity to sell")
    price_per_share: Decimal = Field(..., ge=0, description="Price per share")
    transaction_date: date = Field(..., description="Transaction date")
    commission: Decimal = Field(default=Decimal("0"), ge=0, description="Commission")
    account_name: str | None = Field(
        None, max_length=100, description="Account name"
    )
    notes: str | None = Field(None, description="Transaction notes")


class DividendTransactionRequest(BaseSchema):
    """Schema for creating a dividend transaction."""

    position_id: int = Field(..., gt=0, description="Position ID")
    dividend_amount: Decimal = Field(..., gt=0, description="Total dividend amount")
    transaction_date: date = Field(..., description="Transaction date")
    tax_withheld: Decimal = Field(
        default=Decimal("0"), ge=0, description="Tax withheld"
    )
    account_name: str | None = Field(
        None, max_length=100, description="Account name"
    )
    notes: str | None = Field(None, description="Transaction notes")


class TransactionPerformanceMetrics(BaseSchema):
    """Transaction performance analysis."""

    total_transactions: int = Field(
        ..., ge=0, description="Total number of transactions"
    )
    total_buys: int = Field(..., ge=0, description="Number of buy transactions")
    total_sells: int = Field(..., ge=0, description="Number of sell transactions")
    total_dividends: int = Field(
        ..., ge=0, description="Number of dividend transactions"
    )
    total_invested: Decimal = Field(..., description="Total amount invested")
    total_proceeds: Decimal = Field(..., description="Total proceeds from sells")
    total_dividends_received: Decimal = Field(
        ..., description="Total dividends received"
    )
    total_fees_paid: Decimal = Field(..., description="Total fees paid")
    net_cash_flow: Decimal = Field(
        ..., description="Net cash flow (negative = net investment)"
    )
    realized_gains: Decimal = Field(..., description="Total realized gains/losses")


class BulkTransactionImport(BaseSchema):
    """Schema for bulk transaction import."""

    transactions: list[dict] = Field(..., description="List of transactions to import")
    data_source: str = Field(
        ..., max_length=50, description="Source of transaction data"
    )
    validate_only: bool = Field(
        default=False, description="Only validate, don't import"
    )

    class TransactionImportItem(BaseSchema):
        transaction_type: str
        asset_ticker: str
        transaction_date: str
        quantity: str
        price_per_share: str
        commission: str = "0"
        account_name: str | None = None
        notes: str | None = None
