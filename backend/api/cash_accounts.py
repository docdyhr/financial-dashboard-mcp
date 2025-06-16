"""Cash account API endpoints."""

from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.models import get_db
from backend.schemas.cash_account import (
    CashAccountCreate,
    CashAccountResponse,
    CashTransactionCreate,
)
from backend.services.cash_account import CashAccountService

router = APIRouter(prefix="/cash-accounts", tags=["cash-accounts"])


def get_cash_service() -> CashAccountService:
    """Get cash account service instance."""
    return CashAccountService()


@router.get("/", response_model=list[CashAccountResponse])
def list_cash_accounts(
    user_id: int,
    db: Session = Depends(get_db),
    cash_service: CashAccountService = Depends(get_cash_service),
):
    """List all cash accounts for a user."""
    return cash_service.get_user_cash_accounts(db, user_id)


@router.get("/balance", response_model=dict[str, Decimal])
def get_cash_balances(
    user_id: int,
    currency: str = "USD",
    db: Session = Depends(get_db),
    cash_service: CashAccountService = Depends(get_cash_service),
):
    """Get total cash balance for a user in a specific currency."""
    balance = cash_service.get_cash_balance(db, user_id, currency)
    return {"currency": currency, "balance": balance}


@router.get("/primary", response_model=CashAccountResponse)
def get_primary_cash_account(
    user_id: int,
    currency: str = "USD",
    db: Session = Depends(get_db),
    cash_service: CashAccountService = Depends(get_cash_service),
):
    """Get the primary cash account for a user and currency."""
    return cash_service.get_primary_cash_account(db, user_id, currency)


@router.post("/", response_model=CashAccountResponse)
def create_cash_account(
    user_id: int,
    account_data: CashAccountCreate,
    db: Session = Depends(get_db),
    cash_service: CashAccountService = Depends(get_cash_service),
):
    """Create a new cash account."""
    return cash_service.create_cash_account(db, user_id, account_data)


@router.post("/transaction", response_model=CashAccountResponse)
def process_cash_transaction(
    user_id: int,
    transaction_data: CashTransactionCreate,
    db: Session = Depends(get_db),
    cash_service: CashAccountService = Depends(get_cash_service),
):
    """Process a cash deposit or withdrawal."""
    return cash_service.process_cash_transaction(db, user_id, transaction_data)


@router.post("/transfer", response_model=dict[str, CashAccountResponse])
def transfer_between_accounts(
    user_id: int,
    from_account_id: int,
    to_account_id: int,
    amount: Decimal,
    description: str = None,
    db: Session = Depends(get_db),
    cash_service: CashAccountService = Depends(get_cash_service),
):
    """Transfer money between cash accounts."""
    from_account, to_account = cash_service.transfer_between_accounts(
        db, user_id, from_account_id, to_account_id, amount, description
    )
    return {"from_account": from_account, "to_account": to_account}


@router.put("/{account_id}/primary", response_model=CashAccountResponse)
def set_primary_account(
    user_id: int,
    account_id: int,
    db: Session = Depends(get_db),
    cash_service: CashAccountService = Depends(get_cash_service),
):
    """Set a cash account as primary for its currency."""
    return cash_service.set_primary_account(db, user_id, account_id)


@router.delete("/{account_id}")
def delete_cash_account(
    user_id: int,
    account_id: int,
    db: Session = Depends(get_db),
    cash_service: CashAccountService = Depends(get_cash_service),
):
    """Delete a cash account (only if balance is zero)."""
    cash_service.delete_cash_account(db, user_id, account_id)
    return {"message": "Cash account deleted successfully"}
