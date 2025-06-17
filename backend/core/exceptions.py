"""Standardized exception handling for the Financial Dashboard API."""

from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Standard error response model."""

    error: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = None


class FinancialDashboardException(Exception):
    """Base exception for Financial Dashboard."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(FinancialDashboardException):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class NotFoundError(FinancialDashboardException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} not found",
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "identifier": str(identifier)},
        )


class DuplicateError(FinancialDashboardException):
    """Raised when attempting to create a duplicate resource."""

    def __init__(self, resource: str, field: str, value: Any):
        super().__init__(
            message=f"{resource} with {field}='{value}' already exists",
            error_code="DUPLICATE_ERROR",
            status_code=status.HTTP_409_CONFLICT,
            details={"resource": resource, "field": field, "value": str(value)},
        )


class AuthenticationError(FinancialDashboardException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationError(FinancialDashboardException):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ExternalServiceError(FinancialDashboardException):
    """Raised when an external service fails."""

    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"External service error: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": service},
        )


class RateLimitError(FinancialDashboardException):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


async def financial_dashboard_exception_handler(
    request: Request, exc: FinancialDashboardException
) -> JSONResponse:
    """Handle FinancialDashboardException and return standardized error response."""
    error_detail = ErrorDetail(
        error=exc.error_code,
        message=exc.message,
        details=exc.details,
        request_id=request.headers.get("X-Request-ID"),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_detail.model_dump(exclude_none=True),
    )


async def validation_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """Handle validation exceptions and return standardized error response."""
    error_detail = ErrorDetail(
        error="VALIDATION_ERROR",
        message=str(exc.detail),
        request_id=request.headers.get("X-Request-ID"),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_detail.model_dump(exclude_none=True),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle generic exceptions and return standardized error response."""
    import logging

    logger = logging.getLogger(__name__)
    logger.exception("Unhandled exception occurred")

    error_detail = ErrorDetail(
        error="INTERNAL_ERROR",
        message="An internal error occurred",
        request_id=request.headers.get("X-Request-ID"),
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_detail.model_dump(exclude_none=True),
    )
