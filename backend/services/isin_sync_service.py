"""Real-time ISIN mapping sync service for automatic updates.

This service provides real-time synchronization of ISIN mappings from multiple
data sources, automatic conflict resolution, and background sync tasks.
"""

import asyncio
import contextlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import time
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.models import get_db
from backend.models.isin import ISINTickerMapping
from backend.services.european_mappings import (
    EuropeanStockMapping,
    get_european_mappings_service,
)
from backend.services.german_data_providers import get_german_data_service

logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    """Sync operation status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConflictResolution(Enum):
    """Conflict resolution strategies."""

    KEEP_EXISTING = "keep_existing"
    USE_NEW = "use_new"
    MERGE = "merge"
    MANUAL_REVIEW = "manual_review"


@dataclass
class SyncJob:
    """Sync job configuration."""

    job_id: str
    source: str
    isins: list[str]
    status: SyncStatus = SyncStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    progress: int = 0
    total: int = 0
    results: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate job data after initialization."""
        if not self.isins:
            raise ValueError("ISIN list cannot be empty")
        if not self.job_id:
            raise ValueError("Job ID cannot be empty")
        if not self.source:
            raise ValueError("Source cannot be empty")


@dataclass
class MappingConflict:
    """Represents a conflict between mappings."""

    isin: str
    existing_mapping: ISINTickerMapping
    new_mapping: dict[str, Any]
    conflict_type: str
    resolution: ConflictResolution | None = None
    resolved_at: datetime | None = None


class ISINSyncService:
    """Service for real-time ISIN mapping synchronization."""

    def __init__(self):
        self.active_jobs: dict[str, SyncJob] = {}
        self.sync_queue: asyncio.Queue = asyncio.Queue()
        self.conflicts: dict[str, list[MappingConflict]] = {}

        # Sync configuration
        self.batch_size = 50
        self.max_concurrent_jobs = 3
        self.retry_attempts = 3
        self.retry_delay = 5.0  # seconds

        # Data sources
        self.german_service = get_german_data_service()
        self.european_service = get_european_mappings_service()

        # Sync rules
        self.auto_resolve_rules = {
            "confidence_threshold": 0.8,
            "prefer_primary_listing": True,
            "trust_verified_sources": True,
            "max_age_days": 30,
        }

        # Background task
        self._sync_task = None
        self._running = False

    async def start_background_sync(self):
        """Start the background sync service."""
        if self._running:
            logger.warning("Background sync already running")
            return

        self._running = True
        self._sync_task = asyncio.create_task(self._background_sync_loop())
        logger.info("Background sync service started")

    async def stop_background_sync(self):
        """Stop the background sync service."""
        if not self._running:
            return

        self._running = False

        if self._sync_task:
            self._sync_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._sync_task

        logger.info("Background sync service stopped")

    async def _background_sync_loop(self):
        """Main background sync loop."""
        while self._running:
            try:
                # Process sync queue
                await self._process_sync_queue()

                # Perform periodic full sync
                await self._periodic_full_sync()

                # Clean up old jobs
                self._cleanup_old_jobs()

                # Wait before next iteration
                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background sync loop: {e}")
                await asyncio.sleep(30)  # Wait before retrying

    async def _process_sync_queue(self):
        """Process queued sync jobs."""
        active_count = len(
            [
                job
                for job in self.active_jobs.values()
                if job.status == SyncStatus.RUNNING
            ]
        )

        while active_count < self.max_concurrent_jobs and not self.sync_queue.empty():
            try:
                job = await asyncio.wait_for(self.sync_queue.get(), timeout=1.0)
                await self._execute_sync_job(job)
                active_count += 1
            except TimeoutError:
                break

    async def _execute_sync_job(self, job: SyncJob):
        """Execute a single sync job."""
        try:
            logger.info(f"Starting sync job {job.job_id} for {len(job.isins)} ISINs")

            job.status = SyncStatus.RUNNING
            job.started_at = datetime.now()
            job.total = len(job.isins)

            # Process ISINs in batches
            for i in range(0, len(job.isins), self.batch_size):
                batch = job.isins[i : i + self.batch_size]
                await self._sync_batch(job, batch)

                job.progress = min(i + self.batch_size, job.total)

                if not self._running:
                    job.status = SyncStatus.CANCELLED
                    return

            job.status = SyncStatus.COMPLETED
            job.completed_at = datetime.now()

            logger.info(f"Completed sync job {job.job_id}")

        except Exception as e:
            logger.error(f"Error executing sync job {job.job_id}: {e}")
            job.status = SyncStatus.FAILED
            job.errors.append(str(e))

    async def _sync_batch(self, job: SyncJob, isins: list[str]):
        """Sync a batch of ISINs."""
        db = next(get_db())
        try:
            for isin in isins:
                try:
                    await self._sync_single_isin(db, job, isin)
                except Exception as e:
                    logger.error(f"Error syncing ISIN {isin}: {e}")
                    job.errors.append(f"{isin}: {e!s}")
        finally:
            db.close()

    async def _sync_single_isin(self, db: Session, job: SyncJob, isin: str):
        """Sync a single ISIN."""
        try:
            # Get current mapping from database
            existing = (
                db.query(ISINTickerMapping)
                .filter(ISINTickerMapping.isin == isin, ISINTickerMapping.is_active)
                .first()
            )

            # Get updated data from external sources
            new_data = await self._fetch_external_data(isin, job.source)

            if not new_data:
                return

            # Check for conflicts
            if existing:
                conflict = self._detect_conflict(existing, new_data)
                if conflict:
                    await self._handle_conflict(db, conflict)
                    return

            # Create or update mapping
            await self._create_or_update_mapping(db, isin, new_data)
        except Exception as e:
            logger.error(f"Error syncing ISIN {isin}: {e}")
            # Add error to job if provided
            if hasattr(job, "errors"):
                job.errors.append(f"Failed to sync {isin}: {e!s}")
            # Don't re-raise the exception - handle gracefully

    async def _fetch_external_data(
        self, isin: str, source: str
    ) -> dict[str, Any] | None:
        """Fetch ISIN data from external sources."""
        try:
            if source == "german_data_providers":
                data = await self.german_service.get_comprehensive_data(isin)
                return self._normalize_german_data(data)

            if source == "european_mappings":
                mappings = self.european_service.get_mappings_by_isin(isin)
                if mappings:
                    return self._normalize_european_data(mappings[0])

            # Add more sources as needed

        except Exception as e:
            logger.error(f"Error fetching external data for {isin} from {source}: {e}")

        return None

    def _normalize_german_data(self, data: dict[str, Any]) -> dict[str, Any] | None:
        """Normalize German data provider response."""
        if not data or not data.get("security_info"):
            return None

        info = data["security_info"]
        quote = data.get("best_quote")

        return {
            "ticker": info.ticker_symbol,
            "exchange_code": "XETR",  # Default to Xetra
            "exchange_name": "Xetra",
            "security_name": info.name,
            "currency": quote.currency if quote else "EUR",
            "source": "german_data_providers",
            "confidence": 0.9,
            "last_updated": datetime.now(),
        }

    def _normalize_european_data(self, mapping: EuropeanStockMapping) -> dict[str, Any]:
        """Normalize European mapping data."""
        return {
            "ticker": mapping.ticker,
            "exchange_code": mapping.exchange.code,
            "exchange_name": mapping.exchange.name,
            "security_name": mapping.company_name,
            "currency": mapping.currency,
            "source": "european_mappings",
            "confidence": mapping.confidence,
            "last_updated": datetime.now(),
        }

    def _detect_conflict(
        self, existing: ISINTickerMapping, new_data: dict[str, Any]
    ) -> MappingConflict | None:
        """Detect conflicts between existing and new mappings."""
        conflicts = []

        # Check ticker mismatch
        if existing.ticker != new_data.get("ticker"):
            conflicts.append("ticker_mismatch")

        # Check exchange mismatch
        if existing.exchange_code != new_data.get("exchange_code"):
            conflicts.append("exchange_mismatch")

        # Check security name mismatch
        if (
            existing.security_name
            and new_data.get("security_name")
            and existing.security_name.lower()
            != new_data.get("security_name", "").lower()
        ):
            conflicts.append("name_mismatch")

        if conflicts:
            return MappingConflict(
                isin=existing.isin,
                existing_mapping=existing,
                new_mapping=new_data,
                conflict_type=",".join(conflicts),
            )

        return None

    async def _handle_conflict(self, db: Session, conflict: MappingConflict):
        """Handle mapping conflicts."""
        # Store conflict for manual review
        if conflict.isin not in self.conflicts:
            self.conflicts[conflict.isin] = []

        self.conflicts[conflict.isin].append(conflict)

        # Try automatic resolution
        resolution = self._auto_resolve_conflict(conflict)

        if resolution:
            await self._apply_resolution(db, conflict, resolution)
        else:
            logger.info(f"Conflict for {conflict.isin} requires manual review")

    def _auto_resolve_conflict(
        self, conflict: MappingConflict
    ) -> ConflictResolution | None:
        """Attempt automatic conflict resolution."""
        existing = conflict.existing_mapping
        new_data = conflict.new_mapping

        # Rule 1: Trust high-confidence new data
        if (
            new_data.get("confidence", 0)
            > self.auto_resolve_rules["confidence_threshold"]
        ):
            return ConflictResolution.USE_NEW

        # Rule 2: Keep existing if it's from a verified source
        if self.auto_resolve_rules["trust_verified_sources"] and existing.source in [
            "manual_verified",
            "bloomberg",
            "reuters",
        ]:
            return ConflictResolution.KEEP_EXISTING

        # Rule 3: Prefer primary listings
        if self.auto_resolve_rules["prefer_primary_listing"] and new_data.get(
            "is_primary_listing", False
        ):
            return ConflictResolution.USE_NEW

        # Rule 4: Check data freshness
        if existing.last_updated and isinstance(existing.last_updated, datetime):
            age = datetime.now() - existing.last_updated
            if age.days > self.auto_resolve_rules.get("max_age_days", 30):
                return ConflictResolution.USE_NEW

        return None

    async def _apply_resolution(
        self, db: Session, conflict: MappingConflict, resolution: ConflictResolution
    ):
        """Apply conflict resolution."""
        try:
            if resolution == ConflictResolution.USE_NEW:
                # Update existing mapping with new data
                mapping = conflict.existing_mapping
                new_data = conflict.new_mapping

                mapping.ticker = new_data.get("ticker", mapping.ticker)
                mapping.exchange_code = new_data.get(
                    "exchange_code", mapping.exchange_code
                )
                mapping.exchange_name = new_data.get(
                    "exchange_name", mapping.exchange_name
                )
                mapping.security_name = new_data.get(
                    "security_name", mapping.security_name
                )
                mapping.currency = new_data.get("currency", mapping.currency)
                mapping.source = new_data.get("source", mapping.source)
                mapping.confidence = new_data.get("confidence", mapping.confidence)
                mapping.last_updated = datetime.now()

                db.commit()

            elif resolution == ConflictResolution.MERGE:
                # Implement merge logic
                await self._merge_mappings(db, conflict)

            conflict.resolution = resolution
            conflict.resolved_at = datetime.now()

            logger.info(
                f"Resolved conflict for {conflict.isin} using {resolution.value}"
            )

        except Exception as e:
            logger.error(f"Error applying resolution for {conflict.isin}: {e}")

    async def _merge_mappings(self, db: Session, conflict: MappingConflict):
        """Merge conflicting mappings."""
        existing = conflict.existing_mapping
        new_data = conflict.new_mapping

        # Merge strategy: take the best parts of both
        if not existing.security_name and new_data.get("security_name"):
            existing.security_name = new_data["security_name"]

        if new_data.get("confidence", 0) > existing.confidence:
            existing.confidence = new_data["confidence"]

        # Update timestamp
        existing.last_updated = datetime.now()

        db.commit()

    async def _create_or_update_mapping(
        self, db: Session, isin: str, data: dict[str, Any]
    ):
        """Create or update ISIN mapping."""
        try:
            # Check if mapping exists
            existing = (
                db.query(ISINTickerMapping)
                .filter(
                    ISINTickerMapping.isin == isin,
                    ISINTickerMapping.ticker == data.get("ticker"),
                    ISINTickerMapping.exchange_code == data.get("exchange_code"),
                )
                .first()
            )

            if existing:
                # Update existing
                existing.security_name = data.get(
                    "security_name", existing.security_name
                )
                existing.currency = data.get("currency", existing.currency)
                existing.confidence = data.get("confidence", existing.confidence)
                existing.last_updated = datetime.now()
            else:
                # Create new
                new_mapping = ISINTickerMapping()
                new_mapping.isin = isin
                new_mapping.ticker = data.get("ticker", "")
                new_mapping.exchange_code = data.get("exchange_code")
                new_mapping.exchange_name = data.get("exchange_name")
                new_mapping.security_name = data.get("security_name")
                new_mapping.currency = data.get("currency", "EUR")
                new_mapping.source = data.get("source", "auto_sync")
                new_mapping.confidence = data.get("confidence", 0.8)
                new_mapping.is_active = True

                db.add(new_mapping)

            db.commit()

        except Exception as e:
            logger.error(f"Error creating/updating mapping for {isin}: {e}")
            db.rollback()

    async def _periodic_full_sync(self):
        """Perform periodic full sync of all mappings."""
        # Run full sync once per day
        if not hasattr(self, "_last_full_sync"):
            self._last_full_sync = datetime.now() - timedelta(days=1)

        if datetime.now() - self._last_full_sync > timedelta(days=1):
            logger.info("Starting periodic full sync")

            with contextlib.closing(next(get_db())) as db:
                # Get all ISINs that need updating
                stale_mappings = (
                    db.query(ISINTickerMapping)
                    .filter(
                        or_(
                            ISINTickerMapping.last_updated
                            < datetime.now() - timedelta(days=7),
                            ISINTickerMapping.last_updated.is_(None),
                        )
                    )
                    .limit(1000)
                    .all()
                )

                if stale_mappings:
                    isins = [mapping.isin for mapping in stale_mappings]
                    await self.queue_sync_job(isins, "periodic_full_sync")

            self._last_full_sync = datetime.now()

    def _cleanup_old_jobs(self):
        """Clean up old completed jobs."""
        cutoff = datetime.now() - timedelta(hours=24)

        to_remove = []
        for job_id, job in self.active_jobs.items():
            if (
                job.status
                in [SyncStatus.COMPLETED, SyncStatus.FAILED, SyncStatus.CANCELLED]
                and job.completed_at
                and job.completed_at < cutoff
            ):
                to_remove.append(job_id)

        for job_id in to_remove:
            del self.active_jobs[job_id]

    async def queue_sync_job(self, isins: list[str], source: str = "manual") -> str:
        """Queue a new sync job."""
        import uuid

        job_id = f"sync_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        job = SyncJob(job_id=job_id, source=source, isins=isins.copy())

        self.active_jobs[job_id] = job
        await self.sync_queue.put(job)

        logger.info(f"Queued sync job {job_id} for {len(isins)} ISINs")
        return job_id

    def get_job_status(self, job_id: str) -> dict[str, Any] | None:
        """Get status of a sync job."""
        job = self.active_jobs.get(job_id)
        if not job:
            return None

        return {
            "job_id": job.job_id,
            "source": job.source,
            "status": job.status.value,
            "progress": job.progress,
            "total": job.total,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "errors": job.errors,
            "results": job.results,
        }

    def get_pending_conflicts(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get pending conflicts that need manual resolution."""
        conflicts = []

        for isin, isin_conflicts in self.conflicts.items():
            for conflict in isin_conflicts:
                if conflict.resolution is None:
                    conflicts.append(
                        {
                            "isin": isin,
                            "conflict_type": conflict.conflict_type,
                            "existing_ticker": conflict.existing_mapping.ticker,
                            "existing_exchange": conflict.existing_mapping.exchange_code,
                            "new_ticker": conflict.new_mapping.get("ticker"),
                            "new_exchange": conflict.new_mapping.get("exchange_code"),
                            "existing_confidence": conflict.existing_mapping.confidence,
                            "new_confidence": conflict.new_mapping.get("confidence", 0),
                        }
                    )

        return conflicts[:limit]

    async def resolve_conflict_manually(
        self, isin: str, resolution: ConflictResolution
    ) -> bool:
        """Manually resolve a conflict."""
        if isin not in self.conflicts:
            return False

        unresolved_conflicts = [c for c in self.conflicts[isin] if c.resolution is None]
        if not unresolved_conflicts:
            return False

        try:
            with contextlib.closing(next(get_db())) as db:
                for conflict in unresolved_conflicts:
                    await self._apply_resolution(db, conflict, resolution)

            return True

        except Exception as e:
            logger.error(f"Error manually resolving conflict for {isin}: {e}")
            return False

    def get_sync_statistics(self) -> dict[str, Any]:
        """Get sync service statistics."""
        total_jobs = len(self.active_jobs)
        running_jobs = len(
            [j for j in self.active_jobs.values() if j.status == SyncStatus.RUNNING]
        )
        completed_jobs = len(
            [j for j in self.active_jobs.values() if j.status == SyncStatus.COMPLETED]
        )
        failed_jobs = len(
            [j for j in self.active_jobs.values() if j.status == SyncStatus.FAILED]
        )

        total_conflicts = sum(len(conflicts) for conflicts in self.conflicts.values())
        unresolved_conflicts = sum(
            len([c for c in conflicts if c.resolution is None])
            for conflicts in self.conflicts.values()
        )

        return {
            "service_running": self._running,
            "total_jobs": total_jobs,
            "running_jobs": running_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "queue_size": self.sync_queue.qsize(),
            "total_conflicts": total_conflicts,
            "unresolved_conflicts": unresolved_conflicts,
            "last_full_sync": getattr(self, "_last_full_sync", None),
        }


# Singleton instance
isin_sync_service = ISINSyncService()


def get_isin_sync_service() -> ISINSyncService:
    """Get the ISIN sync service instance."""
    return isin_sync_service


async def start_sync_service():
    """Start the ISIN sync service."""
    await isin_sync_service.start_background_sync()


async def stop_sync_service():
    """Stop the ISIN sync service."""
    await isin_sync_service.stop_background_sync()
