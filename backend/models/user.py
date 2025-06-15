"""User model for authentication and user management."""

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.portfolio_snapshot import PortfolioSnapshot
    from backend.models.position import Position
    from backend.models.transaction import Transaction


class User(Base):
    """User model for authentication and profile management."""

    __tablename__ = "users"

    # Basic user information
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    username: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Authentication
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Profile settings
    preferred_currency: Mapped[str] = mapped_column(
        String(3), default="USD", nullable=False
    )
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)

    # Timestamps for auth tracking
    last_login: Mapped[datetime | None] = mapped_column(nullable=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    positions: Mapped[List["Position"]] = relationship(
        "Position", back_populates="user", cascade="all, delete-orphan"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )
    portfolio_snapshots: Mapped[List["PortfolioSnapshot"]] = relationship(
        "PortfolioSnapshot", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
