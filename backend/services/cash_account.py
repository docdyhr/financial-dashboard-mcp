"""Cash account service for managing user cash balances."""

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.models import CashAccount, User
from backend.schemas.cash_account import CashAccountCreate, CashTransactionCreate


class CashAccountService:
    """Service for cash account operations."""

    def __init__(self) -> None:
        """Initialize cash account service."""

    def get_user_cash_accounts(self, db: Session, user_id: int) -> list[CashAccount]:
        """Get all cash accounts for a user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=404, detail=f"User with ID {user_id} not found"
            )

        return (
            db.query(CashAccount)
            .filter(CashAccount.user_id == user_id)
            .order_by(CashAccount.is_primary.desc(), CashAccount.currency)
            .all()
        )

    def get_primary_cash_account(
        self, db: Session, user_id: int, currency: str = "USD"
    ) -> CashAccount:
        """Get the primary cash account for a user and currency."""
        account = (
            db.query(CashAccount)
            .filter(
                CashAccount.user_id == user_id,
                CashAccount.currency == currency,
                CashAccount.is_primary.is_(True),
            )
            .first()
        )

        if not account:
            # Create default cash account if none exists
            account = self.create_cash_account(
                db,
                user_id,
                CashAccountCreate(
                    currency=currency,
                    account_name=f"Main {currency} Account",
                    balance=Decimal("0"),
                    is_primary=True,
                ),
            )

        return account

    def create_cash_account(
        self, db: Session, user_id: int, account_data: CashAccountCreate
    ) -> CashAccount:
        """Create a new cash account."""
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=404, detail=f"User with ID {user_id} not found"
            )

        # If this is set as primary, unset other primary accounts for this currency
        if account_data.is_primary:
            db.query(CashAccount).filter(
                CashAccount.user_id == user_id,
                CashAccount.currency == account_data.currency,
                CashAccount.is_primary.is_(True),
            ).update({"is_primary": False})

        account = CashAccount(
            user_id=user_id,
            currency=account_data.currency,
            balance=account_data.balance,
            account_name=account_data.account_name,
            is_primary=account_data.is_primary,
        )

        db.add(account)
        db.commit()
        db.refresh(account)

        return account

    def get_cash_balance(
        self, db: Session, user_id: int, currency: str = "USD"
    ) -> Decimal:
        """Get total cash balance for a user in a specific currency."""
        total = (
            db.query(CashAccount)
            .filter(CashAccount.user_id == user_id, CashAccount.currency == currency)
            .with_entities(CashAccount.balance)
            .all()
        )

        return sum(balance[0] for balance in total) if total else Decimal("0")

    def process_cash_transaction(
        self, db: Session, user_id: int, transaction_data: CashTransactionCreate
    ) -> CashAccount:
        """Process a cash deposit or withdrawal."""
        # Get the cash account
        account = (
            db.query(CashAccount)
            .filter(
                CashAccount.id == transaction_data.account_id,
                CashAccount.user_id == user_id,
            )
            .first()
        )

        if not account:
            raise HTTPException(
                status_code=404,
                detail=f"Cash account with ID {transaction_data.account_id} not found",
            )

        # Check for sufficient funds on withdrawal
        if (
            transaction_data.amount < 0
            and account.balance + transaction_data.amount < 0
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient funds. Current balance: {account.balance}, "
                f"withdrawal amount: {abs(transaction_data.amount)}",
            )

        # Update balance
        account.balance += transaction_data.amount

        db.commit()
        db.refresh(account)

        return account

    def transfer_between_accounts(
        self,
        db: Session,
        user_id: int,
        from_account_id: int,
        to_account_id: int,
        amount: Decimal,
        description: str | None = None,
    ) -> tuple[CashAccount, CashAccount]:
        """Transfer money between cash accounts."""
        if amount <= 0:
            raise HTTPException(
                status_code=400, detail="Transfer amount must be positive"
            )

        # Get both accounts
        from_account = (
            db.query(CashAccount)
            .filter(CashAccount.id == from_account_id, CashAccount.user_id == user_id)
            .first()
        )
        to_account = (
            db.query(CashAccount)
            .filter(CashAccount.id == to_account_id, CashAccount.user_id == user_id)
            .first()
        )

        if not from_account:
            raise HTTPException(
                status_code=404, detail=f"Source account {from_account_id} not found"
            )
        if not to_account:
            raise HTTPException(
                status_code=404,
                detail=f"Destination account {to_account_id} not found",
            )

        # Check sufficient funds
        if from_account.balance < amount:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient funds in source account. "
                f"Available: {from_account.balance}, requested: {amount}",
            )

        # Process transfer
        from_account.balance -= amount
        to_account.balance += amount

        db.commit()
        db.refresh(from_account)
        db.refresh(to_account)

        return from_account, to_account

    def delete_cash_account(self, db: Session, user_id: int, account_id: int) -> None:
        """Delete a cash account (only if balance is zero)."""
        account = (
            db.query(CashAccount)
            .filter(CashAccount.id == account_id, CashAccount.user_id == user_id)
            .first()
        )

        if not account:
            raise HTTPException(
                status_code=404, detail=f"Cash account {account_id} not found"
            )

        if account.balance != 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete account with non-zero balance: {account.balance}",
            )

        db.delete(account)
        db.commit()

    def set_primary_account(
        self, db: Session, user_id: int, account_id: int
    ) -> CashAccount:
        """Set a cash account as primary for its currency."""
        account = (
            db.query(CashAccount)
            .filter(CashAccount.id == account_id, CashAccount.user_id == user_id)
            .first()
        )

        if not account:
            raise HTTPException(
                status_code=404, detail=f"Cash account {account_id} not found"
            )

        # Unset other primary accounts for this currency
        db.query(CashAccount).filter(
            CashAccount.user_id == user_id,
            CashAccount.currency == account.currency,
            CashAccount.is_primary.is_(True),
        ).update({"is_primary": False})

        # Set this account as primary
        account.is_primary = True

        db.commit()
        db.refresh(account)

        return account
