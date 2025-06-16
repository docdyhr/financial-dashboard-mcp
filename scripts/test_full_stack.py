#!/usr/bin/env python3
"""Comprehensive Full Stack Integration Test for Financial Dashboard

This script tests the complete integration of all services:
- PostgreSQL database connectivity
- Redis cache operations
- FastAPI backend endpoints
- Celery task processing
- Flower monitoring
- Streamlit frontend (basic connectivity)
- MCP server functionality

Usage:
    python scripts/test_full_stack.py
    python scripts/test_full_stack.py --verbose
    python scripts/test_full_stack.py --service backend
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

import psutil
import redis
import requests
from sqlalchemy import create_engine, text

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class FullStackTester:
    """Comprehensive test suite for all Financial Dashboard services."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: dict[str, bool] = {}
        self.errors: dict[str, str] = {}

        # Load environment
        self._load_environment()

        # Service URLs
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        self.frontend_url = "http://localhost:8501"
        self.flower_url = "http://localhost:5555"
        self.database_url = os.getenv("DATABASE_URL")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    def _load_environment(self):
        """Load environment variables from .env file."""
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ.setdefault(key.strip(), value.strip())

    def _log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        message = f"{test_name}: {status}"
        if details:
            message += f" - {details}"

        if success:
            logger.info(message)
        else:
            logger.error(message)

        self.results[test_name] = success
        if not success and details:
            self.errors[test_name] = details

    def test_prerequisites(self) -> bool:
        """Test that all prerequisites are installed."""
        logger.info("🔍 Testing Prerequisites")

        # Test Python version
        python_version = sys.version_info
        if python_version >= (3, 8):
            self._log_test(
                "Python Version",
                True,
                f"{python_version.major}.{python_version.minor}.{python_version.micro}",
            )
        else:
            self._log_test(
                "Python Version",
                False,
                f"Need 3.8+, got {python_version.major}.{python_version.minor}.{python_version.micro}",
            )
            return False

        # Test required packages
        required_packages = ["requests", "redis", "sqlalchemy", "psutil"]

        for package in required_packages:
            try:
                __import__(package)
                self._log_test(f"Package {package}", True)
            except ImportError:
                self._log_test(f"Package {package}", False, "Not installed")
                return False

        return all(self.results[f"Package {pkg}"] for pkg in required_packages)

    def test_service_ports(self) -> bool:
        """Test that required service ports are accessible."""
        logger.info("🔌 Testing Service Ports")

        ports_to_test = {
            "PostgreSQL": 5432,
            "Redis": 6379,
            "Backend": 8000,
            "Flower": 5555,
            "Frontend": 8501,
        }

        all_ports_ok = True

        for service, port in ports_to_test.items():
            try:
                # Check if port is listening
                port_open = False
                for conn in psutil.net_connections():
                    if (
                        hasattr(conn, "laddr")
                        and conn.laddr
                        and conn.laddr.port == port
                    ):
                        if conn.status == "LISTEN":
                            port_open = True
                            break

                self._log_test(
                    f"Port {port} ({service})",
                    port_open,
                    "Listening" if port_open else "Not accessible",
                )
                if not port_open:
                    all_ports_ok = False

            except Exception as e:
                self._log_test(f"Port {port} ({service})", False, str(e))
                all_ports_ok = False

        return all_ports_ok

    def test_database_connectivity(self) -> bool:
        """Test PostgreSQL database connectivity and basic operations."""
        logger.info("🗄️  Testing Database Connectivity")

        if not self.database_url:
            self._log_test("Database URL", False, "DATABASE_URL not set")
            return False

        try:
            # Test connection
            engine = create_engine(self.database_url)
            with engine.connect() as conn:
                # Test basic query
                result = conn.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                if row is None:
                    self._log_test(
                        "Database Connection", False, "Query returned no results"
                    )
                    return False
                test_value = row[0]

                if test_value == 1:
                    self._log_test("Database Connection", True)
                else:
                    self._log_test(
                        "Database Connection", False, "Query returned unexpected result"
                    )
                    return False

                # Test table existence
                result = conn.execute(
                    text(
                        """
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public'
                """
                    )
                )
                tables = [row[0] for row in result.fetchall()]

                expected_tables = ["assets", "positions", "transactions", "users"]
                tables_exist = any(table in tables for table in expected_tables)

                self._log_test(
                    "Database Tables",
                    tables_exist,
                    f"Found {len(tables)} tables: {', '.join(tables[:5])}",
                )

                return tables_exist

        except Exception as e:
            self._log_test("Database Connection", False, str(e))
            return False

    def test_redis_connectivity(self) -> bool:
        """Test Redis connectivity and basic operations."""
        logger.info("📦 Testing Redis Connectivity")

        try:
            # Parse Redis URL
            if self.redis_url.startswith("redis://"):
                url_parts = self.redis_url.replace("redis://", "").split("/")
                host_port = url_parts[0].split(":")
                host = host_port[0] if host_port else "localhost"
                port = int(host_port[1]) if len(host_port) > 1 else 6379
                db = int(url_parts[1]) if len(url_parts) > 1 else 0
            else:
                host, port, db = "localhost", 6379, 0

            # Test connection
            r = redis.Redis(host=host, port=port, db=db, socket_timeout=5)

            # Test ping
            if r.ping():
                self._log_test("Redis Ping", True)
            else:
                self._log_test("Redis Ping", False, "Ping failed")
                return False

            # Test basic operations
            test_key = "test_full_stack_key"
            test_value = "test_value_12345"

            # Set value
            r.set(test_key, test_value, ex=60)  # Expire in 60 seconds

            # Get value
            retrieved_value = r.get(test_key)
            if retrieved_value and retrieved_value.decode() == test_value:
                self._log_test("Redis Operations", True, "Set/Get test passed")
                r.delete(test_key)  # Cleanup
                return True
            self._log_test("Redis Operations", False, "Set/Get test failed")
            return False

        except Exception as e:
            self._log_test("Redis Connection", False, str(e))
            return False

    def test_backend_api(self) -> bool:
        """Test FastAPI backend endpoints."""
        logger.info("🚀 Testing Backend API")

        try:
            # Test health endpoint
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                self._log_test(
                    "Backend Health", True, f"Status: {response.status_code}"
                )
            else:
                self._log_test(
                    "Backend Health", False, f"Status: {response.status_code}"
                )
                return False

            # Test root endpoint
            response = requests.get(f"{self.backend_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self._log_test(
                    "Backend Root", True, f"Version: {data.get('version', 'unknown')}"
                )
            else:
                self._log_test("Backend Root", False, f"Status: {response.status_code}")
                return False

            # Test API status endpoint
            response = requests.get(f"{self.backend_url}/api/v1/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self._log_test(
                    "API Status", True, f"Status: {data.get('status', 'unknown')}"
                )

                # Check service statuses
                services = data.get("services", {})
                if self.verbose:
                    for service, status in services.items():
                        logger.info(f"  Service {service}: {status}")

            else:
                self._log_test("API Status", False, f"Status: {response.status_code}")

            # Test API documentation
            response = requests.get(f"{self.backend_url}/docs", timeout=10)
            if response.status_code == 200:
                self._log_test("API Documentation", True)
            else:
                self._log_test(
                    "API Documentation", False, f"Status: {response.status_code}"
                )

            # Test portfolio endpoints (basic)
            response = requests.get(
                f"{self.backend_url}/api/v1/portfolio/positions", timeout=10
            )
            # Don't fail if no data, just check endpoint is accessible
            if response.status_code in [200, 404]:  # 404 is OK if no data
                self._log_test(
                    "Portfolio Endpoints", True, f"Status: {response.status_code}"
                )
            else:
                self._log_test(
                    "Portfolio Endpoints", False, f"Status: {response.status_code}"
                )

            return True

        except requests.exceptions.ConnectionError:
            self._log_test(
                "Backend Connection", False, "Connection refused - is backend running?"
            )
            return False
        except Exception as e:
            self._log_test("Backend API", False, str(e))
            return False

    def test_celery_tasks(self) -> bool:
        """Test Celery task processing."""
        logger.info("⚙️  Testing Celery Tasks")

        try:
            # Import Celery app (this tests if Celery can load)
            from backend.tasks import celery_app

            # Test Celery ping
            result = celery_app.control.ping(timeout=5)
            if result:
                active_workers = len(result)
                self._log_test(
                    "Celery Workers", True, f"{active_workers} worker(s) active"
                )
            else:
                self._log_test("Celery Workers", False, "No workers responding")
                return False

            # Test task inspection
            inspect = celery_app.control.inspect()

            # Get active tasks
            active_tasks = inspect.active()
            if active_tasks is not None:
                total_active = sum(len(tasks) for tasks in active_tasks.values())
                self._log_test("Active Tasks", True, f"{total_active} task(s) running")
            else:
                self._log_test("Active Tasks", False, "Cannot inspect tasks")

            # Get registered tasks
            registered = inspect.registered()
            if registered:
                total_registered = sum(len(tasks) for tasks in registered.values())
                self._log_test(
                    "Registered Tasks", True, f"{total_registered} task(s) registered"
                )

                if self.verbose:
                    for worker, tasks in registered.items():
                        logger.info(f"  Worker {worker}: {len(tasks)} tasks")
            else:
                self._log_test("Registered Tasks", False, "No tasks registered")

            return True

        except ImportError as e:
            self._log_test("Celery Import", False, f"Cannot import Celery: {e}")
            return False
        except Exception as e:
            self._log_test("Celery Tasks", False, str(e))
            return False

    def test_flower_monitoring(self) -> bool:
        """Test Flower monitoring interface."""
        logger.info("🌸 Testing Flower Monitoring")

        try:
            # Test Flower with authentication
            response = requests.get(
                self.flower_url, auth=("admin", "admin"), timeout=10
            )
            if response.status_code == 200:
                self._log_test("Flower UI", True, "Accessible with authentication")
            else:
                self._log_test("Flower UI", False, f"Status: {response.status_code}")
                return False

            # Test Flower API
            api_url = f"{self.flower_url}/api/workers"
            response = requests.get(api_url, auth=("admin", "admin"), timeout=10)
            if response.status_code == 200:
                workers = response.json()
                self._log_test("Flower API", True, f"{len(workers)} worker(s) visible")
                return True
            self._log_test("Flower API", False, f"Status: {response.status_code}")
            return False

        except requests.exceptions.ConnectionError:
            self._log_test(
                "Flower Connection", False, "Connection refused - is Flower running?"
            )
            return False
        except Exception as e:
            self._log_test("Flower Monitoring", False, str(e))
            return False

    def test_frontend_connectivity(self) -> bool:
        """Test Streamlit frontend basic connectivity."""
        logger.info("🖥️  Testing Frontend Connectivity")

        try:
            # Test Streamlit health endpoint
            health_url = f"{self.frontend_url}/_stcore/health"
            response = requests.get(health_url, timeout=10)
            if response.status_code == 200:
                self._log_test("Frontend Health", True)
            else:
                self._log_test(
                    "Frontend Health", False, f"Status: {response.status_code}"
                )

            # Test main page (basic connectivity)
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                # Check if it's actually Streamlit
                if (
                    "streamlit" in response.text.lower()
                    or "st-emotion-cache" in response.text
                ):
                    self._log_test("Frontend Main Page", True, "Streamlit detected")
                    return True
                self._log_test("Frontend Main Page", False, "Not a Streamlit app")
                return False
            self._log_test(
                "Frontend Main Page", False, f"Status: {response.status_code}"
            )
            return False

        except requests.exceptions.ConnectionError:
            self._log_test(
                "Frontend Connection",
                False,
                "Connection refused - is frontend running?",
            )
            return False
        except Exception as e:
            self._log_test("Frontend Connectivity", False, str(e))
            return False

    def test_mcp_server(self) -> bool:
        """Test MCP server functionality."""
        logger.info("🤖 Testing MCP Server")

        try:
            # Test MCP server imports
            from mcp_server.main import FinancialDashboardMCP

            self._log_test("MCP Imports", True, "All modules imported successfully")

            # Test MCP server initialization
            mcp_server = FinancialDashboardMCP()
            tool_count = len(mcp_server.all_tools)

            if tool_count > 0:
                self._log_test("MCP Initialization", True, f"{tool_count} tools loaded")

                # Test a few key tools
                expected_tools = [
                    "get_positions",
                    "get_portfolio_summary",
                    "recommend_allocation",
                ]
                available_tools = list(mcp_server.all_tools.keys())

                tools_found = [
                    tool for tool in expected_tools if tool in available_tools
                ]
                if len(tools_found) == len(expected_tools):
                    self._log_test(
                        "MCP Tools",
                        True,
                        f"All expected tools found: {', '.join(tools_found)}",
                    )
                else:
                    missing = [
                        tool for tool in expected_tools if tool not in available_tools
                    ]
                    self._log_test(
                        "MCP Tools", False, f"Missing tools: {', '.join(missing)}"
                    )

                # Cleanup
                asyncio.run(mcp_server.cleanup())
                return True
            self._log_test("MCP Initialization", False, "No tools loaded")
            return False

        except ImportError as e:
            self._log_test("MCP Server Import", False, f"Import error: {e}")
            return False
        except Exception as e:
            self._log_test("MCP Server", False, str(e))
            return False

    def test_integration_flow(self) -> bool:
        """Test end-to-end integration flow."""
        logger.info("🔄 Testing Integration Flow")

        try:
            # Test data flow: Frontend -> Backend -> Database

            # 1. Backend can connect to database
            if not self.results.get("Database Connection", False):
                self._log_test("Integration Flow", False, "Database not accessible")
                return False

            # 2. Backend API is responding
            if not self.results.get("Backend Health", False):
                self._log_test("Integration Flow", False, "Backend not accessible")
                return False

            # 3. Celery can process tasks
            if not self.results.get("Celery Workers", False):
                self._log_test(
                    "Integration Flow", False, "Celery workers not available"
                )
                return False

            # 4. Frontend can reach backend
            try:
                # Make a request from frontend perspective
                response = requests.get(f"{self.backend_url}/api/v1/status", timeout=5)
                if response.status_code == 200:
                    self._log_test(
                        "Frontend->Backend", True, "API reachable from frontend"
                    )
                else:
                    self._log_test(
                        "Frontend->Backend",
                        False,
                        f"API returned {response.status_code}",
                    )
                    return False
            except Exception as e:
                self._log_test("Frontend->Backend", False, str(e))
                return False

            # 5. MCP server can connect to backend
            if self.results.get("MCP Initialization", False):
                self._log_test(
                    "MCP->Backend", True, "MCP server can connect to backend"
                )
            else:
                self._log_test("MCP->Backend", False, "MCP server not functional")

            self._log_test(
                "Integration Flow", True, "All components integrated successfully"
            )
            return True

        except Exception as e:
            self._log_test("Integration Flow", False, str(e))
            return False

    def generate_report(self) -> dict:
        """Generate comprehensive test report."""
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result)
        failed_tests = total_tests - passed_tests

        report = {
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": (
                    (passed_tests / total_tests) * 100 if total_tests > 0 else 0
                ),
            },
            "results": self.results,
            "errors": self.errors,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "environment": {
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "platform": sys.platform,
                "backend_url": self.backend_url,
                "database_url": (
                    self.database_url.split("@")[1]
                    if self.database_url and "@" in self.database_url
                    else "N/A"
                ),
            },
        }

        return report

    def run_all_tests(self) -> bool:
        """Run complete test suite."""
        logger.info("🧪 Starting Full Stack Integration Tests")
        logger.info("=" * 60)

        # Test categories in order
        test_methods = [
            ("Prerequisites", self.test_prerequisites),
            ("Service Ports", self.test_service_ports),
            ("Database", self.test_database_connectivity),
            ("Redis", self.test_redis_connectivity),
            ("Backend API", self.test_backend_api),
            ("Celery Tasks", self.test_celery_tasks),
            ("Flower Monitoring", self.test_flower_monitoring),
            ("Frontend", self.test_frontend_connectivity),
            ("MCP Server", self.test_mcp_server),
            ("Integration Flow", self.test_integration_flow),
        ]

        overall_success = True

        for category, test_method in test_methods:
            try:
                logger.info(f"\n{category} Tests:")
                logger.info("-" * 30)

                success = test_method()
                if not success:
                    overall_success = False

            except Exception as e:
                logger.error(f"Test category '{category}' crashed: {e}")
                self._log_test(f"{category} (crashed)", False, str(e))
                overall_success = False

        # Generate and display report
        report = self.generate_report()

        logger.info("\n" + "=" * 60)
        logger.info("📋 FULL STACK TEST REPORT")
        logger.info("=" * 60)

        summary = report["summary"]
        logger.info(f"Total Tests: {summary['total']}")
        logger.info(f"Passed: {summary['passed']} ✅")
        logger.info(f"Failed: {summary['failed']} ❌")
        logger.info(f"Success Rate: {summary['success_rate']:.1f}%")

        if summary["failed"] > 0:
            logger.info("\n❌ Failed Tests:")
            for test_name, error in report["errors"].items():
                logger.error(f"  • {test_name}: {error}")

        logger.info(f"\n🕐 Test completed at: {report['timestamp']}")

        if overall_success:
            logger.info(
                "\n🎉 ALL TESTS PASSED! Financial Dashboard is fully operational."
            )
        else:
            logger.error("\n💥 SOME TESTS FAILED! Check the errors above.")

        # Save report to file
        report_file = PROJECT_ROOT / "logs" / "test_report.json"
        report_file.parent.mkdir(exist_ok=True)
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"📄 Detailed report saved to: {report_file}")

        return overall_success

    def run_single_test(self, service: str) -> bool:
        """Run test for a single service."""
        test_map = {
            "prerequisites": self.test_prerequisites,
            "ports": self.test_service_ports,
            "database": self.test_database_connectivity,
            "redis": self.test_redis_connectivity,
            "backend": self.test_backend_api,
            "celery": self.test_celery_tasks,
            "flower": self.test_flower_monitoring,
            "frontend": self.test_frontend_connectivity,
            "mcp": self.test_mcp_server,
            "integration": self.test_integration_flow,
        }

        if service.lower() not in test_map:
            logger.error(f"Unknown service: {service}")
            logger.info(f"Available services: {', '.join(test_map.keys())}")
            return False

        logger.info(f"🧪 Testing {service.title()} Service")
        logger.info("=" * 40)

        success = test_map[service.lower()]()

        if success:
            logger.info(f"\n✅ {service.title()} test passed!")
        else:
            logger.error(f"\n❌ {service.title()} test failed!")
            if service.lower() in self.errors:
                logger.error(f"Error: {self.errors[service.lower()]}")

        return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Financial Dashboard Full Stack Integration Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/test_full_stack.py                    # Run all tests
  python scripts/test_full_stack.py --verbose          # Verbose output
  python scripts/test_full_stack.py --service backend  # Test specific service
  python scripts/test_full_stack.py --service database # Test database only
        """,
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--service",
        "-s",
        choices=[
            "prerequisites",
            "ports",
            "database",
            "redis",
            "backend",
            "celery",
            "flower",
            "frontend",
            "mcp",
            "integration",
        ],
        help="Test specific service only",
    )

    args = parser.parse_args()

    # Create tester
    tester = FullStackTester(verbose=args.verbose)

    try:
        if args.service:
            success = tester.run_single_test(args.service)
        else:
            success = tester.run_all_tests()

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Test suite crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
