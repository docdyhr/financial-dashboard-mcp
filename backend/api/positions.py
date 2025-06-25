"""Positions API router for managing portfolio positions."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_active_user
from backend.exceptions import ResourceNotFoundError as NotFoundError
from backend.exceptions import ValidationError
from backend.models import get_db
from backend.models.user import User
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
    current_user: Annotated[User, Depends(get_current_active_user)],
    asset_type: str | None = Query(None, description="Filter by asset type"),
    category: str | None = Query(None, description="Filter by asset category"),
    account_name: str | None = Query(None, description="Filter by account name"),
    is_active: bool = Query(True, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[PositionResponse]:
    """Get positions for the authenticated user with optional filters and pagination."""
    # Create filters object
    filters = PositionFilters(
        user_id=current_user.id,
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
        db, current_user.id, filters, skip, page_size
    )

    # Get total count for pagination
    total = position_service.count(
        db, filters={"user_id": current_user.id, "is_active": is_active}
    )

    return PaginatedResponse.create(
        data=positions, total=total, page=page, page_size=page_size
    )


@router.get("/{position_id}", response_model=BaseResponse[PositionResponse])
async def get_position(
    position_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> BaseResponse[PositionResponse]:
    """Get a specific position by ID."""
    position = position_service.get(db, position_id)
    if not position:
        raise NotFoundError("Position", position_id)

    # Ensure user owns this position
    if position.user_id != current_user.id:
        raise NotFoundError("Position", position_id)

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
        raise NotFoundError("Position", position_id)

    return BaseResponse(
        success=True,
        message="Position retrieved successfully",
        data=position_response,
    )


@router.post("/", response_model=BaseResponse[PositionResponse])
async def create_position(
    position_create: PositionCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> BaseResponse[PositionResponse]:
    """Create a new position."""
    # Set the user_id to the authenticated user
    position_create.user_id = current_user.id

    try:
        position = position_service.create_position(db, position_create)
    except ValueError as e:
        raise ValidationError(str(e))

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


@router.put("/{position_id}", response_model=BaseResponse[PositionResponse])
async def update_position(
    position_id: int,
    position_update: PositionUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> BaseResponse[PositionResponse]:
    """Update an existing position."""
    position = position_service.get(db, position_id)
    if not position:
        raise NotFoundError("Position", position_id)

    # Ensure user owns this position
    if position.user_id != current_user.id:
        raise NotFoundError("Position", position_id)

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


@router.post("/{position_id}/adjust", response_model=BaseResponse[PositionResponse])
async def adjust_position(
    position_id: int,
    adjustment: PositionAdjustment,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> BaseResponse[PositionResponse]:
    """Adjust position quantity (buy/sell)."""
    position = position_service.get(db, position_id)
    if not position:
        raise NotFoundError("Position", position_id)

    # Ensure user owns this position
    if position.user_id != current_user.id:
        raise NotFoundError("Position", position_id)

    try:
        updated_position = position_service.adjust_position(db, position_id, adjustment)
    except ValueError as e:
        raise ValidationError(str(e))

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
        message=f"Position {adjustment.adjustment_type}d successfully",
        data=position_response,
    )


@router.delete("/{position_id}", response_model=BaseResponse[dict[str, Any]])
async def delete_position(
    position_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> BaseResponse[dict[str, Any]]:
    """Delete a position."""
    position = position_service.get(db, position_id)
    if not position:
        raise NotFoundError("Position", position_id)

    # Ensure user owns this position
    if position.user_id != current_user.id:
        raise NotFoundError("Position", position_id)

    position_service.remove(db, id=position_id)

    return BaseResponse(
        success=True,
        message="Position deleted successfully",
        data={"id": position_id},
    )


@router.post("/{position_id}/close", response_model=BaseResponse[PositionResponse])
async def close_position(
    position_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    close_price: float | None = None,
) -> BaseResponse[PositionResponse]:
    """Close a position."""
    position = position_service.get(db, position_id)
    if not position:
        raise NotFoundError("Position", position_id)

    # Ensure user owns this position
    if position.user_id != current_user.id:
        raise NotFoundError("Position", position_id)

    try:
        closed_position = position_service.close_position(db, position_id, close_price)
    except ValueError as e:
        raise ValidationError(str(e))

    # Get the updated position in response format
    positions = position_service.get_user_positions(
        db,
        closed_position.user_id,
        filters=PositionFilters(
            user_id=closed_position.user_id, min_value=None, max_value=None
        ),
        skip=0,
        limit=1000,
    )

    position_response = next((p for p in positions if p.id == position_id), None)

    return BaseResponse(
        success=True,
        message="Position closed successfully",
        data=position_response,
    )


@router.get("/summary/{user_id}", response_model=BaseResponse[PositionSummary])
async def get_position_summary(
    current_user: Annotated[User, Depends(get_current_active_user)],
    account_name: str | None = None,
    db: Session = Depends(get_db),
) -> BaseResponse[PositionSummary]:
    """Get position summary for the authenticated user."""
    summary = position_service.get_position_summary(
        db, current_user.id, account_name=account_name
    )

    return BaseResponse(
        success=True,
        message="Position summary retrieved successfully",
        data=summary,
    )
