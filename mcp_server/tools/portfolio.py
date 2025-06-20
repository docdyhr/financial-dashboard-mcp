"""MCP tools for portfolio management."""

import logging
from typing import Any

import httpx
from mcp.types import TextContent, Tool

from mcp_server.auth import get_auth_manager

logger = logging.getLogger(__name__)


class PortfolioTools:
    """Portfolio management tools for MCP."""

    def __init__(self, backend_url: str = "http://localhost:8000"):
        """Initialize portfolio tools with backend URL."""
        self.backend_url = backend_url
        self.auth_manager = get_auth_manager(backend_url)
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        """Close HTTP client."""
        await self.http_client.aclose()

    def get_tools(self) -> list[Tool]:
        """Get list of portfolio tools."""
        return [
            Tool(
                name="get_positions",
                description="Retrieve current portfolio positions with real-time data",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "include_cash": {
                            "type": "boolean",
                            "description": "Include cash positions in the result",
                            "default": True,
                        }
                    },
                },
            ),
            Tool(
                name="get_portfolio_summary",
                description="Get comprehensive portfolio overview and key metrics",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "include_performance": {
                            "type": "boolean",
                            "description": "Include performance metrics in summary",
                            "default": True,
                        }
                    },
                },
            ),
            Tool(
                name="get_allocation",
                description="Get current portfolio allocation breakdown by asset type",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="add_position",
                description="Add a new position to the portfolio",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "Asset ticker symbol (e.g., AAPL, MSFT)",
                        },
                        "quantity": {
                            "type": "number",
                            "description": "Number of shares to add",
                        },
                        "purchase_price": {
                            "type": "number",
                            "description": "Price per share at purchase",
                        },
                        "purchase_date": {
                            "type": "string",
                            "format": "date",
                            "description": "Purchase date in YYYY-MM-DD format",
                        },
                    },
                    "required": ["ticker", "quantity", "purchase_price"],
                },
            ),
            Tool(
                name="update_position",
                description="Update an existing portfolio position",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "position_id": {
                            "type": "integer",
                            "description": "ID of the position to update",
                        },
                        "quantity": {
                            "type": "number",
                            "description": "New quantity of shares",
                        },
                        "notes": {
                            "type": "string",
                            "description": "Additional notes about the position",
                        },
                    },
                    "required": ["position_id"],
                },
            ),
        ]

    async def execute_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Execute a portfolio tool."""
        try:
            if name == "get_positions":
                return await self._get_positions(arguments)
            if name == "get_portfolio_summary":
                return await self._get_portfolio_summary(arguments)
            if name == "get_allocation":
                return await self._get_allocation(arguments)
            if name == "add_position":
                return await self._add_position(arguments)
            if name == "update_position":
                return await self._update_position(arguments)
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return [TextContent(type="text", text=f"Error executing {name}: {e!s}")]

    async def _get_positions(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Get current portfolio positions."""
        try:
            # Get authenticated headers and user_id
            headers = await self.auth_manager.get_headers()
            user_id = await self.auth_manager.get_user_id()

            if not user_id:
                return [
                    TextContent(
                        type="text",
                        text="Authentication failed. Please check your credentials.",
                    )
                ]

            response = await self.http_client.get(
                f"{self.backend_url}/api/v1/positions/?user_id={user_id}",
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

            positions_text = "**Current Portfolio Positions:**\n\n"
            total_value = 0.0

            # Handle the paginated response structure
            positions = data.get("data", []) if data.get("success") else []

            if not positions:
                return [
                    TextContent(
                        type="text",
                        text="**No positions found in your portfolio.**\n\nTo get started, use the `add_position` tool to add your first investment!",
                    )
                ]

            for position in positions:
                # Get asset info from nested asset object
                asset = position.get("asset", {})
                ticker = asset.get("ticker", "N/A")
                name = asset.get("name", "Unknown")

                # Convert string values to numbers with safe fallbacks
                try:
                    quantity = float(position.get("quantity", 0))
                except (ValueError, TypeError):
                    quantity = 0.0

                try:
                    current_price = float(position.get("current_price") or 0)
                except (ValueError, TypeError):
                    current_price = 0.0

                try:
                    total_pos_value = float(position.get("current_value") or 0)
                except (ValueError, TypeError):
                    total_pos_value = 0.0

                try:
                    daily_change = float(position.get("daily_change") or 0)
                except (ValueError, TypeError):
                    daily_change = 0.0

                try:
                    daily_change_pct = float(position.get("daily_change_percent") or 0)
                except (ValueError, TypeError):
                    daily_change_pct = 0.0

                change_symbol = "+" if daily_change >= 0 else ""
                positions_text += f"**{ticker}** ({name})\n"
                positions_text += f"  • Quantity: {quantity:,.0f} shares\n"
                positions_text += f"  • Current Price: ${current_price:.2f}\n"
                positions_text += f"  • Total Value: ${total_pos_value:,.2f}\n"
                positions_text += f"  • Daily Change: {change_symbol}{daily_change:.2f} ({change_symbol}{daily_change_pct:.2f}%)\n\n"

                total_value += total_pos_value

            if arguments.get("include_cash", True):
                # Get cash balance from summary
                summary_response = await self.http_client.get(
                    f"{self.backend_url}/api/v1/portfolio/summary/{user_id}",
                    headers=headers,
                )
                if summary_response.status_code == 200:
                    summary_data = summary_response.json()
                    data = summary_data.get("data", {})
                    cash_balance = float(data.get("cash_balance", 0.0))
                    if cash_balance > 0:
                        positions_text += "**CASH**\n"
                        positions_text += f"  • Balance: ${cash_balance:,.2f}\n\n"
                        total_value += cash_balance

            positions_text += f"**Total Portfolio Value: ${total_value:,.2f}**"

            return [TextContent(type="text", text=positions_text)]
        except httpx.RequestError as e:
            return [
                TextContent(type="text", text=f"Error connecting to backend: {e!s}")
            ]
        except Exception as e:
            return [TextContent(type="text", text=f"Error retrieving positions: {e!s}")]

    async def _get_portfolio_summary(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Get portfolio summary."""
        try:
            # Get authenticated headers and user_id
            headers = await self.auth_manager.get_headers()
            user_id = await self.auth_manager.get_user_id()

            if not user_id:
                return [
                    TextContent(
                        type="text",
                        text="Authentication failed. Please check your credentials.",
                    )
                ]

            # Get summary data
            summary_response = await self.http_client.get(
                f"{self.backend_url}/api/v1/portfolio/summary/{user_id}",
                headers=headers,
            )
            summary_response.raise_for_status()
            summary_data = summary_response.json()

            # Get performance data if requested
            performance_text = ""
            if arguments.get("include_performance", True):
                try:
                    perf_response = await self.http_client.get(
                        f"{self.backend_url}/api/v1/portfolio/performance/{user_id}",
                        headers=headers,
                    )
                    if perf_response.status_code == 200:
                        perf_data = perf_response.json()
                        performance_text = "\n**Performance Metrics:**\n"
                        for period, metrics in perf_data.items():
                            if isinstance(metrics, dict):
                                return_pct = metrics.get("return_percentage", 0.0)
                                value_change = metrics.get("value_change", 0.0)
                                change_symbol = "+" if value_change >= 0 else ""
                                performance_text += f"  • {period}: {change_symbol}{return_pct:.2f}% ({change_symbol}${value_change:,.2f})\n"
                except Exception:
                    performance_text = "\n*Performance data unavailable*\n"

            # Format summary - extract data from nested structure
            data = summary_data.get("data", {})
            total_value = float(data.get("total_value", 0.0))
            cash_balance = float(data.get("cash_balance", 0.0))
            daily_change = float(data.get("daily_change") or 0.0)
            daily_change_pct = float(data.get("daily_change_percent") or 0.0)
            total_assets = data.get("total_assets", 0)

            change_symbol = "+" if daily_change >= 0 else ""

            summary_text = f"""**Portfolio Summary**

**Total Value:** ${total_value:,.2f}
**Cash Balance:** ${cash_balance:,.2f}
**Total Assets:** {total_assets}

**Today's Performance:**
  • Change: {change_symbol}${daily_change:.2f} ({change_symbol}{daily_change_pct:.2f}%)

{performance_text}

**Investment Allocation:**
  • Invested: ${total_value - cash_balance:,.2f} ({((total_value - cash_balance) / total_value * 100) if total_value > 0 else 0:.1f}%)
  • Cash: ${cash_balance:,.2f} ({(cash_balance / total_value * 100) if total_value > 0 else 0:.1f}%)
"""

            return [TextContent(type="text", text=summary_text)]
        except httpx.RequestError as e:
            return [
                TextContent(type="text", text=f"Error connecting to backend: {e!s}")
            ]
        except Exception as e:
            return [TextContent(type="text", text=f"Error retrieving summary: {e!s}")]

    async def _get_allocation(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Get portfolio allocation breakdown."""
        try:
            # Get authenticated headers and user_id
            headers = await self.auth_manager.get_headers()
            user_id = await self.auth_manager.get_user_id()

            if not user_id:
                return [
                    TextContent(
                        type="text",
                        text="Authentication failed. Please check your credentials.",
                    )
                ]

            response = await self.http_client.get(
                f"{self.backend_url}/api/v1/portfolio/allocation/{user_id}",
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

            allocation_text = "**Portfolio Allocation:**\n\n"

            for allocation in data.get("allocation", []):
                asset_type = allocation.get("asset_type", "Unknown")
                percentage = allocation.get("percentage", 0.0)
                value = allocation.get("value", 0.0)
                allocation_text += (
                    f"**{asset_type}:** {percentage:.1f}% (${value:,.2f})\n"
                )

            return [TextContent(type="text", text=allocation_text)]
        except httpx.RequestError as e:
            return [
                TextContent(type="text", text=f"Error connecting to backend: {e!s}")
            ]
        except Exception as e:
            return [
                TextContent(type="text", text=f"Error retrieving allocation: {e!s}")
            ]

    async def _add_position(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Add a new position."""
        try:
            # Get authenticated headers and user_id
            headers = await self.auth_manager.get_headers()
            user_id = await self.auth_manager.get_user_id()

            if not user_id:
                return [
                    TextContent(
                        type="text",
                        text="Authentication failed. Please check your credentials.",
                    )
                ]

            ticker = arguments["ticker"].upper()
            quantity = float(arguments["quantity"])
            purchase_price = float(arguments["purchase_price"])

            # First, check if asset exists or create it
            asset_response = await self.http_client.get(
                f"{self.backend_url}/api/v1/assets/?query={ticker}", headers=headers
            )
            asset_response.raise_for_status()
            asset_data = asset_response.json()

            asset_id = None
            if asset_data.get("data") and len(asset_data["data"]) > 0:
                asset_id = asset_data["data"][0]["id"]
            else:
                # Create new asset
                asset_create_data = {
                    "ticker": ticker,
                    "name": f"{ticker} Stock",
                    "asset_type": "stock",
                    "category": "equity",
                    "currency": "USD",
                }

                create_response = await self.http_client.post(
                    f"{self.backend_url}/api/v1/assets/",
                    json=asset_create_data,
                    headers=headers,
                )
                create_response.raise_for_status()
                created_asset = create_response.json()
                asset_id = created_asset["data"]["id"]

            # Prepare position data with correct schema
            position_data = {
                "user_id": user_id,
                "asset_id": asset_id,
                "quantity": str(quantity),
                "average_cost_per_share": str(purchase_price),
                "total_cost_basis": str(quantity * purchase_price),
            }

            if "purchase_date" in arguments:
                position_data["purchase_date"] = arguments["purchase_date"]

            response = await self.http_client.post(
                f"{self.backend_url}/api/v1/positions/",
                json=position_data,
                headers=headers,
            )
            response.raise_for_status()

            total_cost = quantity * purchase_price

            success_text = f"""**Position Added Successfully!**

**Asset:** {ticker}
**Quantity:** {quantity:,.0f} shares
**Purchase Price:** ${purchase_price:.2f}
**Total Cost:** ${total_cost:,.2f}

The position has been added to your portfolio and will be included in future calculations.
"""

            return [TextContent(type="text", text=success_text)]
        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", str(e))
            except Exception as ex:
                import logging

                logging.exception(
                    "Error parsing error response in add position: %s", ex
                )
                error_detail = str(e)
            return [
                TextContent(type="text", text=f"Error adding position: {error_detail}")
            ]
        except Exception as e:
            return [TextContent(type="text", text=f"Error adding position: {e!s}")]

    async def _update_position(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Update an existing position."""
        try:
            # Get authenticated headers
            headers = await self.auth_manager.get_headers()

            position_id = arguments["position_id"]
            update_data = {}

            if "quantity" in arguments:
                update_data["quantity"] = float(arguments["quantity"])
            if "notes" in arguments:
                update_data["notes"] = arguments["notes"]

            response = await self.http_client.put(
                f"{self.backend_url}/api/v1/positions/{position_id}",
                json=update_data,
                headers=headers,
            )
            response.raise_for_status()

            success_text = f"""**Position Updated Successfully!**

Position ID {position_id} has been updated with the following changes:
"""
            if "quantity" in update_data:
                success_text += (
                    f"• New Quantity: {update_data['quantity']:,.0f} shares\n"
                )
            if "notes" in update_data:
                success_text += f"• Notes: {update_data['notes']}\n"

            return [TextContent(type="text", text=success_text)]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return [
                    TextContent(
                        type="text",
                        text=f"Position with ID {arguments['position_id']} not found.",
                    )
                ]
            error_detail = str(e)
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", str(e))
            except Exception as ex:  # nosec
                import logging

                logging.exception(
                    "Error parsing error response in update position: %s", ex
                )
            return [
                TextContent(
                    type="text", text=f"Error updating position: {error_detail}"
                )
            ]
        except Exception as e:
            return [TextContent(type="text", text=f"Error updating position: {e!s}")]
