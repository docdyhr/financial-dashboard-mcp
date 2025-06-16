"""Positions API router for managing portfolio positions."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.models import get_db
from backend.schemas.base import BaseResponse, PaginatedResponse
from backend.schemas.position import (
    PositionAdjustment,
    PositionCreate,
    PositionFilters,
    PositionResponse,
    PositionSummary,
    PositionUpdate,
)
from backend.services.position import PositionService

router = APIRouter()
position_service = PositionService()


@router.get("/", response_model=PaginatedResponse[PositionResponse])
async def get_positions(
    user_id: int = Query(..., description="User ID to get positions for"),
    asset_type: str | None = Query(None, description="Filter by asset type"),
    category: str | None = Query(None, description="Filter by asset category"),
    account_name: str | None = Query(None, description="Filter by account name"),
    is_active: bool = Query(True, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[PositionResponse]:
    """Get positions for a user with optional filters and pagination."""
    try:
        # Create filters object
        filters = PositionFilters(
            user_id=user_id,
            asset_type=asset_type,
            category=category,
            account_name=account_name,
            is_active=is_active,
            min_value=None,
            max_value=None,
        )

        # Calculate pagination
        skip = (page - 1) * page_size

        # Get positions
        positions = position_service.get_user_positions(
            db, user_id, filters, skip, page_size
        )

        # Get total count for pagination
        total = position_service.count(
            db, filters={"user_id": user_id, "is_active": is_active}
        )

        return PaginatedResponse.create(
            data=positions, total=total, page=page, page_size=page_size
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{position_id}", response_model=BaseResponse[PositionResponse])
async def get_position(
    position_id: int, db: Session = Depends(get_db)
) -> BaseResponse[PositionResponse]:
    """Get a specific position by ID."""
    try:
        position = position_service.get(db, position_id)
        if not position:
            raise HTTPException(status_code=404, detail="Position not found")

        # Convert to response format
        positions = position_service.get_user_positions(
            db,
            position.user_id,
            filters=PositionFilters(
                user_id=position.user_id, min_value=None, max_value=None
            ),
            skip=0,
            limit=1000,
        )

        position_response = next((p for p in positions if p.id == position_id), None)

        if not position_response:
            raise HTTPException(status_code=404, detail="Position not found")

        return BaseResponse(
            success=True,
            message="Position retrieved successfully",
            data=position_response,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/", response_model=BaseResponse[PositionResponse])
async def create_position(
    position_create: PositionCreate, db: Session = Depends(get_db)
) -> BaseResponse[PositionResponse]:
    """Create a new position."""
    try:
        position = position_service.create_position(db, position_create)

        # Get the created position in response format
        positions = position_service.get_user_positions(
            db,
            position.user_id,
            filters=PositionFilters(
                user_id=position.user_id, min_value=None, max_value=None
            ),
            skip=0,
            limit=1000,
        )

        position_response = next((p for p in positions if p.id == position.id), None)

        return BaseResponse(
            success=True,
            message="Position created successfully",
            data=position_response,
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/{position_id}", response_model=BaseResponse[PositionResponse])
async def update_position(
    position_id: int, position_update: PositionUpdate, db: Session = Depends(get_db)
) -> BaseResponse[PositionResponse]:
    """Update an existing position."""
    try:
        position = position_service.get(db, position_id)
        if not position:
            raise HTTPException(status_code=404, detail="Position not found")

        updated_position = position_service.update(
            db, db_obj=position, obj_in=position_update
        )

        # Get the updated position in response format
        positions = position_service.get_user_positions(
            db,
            updated_position.user_id,
            filters=PositionFilters(
                user_id=updated_position.user_id, min_value=None, max_value=None
            ),
            skip=0,
            limit=1000,
        )

        position_response = next((p for p in positions if p.id == position_id), None)

        return BaseResponse(
            success=True,
            message="Position updated successfully",
            data=position_response,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/{position_id}", response_model=BaseResponse)
async def delete_position(
    position_id: int,
    soft_delete: bool = Query(
        True, description="Soft delete (mark inactive) or hard delete"
    ),
    db: Session = Depends(get_db),
) -> BaseResponse[Any]:
    """Delete a position."""
    try:
        if soft_delete:
            _ = position_service.soft_delete(db, obj_id=position_id)  # type: ignore
        else:
            _ = position_service.delete(db, obj_id=position_id)  # type: ignore

        return BaseResponse(
            success=True,
            message="Position deleted successfully",
            data=None,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/adjust/{position_id}", response_model=BaseResponse[PositionResponse])
async def adjust_position(
    position_id: int, adjustment: PositionAdjustment, db: Session = Depends(get_db)
) -> BaseResponse[PositionResponse]:
    """Adjust a position by adding or reducing shares."""
    try:
        updated_position = position_service.adjust_position(db, position_id, adjustment)
        positions = position_service.get_user_positions(
            db,
            updated_position.user_id,
            filters=PositionFilters(
                user_id=updated_position.user_id, min_value=None, max_value=None
            ),
            skip=0,
            limit=1000,
        )
        position_response = next((p for p in positions if p.id == position_id), None)
        return BaseResponse(
            success=True,
            message="Position adjusted successfully",
            data=position_response,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/close/{position_id}", response_model=BaseResponse[Any])
async def close_position(
    position_id: int, db: Session = Depends(get_db)
) -> BaseResponse[Any]:
    """Close a position by setting quantity to 0."""
    try:
        _ = position_service.close_position(db, position_id)
        return BaseResponse(
            success=True,
            message="Position closed successfully",
            data=None,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/performance/{position_id}", response_model=BaseResponse[Any])
async def get_position_performance(
    position_id: int, db: Session = Depends(get_db)
) -> BaseResponse[Any]:
    """Get performance metrics for a specific position."""
    try:
        performance = position_service.get_position_performance(db, position_id)
        return BaseResponse(
            success=True,
            message="Performance metrics retrieved successfully",
            data=performance,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/category/{user_id}/{category}", response_model=BaseResponse[list[PositionSummary]]
)
async def get_positions_by_category(
    user_id: int, category: str, db: Session = Depends(get_db)
) -> BaseResponse[list[PositionSummary]]:
    """Get all positions in a specific asset category."""
    try:
        positions = position_service.get_positions_by_category(db, user_id, category)
        position_summaries = [PositionSummary.model_validate(p) for p in positions]
        return BaseResponse(
            success=True,
            message=f"Positions in category '{category}' retrieved successfully",
            data=position_summaries,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/sector/{user_id}/{sector}", response_model=BaseResponse[list[PositionSummary]]
)
async def get_positions_by_sector(
    user_id: int, sector: str, db: Session = Depends(get_db)
) -> BaseResponse[list[PositionSummary]]:
    """Get all positions in a specific sector."""
    try:
        positions = position_service.get_positions_by_sector(db, user_id, sector)
        position_summaries = [PositionSummary.model_validate(p) for p in positions]
        return BaseResponse(
            success=True,
            message=f"Positions in sector '{sector}' retrieved successfully",
            data=position_summaries,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/total_value/{user_id}", response_model=BaseResponse[Any])
async def get_total_portfolio_value(
    user_id: int, db: Session = Depends(get_db)
) -> BaseResponse[Any]:
    """Calculate total value of all positions for a user."""
    try:
        total_value = position_service.calculate_total_portfolio_value(db, user_id)
        return BaseResponse(
            success=True,
            message="Total portfolio value calculated successfully",
            data=total_value,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/consolidate", response_model=BaseResponse[Any])
async def consolidate_positions(
    position_ids: list[int], db: Session = Depends(get_db)
) -> BaseResponse[Any]:
    """Consolidate multiple positions of the same asset into one."""
    try:
        consolidated_position = position_service.consolidate_positions(db, position_ids)
        return BaseResponse(
            success=True,
            message="Positions consolidated successfully",
            data=consolidated_position,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/split/{position_id}", response_model=BaseResponse[Any])
async def handle_stock_split(
    position_id: int,
    split_ratio: float,
    notes: str | None = None,
    db: Session = Depends(get_db),
) -> BaseResponse[Any]:
    """Handle stock split for a position."""
    try:
        from decimal import Decimal

        split_ratio_decimal = Decimal(str(split_ratio))
        split_result = position_service.split_position(
            db, position_id, split_ratio_decimal, notes
        )
        return BaseResponse(
            success=True,
            message="Stock split handled successfully",
            data=split_result,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
