#!/usr/bin/env python3
"""Simple, working MCP server for Financial Dashboard."""

import asyncio
import logging
import sys

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("simple-financial-mcp")

# Configuration
BACKEND_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzIiwiZXhwIjoxNzUyODcxOTM2fQ.ThyBQ0AMuRHb9H7QzoBFf04pRIfxcBrEJ501CxW5FX0"
USER_ID = "3"

# Create the server
server = Server("financial-dashboard")


@server.list_tools()
async def list_tools() -> ListToolsResult:
    """List available tools."""
    return ListToolsResult(
        tools=[
            Tool(
                name="get_portfolio_summary",
                description="Get portfolio overview with total value and allocations",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="get_positions",
                description="Get all portfolio positions",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="health_check",
                description="Check if the Financial Dashboard API is healthy",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
        ]
    )


@server.call_tool()
async def call_tool(request: CallToolRequest) -> CallToolResult:
    """Handle tool calls."""
    logger.info(f"Tool called: {request.name}")

    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient() as client:
            if request.name == "health_check":
                response = await client.get(f"{BACKEND_URL}/health", headers=headers)
                data = response.json()
                text = f"✅ API Status: {data.get('status', 'unknown')}\nService: {data.get('service', 'unknown')}\nEnvironment: {data.get('environment', 'unknown')}"

            elif request.name == "get_portfolio_summary":
                response = await client.get(
                    f"{BACKEND_URL}/api/v1/portfolio/summary/{USER_ID}", headers=headers
                )
                response.raise_for_status()
                data = response.json()

                if data.get("success"):
                    portfolio_data = data["data"]
                    text = "📊 Portfolio Summary\n\n"
                    text += f"💰 Total Value: ${float(portfolio_data.get('total_value', 0)):,.2f}\n"
                    text += f"💵 Cash Balance: ${float(portfolio_data.get('cash_balance', 0)):,.2f}\n"
                    text += f"📈 Total Gain/Loss: ${float(portfolio_data.get('total_gain_loss', 0)):,.2f}\n"
                    text += f"📊 Gain/Loss %: {float(portfolio_data.get('total_gain_loss_percent', 0)):.2f}%\n"
                    text += f"🏷️ Total Positions: {portfolio_data.get('total_positions', 0)}\n"
                else:
                    text = f"❌ Error: {data.get('message', 'Unknown error')}"

            elif request.name == "get_positions":
                response = await client.get(
                    f"{BACKEND_URL}/api/v1/positions/?user_id={USER_ID}",
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                if data.get("success") and data.get("data"):
                    positions = data["data"]
                    text = f"📈 Portfolio Positions ({len(positions)} positions)\n\n"

                    for position in positions:
                        asset = position.get("asset", {})
                        symbol = asset.get("ticker", "Unknown")
                        name = asset.get("name", "Unknown")
                        quantity = float(position.get("quantity", 0))
                        current_value = float(position.get("current_value", 0))
                        unrealized_gain = float(position.get("unrealized_gain_loss", 0))

                        text += f"🏷️ {symbol} - {name}\n"
                        text += f"   Quantity: {quantity:,.2f}\n"
                        text += f"   Value: ${current_value:,.2f}\n"
                        text += f"   P&L: ${unrealized_gain:,.2f}\n\n"
                else:
                    text = "No positions found."

            else:
                text = f"Unknown tool: {request.name}"

        return CallToolResult(content=[TextContent(type="text", text=text)])

    except Exception as e:
        logger.error(f"Error in tool {request.name}: {e}")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e!s}")])


async def main():
    """Run the server."""
    logger.info("Starting Simple Financial Dashboard MCP Server")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


if __name__ == "__main__":
    asyncio.run(main())
