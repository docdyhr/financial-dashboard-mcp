#!/usr/bin/env python3
"""Comprehensive production feature testing script.

This script tests all major features of the Financial Dashboard
to ensure production readiness.
"""

import json
import random
import time
from datetime import date, datetime

import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "username": "testuser@production.com",
    "password": "Test@Production123!",
}
ADMIN_USER = {
    "username": "admin@production.com",
    "password": "Admin@Production123!",
}

# Test data
TEST_ASSETS = [
    {"symbol": "AAPL", "name": "Apple Inc.", "type": "stock", "currency": "USD"},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "type": "stock", "currency": "USD"},
    {"symbol": "MSFT", "name": "Microsoft Corp.", "type": "stock", "currency": "USD"},
    {"symbol": "VOO", "name": "Vanguard S&P 500 ETF", "type": "etf", "currency": "USD"},
    {"symbol": "BTC-USD", "name": "Bitcoin", "type": "crypto", "currency": "USD"},
]


class ProductionTester:
    """Test suite for production validation."""

    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        self.test_results = []

    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result."""
        self.test_results.append(
            {
                "test": test_name,
                "success": success,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }
        )

        if success:
            console.print(f"✅ {test_name}", style="green")
        else:
            console.print(f"❌ {test_name}: {message}", style="red")

    def test_health_check(self):
        """Test API health endpoint."""
        try:
            response = self.session.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Health Check", True, f"API Version: {data.get('version')}"
                )
                return True
            self.log_test("Health Check", False, f"Status: {response.status_code}")
            return False
        except Exception as e:
            self.log_test("Health Check", False, str(e))
            return False

    def test_user_registration(self):
        """Test user registration."""
        try:
            # Try to register test user
            response = self.session.post(
                f"{BASE_URL}/api/v1/auth/register",
                json={
                    "username": TEST_USER["username"],
                    "email": TEST_USER["username"],
                    "password": TEST_USER["password"],
                    "full_name": "Test Production User",
                },
            )

            if response.status_code in [200, 201]:
                self.log_test("User Registration", True, "New user created")
                return True
            if response.status_code == 400:
                # User might already exist
                self.log_test("User Registration", True, "User already exists")
                return True
            self.log_test("User Registration", False, f"Status: {response.status_code}")
            return False
        except Exception as e:
            self.log_test("User Registration", False, str(e))
            return False

    def test_user_login(self):
        """Test user authentication."""
        try:
            response = self.session.post(
                f"{BASE_URL}/api/v1/auth/login",
                data={
                    "username": TEST_USER["username"],
                    "password": TEST_USER["password"],
                },
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})

                # Get user info
                user_response = self.session.get(f"{BASE_URL}/api/v1/auth/me")
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    self.user_id = user_data["id"]
                    self.log_test("User Login", True, f"User ID: {self.user_id}")
                    return True

            self.log_test("User Login", False, f"Status: {response.status_code}")
            return False
        except Exception as e:
            self.log_test("User Login", False, str(e))
            return False

    def test_portfolio_operations(self):
        """Test portfolio CRUD operations."""
        try:
            # Create assets if they don't exist
            created_assets = []
            for asset_data in TEST_ASSETS:
                response = self.session.post(
                    f"{BASE_URL}/api/v1/assets/", json=asset_data
                )
                if response.status_code in [200, 201]:
                    created_assets.append(response.json()["data"])
                elif response.status_code == 400:
                    # Asset might already exist, try to get it
                    search_response = self.session.get(
                        f"{BASE_URL}/api/v1/assets/search",
                        params={"symbol": asset_data["symbol"]},
                    )
                    if search_response.status_code == 200:
                        assets = search_response.json()["data"]
                        if assets:
                            created_assets.append(assets[0])

            if not created_assets:
                self.log_test("Portfolio Operations", False, "Failed to create assets")
                return False

            # Create positions
            positions_created = 0
            for asset in created_assets[:3]:  # Create 3 positions
                position_data = {
                    "asset_id": asset["id"],
                    "quantity": random.uniform(10, 100),
                    "average_cost": random.uniform(50, 500),
                    "account_name": "Main Portfolio",
                }

                response = self.session.post(
                    f"{BASE_URL}/api/v1/positions/", json=position_data
                )

                if response.status_code in [200, 201]:
                    positions_created += 1

            # Get portfolio overview
            portfolio_response = self.session.get(
                f"{BASE_URL}/api/v1/portfolio/overview",
                params={"user_id": self.user_id},
            )

            if portfolio_response.status_code == 200:
                portfolio_data = portfolio_response.json()["data"]
                self.log_test(
                    "Portfolio Operations",
                    True,
                    f"Created {positions_created} positions, Total value: ${portfolio_data.get('total_value', 0):,.2f}",
                )
                return True
            self.log_test(
                "Portfolio Operations", False, "Failed to get portfolio overview"
            )
            return False

        except Exception as e:
            self.log_test("Portfolio Operations", False, str(e))
            return False

    def test_transaction_management(self):
        """Test transaction creation and retrieval."""
        try:
            # Get first position
            positions_response = self.session.get(
                f"{BASE_URL}/api/v1/positions/", params={"user_id": self.user_id}
            )

            if positions_response.status_code != 200:
                self.log_test("Transaction Management", False, "No positions found")
                return False

            positions = positions_response.json()["data"]
            if not positions:
                self.log_test("Transaction Management", False, "No positions available")
                return False

            position = positions[0]

            # Create a buy transaction
            buy_data = {
                "asset_id": position["asset"]["id"],
                "quantity": 10,
                "price": 150.00,
                "transaction_date": date.today().isoformat(),
                "account_name": "Main Portfolio",
                "fees": 1.00,
                "notes": "Production test transaction",
            }

            buy_response = self.session.post(
                f"{BASE_URL}/api/v1/transactions/buy",
                params={"user_id": self.user_id},
                json=buy_data,
            )

            if buy_response.status_code not in [200, 201]:
                self.log_test(
                    "Transaction Management",
                    False,
                    f"Buy failed: {buy_response.status_code}",
                )
                return False

            # Create a sell transaction
            sell_data = {
                "position_id": position["id"],
                "quantity": 5,
                "price": 160.00,
                "transaction_date": date.today().isoformat(),
                "fees": 1.00,
                "notes": "Production test sell",
            }

            sell_response = self.session.post(
                f"{BASE_URL}/api/v1/transactions/sell",
                params={"user_id": self.user_id},
                json=sell_data,
            )

            # Get transaction history
            transactions_response = self.session.get(
                f"{BASE_URL}/api/v1/transactions/", params={"user_id": self.user_id}
            )

            if transactions_response.status_code == 200:
                transactions = transactions_response.json()["data"]
                self.log_test(
                    "Transaction Management",
                    True,
                    f"Created transactions, Total: {len(transactions)}",
                )
                return True

            self.log_test(
                "Transaction Management", False, "Failed to retrieve transactions"
            )
            return False

        except Exception as e:
            self.log_test("Transaction Management", False, str(e))
            return False

    def test_market_data_integration(self):
        """Test market data fetching."""
        try:
            # Test single quote
            response = self.session.get(f"{BASE_URL}/api/v1/market-data/quote/AAPL")

            if response.status_code == 200:
                quote_data = response.json()["data"]
                self.log_test(
                    "Market Data - Single Quote",
                    True,
                    f"AAPL: ${quote_data.get('price', 0):.2f}",
                )
            else:
                self.log_test(
                    "Market Data - Single Quote",
                    False,
                    f"Status: {response.status_code}",
                )

            # Test batch quotes
            symbols = ["AAPL", "GOOGL", "MSFT"]
            batch_response = self.session.post(
                f"{BASE_URL}/api/v1/market-data/quotes/batch", json={"symbols": symbols}
            )

            if batch_response.status_code == 200:
                batch_data = batch_response.json()["data"]
                self.log_test(
                    "Market Data - Batch Quotes",
                    True,
                    f"Retrieved {len(batch_data)} quotes",
                )
                return True
            self.log_test(
                "Market Data - Batch Quotes",
                False,
                f"Status: {batch_response.status_code}",
            )
            return False

        except Exception as e:
            self.log_test("Market Data Integration", False, str(e))
            return False

    def test_performance_analytics(self):
        """Test portfolio performance calculations."""
        try:
            # Get performance metrics
            response = self.session.get(
                f"{BASE_URL}/api/v1/portfolio/performance",
                params={"user_id": self.user_id},
            )

            if response.status_code == 200:
                performance_data = response.json()["data"]
                self.log_test(
                    "Performance Analytics",
                    True,
                    f"Total return: {performance_data.get('total_return_percentage', 0):.2f}%",
                )
                return True
            self.log_test(
                "Performance Analytics", False, f"Status: {response.status_code}"
            )
            return False

        except Exception as e:
            self.log_test("Performance Analytics", False, str(e))
            return False

    def test_data_export(self):
        """Test data export functionality."""
        try:
            # Export portfolio data
            export_response = self.session.post(
                f"{BASE_URL}/api/v1/portfolio/export",
                params={"user_id": self.user_id},
                json={"format": "csv"},
            )

            if export_response.status_code == 200:
                self.log_test(
                    "Data Export - CSV", True, "Portfolio exported successfully"
                )
            else:
                self.log_test(
                    "Data Export - CSV", False, f"Status: {export_response.status_code}"
                )

            # Export as JSON
            json_export_response = self.session.post(
                f"{BASE_URL}/api/v1/portfolio/export",
                params={"user_id": self.user_id},
                json={"format": "json"},
            )

            if json_export_response.status_code == 200:
                self.log_test("Data Export - JSON", True, "JSON export successful")
                return True
            self.log_test(
                "Data Export - JSON",
                False,
                f"Status: {json_export_response.status_code}",
            )
            return False

        except Exception as e:
            self.log_test("Data Export", False, str(e))
            return False

    def test_security_features(self):
        """Test security features."""
        try:
            # Test unauthorized access
            unauthorized_session = requests.Session()
            response = unauthorized_session.get(f"{BASE_URL}/api/v1/positions/")

            if response.status_code == 401:
                self.log_test(
                    "Security - Unauthorized Access", True, "Properly rejected"
                )
            else:
                self.log_test(
                    "Security - Unauthorized Access", False, "Should return 401"
                )

            # Test token refresh
            refresh_response = self.session.post(
                f"{BASE_URL}/api/v1/auth/refresh",
                headers={"Authorization": f"Bearer {self.token}"},
            )

            if refresh_response.status_code == 200:
                self.log_test("Security - Token Refresh", True, "Token refreshed")
                return True
            self.log_test(
                "Security - Token Refresh",
                False,
                f"Status: {refresh_response.status_code}",
            )
            return False

        except Exception as e:
            self.log_test("Security Features", False, str(e))
            return False

    def test_celery_tasks(self):
        """Test background task execution."""
        try:
            # Trigger portfolio update task
            response = self.session.post(
                f"{BASE_URL}/api/v1/tasks/update-portfolio-prices",
                params={"user_id": self.user_id},
            )

            if response.status_code == 200:
                task_data = response.json()["data"]
                task_id = task_data.get("task_id")

                # Wait for task completion
                time.sleep(2)

                # Check task status
                status_response = self.session.get(
                    f"{BASE_URL}/api/v1/tasks/status/{task_id}"
                )

                if status_response.status_code == 200:
                    status_data = status_response.json()["data"]
                    self.log_test(
                        "Celery Tasks",
                        True,
                        f"Task status: {status_data.get('status', 'unknown')}",
                    )
                    return True

            self.log_test("Celery Tasks", False, "Failed to execute background task")
            return False

        except Exception as e:
            self.log_test("Celery Tasks", False, str(e))
            return False

    def run_all_tests(self):
        """Run all production tests."""
        console.print("\n🚀 Starting Production Feature Tests\n", style="bold blue")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            # Define test sequence
            tests = [
                ("Health Check", self.test_health_check),
                ("User Registration", self.test_user_registration),
                ("User Authentication", self.test_user_login),
                ("Portfolio Operations", self.test_portfolio_operations),
                ("Transaction Management", self.test_transaction_management),
                ("Market Data Integration", self.test_market_data_integration),
                ("Performance Analytics", self.test_performance_analytics),
                ("Data Export", self.test_data_export),
                ("Security Features", self.test_security_features),
                ("Background Tasks", self.test_celery_tasks),
            ]

            task = progress.add_task("Running tests...", total=len(tests))

            for test_name, test_func in tests:
                progress.update(task, description=f"Testing {test_name}...")
                test_func()
                progress.advance(task)
                time.sleep(0.5)  # Small delay between tests

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test results summary."""
        console.print("\n📊 Test Results Summary\n", style="bold blue")

        # Create results table
        table = Table(title="Production Feature Tests")
        table.add_column("Test", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")

        successful_tests = 0
        failed_tests = 0

        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            style = "green" if result["success"] else "red"

            table.add_row(
                result["test"], f"[{style}]{status}[/{style}]", result["message"]
            )

            if result["success"]:
                successful_tests += 1
            else:
                failed_tests += 1

        console.print(table)

        # Print statistics
        total_tests = len(self.test_results)
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

        console.print("\n📈 Test Statistics:")
        console.print(f"   Total Tests: {total_tests}")
        console.print(f"   ✅ Passed: {successful_tests}")
        console.print(f"   ❌ Failed: {failed_tests}")
        console.print(f"   Success Rate: {success_rate:.1f}%")

        # Production readiness assessment
        console.print("\n🎯 Production Readiness Assessment:")
        if success_rate >= 90:
            console.print("   ✅ System is PRODUCTION READY", style="bold green")
        elif success_rate >= 70:
            console.print(
                "   ⚠️  System needs minor fixes before production", style="bold yellow"
            )
        else:
            console.print("   ❌ System is NOT ready for production", style="bold red")

        # Save detailed report
        report_path = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "summary": {
                        "total_tests": total_tests,
                        "passed": successful_tests,
                        "failed": failed_tests,
                        "success_rate": success_rate,
                    },
                    "results": self.test_results,
                },
                f,
                indent=2,
            )

        console.print(f"\n📄 Detailed report saved to: {report_path}")


def main():
    """Main function."""
    tester = ProductionTester()

    try:
        # Check if API is accessible
        if not tester.test_health_check():
            console.print(
                "\n❌ API is not accessible. Please ensure all services are running.",
                style="bold red",
            )
            console.print("\nRun the following commands in separate terminals:")
            console.print("1. make run-backend")
            console.print("2. make run-frontend")
            console.print("3. make run-celery")
            console.print("4. make run-celery-beat")
            return

        # Run all tests
        tester.run_all_tests()

    except KeyboardInterrupt:
        console.print("\n\n⚠️  Tests interrupted by user", style="bold yellow")
    except Exception as e:
        console.print(f"\n\n❌ Unexpected error: {e}", style="bold red")


if __name__ == "__main__":
    main()
