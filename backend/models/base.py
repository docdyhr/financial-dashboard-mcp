"""Base database model and database setup."""

from collections.abc import Generator
from datetime import datetime

from sqlalchemy import DateTime, Integer, create_engine, func
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

from backend.config import get_settings

settings = get_settings()

# Create database engine
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@as_declarative()
class Base:
    """Base class for all database models."""

    # __tablename__ will be defined in each model individually.

    # Common fields for all models
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


def get_db() -> Generator[Session, None, None]:  # Add return type
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize the database."""
    Base.metadata.create_all(bind=engine)  # type: ignore[attr-defined]


def drop_db() -> None:
    """Drop all tables in the database."""
    Base.metadata.drop_all(bind=engine)  # type: ignore[attr-defined]
