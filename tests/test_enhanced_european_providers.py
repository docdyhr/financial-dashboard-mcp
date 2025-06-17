"""Tests for enhanced European market data providers."""

from unittest.mock import patch

from backend.services.enhanced_european_providers import (
    EnhancedDeutscheBorseProvider,
    EnhancedEuronextProvider,
    EnhancedLondonStockExchangeProvider,
    EuropeanMarketDataAggregator,
)
from backend.services.market_data import MarketDataResult


class TestEnhancedDeutscheBorseProvider:
    """Test enhanced Deutsche Börse provider."""

    def setup_method(self):
        """Set up test instance."""
        self.provider = EnhancedDeutscheBorseProvider()

    def test_provider_initialization(self):
        """Test provider initialization."""
        assert self.provider.name == "Deutsche Börse (Enhanced)"
        assert self.provider.rate_limiter.delay == 1.0
        assert "xetra.com" in self.provider.base_url

    def test_is_isin_detection(self):
        """Test ISIN detection."""
        assert self.provider._is_isin("DE0007164600") is True
        assert self.provider._is_isin("SAP.DE") is False
        assert self.provider._is_isin("US0378331005") is True
        assert self.provider._is_isin("AAPL") is False

    def test_format_ticker_for_deutsche_borse(self):
        """Test ticker formatting for Deutsche Börse."""
        formatted = self.provider._format_ticker_for_deutsche_borse("SAP.DE")
        assert "SAP" in formatted
        assert "SAP.DE" in formatted
        assert "SAP.XETR" in formatted

        # Should remove duplicates
        assert len(formatted) == len(set(formatted))

    @patch.object(EnhancedDeutscheBorseProvider, "_make_request")
    def test_fetch_quote_success(self, mock_request):
        """Test successful quote fetch."""
        mock_request.return_value = {
            "quote": {
                "price": 120.50,
                "currency": "EUR",
                "change": 2.30,
                "changePercent": 1.95,
                "volume": 1000000,
            }
        }

        result = self.provider.fetch_quote("SAP.DE")

        assert result.success is True
        assert result.current_price == 120.50
        assert result.day_change == 2.30
        assert result.day_change_percent == 1.95
        assert result.volume == 1000000

    @patch.object(EnhancedDeutscheBorseProvider, "_make_request")
    def test_fetch_quote_failure(self, mock_request):
        """Test quote fetch failure."""
        mock_request.return_value = None

        result = self.provider.fetch_quote("INVALID")

        assert result.success is False
        assert "Ticker not found" in result.error
        assert len(result.suggestions) > 0

    def test_parse_deutsche_borse_response_invalid(self):
        """Test parsing invalid response."""
        result = self.provider._parse_deutsche_borse_response("TEST", {})

        assert result.success is False
        assert "Invalid response format" in result.error


class TestEnhancedEuronextProvider:
    """Test enhanced Euronext provider."""

    def setup_method(self):
        """Set up test instance."""
        self.provider = EnhancedEuronextProvider()

    def test_provider_initialization(self):
        """Test provider initialization."""
        assert self.provider.name == "Euronext (Enhanced)"
        assert self.provider.rate_limiter.delay == 0.5
        assert "euronext.com" in self.provider.base_url
        assert len(self.provider.markets) == 4

    def test_format_ticker_for_market(self):
        """Test ticker formatting for specific markets."""
        formatted = self.provider._format_ticker_for_market("ASML", "AS")
        assert formatted == "ASML.AS"

        # Should handle existing suffix
        formatted = self.provider._format_ticker_for_market("ASML.AS", "AS")
        assert formatted == "ASML.AS"

    def test_get_euronext_suggestions(self):
        """Test Euronext ticker suggestions."""
        suggestions = self.provider._get_euronext_suggestions("ASML")

        assert "ASML.PA" in suggestions
        assert "ASML.AS" in suggestions
        assert "ASML.BR" in suggestions
        assert "ASML.LS" in suggestions

    @patch.object(EnhancedEuronextProvider, "_make_request")
    def test_fetch_quote_success(self, mock_request):
        """Test successful Euronext quote fetch."""
        mock_request.return_value = {
            "data": {
                "last": 650.20,
                "currency": "EUR",
                "change": 15.50,
                "changePercent": 2.44,
                "volume": 500000,
                "high": 655.00,
                "low": 640.00,
            }
        }

        result = self.provider.fetch_quote("ASML.AS")

        assert result.success is True
        assert result.current_price == 650.20
        assert result.day_change == 15.50
        assert result.day_change_percent == 2.44
        assert result.volume == 500000
        assert result.high_price == 655.00
        assert result.low_price == 640.00


class TestEnhancedLondonStockExchangeProvider:
    """Test enhanced London Stock Exchange provider."""

    def setup_method(self):
        """Set up test instance."""
        self.provider = EnhancedLondonStockExchangeProvider()

    def test_provider_initialization(self):
        """Test provider initialization."""
        assert self.provider.name == "London Stock Exchange (Enhanced)"
        assert self.provider.rate_limiter.delay == 1.0
        assert "londonstockexchange.com" in self.provider.base_url

    def test_format_ticker_for_lse(self):
        """Test ticker formatting for LSE."""
        formatted = self.provider._format_ticker_for_lse("LLOY.L")

        assert "LLOY.L" in formatted
        assert "LLOY.LON" in formatted
        assert "LLOY" in formatted
        assert "LLOY.LSE" in formatted

    def test_get_lse_suggestions(self):
        """Test LSE ticker suggestions."""
        suggestions = self.provider._get_lse_suggestions("LLOY")

        assert "LLOY.L" in suggestions
        assert "LLOY.LON" in suggestions
        assert "LLOY.LSE" in suggestions

    @patch.object(EnhancedLondonStockExchangeProvider, "_make_request")
    def test_fetch_quote_success(self, mock_request):
        """Test successful LSE quote fetch."""
        mock_request.return_value = {
            "quote": {
                "price": 47.50,
                "currency": "GBP",
                "change": 0.75,
                "changePercent": 1.60,
                "volume": 25000000,
            }
        }

        result = self.provider.fetch_quote("LLOY.L")

        assert result.success is True
        assert result.current_price == 47.50
        assert result.day_change == 0.75
        assert result.day_change_percent == 1.60
        assert result.volume == 25000000


class TestEuropeanMarketDataAggregator:
    """Test European market data aggregator."""

    def setup_method(self):
        """Set up test instance."""
        self.aggregator = EuropeanMarketDataAggregator()

    def test_aggregator_initialization(self):
        """Test aggregator initialization."""
        assert self.aggregator.name == "European Markets Aggregator"
        assert len(self.aggregator.providers) == 3
        assert "deutsche_borse" in self.aggregator.providers
        assert "euronext" in self.aggregator.providers
        assert "lse" in self.aggregator.providers

    def test_get_provider_order_german_ticker(self):
        """Test provider order for German tickers."""
        order = self.aggregator._get_provider_order("SAP.DE")
        assert order[0] == "deutsche_borse"

        order = self.aggregator._get_provider_order("DE0007164600")
        assert order[0] == "deutsche_borse"

    def test_get_provider_order_uk_ticker(self):
        """Test provider order for UK tickers."""
        order = self.aggregator._get_provider_order("LLOY.L")
        assert order[0] == "lse"

        order = self.aggregator._get_provider_order("GB0002875804")
        assert order[0] == "lse"

    def test_get_provider_order_euronext_ticker(self):
        """Test provider order for Euronext tickers."""
        order = self.aggregator._get_provider_order("ASML.AS")
        assert order[0] == "euronext"

        order = self.aggregator._get_provider_order("NL0010273215")
        assert order[0] == "euronext"

    def test_get_provider_order_default(self):
        """Test default provider order."""
        order = self.aggregator._get_provider_order("UNKNOWN")
        assert order[0] == "euronext"  # Default first

    @patch.object(EnhancedDeutscheBorseProvider, "fetch_quote")
    def test_fetch_quote_success_first_provider(self, mock_fetch):
        """Test successful fetch from first provider."""
        mock_result = MarketDataResult(
            ticker="SAP.DE",
            success=True,
            current_price=120.50,
            data_source="Deutsche Börse (Enhanced)",
        )
        mock_fetch.return_value = mock_result

        result = self.aggregator.fetch_quote("SAP.DE")

        assert result.success is True
        assert result.current_price == 120.50
        assert "European Markets Aggregator" in result.data_source

    @patch.object(EnhancedDeutscheBorseProvider, "fetch_quote")
    @patch.object(EnhancedEuronextProvider, "fetch_quote")
    def test_fetch_quote_fallback_provider(self, mock_euronext, mock_deutsche):
        """Test fallback to second provider."""
        # First provider fails
        mock_deutsche.return_value = MarketDataResult(
            ticker="SAP.DE", success=False, error="First provider failed"
        )

        # Second provider succeeds
        mock_euronext.return_value = MarketDataResult(
            ticker="SAP.DE",
            success=True,
            current_price=120.50,
            data_source="Euronext (Enhanced)",
        )

        result = self.aggregator.fetch_quote("SAP.DE")

        assert result.success is True
        assert result.current_price == 120.50
        assert "European Markets Aggregator" in result.data_source

    @patch.object(EnhancedDeutscheBorseProvider, "fetch_quote")
    @patch.object(EnhancedEuronextProvider, "fetch_quote")
    @patch.object(EnhancedLondonStockExchangeProvider, "fetch_quote")
    def test_fetch_quote_all_providers_fail(
        self, mock_lse, mock_euronext, mock_deutsche
    ):
        """Test when all providers fail."""
        # All providers fail
        for mock_provider in [mock_deutsche, mock_euronext, mock_lse]:
            mock_provider.return_value = MarketDataResult(
                ticker="INVALID", success=False, error="Provider failed"
            )

        result = self.aggregator.fetch_quote("INVALID")

        assert result.success is False
        assert "All European providers failed" in result.error
        assert len(result.suggestions) > 0

    def test_get_provider_status(self):
        """Test provider status check."""
        status = self.aggregator.get_provider_status()

        assert len(status) == 3
        assert "deutsche_borse" in status
        assert "euronext" in status
        assert "lse" in status

        # Check status structure
        for provider_status in status.values():
            assert "name" in provider_status
            assert "rate_limit_delay" in provider_status
            assert "available" in provider_status


class TestProviderSingletons:
    """Test provider singleton functions."""

    def test_singleton_functions(self):
        """Test that singleton functions work correctly."""
        from backend.services.enhanced_european_providers import (
            get_enhanced_deutsche_borse_provider,
            get_enhanced_euronext_provider,
            get_enhanced_lse_provider,
            get_european_market_aggregator,
        )

        # Test each singleton
        provider1 = get_enhanced_deutsche_borse_provider()
        provider2 = get_enhanced_deutsche_borse_provider()
        assert provider1 is provider2
        assert isinstance(provider1, EnhancedDeutscheBorseProvider)

        provider1 = get_enhanced_euronext_provider()
        provider2 = get_enhanced_euronext_provider()
        assert provider1 is provider2
        assert isinstance(provider1, EnhancedEuronextProvider)

        provider1 = get_enhanced_lse_provider()
        provider2 = get_enhanced_lse_provider()
        assert provider1 is provider2
        assert isinstance(provider1, EnhancedLondonStockExchangeProvider)

        aggregator1 = get_european_market_aggregator()
        aggregator2 = get_european_market_aggregator()
        assert aggregator1 is aggregator2
        assert isinstance(aggregator1, EuropeanMarketDataAggregator)
