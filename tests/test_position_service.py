"""Tests for position service."""

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from backend.models import Asset, AssetType, Position, Transaction, TransactionType, User
from backend.schemas.position import PositionCreate
from backend.services.position import PositionService


@pytest.fixture
def position_service():
    """Create position service instance."""
    return PositionService()


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user."""
    user = User(email="test@example.com", name="Test User")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_asset(db_session: Session):
    """Create a test asset."""
    asset = Asset(
        ticker="AAPL",
        name="Apple Inc.",
        asset_type=AssetType.STOCK,
        sector="Technology",
    )
    db_session.add(asset)
    db_session.commit()
    return asset


class TestPositionService:
    """Test position service methods."""

    def test_create_position(
        self,
        position_service: PositionService,
        db_session: Session,
        test_user: User,
        test_asset: Asset,
    ):
        """Test creating a new position."""
        position_data = PositionCreate(
            asset_id=test_asset.id,
            quantity=Decimal("10"),
            average_cost_basis=Decimal("150"),
        )

        position = position_service.create_position(
            db_session, test_user.id, position_data
        )

        assert position.user_id == test_user.id
        assert position.asset_id == test_asset.id
        assert position.quantity == Decimal("10")
        assert position.average_cost_basis == Decimal("150")
        assert position.total_cost_basis == Decimal("1500")
        assert position.is_active is True

    def test_get_position(
        self,
        position_service: PositionService,
        db_session: Session,
        test_user: User,
        test_asset: Asset,
    ):
        """Test getting a position."""
        # Create position
        position = Position(
            user_id=test_user.id,
            asset_id=test_asset.id,
            quantity=Decimal("10"),
            average_cost_basis=Decimal("150"),
            total_cost_basis=Decimal("1500"),
            is_active=True,
        )
        db_session.add(position)
        db_session.commit()

        # Get position
        retrieved = position_service.get_position(
            db_session, test_user.id, position.id
        )

        assert retrieved.id == position.id
        assert retrieved.quantity == position.quantity

    def test_get_nonexistent_position(
        self,
        position_service: PositionService,
        db_session: Session,
        test_user: User,
    ):
        """Test getting a nonexistent position."""
        with pytest.raises(Exception) as exc_info:
            position_service.get_position(db_session, test_user.id, 999)
        assert "not found" in str(exc_info.value).lower()

    def test_update_position_from_transaction_buy(
        self,
        position_service: PositionService,
        db_session: Session,
        test_user: User,
        test_asset: Asset,
    ):
        """Test updating position from buy transaction."""
        # Create initial position
        position = Position(
            user_id=test_user.id,
            asset_id=test_asset.id,
            quantity=Decimal("10"),
            average_cost_basis=Decimal("100"),
            total_cost_basis=Decimal("1000"),
            is_active=True,
        )
        db_session.add(position)
        db_session.commit()

        # Create buy transaction
        transaction = Transaction(
            user_id=test_user.id,
            asset_id=test_asset.id,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("5"),
            price=Decimal("120"),
            total_amount=Decimal("600"),
        )

        # Update position
        updated = position_service.update_position_from_transaction(
            db_session, position, transaction
        )

        assert updated.quantity == Decimal("15")  # 10 + 5
        assert updated.total_cost_basis == Decimal("1600")  # 1000 + 600
        assert updated.average_cost_basis == Decimal("106.67")  # 1600 / 15

    def test_update_position_from_transaction_sell(
        self,
        position_service: PositionService,
        db_session: Session,
        test_user: User,
        test_asset: Asset,
    ):
        """Test updating position from sell transaction."""
        # Create initial position
        position = Position(
            user_id=test_user.id,
            asset_id=test_asset.id,
            quantity=Decimal("10"),
            average_cost_basis=Decimal("100"),
            total_cost_basis=Decimal("1000"),
            is_active=True,
        )
        db_session.add(position)
        db_session.commit()

        # Create sell transaction
        transaction = Transaction(
            user_id=test_user.id,
            asset_id=test_asset.id,
            transaction_type=TransactionType.SELL,
            quantity=Decimal("5"),
            price=Decimal("120"),
            total_amount=Decimal("600"),
        )

        # Update position
        updated = position_service.update_position_from_transaction(
            db_session, position, transaction
        )

        assert updated.quantity == Decimal("5")  # 10 - 5
        assert updated.total_cost_basis == Decimal("500")  # Proportional reduction
        assert updated.average_cost_basis == Decimal("100")  # Unchanged

    def test_update_position_from_transaction_sell_all(
        self,
        position_service: PositionService,
        db_session: Session,
        test_user: User,
        test_asset: Asset,
    ):
        """Test updating position from sell all transaction."""
        # Create initial position
        position = Position(
            user_id=test_user.id,
            asset_id=test_asset.id,
            quantity=Decimal("10"),
            average_cost_basis=Decimal("100"),
            total_cost_basis=Decimal("1000"),
            is_active=True,
        )
        db_session.add(position)
        db_session.commit()

        # Create sell all transaction
        transaction = Transaction(
            user_id=test_user.id,
            asset_id=test_asset.id,
            transaction_type=TransactionType.SELL,
            quantity=Decimal("10"),
            price=Decimal("120"),
            total_amount=Decimal("1200"),
        )

        # Update position
        updated = position_service.update_position_from_transaction(
            db_session, position, transaction
        )

        assert updated.quantity == Decimal("0")
        assert updated.total_cost_basis == Decimal("0")
        assert updated.is_active is False

    def test_calculate_position_performance(
        self,
        position_service: PositionService,
        db_session: Session,
        test_user: User,
        test_asset: Asset,
    ):
        """Test calculating position performance."""
        # Create position with current price
        position = Position(
            user_id=test_user.id,
            asset_id=test_asset.id,
            quantity=Decimal("10"),
            average_cost_basis=Decimal("100"),
            total_cost_basis=Decimal("1000"),
            current_price=Decimal("120"),
            current_value=Decimal("1200"),
            is_active=True,
        )
        db_session.add(position)
        db_session.commit()

        # Calculate performance
        performance = position_service.calculate_position_performance(position)

        assert performance["gain_loss"] == Decimal("200")  # 1200 - 1000
        assert performance["gain_loss_percent"] == Decimal("20")  # 200 / 1000 * 100
        assert performance["current_value"] == Decimal("1200")
        assert performance["cost_basis"] == Decimal("1000")

    def test_list_user_positions(
        self,
        position_service: PositionService,
        db_session: Session,
        test_user: User,
        test_asset: Asset,
    ):
        """Test listing user positions."""
        # Create multiple positions
        positions = [
            Position(
                user_id=test_user.id,
                asset_id=test_asset.id,
                quantity=Decimal("10"),
                average_cost_basis=Decimal("100"),
                total_cost_basis=Decimal("1000"),
                is_active=True,
            ),
            Position(
                user_id=test_user.id,
                asset_id=test_asset.id,
                quantity=Decimal("5"),
                average_cost_basis=Decimal("150"),
                total_cost_basis=Decimal("750"),
                is_active=False,  # Inactive position
            ),
        ]
        db_session.add_all(positions)
        db_session.commit()

        # List active positions
        active_positions = position_service.list_user_positions(
            db_session, test_user.id, active_only=True
        )
        assert len(active_positions) == 1
        assert active_positions[0].is_active is True

        # List all positions
        all_positions = position_service.list_user_positions(
            db_session, test_user.id, active_only=False
        )
        assert len(all_positions) == 2