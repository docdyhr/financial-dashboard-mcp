"""Transaction service for managing portfolio transactions."""

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session, joinedload

from backend.models.asset import Asset
from backend.models.position import Position
from backend.models.transaction import Transaction, TransactionType
from backend.schemas.transaction import (
    BuyTransactionRequest,
    DividendTransactionRequest,
    SellTransactionRequest,
    TransactionCreate,
    TransactionFilters,
    TransactionPerformanceMetrics,
    TransactionResponse,
    TransactionUpdate,
)
from backend.services.base import BaseService


class TransactionService(
    BaseService[Transaction, TransactionCreate, TransactionUpdate]
):
    """Service for managing transactions."""

    def __init__(self):
        super().__init__(Transaction)

    def get_user_transactions(
        self,
        db: Session,
        user_id: int,
        filters: TransactionFilters | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[TransactionResponse]:
        """Get transactions for a user with optional filters."""
        query = (
            db.query(Transaction)
            .options(joinedload(Transaction.asset))
            .filter(Transaction.user_id == user_id)
        )

        # Apply filters
        if filters:
            if filters.asset_id:
                query = query.filter(Transaction.asset_id == filters.asset_id)
            if filters.position_id:
                query = query.filter(Transaction.position_id == filters.position_id)
            if filters.transaction_type:
                query = query.filter(
                    Transaction.transaction_type == filters.transaction_type
                )
            if filters.account_name:
                query = query.filter(
                    Transaction.account_name.ilike(f"%{filters.account_name}%")
                )
            if filters.start_date:
                query = query.filter(Transaction.transaction_date >= filters.start_date)
            if filters.end_date:
                query = query.filter(Transaction.transaction_date <= filters.end_date)
            if filters.min_amount:
                query = query.filter(Transaction.total_amount >= filters.min_amount)
            if filters.max_amount:
                query = query.filter(Transaction.total_amount <= filters.max_amount)

        # Order by date descending
        query = query.order_by(desc(Transaction.transaction_date), desc(Transaction.id))

        # Apply pagination
        transactions = query.offset(skip).limit(limit).all()

        # Convert to response format
        return [self._to_response(transaction) for transaction in transactions]

    def get_position_transactions(
        self, db: Session, position_id: int, skip: int = 0, limit: int = 100
    ) -> list[TransactionResponse]:
        """Get all transactions for a specific position."""
        transactions = (
            db.query(Transaction)
            .options(joinedload(Transaction.asset))
            .filter(Transaction.position_id == position_id)
            .order_by(desc(Transaction.transaction_date), desc(Transaction.id))
            .offset(skip)
            .limit(limit)
            .all()
        )

        return [self._to_response(transaction) for transaction in transactions]

    def create_buy_transaction(
        self, db: Session, user_id: int, buy_request: BuyTransactionRequest
    ) -> TransactionResponse:
        """Create a buy transaction and update/create position."""
        # Get the asset
        asset = db.query(Asset).filter(Asset.id == buy_request.asset_id).first()
        if not asset:
            raise ValueError(f"Asset with ID {buy_request.asset_id} not found")

        # Check if position exists for this user and asset
        position = (
            db.query(Position)
            .filter(
                and_(
                    Position.user_id == user_id,
                    Position.asset_id == buy_request.asset_id,
                    Position.is_active,
                )
            )
            .first()
        )

        total_cost = buy_request.quantity * buy_request.price_per_share

        # Create or update position
        if position:
            # Update existing position
            position.update_cost_basis(buy_request.quantity, total_cost)
        else:
            # Create new position
            position = Position(
                user_id=user_id,
                asset_id=buy_request.asset_id,
                quantity=buy_request.quantity,
                average_cost_per_share=buy_request.price_per_share,
                total_cost_basis=total_cost,
                account_name=buy_request.account_name,
            )
            db.add(position)
            db.flush()  # Get the position ID

        # Create transaction
        transaction = Transaction.create_buy(
            user_id=user_id,
            asset_id=buy_request.asset_id,
            quantity=buy_request.quantity,
            price_per_share=buy_request.price_per_share,
            transaction_date=buy_request.transaction_date,
            commission=buy_request.commission,
            account_name=buy_request.account_name,
            notes=buy_request.notes,
            position_id=position.id,
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return self._to_response(transaction)

    def create_sell_transaction(
        self, db: Session, user_id: int, sell_request: SellTransactionRequest
    ) -> TransactionResponse:
        """Create a sell transaction and update position."""
        # Get the position
        position = (
            db.query(Position)
            .filter(
                and_(
                    Position.id == sell_request.position_id,
                    Position.user_id == user_id,
                    Position.is_active,
                )
            )
            .first()
        )

        if not position:
            raise ValueError(f"Position with ID {sell_request.position_id} not found")

        if position.quantity < sell_request.quantity:
            raise ValueError(
                f"Cannot sell {sell_request.quantity} shares. "
                f"Only {position.quantity} shares available."
            )

        # Calculate cost basis of sold shares
        cost_basis_sold = position.reduce_position(sell_request.quantity)

        # Create transaction
        transaction = Transaction.create_sell(
            user_id=user_id,
            asset_id=position.asset_id,
            position_id=position.id,
            quantity=sell_request.quantity,
            price_per_share=sell_request.price_per_share,
            transaction_date=sell_request.transaction_date,
            commission=sell_request.commission,
            account_name=sell_request.account_name,
            notes=sell_request.notes,
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return self._to_response(transaction)

    def create_dividend_transaction(
        self, db: Session, user_id: int, dividend_request: DividendTransactionRequest
    ) -> TransactionResponse:
        """Create a dividend transaction."""
        # Get the position
        position = (
            db.query(Position)
            .filter(
                and_(
                    Position.id == dividend_request.position_id,
                    Position.user_id == user_id,
                )
            )
            .first()
        )

        if not position:
            raise ValueError(
                f"Position with ID {dividend_request.position_id} not found"
            )

        # Create dividend transaction
        transaction = Transaction.create_dividend_transaction(
            user_id=user_id,
            asset_id=position.asset_id,
            position_id=position.id,
            dividend_amount=dividend_request.dividend_amount,
            transaction_date=dividend_request.transaction_date,
            shares_held=position.quantity,
            tax_withheld=dividend_request.tax_withheld,
            account_name=dividend_request.account_name,
            notes=dividend_request.notes,
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return self._to_response(transaction)

    def get_transaction_performance(
        self, db: Session, user_id: int, asset_id: int | None = None
    ) -> TransactionPerformanceMetrics:
        """Calculate performance metrics from transactions."""
        query = db.query(Transaction).filter(Transaction.user_id == user_id)

        if asset_id:
            query = query.filter(Transaction.asset_id == asset_id)

        transactions = query.all()

        # Initialize metrics
        total_transactions = len(transactions)
        total_buys = 0
        total_sells = 0
        total_dividends = 0
        total_invested = Decimal("0")
        total_proceeds = Decimal("0")
        total_dividends_received = Decimal("0")
        total_fees_paid = Decimal("0")
        realized_gains = Decimal("0")

        for transaction in transactions:
            total_fees = (
                transaction.commission
                + transaction.regulatory_fees
                + transaction.other_fees
            )
            total_fees_paid += total_fees

            if transaction.transaction_type == TransactionType.BUY:
                total_buys += 1
                total_invested += transaction.total_amount + total_fees

            elif transaction.transaction_type == TransactionType.SELL:
                total_sells += 1
                total_proceeds += transaction.total_amount - total_fees
                # Calculate realized gain/loss (simplified)
                # This would need more sophisticated tracking for accurate calculation
                if transaction.position_id:
                    position = (
                        db.query(Position)
                        .filter(Position.id == transaction.position_id)
                        .first()
                    )
                    if position:
                        cost_basis = (
                            position.average_cost_per_share * transaction.quantity
                        )
                        gain_loss = (transaction.total_amount - total_fees) - cost_basis
                        realized_gains += gain_loss

            elif transaction.transaction_type == TransactionType.DIVIDEND:
                total_dividends += 1
                total_dividends_received += transaction.total_amount

        net_cash_flow = total_proceeds + total_dividends_received - total_invested

        return TransactionPerformanceMetrics(
            total_transactions=total_transactions,
            total_buys=total_buys,
            total_sells=total_sells,
            total_dividends=total_dividends,
            total_invested=total_invested,
            total_proceeds=total_proceeds,
            total_dividends_received=total_dividends_received,
            total_fees_paid=total_fees_paid,
            net_cash_flow=net_cash_flow,
            realized_gains=realized_gains,
        )

    def get_transactions_by_date_range(
        self,
        db: Session,
        user_id: int,
        start_date: date,
        end_date: date,
        transaction_type: TransactionType | None = None,
    ) -> list[TransactionResponse]:
        """Get transactions within a specific date range."""
        query = (
            db.query(Transaction)
            .options(joinedload(Transaction.asset))
            .filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date <= end_date,
                )
            )
        )

        if transaction_type:
            query = query.filter(Transaction.transaction_type == transaction_type)

        transactions = query.order_by(
            desc(Transaction.transaction_date), desc(Transaction.id)
        ).all()

        return [self._to_response(transaction) for transaction in transactions]

    def get_monthly_transaction_summary(
        self, db: Session, user_id: int, year: int, month: int
    ) -> dict[str, Any]:
        """Get transaction summary for a specific month."""
        from calendar import monthrange

        start_date = date(year, month, 1)
        _, last_day = monthrange(year, month)
        end_date = date(year, month, last_day)

        transactions = self.get_transactions_by_date_range(
            db, user_id, start_date, end_date
        )

        # Summarize by type
        summary = {
            "month": f"{year}-{month:02d}",
            "total_transactions": len(transactions),
            "buys": {"count": 0, "total_amount": Decimal("0")},
            "sells": {"count": 0, "total_amount": Decimal("0")},
            "dividends": {"count": 0, "total_amount": Decimal("0")},
            "fees": {"total": Decimal("0")},
        }

        for transaction in transactions:
            fees = (
                transaction.commission
                + transaction.regulatory_fees
                + transaction.other_fees
            )
            summary["fees"]["total"] += fees

            if transaction.transaction_type == "buy":
                summary["buys"]["count"] += 1
                summary["buys"]["total_amount"] += transaction.total_amount
            elif transaction.transaction_type == "sell":
                summary["sells"]["count"] += 1
                summary["sells"]["total_amount"] += transaction.total_amount
            elif transaction.transaction_type == "dividend":
                summary["dividends"]["count"] += 1
                summary["dividends"]["total_amount"] += transaction.total_amount

        return summary

    def delete_transaction(self, db: Session, transaction_id: int) -> bool:
        """Delete a transaction and update related position."""
        transaction = (
            db.query(Transaction).filter(Transaction.id == transaction_id).first()
        )

        if not transaction:
            return False

        # Handle position updates based on transaction type
        if transaction.position_id and transaction.affects_position:
            position = (
                db.query(Position)
                .filter(Position.id == transaction.position_id)
                .first()
            )

            if position:
                if transaction.transaction_type == TransactionType.BUY:
                    # Reverse the buy: reduce quantity and cost basis
                    if position.quantity >= transaction.quantity:
                        cost_to_remove = (
                            transaction.quantity * transaction.price_per_share
                        )
                        position.quantity -= transaction.quantity
                        position.total_cost_basis -= cost_to_remove

                        if position.quantity > 0:
                            position.average_cost_per_share = (
                                position.total_cost_basis / position.quantity
                            )
                        else:
                            position.is_active = False
                    else:
                        raise ValueError(
                            "Cannot delete transaction: would result in negative position"
                        )

                elif transaction.transaction_type == TransactionType.SELL:
                    # Reverse the sell: add back quantity and cost basis
                    cost_to_add = transaction.quantity * position.average_cost_per_share
                    position.quantity += transaction.quantity
                    position.total_cost_basis += cost_to_add
                    position.is_active = True

        # Delete the transaction
        db.delete(transaction)
        db.commit()
        return True

    def _to_response(self, transaction: Transaction) -> TransactionResponse:
        """Convert transaction model to response schema."""
        from backend.schemas.asset import AssetSummary

        # Calculate net amount
        net_amount = transaction.net_amount

        # Calculate realized gain/loss for sell transactions
        realized_gain_loss = None
        if transaction.is_sell_transaction and transaction.position_id:
            # This is a simplified calculation
            # In a real implementation, you'd need to track cost basis more precisely
            cost_basis_estimate = (
                transaction.quantity * transaction.price_per_share
            )  # Placeholder
            realized_gain_loss = net_amount - cost_basis_estimate

        return TransactionResponse(
            id=transaction.id,
            user_id=transaction.user_id,
            asset_id=transaction.asset_id,
            position_id=transaction.position_id,
            transaction_type=transaction.transaction_type,
            transaction_date=transaction.transaction_date,
            settlement_date=transaction.settlement_date,
            quantity=transaction.quantity,
            price_per_share=transaction.price_per_share,
            total_amount=transaction.total_amount,
            commission=transaction.commission,
            regulatory_fees=transaction.regulatory_fees,
            other_fees=transaction.other_fees,
            tax_withheld=transaction.tax_withheld,
            account_name=transaction.account_name,
            notes=transaction.notes,
            currency=transaction.currency,
            exchange_rate=transaction.exchange_rate,
            order_id=transaction.order_id,
            confirmation_number=transaction.confirmation_number,
            split_ratio=transaction.split_ratio,
            data_source=transaction.data_source,
            external_id=transaction.external_id,
            net_amount=net_amount,
            realized_gain_loss=realized_gain_loss,
            asset=AssetSummary(
                id=transaction.asset.id,
                ticker=transaction.asset.ticker,
                name=transaction.asset.name,
                asset_type=transaction.asset.asset_type,
                category=transaction.asset.category,
            ),
            created_at=transaction.created_at,
            updated_at=transaction.updated_at,
        )
