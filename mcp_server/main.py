"""Main MCP server implementation for Financial Dashboard."""

import asyncio
import logging
import os
from typing import Any

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import TextContent, Tool

from .tools.analytics import AnalyticsTools
from .tools.market_data import MarketDataTools
from .tools.portfolio import PortfolioTools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
SERVER_NAME = "financial-dashboard-mcp"
SERVER_VERSION = "1.0.0"


class FinancialDashboardMCP:
    """Main MCP server for Financial Dashboard AI integration."""

    def __init__(self):
        """Initialize the MCP server with all tool modules."""
        self.server = Server(SERVER_NAME)

        # Initialize tool modules
        self.portfolio_tools = PortfolioTools(BACKEND_URL)
        self.market_tools = MarketDataTools(BACKEND_URL)
        self.analytics_tools = AnalyticsTools(BACKEND_URL)

        # All available tools
        self.all_tools: dict[str, Any] = {}
        self._setup_tools()
        self._setup_handlers()

    def _setup_tools(self):
        """Setup all available tools from different modules."""
        # Get tools from each module
        portfolio_tools = self.portfolio_tools.get_tools()
        market_tools = self.market_tools.get_tools()
        analytics_tools = self.analytics_tools.get_tools()

        # Combine all tools
        all_tool_lists = [portfolio_tools, market_tools, analytics_tools]
        for tool_list in all_tool_lists:
            for tool in tool_list:
                self.all_tools[tool.name] = tool

        logger.info(f"Loaded {len(self.all_tools)} MCP tools")

    def _setup_handlers(self):
        """Setup MCP server handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """Handle list tools request."""
            logger.info("Listing available tools")
            return list(self.all_tools.values())

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict[str, Any] | None
        ) -> list[TextContent]:
            """Handle tool execution request."""
            logger.info(f"Executing tool: {name} with arguments: {arguments}")

            if arguments is None:
                arguments = {}

            try:
                # Route tool execution to appropriate module
                if name in [tool.name for tool in self.portfolio_tools.get_tools()]:
                    return await self.portfolio_tools.execute_tool(name, arguments)
                if name in [tool.name for tool in self.market_tools.get_tools()]:
                    return await self.market_tools.execute_tool(name, arguments)
                if name in [tool.name for tool in self.analytics_tools.get_tools()]:
                    return await self.analytics_tools.execute_tool(name, arguments)
                logger.error(f"Unknown tool: {name}")
                return [
                    TextContent(
                        type="text",
                        text=f"Unknown tool: {name}. Available tools: {list(self.all_tools.keys())}",
                    )
                ]

            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return [
                    TextContent(
                        type="text",
                        text=f"Error executing tool {name}: {e!s}",
                    )
                ]

    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up MCP server resources")
        await self.portfolio_tools.close()
        await self.market_tools.close()
        await self.analytics_tools.close()

    async def run_stdio(self):
        """Run the MCP server with stdio transport."""
        logger.info(f"Starting {SERVER_NAME} v{SERVER_VERSION}")
        logger.info(f"Backend URL: {BACKEND_URL}")
        logger.info(f"Available tools: {list(self.all_tools.keys())}")

        try:
            # Import the stdio server function
            from mcp.server.stdio import stdio_server

            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name=SERVER_NAME,
                        server_version=SERVER_VERSION,
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={},
                        ),
                    ),
                )
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
        finally:
            await self.cleanup()


async def main():
    """Main entry point for the MCP server."""
    mcp_server = FinancialDashboardMCP()
    await mcp_server.run_stdio()


if __name__ == "__main__":
    asyncio.run(main())
