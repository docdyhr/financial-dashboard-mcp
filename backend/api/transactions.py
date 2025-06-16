"""Transaction API router for managing portfolio transactions."""

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.models import get_db
from backend.schemas.base import BaseResponse, PaginatedResponse
from backend.schemas.transaction import (
    BuyTransactionRequest,
    DividendTransactionRequest,
    SellTransactionRequest,
    TransactionFilters,
    TransactionPerformanceMetrics,
    TransactionResponse,
    TransactionUpdate,
)
from backend.services.transaction import TransactionService

router = APIRouter()
transaction_service = TransactionService()


@router.get("/", response_model=PaginatedResponse[TransactionResponse])
async def get_transactions(
    user_id: int = Query(..., description="User ID to get transactions for"),
    asset_id: int | None = Query(None, description="Filter by asset ID"),
    position_id: int | None = Query(None, description="Filter by position ID"),
    transaction_type: str
    | None = Query(None, description="Filter by transaction type"),
    account_name: str | None = Query(None, description="Filter by account name"),
    start_date: date | None = Query(None, description="Filter from date"),
    end_date: date | None = Query(None, description="Filter to date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[TransactionResponse]:
    """Get transactions for a user with optional filters and pagination."""
    try:
        # Create filters object
        filters = TransactionFilters(
            user_id=user_id,
            asset_id=asset_id,
            position_id=position_id,
            transaction_type=transaction_type,
            account_name=account_name,
            start_date=start_date,
            end_date=end_date,
            min_amount=None,
            max_amount=None,
        )

        # Calculate pagination
        skip = (page - 1) * page_size

        # Get transactions
        transactions = transaction_service.get_user_transactions(
            db, user_id, filters, skip, page_size
        )

        # Get total count for pagination
        total = transaction_service.count(db, filters={"user_id": user_id})

        return PaginatedResponse.create(
            data=transactions, total=total, page=page, page_size=page_size
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{transaction_id}", response_model=BaseResponse[TransactionResponse])
async def get_transaction(
    transaction_id: int, db: Session = Depends(get_db)
) -> BaseResponse[TransactionResponse]:
    """Get a specific transaction by ID."""
    try:
        transaction = transaction_service.get(db, transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        response_transaction = transaction_service._to_response(transaction)

        return BaseResponse(
            success=True,
            message="Transaction retrieved successfully",
            data=response_transaction,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/buy", response_model=BaseResponse[TransactionResponse])
async def create_buy_transaction(
    buy_request: BuyTransactionRequest,
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db),
) -> BaseResponse[TransactionResponse]:
    """Create a buy transaction."""
    try:
        transaction = transaction_service.create_buy_transaction(
            db, user_id, buy_request
        )
        return BaseResponse(
            success=True,
            message="Buy transaction created successfully",
            data=transaction,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/sell", response_model=BaseResponse[TransactionResponse])
async def create_sell_transaction(
    sell_request: SellTransactionRequest,
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db),
) -> BaseResponse[TransactionResponse]:
    """Create a sell transaction."""
    try:
        transaction = transaction_service.create_sell_transaction(
            db, user_id, sell_request
        )
        return BaseResponse(
            success=True,
            message="Sell transaction created successfully",
            data=transaction,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/dividend", response_model=BaseResponse[TransactionResponse])
async def create_dividend_transaction(
    dividend_request: DividendTransactionRequest,
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db),
) -> BaseResponse[TransactionResponse]:
    """Create a dividend transaction."""
    try:
        transaction = transaction_service.create_dividend_transaction(
            db, user_id, dividend_request
        )
        return BaseResponse(
            success=True,
            message="Dividend transaction created successfully",
            data=transaction,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/{transaction_id}", response_model=BaseResponse[TransactionResponse])
async def update_transaction(
    transaction_id: int,
    transaction_update: TransactionUpdate,
    db: Session = Depends(get_db),
) -> BaseResponse[TransactionResponse]:
    """Update an existing transaction."""
    try:
        transaction = transaction_service.get(db, transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        updated_transaction = transaction_service.update(
            db, db_obj=transaction, obj_in=transaction_update
        )

        response_transaction = transaction_service._to_response(updated_transaction)

        return BaseResponse(
            success=True,
            message="Transaction updated successfully",
            data=response_transaction,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/{transaction_id}", response_model=BaseResponse[Any])
async def delete_transaction(
    transaction_id: int, db: Session = Depends(get_db)
) -> BaseResponse[Any]:
    """Delete a transaction and update related position."""
    try:
        success = transaction_service.delete_transaction(db, transaction_id)
        if not success:
            raise HTTPException(status_code=404, detail="Transaction not found")

        return BaseResponse(
            success=True,
            message="Transaction deleted successfully",
            data=None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/position/{position_id}", response_model=BaseResponse[list[TransactionResponse]]
)
async def get_position_transactions(
    position_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> BaseResponse[list[TransactionResponse]]:
    """Get all transactions for a specific position."""
    try:
        skip = (page - 1) * page_size
        transactions = transaction_service.get_position_transactions(
            db, position_id, skip, page_size
        )

        return BaseResponse(
            success=True,
            message="Position transactions retrieved successfully",
            data=transactions,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/performance/{user_id}", response_model=BaseResponse[TransactionPerformanceMetrics]
)
async def get_transaction_performance(
    user_id: int,
    asset_id: int | None = Query(None, description="Filter by specific asset"),
    db: Session = Depends(get_db),
) -> BaseResponse[TransactionPerformanceMetrics]:
    """Get transaction performance metrics for a user."""
    try:
        performance = transaction_service.get_transaction_performance(
            db, user_id, asset_id
        )

        return BaseResponse(
            success=True,
            message="Transaction performance metrics retrieved successfully",
            data=performance,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/summary/{user_id}/{year}/{month}", response_model=BaseResponse[dict[str, Any]]
)
async def get_monthly_summary(
    user_id: int,
    year: int,
    month: int,
    db: Session = Depends(get_db),
) -> BaseResponse[dict[str, Any]]:
    """Get monthly transaction summary."""
    try:
        # Validate year and month
        if not (2000 <= year <= 2100):
            raise HTTPException(
                status_code=400, detail="Year must be between 2000 and 2100"
            )
        if not (1 <= month <= 12):
            raise HTTPException(
                status_code=400, detail="Month must be between 1 and 12"
            )

        summary = transaction_service.get_monthly_transaction_summary(
            db, user_id, year, month
        )

        return BaseResponse(
            success=True,
            message="Monthly transaction summary retrieved successfully",
            data=summary,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/date-range/{user_id}", response_model=BaseResponse[list[TransactionResponse]]
)
async def get_transactions_by_date_range(
    user_id: int,
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    transaction_type: str
    | None = Query(None, description="Filter by transaction type"),
    db: Session = Depends(get_db),
) -> BaseResponse[list[TransactionResponse]]:
    """Get transactions within a specific date range."""
    try:
        from backend.models.transaction import TransactionType

        parsed_transaction_type = None
        if transaction_type:
            try:
                parsed_transaction_type = TransactionType(transaction_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid transaction type: {transaction_type}",
                )

        transactions = transaction_service.get_transactions_by_date_range(
            db, user_id, start_date, end_date, parsed_transaction_type
        )

        return BaseResponse(
            success=True,
            message="Transactions retrieved successfully",
            data=transactions,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
