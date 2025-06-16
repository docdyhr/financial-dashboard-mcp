"""ISIN (International Securities Identification Number) schemas for API operations."""

from datetime import datetime

from pydantic import Field, field_validator

from backend.schemas.base import BaseSchema, TimestampMixin


class ISINValidationRequest(BaseSchema):
    """Schema for ISIN validation requests."""

    isin: str = Field(
        ..., min_length=12, max_length=12, description="ISIN code to validate"
    )

    @field_validator("isin")
    @classmethod
    def validate_isin_format(cls, v: str) -> str:
        """Basic ISIN format validation."""
        if not v:
            raise ValueError("ISIN cannot be empty")

        v = v.upper().strip()

        # Basic format validation
        import re

        if len(v) != 12 or not re.match(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$", v):
            raise ValueError(
                "ISIN must be 12 characters: 2 letters + 9 alphanumeric + 1 digit"
            )

        return v


class ISINValidationResponse(BaseSchema):
    """Schema for ISIN validation responses."""

    isin: str = Field(..., description="ISIN code that was validated")
    is_valid: bool = Field(..., description="Whether the ISIN is valid")
    country_code: str | None = Field(None, description="Country code from ISIN")
    country_name: str | None = Field(None, description="Country name")
    national_code: str | None = Field(None, description="National securities code")
    check_digit: str | None = Field(None, description="Check digit")
    validation_error: str | None = Field(
        None, description="Validation error message if invalid"
    )


class ISINMappingBase(BaseSchema):
    """Base schema for ISIN ticker mappings."""

    isin: str = Field(..., min_length=12, max_length=12, description="ISIN code")
    ticker: str = Field(..., min_length=1, max_length=20, description="Ticker symbol")
    exchange_code: str | None = Field(None, max_length=10, description="Exchange code")
    exchange_name: str | None = Field(None, max_length=100, description="Exchange name")
    security_name: str | None = Field(None, max_length=200, description="Security name")
    currency: str | None = Field(
        None, min_length=3, max_length=3, description="Currency code"
    )
    source: str = Field(..., max_length=50, description="Data source")
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence score"
    )

    @field_validator("isin")
    @classmethod
    def validate_isin(cls, v: str) -> str:
        """Validate ISIN format."""
        v = v.upper().strip()
        import re

        if not re.match(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$", v):
            raise ValueError("Invalid ISIN format")
        return v

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Validate ticker format."""
        return v.upper().strip()

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        """Validate currency code."""
        if v is not None:
            return v.upper().strip()
        return v


class ISINMappingCreate(ISINMappingBase):
    """Schema for creating ISIN ticker mappings."""


class ISINMappingUpdate(BaseSchema):
    """Schema for updating ISIN ticker mappings."""

    exchange_code: str | None = Field(None, max_length=10)
    exchange_name: str | None = Field(None, max_length=100)
    security_name: str | None = Field(None, max_length=200)
    currency: str | None = Field(None, min_length=3, max_length=3)
    source: str | None = Field(None, max_length=50)
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    is_active: bool | None = None


class ISINMappingResponse(ISINMappingBase, TimestampMixin):
    """Schema for ISIN ticker mapping responses."""

    id: int = Field(..., description="Mapping ID")
    is_active: bool = Field(default=True, description="Whether mapping is active")
    last_updated: datetime = Field(..., description="Last update timestamp")


class ISINMappingSearchParams(BaseSchema):
    """Parameters for searching ISIN mappings."""

    isin: str | None = Field(None, description="Filter by ISIN")
    ticker: str | None = Field(None, description="Filter by ticker")
    exchange_code: str | None = Field(None, description="Filter by exchange")
    source: str | None = Field(None, description="Filter by data source")
    is_active: bool = Field(True, description="Filter by active status")
    min_confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Minimum confidence score"
    )


class ISINResolutionRequest(BaseSchema):
    """Schema for ISIN to ticker resolution requests."""

    identifier: str = Field(..., description="ISIN code or ticker symbol to resolve")
    preferred_exchange: str | None = Field(None, description="Preferred exchange code")
    preferred_country: str | None = Field(None, description="Preferred country code")

    @field_validator("identifier")
    @classmethod
    def validate_identifier(cls, v: str) -> str:
        """Validate identifier format."""
        return v.upper().strip()


class TickerInfo(BaseSchema):
    """Information about a ticker symbol."""

    ticker: str = Field(..., description="Ticker symbol")
    exchange_code: str | None = Field(None, description="Exchange code")
    exchange_name: str | None = Field(None, description="Exchange name")
    currency: str | None = Field(None, description="Currency")
    confidence: float = Field(..., description="Confidence score")
    source: str = Field(..., description="Data source")


class ISINResolutionResponse(BaseSchema):
    """Schema for ISIN to ticker resolution responses."""

    original_identifier: str = Field(..., description="Original input identifier")
    resolved_ticker: str | None = Field(None, description="Resolved ticker symbol")
    identifier_type: str = Field(..., description="Type: 'isin' or 'ticker'")
    success: bool = Field(..., description="Whether resolution was successful")
    error: str | None = Field(None, description="Error message if resolution failed")

    # ISIN-specific information (if input was ISIN)
    isin: str | None = Field(None, description="ISIN code")
    country_code: str | None = Field(None, description="Country code")
    country_name: str | None = Field(None, description="Country name")
    national_code: str | None = Field(None, description="National code")
    check_digit: str | None = Field(None, description="Check digit")

    # Available ticker options
    available_tickers: list[TickerInfo] | None = Field(
        None, description="List of available ticker mappings"
    )


class ISINLookupRequest(BaseSchema):
    """Schema for looking up assets by ISIN."""

    isins: list[str] = Field(
        ..., min_items=1, max_items=50, description="List of ISIN codes to lookup"
    )
    include_inactive: bool = Field(False, description="Include inactive mappings")
    preferred_exchanges: list[str] | None = Field(
        None, description="Preferred exchange codes"
    )

    @field_validator("isins")
    @classmethod
    def validate_isins(cls, v: list[str]) -> list[str]:
        """Validate ISIN format for bulk lookup."""
        validated = []
        for isin in v:
            isin = isin.upper().strip()
            import re

            if not re.match(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$", isin):
                raise ValueError(f"Invalid ISIN format: {isin}")
            validated.append(isin)
        return validated


class ISINLookupResult(BaseSchema):
    """Result for a single ISIN lookup."""

    isin: str = Field(..., description="ISIN code")
    success: bool = Field(..., description="Whether lookup was successful")
    tickers: list[TickerInfo] = Field(default=[], description="Found ticker mappings")
    error: str | None = Field(None, description="Error message if lookup failed")


class ISINLookupResponse(BaseSchema):
    """Schema for bulk ISIN lookup responses."""

    results: list[ISINLookupResult] = Field(
        ..., description="Lookup results for each ISIN"
    )
    total_requested: int = Field(..., description="Total ISINs requested")
    total_found: int = Field(..., description="Total ISINs with mappings found")
    total_failed: int = Field(..., description="Total ISINs that failed lookup")


class ISINSuggestionRequest(BaseSchema):
    """Schema for getting ticker format suggestions based on ISIN."""

    isin: str = Field(..., min_length=12, max_length=12, description="ISIN code")
    base_ticker: str = Field(
        ..., min_length=1, max_length=20, description="Base ticker symbol"
    )

    @field_validator("isin")
    @classmethod
    def validate_isin(cls, v: str) -> str:
        """Validate ISIN format."""
        v = v.upper().strip()
        import re

        if not re.match(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$", v):
            raise ValueError("Invalid ISIN format")
        return v

    @field_validator("base_ticker")
    @classmethod
    def validate_base_ticker(cls, v: str) -> str:
        """Validate base ticker format."""
        return v.upper().strip()


class TickerSuggestion(BaseSchema):
    """A suggested ticker format."""

    ticker: str = Field(..., description="Suggested ticker symbol")
    exchange_name: str = Field(..., description="Exchange name")
    country_code: str = Field(..., description="Country code")
    reason: str = Field(..., description="Reason for suggestion")


class ISINSuggestionResponse(BaseSchema):
    """Schema for ticker format suggestion responses."""

    isin: str = Field(..., description="ISIN code")
    base_ticker: str = Field(..., description="Base ticker symbol")
    country_code: str = Field(..., description="Country from ISIN")
    country_name: str = Field(..., description="Country name")
    suggestions: list[TickerSuggestion] = Field(
        ..., description="List of suggested ticker formats"
    )


class ISINStatistics(BaseSchema):
    """Statistics about ISIN mappings in the system."""

    total_mappings: int = Field(..., description="Total number of ISIN mappings")
    active_mappings: int = Field(..., description="Number of active mappings")
    unique_isins: int = Field(..., description="Number of unique ISINs")
    unique_tickers: int = Field(..., description="Number of unique tickers")
    countries_covered: int = Field(..., description="Number of countries covered")
    exchanges_covered: int = Field(..., description="Number of exchanges covered")
    top_countries: list[dict] = Field(..., description="Top countries by mapping count")
    top_exchanges: list[dict] = Field(..., description="Top exchanges by mapping count")
    data_sources: list[dict] = Field(..., description="Data sources and their counts")
    last_updated: datetime | None = Field(None, description="Last update timestamp")


class ISINImportRequest(BaseSchema):
    """Schema for importing ISIN mappings in bulk."""

    mappings: list[ISINMappingCreate] = Field(
        ..., min_items=1, max_items=1000, description="ISIN mappings to import"
    )
    update_existing: bool = Field(
        True, description="Whether to update existing mappings"
    )
    source: str = Field(..., description="Data source identifier")
    dry_run: bool = Field(False, description="Perform validation only without saving")


class ISINImportResult(BaseSchema):
    """Result of a single ISIN mapping import."""

    isin: str = Field(..., description="ISIN code")
    ticker: str = Field(..., description="Ticker symbol")
    status: str = Field(
        ..., description="Import status: created, updated, skipped, error"
    )
    error: str | None = Field(None, description="Error message if import failed")


class ISINImportResponse(BaseSchema):
    """Schema for bulk ISIN import responses."""

    results: list[ISINImportResult] = Field(
        ..., description="Import results for each mapping"
    )
    total_requested: int = Field(..., description="Total mappings requested")
    total_created: int = Field(..., description="Total new mappings created")
    total_updated: int = Field(..., description="Total existing mappings updated")
    total_skipped: int = Field(..., description="Total mappings skipped")
    total_errors: int = Field(..., description="Total mappings with errors")
    dry_run: bool = Field(..., description="Whether this was a dry run")
