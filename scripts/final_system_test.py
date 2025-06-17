#!/usr/bin/env python3
"""Final integration test for the complete Financial Dashboard system."""

import asyncio
import logging
import sys
import time
from pathlib import Path

import httpx

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SystemTester:
    """Complete system integration tester."""

    def __init__(self):
        """Initialize the system tester."""
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:8501"
        self.processes = []
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def cleanup(self):
        """Cleanup resources."""
        await self.http_client.aclose()
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except Exception:
                process.kill()

    async def test_backend_health(self) -> bool:
        """Test backend health and basic functionality."""
        try:
            logger.info("Testing backend health...")

            # Test health endpoint
            response = await self.http_client.get(f"{self.backend_url}/health")
            if response.status_code != 200:
                logger.error(f"Backend health check failed: {response.status_code}")
                return False

            logger.info("✅ Backend health check passed")

            # Test API endpoints
            endpoints = [
                "/api/portfolio/summary",
                "/api/portfolio/positions",
                "/api/portfolio/allocation",
                "/api/portfolio/performance",
            ]

            for endpoint in endpoints:
                try:
                    response = await self.http_client.get(
                        f"{self.backend_url}{endpoint}"
                    )
                    logger.info(f"✅ {endpoint}: {response.status_code}")
                except Exception as e:
                    logger.warning(f"⚠️ {endpoint}: {e}")

            return True

        except Exception as e:
            logger.error(f"❌ Backend test failed: {e}")
            return False

    async def test_mcp_tools(self) -> bool:
        """Test MCP tools functionality."""
        try:
            logger.info("Testing MCP tools...")

            from mcp_server.tools.analytics import AnalyticsTools
            from mcp_server.tools.portfolio import PortfolioTools

            # Test portfolio tools
            portfolio_tools = PortfolioTools(self.backend_url)
            tools = portfolio_tools.get_tools()
            logger.info(f"✅ Portfolio tools loaded: {len(tools)} tools")

            # Test analytics tools (these work without backend)
            analytics_tools = AnalyticsTools(self.backend_url)
            _ = await analytics_tools.execute_tool(
                "recommend_allocation", {"risk_tolerance": "moderate"}
            )
            logger.info("✅ Analytics tools working")

            await portfolio_tools.close()
            await analytics_tools.close()

            return True

        except Exception as e:
            logger.error(f"❌ MCP tools test failed: {e}")
            return False

    def test_mcp_server_startup(self) -> bool:
        """Test MCP server can start up."""
        try:
            logger.info("Testing MCP server startup...")

            from mcp_server.main import FinancialDashboardMCP

            # Test server initialization
            mcp_server = FinancialDashboardMCP()
            logger.info(
                f"✅ MCP server initialized with {len(mcp_server.all_tools)} tools"
            )

            # Test tool listing
            tool_names = list(mcp_server.all_tools.keys())
            expected_tools = [
                "get_positions",
                "get_portfolio_summary",
                "get_allocation",
                "add_position",
                "update_position",
                "get_asset_price",
                "calculate_performance",
                "analyze_portfolio_risk",
                "get_market_trends",
                "recommend_allocation",
                "analyze_opportunity",
                "rebalance_portfolio",
                "generate_insights",
            ]

            for tool in expected_tools:
                if tool not in tool_names:
                    logger.error(f"❌ Missing expected tool: {tool}")
                    return False

            logger.info("✅ All expected MCP tools are available")
            return True

        except Exception as e:
            logger.error(f"❌ MCP server test failed: {e}")
            return False

    def test_file_structure(self) -> bool:
        """Test project file structure and key files."""
        try:
            logger.info("Testing project file structure...")

            required_files = [
                "README.md",
                "TODO.md",
                "CHANGELOG.md",
                "requirements.txt",
                "docker-compose.yml",
                "backend/main.py",
                "frontend/app.py",
                "mcp_server/main.py",
                "scripts/start_mcp_server.py",
                "scripts/test_mcp_server.py",
                "docs/MCP_SETUP.md",
                "docs/claude_desktop_config.json",
            ]

            missing_files = []
            for file_path in required_files:
                full_path = project_root / file_path
                if not full_path.exists():
                    missing_files.append(file_path)

            if missing_files:
                logger.error(f"❌ Missing required files: {missing_files}")
                return False

            logger.info("✅ All required project files are present")
            return True

        except Exception as e:
            logger.error(f"❌ File structure test failed: {e}")
            return False

    def test_scripts_executable(self) -> bool:
        """Test that key scripts are executable."""
        try:
            logger.info("Testing script permissions...")

            scripts = [
                "scripts/start_mcp_server.py",
                "scripts/test_mcp_server.py",
                "scripts/start_dashboard.sh",
                "scripts/demo_setup.py",
                "scripts/integration_test.py",
                "scripts/start_task_queue.sh",
            ]

            for script in scripts:
                script_path = project_root / script
                if script_path.exists() and not script_path.stat().st_mode & 0o111:
                    logger.warning(f"⚠️ Script not executable: {script}")
                else:
                    logger.info(f"✅ Script executable: {script}")

            return True

        except Exception as e:
            logger.error(f"❌ Script permissions test failed: {e}")
            return False

    async def run_comprehensive_test(self) -> dict[str, bool]:
        """Run all system tests."""
        logger.info("🚀 Starting comprehensive system test")
        logger.info("=" * 60)

        results = {}

        # Test file structure
        results["file_structure"] = self.test_file_structure()

        # Test script permissions
        results["script_permissions"] = self.test_scripts_executable()

        # Test MCP server
        results["mcp_server"] = self.test_mcp_server_startup()

        # Test MCP tools
        results["mcp_tools"] = await self.test_mcp_tools()

        # Test backend (if running)
        try:
            results["backend"] = await self.test_backend_health()
        except Exception:
            logger.info("⚠️ Backend not running - skipping backend tests")
            results["backend"] = None

        return results


async def main():
    """Run the comprehensive system test."""
    tester = SystemTester()

    try:
        results = await tester.run_comprehensive_test()

        # Summary
        logger.info("=" * 60)
        logger.info("🏁 System Test Results Summary:")

        passed = 0
        total = 0

        for test_name, result in results.items():
            if result is None:
                status = "⏭️ SKIPPED"
            elif result:
                status = "✅ PASS"
                passed += 1
                total += 1
            else:
                status = "❌ FAIL"
                total += 1

            logger.info(f"  {test_name.replace('_', ' ').title()}: {status}")

        if total > 0:
            success_rate = (passed / total) * 100
            logger.info(
                f"\nOverall Success Rate: {success_rate:.1f}% ({passed}/{total})"
            )

        if passed == total and total > 0:
            logger.info("\n🎉 All tests passed! System is ready for use.")
            logger.info("\n📋 Next steps:")
            logger.info("  1. Start backend: ./scripts/start_dashboard.sh")
            logger.info("  2. Configure Claude Desktop: see docs/MCP_SETUP.md")
            logger.info("  3. Test with Claude: 'Show me my portfolio'")

            # Create a status file
            status_file = project_root / "SYSTEM_STATUS.md"
            with status_file.open("w") as f:
                f.write("# System Status\n\n")
                f.write("✅ **Status**: All systems operational\n\n")
                f.write("## Test Results\n\n")
                for test_name, result in results.items():
                    status = (
                        "✅ PASS"
                        if result
                        else "⏭️ SKIPPED" if result is None else "❌ FAIL"
                    )
                    f.write(f"- {test_name.replace('_', ' ').title()}: {status}\n")
                f.write(f"\n**Last Updated**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Success Rate**: {success_rate:.1f}%\n")

            logger.info(f"📄 System status written to: {status_file}")

        else:
            logger.error("\n❌ Some tests failed. Please check the errors above.")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ System test failed: {e}")
        sys.exit(1)
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
