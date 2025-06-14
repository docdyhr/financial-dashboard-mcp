"""Base Pydantic schemas for common response models."""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

# Generic type for data in responses
DataT = TypeVar("DataT")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )


class TimestampMixin(BaseModel):
    """Mixin for models with timestamps."""

    created_at: datetime
    updated_at: datetime


class BaseResponse(BaseSchema, Generic[DataT]):
    """Base response model for all API endpoints."""

    success: bool = True
    message: str | None = None
    data: DataT | None = None
    errors: list[str] | None = None


class ErrorResponse(BaseSchema):
    """Error response model."""

    success: bool = False
    message: str
    errors: list[str] | None = None
    error_code: str | None = None


class PaginationParams(BaseSchema):
    """Pagination parameters for list endpoints."""

    page: int = 1
    page_size: int = 20

    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseSchema, Generic[DataT]):
    """Paginated response model."""

    success: bool = True
    data: list[DataT]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

    @classmethod
    def create(
        cls, data: list[DataT], total: int, page: int, page_size: int
    ) -> "PaginatedResponse[DataT]":
        """Create paginated response from data."""
        total_pages = (total + page_size - 1) // page_size

        return cls(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )


class HealthCheck(BaseSchema):
    """Health check response."""

    status: str = "healthy"
    timestamp: datetime
    version: str
    environment: str
    database_status: str = "connected"
    redis_status: str = "connected"


class StatusResponse(BaseSchema):
    """Status response for API endpoints."""

    status: str = "operational"
    timestamp: datetime
    uptime_seconds: float | None = None
    requests_count: int | None = None
