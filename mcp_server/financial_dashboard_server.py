#!/usr/bin/env python3
"""MCP Server for Financial Dashboard - Claude Desktop Integration
This provides a proper MCP server that won't crash Claude Desktop.
"""

import asyncio
import logging
import os
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("financial-dashboard-mcp")

# Configuration from environment variables
BASE_URL = os.getenv("FINANCIAL_DASHBOARD_URL", "http://localhost:8000")
TOKEN = os.getenv(
    "FINANCIAL_DASHBOARD_TOKEN",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzIiwiZXhwIjoxNzUyODcxOTM2fQ.ThyBQ0AMuRHb9H7QzoBFf04pRIfxcBrEJ501CxW5FX0",
)
USER_ID = os.getenv("FINANCIAL_DASHBOARD_USER_ID", "3")


class FinancialDashboardMCPServer:
    """MCP Server for Financial Dashboard API."""

    def __init__(self):
        self.server = Server("financial-dashboard")
        self.setup_handlers()

    def setup_handlers(self):
        """Set up MCP server handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """List available tools."""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="get_portfolio_overview",
                        description="Get portfolio overview with total value and allocations",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    ),
                    Tool(
                        name="get_positions",
                        description="Get all portfolio positions",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    ),
                    Tool(
                        name="get_assets",
                        description="Get all available assets",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    ),
                    Tool(
                        name="get_transactions",
                        description="Get transaction history",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "limit": {
                                    "type": "integer",
                                    "description": "Number of transactions to retrieve (default: 10)",
                                }
                            },
                            "required": [],
                        },
                    ),
                    Tool(
                        name="health_check",
                        description="Check if the Financial Dashboard API is healthy",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    ),
                ]
            )

        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool calls."""
            try:
                if request.name == "health_check":
                    return await self._health_check()
                if request.name == "get_portfolio_overview":
                    return await self._get_portfolio_overview()
                if request.name == "get_positions":
                    return await self._get_positions()
                if request.name == "get_assets":
                    return await self._get_assets()
                if request.name == "get_transactions":
                    limit = (
                        request.arguments.get("limit", 10) if request.arguments else 10
                    )
                    return await self._get_transactions(limit)
                return CallToolResult(
                    content=[
                        TextContent(type="text", text=f"Unknown tool: {request.name}")
                    ]
                )
            except Exception as e:
                logger.error(f"Error calling tool {request.name}: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {e!s}")]
                )

    async def _make_request(
        self, endpoint: str, method: str = "GET", params: dict | None = None
    ) -> dict[str, Any]:
        """Make HTTP request to Financial Dashboard API."""
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        }

        url = f"{BASE_URL}{endpoint}"

        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(
                    url, headers=headers, params=params, timeout=10.0
                )
            else:
                response = await client.request(
                    method, url, headers=headers, params=params, timeout=10.0
                )

            response.raise_for_status()
            return response.json()

    async def _health_check(self) -> CallToolResult:
        """Check API health."""
        try:
            data = await self._make_request("/health")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"✅ Financial Dashboard is healthy!\n\nStatus: {data.get('status')}\nService: {data.get('service')}\nVersion: {data.get('version')}\nEnvironment: {data.get('environment')}",
                    )
                ]
            )
        except Exception as e:
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"❌ Health check failed: {e!s}")
                ]
            )

    async def _get_portfolio_overview(self) -> CallToolResult:
        """Get portfolio overview."""
        try:
            data = await self._make_request(f"/api/v1/portfolio/summary/{USER_ID}")

            total_value = data.get("total_value", 0)
            cash_balance = data.get("cash_balance", 0)
            positions_value = data.get("positions_value", 0)

            text = "📊 Portfolio Overview\n\n"
            text += f"💰 Total Value: ${total_value:,.2f}\n"
            text += f"💵 Cash Balance: ${cash_balance:,.2f}\n"
            text += f"📈 Positions Value: ${positions_value:,.2f}\n"

            if "allocations" in data:
                text += "\n🎯 Asset Allocations:\n"
                for allocation in data["allocations"]:
                    text += f"  • {allocation.get('asset_type', 'Unknown')}: {allocation.get('percentage', 0):.1f}%\n"

            return CallToolResult(content=[TextContent(type="text", text=text)])
        except Exception as e:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"❌ Failed to get portfolio overview: {e!s}",
                    )
                ]
            )

    async def _get_positions(self) -> CallToolResult:
        """Get portfolio positions."""
        try:
            data = await self._make_request(
                "/api/v1/positions/", params={"user_id": USER_ID}
            )

            if not data:
                return CallToolResult(
                    content=[TextContent(type="text", text="No positions found.")]
                )

            text = f"📈 Portfolio Positions ({len(data)} positions)\n\n"

            for position in data:
                symbol = position.get("symbol", "Unknown")
                quantity = position.get("quantity", 0)
                avg_cost = position.get("average_cost", 0)
                current_price = position.get("current_price", 0)
                total_value = quantity * current_price if current_price else 0
                unrealized_pnl = (
                    (current_price - avg_cost) * quantity
                    if current_price and avg_cost
                    else 0
                )

                text += f"🏷️ {symbol}\n"
                text += f"   Quantity: {quantity:,.2f}\n"
                text += f"   Avg Cost: ${avg_cost:,.2f}\n"
                text += f"   Current Price: ${current_price:,.2f}\n"
                text += f"   Total Value: ${total_value:,.2f}\n"
                text += f"   P&L: ${unrealized_pnl:,.2f}\n\n"

            return CallToolResult(content=[TextContent(type="text", text=text)])
        except Exception as e:
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"❌ Failed to get positions: {e!s}")
                ]
            )

    async def _get_assets(self) -> CallToolResult:
        """Get available assets."""
        try:
            data = await self._make_request("/api/v1/assets/")

            if not data:
                return CallToolResult(
                    content=[TextContent(type="text", text="No assets found.")]
                )

            text = f"🏦 Available Assets ({len(data)} assets)\n\n"

            for asset in data:
                symbol = asset.get("symbol", "Unknown")
                name = asset.get("name", "Unknown")
                asset_type = asset.get("asset_type", "Unknown")
                current_price = asset.get("current_price", 0)

                text += f"🏷️ {symbol} - {name}\n"
                text += f"   Type: {asset_type}\n"
                text += f"   Price: ${current_price:,.2f}\n\n"

            return CallToolResult(content=[TextContent(type="text", text=text)])
        except Exception as e:
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"❌ Failed to get assets: {e!s}")
                ]
            )

    async def _get_transactions(self, limit: int = 10) -> CallToolResult:
        """Get transaction history."""
        try:
            data = await self._make_request(
                "/api/v1/transactions/", params={"user_id": USER_ID, "limit": limit}
            )

            if not data:
                return CallToolResult(
                    content=[TextContent(type="text", text="No transactions found.")]
                )

            text = f"💼 Recent Transactions (last {len(data)})\n\n"

            for txn in data:
                date = txn.get("transaction_date", "Unknown")
                transaction_type = txn.get("transaction_type", "Unknown")
                symbol = txn.get("symbol", "Unknown")
                quantity = txn.get("quantity", 0)
                price = txn.get("price", 0)
                total = quantity * price

                text += f"📅 {date}\n"
                text += f"   {transaction_type.title()} {quantity:,.2f} {symbol}\n"
                text += f"   Price: ${price:,.2f}\n"
                text += f"   Total: ${total:,.2f}\n\n"

            return CallToolResult(content=[TextContent(type="text", text=text)])
        except Exception as e:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text=f"❌ Failed to get transactions: {e!s}"
                    )
                ]
            )

    async def run(self):
        """Run the MCP server."""
        logger.info("Starting Financial Dashboard MCP Server")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="financial-dashboard",
                    server_version="1.0.0",
                    capabilities={},
                ),
            )


async def main():
    """Main entry point."""
    server = FinancialDashboardMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
