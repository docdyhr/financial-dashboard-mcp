"""MCP tools for AI-powered analytics and recommendations."""

import logging
from typing import Any

import httpx
from mcp.types import TextContent, Tool

logger = logging.getLogger(__name__)


class AnalyticsTools:
    """AI-powered analytics and recommendation tools for MCP."""

    def __init__(self, backend_url: str = "http://localhost:8000") -> None:
        """Initialize analytics tools with backend URL."""
        self.backend_url = backend_url
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()

    def get_tools(self) -> list[Tool]:
        """Get list of analytics tools."""
        return [
            Tool(
                name="recommend_allocation",
                description="Get AI-powered portfolio allocation recommendations",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "risk_tolerance": {
                            "type": "string",
                            "enum": ["conservative", "moderate", "aggressive"],
                            "description": "Investor risk tolerance level",
                        },
                        "investment_horizon": {
                            "type": "string",
                            "enum": ["short", "medium", "long"],
                            "description": "Investment time horizon",
                            "default": "medium",
                        },
                        "target_amount": {
                            "type": "number",
                            "description": "Target portfolio value (optional)",
                        },
                    },
                    "required": ["risk_tolerance"],
                },
            ),
            Tool(
                name="analyze_opportunity",
                description="Find investment opportunities based on criteria",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "criteria": {
                            "type": "string",
                            "description": "Investment criteria (e.g., 'growth stocks', "
                            "'dividend stocks', 'tech sector')",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of opportunities to return",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 10,
                        },
                    },
                    "required": ["criteria"],
                },
            ),
            Tool(
                name="rebalance_portfolio",
                description="Generate portfolio rebalancing recommendations",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "target_allocation": {
                            "type": "object",
                            "description": "Target allocation percentages",
                            "properties": {
                                "stocks": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 100,
                                },
                                "bonds": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 100,
                                },
                                "cash": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 100,
                                },
                                "other": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 100,
                                },
                            },
                        },
                        "rebalance_threshold": {
                            "type": "number",
                            "description": "Minimum percentage deviation to trigger rebalancing",
                            "default": 5.0,
                            "minimum": 1.0,
                            "maximum": 20.0,
                        },
                    },
                },
            ),
            Tool(
                name="generate_insights",
                description="Generate AI-powered portfolio insights and recommendations",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "focus_area": {
                            "type": "string",
                            "enum": [
                                "performance",
                                "risk",
                                "diversification",
                                "opportunities",
                                "all",
                            ],
                            "description": "Area to focus insights on",
                            "default": "all",
                        }
                    },
                },
            ),
        ]

    async def execute_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Execute an analytics tool."""
        try:
            if name == "recommend_allocation":
                return await self._recommend_allocation(arguments)
            if name == "analyze_opportunity":
                return await self._analyze_opportunity(arguments)
            if name == "rebalance_portfolio":
                return await self._rebalance_portfolio(arguments)
            if name == "generate_insights":
                return await self._generate_insights(arguments)
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            logger.exception("Error executing tool %s", name)
            return [TextContent(type="text", text=f"Error executing {name}: {e!s}")]

    async def _recommend_allocation(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Generate allocation recommendations."""
        risk_tolerance = arguments["risk_tolerance"]
        investment_horizon = arguments.get("investment_horizon", "medium")
        target_amount = arguments.get("target_amount")

        # Base allocations based on risk tolerance
        base_allocations = {
            "conservative": {"stocks": 30, "bonds": 60, "cash": 10},
            "moderate": {"stocks": 60, "bonds": 30, "cash": 10},
            "aggressive": {"stocks": 80, "bonds": 15, "cash": 5},
        }

        allocation = base_allocations[risk_tolerance].copy()

        # Adjust for investment horizon
        if investment_horizon == "long":
            allocation["stocks"] = min(allocation["stocks"] + 10, 90)
            allocation["bonds"] = max(allocation["bonds"] - 8, 5)
            allocation["cash"] = max(allocation["cash"] - 2, 5)
        elif investment_horizon == "short":
            allocation["stocks"] = max(allocation["stocks"] - 15, 20)
            allocation["bonds"] = min(allocation["bonds"] + 10, 70)
            allocation["cash"] = min(allocation["cash"] + 5, 15)

        # Get current allocation for comparison
        try:
            current_response = await self.http_client.get(
                f"{self.backend_url}/api/portfolio/allocation"
            )
            current_allocation: dict[str, float] = {}
            if current_response.status_code == 200:
                current_data = current_response.json()
                for item in current_data.get("allocation", []):
                    asset_type = item.get("asset_type", "").lower()
                    percentage = item.get("percentage", 0.0)
                    if "stock" in asset_type or "equity" in asset_type:
                        current_allocation["stocks"] = (
                            current_allocation.get("stocks", 0) + percentage
                        )
                    elif "bond" in asset_type or "fixed" in asset_type:
                        current_allocation["bonds"] = (
                            current_allocation.get("bonds", 0) + percentage
                        )
                    elif "cash" in asset_type:
                        current_allocation["cash"] = (
                            current_allocation.get("cash", 0) + percentage
                        )
        except Exception:
            current_allocation = {}

        recommendation_text = f"""**Portfolio Allocation Recommendation** 🎯

**Investment Profile:**
  • Risk Tolerance: {risk_tolerance.title()}
  • Investment Horizon: {investment_horizon.title()}-term

**Recommended Allocation:**
  • **Stocks:** {allocation['stocks']}%
  • **Bonds:** {allocation['bonds']}%
  • **Cash:** {allocation['cash']}%

"""

        if current_allocation:
            recommendation_text += "**Current vs Recommended:**\n"
            for asset_type in ["stocks", "bonds", "cash"]:
                current = current_allocation.get(asset_type, 0)
                recommended = allocation[asset_type]
                diff = recommended - current
                arrow = "↗️" if diff > 2 else "↘️" if diff < -2 else "➡️"
                recommendation_text += f"  • {asset_type.title()}: {current:.1f}% → {recommended}% {arrow}\n"

        if target_amount:
            recommendation_text += (
                f"\n**Target Portfolio Value: ${target_amount:,.0f}**\n"
            )
            for asset_type, pct in allocation.items():
                target_value = target_amount * pct / 100
                recommendation_text += (
                    f"  • {asset_type.title()}: ${target_value:,.0f}\n"
                )

        recommendation_text += """
**Key Principles:**
  • Diversification reduces risk
  • Align allocation with your risk tolerance
  • Rebalance periodically to maintain target allocation
  • Consider tax implications when rebalancing

*This is a general recommendation. Consider consulting with a financial advisor for personalized advice.*
"""

        return [TextContent(type="text", text=recommendation_text)]

    async def _analyze_opportunity(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Analyze investment opportunities."""
        criteria = arguments["criteria"].lower()
        max_results = arguments.get("max_results", 5)

        # This is a demo implementation - in production, this would use
        # real market data, screening tools, and ML models
        opportunities: list[dict[str, Any]] = []

        if "growth" in criteria or "tech" in criteria:
            opportunities.extend(
                [
                    {
                        "ticker": "AAPL",
                        "name": "Apple Inc.",
                        "reason": "Strong revenue growth and innovation in services",
                        "score": 8.5,
                    },
                    {
                        "ticker": "MSFT",
                        "name": "Microsoft Corporation",
                        "reason": "Cloud dominance and AI integration",
                        "score": 9.0,
                    },
                    {
                        "ticker": "NVDA",
                        "name": "NVIDIA Corporation",
                        "reason": "AI chip market leader with strong fundamentals",
                        "score": 8.8,
                    },
                ]
            )

        if "dividend" in criteria or "income" in criteria:
            opportunities.extend(
                [
                    {
                        "ticker": "JNJ",
                        "name": "Johnson & Johnson",
                        "reason": "Consistent dividend growth for 60+ years",
                        "score": 8.2,
                    },
                    {
                        "ticker": "KO",
                        "name": "The Coca-Cola Company",
                        "reason": "Stable cash flows and reliable dividend",
                        "score": 7.8,
                    },
                    {
                        "ticker": "PG",
                        "name": "Procter & Gamble",
                        "reason": "Defensive consumer staples with growing dividend",
                        "score": 8.0,
                    },
                ]
            )

        if "value" in criteria or "undervalued" in criteria:
            opportunities.extend(
                [
                    {
                        "ticker": "BRK.B",
                        "name": "Berkshire Hathaway",
                        "reason": "Trading below intrinsic value with strong management",
                        "score": 8.3,
                    },
                    {
                        "ticker": "JPM",
                        "name": "JPMorgan Chase",
                        "reason": "Strong balance sheet, trading at attractive valuation",
                        "score": 7.9,
                    },
                ]
            )

        # Remove duplicates and sort by score
        seen: set[str] = set()
        unique_opportunities: list[dict[str, Any]] = []
        for opp in opportunities:
            if opp["ticker"] not in seen:
                unique_opportunities.append(opp)
                seen.add(opp["ticker"])

        unique_opportunities.sort(key=lambda x: float(x["score"]), reverse=True)
        unique_opportunities = unique_opportunities[:max_results]

        if not unique_opportunities:
            return [
                TextContent(
                    type="text",
                    text=f"""**Investment Opportunity Analysis**

No specific opportunities found for criteria: "{criteria}"

**Suggestions:**
  • Try broader criteria like "growth", "dividend", or "value"
  • Consider diversifying across multiple sectors
  • Look for opportunities in emerging markets or sectors

*This analysis uses simulated data for demonstration purposes.*""",
                )
            ]

        opportunity_text = f"""**Investment Opportunities: {criteria.title()}** 💡

Found {len(unique_opportunities)} opportunities matching your criteria:

"""

        for i, opp in enumerate(unique_opportunities, 1):
            score_stars = "⭐" * int(float(opp["score"]) / 2)
            opportunity_text += f"""**{i}. {opp['ticker']} - {opp['name']}**
  • Investment Score: {opp['score']}/10 {score_stars}
  • Rationale: {opp['reason']}

"""

        opportunity_text += """**Next Steps:**
  • Research each opportunity thoroughly
  • Check current valuation and entry points
  • Consider position sizing within your portfolio
  • Monitor for good entry opportunities

*Always do your own research before investing. Past performance doesn't guarantee future results.*
"""

        return [TextContent(type="text", text=opportunity_text)]

    async def _rebalance_portfolio(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Generate rebalancing recommendations."""
        target_allocation = arguments.get("target_allocation", {})
        threshold = arguments.get("rebalance_threshold", 5.0)

        # Get current portfolio data
        try:
            allocation_response = await self.http_client.get(
                f"{self.backend_url}/api/portfolio/allocation"
            )
            summary_response = await self.http_client.get(
                f"{self.backend_url}/api/portfolio/summary"
            )

            if (
                allocation_response.status_code != 200
                or summary_response.status_code != 200
            ):
                return [
                    TextContent(
                        type="text",
                        text="Unable to retrieve current portfolio data for rebalancing analysis.",
                    )
                ]

            allocation_data = allocation_response.json()
            summary_data = summary_response.json()
            total_value = summary_data.get("total_value", 0.0)

            # Process current allocation
            current_allocation: dict[str, float] = {}
            for item in allocation_data.get("allocation", []):
                asset_type = item.get("asset_type", "").lower()
                percentage = item.get("percentage", 0.0)

                if "stock" in asset_type or "equity" in asset_type:
                    current_allocation["stocks"] = (
                        current_allocation.get("stocks", 0) + percentage
                    )
                elif "bond" in asset_type or "fixed" in asset_type:
                    current_allocation["bonds"] = (
                        current_allocation.get("bonds", 0) + percentage
                    )
                elif "cash" in asset_type:
                    current_allocation["cash"] = (
                        current_allocation.get("cash", 0) + percentage
                    )

        except Exception as e:
            return [
                TextContent(type="text", text=f"Error retrieving portfolio data: {e!s}")
            ]

        if not target_allocation:
            # Use default moderate allocation if none specified
            target_allocation = {"stocks": 60, "bonds": 30, "cash": 10}

        rebalance_text = f"""**Portfolio Rebalancing Analysis** ⚖️

**Rebalancing Threshold:** {threshold}% deviation

**Current vs Target Allocation:**
"""

        needs_rebalancing = False
        rebalancing_actions: list[dict[str, Any]] = []

        for asset_type in ["stocks", "bonds", "cash"]:
            current_pct = current_allocation.get(asset_type, 0)
            target_pct = target_allocation.get(asset_type, 0)
            deviation = current_pct - target_pct
            current_value = total_value * current_pct / 100
            target_value = total_value * target_pct / 100
            diff_value = target_value - current_value

            status = "✅" if abs(deviation) < threshold else "🔄"
            if abs(deviation) >= threshold:
                needs_rebalancing = True
                action = "Buy" if diff_value > 0 else "Sell"
                rebalancing_actions.append(
                    {
                        "asset_type": asset_type,
                        "action": action,
                        "amount": abs(diff_value),
                    }
                )

            rebalance_text += f"""
**{asset_type.title()}:** {status}
  • Current: {current_pct:.1f}% (${current_value:,.0f})
  • Target: {target_pct:.1f}% (${target_value:,.0f})
  • Deviation: {deviation:+.1f}%"""

        if needs_rebalancing:
            rebalance_text += "\n\n**Recommended Actions:**\n"
            for action_item in rebalancing_actions:
                rebalance_text += f"  • {action_item['action']} ${action_item['amount']:,.0f} in {action_item['asset_type']}\n"

            rebalance_text += """
**Rebalancing Tips:**
  • Consider tax implications of selling positions
  • Use new contributions to rebalance when possible
  • Don't over-rebalance - small deviations are normal
  • Consider transaction costs in your decisions
"""
        else:
            rebalance_text += "\n\n**Portfolio Status:** ✅ Well balanced\n"
            rebalance_text += "Your portfolio allocation is within acceptable ranges. No rebalancing needed at this time."

        rebalance_text += """
*Rebalancing helps maintain your target risk level and can improve long-term returns.*
"""

        return [TextContent(type="text", text=rebalance_text)]

    async def _generate_insights(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Generate comprehensive portfolio insights."""
        focus_area = arguments.get("focus_area", "all")

        # Get portfolio data for analysis
        try:
            summary_response = await self.http_client.get(
                f"{self.backend_url}/api/portfolio/summary"
            )
            positions_response = await self.http_client.get(
                f"{self.backend_url}/api/portfolio/positions"
            )
            performance_response = await self.http_client.get(
                f"{self.backend_url}/api/portfolio/performance"
            )

            if summary_response.status_code != 200:
                return [
                    TextContent(
                        type="text",
                        text="Unable to retrieve portfolio data for insights.",
                    )
                ]

            summary_data = summary_response.json()
            positions_data: dict[str, Any] = (
                positions_response.json()
                if positions_response.status_code == 200
                else {}
            )
            performance_data: dict[str, Any] = (
                performance_response.json()
                if performance_response.status_code == 200
                else {}
            )

        except Exception as e:
            return [
                TextContent(
                    type="text", text=f"Error retrieving data for insights: {e!s}"
                )
            ]

        insights_text = "**AI Portfolio Insights** 🤖\n\n"

        # Common data used across insights
        positions: list[dict[str, Any]] = positions_data.get("positions", [])
        num_positions = len(positions)
        total_value: float = sum(pos.get("total_value", 0) for pos in positions)

        # Performance insights
        if focus_area in ["performance", "all"]:
            ytd_return: float = performance_data.get("YTD", {}).get(
                "return_percentage", 0
            )
            monthly_return: float = performance_data.get("1M", {}).get(
                "return_percentage", 0
            )

            insights_text += "**📈 Performance Analysis:**\n"
            if ytd_return > 10:
                insights_text += "• Excellent YTD performance! You're outperforming many benchmarks.\n"
            elif ytd_return > 5:
                insights_text += (
                    "• Solid YTD performance, keeping pace with market averages.\n"
                )
            elif ytd_return > 0:
                insights_text += "• Modest positive returns - consider if this aligns with your goals.\n"
            else:
                insights_text += "• Portfolio is down YTD - review positions and consider rebalancing.\n"

            if abs(monthly_return) > 5:
                insights_text += (
                    "• High volatility in recent month - monitor risk exposure.\n"
                )

        # Risk insights
        if focus_area in ["risk", "all"]:
            insights_text += "\n**⚠️ Risk Analysis:**\n"
            if num_positions < 5:
                insights_text += (
                    "• Low diversification - consider adding more positions.\n"
                )
            elif num_positions > 20:
                insights_text += (
                    "• High number of positions - consider consolidating.\n"
                )

            if positions:
                max_position: dict[str, Any] = max(
                    positions, key=lambda x: x.get("total_value", 0)
                )
                max_percentage: float = (
                    (max_position.get("total_value", 0) / total_value * 100)
                    if total_value > 0
                    else 0
                )
                if max_percentage > 40:
                    insights_text += f"• High concentration in {max_position.get('ticker', 'unknown')} ({max_percentage:.1f}%) - consider reducing.\n"

        # Diversification insights
        if focus_area in ["diversification", "all"]:
            insights_text += "\n**🌐 Diversification Insights:**\n"
            if num_positions >= 8:
                insights_text += "• Good position count for diversification.\n"

            # Sector analysis would go here in a real implementation
            insights_text += (
                "• Consider geographic diversification with international exposure.\n"
            )
            insights_text += "• Review sector allocation to avoid overconcentration.\n"

        # Opportunity insights
        if focus_area in ["opportunities", "all"]:
            cash_percentage = (
                summary_data.get("cash_balance", 0)
                / summary_data.get("total_value", 1)
                * 100
            )

            insights_text += "\n**💡 Opportunities:**\n"
            if cash_percentage > 15:
                insights_text += (
                    "• High cash allocation - consider investing excess cash.\n"
                )
            elif cash_percentage < 5:
                insights_text += (
                    "• Low cash reserves - consider maintaining emergency fund.\n"
                )

            insights_text += (
                "• Market volatility creates potential buying opportunities.\n"
            )
            insights_text += "• Consider dollar-cost averaging for new positions.\n"

        insights_text += """
**📋 Action Items:**
1. Review and rebalance if allocations drift >5% from targets
2. Assess if current positions align with investment goals
3. Consider tax-loss harvesting opportunities
4. Stay disciplined with your investment strategy

*These insights are generated based on portfolio analysis. Always consider your personal financial situation and consult with advisors as needed.*
"""

        return [TextContent(type="text", text=insights_text)]
