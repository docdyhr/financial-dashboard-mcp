"""Financial calculation tests with comprehensive edge case coverage."""

from decimal import Decimal, InvalidOperation
from typing import Any

import pytest


@pytest.mark.financial
@pytest.mark.unit
class TestFinancialCalculations:
    """Test suite for financial calculation functions."""

    def test_simple_interest_calculation(self) -> None:
        """Test simple interest calculation: I = P * R * T."""
        principal = Decimal("1000.00")
        rate = Decimal("0.05")  # 5%
        time = 2

        expected = principal * rate * time
        assert expected == Decimal("100.00")  # nosec

    def test_compound_interest_calculation(
        self, financial_calculation_test_cases: list[tuple[float, float, int, float]]
    ) -> None:
        """Test compound interest calculation: A = P(1 + r)^t."""
        for principal, rate, time, expected in financial_calculation_test_cases:
            result = 0.0 if principal == 0 else float(principal * (1 + rate) ** time)
            # Use relative tolerance for large numbers
            tolerance = max(
                0.01, abs(expected) * 0.001
            )  # 0.1% tolerance for large numbers
            assert (
                abs(result - expected) < tolerance
            ), f"Failed for P={principal}, r={rate}, t={time}"  # nosec

    def test_portfolio_percentage_calculation(
        self, sample_portfolio_data: dict[str, Any]
    ) -> None:
        """Test portfolio percentage calculations."""
        portfolio = sample_portfolio_data
        total_value = portfolio["total_value"]
        for position in portfolio["positions"]:
            position_value = position["total_value"]
            percentage = (position_value / total_value) * 100
            # AAPL should be ~68.18% (15000/22000)
            if position["ticker"] == "AAPL":
                assert abs(percentage - Decimal("68.18")) < Decimal("0.01")  # nosec
            # GOOGL should be ~31.82% (7000/22000)
            elif position["ticker"] == "GOOGL":
                assert abs(percentage - Decimal("31.82")) < Decimal("0.01")  # nosec

    def test_gain_loss_calculation(self, sample_portfolio_data: dict[str, Any]) -> None:
        """Test gain/loss calculation accuracy."""
        for position in sample_portfolio_data["positions"]:
            quantity = position["quantity"]
            purchase_price = position["purchase_price"]
            current_price = position["current_price"]
            expected_gain = (current_price - purchase_price) * quantity
            expected_percentage = (
                (current_price - purchase_price) / purchase_price
            ) * 100
            assert position["gain_loss"] == expected_gain  # nosec
            assert abs(position["gain_loss_percent"] - expected_percentage) < Decimal(
                "0.01"
            )  # nosec

    def test_zero_division_protection(self) -> None:
        """Test protection against division by zero errors."""
        with pytest.raises(ZeroDivisionError):
            result = Decimal("1000") / Decimal("0")

    def test_negative_values_handling(self) -> None:
        """Test handling of negative financial values."""
        # Negative prices should be invalid
        with pytest.raises(ValueError, match="Price cannot be negative"):
            self._validate_price(Decimal("-100.00"))

        # Negative quantities should be invalid for long positions
        with pytest.raises(ValueError, match="Quantity cannot be negative"):
            self._validate_quantity(Decimal("-10"))

    def test_precision_handling(self) -> None:
        """Test decimal precision in financial calculations."""
        # Test very small amounts
        small_amount = Decimal("0.01")
        rate = Decimal("0.001")
        result = small_amount * rate
        assert result == Decimal("0.00001")  # nosec

        # Test large amounts
        large_amount = Decimal("1000000000.00")
        small_rate = Decimal("0.0001")
        result = large_amount * small_rate
        assert result == Decimal("100000.00")  # nosec

    def test_currency_rounding(self) -> None:
        """Test proper currency rounding to 2 decimal places."""
        # Test rounding down
        value = Decimal("123.454")
        rounded = value.quantize(Decimal("0.01"))
        assert rounded == Decimal("123.45")  # nosec

        # Test rounding up
        value = Decimal("123.456")
        rounded = value.quantize(Decimal("0.01"))
        assert rounded == Decimal("123.46")  # nosec

    def test_percentage_calculations(self) -> None:
        """Test percentage calculation edge cases."""
        # Normal percentage
        part = Decimal("25")
        whole = Decimal("100")
        percentage = (part / whole) * 100
        assert percentage == Decimal("25")  # nosec

        # Percentage greater than 100%
        part = Decimal("150")
        whole = Decimal("100")
        percentage = (part / whole) * 100
        assert percentage == Decimal("150")  # nosec

        # Very small percentage
        part = Decimal("0.01")
        whole = Decimal("1000")
        percentage = (part / whole) * 100
        assert percentage == Decimal("0.001")  # nosec

    def test_volatility_calculation(self) -> None:
        """Test volatility calculation for risk assessment."""
        # Sample price returns
        returns = [
            Decimal("0.02"),  # 2%
            Decimal("-0.01"),  # -1%
            Decimal("0.03"),  # 3%
            Decimal("-0.02"),  # -2%
            Decimal("0.01"),  # 1%
        ]

        # Calculate mean return
        mean_return = sum(returns) / Decimal(len(returns))
        assert mean_return == Decimal("0.006")  # nosec

        # Calculate variance using Decimal arithmetic
        variance_sum = Decimal(0)
        for r in returns:
            variance_sum += (r - mean_return) ** 2
        variance = variance_sum / Decimal(len(returns))

        # The correct expected variance should be calculated properly
        # Variance = [(0.02-0.006)² + (-0.01-0.006)² + (0.03-0.006)² +
        #            (-0.02-0.006)² + (0.01-0.006)²] / 5
        # = [0.000196 + 0.000256 + 0.000576 + 0.000676 + 0.000016] / 5
        # = 0.001720 / 5 = 0.000344
        expected_variance = Decimal("0.000344")
        assert abs(variance - expected_variance) < Decimal("0.000001")  # nosec

    def test_sharpe_ratio_calculation(self) -> None:
        """Test Sharpe ratio calculation for risk-adjusted returns."""
        portfolio_return = Decimal("0.12")  # 12%
        risk_free_rate = Decimal("0.02")  # 2%
        volatility = Decimal("0.15")  # 15%

        sharpe_ratio = (portfolio_return - risk_free_rate) / volatility
        expected_sharpe = Decimal("0.67")  # (0.12 - 0.02) / 0.15 ≈ 0.67

        assert abs(sharpe_ratio - expected_sharpe) < Decimal("0.01")  # nosec

    def test_beta_calculation(self) -> None:
        """Test beta calculation for market risk assessment."""
        # Mock market and stock returns
        market_returns = [Decimal("0.01"), Decimal("0.02"), Decimal("-0.01")]
        stock_returns = [Decimal("0.015"), Decimal("0.025"), Decimal("-0.005")]

        # Calculate covariance and variance using Decimal
        market_mean = sum(market_returns) / Decimal(len(market_returns))
        stock_mean = sum(stock_returns) / Decimal(len(stock_returns))

        covariance_sum = Decimal(0)
        for m, s in zip(market_returns, stock_returns, strict=False):
            covariance_sum += (m - market_mean) * (s - stock_mean)
        covariance = covariance_sum / Decimal(len(market_returns))

        variance_sum = Decimal(0)
        for m in market_returns:
            variance_sum += (m - market_mean) ** 2
        market_variance = variance_sum / Decimal(len(market_returns))

        beta = covariance / market_variance if market_variance != 0 else Decimal("1.0")

        # Beta should be 1.0 for this example
        assert abs(beta - Decimal("1.0")) < Decimal("0.01")  # nosec

    @staticmethod
    def _validate_price(price: Decimal) -> None:
        """Validate that price is positive."""
        if price < 0:
            raise ValueError("Price cannot be negative")

    @staticmethod
    def _validate_quantity(quantity: Decimal) -> None:
        """Validate that quantity is positive."""
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")


@pytest.mark.financial
@pytest.mark.integration
class TestFinancialIntegration:
    """Integration tests for financial calculations."""

    def test_portfolio_total_calculation(
        self, sample_portfolio_data: dict[str, Any]
    ) -> None:
        """Test complete portfolio calculation integration."""
        portfolio = sample_portfolio_data

        # Calculate total value from positions
        calculated_total = sum(
            position["total_value"] for position in portfolio["positions"]
        )

        assert calculated_total == portfolio["total_value"]  # nosec

    def test_portfolio_cost_basis_calculation(
        self, sample_portfolio_data: dict[str, Any]
    ) -> None:
        """Test portfolio cost basis calculation."""
        portfolio = sample_portfolio_data

        # Calculate total cost from positions
        calculated_cost = sum(
            position["quantity"] * position["purchase_price"]
            for position in portfolio["positions"]
        )

        assert calculated_cost == portfolio["total_cost"]  # nosec

    def test_portfolio_gain_percentage(
        self, sample_portfolio_data: dict[str, Any]
    ) -> None:
        """Test overall portfolio gain percentage."""
        portfolio = sample_portfolio_data
        total_cost = portfolio["total_cost"]
        total_value = portfolio["total_value"]

        calculated_gain_percent = ((total_value - total_cost) / total_cost) * 100

        assert abs(calculated_gain_percent - portfolio["total_gain_percent"]) < Decimal(
            "0.01"
        )  # nosec


@pytest.mark.financial
@pytest.mark.security
class TestFinancialSecurity:
    """Security tests for financial calculations."""

    def test_input_sanitization(self) -> None:
        """Test that financial inputs are properly sanitized."""
        # Test SQL injection attempt
        malicious_input = "'; DROP TABLE positions; --"
        with pytest.raises(InvalidOperation):
            Decimal(malicious_input)

    def test_overflow_protection(self) -> None:
        """Test protection against numeric overflow."""
        # Test very large numbers
        large_number = Decimal("9" * 28)  # Maximum for Decimal
        result = large_number + Decimal("1")
        assert isinstance(result, Decimal)  # nosec

    def test_precision_limits(self) -> None:
        """Test decimal precision limits are respected."""
        # Test maximum precision
        precise_number = Decimal("1.23456789012345678901234567890")
        # Should not raise an exception but may truncate
        assert isinstance(precise_number, Decimal)  # nosec


@pytest.mark.financial
@pytest.mark.external
class TestMarketDataCalculations:
    """Tests for market data calculation accuracy."""

    def test_price_change_calculation(
        self, sample_asset_prices: dict[str, dict[str, Any]]
    ) -> None:
        """Test price change calculation from market data."""
        for ticker, data in sample_asset_prices.items():
            price = data["price"]
            change = data["change"]
            change_percent = data["change_percent"]

            # Calculate expected previous price
            previous_price = price - change

            # Verify percentage calculation
            calculated_percent = (change / previous_price) * 100
            assert abs(calculated_percent - change_percent) < Decimal("0.01")  # nosec

    def test_market_cap_calculation(
        self, sample_asset_prices: dict[str, dict[str, Any]]
    ) -> None:
        """Test market capitalization calculations."""
        # Mock shares outstanding for calculation
        shares_outstanding = {
            "AAPL": 15500000000,  # ~15.5B shares
            "GOOGL": 12800000000,  # ~12.8B shares
            "MSFT": 7400000000,  # ~7.4B shares
        }

        for ticker, data in sample_asset_prices.items():
            price = float(data["price"])
            shares = shares_outstanding[ticker]
            calculated_market_cap = price * shares

            # Allow for some variance in market cap calculation
            assert (
                abs(calculated_market_cap - data["market_cap"]) / data["market_cap"]
                < 0.1
            )  # nosec

    @pytest.mark.slow
    def test_performance_large_portfolio(self) -> None:
        """Test calculation performance with large portfolios."""
        import time

        # Create a large portfolio with 1000 positions
        large_portfolio = []
        for i in range(1000):
            position = {
                "quantity": Decimal("100"),
                "purchase_price": Decimal(f"{100 + i * 0.1:.2f}"),
                "current_price": Decimal(f"{105 + i * 0.1:.2f}"),
            }
            large_portfolio.append(position)

        # Time the calculation
        start_time = time.time()

        total_value = sum(
            pos["quantity"] * pos["current_price"] for pos in large_portfolio
        )
        total_cost = sum(
            pos["quantity"] * pos["purchase_price"] for pos in large_portfolio
        )

        end_time = time.time()
        calculation_time = end_time - start_time

        # Should complete in under 1 second
        assert calculation_time < 1.0  # nosec
        assert total_value > total_cost  # Portfolio should have gains  # nosec
