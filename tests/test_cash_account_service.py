"""Tests for cash account service."""

from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.models import CashAccount, User
from backend.schemas.cash_account import CashAccountCreate, CashTransactionCreate
from backend.services.cash_account import CashAccountService


@pytest.fixture
def cash_service():
    """Create cash account service instance."""
    return CashAccountService()


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password="hashed_password_here",
    )
    db_session.add(user)
    db_session.commit()
    return user


class TestCashAccountService:
    """Test cash account service methods."""

    def test_create_cash_account(
        self,
        cash_service: CashAccountService,
        db_session: Session,
        test_user: User,
    ):
        """Test creating a cash account."""
        account_data = CashAccountCreate(
            currency="USD",
            account_name="Main USD Account",
            balance=Decimal("5000"),
            is_primary=True,
        )

        account = cash_service.create_cash_account(
            db_session, test_user.id, account_data
        )

        assert account.user_id == test_user.id
        assert account.currency == "USD"
        assert account.account_name == "Main USD Account"
        assert account.balance == Decimal("5000")
        assert account.is_primary is True

    def test_get_primary_cash_account_creates_default(
        self,
        cash_service: CashAccountService,
        db_session: Session,
        test_user: User,
    ):
        """Test getting primary cash account creates default if none exists."""
        account = cash_service.get_primary_cash_account(db_session, test_user.id, "USD")

        assert account.user_id == test_user.id
        assert account.currency == "USD"
        assert account.is_primary is True
        assert account.balance == Decimal("0")

    def test_get_primary_cash_account_existing(
        self,
        cash_service: CashAccountService,
        db_session: Session,
        test_user: User,
    ):
        """Test getting existing primary cash account."""
        # Create account
        existing_account = CashAccount(
            user_id=test_user.id,
            currency="USD",
            account_name="Existing Account",
            balance=Decimal("1000"),
            is_primary=True,
        )
        db_session.add(existing_account)
        db_session.commit()

        account = cash_service.get_primary_cash_account(db_session, test_user.id, "USD")

        assert account.id == existing_account.id
        assert account.balance == Decimal("1000")

    def test_get_cash_balance(
        self,
        cash_service: CashAccountService,
        db_session: Session,
        test_user: User,
    ):
        """Test getting total cash balance."""
        # Create multiple USD accounts
        accounts = [
            CashAccount(
                user_id=test_user.id,
                currency="USD",
                account_name="Account 1",
                balance=Decimal("1000"),
            ),
            CashAccount(
                user_id=test_user.id,
                currency="USD",
                account_name="Account 2",
                balance=Decimal("2500"),
            ),
            CashAccount(
                user_id=test_user.id,
                currency="EUR",
                account_name="EUR Account",
                balance=Decimal("500"),
            ),
        ]
        db_session.add_all(accounts)
        db_session.commit()

        # Test USD balance
        usd_balance = cash_service.get_cash_balance(db_session, test_user.id, "USD")
        assert usd_balance == Decimal("3500")

        # Test EUR balance
        eur_balance = cash_service.get_cash_balance(db_session, test_user.id, "EUR")
        assert eur_balance == Decimal("500")

        # Test non-existent currency
        gbp_balance = cash_service.get_cash_balance(db_session, test_user.id, "GBP")
        assert gbp_balance == Decimal("0")

    def test_process_cash_deposit(
        self,
        cash_service: CashAccountService,
        db_session: Session,
        test_user: User,
    ):
        """Test processing cash deposit."""
        # Create account
        account = CashAccount(
            user_id=test_user.id,
            currency="USD",
            account_name="Main Account",
            balance=Decimal("1000"),
        )
        db_session.add(account)
        db_session.commit()

        # Process deposit
        transaction_data = CashTransactionCreate(
            account_id=account.id,
            amount=Decimal("500"),
            description="Test deposit",
        )

        updated_account = cash_service.process_cash_transaction(
            db_session, test_user.id, transaction_data
        )

        assert updated_account.balance == Decimal("1500")

    def test_process_cash_withdrawal(
        self,
        cash_service: CashAccountService,
        db_session: Session,
        test_user: User,
    ):
        """Test processing cash withdrawal."""
        # Create account
        account = CashAccount(
            user_id=test_user.id,
            currency="USD",
            account_name="Main Account",
            balance=Decimal("1000"),
        )
        db_session.add(account)
        db_session.commit()

        # Process withdrawal
        transaction_data = CashTransactionCreate(
            account_id=account.id,
            amount=Decimal("-300"),
            description="Test withdrawal",
        )

        updated_account = cash_service.process_cash_transaction(
            db_session, test_user.id, transaction_data
        )

        assert updated_account.balance == Decimal("700")

    def test_process_cash_withdrawal_insufficient_funds(
        self,
        cash_service: CashAccountService,
        db_session: Session,
        test_user: User,
    ):
        """Test processing cash withdrawal with insufficient funds."""
        # Create account
        account = CashAccount(
            user_id=test_user.id,
            currency="USD",
            account_name="Main Account",
            balance=Decimal("100"),
        )
        db_session.add(account)
        db_session.commit()

        # Try to withdraw more than available
        transaction_data = CashTransactionCreate(
            account_id=account.id,
            amount=Decimal("-500"),
            description="Overdraft attempt",
        )

        with pytest.raises(HTTPException) as exc_info:
            cash_service.process_cash_transaction(
                db_session, test_user.id, transaction_data
            )
        assert "Insufficient funds" in str(exc_info.value.detail)

    def test_transfer_between_accounts(
        self,
        cash_service: CashAccountService,
        db_session: Session,
        test_user: User,
    ):
        """Test transferring money between accounts."""
        # Create two accounts
        from_account = CashAccount(
            user_id=test_user.id,
            currency="USD",
            account_name="From Account",
            balance=Decimal("1000"),
        )
        to_account = CashAccount(
            user_id=test_user.id,
            currency="USD",
            account_name="To Account",
            balance=Decimal("500"),
        )
        db_session.add_all([from_account, to_account])
        db_session.commit()

        # Transfer money
        updated_from, updated_to = cash_service.transfer_between_accounts(
            db_session,
            test_user.id,
            from_account.id,
            to_account.id,
            Decimal("300"),
            "Test transfer",
        )

        assert updated_from.balance == Decimal("700")
        assert updated_to.balance == Decimal("800")

    def test_transfer_insufficient_funds(
        self,
        cash_service: CashAccountService,
        db_session: Session,
        test_user: User,
    ):
        """Test transfer with insufficient funds."""
        # Create two accounts
        from_account = CashAccount(
            user_id=test_user.id,
            currency="USD",
            account_name="From Account",
            balance=Decimal("100"),
        )
        to_account = CashAccount(
            user_id=test_user.id,
            currency="USD",
            account_name="To Account",
            balance=Decimal("500"),
        )
        db_session.add_all([from_account, to_account])
        db_session.commit()

        # Try to transfer more than available
        with pytest.raises(HTTPException) as exc_info:
            cash_service.transfer_between_accounts(
                db_session,
                test_user.id,
                from_account.id,
                to_account.id,
                Decimal("500"),
            )
        assert "Insufficient funds" in str(exc_info.value.detail)

    def test_set_primary_account(
        self,
        cash_service: CashAccountService,
        db_session: Session,
        test_user: User,
    ):
        """Test setting an account as primary."""
        # Create two USD accounts
        account1 = CashAccount(
            user_id=test_user.id,
            currency="USD",
            account_name="Account 1",
            balance=Decimal("1000"),
            is_primary=True,
        )
        account2 = CashAccount(
            user_id=test_user.id,
            currency="USD",
            account_name="Account 2",
            balance=Decimal("500"),
            is_primary=False,
        )
        db_session.add_all([account1, account2])
        db_session.commit()

        # Set account2 as primary
        updated_account = cash_service.set_primary_account(
            db_session, test_user.id, account2.id
        )

        assert updated_account.is_primary is True

        # Refresh account1 to check it's no longer primary
        db_session.refresh(account1)
        assert account1.is_primary is False

    def test_delete_cash_account(
        self,
        cash_service: CashAccountService,
        db_session: Session,
        test_user: User,
    ):
        """Test deleting cash account with zero balance."""
        # Create account with zero balance
        account = CashAccount(
            user_id=test_user.id,
            currency="USD",
            account_name="Empty Account",
            balance=Decimal("0"),
        )
        db_session.add(account)
        db_session.commit()
        account_id = account.id

        # Delete account
        cash_service.delete_cash_account(db_session, test_user.id, account_id)

        # Verify it's deleted
        deleted_account = (
            db_session.query(CashAccount).filter(CashAccount.id == account_id).first()
        )
        assert deleted_account is None

    def test_delete_cash_account_non_zero_balance(
        self,
        cash_service: CashAccountService,
        db_session: Session,
        test_user: User,
    ):
        """Test deleting cash account with non-zero balance fails."""
        # Create account with balance
        account = CashAccount(
            user_id=test_user.id,
            currency="USD",
            account_name="Non-empty Account",
            balance=Decimal("100"),
        )
        db_session.add(account)
        db_session.commit()

        # Try to delete account
        with pytest.raises(HTTPException) as exc_info:
            cash_service.delete_cash_account(db_session, test_user.id, account.id)
        assert "non-zero balance" in str(exc_info.value.detail)

    def test_list_user_cash_accounts(
        self,
        cash_service: CashAccountService,
        db_session: Session,
        test_user: User,
    ):
        """Test listing user cash accounts."""
        # Create multiple accounts
        accounts = [
            CashAccount(
                user_id=test_user.id,
                currency="USD",
                account_name="USD Primary",
                balance=Decimal("1000"),
                is_primary=True,
            ),
            CashAccount(
                user_id=test_user.id,
                currency="USD",
                account_name="USD Secondary",
                balance=Decimal("500"),
                is_primary=False,
            ),
            CashAccount(
                user_id=test_user.id,
                currency="EUR",
                account_name="EUR Account",
                balance=Decimal("200"),
                is_primary=True,
            ),
        ]
        db_session.add_all(accounts)
        db_session.commit()

        # List accounts
        user_accounts = cash_service.get_user_cash_accounts(db_session, test_user.id)

        assert len(user_accounts) == 3
        # Should be ordered by is_primary desc, then currency
        assert user_accounts[0].is_primary is True
        assert user_accounts[1].is_primary is True
        assert user_accounts[2].is_primary is False
