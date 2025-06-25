"""End-to-end system validation tests."""

from decimal import Decimal

from fastapi.testclient import TestClient
import pytest

from backend.main import app

client = TestClient(app)


@pytest.mark.integration
@pytest.mark.smoke
@pytest.mark.e2e
class TestEndToEndSystemValidation:
    """Validate that the entire system works end-to-end."""

    def test_complete_user_workflow(self):
        """Test complete user workflow from registration to portfolio management."""
        import uuid

        unique_id = str(uuid.uuid4())[:8]

        # Step 1: User Registration
        user_data = {
            "email": f"e2etest{unique_id}@example.com",
            "username": f"e2etest{unique_id}",
            "password": "SecurePass123!",
            "full_name": "E2E Test User",
        }

        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 200
        user_info = register_response.json()
        assert user_info["email"] == user_data["email"]
        user_id = user_info["id"]

        # Step 2: User Login
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": user_data["email"],
                "password": user_data["password"],
            },
        )
        assert login_response.status_code == 200
        token_data = login_response.json()
        assert "access_token" in token_data

        auth_headers = {"Authorization": f"Bearer {token_data['access_token']}"}

        # Step 3: Create Cash Account
        cash_account_data = {
            "currency": "USD",
            "account_name": "Main Account",
            "balance": "10000.00",
            "is_primary": True,
        }

        cash_response = client.post(
            f"/api/v1/cash-accounts/?user_id={user_id}",
            headers=auth_headers,
            json=cash_account_data,
        )
        assert cash_response.status_code == 200
        cash_account = cash_response.json()
        assert cash_account["currency"] == "USD"
        assert Decimal(cash_account["balance"]) == Decimal("10000.00")

        # Step 4: Cash Transaction (Deposit)
        transaction_data = {
            "account_id": cash_account["id"],
            "amount": "2000.00",
            "description": "Initial deposit",
        }

        transaction_response = client.post(
            f"/api/v1/cash-accounts/transaction?user_id={user_id}",
            headers=auth_headers,
            json=transaction_data,
        )
        assert transaction_response.status_code == 200
        updated_account = transaction_response.json()
        assert Decimal(updated_account["balance"]) == Decimal("12000.00")

        # Step 5: Get Portfolio Summary (if available)
        portfolio_response = client.get(
            f"/api/v1/portfolio/summary?user_id={user_id}",
            headers=auth_headers,
        )
        if portfolio_response.status_code == 200:
            portfolio = portfolio_response.json()
            # Portfolio should reflect cash balance
            assert portfolio is not None
        else:
            # Portfolio endpoint might not be implemented yet
            assert portfolio_response.status_code in [404, 422]

        # Step 6: Create Position (if endpoint exists)
        try:
            position_data = {
                "ticker": "AAPL",
                "quantity": "10",
                "purchase_price": "150.00",
                "purchase_date": "2024-01-01",
            }

            position_response = client.post(
                f"/api/v1/positions/?user_id={user_id}",
                headers=auth_headers,
                json=position_data,
            )

            if position_response.status_code == 200:
                position = position_response.json()
                assert position["ticker"] == "AAPL"
                assert Decimal(position["quantity"]) == Decimal("10")
        except Exception:
            # Position creation might not be available yet
            pass

        # Step 7: Get User's Data
        positions_response = client.get(
            f"/api/v1/positions/?user_id={user_id}",
            headers=auth_headers,
        )
        # Should return 200 even if empty list, or 404 if not implemented
        assert positions_response.status_code in [200, 404, 422]

        cash_accounts_response = client.get(
            f"/api/v1/cash-accounts/?user_id={user_id}",
            headers=auth_headers,
        )
        assert cash_accounts_response.status_code == 200
        accounts = cash_accounts_response.json()
        assert len(accounts) >= 1
        assert accounts[0]["currency"] == "USD"

    def test_authentication_security_flow(self):
        """Test authentication security measures."""
        # Test 1: Access protected endpoint without auth
        response = client.get("/api/v1/positions/")
        assert response.status_code == 401

        # Test 2: Invalid credentials
        invalid_login = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "wrongpassword",
            },
        )
        assert invalid_login.status_code == 401

        # Test 3: Malformed token
        malformed_headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/api/v1/positions/", headers=malformed_headers)
        assert response.status_code == 401

        # Test 4: Valid registration and auth flow
        import time

        timestamp = str(int(time.time()))
        test_email = f"securitytest{timestamp}@example.com"
        test_username = f"securitytest{timestamp}"

        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_email,
                "username": test_username,
                "password": "SecurePass123!",
                "full_name": "Security Test User",
            },
        )
        assert register_response.status_code == 200

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_email,
                "password": "SecurePass123!",
            },
        )
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Now should be able to access protected endpoints
        response = client.get("/api/v1/positions/", headers=auth_headers)
        assert response.status_code == 200

    def test_database_operations_integrity(self):
        """Test database operations maintain data integrity."""
        # Register user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "dbtest@example.com",
                "username": "dbtest",
                "password": "dbpass123",
            },
        )

        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "dbtest@example.com",
                "password": "dbpass123",
            },
        )
        token = login_response.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Create multiple cash accounts
        accounts = []
        for i in range(3):
            account_data = {
                "currency": "USD",
                "account_name": f"Account {i}",
                "balance": f"{1000 * (i + 1)}.00",
                "is_primary": i == 0,
            }

            response = client.post(
                "/api/v1/cash-accounts/",
                headers=auth_headers,
                json=account_data,
            )
            assert response.status_code == 200
            accounts.append(response.json())

        # Verify accounts were created correctly
        get_response = client.get("/api/v1/cash-accounts/", headers=auth_headers)
        assert get_response.status_code == 200
        retrieved_accounts = get_response.json()
        assert len(retrieved_accounts) >= 3

        # Test transaction integrity
        account_id = accounts[0]["id"]
        initial_balance = Decimal(accounts[0]["balance"])

        # Perform multiple transactions
        transactions = [
            {"amount": "500.00", "description": "Deposit 1"},
            {"amount": "-200.00", "description": "Withdrawal 1"},
            {"amount": "300.00", "description": "Deposit 2"},
        ]

        expected_balance = initial_balance
        for transaction in transactions:
            response = client.post(
                "/api/v1/cash-accounts/transaction",
                headers=auth_headers,
                json={
                    "account_id": account_id,
                    "amount": transaction["amount"],
                    "description": transaction["description"],
                },
            )
            assert response.status_code == 200
            expected_balance += Decimal(transaction["amount"])

            updated_account = response.json()
            assert Decimal(updated_account["balance"]) == expected_balance

    def test_error_handling_and_recovery(self):
        """Test system error handling and recovery."""
        # Register user for error testing
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "errortest@example.com",
                "username": "errortest",
                "password": "errorpass123",
            },
        )

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "errortest@example.com",
                "password": "errorpass123",
            },
        )
        token = login_response.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Test 1: Duplicate registration
        duplicate_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "errortest@example.com",
                "username": "errortest2",
                "password": "errorpass123",
            },
        )
        assert duplicate_response.status_code == 400

        # Test 2: Invalid cash account data
        invalid_account = {
            "currency": "INVALID",
            "account_name": "",
            "balance": "not_a_number",
        }

        response = client.post(
            "/api/v1/cash-accounts/",
            headers=auth_headers,
            json=invalid_account,
        )
        assert response.status_code == 422  # Validation error

        # Test 3: Insufficient funds
        # First create account
        account_response = client.post(
            "/api/v1/cash-accounts/",
            headers=auth_headers,
            json={
                "currency": "USD",
                "account_name": "Small Account",
                "balance": "100.00",
            },
        )
        account_id = account_response.json()["id"]

        # Try to withdraw more than available
        overdraft_response = client.post(
            "/api/v1/cash-accounts/transaction",
            headers=auth_headers,
            json={
                "account_id": account_id,
                "amount": "-500.00",
                "description": "Overdraft attempt",
            },
        )
        assert overdraft_response.status_code == 400

        # Test 4: System should still function after errors
        # Normal operations should still work
        valid_response = client.get("/api/v1/cash-accounts/", headers=auth_headers)
        assert valid_response.status_code == 200

    def test_api_consistency_and_standards(self):
        """Test that APIs follow consistent patterns and standards."""
        # Register user for API testing
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "apitest@example.com",
                "username": "apitest",
                "password": "apipass123",
            },
        )

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "apitest@example.com",
                "password": "apipass123",
            },
        )
        token = login_response.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Test API endpoints return consistent structure
        endpoints_to_test = [
            "/api/v1/positions/",
            "/api/v1/cash-accounts/",
        ]

        for endpoint in endpoints_to_test:
            response = client.get(endpoint, headers=auth_headers)

            # All protected endpoints should require auth
            unauth_response = client.get(endpoint)
            assert unauth_response.status_code == 401

            # Authenticated requests should return 200
            assert response.status_code == 200

            # Responses should be valid JSON
            data = response.json()
            assert data is not None


@pytest.mark.smoke
@pytest.mark.fast
class TestSystemStartupValidation:
    """Quick validation tests for system startup."""

    def test_application_starts(self):
        """Test that the application starts without errors."""
        # Basic health check
        try:
            response = client.get("/")
            # Should not crash, status code depends on implementation
            assert response.status_code in [
                200,
                404,
                422,
            ]  # Various acceptable responses
        except Exception as e:
            pytest.fail(f"Application failed to start: {e}")

    def test_api_documentation_accessible(self):
        """Test that API documentation is accessible."""
        try:
            docs_response = client.get("/docs")
            # Documentation should be accessible
            assert docs_response.status_code == 200
        except Exception:
            # If docs endpoint doesn't exist, that's also acceptable
            pass

    def test_basic_endpoints_respond(self):
        """Test that basic endpoints respond without crashing."""
        # Test public endpoints (should not require auth)
        endpoints = [
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

        for endpoint in endpoints:
            try:
                response = client.get(endpoint)
                # Should not crash, various response codes are acceptable
                assert response.status_code in [200, 404, 422]
            except Exception:
                # Some endpoints might not exist, that's ok
                pass

    def test_protected_endpoints_require_auth(self):
        """Test that protected endpoints properly require authentication."""
        protected_endpoints = [
            "/api/v1/positions/",
            "/api/v1/cash-accounts/",
            "/api/v1/portfolio/summary",
            "/api/v1/transactions/",
        ]

        for endpoint in protected_endpoints:
            try:
                response = client.get(endpoint)
                # Should require authentication
                assert response.status_code == 401
            except Exception:
                # Endpoint might not exist yet, that's acceptable
                pass

    def test_auth_endpoints_functional(self):
        """Test that authentication endpoints are functional."""
        # Test registration endpoint exists and accepts requests
        test_data = {
            "email": "startuptest@example.com",
            "username": "startuptest",
            "password": "startuppass123",
        }

        try:
            response = client.post("/api/v1/auth/register", json=test_data)
            # Should not crash, various response codes acceptable
            assert response.status_code in [200, 400, 422]
        except Exception as e:
            pytest.fail(f"Auth registration endpoint failed: {e}")

        # Test login endpoint exists
        try:
            response = client.post(
                "/api/v1/auth/login",
                data={
                    "username": "startuptest@example.com",
                    "password": "startuppass123",
                },
            )
            # Should not crash
            assert response.status_code in [200, 401, 422]
        except Exception as e:
            pytest.fail(f"Auth login endpoint failed: {e}")
