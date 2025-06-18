"""Error handling middleware for FastAPI."""

import logging

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError

from backend.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    DatabaseError,
    DuplicateResourceError,
    ExternalServiceError,
    FinancialDashboardError,
    InsufficientFundsError,
    RateLimitError,
    ResourceNotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)


async def error_handler_middleware(request: Request, call_next):
    """Global error handler middleware."""
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        return handle_exception(exc)


def handle_exception(exc: Exception) -> JSONResponse:
    """Convert exceptions to JSON responses."""
    # Handle custom exceptions
    if isinstance(exc, ValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    if isinstance(exc, AuthenticationError):
        return JSONResponse(
            status_code=401,
            content={
                "error": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    if isinstance(exc, AuthorizationError):
        return JSONResponse(
            status_code=403,
            content={
                "error": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    if isinstance(exc, ResourceNotFoundError):
        return JSONResponse(
            status_code=404,
            content={
                "error": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    if isinstance(exc, DuplicateResourceError):
        return JSONResponse(
            status_code=409,
            content={
                "error": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    if isinstance(exc, InsufficientFundsError):
        return JSONResponse(
            status_code=400,
            content={
                "error": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    if isinstance(exc, RateLimitError):
        headers = {}
        if exc.details.get("retry_after"):
            headers["Retry-After"] = str(exc.details["retry_after"])
        return JSONResponse(
            status_code=429,
            content={
                "error": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
            headers=headers,
        )

    if isinstance(exc, ExternalServiceError):
        return JSONResponse(
            status_code=503,
            content={
                "error": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    if isinstance(exc, ConfigurationError | DatabaseError):
        return JSONResponse(
            status_code=500,
            content={
                "error": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    if isinstance(exc, FinancialDashboardError):
        # Generic financial dashboard error
        return JSONResponse(
            status_code=500,
            content={
                "error": exc.code or "INTERNAL_ERROR",
                "message": exc.message,
                "details": exc.details,
            },
        )

    # Handle SQLAlchemy exceptions
    if isinstance(exc, IntegrityError):
        logger.error(f"Database integrity error: {exc}")
        return JSONResponse(
            status_code=409,
            content={
                "error": "DATABASE_INTEGRITY_ERROR",
                "message": "Database constraint violation",
                "details": {
                    "error": str(exc.orig) if hasattr(exc, "orig") else str(exc)
                },
            },
        )

    if isinstance(exc, OperationalError):
        logger.error(f"Database operational error: {exc}")
        return JSONResponse(
            status_code=503,
            content={
                "error": "DATABASE_UNAVAILABLE",
                "message": "Database service unavailable",
                "details": {},
            },
        )

    # Handle FastAPI HTTPException
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP_ERROR",
                "message": exc.detail,
                "details": {},
            },
        )

    # Handle all other exceptions
    # Log the full exception with traceback
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # In production, don't expose internal errors
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": {},
        },
    )


def setup_exception_handlers(app):
    """Setup exception handlers for the FastAPI app."""
    # Add middleware
    app.middleware("http")(error_handler_middleware)

    # Add specific exception handlers
    app.add_exception_handler(ValidationError, handle_exception)
    app.add_exception_handler(AuthenticationError, handle_exception)
    app.add_exception_handler(AuthorizationError, handle_exception)
    app.add_exception_handler(ResourceNotFoundError, handle_exception)
    app.add_exception_handler(DuplicateResourceError, handle_exception)
    app.add_exception_handler(InsufficientFundsError, handle_exception)
    app.add_exception_handler(RateLimitError, handle_exception)
    app.add_exception_handler(ExternalServiceError, handle_exception)
    app.add_exception_handler(ConfigurationError, handle_exception)
    app.add_exception_handler(DatabaseError, handle_exception)
    app.add_exception_handler(FinancialDashboardError, handle_exception)
    app.add_exception_handler(IntegrityError, handle_exception)
    app.add_exception_handler(OperationalError, handle_exception)
    app.add_exception_handler(Exception, handle_exception)
