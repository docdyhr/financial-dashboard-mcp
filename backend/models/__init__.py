"""Models module."""

from backend.models.asset import Asset, AssetCategory, AssetType
from backend.models.base import Base, drop_db, get_db, init_db
from backend.models.portfolio_snapshot import PortfolioSnapshot
from backend.models.position import Position
from backend.models.price_history import PriceHistory
from backend.models.transaction import Transaction, TransactionType
from backend.models.user import User

# All models are now exported with their relationships defined inline
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
    "drop_db",
    "get_db",
    "init_db",
]
