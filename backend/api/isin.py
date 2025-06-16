"""ISIN (International Securities Identification Number) API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from backend.database import get_db_session
from backend.models.isin import ISINTickerMapping
from backend.schemas.isin import (
    ISINImportRequest,
    ISINImportResponse,
    ISINLookupRequest,
    ISINLookupResponse,
    ISINMappingCreate,
    ISINMappingResponse,
    ISINMappingSearchParams,
    ISINMappingUpdate,
    ISINResolutionRequest,
    ISINResolutionResponse,
    ISINStatistics,
    ISINSuggestionRequest,
    ISINSuggestionResponse,
    ISINValidationRequest,
    ISINValidationResponse,
    TickerSuggestion,
)
from backend.services.isin_utils import ISINUtils, isin_service
from backend.services.market_data import market_data_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/isin", tags=["ISIN"])


@router.post("/validate", response_model=ISINValidationResponse)
async def validate_isin(
    request: ISINValidationRequest, db: Session = Depends(get_db_session)
) -> ISINValidationResponse:
    """Validate an ISIN code.

    This endpoint validates the format and checksum of an ISIN code
    and returns detailed information about the ISIN structure.
    """
    try:
        isin_info = ISINUtils.parse_isin(request.isin)

        return ISINValidationResponse(
            isin=request.isin,
            is_valid=isin_info.is_valid,
            country_code=isin_info.country_code if isin_info.is_valid else None,
            country_name=isin_info.country_name if isin_info.is_valid else None,
            national_code=isin_info.national_code if isin_info.is_valid else None,
            check_digit=isin_info.check_digit if isin_info.is_valid else None,
            validation_error=isin_info.validation_error,
        )
    except Exception as e:
        logger.error(f"Error validating ISIN {request.isin}: {e}")
        raise HTTPException(status_code=500, detail=f"Validation error: {e!s}")


@router.post("/resolve", response_model=ISINResolutionResponse)
async def resolve_identifier(
    request: ISINResolutionRequest, db: Session = Depends(get_db_session)
) -> ISINResolutionResponse:
    """Resolve an identifier (ISIN or ticker) to get comprehensive asset information.

    This endpoint can handle both ISIN codes and ticker symbols, automatically
    detecting the type and providing appropriate resolution.
    """
    try:
        asset_info = isin_service.get_asset_info(db, request.identifier)

        response = ISINResolutionResponse(
            original_identifier=asset_info["original_identifier"],
            resolved_ticker=asset_info.get("resolved_ticker"),
            identifier_type=asset_info.get("identifier_type", "unknown"),
            success=asset_info["success"],
            error=asset_info.get("error"),
        )

        # Add ISIN-specific information if available
        if asset_info.get("isin"):
            response.isin = asset_info["isin"]
            response.country_code = asset_info.get("country_code")
            response.country_name = asset_info.get("country_name")
            response.national_code = asset_info.get("national_code")
            response.check_digit = asset_info.get("check_digit")

        # Add available tickers if found
        if asset_info.get("available_tickers"):
            response.available_tickers = asset_info["available_tickers"]

        return response

    except Exception as e:
        logger.error(f"Error resolving identifier {request.identifier}: {e}")
        raise HTTPException(status_code=500, detail=f"Resolution error: {e!s}")


@router.post("/lookup", response_model=ISINLookupResponse)
async def lookup_isins(
    request: ISINLookupRequest, db: Session = Depends(get_db_session)
) -> ISINLookupResponse:
    """Bulk lookup of ISIN codes to find their ticker mappings.

    This endpoint allows efficient bulk lookup of multiple ISIN codes
    and returns all available ticker mappings for each.
    """
    try:
        from backend.schemas.isin import ISINLookupResult, TickerInfo

        results = []
        total_found = 0
        total_failed = 0

        for isin in request.isins:
            try:
                # Get mappings for this ISIN
                mappings = isin_service.mapping_service.get_mappings_from_db(
                    db=db, isin=isin, active_only=not request.include_inactive
                )

                if mappings:
                    ticker_infos = [
                        TickerInfo(
                            ticker=mapping.ticker,
                            exchange_code=mapping.exchange_code,
                            exchange_name=mapping.exchange_name,
                            currency=mapping.currency,
                            confidence=mapping.confidence,
                            source=mapping.source,
                        )
                        for mapping in mappings
                    ]

                    results.append(
                        ISINLookupResult(isin=isin, success=True, tickers=ticker_infos)
                    )
                    total_found += 1
                else:
                    results.append(
                        ISINLookupResult(
                            isin=isin,
                            success=False,
                            tickers=[],
                            error="No ticker mappings found",
                        )
                    )
                    total_failed += 1

            except Exception as e:
                results.append(
                    ISINLookupResult(isin=isin, success=False, tickers=[], error=str(e))
                )
                total_failed += 1

        return ISINLookupResponse(
            results=results,
            total_requested=len(request.isins),
            total_found=total_found,
            total_failed=total_failed,
        )

    except Exception as e:
        logger.error(f"Error in bulk ISIN lookup: {e}")
        raise HTTPException(status_code=500, detail=f"Lookup error: {e!s}")


@router.post("/suggest", response_model=ISINSuggestionResponse)
async def suggest_ticker_formats(
    request: ISINSuggestionRequest, db: Session = Depends(get_db_session)
) -> ISINSuggestionResponse:
    """Get suggested ticker formats based on ISIN country information.

    This endpoint provides intelligent ticker format suggestions based on
    the country information embedded in the ISIN code.
    """
    try:
        # Parse ISIN to get country information
        isin_info = ISINUtils.parse_isin(request.isin)

        if not isin_info.is_valid:
            raise HTTPException(
                status_code=400, detail=f"Invalid ISIN: {isin_info.validation_error}"
            )

        # Get suggested ticker formats
        suggested_formats = ISINUtils.suggest_ticker_formats(
            request.isin, request.base_ticker
        )

        # Convert to response format
        suggestions = []

        for ticker_format in suggested_formats:
            if ticker_format == request.base_ticker:
                # Base ticker (usually US)
                suggestions.append(
                    TickerSuggestion(
                        ticker=ticker_format,
                        exchange_name="US Exchanges (NYSE/NASDAQ)",
                        country_code="US",
                        reason="Base ticker format (US markets)",
                    )
                )
            elif "." in ticker_format:
                # Exchange-specific format
                base, suffix = ticker_format.split(".", 1)
                exchange_info = {
                    "DE": "Frankfurt/XETRA",
                    "L": "London Stock Exchange",
                    "PA": "Euronext Paris",
                    "MI": "Milan",
                    "AS": "Amsterdam",
                    "F": "Frankfurt",
                    "BE": "Berlin",
                    "DU": "Düsseldorf",
                    "HM": "Hamburg",
                    "MU": "Munich",
                    "SG": "Stuttgart",
                    "SW": "Swiss Exchange",
                    "TO": "Toronto",
                    "AX": "Australia",
                    "T": "Tokyo",
                    "HK": "Hong Kong",
                }

                exchange_name = exchange_info.get(suffix, f"Exchange (.{suffix})")
                suggestions.append(
                    TickerSuggestion(
                        ticker=ticker_format,
                        exchange_name=exchange_name,
                        country_code=isin_info.country_code,
                        reason=f"Country-specific format for {isin_info.country_name}",
                    )
                )

        return ISINSuggestionResponse(
            isin=request.isin,
            base_ticker=request.base_ticker,
            country_code=isin_info.country_code,
            country_name=isin_info.country_name,
            suggestions=suggestions,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating suggestions for ISIN {request.isin}: {e}")
        raise HTTPException(status_code=500, detail=f"Suggestion error: {e!s}")


@router.get("/mappings", response_model=list[ISINMappingResponse])
async def get_mappings(
    params: ISINMappingSearchParams = Depends(),
    db: Session = Depends(get_db_session),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
) -> list[ISINMappingResponse]:
    """Search and retrieve ISIN ticker mappings.

    This endpoint allows searching for ISIN mappings with various filters
    and returns paginated results.
    """
    try:
        query = db.query(ISINTickerMapping)

        # Apply filters
        if params.isin:
            query = query.filter(ISINTickerMapping.isin == params.isin.upper())
        if params.ticker:
            query = query.filter(ISINTickerMapping.ticker == params.ticker.upper())
        if params.exchange_code:
            query = query.filter(
                ISINTickerMapping.exchange_code == params.exchange_code.upper()
            )
        if params.source:
            query = query.filter(ISINTickerMapping.source == params.source)
        if params.min_confidence is not None:
            query = query.filter(ISINTickerMapping.confidence >= params.min_confidence)

        query = query.filter(ISINTickerMapping.is_active == params.is_active)

        # Order by confidence (highest first) and creation date (newest first)
        query = query.order_by(
            ISINTickerMapping.confidence.desc(), ISINTickerMapping.created_at.desc()
        )

        # Apply pagination
        mappings = query.offset(skip).limit(limit).all()

        return [
            ISINMappingResponse(
                id=mapping.id,
                isin=mapping.isin,
                ticker=mapping.ticker,
                exchange_code=mapping.exchange_code,
                exchange_name=mapping.exchange_name,
                security_name=mapping.security_name,
                currency=mapping.currency,
                source=mapping.source,
                confidence=mapping.confidence,
                is_active=mapping.is_active,
                created_at=mapping.created_at,
                updated_at=mapping.last_updated,
                last_updated=mapping.last_updated,
            )
            for mapping in mappings
        ]

    except Exception as e:
        logger.error(f"Error retrieving ISIN mappings: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval error: {e!s}")


@router.post("/mappings", response_model=ISINMappingResponse)
async def create_mapping(
    mapping: ISINMappingCreate, db: Session = Depends(get_db_session)
) -> ISINMappingResponse:
    """Create a new ISIN ticker mapping.

    This endpoint allows manual creation of ISIN to ticker mappings,
    useful for adding custom or missing mappings.
    """
    try:
        # Validate ISIN
        is_valid, error = ISINUtils.validate_isin(mapping.isin)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid ISIN: {error}")

        # Check if mapping already exists
        existing = (
            db.query(ISINTickerMapping)
            .filter(
                and_(
                    ISINTickerMapping.isin == mapping.isin,
                    ISINTickerMapping.ticker == mapping.ticker,
                    ISINTickerMapping.exchange_code == mapping.exchange_code,
                )
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Mapping already exists for this ISIN, ticker, and exchange combination",
            )

        # Create new mapping
        new_mapping = ISINTickerMapping(
            isin=mapping.isin,
            ticker=mapping.ticker,
            exchange_code=mapping.exchange_code,
            exchange_name=mapping.exchange_name,
            security_name=mapping.security_name,
            currency=mapping.currency,
            source=mapping.source,
            confidence=mapping.confidence,
        )

        db.add(new_mapping)
        db.commit()
        db.refresh(new_mapping)

        logger.info(f"Created ISIN mapping: {mapping.isin} -> {mapping.ticker}")

        return ISINMappingResponse(
            id=new_mapping.id,
            isin=new_mapping.isin,
            ticker=new_mapping.ticker,
            exchange_code=new_mapping.exchange_code,
            exchange_name=new_mapping.exchange_name,
            security_name=new_mapping.security_name,
            currency=new_mapping.currency,
            source=new_mapping.source,
            confidence=new_mapping.confidence,
            is_active=new_mapping.is_active,
            created_at=new_mapping.created_at,
            updated_at=new_mapping.last_updated,
            last_updated=new_mapping.last_updated,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ISIN mapping: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Creation error: {e!s}")


@router.put("/mappings/{mapping_id}", response_model=ISINMappingResponse)
async def update_mapping(
    mapping_id: int,
    update_data: ISINMappingUpdate,
    db: Session = Depends(get_db_session),
) -> ISINMappingResponse:
    """Update an existing ISIN ticker mapping.

    This endpoint allows updating specific fields of an existing
    ISIN to ticker mapping.
    """
    try:
        # Get existing mapping
        mapping = (
            db.query(ISINTickerMapping)
            .filter(ISINTickerMapping.id == mapping_id)
            .first()
        )

        if not mapping:
            raise HTTPException(status_code=404, detail="ISIN mapping not found")

        # Update fields
        if update_data.exchange_code is not None:
            mapping.exchange_code = update_data.exchange_code
        if update_data.exchange_name is not None:
            mapping.exchange_name = update_data.exchange_name
        if update_data.security_name is not None:
            mapping.security_name = update_data.security_name
        if update_data.currency is not None:
            mapping.currency = update_data.currency
        if update_data.source is not None:
            mapping.source = update_data.source
        if update_data.confidence is not None:
            mapping.confidence = update_data.confidence
        if update_data.is_active is not None:
            mapping.is_active = update_data.is_active

        db.commit()
        db.refresh(mapping)

        logger.info(
            f"Updated ISIN mapping {mapping_id}: {mapping.isin} -> {mapping.ticker}"
        )

        return ISINMappingResponse(
            id=mapping.id,
            isin=mapping.isin,
            ticker=mapping.ticker,
            exchange_code=mapping.exchange_code,
            exchange_name=mapping.exchange_name,
            security_name=mapping.security_name,
            currency=mapping.currency,
            source=mapping.source,
            confidence=mapping.confidence,
            is_active=mapping.is_active,
            created_at=mapping.created_at,
            updated_at=mapping.last_updated,
            last_updated=mapping.last_updated,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ISIN mapping {mapping_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Update error: {e!s}")


@router.delete("/mappings/{mapping_id}")
async def delete_mapping(
    mapping_id: int, db: Session = Depends(get_db_session)
) -> dict:
    """Delete an ISIN ticker mapping.

    This endpoint soft-deletes an ISIN mapping by setting it as inactive
    rather than removing it from the database.
    """
    try:
        # Get existing mapping
        mapping = (
            db.query(ISINTickerMapping)
            .filter(ISINTickerMapping.id == mapping_id)
            .first()
        )

        if not mapping:
            raise HTTPException(status_code=404, detail="ISIN mapping not found")

        # Soft delete by setting inactive
        mapping.is_active = False
        db.commit()

        logger.info(
            f"Deleted ISIN mapping {mapping_id}: {mapping.isin} -> {mapping.ticker}"
        )

        return {"message": "ISIN mapping deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting ISIN mapping {mapping_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Deletion error: {e!s}")


@router.get("/statistics", response_model=ISINStatistics)
async def get_statistics(db: Session = Depends(get_db_session)) -> ISINStatistics:
    """Get statistics about ISIN mappings in the system.

    This endpoint provides comprehensive statistics about the ISIN
    mappings database, including coverage and data source information.
    """
    try:
        # Basic counts
        total_mappings = db.query(ISINTickerMapping).count()
        active_mappings = (
            db.query(ISINTickerMapping).filter(ISINTickerMapping.is_active).count()
        )

        unique_isins = db.query(
            func.count(func.distinct(ISINTickerMapping.isin))
        ).scalar()
        unique_tickers = db.query(
            func.count(func.distinct(ISINTickerMapping.ticker))
        ).scalar()

        # Country statistics (from ISIN country codes)
        country_stats = (
            db.query(
                func.substr(ISINTickerMapping.isin, 1, 2).label("country"),
                func.count().label("count"),
            )
            .filter(ISINTickerMapping.is_active)
            .group_by(func.substr(ISINTickerMapping.isin, 1, 2))
            .order_by(desc("count"))
            .limit(10)
            .all()
        )

        # Exchange statistics
        exchange_stats = (
            db.query(ISINTickerMapping.exchange_code, func.count().label("count"))
            .filter(
                and_(
                    ISINTickerMapping.is_active,
                    ISINTickerMapping.exchange_code.isnot(None),
                )
            )
            .group_by(ISINTickerMapping.exchange_code)
            .order_by(desc("count"))
            .limit(10)
            .all()
        )

        # Data source statistics
        source_stats = (
            db.query(ISINTickerMapping.source, func.count().label("count"))
            .filter(ISINTickerMapping.is_active)
            .group_by(ISINTickerMapping.source)
            .order_by(desc("count"))
            .all()
        )

        # Get last update time
        last_updated = db.query(func.max(ISINTickerMapping.last_updated)).scalar()

        return ISINStatistics(
            total_mappings=total_mappings,
            active_mappings=active_mappings,
            unique_isins=unique_isins,
            unique_tickers=unique_tickers,
            countries_covered=len(country_stats),
            exchanges_covered=len(exchange_stats),
            top_countries=[
                {"country": stat.country, "count": stat.count} for stat in country_stats
            ],
            top_exchanges=[
                {"exchange": stat.exchange_code, "count": stat.count}
                for stat in exchange_stats
            ],
            data_sources=[
                {"source": stat.source, "count": stat.count} for stat in source_stats
            ],
            last_updated=last_updated,
        )

    except Exception as e:
        logger.error(f"Error generating ISIN statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Statistics error: {e!s}")


@router.post("/import", response_model=ISINImportResponse)
async def import_mappings(
    request: ISINImportRequest, db: Session = Depends(get_db_session)
) -> ISINImportResponse:
    """Import ISIN mappings in bulk.

    This endpoint allows bulk import of ISIN to ticker mappings,
    with options for dry-run validation and updating existing mappings.
    """
    try:
        from backend.schemas.isin import ISINImportResult

        results = []
        total_created = 0
        total_updated = 0
        total_skipped = 0
        total_errors = 0

        for mapping_data in request.mappings:
            try:
                # Validate ISIN
                is_valid, error = ISINUtils.validate_isin(mapping_data.isin)
                if not is_valid:
                    results.append(
                        ISINImportResult(
                            isin=mapping_data.isin,
                            ticker=mapping_data.ticker,
                            status="error",
                            error=f"Invalid ISIN: {error}",
                        )
                    )
                    total_errors += 1
                    continue

                # Check if mapping exists
                existing = (
                    db.query(ISINTickerMapping)
                    .filter(
                        and_(
                            ISINTickerMapping.isin == mapping_data.isin,
                            ISINTickerMapping.ticker == mapping_data.ticker,
                            ISINTickerMapping.exchange_code
                            == mapping_data.exchange_code,
                        )
                    )
                    .first()
                )

                if existing:
                    if request.update_existing and not request.dry_run:
                        # Update existing mapping
                        existing.exchange_name = mapping_data.exchange_name
                        existing.security_name = mapping_data.security_name
                        existing.currency = mapping_data.currency
                        existing.source = mapping_data.source
                        existing.confidence = mapping_data.confidence
                        existing.is_active = True

                        results.append(
                            ISINImportResult(
                                isin=mapping_data.isin,
                                ticker=mapping_data.ticker,
                                status="updated",
                            )
                        )
                        total_updated += 1
                    else:
                        results.append(
                            ISINImportResult(
                                isin=mapping_data.isin,
                                ticker=mapping_data.ticker,
                                status="skipped",
                                error="Mapping already exists",
                            )
                        )
                        total_skipped += 1
                else:
                    if not request.dry_run:
                        # Create new mapping
                        new_mapping = ISINTickerMapping(
                            isin=mapping_data.isin,
                            ticker=mapping_data.ticker,
                            exchange_code=mapping_data.exchange_code,
                            exchange_name=mapping_data.exchange_name,
                            security_name=mapping_data.security_name,
                            currency=mapping_data.currency,
                            source=mapping_data.source,
                            confidence=mapping_data.confidence,
                        )
                        db.add(new_mapping)

                    results.append(
                        ISINImportResult(
                            isin=mapping_data.isin,
                            ticker=mapping_data.ticker,
                            status="created",
                        )
                    )
                    total_created += 1

            except Exception as e:
                results.append(
                    ISINImportResult(
                        isin=mapping_data.isin,
                        ticker=mapping_data.ticker,
                        status="error",
                        error=str(e),
                    )
                )
                total_errors += 1

        if not request.dry_run:
            db.commit()
            logger.info(
                f"Imported ISIN mappings: {total_created} created, {total_updated} updated"
            )
        else:
            logger.info(
                f"Dry run import validation: {total_created} would be created, {total_updated} would be updated"
            )

        return ISINImportResponse(
            results=results,
            total_requested=len(request.mappings),
            total_created=total_created,
            total_updated=total_updated,
            total_skipped=total_skipped,
            total_errors=total_errors,
            dry_run=request.dry_run,
        )

    except Exception as e:
        logger.error(f"Error importing ISIN mappings: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Import error: {e!s}")


@router.get("/quote/{identifier}")
async def get_quote_by_identifier(
    identifier: str, db: Session = Depends(get_db_session)
) -> dict:
    """Get market data quote by identifier (ISIN or ticker).

    This endpoint fetches real-time market data for a security
    identified by either its ISIN code or ticker symbol.
    """
    try:
        # Use the market data service with ISIN support
        result = market_data_service.fetch_quote(identifier, db)

        if result.success:
            return {
                "identifier": identifier,
                "ticker": result.ticker,
                "current_price": (
                    float(result.current_price) if result.current_price else None
                ),
                "day_change": float(result.day_change) if result.day_change else None,
                "day_change_percent": (
                    float(result.day_change_percent)
                    if result.day_change_percent
                    else None
                ),
                "volume": result.volume,
                "data_source": result.data_source,
                "success": True,
            }
        raise HTTPException(
            status_code=404,
            detail={
                "identifier": identifier,
                "error": result.error,
                "suggestions": getattr(result, "suggestions", []),
                "success": False,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quote for identifier {identifier}: {e}")
        raise HTTPException(status_code=500, detail=f"Quote error: {e!s}")
