"""Asset schemas for API requests and responses."""

from decimal import Decimal

from pydantic import Field, field_validator

from backend.models.asset import AssetCategory, AssetType
from backend.schemas.base import BaseSchema, TimestampMixin


class AssetBase(BaseSchema):
    """Base asset schema with common fields."""

    ticker: str = Field(
        ..., min_length=1, max_length=20, description="Asset ticker symbol"
    )
    name: str = Field(..., min_length=1, max_length=255, description="Asset name")
    description: str | None = Field(
        None, max_length=1000, description="Asset description"
    )
    isin: str | None = Field(
        None,
        min_length=12,
        max_length=12,
        description="International Securities Identification Number (ISIN)",
    )
    asset_type: AssetType = Field(..., description="Type of asset")
    category: AssetCategory = Field(..., description="Asset category for allocation")
    sector: str | None = Field(
        None, max_length=100, description="Sector classification"
    )
    industry: str | None = Field(
        None, max_length=100, description="Industry classification"
    )
    exchange: str | None = Field(
        None, max_length=20, description="Exchange where asset is traded"
    )
    currency: str = Field(
        default="USD", max_length=3, description="Currency denomination"
    )
    country: str | None = Field(
        None, max_length=2, description="Country code (ISO 2-letter)"
    )

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Validate ticker format."""
        if not v or not v.strip():
            raise ValueError("Ticker cannot be empty")

        ticker = v.upper().strip()

        # Common European exchange suffixes
        european_suffixes = {
            ".L": "London Stock Exchange",
            ".PA": "Euronext Paris",
            ".DE": "Frankfurt/XETRA",
            ".MI": "Milan",
            ".AS": "Amsterdam",
            ".BR": "Brussels",
            ".LS": "Lisbon",
            ".MC": "Madrid",
            ".VI": "Vienna",
            ".ST": "Stockholm",
            ".HE": "Helsinki",
            ".OL": "Oslo",
            ".CO": "Copenhagen",
            ".IC": "Iceland",
            ".SW": "Swiss Exchange",
            ".TO": "Toronto",
            ".V": "TSX Venture",
            ".AX": "Australian Securities Exchange",
            ".T": "Tokyo Stock Exchange",
            ".HK": "Hong Kong Stock Exchange",
            ".SG": "Singapore Exchange",
            ".KS": "Korea Stock Exchange",
            ".SS": "Shanghai Stock Exchange",
            ".SZ": "Shenzhen Stock Exchange",
            ".NS": "National Stock Exchange of India",
            ".BO": "Bombay Stock Exchange",
            ".SA": "Brazil Stock Exchange",
        }

        # Validate ticker format
        if "." in ticker:
            parts = ticker.split(".")
            if len(parts) == 2:
                base_ticker, suffix = parts
                if not base_ticker or not suffix:
                    raise ValueError(
                        "Invalid ticker format: both base ticker and suffix are required"
                    )
                if len(base_ticker) < 1 or len(base_ticker) > 15:
                    raise ValueError("Base ticker must be between 1 and 15 characters")
                if len(suffix) < 1 or len(suffix) > 3:
                    raise ValueError(
                        "Exchange suffix must be between 1 and 3 characters"
                    )
                # Check if it's a known European/international suffix
                full_suffix = "." + suffix
                if full_suffix in european_suffixes:
                    # Valid international ticker - perform additional validation
                    cls._validate_international_ticker(ticker, full_suffix)
                # Unknown suffix - validate format but allow with warning
                elif not cls._is_valid_ticker_format(base_ticker):
                    raise ValueError(
                        f"Invalid ticker format for base ticker '{base_ticker}'. "
                        f"Must be 1-10 alphanumeric characters."
                    )
                    # Note: We allow unknown suffixes but could log a warning
            else:
                raise ValueError(
                    "Invalid ticker format: only one dot separator allowed"
                )
        # US ticker format
        elif len(ticker) < 1 or len(ticker) > 10:
            raise ValueError("US ticker must be between 1 and 10 characters")

        return ticker

    @classmethod
    def _is_valid_ticker_format(cls, ticker: str) -> bool:
        """Check if ticker has valid format (1-10 alphanumeric characters)."""
        import re

        return bool(re.match(r"^[A-Z0-9]{1,10}$", ticker))

    @classmethod
    def _validate_international_ticker(cls, ticker: str, suffix: str) -> None:
        """Perform additional validation for international tickers."""
        base_ticker = ticker.split(".")[0]

        # Validate base ticker format
        if not cls._is_valid_ticker_format(base_ticker):
            raise ValueError(
                f"Invalid base ticker format '{base_ticker}'. "
                f"Must be 1-10 alphanumeric characters."
            )

        # Additional validation based on exchange
        if suffix == ".L":  # London Stock Exchange
            if len(base_ticker) < 2:
                raise ValueError(
                    f"London Stock Exchange tickers typically have 2+ characters, got '{base_ticker}'"
                )
        elif suffix == ".PA":  # Euronext Paris
            if len(base_ticker) > 5:
                raise ValueError(
                    f"Euronext Paris tickers typically have 5 or fewer characters, got '{base_ticker}'"
                )
        elif suffix == ".AS":  # Euronext Amsterdam
            if len(base_ticker) > 5:
                raise ValueError(
                    f"Euronext Amsterdam tickers typically have 5 or fewer characters, got '{base_ticker}'"
                )
        # Add more exchange-specific validation as needed

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency format."""
        return v.upper()

    @field_validator("isin")
    @classmethod
    def validate_isin(cls, v: str | None) -> str | None:
        """Validate ISIN format and checksum."""
        if v is None or v == "":
            return None

        v = v.upper().strip()

        # Basic format validation
        import re

        if len(v) != 12 or not re.match(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$", v):
            raise ValueError(
                "ISIN must be 12 characters: 2 letters + 9 alphanumeric + 1 digit"
            )

        # Validate checksum using Luhn algorithm
        converted = ""
        for char in v[:-1]:  # Exclude check digit
            if char.isalpha():
                converted += str(ord(char.upper()) - ord("A") + 10)
            else:
                converted += char

        total = 0
        for i, digit in enumerate(reversed(converted)):
            n = int(digit)
            if i % 2 == 0:  # Every second digit from right
                n *= 2
                if n > 9:
                    n = n // 10 + n % 10
            total += n

        check_digit = (10 - (total % 10)) % 10
        if str(check_digit) != v[11]:
            raise ValueError(
                f"Invalid ISIN checksum (expected {check_digit}, got {v[11]})"
            )

        return v

    @field_validator("asset_type", mode="before")
    @classmethod
    def validate_asset_type(cls, v: str | AssetType) -> str:
        """Validate asset type, accepting both upper and lower case."""
        if isinstance(v, str):
            # Convert to lowercase to match enum values
            return v.lower()
        return v.value if hasattr(v, "value") else str(v)

    @field_validator("category", mode="before")
    @classmethod
    def validate_category(cls, v: str | AssetCategory) -> str:
        """Validate category, accepting both upper and lower case."""
        if isinstance(v, str):
            # Convert to lowercase to match enum values
            return v.lower()
        return v.value if hasattr(v, "value") else str(v)


class AssetCreate(AssetBase):
    """Schema for creating a new asset."""


class AssetUpdate(BaseSchema):
    """Schema for updating an asset."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    isin: str | None = Field(
        None, min_length=12, max_length=12, description="ISIN code"
    )
    sector: str | None = Field(None, max_length=100)
    industry: str | None = Field(None, max_length=100)
    exchange: str | None = Field(None, max_length=20)
    currency: str | None = Field(None, max_length=3)
    country: str | None = Field(None, max_length=2)
    is_active: bool | None = None

    @field_validator("currency", mode="before")
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        """Validate currency format."""
        if v is not None:
            return v.upper()
        return v

    @field_validator("isin")
    @classmethod
    def validate_isin_update(cls, v: str | None) -> str | None:
        """Validate ISIN format for updates."""
        if v is None or v == "":
            return None

        # Use the same validation as AssetBase
        return AssetBase.validate_isin(v)


class AssetMarketData(BaseSchema):
    """Schema for asset market data."""

    current_price: Decimal | None = Field(
        None, ge=0, description="Current market price"
    )
    previous_close: Decimal | None = Field(
        None, ge=0, description="Previous close price"
    )
    day_change: Decimal | None = Field(None, description="Absolute price change")
    day_change_percent: Decimal | None = Field(
        None, description="Percentage price change"
    )
    market_cap: Decimal | None = Field(None, ge=0, description="Market capitalization")
    pe_ratio: Decimal | None = Field(None, ge=0, description="Price-to-earnings ratio")
    dividend_yield: Decimal | None = Field(
        None, ge=0, le=100, description="Dividend yield percentage"
    )
    data_source: str | None = Field(None, max_length=50, description="Data source")


class AssetResponse(AssetBase, AssetMarketData, TimestampMixin):
    """Schema for asset response."""

    id: int = Field(..., description="Asset ID")
    is_active: bool = Field(default=True, description="Whether asset is active")

    @property
    def display_name(self) -> str:
        """Display-friendly name for the asset."""
        return f"{self.ticker} - {self.name}"

    @property
    def is_equity(self) -> bool:
        """Check if asset is an equity instrument."""
        return self.category == AssetCategory.EQUITY

    @property
    def is_fixed_income(self) -> bool:
        """Check if asset is a fixed income instrument."""
        return self.category == AssetCategory.FIXED_INCOME


class AssetSummary(BaseSchema):
    """Simplified asset schema for lists and references."""

    id: int
    ticker: str
    name: str
    asset_type: AssetType
    category: AssetCategory
    current_price: Decimal | None = None
    currency: str = "USD"
    isin: str | None = None
    is_active: bool = True


class AssetSearchParams(BaseSchema):
    """Parameters for asset search."""

    query: str | None = Field(None, description="Search query (ticker, name, or ISIN)")
    isin: str | None = Field(None, description="Search by ISIN code")
    asset_type: AssetType | None = Field(None, description="Filter by asset type")
    category: AssetCategory | None = Field(None, description="Filter by category")
    sector: str | None = Field(None, description="Filter by sector")
    exchange: str | None = Field(None, description="Filter by exchange")
    currency: str | None = Field(None, description="Filter by currency")
    is_active: bool = Field(True, description="Filter by active status")


class AssetPriceUpdate(BaseSchema):
    """Schema for updating asset prices."""

    current_price: Decimal = Field(..., ge=0, description="New current price")
    previous_close: Decimal | None = Field(
        None, ge=0, description="Previous close price"
    )
    data_source: str = Field(..., max_length=50, description="Source of price data")

    @property
    def day_change(self) -> Decimal | None:
        """Calculate absolute price change."""
        if self.previous_close:
            return self.current_price - self.previous_close
        return None

    @property
    def day_change_percent(self) -> Decimal | None:
        """Calculate percentage price change."""
        if self.previous_close and self.previous_close > 0:
            return (
                (self.current_price - self.previous_close) / self.previous_close
            ) * 100
        return None


class Update(BaseSchema):
    ticker: str
    current_price: Decimal
    previous_close: Decimal | None = None


class BulkAssetPriceUpdate(BaseSchema):
    """Schema for bulk asset price updates."""

    updates: list[Update] = Field(..., description="List of price updates")
    data_source: str = Field(..., max_length=50, description="Source of price data")
