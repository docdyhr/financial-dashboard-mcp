"""Comprehensive tests for MarketDataService and providers."""

from decimal import Decimal
import time
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from backend.models.asset import Asset
from backend.models.price_history import PriceHistory
from backend.services.market_data import (
    AlphaVantageProvider,
    FinnhubProvider,
    MarketDataProvider,
    MarketDataResult,
    MultiProviderMarketDataService,
    YFinanceProvider,
    market_data_service,
)


class TestMarketDataResult:
    """Test suite for MarketDataResult dataclass."""

    def test_market_data_result_default_values(self):
        """Test MarketDataResult with default values."""
        result = MarketDataResult(ticker="AAPL")

        assert result.ticker == "AAPL"
        assert result.current_price is None
        assert result.success is False
        assert result.error is None
        assert result.data_source is None

    def test_market_data_result_with_values(self):
        """Test MarketDataResult with all values populated."""
        result = MarketDataResult(
            ticker="AAPL",
            current_price=150.0,
            open_price=148.0,
            high_price=152.0,
            low_price=147.0,
            volume=1000000,
            previous_close=149.0,
            day_change=1.0,
            day_change_percent=0.67,
            data_source="test_provider",
            success=True,
        )

        assert result.ticker == "AAPL"
        assert result.current_price == 150.0
        assert result.open_price == 148.0
        assert result.high_price == 152.0
        assert result.low_price == 147.0
        assert result.volume == 1000000
        assert result.previous_close == 149.0
        assert result.day_change == 1.0
        assert result.day_change_percent == 0.67
        assert result.data_source == "test_provider"
        assert result.success is True


class TestMarketDataProvider:
    """Test suite for base MarketDataProvider class."""

    def test_provider_initialization(self):
        """Test provider initialization."""
        provider = MarketDataProvider("test_provider")
        assert provider.name == "test_provider"

    def test_fetch_quote_not_implemented(self):
        """Test that fetch_quote raises NotImplementedError."""
        provider = MarketDataProvider("test_provider")

        with pytest.raises(NotImplementedError):
            provider.fetch_quote("AAPL")

    def test_fetch_multiple_quotes(self):
        """Test fetch_multiple_quotes default implementation."""
        provider = MarketDataProvider("test_provider")

        # Mock the fetch_quote method
        mock_result = MarketDataResult(ticker="AAPL", success=True)
        provider.fetch_quote = Mock(return_value=mock_result)

        with patch("time.sleep") as mock_sleep:
            results = provider.fetch_multiple_quotes(["AAPL", "GOOGL"])

            assert len(results) == 2
            assert all(result.success for result in results)
            # Verify sleep was called for rate limiting
            assert mock_sleep.call_count == 2


class TestYFinanceProvider:
    """Test suite for YFinanceProvider."""

    @pytest.fixture
    def yfinance_provider(self):
        """Create YFinanceProvider instance."""
        return YFinanceProvider()

    def test_yfinance_provider_initialization(self, yfinance_provider):
        """Test YFinanceProvider initialization."""
        assert yfinance_provider.name == "yfinance"
        assert yfinance_provider.rate_limit_delay == 1.0
        assert yfinance_provider.last_call_time == 0

    def test_respect_rate_limit_no_delay_needed(self, yfinance_provider):
        """Test rate limiting when no delay is needed."""
        yfinance_provider.last_call_time = time.time() - 2.0  # 2 seconds ago

        with patch("time.sleep") as mock_sleep:
            yfinance_provider._respect_rate_limit()
            mock_sleep.assert_not_called()

    def test_respect_rate_limit_delay_needed(self, yfinance_provider):
        """Test rate limiting when delay is needed."""
        yfinance_provider.last_call_time = time.time() - 0.5  # 0.5 seconds ago

        with (
            patch("time.sleep") as mock_sleep,
            patch("time.time", return_value=time.time()),
        ):
            yfinance_provider._respect_rate_limit()
            mock_sleep.assert_called_once()

    @patch("backend.services.market_data.yf.Ticker")
    @patch("backend.services.ticker_utils.TickerUtils.format_for_yfinance")
    @patch("backend.services.ticker_utils.TickerUtils.parse_ticker")
    def test_fetch_quote_success(
        self, mock_parse_ticker, mock_format_ticker, mock_yf_ticker, yfinance_provider
    ):
        """Test successful quote fetch."""
        # Mock ticker parsing
        mock_ticker_info = Mock()
        mock_ticker_info.is_international = False
        mock_parse_ticker.return_value = mock_ticker_info
        mock_format_ticker.return_value = "AAPL"

        # Mock yfinance data
        mock_hist = Mock()
        mock_hist.empty = False
        mock_hist.__len__ = Mock(return_value=2)

        # Create proper iloc mock objects
        close_iloc = Mock()
        close_iloc.__getitem__ = Mock(side_effect=lambda x: 149.0 if x == -2 else 150.0)

        open_iloc = Mock()
        open_iloc.__getitem__ = Mock(return_value=148.0)

        high_iloc = Mock()
        high_iloc.__getitem__ = Mock(return_value=152.0)

        low_iloc = Mock()
        low_iloc.__getitem__ = Mock(return_value=147.0)

        volume_iloc = Mock()
        volume_iloc.__getitem__ = Mock(return_value=1000000)

        mock_hist.__getitem__ = Mock(
            side_effect=lambda key: {
                "Close": Mock(iloc=close_iloc),
                "Open": Mock(iloc=open_iloc),
                "High": Mock(iloc=high_iloc),
                "Low": Mock(iloc=low_iloc),
                "Volume": Mock(iloc=volume_iloc),
            }[key]
        )
        mock_hist.columns = ["Close", "Open", "High", "Low", "Volume"]

        mock_stock = Mock()
        mock_stock.history.return_value = mock_hist
        mock_yf_ticker.return_value = mock_stock

        with patch.object(yfinance_provider, "_respect_rate_limit"):
            result = yfinance_provider.fetch_quote("AAPL")

            assert result.success is True
            assert result.ticker == "AAPL"
            assert result.current_price == 150.0
            assert result.open_price == 148.0
            assert result.high_price == 152.0
            assert result.low_price == 147.0
            assert result.volume == 1000000
            assert result.previous_close == 149.0
            assert result.day_change == 1.0
            assert result.day_change_percent == pytest.approx(0.671, rel=1e-2)
            assert result.data_source == "yfinance"

    @patch("backend.services.market_data.yf.Ticker")
    @patch("backend.services.ticker_utils.TickerUtils.format_for_yfinance")
    @patch("backend.services.ticker_utils.TickerUtils.parse_ticker")
    def test_fetch_quote_no_history_with_info(
        self, mock_parse_ticker, mock_format_ticker, mock_yf_ticker, yfinance_provider
    ):
        """Test quote fetch when history is empty but info is available."""
        # Mock ticker parsing
        mock_ticker_info = Mock()
        mock_ticker_info.is_international = False
        mock_parse_ticker.return_value = mock_ticker_info
        mock_format_ticker.return_value = "AAPL"

        # Mock empty history but available info
        mock_hist = Mock()
        mock_hist.empty = True

        mock_info = {"regularMarketPrice": 150.0}
        mock_stock = Mock()
        mock_stock.history.return_value = mock_hist
        mock_stock.info = mock_info
        mock_yf_ticker.return_value = mock_stock

        with patch.object(yfinance_provider, "_respect_rate_limit"):
            result = yfinance_provider.fetch_quote("AAPL")

            assert result.success is True
            assert result.current_price == 150.0
            assert result.data_source == "yfinance"

    @patch("backend.services.market_data.yf.Ticker")
    @patch("backend.services.ticker_utils.TickerUtils.format_for_yfinance")
    @patch("backend.services.ticker_utils.TickerUtils.parse_ticker")
    def test_fetch_quote_no_data(
        self, mock_parse_ticker, mock_format_ticker, mock_yf_ticker, yfinance_provider
    ):
        """Test quote fetch when no data is available."""
        # Mock ticker parsing
        mock_ticker_info = Mock()
        mock_ticker_info.is_international = False
        mock_parse_ticker.return_value = mock_ticker_info
        mock_format_ticker.return_value = "AAPL"

        # Mock empty history and no info
        mock_hist = Mock()
        mock_hist.empty = True

        mock_stock = Mock()
        mock_stock.history.return_value = mock_hist
        mock_stock.info = {}
        mock_yf_ticker.return_value = mock_stock

        with patch.object(yfinance_provider, "_respect_rate_limit"):
            result = yfinance_provider.fetch_quote("AAPL")

            assert result.success is False
            assert result.error == "No historical data available"
            assert result.data_source == "yfinance"

    @patch("backend.services.market_data.yf.Ticker")
    @patch("backend.services.ticker_utils.TickerUtils.format_for_yfinance")
    @patch("backend.services.ticker_utils.TickerUtils.parse_ticker")
    def test_fetch_quote_exception(
        self, mock_parse_ticker, mock_format_ticker, mock_yf_ticker, yfinance_provider
    ):
        """Test quote fetch when an exception occurs."""
        # Mock ticker parsing
        mock_ticker_info = Mock()
        mock_ticker_info.is_international = False
        mock_ticker_info.base_ticker = "AAPL"
        mock_ticker_info.exchange_suffix = None
        mock_parse_ticker.return_value = mock_ticker_info
        mock_format_ticker.return_value = "AAPL"

        # Mock exception
        mock_yf_ticker.side_effect = Exception("Network error")

        with patch.object(yfinance_provider, "_respect_rate_limit"):
            result = yfinance_provider.fetch_quote("AAPL")

            assert result.success is False
            assert "Network error" in result.error
            assert result.data_source == "yfinance"


class TestAlphaVantageProvider:
    """Test suite for AlphaVantageProvider."""

    @pytest.fixture
    def alphavantage_provider(self):
        """Create AlphaVantageProvider instance."""
        return AlphaVantageProvider("test_api_key")

    def test_alphavantage_provider_initialization(self, alphavantage_provider):
        """Test AlphaVantageProvider initialization."""
        assert alphavantage_provider.name == "alpha_vantage"
        assert alphavantage_provider.api_key == "test_api_key"
        assert alphavantage_provider.rate_limit_delay == 12

    @patch("requests.get")
    @patch("backend.services.ticker_utils.TickerUtils.format_for_alpha_vantage")
    @patch("backend.services.ticker_utils.TickerUtils.parse_ticker")
    def test_fetch_quote_success(
        self,
        mock_parse_ticker,
        mock_format_ticker,
        mock_requests_get,
        alphavantage_provider,
    ):
        """Test successful quote fetch from Alpha Vantage."""
        # Mock ticker parsing
        mock_ticker_info = Mock()
        mock_ticker_info.is_international = False
        mock_parse_ticker.return_value = mock_ticker_info
        mock_format_ticker.return_value = "AAPL"

        # Mock successful API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "Global Quote": {
                "05. price": "150.00",
                "02. open": "148.00",
                "03. high": "152.00",
                "04. low": "147.00",
                "06. volume": "1000000",
                "08. previous close": "149.00",
                "09. change": "1.00",
                "10. change percent": "0.67%",
            }
        }
        mock_requests_get.return_value = mock_response

        with patch.object(alphavantage_provider, "_respect_rate_limit"):
            result = alphavantage_provider.fetch_quote("AAPL")

            assert result.success is True
            assert result.current_price == 150.0
            assert result.open_price == 148.0
            assert result.high_price == 152.0
            assert result.low_price == 147.0
            assert result.volume == 1000000
            assert result.previous_close == 149.0
            assert result.day_change == 1.0
            assert result.day_change_percent == 0.67
            assert result.data_source == "alpha_vantage"

    @patch("requests.get")
    @patch("backend.services.ticker_utils.TickerUtils.format_for_alpha_vantage")
    @patch("backend.services.ticker_utils.TickerUtils.parse_ticker")
    def test_fetch_quote_error_message(
        self,
        mock_parse_ticker,
        mock_format_ticker,
        mock_requests_get,
        alphavantage_provider,
    ):
        """Test quote fetch when API returns error message."""
        # Mock ticker parsing
        mock_ticker_info = Mock()
        mock_ticker_info.is_international = False
        mock_parse_ticker.return_value = mock_ticker_info
        mock_format_ticker.return_value = "INVALID"

        # Mock API error response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"Error Message": "Invalid API call"}
        mock_requests_get.return_value = mock_response

        with patch.object(alphavantage_provider, "_respect_rate_limit"):
            result = alphavantage_provider.fetch_quote("INVALID")

            assert result.success is False
            assert result.error == "Invalid API call"
            assert result.data_source == "alpha_vantage"

    @patch("requests.get")
    @patch("backend.services.ticker_utils.TickerUtils.format_for_alpha_vantage")
    @patch("backend.services.ticker_utils.TickerUtils.parse_ticker")
    def test_fetch_quote_rate_limit(
        self,
        mock_parse_ticker,
        mock_format_ticker,
        mock_requests_get,
        alphavantage_provider,
    ):
        """Test quote fetch when rate limit is hit."""
        # Mock ticker parsing
        mock_ticker_info = Mock()
        mock_ticker_info.is_international = False
        mock_parse_ticker.return_value = mock_ticker_info
        mock_format_ticker.return_value = "AAPL"

        # Mock rate limit response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "Note": "Thank you for using Alpha Vantage! Rate limit exceeded."
        }
        mock_requests_get.return_value = mock_response

        with patch.object(alphavantage_provider, "_respect_rate_limit"):
            result = alphavantage_provider.fetch_quote("AAPL")

            assert result.success is False
            assert result.error == "API rate limit exceeded"
            assert result.data_source == "alpha_vantage"


class TestFinnhubProvider:
    """Test suite for FinnhubProvider."""

    @pytest.fixture
    def finnhub_provider(self):
        """Create FinnhubProvider instance."""
        return FinnhubProvider("test_api_key")

    def test_finnhub_provider_initialization(self, finnhub_provider):
        """Test FinnhubProvider initialization."""
        assert finnhub_provider.name == "finnhub"
        assert finnhub_provider.api_key == "test_api_key"
        assert finnhub_provider.rate_limit_delay == 1

    @patch("requests.get")
    @patch("backend.services.ticker_utils.TickerUtils.parse_ticker")
    def test_fetch_quote_success(
        self, mock_parse_ticker, mock_requests_get, finnhub_provider
    ):
        """Test successful quote fetch from Finnhub."""
        # Mock ticker parsing
        mock_ticker_info = Mock()
        mock_ticker_info.is_international = False
        mock_ticker_info.base_ticker = "AAPL"
        mock_parse_ticker.return_value = mock_ticker_info

        # Mock successful API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "c": 150.0,  # current price
            "o": 148.0,  # open
            "h": 152.0,  # high
            "l": 147.0,  # low
            "pc": 149.0,  # previous close
        }
        mock_requests_get.return_value = mock_response

        with patch.object(finnhub_provider, "_respect_rate_limit"):
            result = finnhub_provider.fetch_quote("AAPL")

            assert result.success is True
            assert result.current_price == 150.0
            assert result.open_price == 148.0
            assert result.high_price == 152.0
            assert result.low_price == 147.0
            assert result.previous_close == 149.0
            assert result.day_change == 1.0
            assert result.day_change_percent == pytest.approx(0.671, rel=1e-2)
            assert result.data_source == "finnhub"


class TestMultiProviderMarketDataService:
    """Test suite for MultiProviderMarketDataService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def market_service(self):
        """Create MultiProviderMarketDataService instance."""
        with patch("backend.services.market_data.settings") as mock_settings:
            mock_settings.alpha_vantage_api_key = None
            mock_settings.finnhub_api_key = None
            return MultiProviderMarketDataService()

    def test_service_initialization_no_api_keys(self, market_service):
        """Test service initialization with no API keys."""
        assert len(market_service.providers) == 1  # Only YFinance
        assert market_service.providers[0].name == "yfinance"

    def test_service_initialization_with_api_keys(self):
        """Test service initialization with API keys."""
        with patch("backend.services.market_data.settings") as mock_settings:
            mock_settings.alpha_vantage_api_key = "test_av_key"
            mock_settings.finnhub_api_key = "test_fh_key"

            service = MultiProviderMarketDataService()

            assert len(service.providers) == 3  # YFinance, AlphaVantage, Finnhub
            provider_names = [p.name for p in service.providers]
            assert "yfinance" in provider_names
            assert "alpha_vantage" in provider_names
            assert "finnhub" in provider_names

    def test_fetch_quote_success_first_provider(self, market_service):
        """Test successful quote fetch from first provider."""
        # Mock successful result
        mock_result = MarketDataResult(
            ticker="AAPL", current_price=150.0, success=True, data_source="yfinance"
        )

        market_service.providers[0].fetch_quote = Mock(return_value=mock_result)

        result = market_service.fetch_quote("AAPL")

        assert result.success is True
        assert result.current_price == 150.0
        assert result.data_source == "yfinance"

    def test_fetch_quote_fallback_to_second_provider(self):
        """Test quote fetch with fallback to second provider."""
        with patch("backend.services.market_data.get_settings") as mock_settings:
            mock_settings.return_value.alpha_vantage_api_key = "test_key"
            mock_settings.return_value.finnhub_api_key = None

            service = MultiProviderMarketDataService()

            # Mock first provider failure, second provider success
            failed_result = MarketDataResult(
                ticker="AAPL", success=False, error="Network error"
            )
            success_result = MarketDataResult(
                ticker="AAPL",
                current_price=150.0,
                success=True,
                data_source="alpha_vantage",
            )

            service.providers[0].fetch_quote = Mock(return_value=failed_result)
            service.providers[1].fetch_quote = Mock(return_value=success_result)

            result = service.fetch_quote("AAPL")

            assert result.success is True
            assert result.current_price == 150.0
            assert result.data_source == "alpha_vantage"

    def test_fetch_quote_all_providers_fail(self, market_service):
        """Test quote fetch when all providers fail."""
        failed_result = MarketDataResult(
            ticker="AAPL", success=False, error="Network error"
        )
        market_service.providers[0].fetch_quote = Mock(return_value=failed_result)

        result = market_service.fetch_quote("AAPL")

        assert result.success is False
        assert "All providers failed" in result.error
        assert result.data_source == "multi_provider"

    @patch("backend.services.isin_utils.ISINUtils.is_isin_format")
    @patch("backend.services.market_data.isin_service")
    def test_fetch_quote_with_isin_resolution(
        self, mock_isin_service, mock_is_isin, market_service, mock_db
    ):
        """Test quote fetch with ISIN resolution."""
        mock_is_isin.return_value = True
        mock_isin_service.resolve_identifier.return_value = ("AAPL", "ticker", {})

        # Mock successful result
        mock_result = MarketDataResult(
            ticker="AAPL", current_price=150.0, success=True, data_source="yfinance"
        )
        market_service.providers[0].fetch_quote = Mock(return_value=mock_result)

        result = market_service.fetch_quote("US0378331005", mock_db)  # AAPL ISIN

        assert result.success is True
        # Note: The service updates the ticker to the original ISIN only if identifier_type == "isin"
        # but our mock returns "ticker", so the ticker won't be updated
        assert result.current_price == 150.0
        mock_isin_service.resolve_identifier.assert_called_once()

    @patch("backend.services.isin_utils.ISINUtils.validate_isin")
    @patch("backend.services.market_data.isin_service")
    def test_fetch_quote_by_isin_success(
        self, mock_isin_service, mock_validate_isin, market_service, mock_db
    ):
        """Test successful quote fetch by ISIN."""
        mock_validate_isin.return_value = (True, None)
        mock_isin_service.resolve_identifier.return_value = ("AAPL", "ticker", {})

        # Mock successful quote fetch
        mock_result = MarketDataResult(
            ticker="AAPL", current_price=150.0, success=True, data_source="yfinance"
        )
        market_service.fetch_quote = Mock(return_value=mock_result)

        result = market_service.fetch_quote_by_isin(mock_db, "US0378331005")

        assert result.success is True
        assert result.ticker == "US0378331005"  # ISIN preserved in result
        assert result.current_price == 150.0

    @patch("backend.services.isin_utils.ISINUtils.validate_isin")
    def test_fetch_quote_by_isin_invalid(
        self, mock_validate_isin, market_service, mock_db
    ):
        """Test quote fetch by invalid ISIN."""
        mock_validate_isin.return_value = (False, "Invalid checksum")

        result = market_service.fetch_quote_by_isin(mock_db, "INVALID_ISIN")

        assert result.success is False
        assert "Invalid ISIN" in result.error
        assert result.data_source == "isin_validation"

    def test_fetch_multiple_quotes(self, market_service):
        """Test fetching multiple quotes."""
        # Mock multiple successful results
        mock_results = [
            MarketDataResult(
                ticker="AAPL", current_price=150.0, success=True, data_source="yfinance"
            ),
            MarketDataResult(
                ticker="GOOGL",
                current_price=2500.0,
                success=True,
                data_source="yfinance",
            ),
        ]

        market_service.fetch_quote = Mock(side_effect=mock_results)

        results = market_service.fetch_multiple_quotes(["AAPL", "GOOGL"])

        assert len(results) == 2
        assert all(result.success for result in results)
        assert results[0].ticker == "AAPL"
        assert results[1].ticker == "GOOGL"

    def test_update_asset_prices_success(self, market_service, mock_db):
        """Test successful asset price updates."""
        # Mock successful quote fetch
        mock_result = MarketDataResult(
            ticker="AAPL",
            current_price=150.0,
            open_price=148.0,
            high_price=152.0,
            low_price=147.0,
            volume=1000000,
            previous_close=149.0,
            day_change=1.0,
            day_change_percent=0.67,
            success=True,
            data_source="yfinance",
        )
        market_service.fetch_multiple_quotes = Mock(return_value=[mock_result])

        # Mock asset in database
        mock_asset = Mock(spec=Asset)
        mock_asset.id = 1

        # Mock query chain for asset lookup and price history lookup
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_asset,  # Asset found
            None,  # No existing price history
        ]

        result = market_service.update_asset_prices(mock_db, ["AAPL"])

        assert result["status"] == "completed"
        assert result["updated_count"] == 1
        assert result["failed_count"] == 0
        assert result["total_tickers"] == 1
        mock_db.commit.assert_called_once()

    def test_update_asset_prices_asset_not_found(self, market_service, mock_db):
        """Test asset price update when asset not found in database."""
        # Mock successful quote fetch
        mock_result = MarketDataResult(
            ticker="AAPL", current_price=150.0, success=True, data_source="yfinance"
        )
        market_service.fetch_multiple_quotes = Mock(return_value=[mock_result])

        # Mock asset not found
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = market_service.update_asset_prices(mock_db, ["AAPL"])

        assert result["status"] == "completed"
        assert result["updated_count"] == 0
        # When asset is not found, it doesn't increment failed_count, just continues
        assert result["failed_count"] == 0
        assert result["failed_tickers"] == []

    def test_update_asset_prices_quote_failed(self, market_service, mock_db):
        """Test asset price update when quote fetch fails."""
        # Mock failed quote fetch
        mock_result = MarketDataResult(
            ticker="AAPL", success=False, error="Network error"
        )
        market_service.fetch_multiple_quotes = Mock(return_value=[mock_result])

        result = market_service.update_asset_prices(mock_db, ["AAPL"])

        assert result["status"] == "completed"
        assert result["updated_count"] == 0
        assert result["failed_count"] == 1
        assert "AAPL" in result["failed_tickers"]

    def test_update_asset_prices_existing_price_history(self, market_service, mock_db):
        """Test asset price update with existing price history."""
        # Mock successful quote fetch
        mock_result = MarketDataResult(
            ticker="AAPL",
            current_price=150.0,
            open_price=148.0,
            success=True,
            data_source="yfinance",
        )
        market_service.fetch_multiple_quotes = Mock(return_value=[mock_result])

        # Mock asset in database
        mock_asset = Mock(spec=Asset)
        mock_asset.id = 1

        # Mock existing price history
        mock_price_record = Mock(spec=PriceHistory)

        # Setup query mocks for asset and price history
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_asset,  # Asset query
            mock_price_record,  # Price history query
        ]

        result = market_service.update_asset_prices(mock_db, ["AAPL"])

        assert result["status"] == "completed"
        assert result["updated_count"] == 1
        assert result["failed_count"] == 0
        # Verify existing price record was updated
        assert mock_price_record.close_price == Decimal("150.0")

    def test_update_asset_prices_commit_error(self, market_service, mock_db):
        """Test asset price update when database commit fails."""
        # Mock successful quote fetch
        mock_result = MarketDataResult(
            ticker="AAPL", current_price=150.0, success=True, data_source="yfinance"
        )
        market_service.fetch_multiple_quotes = Mock(return_value=[mock_result])

        # Mock asset in database
        mock_asset = Mock(spec=Asset)
        mock_asset.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_asset

        # Mock commit error
        mock_db.commit.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            market_service.update_asset_prices(mock_db, ["AAPL"])

        mock_db.rollback.assert_called_once()


class TestGlobalMarketDataService:
    """Test suite for global market_data_service instance."""

    def test_global_service_instance(self):
        """Test that global service instance exists and is properly configured."""
        assert market_data_service is not None
        assert isinstance(market_data_service, MultiProviderMarketDataService)
        assert len(market_data_service.providers) >= 1  # At least YFinance
