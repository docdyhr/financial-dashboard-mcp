"""API endpoints for ISIN sync service management."""

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db_session
from backend.services.isin_sync_service import ConflictResolution, get_isin_sync_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/isin/sync", tags=["ISIN Sync"])


class SyncJobRequest(BaseModel):
    """Request model for creating sync jobs."""

    isins: list[str] = Field(..., description="List of ISINs to sync")
    source: str = Field(default="manual", description="Data source for sync")
    priority: str = Field(
        default="normal", description="Job priority (low, normal, high)"
    )


class ConflictResolutionRequest(BaseModel):
    """Request model for resolving conflicts."""

    isin: str = Field(..., description="ISIN with conflict")
    resolution: str = Field(..., description="Resolution strategy")
    reason: str | None = Field(None, description="Reason for resolution")


class BulkSyncRequest(BaseModel):
    """Request model for bulk sync operations."""

    country_codes: list[str] | None = Field(None, description="Country codes to sync")
    exchanges: list[str] | None = Field(None, description="Exchange codes to sync")
    max_isins: int = Field(default=1000, description="Maximum ISINs to sync")
    source: str = Field(default="bulk_sync", description="Source identifier")


@router.get("/status")
async def get_sync_status() -> dict[str, Any]:
    """Get overall sync service status and statistics.

    Returns comprehensive information about the sync service including
    running jobs, conflicts, and performance metrics.
    """
    try:
        sync_service = get_isin_sync_service()
        stats = sync_service.get_sync_statistics()

        return {
            "success": True,
            "data": stats,
            "message": "Sync service status retrieved successfully",
        }

    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs", response_model=dict[str, Any])
async def create_sync_job(
    request: SyncJobRequest, background_tasks: BackgroundTasks
) -> dict[str, Any]:
    """Create a new ISIN sync job.

    This endpoint queues a new synchronization job for the specified ISINs.
    The job will be processed asynchronously in the background.
    """
    try:
        # Validate ISINs
        if not request.isins:
            raise HTTPException(
                status_code=400, detail="At least one ISIN must be provided"
            )

        if len(request.isins) > 500:
            raise HTTPException(status_code=400, detail="Maximum 500 ISINs per job")

        # Validate ISIN format
        invalid_isins = []
        for isin in request.isins:
            if not isin or len(isin) != 12:
                invalid_isins.append(isin)

        if invalid_isins:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid ISIN format: {', '.join(invalid_isins[:5])}",
            )

        # Queue the job
        sync_service = get_isin_sync_service()
        job_id = await sync_service.queue_sync_job(request.isins, request.source)

        return {
            "success": True,
            "data": {
                "job_id": job_id,
                "status": "queued",
                "isin_count": len(request.isins),
                "source": request.source,
            },
            "message": f"Sync job {job_id} created successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating sync job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str) -> dict[str, Any]:
    """Get status of a specific sync job.

    Returns detailed information about job progress, results, and any errors.
    """
    try:
        sync_service = get_isin_sync_service()
        job_status = sync_service.get_job_status(job_id)

        if not job_status:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return {
            "success": True,
            "data": job_status,
            "message": f"Job {job_id} status retrieved successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def list_sync_jobs(status: str | None = None, limit: int = 50) -> dict[str, Any]:
    """List sync jobs with optional filtering.

    Args:
        status: Filter by job status (pending, running, completed, failed)
        limit: Maximum number of jobs to return
    """
    try:
        sync_service = get_isin_sync_service()

        jobs = []
        for job_id, job in sync_service.active_jobs.items():
            if status is None or job.status.value == status:
                job_info = sync_service.get_job_status(job_id)
                if job_info:
                    jobs.append(job_info)

        # Sort by creation time (newest first)
        jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return {
            "success": True,
            "data": {
                "jobs": jobs[:limit],
                "total": len(jobs),
                "filtered_by_status": status,
            },
            "message": f"Retrieved {len(jobs[:limit])} sync jobs",
        }

    except Exception as e:
        logger.error(f"Error listing sync jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conflicts")
async def get_pending_conflicts(limit: int = 50) -> dict[str, Any]:
    """Get pending conflicts that require manual resolution.

    Returns a list of mapping conflicts that couldn't be automatically resolved.
    """
    try:
        sync_service = get_isin_sync_service()
        conflicts = sync_service.get_pending_conflicts(limit)

        return {
            "success": True,
            "data": {"conflicts": conflicts, "total": len(conflicts), "limit": limit},
            "message": f"Retrieved {len(conflicts)} pending conflicts",
        }

    except Exception as e:
        logger.error(f"Error getting pending conflicts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conflicts/resolve")
async def resolve_conflict(request: ConflictResolutionRequest) -> dict[str, Any]:
    """Manually resolve a mapping conflict.

    This endpoint allows manual resolution of conflicts that couldn't be
    automatically resolved by the sync service.
    """
    try:
        # Validate resolution strategy
        valid_resolutions = ["keep_existing", "use_new", "merge"]
        if request.resolution not in valid_resolutions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid resolution. Must be one of: {', '.join(valid_resolutions)}",
            )

        # Convert string to enum
        resolution_enum = ConflictResolution(request.resolution)

        sync_service = get_isin_sync_service()
        success = await sync_service.resolve_conflict_manually(
            request.isin, resolution_enum
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"No unresolved conflicts found for ISIN {request.isin}",
            )

        return {
            "success": True,
            "data": {
                "isin": request.isin,
                "resolution": request.resolution,
                "reason": request.reason,
            },
            "message": f"Conflict for {request.isin} resolved successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving conflict for {request.isin}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk")
async def start_bulk_sync(
    request: BulkSyncRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session),
) -> dict[str, Any]:
    """Start bulk synchronization based on criteria.

    This endpoint allows syncing large numbers of ISINs based on
    country codes, exchanges, or other criteria.
    """
    try:
        from sqlalchemy import or_

        from backend.models.isin import ISINTickerMapping

        # Build query based on criteria
        query = db.query(ISINTickerMapping).filter(ISINTickerMapping.is_active)

        if request.country_codes:
            # Filter by ISIN country codes
            country_filters = [
                ISINTickerMapping.isin.like(f"{code}%")
                for code in request.country_codes
            ]
            query = query.filter(or_(*country_filters))

        if request.exchanges:
            query = query.filter(ISINTickerMapping.exchange_code.in_(request.exchanges))

        # Get ISINs to sync
        mappings = query.limit(request.max_isins).all()
        isins = [mapping.isin for mapping in mappings]

        if not isins:
            return {
                "success": True,
                "data": {
                    "job_id": None,
                    "isin_count": 0,
                    "message": "No ISINs found matching criteria",
                },
                "message": "No ISINs to sync",
            }

        # Queue the bulk sync job
        sync_service = get_isin_sync_service()
        job_id = await sync_service.queue_sync_job(isins, request.source)

        return {
            "success": True,
            "data": {
                "job_id": job_id,
                "isin_count": len(isins),
                "criteria": {
                    "country_codes": request.country_codes,
                    "exchanges": request.exchanges,
                    "max_isins": request.max_isins,
                },
                "source": request.source,
            },
            "message": f"Bulk sync job {job_id} started for {len(isins)} ISINs",
        }

    except Exception as e:
        logger.error(f"Error starting bulk sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/service/start")
async def start_sync_service() -> dict[str, Any]:
    """Start the background sync service.

    This endpoint starts the background synchronization service if it's not already running.
    """
    try:
        sync_service = get_isin_sync_service()

        if sync_service._running:
            return {
                "success": True,
                "data": {"status": "already_running"},
                "message": "Sync service is already running",
            }

        await sync_service.start_background_sync()

        return {
            "success": True,
            "data": {"status": "started"},
            "message": "Background sync service started successfully",
        }

    except Exception as e:
        logger.error(f"Error starting sync service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/service/stop")
async def stop_sync_service() -> dict[str, Any]:
    """Stop the background sync service.

    This endpoint stops the background synchronization service and waits for
    currently running jobs to complete.
    """
    try:
        sync_service = get_isin_sync_service()

        if not sync_service._running:
            return {
                "success": True,
                "data": {"status": "already_stopped"},
                "message": "Sync service is not running",
            }

        await sync_service.stop_background_sync()

        return {
            "success": True,
            "data": {"status": "stopped"},
            "message": "Background sync service stopped successfully",
        }

    except Exception as e:
        logger.error(f"Error stopping sync service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
async def cancel_sync_job(job_id: str) -> dict[str, Any]:
    """Cancel a pending or running sync job.

    This endpoint attempts to cancel a sync job. Jobs that are already
    completed cannot be cancelled.
    """
    try:
        sync_service = get_isin_sync_service()
        job = sync_service.active_jobs.get(job_id)

        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        if job.status.value in ["completed", "failed", "cancelled"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel job with status: {job.status.value}",
            )

        # Mark job as cancelled
        from backend.services.isin_sync_service import SyncStatus

        job.status = SyncStatus.CANCELLED
        job.completed_at = __import__("datetime").datetime.now()

        return {
            "success": True,
            "data": {"job_id": job_id, "status": "cancelled"},
            "message": f"Job {job_id} cancelled successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def sync_service_health() -> dict[str, Any]:
    """Get health status of the sync service.

    Returns detailed health information including service status,
    queue health, and recent performance metrics.
    """
    try:
        sync_service = get_isin_sync_service()
        stats = sync_service.get_sync_statistics()

        # Determine health status
        is_healthy = (
            stats["service_running"]
            and stats["failed_jobs"]
            < stats["total_jobs"] * 0.1  # Less than 10% failure rate
        )

        health_data = {
            "healthy": is_healthy,
            "service_running": stats["service_running"],
            "queue_size": stats["queue_size"],
            "active_jobs": stats["running_jobs"],
            "recent_failures": stats["failed_jobs"],
            "unresolved_conflicts": stats["unresolved_conflicts"],
            "last_check": __import__("datetime").datetime.now().isoformat(),
        }

        return {
            "success": True,
            "data": health_data,
            "message": "Sync service health check completed",
        }

    except Exception as e:
        logger.error(f"Error checking sync service health: {e}")
        raise HTTPException(status_code=500, detail=str(e))
