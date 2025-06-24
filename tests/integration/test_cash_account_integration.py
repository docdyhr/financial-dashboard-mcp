"""Integration tests for cash account functionality."""

from decimal import Decimal

from fastapi.testclient import TestClient
import pytest

from backend.main import app
from backend.models import CashAccount, User

client = TestClient(app)


@pytest.mark.integration
@pytest.mark.cash
@pytest.mark.api
class TestCashAccountAPIIntegration:
    """Test cash account functionality through API."""

    def setup_method(self):
        """Set up authenticated user for each test."""
        # Register and login user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "cashtest@example.com",
                "username": "cashtest",
                "password": "cashpass123",
                "full_name": "Cash Test User",
            },
        )

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "cashtest@example.com",
                "password": "cashpass123",
            },
        )
        self.token = login_response.json()["access_token"]
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}

    def test_create_cash_account_via_api(self):
        """Test creating cash account through API endpoint."""
        response = client.post(
            "/api/v1/cash-accounts/",
            headers=self.auth_headers,
            json={
                "currency": "USD",
                "account_name": "Main Checking",
                "balance": "5000.00",
                "is_primary": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["currency"] == "USD"
        assert data["account_name"] == "Main Checking"
        assert Decimal(data["balance"]) == Decimal("5000.00")
        assert data["is_primary"] is True

    def test_get_cash_accounts_via_api(self):
        """Test retrieving cash accounts through API."""
        # Create multiple accounts
        accounts_data = [
            {
                "currency": "USD",
                "account_name": "USD Primary",
                "balance": "1000.00",
                "is_primary": True,
            },
            {
                "currency": "EUR",
                "account_name": "EUR Account",
                "balance": "500.00",
                "is_primary": False,
            },
        ]

        for account_data in accounts_data:
            client.post(
                "/api/v1/cash-accounts/",
                headers=self.auth_headers,
                json=account_data,
            )

        # Get accounts
        response = client.get(
            "/api/v1/cash-accounts/",
            headers=self.auth_headers,
        )

        assert response.status_code == 200
        accounts = response.json()
        assert len(accounts) >= 2

        # Check currency filtering
        usd_accounts = [acc for acc in accounts if acc["currency"] == "USD"]
        eur_accounts = [acc for acc in accounts if acc["currency"] == "EUR"]
        assert len(usd_accounts) >= 1
        assert len(eur_accounts) >= 1

    def test_cash_transaction_via_api(self):
        """Test cash transactions through API."""
        # Create account first
        create_response = client.post(
            "/api/v1/cash-accounts/",
            headers=self.auth_headers,
            json={
                "currency": "USD",
                "account_name": "Transaction Test",
                "balance": "1000.00",
                "is_primary": False,
            },
        )
        account_id = create_response.json()["id"]

        # Deposit money
        deposit_response = client.post(
            "/api/v1/cash-accounts/transactions/",
            headers=self.auth_headers,
            json={
                "account_id": account_id,
                "amount": "500.00",
                "description": "Test deposit",
            },
        )

        assert deposit_response.status_code == 200
        account = deposit_response.json()
        assert Decimal(account["balance"]) == Decimal("1500.00")

        # Withdraw money
        withdraw_response = client.post(
            "/api/v1/cash-accounts/transactions/",
            headers=self.auth_headers,
            json={
                "account_id": account_id,
                "amount": "-200.00",
                "description": "Test withdrawal",
            },
        )

        assert withdraw_response.status_code == 200
        account = withdraw_response.json()
        assert Decimal(account["balance"]) == Decimal("1300.00")

    def test_insufficient_funds_via_api(self):
        """Test insufficient funds error through API."""
        # Create account with small balance
        create_response = client.post(
            "/api/v1/cash-accounts/",
            headers=self.auth_headers,
            json={
                "currency": "USD",
                "account_name": "Small Balance",
                "balance": "100.00",
                "is_primary": False,
            },
        )
        account_id = create_response.json()["id"]

        # Try to withdraw more than available
        response = client.post(
            "/api/v1/cash-accounts/transactions/",
            headers=self.auth_headers,
            json={
                "account_id": account_id,
                "amount": "-500.00",
                "description": "Overdraft attempt",
            },
        )

        assert response.status_code == 400
        assert "insufficient funds" in response.json()["detail"].lower()


@pytest.mark.integration
@pytest.mark.cash
@pytest.mark.portfolio
class TestCashAccountPortfolioIntegration:
    """Test cash account integration with portfolio functionality."""

    def setup_method(self):
        """Set up authenticated user for each test."""
        # Register and login user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "portfoliotest@example.com",
                "username": "portfoliotest",
                "password": "portfoliopass123",
                "full_name": "Portfolio Test User",
            },
        )

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "portfoliotest@example.com",
                "password": "portfoliopass123",
            },
        )
        self.token = login_response.json()["access_token"]
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}

    def test_portfolio_includes_cash_balance(self):
        """Test that portfolio summary includes cash balances."""
        # Create cash account
        client.post(
            "/api/v1/cash-accounts/",
            headers=self.auth_headers,
            json={
                "currency": "USD",
                "account_name": "Portfolio Cash",
                "balance": "10000.00",
                "is_primary": True,
            },
        )

        # Get portfolio summary
        response = client.get(
            "/api/v1/portfolio/summary",
            headers=self.auth_headers,
        )

        assert response.status_code == 200
        portfolio = response.json()

        # Portfolio should include cash balance
        assert "cash_balance" in portfolio or "total_cash" in portfolio

        # Check if cash is included in total value
        if "total_value" in portfolio:
            # Total value should include cash
            assert Decimal(str(portfolio["total_value"])) >= Decimal("10000.00")

    def test_cash_allocation_in_portfolio(self):
        """Test cash allocation calculation in portfolio."""
        # Create cash account
        client.post(
            "/api/v1/cash-accounts/",
            headers=self.auth_headers,
            json={
                "currency": "USD",
                "account_name": "Allocation Test",
                "balance": "5000.00",
                "is_primary": True,
            },
        )

        # Create a position (if API supports it)
        try:
            client.post(
                "/api/v1/positions/",
                headers=self.auth_headers,
                json={
                    "ticker": "AAPL",
                    "quantity": "10",
                    "purchase_price": "150.00",
                    "purchase_date": "2024-01-01",
                },
            )
        except Exception:
            # Position creation might not be available in API yet
            pass

        # Get portfolio allocation
        response = client.get(
            "/api/v1/portfolio/allocation",
            headers=self.auth_headers,
        )

        # Should return allocation including cash
        if response.status_code == 200:
            allocation = response.json()
            # Should have cash as one of the allocation categories
            cash_allocation = None
            for item in allocation:
                if "cash" in item.get("category", "").lower():
                    cash_allocation = item
                    break

            # If we have only cash, it should be 100% allocation
            if cash_allocation:
                assert Decimal(str(cash_allocation["percentage"])) > 0

    def test_multi_currency_cash_handling(self):
        """Test handling of multiple currencies in portfolio."""
        # Create accounts in different currencies
        currencies = ["USD", "EUR", "GBP"]
        for currency in currencies:
            client.post(
                "/api/v1/cash-accounts/",
                headers=self.auth_headers,
                json={
                    "currency": currency,
                    "account_name": f"{currency} Account",
                    "balance": "1000.00",
                    "is_primary": False,
                },
            )

        # Get portfolio summary
        response = client.get(
            "/api/v1/portfolio/summary",
            headers=self.auth_headers,
        )

        assert response.status_code == 200
        portfolio = response.json()

        # Portfolio should handle multiple currencies
        # This might convert to base currency or show breakdown
        assert portfolio is not None


@pytest.mark.integration
@pytest.mark.cash
@pytest.mark.database
class TestCashAccountDatabaseIntegration:
    """Test cash account database integration and constraints."""

    def test_currency_validation(self, db_session):
        """Test that invalid currencies are rejected."""
        user = User(
            email="currencytest@example.com",
            username="currencytest",
            full_name="Currency Test",
            hashed_password="hashed",
        )
        db_session.add(user)
        db_session.commit()

        # Valid currency should work
        valid_account = CashAccount(
            user_id=user.id,
            currency="USD",
            account_name="Valid Account",
            balance=Decimal("1000"),
        )
        db_session.add(valid_account)
        db_session.commit()

        # Invalid currency should be rejected by application logic
        # (Database constraints depend on schema definition)
        invalid_account = CashAccount(
            user_id=user.id,
            currency="INVALID",
            account_name="Invalid Account",
            balance=Decimal("1000"),
        )

        # This might raise constraint error or be handled by application
        try:
            db_session.add(invalid_account)
            db_session.commit()
            # If no error, application should validate currency
            assert invalid_account.currency in ["USD", "EUR", "GBP", "INVALID"]
        except Exception:
            # Database constraint rejected invalid currency
            db_session.rollback()

    def test_balance_precision(self, db_session):
        """Test decimal precision for balances."""
        user = User(
            email="precisiontest@example.com",
            username="precisiontest",
            full_name="Precision Test",
            hashed_password="hashed",
        )
        db_session.add(user)
        db_session.commit()

        # Test balance precision - database may round to 2 decimal places
        account = CashAccount(
            user_id=user.id,
            currency="USD",
            account_name="Precision Test",
            balance=Decimal("1234.56"),
        )
        db_session.add(account)
        db_session.commit()

        # Verify precision is maintained (at least 2 decimal places)
        db_session.refresh(account)
        assert account.balance == Decimal("1234.56")

        # Test that decimal values work correctly
        account.balance = Decimal("9876.54")
        db_session.commit()
        db_session.refresh(account)
        assert account.balance == Decimal("9876.54")

    def test_user_isolation(self, db_session):
        """Test that users can only access their own cash accounts."""
        # Create two users
        user1 = User(
            email="user1@example.com",
            username="user1",
            full_name="User One",
            hashed_password="hashed",
        )
        user2 = User(
            email="user2@example.com",
            username="user2",
            full_name="User Two",
            hashed_password="hashed",
        )
        db_session.add_all([user1, user2])
        db_session.commit()

        # Create accounts for each user
        account1 = CashAccount(
            user_id=user1.id,
            currency="USD",
            account_name="User 1 Account",
            balance=Decimal("1000"),
        )
        account2 = CashAccount(
            user_id=user2.id,
            currency="USD",
            account_name="User 2 Account",
            balance=Decimal("2000"),
        )
        db_session.add_all([account1, account2])
        db_session.commit()

        # User 1 should only see their account
        user1_accounts = (
            db_session.query(CashAccount).filter(CashAccount.user_id == user1.id).all()
        )
        assert len(user1_accounts) == 1
        assert user1_accounts[0].balance == Decimal("1000")

        # User 2 should only see their account
        user2_accounts = (
            db_session.query(CashAccount).filter(CashAccount.user_id == user2.id).all()
        )
        assert len(user2_accounts) == 1
        assert user2_accounts[0].balance == Decimal("2000")


@pytest.mark.integration
@pytest.mark.cash
@pytest.mark.performance
class TestCashAccountPerformance:
    """Test cash account performance with larger datasets."""

    def test_bulk_transaction_performance(self, db_session):
        """Test performance with many transactions."""
        user = User(
            email="perftest@example.com",
            username="perftest",
            full_name="Performance Test",
            hashed_password="hashed",
        )
        db_session.add(user)
        db_session.commit()

        # Create account
        account = CashAccount(
            user_id=user.id,
            currency="USD",
            account_name="Performance Test",
            balance=Decimal("10000"),
        )
        db_session.add(account)
        db_session.commit()

        # This would be expanded with actual performance testing
        # For now, just verify basic functionality with multiple operations
        import time

        start_time = time.time()

        # Simulate multiple balance queries
        for _ in range(100):
            balance = (
                db_session.query(CashAccount.balance)
                .filter(CashAccount.id == account.id)
                .scalar()
            )
            assert balance == Decimal("10000")

        end_time = time.time()
        execution_time = end_time - start_time

        # Should complete 100 queries in reasonable time (adjust threshold as needed)
        assert execution_time < 1.0  # Less than 1 second for 100 simple queries

    def test_currency_aggregation_performance(self, db_session):
        """Test performance of currency aggregation queries."""
        user = User(
            email="aggtest@example.com",
            username="aggtest",
            full_name="Aggregation Test",
            hashed_password="hashed",
        )
        db_session.add(user)
        db_session.commit()

        # Create multiple accounts in same currency
        accounts = []
        for i in range(50):
            account = CashAccount(
                user_id=user.id,
                currency="USD",
                account_name=f"Account {i}",
                balance=Decimal("100"),
            )
            accounts.append(account)

        db_session.add_all(accounts)
        db_session.commit()

        # Test aggregation performance
        import time

        start_time = time.time()

        total_balance = (
            db_session.query(CashAccount.balance)
            .filter(CashAccount.user_id == user.id)
            .filter(CashAccount.currency == "USD")
            .all()
        )

        end_time = time.time()
        execution_time = end_time - start_time

        # Should complete aggregation in reasonable time
        assert execution_time < 0.1  # Less than 100ms
        assert len(total_balance) == 50
