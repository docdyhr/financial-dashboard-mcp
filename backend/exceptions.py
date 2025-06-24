"""Centralized exception handling for the Financial Dashboard application."""

from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class FinancialDashboardError(Exception):
    """Base exception for all Financial Dashboard errors."""

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class ValidationError(FinancialDashboardError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code="VALIDATION_ERROR", details=details)
        if field:
            self.details["field"] = field


class AuthenticationError(FinancialDashboardError):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code="AUTH_ERROR", details=details)


class AuthorizationError(FinancialDashboardError):
    """Raised when user lacks required permissions."""

    def __init__(
        self, message: str = "Permission denied", details: dict[str, Any] | None = None
    ):
        super().__init__(message, code="AUTHZ_ERROR", details=details)


class ResourceNotFoundError(FinancialDashboardError):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: Any,
        details: dict[str, Any] | None = None,
    ):
        message = f"{resource_type} with id '{resource_id}' not found"
        super().__init__(message, code="NOT_FOUND", details=details)
        self.details.update(
            {"resource_type": resource_type, "resource_id": resource_id}
        )


class DuplicateResourceError(FinancialDashboardError):
    """Raised when attempting to create a duplicate resource."""

    def __init__(
        self, resource_type: str, identifier: str, details: dict[str, Any] | None = None
    ):
        message = f"{resource_type} with identifier '{identifier}' already exists"
        super().__init__(message, code="DUPLICATE", details=details)
        self.details.update({"resource_type": resource_type, "identifier": identifier})


class ExternalServiceError(FinancialDashboardError):
    """Raised when an external service fails."""

    def __init__(
        self, service: str, message: str, details: dict[str, Any] | None = None
    ):
        full_message = f"{service} error: {message}"
        super().__init__(full_message, code="EXTERNAL_SERVICE_ERROR", details=details)
        self.details["service"] = service


class MarketDataError(ExternalServiceError):
    """Raised when market data fetching fails."""

    def __init__(
        self,
        provider: str,
        ticker: str,
        message: str,
        suggestions: list[str] | None = None,
    ):
        details = {"ticker": ticker}
        if suggestions:
            details["suggestions"] = suggestions
        super().__init__(service=provider, message=message, details=details)


class DatabaseError(FinancialDashboardError):
    """Raised when a database operation fails."""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code="DATABASE_ERROR", details=details)
        if operation:
            self.details["operation"] = operation


class ConfigurationError(FinancialDashboardError):
    """Raised when configuration is invalid or missing."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code="CONFIG_ERROR", details=details)
        if config_key:
            self.details["config_key"] = config_key


class InsufficientFundsError(FinancialDashboardError):
    """Raised when attempting a transaction with insufficient funds."""

    def __init__(
        self,
        requested_amount: float,
        available_amount: float,
        currency: str,
        details: dict[str, Any] | None = None,
    ):
        message = f"Insufficient funds: requested {requested_amount} {currency}, available {available_amount} {currency}"
        super().__init__(message, code="INSUFFICIENT_FUNDS", details=details)
        self.details.update(
            {
                "requested_amount": requested_amount,
                "available_amount": available_amount,
                "currency": currency,
            }
        )


class ISINValidationError(ValidationError):
    """Raised when ISIN validation fails."""

    def __init__(self, isin: str, reason: str, details: dict[str, Any] | None = None):
        message = f"Invalid ISIN '{isin}': {reason}"
        super().__init__(message, field="isin", details=details)
        self.details["isin"] = isin
        self.details["reason"] = reason


class RateLimitError(ExternalServiceError):
    """Raised when API rate limit is exceeded."""

    def __init__(
        self,
        service: str,
        retry_after: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        message = "Rate limit exceeded"
        if retry_after:
            message += f", retry after {retry_after} seconds"
        super().__init__(service=service, message=message, details=details)
        if retry_after:
            self.details["retry_after"] = retry_after


# FastAPI Exception Handling

class ErrorDetail(BaseModel):
    """Standard error response model."""

    error: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = None


# Alias for backwards compatibility with core.exceptions
FinancialDashboardException = FinancialDashboardError


async def financial_dashboard_exception_handler(
    request: Request, exc: FinancialDashboardError
) -> JSONResponse:
    """Handle FinancialDashboardError and return standardized error response."""
    # Map to appropriate HTTP status code
    status_code_map = {
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "AUTH_ERROR": status.HTTP_401_UNAUTHORIZED,
        "AUTHZ_ERROR": status.HTTP_403_FORBIDDEN,
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "DUPLICATE": status.HTTP_409_CONFLICT,
        "RATE_LIMIT_ERROR": status.HTTP_429_TOO_MANY_REQUESTS,
        "EXTERNAL_SERVICE_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
        "DATABASE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "CONFIG_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "INSUFFICIENT_FUNDS": status.HTTP_400_BAD_REQUEST,
    }
    
    status_code = status_code_map.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    error_detail = ErrorDetail(
        error=exc.code or "INTERNAL_ERROR",
        message=exc.message,
        details=exc.details,
        request_id=request.headers.get("X-Request-ID"),
    )

    return JSONResponse(
        status_code=status_code,
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
