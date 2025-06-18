"""Portfolio performance benchmarking service.

This service provides comprehensive benchmarking capabilities for portfolio performance
analysis, including multiple benchmark comparisons, risk-adjusted returns, and
performance attribution analysis.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from backend.models.asset import Asset
from backend.models.price_history import PriceHistory
from backend.schemas.portfolio import PerformanceMetrics
from backend.services.market_data import market_data_service
from backend.services.portfolio import PortfolioService

logger = logging.getLogger(__name__)


class BenchmarkMetrics:
    """Benchmark performance metrics."""

    def __init__(
        self,
        name: str,
        ticker: str,
        total_return: Decimal,
        annualized_return: Decimal | None = None,
        volatility: Decimal | None = None,
        sharpe_ratio: Decimal | None = None,
        max_drawdown: Decimal | None = None,
    ):
        self.name = name
        self.ticker = ticker
        self.total_return = total_return
        self.annualized_return = annualized_return
        self.volatility = volatility
        self.sharpe_ratio = sharpe_ratio
        self.max_drawdown = max_drawdown


class PerformanceBenchmarkService:
    """Service for comprehensive portfolio performance benchmarking."""

    # Common benchmark definitions
    BENCHMARKS = {
        "SPY": {"name": "S&P 500", "description": "Large-cap US stocks"},
        "VTI": {"name": "Total Stock Market", "description": "Total US stock market"},
        "QQQ": {"name": "NASDAQ 100", "description": "Technology-heavy index"},
        "IWM": {"name": "Russell 2000", "description": "Small-cap US stocks"},
        "VEA": {
            "name": "Developed Markets",
            "description": "International developed markets",
        },
        "VWO": {"name": "Emerging Markets", "description": "Emerging markets stocks"},
        "BND": {"name": "Bond Index", "description": "US investment-grade bonds"},
        "VNQ": {"name": "REIT Index", "description": "Real estate investment trusts"},
        "DIA": {"name": "Dow Jones", "description": "Dow Jones Industrial Average"},
        "EFA": {"name": "EAFE", "description": "Europe, Australasia, Far East"},
    }

    def __init__(self):
        self.portfolio_service = PortfolioService()

    def get_comprehensive_benchmark_analysis(
        self,
        db: Session,
        user_id: int,
        benchmark_tickers: list[str] | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """Get comprehensive benchmark analysis comparing portfolio to multiple benchmarks."""
        if not benchmark_tickers:
            benchmark_tickers = ["SPY", "VTI", "QQQ", "BND"]  # Default diverse set

        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=365)

        # Get portfolio performance
        portfolio_metrics = self.portfolio_service.calculate_performance_metrics(
            db, user_id, start_date, end_date
        )

        # Get benchmark performances
        benchmark_comparisons = {}
        for ticker in benchmark_tickers:
            try:
                benchmark_metrics = self._calculate_benchmark_metrics(
                    db, ticker, start_date, end_date
                )

                comparison = self._compare_portfolio_to_benchmark(
                    portfolio_metrics, benchmark_metrics
                )

                benchmark_comparisons[ticker] = {
                    "benchmark": benchmark_metrics,
                    "comparison": comparison,
                }
            except Exception as e:
                logger.warning(f"Failed to calculate benchmark for {ticker}: {e}")
                continue

        # Performance ranking
        ranking = self._rank_performance(portfolio_metrics, benchmark_comparisons)

        # Risk-adjusted performance analysis
        risk_analysis = self._analyze_risk_adjusted_performance(
            portfolio_metrics, benchmark_comparisons
        )

        return {
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days,
            },
            "portfolio_performance": {
                "total_return": float(portfolio_metrics.total_return_percent or 0),
                "annualized_return": float(portfolio_metrics.annualized_return or 0),
                "volatility": float(portfolio_metrics.volatility or 0),
                "sharpe_ratio": float(portfolio_metrics.sharpe_ratio or 0),
                "max_drawdown": float(portfolio_metrics.max_drawdown or 0),
            },
            "benchmark_comparisons": benchmark_comparisons,
            "performance_ranking": ranking,
            "risk_analysis": risk_analysis,
            "summary": self._generate_performance_summary(
                portfolio_metrics, benchmark_comparisons, ranking
            ),
        }

    def _calculate_benchmark_metrics(
        self,
        db: Session,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> BenchmarkMetrics:
        """Calculate comprehensive metrics for a benchmark."""
        # Get benchmark asset and price history
        asset = db.query(Asset).filter(Asset.ticker == ticker).first()

        if not asset:
            # Try to create asset if it doesn't exist
            asset = self._create_benchmark_asset(db, ticker)

        # Get price history
        prices = (
            db.query(PriceHistory)
            .filter(
                PriceHistory.asset_id == asset.id,
                PriceHistory.price_date >= start_date,
                PriceHistory.price_date <= end_date,
            )
            .order_by(PriceHistory.price_date)
            .all()
        )

        if len(prices) < 2:
            # Fallback to simple return calculation
            return self._get_simple_benchmark_return(db, ticker, start_date, end_date)

        # Calculate comprehensive metrics
        returns = []
        for i in range(1, len(prices)):
            daily_return = (prices[i].close_price - prices[i - 1].close_price) / prices[
                i - 1
            ].close_price
            returns.append(float(daily_return))

        total_return = (
            (prices[-1].close_price - prices[0].close_price)
            / prices[0].close_price
            * 100
        )

        # Calculate additional metrics
        avg_return = sum(returns) / len(returns) if returns else 0
        volatility = self._calculate_volatility(returns) if len(returns) > 1 else None
        annualized_return = self._annualize_return(avg_return, len(returns))
        sharpe_ratio = (
            self._calculate_sharpe_ratio(returns, volatility) if volatility else None
        )
        max_drawdown = self._calculate_max_drawdown([p.close_price for p in prices])

        benchmark_info = self.BENCHMARKS.get(
            ticker, {"name": ticker, "description": ""}
        )

        return BenchmarkMetrics(
            name=benchmark_info["name"],
            ticker=ticker,
            total_return=Decimal(str(total_return)),
            annualized_return=(
                Decimal(str(annualized_return)) if annualized_return else None
            ),
            volatility=Decimal(str(volatility)) if volatility else None,
            sharpe_ratio=Decimal(str(sharpe_ratio)) if sharpe_ratio else None,
            max_drawdown=Decimal(str(max_drawdown)) if max_drawdown else None,
        )

    def _compare_portfolio_to_benchmark(
        self,
        portfolio: PerformanceMetrics,
        benchmark: BenchmarkMetrics,
    ) -> dict[str, Any]:
        """Compare portfolio performance to a specific benchmark."""
        portfolio_return = float(portfolio.total_return_percent or 0)
        benchmark_return = float(benchmark.total_return)

        excess_return = portfolio_return - benchmark_return

        # Calculate relative performance metrics
        comparison = {
            "excess_return": excess_return,
            "relative_return": (
                (excess_return / benchmark_return * 100) if benchmark_return != 0 else 0
            ),
            "outperformed": excess_return > 0,
        }

        # Risk-adjusted comparisons
        if portfolio.sharpe_ratio and benchmark.sharpe_ratio:
            comparison["sharpe_ratio_diff"] = float(
                portfolio.sharpe_ratio - benchmark.sharpe_ratio
            )

        if portfolio.volatility and benchmark.volatility:
            comparison["volatility_diff"] = float(
                portfolio.volatility - benchmark.volatility
            )

        if portfolio.max_drawdown and benchmark.max_drawdown:
            comparison["max_drawdown_diff"] = float(
                portfolio.max_drawdown - benchmark.max_drawdown
            )

        # Performance consistency
        comparison["risk_adjusted_excess"] = self._calculate_information_ratio(
            excess_return, portfolio.volatility, benchmark.volatility
        )

        return comparison

    def _rank_performance(
        self,
        portfolio: PerformanceMetrics,
        benchmarks: dict[str, Any],
    ) -> dict[str, Any]:
        """Rank portfolio performance against benchmarks."""
        portfolio_return = float(portfolio.total_return_percent or 0)

        # Create performance list including portfolio
        performance_list = [
            {"name": "Your Portfolio", "return": portfolio_return, "type": "portfolio"}
        ]

        for ticker, data in benchmarks.items():
            benchmark_return = float(data["benchmark"].total_return)
            benchmark_name = data["benchmark"].name
            performance_list.append(
                {
                    "name": benchmark_name,
                    "return": benchmark_return,
                    "type": "benchmark",
                    "ticker": ticker,
                }
            )

        # Sort by return (descending)
        performance_list.sort(key=lambda x: x["return"], reverse=True)

        # Find portfolio rank
        portfolio_rank = next(
            (
                i + 1
                for i, item in enumerate(performance_list)
                if item["type"] == "portfolio"
            ),
            len(performance_list),
        )

        total_items = len(performance_list)
        percentile = (
            ((total_items - portfolio_rank) / (total_items - 1)) * 100
            if total_items > 1
            else 50
        )

        return {
            "rank": portfolio_rank,
            "total_benchmarks": total_items - 1,
            "percentile": round(percentile, 1),
            "performance_ranking": performance_list,
            "summary": self._get_ranking_summary(
                portfolio_rank, total_items, percentile
            ),
        }

    def _analyze_risk_adjusted_performance(
        self,
        portfolio: PerformanceMetrics,
        benchmarks: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze risk-adjusted performance metrics."""
        analysis = {
            "sharpe_ratio_analysis": {},
            "volatility_analysis": {},
            "risk_return_efficiency": {},
        }

        portfolio_sharpe = float(portfolio.sharpe_ratio or 0)
        portfolio_volatility = float(portfolio.volatility or 0)
        portfolio_return = float(portfolio.total_return_percent or 0)

        # Sharpe ratio analysis
        sharpe_ratios = []
        for data in benchmarks.values():
            if data["benchmark"].sharpe_ratio:
                sharpe_ratios.append(float(data["benchmark"].sharpe_ratio))

        if sharpe_ratios:
            avg_benchmark_sharpe = sum(sharpe_ratios) / len(sharpe_ratios)
            analysis["sharpe_ratio_analysis"] = {
                "portfolio_sharpe": portfolio_sharpe,
                "benchmark_average": avg_benchmark_sharpe,
                "relative_performance": portfolio_sharpe - avg_benchmark_sharpe,
                "percentile_rank": self._calculate_percentile_rank(
                    portfolio_sharpe, sharpe_ratios
                ),
            }

        # Volatility analysis
        volatilities = []
        for data in benchmarks.values():
            if data["benchmark"].volatility:
                volatilities.append(float(data["benchmark"].volatility))

        if volatilities:
            avg_benchmark_volatility = sum(volatilities) / len(volatilities)
            analysis["volatility_analysis"] = {
                "portfolio_volatility": portfolio_volatility,
                "benchmark_average": avg_benchmark_volatility,
                "relative_risk": portfolio_volatility - avg_benchmark_volatility,
                "risk_level": self._categorize_risk_level(
                    portfolio_volatility, volatilities
                ),
            }

        # Risk-return efficiency
        if portfolio_volatility > 0:
            risk_return_ratio = portfolio_return / portfolio_volatility
            analysis["risk_return_efficiency"] = {
                "portfolio_efficiency": risk_return_ratio,
                "efficiency_rating": self._rate_efficiency(risk_return_ratio),
            }

        return analysis

    def _generate_performance_summary(
        self,
        portfolio: PerformanceMetrics,
        benchmarks: dict[str, Any],
        ranking: dict[str, Any],
    ) -> dict[str, str]:
        """Generate a human-readable performance summary."""
        portfolio_return = float(portfolio.total_return_percent or 0)
        outperformed_count = sum(
            1
            for data in benchmarks.values()
            if portfolio_return > float(data["benchmark"].total_return)
        )
        total_benchmarks = len(benchmarks)

        summary = {
            "overall": f"Portfolio returned {portfolio_return:.2f}% vs benchmark average",
            "ranking": f"Ranked #{ranking['rank']} out of {ranking['total_benchmarks'] + 1} investments",
            "outperformance": f"Outperformed {outperformed_count} of {total_benchmarks} benchmarks",
        }

        # Risk assessment
        portfolio_sharpe = float(portfolio.sharpe_ratio or 0)
        if portfolio_sharpe > 1.0:
            summary["risk_adjusted"] = "Excellent risk-adjusted returns (Sharpe > 1.0)"
        elif portfolio_sharpe > 0.5:
            summary["risk_adjusted"] = "Good risk-adjusted returns (Sharpe > 0.5)"
        else:
            summary["risk_adjusted"] = "Below-average risk-adjusted returns"

        return summary

    # Helper methods

    def _create_benchmark_asset(self, db: Session, ticker: str) -> Asset:
        """Create a benchmark asset if it doesn't exist."""
        benchmark_info = self.BENCHMARKS.get(
            ticker, {"name": ticker, "description": ""}
        )

        asset = Asset(
            ticker=ticker,
            name=benchmark_info["name"],
            asset_type="etf",
            category="index",
            currency="USD",
            exchange_code="NYSE",  # Default
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return asset

    def _get_simple_benchmark_return(
        self, db: Session, ticker: str, start_date: date, end_date: date
    ) -> BenchmarkMetrics:
        """Get simple benchmark return when detailed data is unavailable."""
        try:
            result = market_data_service.fetch_quote(ticker, db)
            if result.success and result.day_change_percent:
                # Use current day change as proxy
                return_pct = float(result.day_change_percent)
            else:
                # Use historical average based on benchmark type
                days_diff = (end_date - start_date).days
                annual_return = self._get_default_benchmark_return(ticker)
                return_pct = (annual_return * days_diff) / 365

            benchmark_info = self.BENCHMARKS.get(ticker, {"name": ticker})
            return BenchmarkMetrics(
                name=benchmark_info["name"],
                ticker=ticker,
                total_return=Decimal(str(return_pct)),
            )
        except Exception as e:
            logger.error(f"Error calculating simple benchmark return for {ticker}: {e}")
            raise

    def _get_default_benchmark_return(self, ticker: str) -> float:
        """Get default expected annual return for common benchmarks."""
        defaults = {
            "SPY": 10.0,  # S&P 500 historical average
            "VTI": 9.5,  # Total market
            "QQQ": 12.0,  # Tech-heavy, higher expected return
            "IWM": 8.5,  # Small cap, more volatile
            "BND": 3.0,  # Bonds, lower return
            "VNQ": 8.0,  # REITs
        }
        return defaults.get(ticker, 8.0)  # Default 8% if unknown

    def _calculate_volatility(self, returns: list[float]) -> float:
        """Calculate annualized volatility from daily returns."""
        if len(returns) < 2:
            return 0.0

        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        daily_volatility = variance**0.5
        return daily_volatility * (252**0.5) * 100  # Annualized percentage

    def _annualize_return(self, daily_avg_return: float, days: int) -> float:
        """Annualize a daily average return."""
        if days == 0:
            return 0.0
        return ((1 + daily_avg_return) ** (252 / days) - 1) * 100

    def _calculate_sharpe_ratio(self, returns: list[float], volatility: float) -> float:
        """Calculate Sharpe ratio (assuming 2% risk-free rate)."""
        if not returns or volatility == 0:
            return 0.0

        avg_return = sum(returns) / len(returns) * 252 * 100  # Annualized
        risk_free_rate = 2.0  # 2% risk-free rate assumption
        excess_return = avg_return - risk_free_rate
        return excess_return / volatility if volatility > 0 else 0.0

    def _calculate_max_drawdown(self, prices: list[Decimal]) -> float:
        """Calculate maximum drawdown from price series."""
        if len(prices) < 2:
            return 0.0

        peak = prices[0]
        max_drawdown = 0.0

        for price in prices[1:]:
            if price > peak:
                peak = price
            else:
                drawdown = (peak - price) / peak
                max_drawdown = max(max_drawdown, drawdown)

        return float(max_drawdown) * 100  # Return as percentage

    def _calculate_information_ratio(
        self,
        excess_return: float,
        portfolio_vol: Decimal | None,
        benchmark_vol: Decimal | None,
    ) -> float | None:
        """Calculate information ratio (excess return / tracking error)."""
        if not portfolio_vol or not benchmark_vol:
            return None

        tracking_error = abs(float(portfolio_vol) - float(benchmark_vol))
        if tracking_error == 0:
            return None

        return excess_return / tracking_error

    def _calculate_percentile_rank(
        self, value: float, benchmark_values: list[float]
    ) -> float:
        """Calculate percentile rank of value within benchmark values."""
        if not benchmark_values:
            return 50.0

        count_below = sum(1 for b in benchmark_values if b < value)
        return (count_below / len(benchmark_values)) * 100

    def _categorize_risk_level(
        self, portfolio_vol: float, benchmark_vols: list[float]
    ) -> str:
        """Categorize portfolio risk level relative to benchmarks."""
        if not benchmark_vols:
            return "Unknown"

        avg_vol = sum(benchmark_vols) / len(benchmark_vols)

        if portfolio_vol < avg_vol * 0.8:
            return "Low Risk"
        if portfolio_vol < avg_vol * 1.2:
            return "Moderate Risk"
        return "High Risk"

    def _rate_efficiency(self, efficiency_ratio: float) -> str:
        """Rate risk-return efficiency."""
        if efficiency_ratio > 2.0:
            return "Excellent"
        if efficiency_ratio > 1.0:
            return "Good"
        if efficiency_ratio > 0.5:
            return "Fair"
        return "Poor"

    def _get_ranking_summary(self, rank: int, total: int, percentile: float) -> str:
        """Generate ranking summary text."""
        if rank == 1:
            return "Top performer - outperformed all benchmarks"
        if percentile >= 75:
            return f"Strong performance - top {100-percentile:.0f}% of investments"
        if percentile >= 50:
            return (
                f"Above-average performance - top {100-percentile:.0f}% of investments"
            )
        if percentile >= 25:
            return (
                f"Below-average performance - bottom {percentile:.0f}% of investments"
            )
        return f"Poor performance - bottom {percentile:.0f}% of investments"


# Singleton instance
performance_benchmark_service = PerformanceBenchmarkService()


def get_performance_benchmark_service() -> PerformanceBenchmarkService:
    """Get the performance benchmark service instance."""
    return performance_benchmark_service
