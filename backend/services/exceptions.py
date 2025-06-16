"""Centralized exception handling for services."""

from typing import Any

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError


class ServiceException(Exception):
    """Base exception for service layer."""

    def __init__(self, message: str, status_code: int = 500, details: Any = None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class NotFoundError(ServiceException):
    """Resource not found error."""

    def __init__(self, resource: str, identifier: Any):
        message = f"{resource} with ID {identifier} not found"
        super().__init__(message, status_code=404)


class ValidationError(ServiceException):
    """Validation error."""

    def __init__(self, message: str, field: str | None = None):
        details = {"field": field} if field else None
        super().__init__(message, status_code=400, details=details)


class PermissionError(ServiceException):
    """Permission denied error."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, status_code=403)


class ConflictError(ServiceException):
    """Resource conflict error."""

    def __init__(self, message: str):
        super().__init__(message, status_code=409)


class ExternalServiceError(ServiceException):
    """External service error."""

    def __init__(self, service: str, message: str):
        full_message = f"External service '{service}' error: {message}"
        super().__init__(full_message, status_code=502)


def handle_database_error(error: Exception) -> None:
    """Handle database errors and convert to appropriate exceptions."""
    if isinstance(error, IntegrityError):
        raise ConflictError("Database integrity violation")
    if isinstance(error, OperationalError):
        raise ServiceException("Database operation failed", status_code=503)
    raise ServiceException(f"Database error: {error!s}")


def to_http_exception(error: ServiceException) -> HTTPException:
    """Convert service exception to HTTP exception."""
    return HTTPException(
        status_code=error.status_code,
        detail={"message": error.message, "details": error.details},
    )
