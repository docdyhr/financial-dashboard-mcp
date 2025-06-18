#!/usr/bin/env python3
"""Test MCP Server for Claude Desktop Integration

This script tests the MCP server in standalone mode to verify it works
correctly with Claude Desktop. It simulates the MCP protocol communication
that Claude Desktop would use.

Usage:
    python scripts/test_mcp_standalone.py
    python scripts/test_mcp_standalone.py --verbose
    python scripts/test_mcp_standalone.py --tool get_positions
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.main import FinancialDashboardMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class MCPTester:
    """Test MCP server functionality for Claude Desktop integration."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.mcp_server = None

    async def initialize_server(self) -> bool:
        """Initialize the MCP server."""
        try:
            logger.info("🚀 Initializing MCP Server...")
            self.mcp_server = FinancialDashboardMCP()
            tool_count = len(self.mcp_server.all_tools)
            logger.info(f"✅ MCP Server initialized with {tool_count} tools")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize MCP Server: {e}")
            return False

    async def list_tools(self) -> list[dict]:
        """Test listing all available tools."""
        if not self.mcp_server:
            logger.error("MCP Server not initialized")
            return []

        try:
            tools = list(self.mcp_server.all_tools.values())
            logger.info(f"📋 Found {len(tools)} available tools:")

            for tool in tools:
                logger.info(f"  • {tool.name}: {tool.description}")
                if self.verbose and tool.inputSchema:
                    properties = tool.inputSchema.get("properties", {})
                    if properties:
                        logger.info(f"    Parameters: {', '.join(properties.keys())}")

            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema,
                }
                for tool in tools
            ]
        except Exception as e:
            logger.error(f"❌ Failed to list tools: {e}")
            return []

    async def test_tool_execution(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> bool:
        """Test executing a specific tool."""
        if not self.mcp_server:
            logger.error("MCP Server not initialized")
            return False

        if tool_name not in self.mcp_server.all_tools:
            logger.error(f"❌ Tool '{tool_name}' not found")
            available_tools = list(self.mcp_server.all_tools.keys())
            logger.info(f"Available tools: {', '.join(available_tools)}")
            return False

        try:
            logger.info(f"🔧 Testing tool: {tool_name}")
            if arguments:
                logger.info(f"   Arguments: {arguments}")

            # Determine which module handles this tool
            result = None
            if tool_name in [
                tool.name for tool in self.mcp_server.portfolio_tools.get_tools()
            ]:
                result = await self.mcp_server.portfolio_tools.execute_tool(
                    tool_name, arguments if arguments is not None else {}
                )
            elif tool_name in [
                tool.name for tool in self.mcp_server.market_tools.get_tools()
            ]:
                result = await self.mcp_server.market_tools.execute_tool(
                    tool_name, arguments if arguments is not None else {}
                )
            elif tool_name in [
                tool.name for tool in self.mcp_server.analytics_tools.get_tools()
            ]:
                result = await self.mcp_server.analytics_tools.execute_tool(
                    tool_name, arguments if arguments is not None else {}
                )

            if result:
                logger.info("✅ Tool executed successfully")
                if self.verbose:
                    for item in result:
                        logger.info(f"   Result: {item.text[:200]}...")
                return True
            logger.error("❌ Tool execution failed - no result")
            return False

        except Exception as e:
            logger.error(f"❌ Tool execution failed: {e}")
            return False

    async def test_sample_tools(self) -> dict[str, bool]:
        """Test a sample of tools with various scenarios."""
        test_results = {}

        # Test portfolio tools (may fail if backend not running - that's OK)
        portfolio_tests = [
            ("get_positions", {"include_cash": True}),
            ("get_portfolio_summary", {}),
            ("get_allocation", {}),
        ]

        # Test market data tools (may fail if backend not running - that's OK)
        market_tests = [
            ("get_asset_price", {"ticker": "AAPL"}),
        ]

        # Test analytics tools (should work without backend)
        analytics_tests = [
            (
                "recommend_allocation",
                {"risk_tolerance": "moderate", "investment_horizon": "long"},
            ),
            (
                "analyze_opportunity",
                {"criteria": {"sector": "technology", "max_pe_ratio": 25}},
            ),
            ("generate_insights", {"focus": "diversification"}),
        ]

        all_tests = portfolio_tests + market_tests + analytics_tests

        logger.info(f"🧪 Testing {len(all_tests)} sample tool executions...")

        for tool_name, arguments in all_tests:
            success = await self.test_tool_execution(tool_name, arguments)
            test_results[tool_name] = success

            # Brief pause between tests
            await asyncio.sleep(0.5)

        return test_results

    async def test_claude_desktop_integration(self) -> bool:
        """Test MCP server as Claude Desktop would use it."""
        logger.info("🖥️  Testing Claude Desktop Integration Pattern...")

        try:
            # 1. List tools (as Claude would do on startup)
            tools = await self.list_tools()
            if not tools:
                logger.error("❌ Failed to list tools")
                return False

            # 2. Test a safe analytics tool (doesn't require backend)
            success = await self.test_tool_execution(
                "recommend_allocation",
                {"risk_tolerance": "moderate", "investment_horizon": "long"},
            )

            if not success:
                logger.error("❌ Failed to execute basic tool")
                return False

            # 3. Test tool with different parameters
            success = await self.test_tool_execution(
                "generate_insights", {"focus": "risk_management"}
            )

            if not success:
                logger.error("❌ Failed to execute parameterized tool")
                return False

            logger.info("✅ Claude Desktop integration pattern successful")
            return True

        except Exception as e:
            logger.error(f"❌ Claude Desktop integration test failed: {e}")
            return False

    async def generate_claude_config(self) -> str:
        """Generate Claude Desktop configuration."""
        config = {
            "mcpServers": {
                "financial-dashboard": {
                    "command": str(project_root / ".venv" / "bin" / "python"),
                    "args": ["-m", "mcp_server"],
                    "cwd": str(project_root),
                    "env": {"BACKEND_URL": "http://localhost:8000"},
                }
            }
        }

        config_json = json.dumps(config, indent=2)

        logger.info("📋 Claude Desktop Configuration:")
        logger.info("=" * 50)
        logger.info(config_json)
        logger.info("=" * 50)

        # Save to file
        config_file = project_root / "docs" / "claude_desktop_config.json"
        with open(config_file, "w") as f:
            f.write(config_json)

        logger.info(f"💾 Configuration saved to: {config_file}")

        return config_json

    async def cleanup(self):
        """Cleanup resources."""
        if self.mcp_server:
            await self.mcp_server.cleanup()
            logger.info("🧹 Cleaned up MCP server resources")

    async def run_full_test(self) -> bool:
        """Run complete MCP server test suite."""
        logger.info("🚀 Starting MCP Server Standalone Test")
        logger.info("=" * 60)

        try:
            # 1. Initialize server
            if not await self.initialize_server():
                return False

            # 2. List all tools
            tools = await self.list_tools()
            if not tools:
                return False

            # 3. Test Claude Desktop integration pattern
            if not await self.test_claude_desktop_integration():
                return False

            # 4. Test sample tools
            test_results = await self.test_sample_tools()

            # 5. Generate Claude Desktop config
            await self.generate_claude_config()

            # Summary
            total_tests = len(test_results)
            passed_tests = sum(1 for result in test_results.values() if result)
            failed_tests = total_tests - passed_tests

            logger.info("\n" + "=" * 60)
            logger.info("📊 MCP SERVER TEST SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Total Tools: {len(tools)}")
            logger.info(f"Tool Tests: {passed_tests}/{total_tests} passed")

            if failed_tests > 0:
                logger.info(
                    "\n❌ Failed Tools (may be expected if backend not running):"
                )
                for tool_name, success in test_results.items():
                    if not success:
                        logger.info(f"  • {tool_name}")

            if passed_tests > 0:
                logger.info("\n✅ Working Tools:")
                for tool_name, success in test_results.items():
                    if success:
                        logger.info(f"  • {tool_name}")

            # Overall assessment
            analytics_tools_working = any(
                tool_name.startswith(("recommend_", "analyze_", "generate_"))
                and success
                for tool_name, success in test_results.items()
            )

            if analytics_tools_working:
                logger.info("\n🎉 MCP SERVER IS READY FOR CLAUDE DESKTOP!")
                logger.info("💡 Key Points:")
                logger.info("  • AI analytics tools are working")
                logger.info("  • Server initializes correctly")
                logger.info("  • Claude Desktop configuration generated")
                logger.info("  • Portfolio/market tools may need backend running")
                return True
            logger.error("\n❌ MCP Server has critical issues")
            return False

        except Exception as e:
            logger.error(f"💥 Test suite crashed: {e}")
            return False
        finally:
            await self.cleanup()

    async def run_single_tool_test(self, tool_name: str) -> bool:
        """Test a single tool."""
        logger.info(f"🔧 Testing Single Tool: {tool_name}")
        logger.info("=" * 40)

        try:
            if not await self.initialize_server():
                return False

            # Test the specific tool
            success = await self.test_tool_execution(tool_name)

            if success:
                logger.info(f"\n✅ Tool '{tool_name}' works correctly!")
            else:
                logger.error(f"\n❌ Tool '{tool_name}' failed!")

            return success

        except Exception as e:
            logger.error(f"💥 Single tool test crashed: {e}")
            return False
        finally:
            await self.cleanup()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test MCP Server for Claude Desktop Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/test_mcp_standalone.py                    # Run full test suite
  python scripts/test_mcp_standalone.py --verbose          # Verbose output
  python scripts/test_mcp_standalone.py --tool get_positions  # Test specific tool
        """,
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument("--tool", "-t", help="Test specific tool only")

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create tester
    tester = MCPTester(verbose=args.verbose)

    try:
        if args.tool:
            success = await tester.run_single_tool_test(args.tool)
        else:
            success = await tester.run_full_test()

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("\n⏹️  Test interrupted by user")
        await tester.cleanup()
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Test crashed: {e}")
        await tester.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
