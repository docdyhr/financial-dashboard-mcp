"""Assets API router for asset management and price data."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.models import Asset, get_db
from backend.schemas.asset import (
    AssetCreate,
    AssetPriceUpdate,
    AssetResponse,
    AssetSummary,
    AssetUpdate,
    BulkAssetPriceUpdate,
)
from backend.schemas.base import BaseResponse, PaginatedResponse
from backend.services.base import BaseService

router = APIRouter()
asset_service = BaseService(Asset)


@router.get("/", response_model=PaginatedResponse[AssetResponse])
async def get_assets(
    query: str | None = Query(None, description="Search query (ticker or name)"),
    asset_type: str | None = Query(None, description="Filter by asset type"),
    category: str | None = Query(None, description="Filter by category"),
    sector: str | None = Query(None, description="Filter by sector"),
    exchange: str | None = Query(None, description="Filter by exchange"),
    currency: str | None = Query(None, description="Filter by currency"),
    is_active: bool = Query(True, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """Get assets with optional search and filtering."""
    try:
        skip = (page - 1) * page_size

        # Build filters
        filters = {"is_active": is_active}
        if asset_type:
            filters["asset_type"] = asset_type
        if category:
            filters["category"] = category
        if sector:
            filters["sector"] = sector
        if exchange:
            filters["exchange"] = exchange
        if currency:
            filters["currency"] = currency.upper()

        # Get assets
        if query:
            # Use search functionality
            assets = asset_service.search(
                db,
                search_term=query,
                search_fields=["ticker", "name"],
                skip=skip,
                limit=page_size,
            )
            # Apply additional filters manually for search results
            if filters:
                assets = [
                    a
                    for a in assets
                    if all(
                        getattr(a, field) == value
                        for field, value in filters.items()
                        if hasattr(a, field)
                    )
                ]
            total = len(assets)
        else:
            assets = asset_service.get_multi(
                db, skip=skip, limit=page_size, filters=filters
            )
            total = asset_service.count(db, filters=filters)

        # Convert to response format
        asset_responses = [
            AssetResponse(
                id=asset.id,
                ticker=asset.ticker,
                name=asset.name,
                description=asset.description,
                asset_type=asset.asset_type,
                category=asset.category,
                sector=asset.sector,
                industry=asset.industry,
                exchange=asset.exchange,
                currency=asset.currency,
                country=asset.country,
                current_price=asset.current_price,
                previous_close=asset.previous_close,
                day_change=asset.day_change,
                day_change_percent=asset.day_change_percent,
                market_cap=asset.market_cap,
                pe_ratio=asset.pe_ratio,
                dividend_yield=asset.dividend_yield,
                is_active=asset.is_active,
                data_source=asset.data_source,
                created_at=asset.created_at,
                updated_at=asset.updated_at,
            )
            for asset in assets
        ]

        return PaginatedResponse.create(
            data=asset_responses, total=total, page=page, page_size=page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{asset_id}", response_model=BaseResponse[AssetResponse])
async def get_asset(asset_id: int, db: Session = Depends(get_db)):
    """Get a specific asset by ID."""
    try:
        asset = asset_service.get(db, asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        asset_response = AssetResponse(
            id=asset.id,
            ticker=asset.ticker,
            name=asset.name,
            description=asset.description,
            asset_type=asset.asset_type,
            category=asset.category,
            sector=asset.sector,
            industry=asset.industry,
            exchange=asset.exchange,
            currency=asset.currency,
            country=asset.country,
            current_price=asset.current_price,
            previous_close=asset.previous_close,
            day_change=asset.day_change,
            day_change_percent=asset.day_change_percent,
            market_cap=asset.market_cap,
            pe_ratio=asset.pe_ratio,
            dividend_yield=asset.dividend_yield,
            is_active=asset.is_active,
            data_source=asset.data_source,
            created_at=asset.created_at,
            updated_at=asset.updated_at,
        )

        return BaseResponse(
            success=True, message="Asset retrieved successfully", data=asset_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ticker/{ticker}", response_model=BaseResponse[AssetResponse])
async def get_asset_by_ticker(ticker: str, db: Session = Depends(get_db)):
    """Get a specific asset by ticker symbol."""
    try:
        asset = asset_service.get_by_field(db, "ticker", ticker.upper())
        if not asset:
            raise HTTPException(
                status_code=404, detail=f"Asset with ticker '{ticker}' not found"
            )

        asset_response = AssetResponse(
            id=asset.id,
            ticker=asset.ticker,
            name=asset.name,
            description=asset.description,
            asset_type=asset.asset_type,
            category=asset.category,
            sector=asset.sector,
            industry=asset.industry,
            exchange=asset.exchange,
            currency=asset.currency,
            country=asset.country,
            current_price=asset.current_price,
            previous_close=asset.previous_close,
            day_change=asset.day_change,
            day_change_percent=asset.day_change_percent,
            market_cap=asset.market_cap,
            pe_ratio=asset.pe_ratio,
            dividend_yield=asset.dividend_yield,
            is_active=asset.is_active,
            data_source=asset.data_source,
            created_at=asset.created_at,
            updated_at=asset.updated_at,
        )

        return BaseResponse(
            success=True, message="Asset retrieved successfully", data=asset_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=BaseResponse[AssetResponse])
async def create_asset(asset_create: AssetCreate, db: Session = Depends(get_db)):
    """Create a new asset."""
    try:
        # Check if asset with ticker already exists
        existing_asset = asset_service.get_by_field(db, "ticker", asset_create.ticker)
        if existing_asset:
            raise HTTPException(
                status_code=400,
                detail=f"Asset with ticker '{asset_create.ticker}' already exists",
            )

        asset = asset_service.create(db, obj_in=asset_create)

        asset_response = AssetResponse(
            id=asset.id,
            ticker=asset.ticker,
            name=asset.name,
            description=asset.description,
            asset_type=asset.asset_type,
            category=asset.category,
            sector=asset.sector,
            industry=asset.industry,
            exchange=asset.exchange,
            currency=asset.currency,
            country=asset.country,
            current_price=asset.current_price,
            previous_close=asset.previous_close,
            day_change=asset.day_change,
            day_change_percent=asset.day_change_percent,
            market_cap=asset.market_cap,
            pe_ratio=asset.pe_ratio,
            dividend_yield=asset.dividend_yield,
            is_active=asset.is_active,
            data_source=asset.data_source,
            created_at=asset.created_at,
            updated_at=asset.updated_at,
        )

        return BaseResponse(
            success=True, message="Asset created successfully", data=asset_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{asset_id}", response_model=BaseResponse[AssetResponse])
async def update_asset(
    asset_id: int, asset_update: AssetUpdate, db: Session = Depends(get_db)
):
    """Update an existing asset."""
    try:
        asset = asset_service.get(db, asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        updated_asset = asset_service.update(db, db_obj=asset, obj_in=asset_update)

        asset_response = AssetResponse(
            id=updated_asset.id,
            ticker=updated_asset.ticker,
            name=updated_asset.name,
            description=updated_asset.description,
            asset_type=updated_asset.asset_type,
            category=updated_asset.category,
            sector=updated_asset.sector,
            industry=updated_asset.industry,
            exchange=updated_asset.exchange,
            currency=updated_asset.currency,
            country=updated_asset.country,
            current_price=updated_asset.current_price,
            previous_close=updated_asset.previous_close,
            day_change=updated_asset.day_change,
            day_change_percent=updated_asset.day_change_percent,
            market_cap=updated_asset.market_cap,
            pe_ratio=updated_asset.pe_ratio,
            dividend_yield=updated_asset.dividend_yield,
            is_active=updated_asset.is_active,
            data_source=updated_asset.data_source,
            created_at=updated_asset.created_at,
            updated_at=updated_asset.updated_at,
        )

        return BaseResponse(
            success=True, message="Asset updated successfully", data=asset_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{asset_id}", response_model=BaseResponse)
async def delete_asset(
    asset_id: int,
    soft_delete: bool = Query(
        True, description="Soft delete (mark inactive) or hard delete"
    ),
    db: Session = Depends(get_db),
):
    """Delete an asset."""
    try:
        if soft_delete:
            asset = asset_service.soft_delete(db, id=asset_id)
        else:
            asset = asset_service.delete(db, id=asset_id)

        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        return BaseResponse(
            success=True,
            message="Asset deleted successfully",
            data={"asset_id": asset_id},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{asset_id}/price", response_model=BaseResponse)
async def update_asset_price(
    asset_id: int, price_update: AssetPriceUpdate, db: Session = Depends(get_db)
):
    """Update asset price data."""
    try:
        asset = asset_service.get(db, asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        # Update price fields
        update_data = {
            "current_price": price_update.current_price,
            "data_source": price_update.data_source,
        }

        if price_update.previous_close:
            update_data["previous_close"] = price_update.previous_close
            update_data["day_change"] = price_update.day_change
            update_data["day_change_percent"] = price_update.day_change_percent

        updated_asset = asset_service.update(db, db_obj=asset, obj_in=update_data)

        return BaseResponse(
            success=True,
            message="Asset price updated successfully",
            data={
                "asset_id": updated_asset.id,
                "ticker": updated_asset.ticker,
                "current_price": updated_asset.current_price,
                "day_change": updated_asset.day_change,
                "day_change_percent": updated_asset.day_change_percent,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prices/bulk-update", response_model=BaseResponse)
async def bulk_update_asset_prices(
    bulk_update: BulkAssetPriceUpdate, db: Session = Depends(get_db)
):
    """Bulk update asset prices."""
    try:
        updated_count = 0
        errors = []

        for update_item in bulk_update.updates:
            try:
                ticker = update_item.get("ticker")
                current_price = update_item.get("current_price")
                previous_close = update_item.get("previous_close")

                if not ticker or current_price is None:
                    errors.append(
                        f"Missing ticker or current_price for item: {update_item}"
                    )
                    continue

                asset = asset_service.get_by_field(db, "ticker", ticker.upper())
                if not asset:
                    errors.append(f"Asset not found for ticker: {ticker}")
                    continue

                # Calculate day change if previous close provided
                day_change = None
                day_change_percent = None
                if previous_close:
                    day_change = float(current_price) - float(previous_close)
                    day_change_percent = (
                        (day_change / float(previous_close)) * 100
                        if previous_close > 0
                        else 0
                    )

                update_data = {
                    "current_price": current_price,
                    "previous_close": previous_close,
                    "day_change": day_change,
                    "day_change_percent": day_change_percent,
                    "data_source": bulk_update.data_source,
                }

                asset_service.update(db, db_obj=asset, obj_in=update_data)
                updated_count += 1

            except Exception as e:
                errors.append(f"Error updating {ticker}: {e!s}")

        return BaseResponse(
            success=True,
            message=f"Bulk price update completed. Updated {updated_count} assets.",
            data={
                "updated_count": updated_count,
                "total_items": len(bulk_update.updates),
                "errors": errors,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/price/{ticker}", response_model=BaseResponse)
async def get_asset_price(ticker: str, db: Session = Depends(get_db)):
    """Get current price for a specific asset."""
    try:
        asset = asset_service.get_by_field(db, "ticker", ticker.upper())
        if not asset:
            raise HTTPException(
                status_code=404, detail=f"Asset with ticker '{ticker}' not found"
            )

        return BaseResponse(
            success=True,
            message="Asset price retrieved successfully",
            data={
                "ticker": asset.ticker,
                "name": asset.name,
                "current_price": asset.current_price,
                "previous_close": asset.previous_close,
                "day_change": asset.day_change,
                "day_change_percent": asset.day_change_percent,
                "currency": asset.currency,
                "last_updated": asset.updated_at,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/tickers", response_model=BaseResponse[list[AssetSummary]])
async def search_asset_tickers(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: Session = Depends(get_db),
):
    """Search for assets by ticker or name (for autocomplete)."""
    try:
        assets = asset_service.search(
            db, search_term=query, search_fields=["ticker", "name"], skip=0, limit=limit
        )

        # Convert to summary format
        asset_summaries = [
            AssetSummary(
                id=asset.id,
                ticker=asset.ticker,
                name=asset.name,
                asset_type=asset.asset_type,
                category=asset.category,
                current_price=asset.current_price,
                currency=asset.currency,
                is_active=asset.is_active,
            )
            for asset in assets
            if asset.is_active
        ]

        return BaseResponse(
            success=True,
            message="Asset search completed successfully",
            data=asset_summaries,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
