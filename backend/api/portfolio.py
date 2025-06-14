"""Portfolio API router for portfolio summary and performance endpoints."""

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.models import get_db
from backend.schemas.base import BaseResponse
from backend.schemas.portfolio import (
    AllocationBreakdown,
    DiversificationMetrics,
    PerformanceMetrics,
    PortfolioSummary,
)
from backend.services.portfolio import PortfolioService

router = APIRouter()
portfolio_service = PortfolioService()


@router.get("/summary/{user_id}", response_model=BaseResponse[PortfolioSummary])
async def get_portfolio_summary(
    user_id: int, db: Session = Depends(get_db)
) -> BaseResponse[PortfolioSummary]:
    """Get comprehensive portfolio summary for a user."""
    try:
        summary = portfolio_service.get_portfolio_summary(db, user_id)
        return BaseResponse(
            success=True,
            message="Portfolio summary retrieved successfully",
            data=summary,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/allocation/{user_id}", response_model=BaseResponse[AllocationBreakdown])
async def get_allocation_breakdown(
    user_id: int, db: Session = Depends(get_db)
) -> BaseResponse[AllocationBreakdown]:
    """Get asset allocation breakdown for a portfolio."""
    try:
        allocation = portfolio_service.get_allocation_breakdown(db, user_id)
        return BaseResponse(
            success=True,
            message="Allocation breakdown retrieved successfully",
            data=allocation,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/performance/{user_id}", response_model=BaseResponse[PerformanceMetrics])
async def get_performance_metrics(
    user_id: int,
    start_date: date | None = Query(
        None, description="Start date for performance calculation"
    ),
    end_date: date | None = Query(
        None, description="End date for performance calculation"
    ),
    db: Session = Depends(get_db),
) -> BaseResponse[PerformanceMetrics]:
    """Calculate portfolio performance metrics."""
    try:
        performance = portfolio_service.calculate_performance_metrics(
            db, user_id, start_date, end_date
        )
        return BaseResponse(
            success=True,
            message="Performance metrics calculated successfully",
            data=performance,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/diversification/{user_id}", response_model=BaseResponse[DiversificationMetrics]
)
async def get_diversification_metrics(
    user_id: int, db: Session = Depends(get_db)
) -> BaseResponse[DiversificationMetrics]:
    """Get portfolio diversification metrics."""
    try:
        diversification = portfolio_service.get_diversification_metrics(db, user_id)
        return BaseResponse(
            success=True,
            message="Diversification metrics calculated successfully",
            data=diversification,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/snapshot/{user_id}")
async def create_portfolio_snapshot(
    user_id: int, snapshot_date: date | None = None, db: Session = Depends(get_db)
) -> BaseResponse[dict[str, Any]]:
    """Create a portfolio snapshot for a specific date."""
    try:
        snapshot = portfolio_service.create_portfolio_snapshot(
            db, user_id, snapshot_date
        )
        return BaseResponse(
            success=True,
            message="Portfolio snapshot created successfully",
            data={
                "snapshot_id": snapshot.id,
                "snapshot_date": snapshot.snapshot_date,
                "total_value": snapshot.total_value,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/comparison/{user_id}")
async def get_performance_comparison(
    user_id: int,
    benchmark_ticker: str = Query("SPY", description="Benchmark ticker for comparison"),
    start_date: date | None = Query(None, description="Start date for comparison"),
    end_date: date | None = Query(None, description="End date for comparison"),
    db: Session = Depends(get_db),
) -> BaseResponse[Any]:
    """Compare portfolio performance to a benchmark."""
    try:
        comparison = portfolio_service.get_performance_comparison(
            db, user_id, benchmark_ticker, start_date, end_date
        )
        return BaseResponse(
            success=True,
            message="Performance comparison calculated successfully",
            data=comparison,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/weights/{user_id}")
async def get_position_weights(
    user_id: int, db: Session = Depends(get_db)
) -> BaseResponse[Any]:
    """Get position weights in portfolio."""
    try:
        weights = portfolio_service.calculate_position_weights(db, user_id)
        return BaseResponse(
            success=True,
            message="Position weights calculated successfully",
            data=weights,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
