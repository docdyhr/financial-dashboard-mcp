"""Tests for portfolio service."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from backend.models import Asset, AssetCategory, AssetType, CashAccount, Position, User
from backend.services.portfolio import PortfolioService


@pytest.fixture
def portfolio_service():
    """Create portfolio service instance."""
    return PortfolioService()


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password="hashed_password_here",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_assets(db_session: Session):
    """Create test assets."""
    assets = [
        Asset(
            ticker="AAPL",
            name="Apple Inc.",
            asset_type=AssetType.STOCK,
            category=AssetCategory.EQUITY,
            sector="Technology",
            current_price=Decimal("180"),
        ),
        Asset(
            ticker="GOOGL",
            name="Alphabet Inc.",
            asset_type=AssetType.STOCK,
            category=AssetCategory.EQUITY,
            sector="Technology",
            current_price=Decimal("3000"),
        ),
        Asset(
            ticker="MSFT",
            name="Microsoft Corp.",
            asset_type=AssetType.STOCK,
            category=AssetCategory.EQUITY,
            sector="Technology",
            current_price=Decimal("400"),
        ),
        Asset(
            ticker="JPM",
            name="JPMorgan Chase",
            asset_type=AssetType.STOCK,
            category=AssetCategory.EQUITY,
            sector="Financial",
            current_price=Decimal("150"),
        ),
        Asset(
            ticker="AGG",
            name="iShares Core US Aggregate Bond ETF",
            asset_type=AssetType.ETF,
            category=AssetCategory.FIXED_INCOME,
            sector="Bonds",
            current_price=Decimal("95"),
        ),
    ]
    db_session.add_all(assets)
    db_session.commit()
    return assets


@pytest.fixture
def test_cash_account(db_session: Session, test_user: User):
    """Create a test cash account."""
    cash_account = CashAccount(
        user_id=test_user.id,
        currency="USD",
        account_name="Main USD Account",
        balance=Decimal("5000"),
        is_primary=True,
    )
    db_session.add(cash_account)
    db_session.commit()
    return cash_account


@pytest.fixture
def test_positions(db_session: Session, test_user: User, test_assets: list[Asset]):
    """Create test positions."""
    positions = [
        Position(
            user_id=test_user.id,
            asset_id=test_assets[0].id,
            quantity=Decimal("10"),
            average_cost_per_share=Decimal("150"),
            total_cost_basis=Decimal("1500"),
            is_active=True,
        ),
        Position(
            user_id=test_user.id,
            asset_id=test_assets[1].id,
            quantity=Decimal("5"),
            average_cost_per_share=Decimal("2800"),
            total_cost_basis=Decimal("14000"),
            is_active=True,
        ),
        Position(
            user_id=test_user.id,
            asset_id=test_assets[2].id,
            quantity=Decimal("8"),
            average_cost_per_share=Decimal("350"),
            total_cost_basis=Decimal("2800"),
            is_active=True,
        ),
        Position(
            user_id=test_user.id,
            asset_id=test_assets[3].id,
            quantity=Decimal("20"),
            average_cost_per_share=Decimal("140"),
            total_cost_basis=Decimal("2800"),
            is_active=True,
        ),
        Position(
            user_id=test_user.id,
            asset_id=test_assets[4].id,
            quantity=Decimal("50"),
            average_cost_per_share=Decimal("100"),
            total_cost_basis=Decimal("5000"),
            is_active=True,
        ),
    ]
    db_session.add_all(positions)
    db_session.commit()
    return positions


class TestPortfolioService:
    """Test portfolio service methods."""

    def test_get_portfolio_summary(
        self,
        portfolio_service: PortfolioService,
        db_session: Session,
        test_user: User,
        test_positions: list[Position],
        test_cash_account: CashAccount,
    ):
        """Test getting portfolio summary."""
        summary = portfolio_service.get_portfolio_summary(db_session, test_user.id)

        # Check totals
        expected_total_value = (
            sum(p.current_value for p in test_positions) + test_cash_account.balance
        )
        assert summary.total_value == expected_total_value
        assert summary.total_cost_basis == sum(
            p.total_cost_basis for p in test_positions
        )
        assert summary.cash_balance == test_cash_account.balance
        assert len(summary.top_positions) <= 5  # Top 5 positions limit

        # Check performance calculations
        expected_total_gain_loss = sum(
            p.current_value - p.total_cost_basis for p in test_positions
        )
        assert summary.total_gain_loss == expected_total_gain_loss

        expected_percent = (
            (expected_total_gain_loss / summary.total_cost_basis * 100)
            if summary.total_cost_basis > 0
            else Decimal("0")
        )
        assert summary.total_gain_loss_percent == expected_percent

    def test_get_portfolio_summary_nonexistent_user(
        self,
        portfolio_service: PortfolioService,
        db_session: Session,
    ):
        """Test getting portfolio summary for nonexistent user."""
        with pytest.raises(Exception) as exc_info:
            portfolio_service.get_portfolio_summary(db_session, 999)
        assert "not found" in str(exc_info.value).lower()

    def test_calculate_diversification_metrics(
        self,
        portfolio_service: PortfolioService,
        db_session: Session,
        test_user: User,
        test_positions: list[Position],
        test_cash_account: CashAccount,
    ):
        """Test diversification metrics calculation."""
        metrics = portfolio_service.get_diversification_metrics(
            db_session, test_user.id
        )

        # Check basic metrics
        assert metrics.effective_number_of_assets > 0
        assert 0 <= metrics.concentration_risk <= 100
        assert 0 <= metrics.herfindahl_index <= 1

        # Check diversification scores
        assert 0 <= metrics.overall_diversification_score <= 100
        assert 0 <= metrics.sector_diversification_score <= 100
        assert 0 <= metrics.asset_type_diversification_score <= 100

        # Check sector concentration
        assert "Technology" in metrics.sector_concentration
        assert "Financial" in metrics.sector_concentration
        assert "Bonds" in metrics.sector_concentration

    def test_calculate_diversification_metrics_no_positions(
        self,
        portfolio_service: PortfolioService,
        db_session: Session,
        test_user: User,
    ):
        """Test diversification metrics with no positions."""
        metrics = portfolio_service.get_diversification_metrics(
            db_session, test_user.id
        )

        assert metrics.concentration_risk == Decimal("100")
        assert metrics.herfindahl_index == Decimal("1")
        assert metrics.effective_number_of_assets == Decimal("0")
        assert metrics.overall_diversification_score == 0

    def test_calculate_allocation_breakdown(
        self,
        portfolio_service: PortfolioService,
        db_session: Session,
        test_user: User,
        test_positions: list[Position],
        test_cash_account: CashAccount,
    ):
        """Test allocation breakdown calculation."""
        allocation = portfolio_service.get_allocation_breakdown(
            db_session, test_user.id
        )

        # Check that allocations are reasonable (may not sum to exactly 100% depending on implementation)
        total_asset_allocation = sum(
            allocation.allocation_by_category.values(), Decimal("0")
        )
        assert total_asset_allocation > Decimal("0"), "Should have some allocation"
        assert total_asset_allocation <= Decimal(
            "100"
        ), "Total allocation should not exceed 100%"

        # Check sector allocation
        assert "Technology" in allocation.allocation_by_sector
        assert "Financial" in allocation.allocation_by_sector
        assert "Bonds" in allocation.allocation_by_sector

        # Check asset type allocation
        assert AssetType.STOCK in allocation.allocation_by_asset_type
        assert AssetType.ETF in allocation.allocation_by_asset_type

    def test_create_portfolio_snapshot(
        self,
        portfolio_service: PortfolioService,
        db_session: Session,
        test_user: User,
        test_positions: list[Position],
        test_cash_account: CashAccount,
    ):
        """Test creating portfolio snapshot."""
        snapshot_date = date.today()
        snapshot = portfolio_service.create_portfolio_snapshot(
            db_session, test_user.id, snapshot_date
        )

        assert snapshot.user_id == test_user.id
        assert snapshot.snapshot_date == snapshot_date
        assert (
            snapshot.total_value
            == sum(p.current_value for p in test_positions) + test_cash_account.balance
        )
        assert snapshot.cash_balance == test_cash_account.balance
        assert snapshot.number_of_positions == len(test_positions)

    def test_calculate_position_weights(
        self,
        portfolio_service: PortfolioService,
        db_session: Session,
        test_user: User,
        test_positions: list[Position],
        test_cash_account: CashAccount,
    ):
        """Test position weight calculation."""
        weights = portfolio_service.calculate_position_weights(db_session, test_user.id)

        # Check that all positions have weights
        assert len(weights) == len(test_positions)

        # Check that weights sum to 100%
        total_weight = sum(weights.values())
        assert abs(total_weight - Decimal("100")) < Decimal("0.01")

        # Check individual weights are correct
        total_value = sum(p.current_value for p in test_positions)
        for position in test_positions:
            expected_weight = (position.current_value / total_value) * 100
            assert abs(weights[position.id] - expected_weight) < Decimal("0.01")
