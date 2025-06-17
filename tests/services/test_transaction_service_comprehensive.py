"""Comprehensive tests for TransactionService."""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from backend.models.asset import Asset, AssetCategory, AssetType
from backend.models.position import Position
from backend.models.transaction import Transaction, TransactionType
from backend.schemas.transaction import (
    BuyTransactionRequest,
    DividendTransactionRequest,
    SellTransactionRequest,
    TransactionFilters,
    TransactionPerformanceMetrics,
    TransactionResponse,
)
from backend.services.transaction import TransactionService


class TestTransactionService:
    """Test suite for TransactionService."""

    @pytest.fixture
    def transaction_service(self):
        """Create transaction service instance."""
        return TransactionService()

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def mock_asset(self):
        """Create mock asset."""
        asset = Mock(spec=Asset)
        asset.id = 1
        asset.ticker = "AAPL"
        asset.name = "Apple Inc."
        asset.asset_type = AssetType.STOCK
        asset.category = AssetCategory.EQUITY
        return asset

    @pytest.fixture
    def mock_position(self):
        """Create mock position."""
        position = Mock(spec=Position)
        position.id = 1
        position.user_id = 1
        position.asset_id = 1
        position.quantity = Decimal("100")
        position.average_cost_per_share = Decimal("150.00")
        position.total_cost_basis = Decimal("15000.00")
        position.is_active = True
        return position

    @pytest.fixture
    def mock_transaction(self, mock_asset):
        """Create mock transaction."""
        transaction = Mock(spec=Transaction)
        transaction.id = 1
        transaction.user_id = 1
        transaction.asset_id = 1
        transaction.position_id = 1
        transaction.transaction_type = TransactionType.BUY
        transaction.transaction_date = date.today()
        transaction.settlement_date = date.today()
        transaction.quantity = Decimal("10")
        transaction.price_per_share = Decimal("150.00")
        transaction.total_amount = Decimal("1500.00")
        transaction.commission = Decimal("5.00")
        transaction.regulatory_fees = Decimal("1.00")
        transaction.other_fees = Decimal("0.50")
        transaction.tax_withheld = Decimal("0")
        transaction.account_name = "test_account"
        transaction.notes = "Test transaction"
        transaction.currency = "USD"
        transaction.exchange_rate = Decimal("1.0")
        transaction.order_id = "ORDER123"
        transaction.confirmation_number = "CONF123"
        transaction.split_ratio = None
        transaction.data_source = "manual"
        transaction.external_id = None
        transaction.net_amount = Decimal("1493.50")  # total - fees
        transaction.is_sell_transaction = False
        transaction.affects_position = True
        transaction.asset = mock_asset
        transaction.created_at = date.today()
        transaction.updated_at = date.today()
        return transaction

    def test_init(self, transaction_service):
        """Test TransactionService initialization."""
        assert hasattr(transaction_service, "model")
        assert transaction_service.model == Transaction

    def test_get_user_transactions_no_filters(
        self, transaction_service, mock_db, mock_transaction
    ):
        """Test getting user transactions without filters."""
        mock_db.query.return_value.options.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            mock_transaction
        ]

        with patch.object(transaction_service, "_to_response") as mock_to_response:
            mock_response = Mock(spec=TransactionResponse)
            mock_to_response.return_value = mock_response

            result = transaction_service.get_user_transactions(mock_db, 1)

            assert len(result) == 1
            assert result[0] == mock_response
            mock_db.query.assert_called_with(Transaction)

    def test_get_user_transactions_with_filters(
        self, transaction_service, mock_db, mock_transaction
    ):
        """Test getting user transactions with filters."""
        filters = TransactionFilters(
            asset_id=1,
            transaction_type=TransactionType.BUY,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today(),
            min_amount=Decimal("100"),
            max_amount=Decimal("2000"),
        )

        # Mock the query chain
        query_mock = Mock()
        mock_db.query.return_value = query_mock
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [mock_transaction]

        with patch.object(transaction_service, "_to_response") as mock_to_response:
            mock_response = Mock(spec=TransactionResponse)
            mock_to_response.return_value = mock_response

            result = transaction_service.get_user_transactions(mock_db, 1, filters)

            assert len(result) == 1
            assert result[0] == mock_response
            # Verify filters were applied (query.filter called multiple times)
            assert (
                query_mock.filter.call_count >= 6
            )  # At least 6 filter calls for the given filters

    def test_get_position_transactions(
        self, transaction_service, mock_db, mock_transaction
    ):
        """Test getting transactions for a specific position."""
        mock_db.query.return_value.options.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            mock_transaction
        ]

        with patch.object(transaction_service, "_to_response") as mock_to_response:
            mock_response = Mock(spec=TransactionResponse)
            mock_to_response.return_value = mock_response

            result = transaction_service.get_position_transactions(mock_db, 1)

            assert len(result) == 1
            assert result[0] == mock_response

    def test_create_buy_transaction_new_position(
        self, transaction_service, mock_db, mock_asset
    ):
        """Test creating a buy transaction with new position."""
        buy_request = BuyTransactionRequest(
            asset_id=1,
            quantity=Decimal("10"),
            price_per_share=Decimal("150.00"),
            transaction_date=date.today(),
            commission=Decimal("5.00"),
            account_name="test_account",
        )

        # Mock asset query
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_asset,  # Asset found
            None,  # No existing position
        ]

        # Mock transaction creation
        mock_transaction = Mock(spec=Transaction)
        with patch(
            "backend.models.transaction.Transaction.create_buy"
        ) as mock_create_buy:
            mock_create_buy.return_value = mock_transaction

            with patch("backend.models.position.Position") as mock_position_class:
                mock_position = Mock()
                mock_position.id = 1
                mock_position_class.return_value = mock_position

                with patch.object(
                    transaction_service, "_to_response"
                ) as mock_to_response:
                    mock_response = Mock(spec=TransactionResponse)
                    mock_to_response.return_value = mock_response

                    result = transaction_service.create_buy_transaction(
                        mock_db, 1, buy_request
                    )

                    assert result == mock_response
                    mock_db.add.assert_called()
                    mock_db.commit.assert_called()

    def test_create_buy_transaction_existing_position(
        self, transaction_service, mock_db, mock_asset, mock_position
    ):
        """Test creating a buy transaction with existing position."""
        buy_request = BuyTransactionRequest(
            asset_id=1,
            quantity=Decimal("10"),
            price_per_share=Decimal("150.00"),
            transaction_date=date.today(),
            commission=Decimal("5.00"),
            account_name="test_account",
        )

        # Mock queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_asset,  # Asset found
            mock_position,  # Existing position found
        ]

        # Mock transaction creation
        mock_transaction = Mock(spec=Transaction)
        with patch(
            "backend.models.transaction.Transaction.create_buy"
        ) as mock_create_buy:
            mock_create_buy.return_value = mock_transaction

            with patch.object(transaction_service, "_to_response") as mock_to_response:
                mock_response = Mock(spec=TransactionResponse)
                mock_to_response.return_value = mock_response

                result = transaction_service.create_buy_transaction(
                    mock_db, 1, buy_request
                )

                assert result == mock_response
                mock_position.update_cost_basis.assert_called_once()
                mock_db.add.assert_called_with(mock_transaction)
                mock_db.commit.assert_called()

    def test_create_buy_transaction_asset_not_found(self, transaction_service, mock_db):
        """Test creating buy transaction when asset doesn't exist."""
        buy_request = BuyTransactionRequest(
            asset_id=999,
            quantity=Decimal("10"),
            price_per_share=Decimal("150.00"),
            transaction_date=date.today(),
            commission=Decimal("5.00"),
            account_name="test_account",
        )

        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Asset with ID 999 not found"):
            transaction_service.create_buy_transaction(mock_db, 1, buy_request)

    def test_create_sell_transaction_success(
        self, transaction_service, mock_db, mock_position
    ):
        """Test creating a successful sell transaction."""
        sell_request = SellTransactionRequest(
            position_id=1,
            quantity=Decimal("5"),
            price_per_share=Decimal("160.00"),
            transaction_date=date.today(),
            commission=Decimal("5.00"),
            account_name="test_account",
        )

        mock_position.asset_id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_position
        )
        mock_position.reduce_position.return_value = Decimal(
            "750.00"
        )  # Cost basis of sold shares

        # Mock transaction creation
        mock_transaction = Mock(spec=Transaction)
        with patch(
            "backend.models.transaction.Transaction.create_sell"
        ) as mock_create_sell:
            mock_create_sell.return_value = mock_transaction

            with patch.object(transaction_service, "_to_response") as mock_to_response:
                mock_response = Mock(spec=TransactionResponse)
                mock_to_response.return_value = mock_response

                result = transaction_service.create_sell_transaction(
                    mock_db, 1, sell_request
                )

                assert result == mock_response
                mock_position.reduce_position.assert_called_once_with(Decimal("5"))
                mock_db.add.assert_called_with(mock_transaction)
                mock_db.commit.assert_called()

    def test_create_sell_transaction_position_not_found(
        self, transaction_service, mock_db
    ):
        """Test creating sell transaction when position doesn't exist."""
        sell_request = SellTransactionRequest(
            position_id=999,
            quantity=Decimal("5"),
            price_per_share=Decimal("160.00"),
            transaction_date=date.today(),
            commission=Decimal("5.00"),
            account_name="test_account",
        )

        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Position with ID 999 not found"):
            transaction_service.create_sell_transaction(mock_db, 1, sell_request)

    def test_create_sell_transaction_insufficient_shares(
        self, transaction_service, mock_db, mock_position
    ):
        """Test creating sell transaction with insufficient shares."""
        sell_request = SellTransactionRequest(
            position_id=1,
            quantity=Decimal("150"),  # More than available
            price_per_share=Decimal("160.00"),
            transaction_date=date.today(),
            commission=Decimal("5.00"),
            account_name="test_account",
        )

        mock_position.quantity = Decimal("100")  # Only 100 shares available
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_position
        )

        with pytest.raises(ValueError, match="Cannot sell 150 shares"):
            transaction_service.create_sell_transaction(mock_db, 1, sell_request)

    def test_create_dividend_transaction_success(
        self, transaction_service, mock_db, mock_position
    ):
        """Test creating a successful dividend transaction."""
        dividend_request = DividendTransactionRequest(
            position_id=1,
            dividend_amount=Decimal("50.00"),
            transaction_date=date.today(),
            tax_withheld=Decimal("5.00"),
            account_name="test_account",
        )

        mock_position.asset_id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_position
        )

        # Mock transaction creation
        mock_transaction = Mock(spec=Transaction)
        with patch(
            "backend.models.transaction.Transaction.create_dividend_transaction"
        ) as mock_create_dividend:
            mock_create_dividend.return_value = mock_transaction

            with patch.object(transaction_service, "_to_response") as mock_to_response:
                mock_response = Mock(spec=TransactionResponse)
                mock_to_response.return_value = mock_response

                result = transaction_service.create_dividend_transaction(
                    mock_db, 1, dividend_request
                )

                assert result == mock_response
                mock_db.add.assert_called_with(mock_transaction)
                mock_db.commit.assert_called()

    def test_create_dividend_transaction_position_not_found(
        self, transaction_service, mock_db
    ):
        """Test creating dividend transaction when position doesn't exist."""
        dividend_request = DividendTransactionRequest(
            position_id=999,
            dividend_amount=Decimal("50.00"),
            transaction_date=date.today(),
            account_name="test_account",
        )

        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Position with ID 999 not found"):
            transaction_service.create_dividend_transaction(
                mock_db, 1, dividend_request
            )

    def test_get_transaction_performance_no_asset_filter(
        self, transaction_service, mock_db
    ):
        """Test getting transaction performance metrics without asset filter."""
        # Mock transactions
        buy_transaction = Mock()
        buy_transaction.transaction_type = TransactionType.BUY
        buy_transaction.total_amount = Decimal("1500.00")
        buy_transaction.commission = Decimal("5.00")
        buy_transaction.regulatory_fees = Decimal("1.00")
        buy_transaction.other_fees = Decimal("0.50")
        buy_transaction.position_id = None

        sell_transaction = Mock()
        sell_transaction.transaction_type = TransactionType.SELL
        sell_transaction.total_amount = Decimal("1600.00")
        sell_transaction.commission = Decimal("5.00")
        sell_transaction.regulatory_fees = Decimal("1.00")
        sell_transaction.other_fees = Decimal("0.50")
        sell_transaction.position_id = 1
        sell_transaction.quantity = Decimal("10")

        dividend_transaction = Mock()
        dividend_transaction.transaction_type = TransactionType.DIVIDEND
        dividend_transaction.total_amount = Decimal("25.00")
        dividend_transaction.commission = Decimal("0")
        dividend_transaction.regulatory_fees = Decimal("0")
        dividend_transaction.other_fees = Decimal("0")
        dividend_transaction.position_id = None

        mock_db.query.return_value.filter.return_value.all.return_value = [
            buy_transaction,
            sell_transaction,
            dividend_transaction,
        ]

        # Mock position query for sell transaction
        mock_position = Mock()
        mock_position.average_cost_per_share = Decimal("150.00")
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_position
        )

        result = transaction_service.get_transaction_performance(mock_db, 1)

        assert isinstance(result, TransactionPerformanceMetrics)
        assert result.total_transactions == 3
        assert result.total_buys == 1
        assert result.total_sells == 1
        assert result.total_dividends == 1
        assert result.total_invested == Decimal("1506.50")  # 1500 + 6.50 fees
        assert result.total_proceeds == Decimal("1593.50")  # 1600 - 6.50 fees
        assert result.total_dividends_received == Decimal("25.00")

    def test_get_transaction_performance_with_asset_filter(
        self, transaction_service, mock_db
    ):
        """Test getting transaction performance metrics with asset filter."""
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = (
            []
        )

        result = transaction_service.get_transaction_performance(mock_db, 1, asset_id=1)

        assert isinstance(result, TransactionPerformanceMetrics)
        assert result.total_transactions == 0

    def test_get_transactions_by_date_range_no_type_filter(
        self, transaction_service, mock_db, mock_transaction
    ):
        """Test getting transactions by date range without type filter."""
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        mock_db.query.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_transaction
        ]

        with patch.object(transaction_service, "_to_response") as mock_to_response:
            mock_response = Mock(spec=TransactionResponse)
            mock_to_response.return_value = mock_response

            result = transaction_service.get_transactions_by_date_range(
                mock_db, 1, start_date, end_date
            )

            assert len(result) == 1
            assert result[0] == mock_response

    def test_get_transactions_by_date_range_with_type_filter(
        self, transaction_service, mock_db, mock_transaction
    ):
        """Test getting transactions by date range with type filter."""
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        query_mock = Mock()
        mock_db.query.return_value = query_mock
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.all.return_value = [mock_transaction]

        with patch.object(transaction_service, "_to_response") as mock_to_response:
            mock_response = Mock(spec=TransactionResponse)
            mock_to_response.return_value = mock_response

            result = transaction_service.get_transactions_by_date_range(
                mock_db, 1, start_date, end_date, TransactionType.BUY
            )

            assert len(result) == 1
            assert result[0] == mock_response
            # Verify type filter was applied
            assert query_mock.filter.call_count >= 2  # Date range filter + type filter

    def test_get_monthly_transaction_summary(self, transaction_service, mock_db):
        """Test getting monthly transaction summary."""
        # Mock response from get_transactions_by_date_range
        transaction_response = Mock()
        transaction_response.transaction_type = "buy"
        transaction_response.total_amount = Decimal("1500.00")
        transaction_response.commission = Decimal("5.00")
        transaction_response.regulatory_fees = Decimal("1.00")
        transaction_response.other_fees = Decimal("0.50")

        with patch.object(
            transaction_service, "get_transactions_by_date_range"
        ) as mock_get_transactions:
            mock_get_transactions.return_value = [transaction_response]

            result = transaction_service.get_monthly_transaction_summary(
                mock_db, 1, 2025, 6
            )

            assert result["month"] == "2025-06"
            assert result["total_transactions"] == 1
            assert result["buys"]["count"] == 1
            assert result["buys"]["total_amount"] == Decimal("1500.00")
            assert result["fees"]["total"] == Decimal("6.50")

    def test_delete_transaction_not_found(self, transaction_service, mock_db):
        """Test deleting a transaction that doesn't exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = transaction_service.delete_transaction(mock_db, 999)

        assert result is False

    def test_delete_buy_transaction_success(
        self, transaction_service, mock_db, mock_position
    ):
        """Test successfully deleting a buy transaction."""
        transaction = Mock()
        transaction.position_id = 1
        transaction.affects_position = True
        transaction.transaction_type = TransactionType.BUY
        transaction.quantity = Decimal("10")
        transaction.price_per_share = Decimal("150.00")

        mock_position.quantity = Decimal("50")  # Has enough shares
        mock_position.total_cost_basis = Decimal("7500.00")

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            transaction,  # Transaction found
            mock_position,  # Position found
        ]

        result = transaction_service.delete_transaction(mock_db, 1)

        assert result is True
        # Verify position was updated
        assert mock_position.quantity == Decimal("40")  # 50 - 10
        assert mock_position.total_cost_basis == Decimal("6000.00")  # 7500 - 1500
        mock_db.delete.assert_called_with(transaction)
        mock_db.commit.assert_called()

    def test_delete_buy_transaction_insufficient_shares(
        self, transaction_service, mock_db, mock_position
    ):
        """Test deleting a buy transaction with insufficient shares."""
        transaction = Mock()
        transaction.position_id = 1
        transaction.affects_position = True
        transaction.transaction_type = TransactionType.BUY
        transaction.quantity = Decimal("100")
        transaction.price_per_share = Decimal("150.00")

        mock_position.quantity = Decimal("50")  # Not enough shares

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            transaction,  # Transaction found
            mock_position,  # Position found
        ]

        with pytest.raises(
            ValueError,
            match="Cannot delete transaction: would result in negative position",
        ):
            transaction_service.delete_transaction(mock_db, 1)

    def test_delete_sell_transaction_success(
        self, transaction_service, mock_db, mock_position
    ):
        """Test successfully deleting a sell transaction."""
        transaction = Mock()
        transaction.position_id = 1
        transaction.affects_position = True
        transaction.transaction_type = TransactionType.SELL
        transaction.quantity = Decimal("10")

        mock_position.quantity = Decimal("40")
        mock_position.total_cost_basis = Decimal("6000.00")
        mock_position.average_cost_per_share = Decimal("150.00")

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            transaction,  # Transaction found
            mock_position,  # Position found
        ]

        result = transaction_service.delete_transaction(mock_db, 1)

        assert result is True
        # Verify position was updated (reversed the sell)
        assert mock_position.quantity == Decimal("50")  # 40 + 10
        assert mock_position.total_cost_basis == Decimal("7500.00")  # 6000 + 1500
        assert mock_position.is_active is True
        mock_db.delete.assert_called_with(transaction)
        mock_db.commit.assert_called()

    def test_to_response_conversion(self, transaction_service, mock_transaction):
        """Test converting transaction model to response schema."""
        # Add required numeric fields for calculations
        mock_transaction.quantity = Decimal("10")
        mock_transaction.price_per_share = Decimal("150.00")
        mock_transaction.net_amount = Decimal("1500.00")
        mock_transaction.is_sell_transaction = False

        result = transaction_service._to_response(mock_transaction)

        assert isinstance(result, TransactionResponse)
        assert result.id == mock_transaction.id
        assert result.user_id == mock_transaction.user_id
        assert result.transaction_type == mock_transaction.transaction_type
        assert result.quantity == mock_transaction.quantity
        assert result.price_per_share == mock_transaction.price_per_share
        assert result.net_amount == mock_transaction.net_amount

    def test_to_response_with_sell_transaction(
        self, transaction_service, mock_transaction
    ):
        """Test converting sell transaction with realized gain/loss calculation."""
        mock_transaction.is_sell_transaction = True
        mock_transaction.position_id = 1
        mock_transaction.net_amount = Decimal("1600.00")
        mock_transaction.quantity = Decimal("10")
        mock_transaction.price_per_share = Decimal("150.00")

        result = transaction_service._to_response(mock_transaction)

        assert isinstance(result, TransactionResponse)
        assert (
            result.realized_gain_loss is not None
        )  # Should calculate realized gain/loss
