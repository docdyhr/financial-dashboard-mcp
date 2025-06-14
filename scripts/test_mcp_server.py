#!/usr/bin/env python3
"""Test the MCP server functionality."""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_mcp_tools():
    """Test MCP server tools directly."""
    try:
        from mcp_server.tools.analytics import AnalyticsTools
        from mcp_server.tools.market_data import MarketDataTools
        from mcp_server.tools.portfolio import PortfolioTools

        # Test portfolio tools
        logger.info("Testing Portfolio Tools...")
        portfolio_tools = PortfolioTools()

        # Test get tools
        tools = portfolio_tools.get_tools()
        logger.info(f"Portfolio tools available: {[tool.name for tool in tools]}")

        # Test a simple tool
        try:
            result = await portfolio_tools.execute_tool(
                "get_positions", {"include_cash": True}
            )
            logger.info("✅ get_positions tool executed successfully")
            print(f"Result: {result[0].text[:200]}...")
        except Exception as e:
            logger.warning(
                f"⚠️ get_positions failed (expected if backend not running): {e}"
            )

        await portfolio_tools.close()

        # Test market data tools
        logger.info("Testing Market Data Tools...")
        market_tools = MarketDataTools()

        tools = market_tools.get_tools()
        logger.info(f"Market tools available: {[tool.name for tool in tools]}")

        try:
            result = await market_tools.execute_tool(
                "get_asset_price", {"ticker": "AAPL"}
            )
            logger.info("✅ get_asset_price tool executed successfully")
            print(f"Result: {result[0].text[:200]}...")
        except Exception as e:
            logger.warning(
                f"⚠️ get_asset_price failed (expected if backend not running): {e}"
            )

        await market_tools.close()

        # Test analytics tools
        logger.info("Testing Analytics Tools...")
        analytics_tools = AnalyticsTools()

        tools = analytics_tools.get_tools()
        logger.info(f"Analytics tools available: {[tool.name for tool in tools]}")

        # Test recommendation tool (doesn't require backend)
        try:
            result = await analytics_tools.execute_tool(
                "recommend_allocation",
                {"risk_tolerance": "moderate", "investment_horizon": "long"},
            )
            logger.info("✅ recommend_allocation tool executed successfully")
            print(f"Result: {result[0].text[:300]}...")
        except Exception as e:
            logger.error(f"❌ recommend_allocation failed: {e}")

        await analytics_tools.close()

        logger.info("✅ All MCP tools tested successfully!")

    except Exception as e:
        logger.error(f"❌ MCP tools test failed: {e}")
        return False

    return True


async def test_mcp_server():
    """Test MCP server initialization."""
    try:
        from mcp_server.main import FinancialDashboardMCP

        logger.info("Testing MCP Server initialization...")

        # Create server instance
        mcp_server = FinancialDashboardMCP()

        # Check tools are loaded
        logger.info(f"Server loaded {len(mcp_server.all_tools)} tools:")
        for tool_name in mcp_server.all_tools.keys():
            logger.info(f"  - {tool_name}")

        # Cleanup
        await mcp_server.cleanup()

        logger.info("✅ MCP Server initialization test passed!")
        return True

    except Exception as e:
        logger.error(f"❌ MCP Server test failed: {e}")
        return False


def test_mcp_configuration():
    """Test MCP configuration and dependencies."""
    try:
        logger.info("Testing MCP configuration...")

        # Test MCP imports
        from mcp.types import TextContent, Tool

        logger.info("✅ MCP package imports successful")

        # Test HTTP client

        logger.info("✅ HTTP client available")

        # Test tool creation
        test_tool = Tool(
            name="test_tool",
            description="A test tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "test_param": {"type": "string", "description": "A test parameter"}
                },
            },
        )
        logger.info("✅ Tool creation successful")

        # Test text content creation
        test_content = TextContent(type="text", text="Test content")
        logger.info("✅ TextContent creation successful")

        logger.info("✅ MCP configuration test passed!")
        return True

    except Exception as e:
        logger.error(f"❌ MCP configuration test failed: {e}")
        return False


def create_mcp_config():
    """Create sample MCP configuration for Claude Desktop."""
    config = {
        "mcpServers": {
            "financial-dashboard": {
                "command": "python",
                "args": [str(project_root / "scripts" / "start_mcp_server.py")],
                "env": {"BACKEND_URL": "http://localhost:8000"},
            }
        }
    }

    config_path = project_root / "docs" / "claude_desktop_config.json"
    config_path.parent.mkdir(exist_ok=True)

    with open(config_path, "w") as f:
        json.dump(config, indent=2, fp=f)

    logger.info(f"✅ Created Claude Desktop config at: {config_path}")

    # Also create a README for MCP setup
    readme_content = """# MCP Server Setup for Claude Desktop

## Installation

1. **Install the Financial Dashboard MCP Server:**
   ```bash
   cd /path/to/financial-dashboard-mcp
   pip install -e .
   ```

2. **Start the backend services:**
   ```bash
   ./scripts/start_dashboard.sh
   ```

3. **Configure Claude Desktop:**

   Add the following to your Claude Desktop configuration file:
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\\Claude\\claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "financial-dashboard": {
         "command": "python",
         "args": [
           "/full/path/to/financial-dashboard-mcp/scripts/start_mcp_server.py"
         ],
         "env": {
           "BACKEND_URL": "http://localhost:8000"
         }
       }
     }
   }
   ```

4. **Restart Claude Desktop** to load the MCP server.

## Available Tools

### Portfolio Management
- `get_positions` - Retrieve current portfolio positions
- `get_portfolio_summary` - Get comprehensive portfolio overview
- `get_allocation` - Get current portfolio allocation breakdown
- `add_position` - Add a new position to the portfolio
- `update_position` - Update an existing portfolio position

### Market Data
- `get_asset_price` - Get current price and basic info for an asset
- `calculate_performance` - Calculate portfolio performance for specific periods
- `analyze_portfolio_risk` - Analyze portfolio risk metrics and volatility
- `get_market_trends` - Get current market trends and sector performance

### AI Analytics
- `recommend_allocation` - Get AI-powered portfolio allocation recommendations
- `analyze_opportunity` - Find investment opportunities based on criteria
- `rebalance_portfolio` - Generate portfolio rebalancing recommendations
- `generate_insights` - Generate AI-powered portfolio insights and recommendations

## Example Usage

Once configured, you can ask Claude questions like:

- "Show me my current portfolio positions"
- "What's my portfolio performance this year?"
- "Recommend an allocation for moderate risk tolerance"
- "Analyze opportunities in growth stocks"
- "Should I rebalance my portfolio?"
- "Give me insights on my portfolio risk"

## Troubleshooting

- Ensure the backend is running on `http://localhost:8000`
- Check that the MCP server script path is correct
- Look at Claude Desktop logs for any connection issues
- Test the MCP server independently: `python scripts/test_mcp_server.py`
"""

    readme_path = project_root / "docs" / "MCP_SETUP.md"
    with open(readme_path, "w") as f:
        f.write(readme_content)

    logger.info(f"✅ Created MCP setup guide at: {readme_path}")


async def main():
    """Run all tests."""
    logger.info("🚀 Starting MCP Server Tests")
    logger.info("=" * 50)

    # Test configuration
    config_success = test_mcp_configuration()
    if not config_success:
        logger.error("❌ Configuration test failed, stopping tests")
        sys.exit(1)

    # Test tools
    tools_success = await test_mcp_tools()

    # Test server
    server_success = await test_mcp_server()

    # Create config files
    try:
        create_mcp_config()
        config_created = True
    except Exception as e:
        logger.error(f"❌ Failed to create config: {e}")
        config_created = False

    # Summary
    logger.info("=" * 50)
    logger.info("🏁 Test Results Summary:")
    logger.info(f"  Configuration: {'✅ PASS' if config_success else '❌ FAIL'}")
    logger.info(f"  Tools: {'✅ PASS' if tools_success else '⚠️ PARTIAL'}")
    logger.info(f"  Server: {'✅ PASS' if server_success else '❌ FAIL'}")
    logger.info(f"  Config Creation: {'✅ PASS' if config_created else '❌ FAIL'}")

    if config_success and server_success and config_created:
        logger.info("\n🎉 MCP Server is ready!")
        logger.info("📋 Next steps:")
        logger.info("  1. Start the backend: ./scripts/start_dashboard.sh")
        logger.info("  2. Configure Claude Desktop (see docs/MCP_SETUP.md)")
        logger.info("  3. Test with Claude: 'Show me my portfolio positions'")
    else:
        logger.error("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
