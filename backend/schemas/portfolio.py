"""Portfolio schemas for summary and performance API."""
from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import Field

from backend.schemas.asset import AssetSummary
from backend.schemas.base import BaseSchema
from backend.schemas.position import PositionSummary


class PortfolioSummary(BaseSchema):
    """Portfolio overview and summary statistics."""

    user_id: int = Field(..., description="User ID")
    total_value: Decimal = Field(..., description="Total portfolio value")
    total_cost_basis: Decimal = Field(..., description="Total cost basis")
    cash_balance: Decimal = Field(..., description="Cash balance")
    invested_amount: Decimal = Field(..., description="Total invested amount")

    # Performance metrics
    total_gain_loss: Decimal = Field(..., description="Total unrealized gain/loss")
    total_gain_loss_percent: Decimal = Field(
        ..., description="Total gain/loss percentage"
    )
    daily_change: Decimal | None = Field(None, description="Daily change in value")
    daily_change_percent: Decimal | None = Field(
        None, description="Daily change percentage"
    )

    # Position counts
    total_positions: int = Field(..., description="Total number of positions")
    total_assets: int = Field(..., description="Total number of unique assets")

    # Top positions (by value)
    top_positions: list[PositionSummary] = Field(
        default=[], description="Top 5 positions by value"
    )


class AllocationBreakdown(BaseSchema):
    """Asset allocation breakdown."""

    equity_percent: Decimal = Field(..., description="Equity allocation percentage")
    fixed_income_percent: Decimal = Field(
        ..., description="Fixed income allocation percentage"
    )
    alternative_percent: Decimal = Field(
        ..., description="Alternative investments percentage"
    )
    cash_percent: Decimal = Field(..., description="Cash allocation percentage")
    commodity_percent: Decimal = Field(
        ..., description="Commodity allocation percentage"
    )
    real_estate_percent: Decimal = Field(
        ..., description="Real estate allocation percentage"
    )

    # Detailed breakdown
    allocation_by_category: dict[str, Decimal] = Field(
        default={}, description="Allocation by asset category"
    )
    allocation_by_sector: dict[str, Decimal] = Field(
        default={}, description="Allocation by sector"
    )
    allocation_by_asset_type: dict[str, Decimal] = Field(
        default={}, description="Allocation by asset type"
    )


class PerformanceMetrics(BaseSchema):
    """Portfolio performance metrics."""

    # Return metrics
    total_return: Decimal = Field(..., description="Total return amount")
    total_return_percent: Decimal = Field(..., description="Total return percentage")
    annualized_return: Decimal | None = Field(
        None, description="Annualized return percentage"
    )

    # Time-based returns
    daily_return: Decimal | None = Field(None, description="Daily return percentage")
    weekly_return: Decimal | None = Field(
        None, description="Weekly return percentage"
    )
    monthly_return: Decimal | None = Field(
        None, description="Monthly return percentage"
    )
    quarterly_return: Decimal | None = Field(
        None, description="Quarterly return percentage"
    )
    ytd_return: Decimal | None = Field(
        None, description="Year-to-date return percentage"
    )
    one_year_return: Decimal | None = Field(
        None, description="One year return percentage"
    )

    # Risk metrics
    volatility: Decimal | None = Field(
        None, description="Portfolio volatility (standard deviation)"
    )
    sharpe_ratio: Decimal | None = Field(None, description="Sharpe ratio")
    beta: Decimal | None = Field(None, description="Portfolio beta")
    alpha: Decimal | None = Field(None, description="Portfolio alpha")
    max_drawdown: Decimal | None = Field(
        None, description="Maximum drawdown percentage"
    )

    # Income metrics
    dividend_yield: Decimal | None = Field(
        None, description="Portfolio dividend yield"
    )
    annual_dividend_income: Decimal | None = Field(
        None, description="Annual dividend income"
    )


class PortfolioPerformanceRequest(BaseSchema):
    """Request parameters for portfolio performance analysis."""

    user_id: int = Field(..., description="User ID")
    start_date: date | None = Field(
        None, description="Start date for performance calculation"
    )
    end_date: date | None = Field(
        None, description="End date for performance calculation"
    )
    benchmark_ticker: str | None = Field(
        None, description="Benchmark ticker for comparison"
    )
    include_cash: bool = Field(
        True, description="Include cash in performance calculations"
    )
    annualize: bool = Field(True, description="Annualize returns where applicable")


class PortfolioPerformanceResponse(BaseSchema):
    """Portfolio performance analysis response."""

    user_id: int = Field(..., description="User ID")
    analysis_period: str = Field(..., description="Analysis period description")
    start_date: date | None = Field(None, description="Analysis start date")
    end_date: date | None = Field(None, description="Analysis end date")

    summary: PortfolioSummary = Field(..., description="Portfolio summary")
    allocation: AllocationBreakdown = Field(..., description="Allocation breakdown")
    performance: PerformanceMetrics = Field(..., description="Performance metrics")

    # Benchmark comparison (if requested)
    benchmark_ticker: str | None = Field(None, description="Benchmark ticker")
    benchmark_return: Decimal | None = Field(
        None, description="Benchmark return for period"
    )
    excess_return: Decimal | None = Field(
        None, description="Excess return vs benchmark"
    )


class PortfolioHistoricalPerformance(BaseSchema):
    """Historical portfolio performance data."""

    dates: list[date] = Field(..., description="Historical dates")
    values: list[Decimal] = Field(..., description="Portfolio values")
    returns: list[Decimal] = Field(..., description="Daily returns")
    cumulative_returns: list[Decimal] = Field(..., description="Cumulative returns")
    drawdowns: list[Decimal] = Field(..., description="Drawdown percentages")


class DiversificationMetrics(BaseSchema):
    """Portfolio diversification analysis."""

    concentration_risk: Decimal = Field(..., description="Concentration risk score")
    herfindahl_index: Decimal = Field(..., description="Herfindahl-Hirschman Index")
    effective_number_of_assets: Decimal = Field(
        ..., description="Effective number of assets"
    )
    sector_concentration: dict[str, Decimal] = Field(
        default={}, description="Sector concentration"
    )
    geographic_concentration: dict[str, Decimal] = Field(
        default={}, description="Geographic concentration"
    )

    # Diversification scores (0-100)
    overall_diversification_score: int = Field(
        ..., ge=0, le=100, description="Overall diversification score"
    )
    sector_diversification_score: int = Field(
        ..., ge=0, le=100, description="Sector diversification score"
    )
    asset_type_diversification_score: int = Field(
        ..., ge=0, le=100, description="Asset type diversification score"
    )


class RebalancingRecommendation(BaseSchema):
    """Portfolio rebalancing recommendations."""

    current_allocation: AllocationBreakdown = Field(
        ..., description="Current allocation"
    )
    target_allocation: AllocationBreakdown = Field(..., description="Target allocation")
    rebalancing_required: bool = Field(
        ..., description="Whether rebalancing is recommended"
    )
    total_drift: Decimal = Field(..., description="Total allocation drift percentage")

    # Specific recommendations
    recommendations: list[dict] = Field(
        default=[], description="Specific rebalancing actions"
    )
    estimated_cost: Decimal = Field(..., description="Estimated cost of rebalancing")
    tax_implications: str | None = Field(
        None, description="Tax implications summary"
    )


class PortfolioOptimizationRequest(BaseSchema):
    """Request for portfolio optimization analysis."""

    user_id: int = Field(..., description="User ID")
    target_allocation: dict[str, Decimal] = Field(
        ..., description="Target allocation percentages"
    )
    risk_tolerance: str = Field(..., description="Risk tolerance level")
    investment_horizon: int = Field(..., description="Investment horizon in years")
    constraints: dict[str, Any] = Field(
        default={}, description="Investment constraints"
    )


class PortfolioStressTestResults(BaseSchema):
    """Portfolio stress test results."""

    scenario_name: str = Field(..., description="Stress test scenario name")
    portfolio_impact: Decimal = Field(..., description="Portfolio impact percentage")
    worst_performing_assets: list[AssetSummary] = Field(
        ..., description="Worst performing assets"
    )
    sector_impacts: dict[str, Decimal] = Field(..., description="Impact by sector")
    recovery_time_estimate: int | None = Field(
        None, description="Estimated recovery time in days"
    )


class PortfolioAnalyticsResponse(BaseSchema):
    """Comprehensive portfolio analytics response."""

    summary: PortfolioSummary = Field(..., description="Portfolio summary")
    performance: PortfolioPerformanceResponse = Field(
        ..., description="Performance analysis"
    )
    diversification: DiversificationMetrics = Field(
        ..., description="Diversification metrics"
    )
    rebalancing: RebalancingRecommendation = Field(
        ..., description="Rebalancing recommendations"
    )
    historical_data: PortfolioHistoricalPerformance = Field(
        ..., description="Historical performance"
    )
    stress_tests: list[PortfolioStressTestResults] = Field(
        default=[], description="Stress test results"
    )


class PortfolioComparisonRequest(BaseSchema):
    """Request for comparing multiple portfolios."""

    portfolio_ids: list[int] = Field(
        ..., min_items=2, max_items=10, description="Portfolio IDs to compare"
    )
    start_date: date | None = Field(None, description="Comparison start date")
    end_date: date | None = Field(None, description="Comparison end date")
    metrics: list[str] = Field(
        default=["return", "volatility", "sharpe"], description="Metrics to compare"
    )


class PortfolioRiskAnalysis(BaseSchema):
    """Portfolio risk analysis."""

    value_at_risk: dict[str, Decimal] = Field(
        ..., description="VaR at different confidence levels"
    )
    expected_shortfall: dict[str, Decimal] = Field(
        ..., description="Expected shortfall (CVaR)"
    )
    risk_contribution: dict[str, Decimal] = Field(
        ..., description="Risk contribution by position"
    )
    correlation_matrix: dict[str, dict[str, Decimal]] = Field(
        default={}, description="Asset correlation matrix"
    )

    # Risk metrics
    portfolio_volatility: Decimal = Field(..., description="Portfolio volatility")
    tracking_error: Decimal | None = Field(
        None, description="Tracking error vs benchmark"
    )
    information_ratio: Decimal | None = Field(None, description="Information ratio")
