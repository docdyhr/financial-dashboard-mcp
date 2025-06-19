"""MCP tools for market data and analytics."""

import logging
from typing import Any

import httpx
from mcp.types import TextContent, Tool

logger = logging.getLogger(__name__)


class MarketDataTools:
    """Market data and analytics tools for MCP."""

    def __init__(self, backend_url: str = "http://localhost:8000"):
        """Initialize market data tools with backend URL."""
        self.backend_url = backend_url
        # Set up authentication headers
        self.auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzIiwiZXhwIjoxNzUyODcxOTM2fQ.ThyBQ0AMuRHb9H7QzoBFf04pRIfxcBrEJ501CxW5FX0"
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }
        self.http_client = httpx.AsyncClient(timeout=30.0, headers=self.headers)

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()

    def get_tools(self) -> list[Tool]:
        """Get list of market data tools."""
        return [
            Tool(
                name="get_asset_price",
                description="Get current price and basic info for an asset",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "Asset ticker symbol (e.g., AAPL, MSFT, BTC-USD)",
                        }
                    },
                    "required": ["ticker"],
                },
            ),
            Tool(
                name="calculate_performance",
                description="Calculate portfolio performance for a specific time period",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "period": {
                            "type": "string",
                            "enum": ["1D", "1W", "1M", "3M", "6M", "1Y", "YTD"],
                            "description": "Time period for performance calculation",
                        }
                    },
                    "required": ["period"],
                },
            ),
            Tool(
                name="analyze_portfolio_risk",
                description="Analyze portfolio risk metrics and volatility",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "period": {
                            "type": "string",
                            "enum": ["1M", "3M", "6M", "1Y"],
                            "description": "Analysis period",
                            "default": "1Y",
                        }
                    },
                },
            ),
            Tool(
                name="get_market_trends",
                description="Get current market trends and sector performance",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "include_sectors": {
                            "type": "boolean",
                            "description": "Include sector performance breakdown",
                            "default": True,
                        }
                    },
                },
            ),
        ]

    async def execute_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Execute a market data tool."""
        try:
            if name == "get_asset_price":
                return await self._get_asset_price(arguments)
            if name == "calculate_performance":
                return await self._calculate_performance(arguments)
            if name == "analyze_portfolio_risk":
                return await self._analyze_portfolio_risk(arguments)
            if name == "get_market_trends":
                return await self._get_market_trends(arguments)
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return [TextContent(type="text", text=f"Error executing {name}: {e!s}")]

    async def _get_asset_price(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Get asset price information."""
        try:
            ticker = arguments["ticker"].upper()
            response = await self.http_client.get(
                f"{self.backend_url}/api/assets/price/{ticker}"
            )
            response.raise_for_status()
            data = response.json()

            price_info = data.get("price_info", {})
            current_price = price_info.get("current_price", 0.0)
            daily_change = price_info.get("daily_change", 0.0)
            daily_change_pct = price_info.get("daily_change_percent", 0.0)
            volume = price_info.get("volume", 0)
            market_cap = price_info.get("market_cap", 0)
            pe_ratio = price_info.get("pe_ratio", 0.0)

            change_symbol = "+" if daily_change >= 0 else ""

            price_text = f"""**{ticker} - Asset Price Information**

**Current Price:** ${current_price:.2f}
**Daily Change:** {change_symbol}${daily_change:.2f} ({change_symbol}{daily_change_pct:.2f}%)

**Additional Metrics:**
  • Volume: {volume:,} shares
  • Market Cap: ${market_cap:,.0f} (if applicable)
  • P/E Ratio: {pe_ratio:.2f} (if applicable)

*Data updated in real-time from market sources*
"""

            return [TextContent(type="text", text=price_text)]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return [
                    TextContent(
                        type="text",
                        text=f"Asset '{arguments['ticker']}' not found or price data unavailable.",
                    )
                ]
            return [
                TextContent(
                    type="text",
                    text=f"Error retrieving price data: {e.response.status_code}",
                )
            ]
        except Exception as e:
            return [
                TextContent(type="text", text=f"Error retrieving asset price: {e!s}")
            ]

    async def _calculate_performance(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Calculate portfolio performance."""
        try:
            period = arguments["period"]
            response = await self.http_client.get(
                f"{self.backend_url}/api/portfolio/performance"
            )
            response.raise_for_status()
            data = response.json()

            if period not in data:
                return [
                    TextContent(
                        type="text",
                        text=f"Performance data for period '{period}' is not available.",
                    )
                ]

            period_data = data[period]
            return_pct = period_data.get("return_percentage", 0.0)
            value_change = period_data.get("value_change", 0.0)
            start_value = period_data.get("start_value", 0.0)
            end_value = period_data.get("end_value", 0.0)

            change_symbol = "+" if value_change >= 0 else ""
            performance_indicator = "📈" if value_change >= 0 else "📉"

            performance_text = f"""**Portfolio Performance - {period}** {performance_indicator}

**Return:** {change_symbol}{return_pct:.2f}%
**Value Change:** {change_symbol}${value_change:,.2f}

**Period Details:**
  • Starting Value: ${start_value:,.2f}
  • Ending Value: ${end_value:,.2f}
  • Period: {period}

"""
            # Add context based on performance
            if abs(return_pct) < 1:
                performance_text += "*Performance is relatively flat for this period.*"
            elif return_pct > 10:
                performance_text += "*Strong positive performance! 🎉*"
            elif return_pct > 5:
                performance_text += "*Good positive performance.*"
            elif return_pct < -10:
                performance_text += (
                    "*Significant decline - consider reviewing positions.*"
                )
            elif return_pct < -5:
                performance_text += "*Notable decline in portfolio value.*"

            return [TextContent(type="text", text=performance_text)]
        except httpx.RequestError as e:
            return [
                TextContent(type="text", text=f"Error connecting to backend: {e!s}")
            ]
        except Exception as e:
            return [
                TextContent(type="text", text=f"Error calculating performance: {e!s}")
            ]

    async def _analyze_portfolio_risk(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Analyze portfolio risk metrics."""
        try:
            # This is a placeholder implementation - in a real system, this would
            # calculate actual risk metrics like Sharpe ratio, beta, VaR, etc.
            period = arguments.get("period", "1Y")

            # Get current positions for diversification analysis
            positions_response = await self.http_client.get(
                f"{self.backend_url}/api/portfolio/positions"
            )
            if positions_response.status_code != 200:
                return [
                    TextContent(
                        type="text",
                        text="Unable to retrieve portfolio data for risk analysis.",
                    )
                ]

            positions_data = positions_response.json()
            positions = positions_data.get("positions", [])

            # Calculate basic risk metrics
            num_positions = len(positions)
            total_value = sum(pos.get("total_value", 0) for pos in positions)

            # Calculate concentration risk
            max_position_value = max(
                (pos.get("total_value", 0) for pos in positions), default=0
            )
            concentration_pct = (
                (max_position_value / total_value * 100) if total_value > 0 else 0
            )

            # Risk assessment
            if num_positions <= 2:
                diversification_risk = "HIGH - Very few positions"
            elif num_positions <= 5:
                diversification_risk = "MEDIUM - Limited diversification"
            elif num_positions <= 10:
                diversification_risk = "MODERATE - Reasonable diversification"
            else:
                diversification_risk = "LOW - Well diversified"

            if concentration_pct > 50:
                concentration_risk = "HIGH - Single position dominates"
            elif concentration_pct > 30:
                concentration_risk = "MEDIUM - High concentration"
            elif concentration_pct > 20:
                concentration_risk = "MODERATE - Some concentration"
            else:
                concentration_risk = "LOW - Well balanced"

            risk_text = f"""**Portfolio Risk Analysis ({period})**

**Diversification Metrics:**
  • Number of Positions: {num_positions}
  • Diversification Risk: {diversification_risk}
  • Largest Position: {concentration_pct:.1f}% of portfolio
  • Concentration Risk: {concentration_risk}

**Risk Assessment:**
  • **Overall Risk Level:** {"HIGH" if concentration_pct > 40 or num_positions < 3 else "MODERATE" if concentration_pct > 25 or num_positions < 6 else "LOW"}

**Recommendations:**
"""
            if num_positions < 5:
                risk_text += (
                    "  • Consider adding more positions to improve diversification\n"
                )
            if concentration_pct > 30:
                risk_text += "  • Consider reducing position size of largest holding\n"
            if num_positions >= 5 and concentration_pct <= 25:
                risk_text += (
                    "  • Portfolio shows good diversification characteristics\n"
                )

            risk_text += "\n*Note: This is a basic risk assessment. Consider consulting with a financial advisor for comprehensive risk analysis.*"

            return [TextContent(type="text", text=risk_text)]
        except Exception as e:
            return [
                TextContent(type="text", text=f"Error analyzing portfolio risk: {e!s}")
            ]

    async def _get_market_trends(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Get market trends information."""
        try:
            # This is a placeholder implementation - in a real system, this would
            # fetch current market indices, sector performance, etc.

            trends_text = """**Current Market Trends** 📊

**Major Indices (Last Close):**
  • S&P 500: +0.45% (📈)
  • NASDAQ: +0.72% (📈)
  • Dow Jones: +0.23% (📈)
  • Russell 2000: -0.12% (📉)

**Market Sentiment:** Cautiously Optimistic
  • VIX (Fear Index): 18.5 (Moderate)
  • 10Y Treasury Yield: 4.25%
  • USD Index: 103.2

"""
            if arguments.get("include_sectors", True):
                trends_text += """**Sector Performance (Today):**
  • Technology: +1.2% (🔥 Leading)
  • Healthcare: +0.8%
  • Financials: +0.5%
  • Energy: +0.3%
  • Consumer Discretionary: -0.2%
  • Utilities: -0.4%
  • Real Estate: -0.6%

**Key Market Themes:**
  • AI and Technology stocks continue strong performance
  • Interest rate expectations driving bond yields
  • Energy sector showing mixed signals
  • Flight to quality in uncertain times
"""

            trends_text += """
*Data is simulated for demonstration. In production, this would connect to real market data feeds.*"""

            return [TextContent(type="text", text=trends_text)]
        except Exception as e:
            return [
                TextContent(type="text", text=f"Error retrieving market trends: {e!s}")
            ]
