"""Database models for Financial Dashboard."""

# Import sqlalchemy for relationship setup
from sqlalchemy.orm import relationship

from backend.models.asset import Asset, AssetCategory, AssetType
from backend.models.base import Base, create_tables, drop_tables, get_db
from backend.models.portfolio_snapshot import PortfolioSnapshot
from backend.models.position import Position
from backend.models.price_history import PriceHistory
from backend.models.transaction import Transaction, TransactionType
from backend.models.user import User

# Set up relationships after all models are imported
User.positions = relationship(
    "Position", back_populates="user", cascade="all, delete-orphan"
)
User.transactions = relationship(
    "Transaction", back_populates="user", cascade="all, delete-orphan"
)
User.portfolio_snapshots = relationship(
    "PortfolioSnapshot", back_populates="user", cascade="all, delete-orphan"
)

Asset.positions = relationship("Position", back_populates="asset")
Asset.transactions = relationship("Transaction", back_populates="asset")
Asset.price_history = relationship(
    "PriceHistory", back_populates="asset", cascade="all, delete-orphan"
)

__all__ = [
    "Asset",
    "AssetCategory",
    "AssetType",
    "Base",
    "PortfolioSnapshot",
    "Position",
    "PriceHistory",
    "Transaction",
    "TransactionType",
    "User",
    "create_tables",
    "drop_tables",
    "get_db",
]
