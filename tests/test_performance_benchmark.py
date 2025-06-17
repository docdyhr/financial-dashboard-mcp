"""Tests for portfolio performance benchmarking service."""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from backend.services.performance_benchmark import (
    BenchmarkMetrics,
    PerformanceBenchmarkService,
)


class TestPerformanceBenchmarkService:
    """Test performance benchmarking service."""

    def setup_method(self):
        """Set up test instance."""
        self.service = PerformanceBenchmarkService()

    def test_benchmark_metrics_initialization(self):
        """Test BenchmarkMetrics initialization."""
        metrics = BenchmarkMetrics(
            name="S&P 500",
            ticker="SPY",
            total_return=Decimal("10.5"),
            annualized_return=Decimal("8.2"),
            volatility=Decimal("15.3"),
        )

        assert metrics.name == "S&P 500"
        assert metrics.ticker == "SPY"
        assert metrics.total_return == Decimal("10.5")
        assert metrics.annualized_return == Decimal("8.2")
        assert metrics.volatility == Decimal("15.3")

    def test_get_default_benchmark_return(self):
        """Test default benchmark return values."""
        assert self.service._get_default_benchmark_return("SPY") == 10.0
        assert self.service._get_default_benchmark_return("VTI") == 9.5
        assert self.service._get_default_benchmark_return("QQQ") == 12.0
        assert self.service._get_default_benchmark_return("BND") == 3.0
        assert self.service._get_default_benchmark_return("UNKNOWN") == 8.0

    def test_calculate_volatility(self):
        """Test volatility calculation."""
        returns = [0.01, -0.005, 0.02, -0.015, 0.008]
        volatility = self.service._calculate_volatility(returns)

        assert isinstance(volatility, float)
        assert volatility > 0

        # Test edge cases
        assert self.service._calculate_volatility([]) == 0.0
        assert self.service._calculate_volatility([0.01]) == 0.0

    def test_annualize_return(self):
        """Test return annualization."""
        daily_return = 0.001  # 0.1% daily
        days = 252  # One year

        annualized = self.service._annualize_return(daily_return, days)
        assert isinstance(annualized, float)
        assert annualized > 0

    def test_calculate_sharpe_ratio(self):
        """Test Sharpe ratio calculation."""
        returns = [0.001] * 252  # Consistent positive returns
        volatility = 10.0

        sharpe = self.service._calculate_sharpe_ratio(returns, volatility)
        assert isinstance(sharpe, float)

        # Test edge cases
        assert self.service._calculate_sharpe_ratio([], 10.0) == 0.0
        assert self.service._calculate_sharpe_ratio([0.001], 0.0) == 0.0

    def test_calculate_max_drawdown(self):
        """Test maximum drawdown calculation."""
        prices = [Decimal("100"), Decimal("110"), Decimal("95"), Decimal("105")]

        max_dd = self.service._calculate_max_drawdown(prices)
        assert isinstance(max_dd, float)
        assert max_dd > 0

        # Test edge cases
        assert self.service._calculate_max_drawdown([Decimal("100")]) == 0.0
        assert self.service._calculate_max_drawdown([]) == 0.0

    def test_calculate_percentile_rank(self):
        """Test percentile rank calculation."""
        value = 7.5
        benchmarks = [5.0, 6.0, 8.0, 9.0, 10.0]

        percentile = self.service._calculate_percentile_rank(value, benchmarks)
        assert 0 <= percentile <= 100

        # Test edge cases
        assert self.service._calculate_percentile_rank(5.0, []) == 50.0

    def test_categorize_risk_level(self):
        """Test risk level categorization."""
        portfolio_vol = 15.0
        benchmark_vols = [12.0, 14.0, 16.0, 18.0]

        risk_level = self.service._categorize_risk_level(portfolio_vol, benchmark_vols)
        assert risk_level in ["Low Risk", "Moderate Risk", "High Risk"]

        # Test edge case
        assert self.service._categorize_risk_level(15.0, []) == "Unknown"

    def test_rate_efficiency(self):
        """Test efficiency rating."""
        assert self.service._rate_efficiency(2.5) == "Excellent"
        assert self.service._rate_efficiency(1.5) == "Good"
        assert self.service._rate_efficiency(0.7) == "Fair"
        assert self.service._rate_efficiency(0.3) == "Poor"

    def test_get_ranking_summary(self):
        """Test ranking summary generation."""
        summary = self.service._get_ranking_summary(1, 5, 100.0)
        assert "Top performer" in summary

        summary = self.service._get_ranking_summary(2, 5, 80.0)
        assert "Strong performance" in summary

        summary = self.service._get_ranking_summary(4, 5, 20.0)
        assert "Poor performance" in summary

    def test_benchmarks_constant(self):
        """Test that benchmark constants are properly defined."""
        assert "SPY" in self.service.BENCHMARKS
        assert "VTI" in self.service.BENCHMARKS
        assert "QQQ" in self.service.BENCHMARKS
        assert "BND" in self.service.BENCHMARKS

        spy_info = self.service.BENCHMARKS["SPY"]
        assert spy_info["name"] == "S&P 500"
        assert "description" in spy_info

    @patch("backend.services.performance_benchmark.market_data_service")
    def test_get_simple_benchmark_return_success(self, mock_market_service):
        """Test simple benchmark return calculation with successful market data."""
        mock_result = Mock()
        mock_result.success = True
        mock_result.day_change_percent = 1.5
        mock_market_service.fetch_quote.return_value = mock_result

        mock_db = Mock()
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        result = self.service._get_simple_benchmark_return(
            mock_db, "SPY", start_date, end_date
        )

        assert isinstance(result, BenchmarkMetrics)
        assert result.ticker == "SPY"
        assert result.name == "S&P 500"
        assert result.total_return == Decimal("1.5")

    @patch("backend.services.performance_benchmark.market_data_service")
    def test_get_simple_benchmark_return_fallback(self, mock_market_service):
        """Test simple benchmark return fallback to historical average."""
        mock_result = Mock()
        mock_result.success = False
        mock_market_service.fetch_quote.return_value = mock_result

        mock_db = Mock()
        start_date = date.today() - timedelta(days=365)
        end_date = date.today()

        result = self.service._get_simple_benchmark_return(
            mock_db, "SPY", start_date, end_date
        )

        assert isinstance(result, BenchmarkMetrics)
        assert result.ticker == "SPY"
        # Should use SPY default return of 10% for 1 year
        assert result.total_return == Decimal("10.0")

    def test_compare_portfolio_to_benchmark(self):
        """Test portfolio to benchmark comparison."""
        # Create mock portfolio metrics
        portfolio = Mock()
        portfolio.total_return_percent = Decimal("12.5")
        portfolio.sharpe_ratio = Decimal("1.2")
        portfolio.volatility = Decimal("15.0")
        portfolio.max_drawdown = Decimal("8.0")

        # Create benchmark metrics
        benchmark = BenchmarkMetrics(
            name="S&P 500",
            ticker="SPY",
            total_return=Decimal("10.0"),
            sharpe_ratio=Decimal("1.0"),
            volatility=Decimal("12.0"),
            max_drawdown=Decimal("10.0"),
        )

        comparison = self.service._compare_portfolio_to_benchmark(portfolio, benchmark)

        assert comparison["excess_return"] == 2.5  # 12.5 - 10.0
        assert comparison["outperformed"] is True
        assert comparison["sharpe_ratio_diff"] == 0.2  # 1.2 - 1.0
        assert comparison["volatility_diff"] == 3.0  # 15.0 - 12.0
        assert comparison["max_drawdown_diff"] == -2.0  # 8.0 - 10.0 (better)

    def test_rank_performance(self):
        """Test performance ranking."""
        portfolio = Mock()
        portfolio.total_return_percent = Decimal("8.5")

        # Mock benchmark data
        benchmarks = {
            "SPY": {"benchmark": BenchmarkMetrics("S&P 500", "SPY", Decimal("10.0"))},
            "BND": {"benchmark": BenchmarkMetrics("Bonds", "BND", Decimal("3.0"))},
            "QQQ": {"benchmark": BenchmarkMetrics("NASDAQ", "QQQ", Decimal("12.0"))},
        }

        ranking = self.service._rank_performance(portfolio, benchmarks)

        assert ranking["rank"] == 3  # Should rank 3rd out of 4 (behind QQQ and SPY)
        assert ranking["total_benchmarks"] == 3
        assert ranking["percentile"] == 33.3  # (4-3)/(4-1) * 100 = 33.3%
        assert len(ranking["performance_ranking"]) == 4  # Portfolio + 3 benchmarks

    @patch("backend.services.performance_benchmark.PortfolioService")
    def test_analyze_risk_adjusted_performance(self, mock_portfolio_service):
        """Test risk-adjusted performance analysis."""
        portfolio = Mock()
        portfolio.sharpe_ratio = Decimal("1.5")
        portfolio.volatility = Decimal("18.0")
        portfolio.total_return_percent = Decimal("15.0")

        # Mock benchmark data with various metrics
        benchmarks = {
            "SPY": {
                "benchmark": BenchmarkMetrics(
                    "S&P 500",
                    "SPY",
                    Decimal("10.0"),
                    sharpe_ratio=Decimal("1.2"),
                    volatility=Decimal("15.0"),
                )
            },
            "BND": {
                "benchmark": BenchmarkMetrics(
                    "Bonds",
                    "BND",
                    Decimal("3.0"),
                    sharpe_ratio=Decimal("0.8"),
                    volatility=Decimal("5.0"),
                )
            },
        }

        analysis = self.service._analyze_risk_adjusted_performance(
            portfolio, benchmarks
        )

        assert "sharpe_ratio_analysis" in analysis
        assert "volatility_analysis" in analysis
        assert "risk_return_efficiency" in analysis

        # Check Sharpe ratio analysis
        sharpe_analysis = analysis["sharpe_ratio_analysis"]
        assert sharpe_analysis["portfolio_sharpe"] == 1.5
        assert sharpe_analysis["benchmark_average"] == 1.0  # (1.2 + 0.8) / 2
        assert sharpe_analysis["relative_performance"] == 0.5  # 1.5 - 1.0


class TestPerformanceBenchmarkAPI:
    """Test performance benchmarking API integration."""

    def test_benchmark_service_singleton(self):
        """Test that the service singleton is properly configured."""
        from backend.services.performance_benchmark import (
            get_performance_benchmark_service,
            performance_benchmark_service,
        )

        service1 = get_performance_benchmark_service()
        service2 = get_performance_benchmark_service()

        assert service1 is service2
        assert service1 is performance_benchmark_service
        assert isinstance(service1, PerformanceBenchmarkService)
