"""Task management API endpoints."""
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from backend.tasks.manager import task_manager

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskSubmissionRequest(BaseModel):
    """Request model for task submissions."""



class MarketDataRequest(TaskSubmissionRequest):
    """Request for market data fetch task."""

    symbols: list[str]
    period: str = "1d"


class PortfolioPricesRequest(TaskSubmissionRequest):
    """Request for portfolio price update task."""

    user_id: int | None = None


class AssetInfoRequest(TaskSubmissionRequest):
    """Request for asset info fetch task."""

    ticker: str


class PortfolioPerformanceRequest(TaskSubmissionRequest):
    """Request for portfolio performance calculation."""

    user_id: int
    days_back: int = 30


class PortfolioSnapshotRequest(TaskSubmissionRequest):
    """Request for portfolio snapshot creation."""

    user_id: int | None = None


class TaskResponse(BaseModel):
    """Response model for task submissions."""

    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """Response model for task status."""

    task_id: str
    status: str
    ready: bool
    successful: bool | None = None
    failed: bool | None = None
    result: Any | None = None
    error: str | None = None
    progress: dict[str, Any] | None = None


@router.post("/market-data", response_model=TaskResponse)
async def submit_market_data_task(request: MarketDataRequest):
    """Submit a market data fetch task."""
    try:
        task_id = task_manager.submit_market_data_update(
            symbols=request.symbols, period=request.period
        )
        return TaskResponse(
            task_id=task_id,
            status="submitted",
            message=f"Market data fetch task submitted for {len(request.symbols)} symbols",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio-prices", response_model=TaskResponse)
async def submit_portfolio_prices_task(request: PortfolioPricesRequest):
    """Submit a portfolio price update task."""
    try:
        task_id = task_manager.submit_portfolio_price_update(user_id=request.user_id)
        user_msg = f"user {request.user_id}" if request.user_id else "all users"
        return TaskResponse(
            task_id=task_id,
            status="submitted",
            message=f"Portfolio price update task submitted for {user_msg}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/asset-info", response_model=TaskResponse)
async def submit_asset_info_task(request: AssetInfoRequest):
    """Submit an asset info fetch task."""
    try:
        task_id = task_manager.submit_asset_info_fetch(ticker=request.ticker)
        return TaskResponse(
            task_id=task_id,
            status="submitted",
            message=f"Asset info fetch task submitted for {request.ticker}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio-performance", response_model=TaskResponse)
async def submit_portfolio_performance_task(request: PortfolioPerformanceRequest):
    """Submit a portfolio performance calculation task."""
    try:
        task_id = task_manager.submit_portfolio_performance_calculation(
            user_id=request.user_id, days_back=request.days_back
        )
        return TaskResponse(
            task_id=task_id,
            status="submitted",
            message=f"Portfolio performance calculation submitted for user {request.user_id}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio-snapshot", response_model=TaskResponse)
async def submit_portfolio_snapshot_task(request: PortfolioSnapshotRequest):
    """Submit a portfolio snapshot creation task."""
    try:
        task_id = task_manager.submit_portfolio_snapshot_creation(
            user_id=request.user_id
        )
        user_msg = f"user {request.user_id}" if request.user_id else "all users"
        return TaskResponse(
            task_id=task_id,
            status="submitted",
            message=f"Portfolio snapshot creation submitted for {user_msg}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get the status of a specific task."""
    try:
        status_info = task_manager.get_task_status(task_id)
        return TaskStatusResponse(**status_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cancel/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a running task."""
    try:
        success = task_manager.cancel_task(task_id)
        if success:
            return {"message": f"Task {task_id} cancelled successfully"}
        raise HTTPException(status_code=400, detail="Failed to cancel task")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_tasks():
    """Get list of currently active tasks."""
    try:
        active_tasks = task_manager.get_active_tasks()
        return {"active_tasks": active_tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workers")
async def get_worker_stats():
    """Get Celery worker statistics."""
    try:
        stats = task_manager.get_worker_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk/update-all-prices")
async def bulk_update_all_prices(background_tasks: BackgroundTasks):
    """Convenience endpoint to update all portfolio prices."""
    try:
        task_id = task_manager.submit_portfolio_price_update(user_id=None)
        return TaskResponse(
            task_id=task_id,
            status="submitted",
            message="Bulk price update task submitted for all users",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk/create-snapshots")
async def bulk_create_snapshots(background_tasks: BackgroundTasks):
    """Convenience endpoint to create portfolio snapshots for all users."""
    try:
        task_id = task_manager.submit_portfolio_snapshot_creation(user_id=None)
        return TaskResponse(
            task_id=task_id,
            status="submitted",
            message="Bulk snapshot creation task submitted for all users",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
