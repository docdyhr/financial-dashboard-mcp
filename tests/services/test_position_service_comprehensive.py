"""Comprehensive tests for PositionService."""

import datetime
from decimal import Decimal
from unittest.mock import Mock, patch

from fastapi import HTTPException
import pytest
from sqlalchemy.orm import Session

from backend.models.asset import Asset, AssetCategory, AssetType
from backend.models.position import Position
from backend.models.transaction import Transaction, TransactionType
from backend.models.user import User
from backend.schemas.position import (
    PositionAdjustment,
    PositionCreate,
    PositionFilters,
    PositionResponse,
)
from backend.services.position import PositionService


class TestPositionService:
    """Test suite for PositionService."""

    @pytest.fixture
    def position_service(self):
        """Create position service instance."""
        return PositionService()

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.username = "testuser"
        return user

    @pytest.fixture
    def mock_asset(self):
        """Create mock asset."""
        asset = Mock(spec=Asset)
        asset.id = 1
        asset.ticker = "AAPL"
        asset.name = "Apple Inc."
        asset.asset_type = AssetType.STOCK
        asset.category = AssetCategory.EQUITY  # Use actual enum value
        asset.sector = "Technology"
        asset.current_price = Decimal("150.00")
        asset.currency = "USD"
        asset.is_active = True
        return asset

    @pytest.fixture
    def mock_position(self, mock_asset):
        """Create mock position."""
        position = Mock(spec=Position)
        position.id = 1
        position.user_id = 1
        position.asset_id = 1
        position.asset = mock_asset
        position.quantity = Decimal("10.0")
        position.average_cost_per_share = Decimal("140.00")
        position.total_cost_basis = Decimal("1400.00")
        position.account_name = "Test Account"
        position.notes = "Test position"
        position.tax_lot_method = "FIFO"
        position.is_active = True
        position.created_at = datetime.datetime.now()
        position.updated_at = datetime.datetime.now()
        position.current_value = Decimal("1500.00")  # 10 * 150
        position.unrealized_gain_loss = Decimal("100.00")  # 1500 - 1400
        position.unrealized_gain_loss_percent = Decimal("7.14")
        return position

    def test_init(self, position_service):
        """Test PositionService initialization."""
        assert hasattr(position_service, "model")
        assert position_service.model == Position

    def test_get_user_positions_user_not_found(self, position_service, mock_db):
        """Test getting user positions when user doesn't exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            position_service.get_user_positions(mock_db, 999)

        assert exc_info.value.status_code == 404
        assert "User with ID 999 not found" in str(exc_info.value.detail)

    def test_get_user_positions_no_filters(
        self, position_service, mock_db, mock_user, mock_position
    ):
        """Test getting user positions without filters."""
        # Mock user query
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Mock position query
        query_mock = Mock()
        mock_db.query.return_value.options.return_value.filter.return_value = query_mock
        query_mock.offset.return_value.limit.return_value.all.return_value = [
            mock_position
        ]

        result = position_service.get_user_positions(mock_db, 1)

        assert len(result) == 1
        assert isinstance(result[0], PositionResponse)
        assert result[0].id == mock_position.id
        assert result[0].user_id == mock_position.user_id
        assert result[0].quantity == mock_position.quantity

    def test_get_user_positions_with_filters(
        self, position_service, mock_db, mock_user, mock_position
    ):
        """Test getting user positions with filters."""
        filters = PositionFilters(
            asset_type=AssetType.STOCK,
            category=AssetCategory.EQUITY,
            account_name="Test Account",
            min_value=Decimal("1000"),
            max_value=Decimal("2000"),
            is_active=True,
        )

        # Mock user query
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Mock complex query chain with joins and filters
        query_mock = Mock()
        mock_db.query.return_value.options.return_value.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.offset.return_value.limit.return_value.all.return_value = [
            mock_position
        ]

        result = position_service.get_user_positions(mock_db, 1, filters)

        assert len(result) == 1
        assert isinstance(result[0], PositionResponse)
        # Verify joins and filters were called
        assert query_mock.join.call_count >= 4  # Multiple joins for filters
        assert query_mock.filter.call_count >= 4  # Multiple filters applied

    def test_get_user_positions_empty_portfolio(
        self, position_service, mock_db, mock_user
    ):
        """Test getting user positions with empty portfolio."""
        # Mock user query
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Mock empty position query
        query_mock = Mock()
        mock_db.query.return_value.options.return_value.filter.return_value = query_mock
        query_mock.offset.return_value.limit.return_value.all.return_value = []

        result = position_service.get_user_positions(mock_db, 1)

        assert len(result) == 0

    def test_calculate_position_weight(self, position_service, mock_position):
        """Test calculating position weight in portfolio."""
        # Create additional mock positions
        other_position = Mock(spec=Position)
        other_position.current_value = Decimal("1000.00")

        all_positions = [mock_position, other_position]

        weight = position_service._calculate_position_weight(
            mock_position, all_positions
        )

        assert weight == Decimal("60.00")  # 1500 / (1500 + 1000) * 100

    def test_calculate_position_weight_no_current_value(
        self, position_service, mock_position
    ):
        """Test calculating position weight when position has no current value."""
        mock_position.current_value = None

        weight = position_service._calculate_position_weight(mock_position, [])

        assert weight is None

    def test_calculate_position_weight_zero_total_value(
        self, position_service, mock_position
    ):
        """Test calculating position weight when position has zero current value."""
        mock_position.current_value = Decimal("0")
        all_positions = [mock_position]

        weight = position_service._calculate_position_weight(
            mock_position, all_positions
        )

        # When current_value is 0, the method returns None (not 0)
        assert weight is None

    def test_calculate_position_weight_exception_handling(
        self, position_service, mock_position
    ):
        """Test position weight calculation with exception handling."""
        # Simulate an exception during calculation
        mock_position.current_value = "invalid"  # This should cause an error

        with patch("backend.services.position.logger") as mock_logger:
            weight = position_service._calculate_position_weight(
                mock_position, [mock_position]
            )

            assert weight is None
            mock_logger.warning.assert_called_once()

    def test_get_position_by_asset_found(
        self, position_service, mock_db, mock_position
    ):
        """Test getting position by asset when found."""
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_position
        )

        result = position_service.get_position_by_asset(mock_db, 1, 1)

        assert result == mock_position

    def test_get_position_by_asset_not_found(self, position_service, mock_db):
        """Test getting position by asset when not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = position_service.get_position_by_asset(mock_db, 1, 1)

        assert result is None

    def test_create_position_success(self, position_service, mock_db):
        """Test successfully creating a new position."""
        position_create = PositionCreate(
            user_id=1,
            asset_id=1,
            quantity=Decimal("10"),
            average_cost_per_share=Decimal("150.00"),
            total_cost_basis=Decimal("1500.00"),
            account_name="Test Account",
        )

        # Mock no existing position
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Mock the parent create method
        expected_position = Mock(spec=Position)
        with patch.object(position_service, "create") as mock_create:
            mock_create.return_value = expected_position

            result = position_service.create_position(mock_db, position_create)

            assert result == expected_position
            mock_create.assert_called_once_with(mock_db, obj_in=position_create)

    def test_create_position_already_exists(
        self, position_service, mock_db, mock_position
    ):
        """Test creating position when it already exists."""
        position_create = PositionCreate(
            user_id=1,
            asset_id=1,
            quantity=Decimal("10"),
            average_cost_per_share=Decimal("150.00"),
            total_cost_basis=Decimal("1500.00"),
        )

        # Mock existing position
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_position
        )

        with pytest.raises(ValueError, match="Position already exists"):
            position_service.create_position(mock_db, position_create)

    def test_adjust_position_add_shares(self, position_service, mock_db, mock_position):
        """Test adjusting position by adding shares."""
        adjustment = PositionAdjustment(
            quantity=Decimal("5"), price_per_share=Decimal("160.00"), notes="Buy more"
        )

        mock_db.get.return_value = mock_position

        result = position_service.adjust_position(mock_db, 1, adjustment)

        assert result == mock_position
        mock_position.update_cost_basis.assert_called_once_with(
            Decimal("5"), Decimal("800.00")  # 5 * 160
        )
        assert mock_position.notes == "Buy more"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_position)

    def test_adjust_position_reduce_shares(
        self, position_service, mock_db, mock_position
    ):
        """Test adjusting position by reducing shares."""
        adjustment = PositionAdjustment(
            quantity=Decimal("-3"), price_per_share=Decimal("160.00"), notes="Sell some"
        )

        mock_db.get.return_value = mock_position

        result = position_service.adjust_position(mock_db, 1, adjustment)

        assert result == mock_position
        mock_position.reduce_position.assert_called_once_with(Decimal("3"))
        mock_db.commit.assert_called_once()

    def test_adjust_position_not_found(self, position_service, mock_db):
        """Test adjusting position that doesn't exist."""
        adjustment = PositionAdjustment(
            quantity=Decimal("5"), price_per_share=Decimal("160.00")
        )

        mock_db.get.return_value = None

        with pytest.raises(ValueError, match="Position 1 not found"):
            position_service.adjust_position(mock_db, 1, adjustment)

    def test_adjust_position_insufficient_shares(
        self, position_service, mock_db, mock_position
    ):
        """Test adjusting position with insufficient shares to sell."""
        adjustment = PositionAdjustment(
            quantity=Decimal("-15"), price_per_share=Decimal("160.00")  # More than held
        )

        mock_position.quantity = Decimal("10")
        mock_db.get.return_value = mock_position

        with pytest.raises(ValueError, match="Cannot sell more shares"):
            position_service.adjust_position(mock_db, 1, adjustment)

    def test_close_position_success(self, position_service, mock_db, mock_position):
        """Test successfully closing a position."""
        mock_db.get.return_value = mock_position

        result = position_service.close_position(mock_db, 1)

        assert result == mock_position
        assert mock_position.quantity == Decimal("0")
        assert mock_position.is_active is False
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_position)

    def test_close_position_not_found(self, position_service, mock_db):
        """Test closing position that doesn't exist."""
        mock_db.get.return_value = None

        with pytest.raises(ValueError, match="Position 1 not found"):
            position_service.close_position(mock_db, 1)

    def test_get_positions_by_category(self, position_service, mock_db, mock_position):
        """Test getting positions by category."""
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [
            mock_position
        ]

        result = position_service.get_positions_by_category(mock_db, 1, "EQUITY")

        assert len(result) == 1
        assert result[0] == mock_position

    def test_get_positions_by_sector(self, position_service, mock_db, mock_position):
        """Test getting positions by sector."""
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [
            mock_position
        ]

        result = position_service.get_positions_by_sector(mock_db, 1, "Technology")

        assert len(result) == 1
        assert result[0] == mock_position

    def test_calculate_total_portfolio_value_user_not_found(
        self, position_service, mock_db
    ):
        """Test calculating total portfolio value when user doesn't exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            position_service.calculate_total_portfolio_value(mock_db, 999)

        assert exc_info.value.status_code == 404

    def test_calculate_total_portfolio_value_success(
        self, position_service, mock_db, mock_user, mock_position
    ):
        """Test successfully calculating total portfolio value."""
        # Mock user query
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Mock positions query
        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_position
        ]

        result = position_service.calculate_total_portfolio_value(mock_db, 1)

        assert result == Decimal("1500.00")  # mock_position.current_value

    def test_calculate_total_portfolio_value_empty_portfolio(
        self, position_service, mock_db, mock_user
    ):
        """Test calculating total portfolio value with empty portfolio."""
        # Mock user query
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Mock empty positions
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = position_service.calculate_total_portfolio_value(mock_db, 1)

        assert result == Decimal("0")

    def test_get_position_performance_not_found(self, position_service, mock_db):
        """Test getting position performance when position doesn't exist."""
        mock_db.get.return_value = None

        with pytest.raises(ValueError, match="Position 1 not found"):
            position_service.get_position_performance(mock_db, 1)

    def test_get_position_performance_success(
        self, position_service, mock_db, mock_position
    ):
        """Test successfully getting position performance."""
        # Mock transactions
        buy_transaction = Mock(spec=Transaction)
        buy_transaction.transaction_type = TransactionType.BUY
        buy_transaction.total_amount = Decimal("1400.00")
        buy_transaction.transaction_date = datetime.date.today() - datetime.timedelta(
            days=30
        )

        dividend_transaction = Mock(spec=Transaction)
        dividend_transaction.transaction_type = TransactionType.DIVIDEND
        dividend_transaction.total_amount = Decimal("25.00")

        mock_db.get.return_value = mock_position
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            buy_transaction,
            dividend_transaction,
        ]

        result = position_service.get_position_performance(mock_db, 1)

        assert result["total_invested"] == Decimal("1400.00")
        assert result["current_value"] == Decimal("1500.00")
        assert result["dividend_income"] == Decimal("25.00")
        assert result["days_held"] in [29, 30]  # Allow for timezone/date differences
        assert "total_return" in result
        assert "total_return_percent" in result

    def test_get_position_performance_no_transactions(
        self, position_service, mock_db, mock_position
    ):
        """Test getting position performance with no transactions."""
        mock_db.get.return_value = mock_position

        # Mock empty transactions
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            []
        )

        result = position_service.get_position_performance(mock_db, 1)

        assert result["total_invested"] == Decimal("0")
        assert result["dividend_income"] == Decimal("0")
        assert result["days_held"] == Decimal("0")

    def test_get_positions_needing_rebalancing(
        self, position_service, mock_db, mock_user, mock_position
    ):
        """Test getting positions needing rebalancing."""
        target_allocations = {"equity": Decimal("70"), "bond": Decimal("30")}

        # Mock user positions and total portfolio value
        with (
            patch.object(position_service, "get_user_positions") as mock_get_positions,
            patch.object(
                position_service, "calculate_total_portfolio_value"
            ) as mock_total_value,
        ):
            mock_get_positions.return_value = [mock_position]
            mock_total_value.return_value = Decimal("2000.00")

            result = position_service.get_positions_needing_rebalancing(
                mock_db,
                1,
                target_allocations,
                tolerance=Decimal("1"),  # Lower tolerance to trigger rebalancing
            )

            # Current weight: 1500/2000 = 75%, target: 70%, deviation: 5%
            # With tolerance of 1%, this should need rebalancing
            assert len(result) == 1
            assert result[0]["position_id"] == 1
            assert result[0]["current_weight"] == Decimal("75.00")
            assert result[0]["target_weight"] == Decimal(
                "70"
            )  # Looking for "equity" not "EQUITY"
            assert result[0]["deviation"] == Decimal("5.00")
            assert result[0]["action_needed"] == "reduce"

    def test_get_positions_needing_rebalancing_empty_portfolio(
        self, position_service, mock_db
    ):
        """Test getting positions needing rebalancing with empty portfolio."""
        target_allocations = {"equity": Decimal("70")}

        # Mock both methods needed
        with (
            patch.object(position_service, "get_user_positions") as mock_get_positions,
            patch.object(
                position_service, "calculate_total_portfolio_value"
            ) as mock_total_value,
        ):
            mock_get_positions.return_value = []
            mock_total_value.return_value = Decimal("0")

            result = position_service.get_positions_needing_rebalancing(
                mock_db, 1, target_allocations
            )

            assert len(result) == 0

    def test_consolidate_positions_success(self, position_service, mock_db):
        """Test successfully consolidating positions."""
        # Create multiple positions for the same asset
        position1 = Mock(spec=Position)
        position1.asset_id = 1
        position1.user_id = 1
        position1.quantity = Decimal("10")
        position1.total_cost_basis = Decimal("1000")

        position2 = Mock(spec=Position)
        position2.asset_id = 1
        position2.user_id = 1
        position2.quantity = Decimal("5")
        position2.total_cost_basis = Decimal("600")

        mock_db.query.return_value.filter.return_value.all.return_value = [
            position1,
            position2,
        ]

        result = position_service.consolidate_positions(mock_db, [1, 2])

        assert result == position1
        assert position1.quantity == Decimal("15")  # 10 + 5
        assert position1.total_cost_basis == Decimal("1600")  # 1000 + 600
        # Check average cost per share with tolerance for decimal precision
        expected_avg_cost = Decimal("1600") / Decimal("15")
        assert abs(position1.average_cost_per_share - expected_avg_cost) < Decimal(
            "0.01"
        )
        assert position2.is_active is False
        mock_db.commit.assert_called_once()

    def test_consolidate_positions_no_positions(self, position_service, mock_db):
        """Test consolidating positions when none found."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with pytest.raises(ValueError, match="No positions found to consolidate"):
            position_service.consolidate_positions(mock_db, [1, 2])

    def test_consolidate_positions_different_assets(self, position_service, mock_db):
        """Test consolidating positions with different assets."""
        position1 = Mock(spec=Position)
        position1.asset_id = 1
        position1.user_id = 1

        position2 = Mock(spec=Position)
        position2.asset_id = 2  # Different asset
        position2.user_id = 1

        mock_db.query.return_value.filter.return_value.all.return_value = [
            position1,
            position2,
        ]

        with pytest.raises(
            ValueError, match="All positions must be for the same asset and user"
        ):
            position_service.consolidate_positions(mock_db, [1, 2])

    def test_split_position_success(self, position_service, mock_db, mock_position):
        """Test successfully handling stock split."""
        mock_position.quantity = Decimal("10")
        mock_position.average_cost_per_share = Decimal("100.00")
        mock_position.notes = "Original position"

        mock_db.get.return_value = mock_position

        result = position_service.split_position(
            mock_db, 1, Decimal("2"), notes="2:1 stock split"
        )

        assert result == mock_position
        assert mock_position.quantity == Decimal("20")  # 10 * 2
        assert mock_position.average_cost_per_share == Decimal("50.00")  # 100 / 2
        assert "Stock split 2:1" in mock_position.notes
        mock_db.commit.assert_called_once()

    def test_split_position_not_found(self, position_service, mock_db):
        """Test stock split when position doesn't exist."""
        mock_db.get.return_value = None

        with pytest.raises(ValueError, match="Position 1 not found"):
            position_service.split_position(mock_db, 1, Decimal("2"))

    def test_split_position_no_notes(self, position_service, mock_db, mock_position):
        """Test stock split without additional notes."""
        mock_position.notes = None
        mock_db.get.return_value = mock_position

        # The split_position method only updates notes if the `notes` parameter is provided
        # When notes=None, it doesn't change the existing notes
        result = position_service.split_position(mock_db, 1, Decimal("2"))

        # Verify the split calculations were done
        assert mock_position.quantity == Decimal("20")  # 10 * 2
        assert mock_position.average_cost_per_share == Decimal("70.00")  # 140 / 2
        assert result == mock_position
