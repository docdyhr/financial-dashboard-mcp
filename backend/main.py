"""Main FastAPI application for Financial Dashboard."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api import assets, portfolio, positions, tasks
from backend.config import get_settings
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
    except Exception:
        services["database"] = "unhealthy"

    # Check Redis/Celery (simplified check)
    try:
        from backend.tasks import celery_app

        # Simple ping to check if Celery is responding
        result = celery_app.control.ping(timeout=1)
        services["celery"] = "healthy" if result else "unhealthy"
        services["redis"] = "healthy" if result else "unhealthy"
    except Exception:
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
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "backend",
            "version": settings.app_version,
        },
        status_code=200,
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
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["portfolio"])
app.include_router(assets.router, prefix="/api/v1/assets", tags=["assets"])
app.include_router(positions.router, prefix="/api/v1/positions", tags=["positions"])
app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
