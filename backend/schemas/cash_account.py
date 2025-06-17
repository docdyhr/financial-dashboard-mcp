"""Cash account schemas for API serialization."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CashAccountBase(BaseModel):
    """Base cash account schema."""

    currency: str = Field(..., min_length=3, max_length=3, description="Currency code")
    account_name: str = Field(
        ..., min_length=1, max_length=100, description="Account name"
    )
    is_primary: bool = Field(
        default=True, description="Whether this is the primary account"
    )


class CashAccountCreate(CashAccountBase):
    """Schema for creating a cash account."""

    balance: Decimal = Field(default=Decimal("0"), ge=0, description="Initial balance")


class CashAccountUpdate(BaseModel):
    """Schema for updating a cash account."""

    account_name: str | None = Field(None, min_length=1, max_length=100)
    is_primary: bool | None = None


class CashAccountResponse(CashAccountBase):
    """Schema for cash account responses."""

    id: int
    user_id: int
    balance: Decimal
    formatted_balance: str

    model_config = ConfigDict(from_attributes=True)


class CashTransactionCreate(BaseModel):
    """Schema for cash deposit/withdrawal transactions."""

    account_id: int = Field(..., description="Cash account ID")
    amount: Decimal = Field(
        ...,
        description="Transaction amount (positive for deposit, negative for withdrawal)",
    )
    description: str | None = Field(
        None, max_length=255, description="Transaction description"
    )


class CashTransactionResponse(BaseModel):
    """Schema for cash transaction responses."""

    id: int
    account_id: int
    amount: Decimal
    description: str | None
    transaction_date: str
    new_balance: Decimal

    model_config = ConfigDict(from_attributes=True)
