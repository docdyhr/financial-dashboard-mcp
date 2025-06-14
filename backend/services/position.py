"""Position service for position management operations."""

import datetime
from decimal import Decimal
from typing import Any, cast

from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from backend.models import Asset, Position, Transaction, User
from backend.models.transaction import TransactionType
from backend.schemas.asset import AssetSummary
from backend.schemas.position import (
    PositionAdjustment,
    PositionCreate,
    PositionFilters,
    PositionResponse,
)
from backend.services.base import BaseService


class PositionService(BaseService[Position, PositionCreate, PositionAdjustment]):
    """Service for position management operations."""

    def __init__(self) -> None:
        """Initialize position service."""
        super().__init__(Position)

    def get_user_positions(
        self,
        db: Session,
        user_id: int,
        filters: PositionFilters | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[PositionResponse]:
        """Get positions for a user with optional filters."""

        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=404, detail=f"User with ID {user_id} not found"
            )

        query = (
            db.query(Position)
            .options(joinedload(Position.asset))
            .filter(Position.user_id == user_id)
        )

        # Apply filters
        if filters:
            if filters.asset_type:
                query = query.join(Asset).filter(Asset.asset_type == filters.asset_type)
            if filters.category:
                query = query.join(Asset).filter(Asset.category == filters.category)
            if filters.account_name:
                query = query.filter(Position.account_name == filters.account_name)
            if filters.min_value:
                # This would need to be calculated with current prices
                pass
            if filters.max_value:
                # This would need to be calculated with current prices
                pass

            query = query.filter(Position.is_active == filters.is_active)

        positions = query.offset(skip).limit(limit).all()

        # Convert to response objects
        position_responses = []
        for position in positions:
            asset_summary = AssetSummary(
                id=position.asset.id,
                ticker=position.asset.ticker,
                name=position.asset.name,
                asset_type=position.asset.asset_type,
                category=position.asset.category,
                current_price=(
                    Decimal(str(position.asset.current_price))
                    if position.asset.current_price is not None
                    else None
                ),
                currency=position.asset.currency,
                is_active=position.asset.is_active,
            )

            position_response = PositionResponse(
                id=position.id,
                user_id=position.user_id,
                asset_id=position.asset_id,
                asset=asset_summary,
                quantity=position.quantity,
                average_cost_per_share=position.average_cost_per_share,
                total_cost_basis=position.total_cost_basis,
                account_name=position.account_name,
                notes=position.notes,
                tax_lot_method=position.tax_lot_method,
                is_active=position.is_active,
                created_at=position.created_at,
                updated_at=position.updated_at,
                current_value=position.current_value,
                unrealized_gain_loss=position.unrealized_gain_loss,
                unrealized_gain_loss_percent=position.unrealized_gain_loss_percent,
                weight_in_portfolio=None,  # TODO: Calculate if needed
            )
            position_responses.append(position_response)

        return position_responses

    def get_position_by_asset(
        self, db: Session, user_id: int, asset_id: int
    ) -> Position | None:
        """Get a user's position in a specific asset."""
        return (
            db.query(Position)
            .filter(
                and_(
                    Position.user_id == user_id,
                    Position.asset_id == asset_id,
                    Position.is_active.is_(True),
                )
            )
            .first()
        )

    def create_position(self, db: Session, position_create: PositionCreate) -> Position:
        """Create a new position."""
        # Check if position already exists for this user/asset
        existing_position = self.get_position_by_asset(
            db, position_create.user_id, position_create.asset_id
        )

        if existing_position:
            raise ValueError(
                f"Position already exists for user {position_create.user_id} "
                f"and asset {position_create.asset_id}"
            )

        return self.create(db, obj_in=position_create)

    def adjust_position(
        self, db: Session, position_id: int, adjustment: PositionAdjustment
    ) -> Position:
        """Adjust a position by adding or reducing shares."""
        position = db.query(Position).get(position_id)
        if not position:
            raise ValueError(f"Position {position_id} not found")
        position = cast("Position", position)

        if adjustment.quantity > 0:
            # Adding to position
            position.update_cost_basis(
                adjustment.quantity, adjustment.quantity * adjustment.price_per_share
            )
        elif adjustment.quantity < 0:
            # Reducing position
            quantity_to_sell = abs(adjustment.quantity)
            if quantity_to_sell > position.quantity:
                raise ValueError("Cannot sell more shares than currently held")

            position.reduce_position(quantity_to_sell)

        # Update notes if provided
        if adjustment.notes:
            position.notes = adjustment.notes

        db.commit()
        db.refresh(position)
        return position

    def close_position(self, db: Session, position_id: int) -> Position:
        """Close a position by setting quantity to 0 and marking inactive."""
        position = db.query(Position).get(position_id)
        if not position:
            raise ValueError(f"Position {position_id} not found")
        position = cast("Position", position)

        position.quantity = Decimal("0")
        position.is_active = False

        db.commit()
        db.refresh(position)
        return position

    def get_positions_by_category(
        self, db: Session, user_id: int, category: str
    ) -> list[Position]:
        """Get all positions in a specific asset category."""
        return (
            db.query(Position)
            .join(Asset)
            .filter(
                and_(
                    Position.user_id == user_id,
                    Asset.category == category,
                    Position.is_active.is_(True),
                )
            )
            .all()
        )

    def get_positions_by_sector(
        self, db: Session, user_id: int, sector: str
    ) -> list[Position]:
        """Get all positions in a specific sector."""
        return (
            db.query(Position)
            .join(Asset)
            .filter(
                and_(
                    Position.user_id == user_id,
                    Asset.sector == sector,
                    Position.is_active.is_(True),
                )
            )
            .all()
        )

    def calculate_total_portfolio_value(self, db: Session, user_id: int) -> Decimal:
        """Calculate total value of all positions for a user."""
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=404, detail=f"User with ID {user_id} not found"
            )

        positions = (
            db.query(Position)
            .filter(and_(Position.user_id == user_id, Position.is_active.is_(True)))
            .all()
        )

        total_value = Decimal("0")
        for position in positions:
            if position.current_value:
                total_value += position.current_value

        return total_value

    def get_position_performance(
        self, db: Session, position_id: int
    ) -> dict[str, Decimal]:
        """Get performance metrics for a specific position."""
        position = db.query(Position).get(position_id)
        if not position:
            raise ValueError(f"Position {position_id} not found")
        position = cast("Position", position)

        # Get all transactions for this position
        transactions = (
            db.query(Transaction)
            .filter(Transaction.position_id == position_id)
            .order_by(Transaction.transaction_date)
            .all()
        )

        # Calculate metrics
        total_invested = sum(
            t.total_amount
            for t in transactions
            if t.transaction_type in [TransactionType.BUY, TransactionType.TRANSFER_IN]
        )

        total_proceeds = sum(
            t.total_amount
            for t in transactions
            if t.transaction_type
            in [TransactionType.SELL, TransactionType.TRANSFER_OUT]
        )

        dividend_income = sum(
            t.total_amount
            for t in transactions
            if t.transaction_type == TransactionType.DIVIDEND
        )

        current_value = position.current_value or Decimal("0")
        unrealized_gain_loss = position.unrealized_gain_loss or Decimal("0")

        # Calculate total return including dividends and realized gains
        total_return = (
            unrealized_gain_loss + dividend_income + (total_proceeds - total_invested)
        )
        total_return_percent = (
            (total_return / total_invested * 100)
            if total_invested > 0
            else Decimal("0")
        )

        # Calculate days held (from first purchase)
        first_transaction = transactions[0] if transactions else None
        days_held = 0
        if first_transaction:
            days_held = (
                datetime.datetime.now(tz=datetime.UTC).date()
                - first_transaction.transaction_date
            ).days

        return {
            "total_invested": Decimal(str(total_invested)),
            "current_value": Decimal(str(current_value)),
            "total_return": Decimal(str(total_return)),
            "total_return_percent": Decimal(str(total_return_percent)),
            "unrealized_gain_loss": Decimal(str(unrealized_gain_loss)),
            "dividend_income": Decimal(str(dividend_income)),
            "days_held": Decimal(days_held),
        }

    def get_positions_needing_rebalancing(
        self,
        db: Session,
        user_id: int,
        target_allocations: dict[str, Decimal],
        tolerance: Decimal = Decimal("5"),
    ) -> list[dict[str, Any]]:
        """Get positions that need rebalancing based on target allocations."""
        positions = self.get_user_positions(db, user_id)
        total_value = self.calculate_total_portfolio_value(db, user_id)

        if total_value == 0:
            return []

        rebalancing_needed = []

        for position in positions:
            current_weight = (
                (position.current_value or Decimal("0")) / total_value * 100
            )
            category = position.asset.category.value
            target_weight = target_allocations.get(category, Decimal("0"))

            deviation = abs(current_weight - target_weight)

            if deviation > tolerance:
                rebalancing_needed.append(
                    {
                        "position_id": position.id,
                        "ticker": position.asset.ticker,
                        "category": category,
                        "current_weight": current_weight,
                        "target_weight": target_weight,
                        "deviation": deviation,
                        "action_needed": (
                            "reduce" if current_weight > target_weight else "increase"
                        ),
                    }
                )

        return rebalancing_needed

    def consolidate_positions(self, db: Session, position_ids: list[int]) -> Position:
        """Consolidate multiple positions of the same asset into one."""
        positions = db.query(Position).filter(Position.id.in_(position_ids)).all()

        if not positions:
            raise ValueError("No positions found to consolidate")

        # Verify all positions are for the same asset
        asset_id = positions[0].asset_id
        user_id = positions[0].user_id

        if not all(p.asset_id == asset_id and p.user_id == user_id for p in positions):
            raise ValueError("All positions must be for the same asset and user")

        # Calculate consolidated values
        total_quantity = sum(p.quantity for p in positions)
        total_cost_basis = sum(p.total_cost_basis for p in positions)
        average_cost = (
            total_cost_basis / total_quantity if total_quantity > 0 else Decimal("0")
        )

        # Keep the first position and update it
        main_position = positions[0]
        main_position.quantity = Decimal(str(total_quantity))
        main_position.total_cost_basis = Decimal(str(total_cost_basis))
        main_position.average_cost_per_share = Decimal(str(average_cost))

        # Mark other positions as inactive
        for position in positions[1:]:
            position.is_active = False

        db.commit()
        db.refresh(main_position)

        return main_position

    def split_position(
        self,
        db: Session,
        position_id: int,
        split_ratio: Decimal,
        notes: str | None = None,
    ) -> Position:
        """Handle stock split for a position."""
        position = db.query(Position).get(position_id)
        if not position:
            raise ValueError(f"Position {position_id} not found")
        position = cast("Position", position)

        # Update quantity and average cost for split
        position.quantity *= split_ratio
        position.average_cost_per_share /= split_ratio
        # Total cost basis remains the same

        if notes:
            position.notes = (
                f"{position.notes or ''}\nStock split {split_ratio}:1 - {notes}".strip()
            )

        db.commit()
        db.refresh(position)
        return position
