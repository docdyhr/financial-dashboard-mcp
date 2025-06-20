#!/usr/bin/env python3
"""Financial Dashboard MCP Server

A Model Context Protocol server that provides AI-powered financial analysis tools
for portfolio management, market data, and investment recommendations.
"""

import asyncio
import logging
import os
from typing import Any

from mcp import types
from mcp.server import Server
from mcp.server.session import ServerSession
from mcp.server.stdio import stdio_server

from mcp_server.tools.analytics import AnalyticsTools
from mcp_server.tools.market_data import MarketDataTools
from mcp_server.tools.portfolio import PortfolioTools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


class FinancialDashboardMCP:
    """Financial Dashboard MCP Server implementation."""

    def __init__(self):
        """Initialize the MCP server with tool instances."""
        self.server = Server("financial-dashboard")
        self.portfolio_tools = PortfolioTools(BACKEND_URL)
        self.market_tools = MarketDataTools(BACKEND_URL)
        self.analytics_tools = AnalyticsTools(BACKEND_URL)

        # Combine all tools
        self.all_tools = []
        self.all_tools.extend(self.portfolio_tools.get_tools())
        self.all_tools.extend(self.market_tools.get_tools())
        self.all_tools.extend(self.analytics_tools.get_tools())

        self._setup_handlers()

    def _setup_handlers(self):
        """Set up MCP server handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available tools."""
            logger.info("Listing available tools")
            return self.all_tools

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict[str, Any] | None
        ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Call a tool with the given arguments."""
            logger.info(f"Calling tool: {name} with arguments: {arguments}")

            if not arguments:
                arguments = {}

            # Route to appropriate tool handler
            try:
                # Portfolio tools
                portfolio_tool_names = [
                    tool.name for tool in self.portfolio_tools.get_tools()
                ]
                if name in portfolio_tool_names:
                    return await self.portfolio_tools.execute_tool(name, arguments)

                # Market data tools
                market_tool_names = [
                    tool.name for tool in self.market_tools.get_tools()
                ]
                if name in market_tool_names:
                    return await self.market_tools.execute_tool(name, arguments)

                # Analytics tools
                analytics_tool_names = [
                    tool.name for tool in self.analytics_tools.get_tools()
                ]
                if name in analytics_tool_names:
                    return await self.analytics_tools.execute_tool(name, arguments)

                # Tool not found
                return [
                    types.TextContent(
                        type="text",
                        text=f"Unknown tool: {name}. Available tools: {[tool.name for tool in self.all_tools]}",
                    )
                ]

            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text", text=f"Error executing tool {name}: {e!s}"
                    )
                ]

        @self.server.get_prompt()
        async def handle_get_prompt(
            name: str, arguments: dict[str, str] | None
        ) -> types.GetPromptResult:
            """Handle prompt requests."""
            if name == "portfolio_analysis":
                return types.GetPromptResult(
                    description="Analyze the user's investment portfolio and provide insights",
                    messages=[
                        types.PromptMessage(
                            role="user",
                            content=types.TextContent(
                                type="text",
                                text="Please analyze my portfolio and provide insights on performance, allocation, and recommendations.",
                            ),
                        )
                    ],
                )

            raise ValueError(f"Unknown prompt: {name}")

        @self.server.list_prompts()
        async def handle_list_prompts() -> list[types.Prompt]:
            """List available prompts."""
            return [
                types.Prompt(
                    name="portfolio_analysis",
                    description="Comprehensive portfolio analysis and recommendations",
                    arguments=[
                        types.PromptArgument(
                            name="focus",
                            description="Focus area for analysis (performance, risk, allocation, opportunities)",
                            required=False,
                        )
                    ],
                )
            ]

    async def run(self):
        """Run the MCP server."""
        logger.info("Starting Financial Dashboard MCP Server")

        try:
            # Run server with stdio transport
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream, write_stream, ServerSession.server_capabilities()
                )
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
        finally:
            # Clean up resources
            await self.portfolio_tools.close()
            await self.market_tools.close()
            await self.analytics_tools.close()


async def main():
    """Main entry point."""
    server_instance = FinancialDashboardMCP()
    await server_instance.run()


if __name__ == "__main__":
    asyncio.run(main())
