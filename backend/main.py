"""Main FastAPI application for Financial Dashboard."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api import (
    assets,
    auth,
    cash_accounts,
    isin,
    portfolio,
    positions,
    tasks,
    transactions,
    user_settings,
)
from backend.config import get_settings
from backend.core.exceptions import (
    FinancialDashboardException,
    financial_dashboard_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)
from backend.database import get_db_session

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def _check_services() -> dict[str, str]:
    """Check health of dependent services."""
    services = {}

    # Check database
    try:
        from sqlalchemy import text

        with get_db_session() as db:
            db.execute(text("SELECT 1"))
        services["database"] = "healthy"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        services["database"] = "unhealthy"

    # Check Redis/Celery (simplified check)
    try:
        from backend.tasks import celery_app

        # Simple ping to check if Celery is responding
        result = celery_app.control.ping(timeout=1)
        services["celery"] = "healthy" if result else "unhealthy"
        services["redis"] = "healthy" if result else "unhealthy"
    except Exception as e:
        logger.warning(f"Celery/Redis health check failed: {e}")
        services["celery"] = "unhealthy"
        services["redis"] = "unhealthy"

    return services


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Financial Dashboard API...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    yield

    # Shutdown
    logger.info("Shutting down Financial Dashboard API...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(
    FinancialDashboardException, financial_dashboard_exception_handler
)
app.add_exception_handler(HTTPException, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Financial Dashboard API",
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from backend.core.security import validate_production_config

    config_errors = []
    if settings.environment == "production":
        config_errors = validate_production_config()

    status = "healthy" if not config_errors else "degraded"
    status_code = 200 if not config_errors else 503

    return JSONResponse(
        content={
            "status": status,
            "service": "backend",
            "version": settings.app_version,
            "environment": settings.environment,
            "config_errors": config_errors,
        },
        status_code=status_code,
    )


@app.get("/api/v1/status")
async def api_status():
    """API status endpoint with more detailed information."""
    return {
        "status": "operational",
        "api_version": "v1",
        "app_version": settings.app_version,
        "environment": settings.environment,
        "services": await _check_services(),
    }


# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["portfolio"])
app.include_router(assets.router, prefix="/api/v1/assets", tags=["assets"])
app.include_router(cash_accounts.router, prefix="/api/v1", tags=["cash-accounts"])
app.include_router(isin.router, prefix="/api/v1", tags=["isin"])
app.include_router(positions.router, prefix="/api/v1/positions", tags=["positions"])
app.include_router(
    transactions.router, prefix="/api/v1/transactions", tags=["transactions"]
)
app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
app.include_router(
    user_settings.router, prefix="/api/v1/user-settings", tags=["user-settings"]
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
