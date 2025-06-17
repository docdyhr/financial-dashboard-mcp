"""ISIN (International Securities Identification Number) related models."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, validates
from sqlalchemy.sql import func

from backend.models.base import Base


class ISINTickerMapping(Base):
    """Model for storing ISIN to ticker symbol mappings."""

    __tablename__ = "isin_ticker_mappings"

    # Primary identifiers
    isin: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Exchange information
    exchange_code: Mapped[str | None] = mapped_column(
        String(10), nullable=True, index=True
    )
    exchange_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Security details
    security_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)

    # Mapping metadata
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )

    # Timestamps
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "isin",
            "ticker",
            "exchange_code",
            name="uq_isin_ticker_exchange_active",
        ),
    )

    @validates("isin")
    def validate_isin(self, key: str, isin: str) -> str:
        """Validate ISIN format."""
        if not isin:
            raise ValueError("ISIN cannot be empty")

        isin = isin.upper().strip()

        # Basic format validation
        import re

        if len(isin) != 12 or not re.match(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$", isin):
            raise ValueError(
                "ISIN must be 12 characters: 2 letters + 9 alphanumeric + 1 digit"
            )

        return isin

    @validates("ticker")
    def validate_ticker(self, key: str, ticker: str) -> str:
        """Validate ticker format."""
        if not ticker:
            raise ValueError("Ticker cannot be empty")

        ticker = ticker.upper().strip()

        # Basic ticker validation
        if len(ticker) > 20:
            raise ValueError("Ticker cannot be longer than 20 characters")

        return ticker

    @validates("confidence")
    def validate_confidence(self, key: str, confidence: float) -> float:
        """Validate confidence score."""
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return confidence

    @validates("currency")
    def validate_currency(self, key: str, currency: str | None) -> str | None:
        """Validate currency code."""
        if currency is None:
            return None

        currency = currency.upper().strip()

        if len(currency) != 3:
            raise ValueError("Currency must be a 3-letter ISO code")

        return currency

    def __repr__(self) -> str:
        return (
            f"<ISINTickerMapping(id={self.id}, isin={self.isin}, "
            f"ticker={self.ticker}, exchange={self.exchange_code}, "
            f"source={self.source}, active={self.is_active})>"
        )

    @property
    def display_name(self) -> str:
        """Return a display-friendly representation."""
        exchange_part = f" ({self.exchange_code})" if self.exchange_code else ""
        return f"{self.ticker}{exchange_part} -> {self.isin}"

    @property
    def country_code(self) -> str:
        """Extract country code from ISIN."""
        return self.isin[:2] if self.isin else ""

    @property
    def national_code(self) -> str:
        """Extract national code from ISIN."""
        return self.isin[2:11] if len(self.isin) >= 11 else ""

    @property
    def check_digit(self) -> str:
        """Extract check digit from ISIN."""
        return self.isin[11] if len(self.isin) == 12 else ""


class ISINValidationCache(Base):
    """Model for caching ISIN validation results to improve performance."""

    __tablename__ = "isin_validation_cache"

    # ISIN being validated
    isin: Mapped[str] = mapped_column(
        String(12), nullable=False, unique=True, index=True
    )

    # Validation results
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    country_code: Mapped[str | None] = mapped_column(
        String(2), nullable=True, index=True
    )
    country_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    national_code: Mapped[str | None] = mapped_column(String(9), nullable=True)
    check_digit: Mapped[str | None] = mapped_column(String(1), nullable=True)
    validation_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Cache metadata
    cached_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    @validates("isin")
    def validate_isin_format(self, key: str, isin: str) -> str:
        """Validate ISIN format before caching."""
        if not isin:
            raise ValueError("ISIN cannot be empty")

        isin = isin.upper().strip()

        # Basic format validation
        import re

        if len(isin) != 12 or not re.match(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$", isin):
            raise ValueError(
                "ISIN must be 12 characters: 2 letters + 9 alphanumeric + 1 digit"
            )

        return isin

    @validates("country_code")
    def validate_country_code(self, key: str, country_code: str | None) -> str | None:
        """Validate country code format."""
        if country_code is None:
            return None

        country_code = country_code.upper().strip()

        if len(country_code) != 2:
            raise ValueError("Country code must be 2 letters")

        return country_code

    def __repr__(self) -> str:
        return (
            f"<ISINValidationCache(id={self.id}, isin={self.isin}, "
            f"valid={self.is_valid}, country={self.country_code})>"
        )

    def is_fresh(self, max_age_hours: int = 24) -> bool:
        """Check if the cached validation is still fresh."""
        if not self.cached_at:
            return False

        age = datetime.now(self.cached_at.tzinfo) - self.cached_at
        return age.total_seconds() < (max_age_hours * 3600)

    @classmethod
    def create_from_validation(
        cls,
        isin: str,
        is_valid: bool,
        country_code: str | None = None,
        country_name: str | None = None,
        national_code: str | None = None,
        check_digit: str | None = None,
        validation_error: str | None = None,
    ) -> "ISINValidationCache":
        """Create a new validation cache entry."""
        instance = cls()
        instance.isin = isin
        instance.is_valid = is_valid
        instance.country_code = country_code
        instance.country_name = country_name
        instance.national_code = national_code
        instance.check_digit = check_digit
        instance.validation_error = validation_error
        return instance
