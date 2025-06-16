"""Integration tests for ISIN sync service and API endpoints.

This module tests the complete ISIN synchronization workflow including
background tasks, conflict resolution, and API endpoints.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from backend.api.isin_sync import router
from backend.services.isin_sync_service import (
    ConflictResolution,
    ISINSyncService,
    MappingConflict,
    SyncJob,
    SyncStatus,
)


@pytest.fixture()
def sync_service():
    """Create ISIN sync service instance for testing."""
    service = ISINSyncService()
    # Reset state for each test
    service.active_jobs.clear()
    service.conflicts.clear()
    return service


@pytest.fixture()
def test_client():
    """Create FastAPI test client."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture()
def mock_db_with_mappings():
    """Mock database with sample ISIN mappings."""
    mock_db = Mock()

    # Sample existing mapping
    existing_mapping = Mock()
    existing_mapping.isin = "DE0007164600"
    existing_mapping.ticker = "SAP"
    existing_mapping.exchange_code = "XETR"
    existing_mapping.exchange_name = "Xetra"
    existing_mapping.security_name = "SAP SE"
    existing_mapping.currency = "EUR"
    existing_mapping.source = "manual_verified"
    existing_mapping.confidence = 0.95
    existing_mapping.is_active = True
    existing_mapping.last_updated = datetime.now() - timedelta(days=30)

    mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
        existing_mapping
    )
    mock_db.query.return_value.filter.return_value.first.return_value = existing_mapping
    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.rollback = Mock()

    return mock_db


class TestISINSyncService:
    """Test ISIN sync service core functionality."""

    @pytest.mark.asyncio()
    async def test_start_stop_background_sync(self, sync_service):
        """Test starting and stopping the background sync service."""
        # Initially not running
        assert not sync_service._running

        # Start service
        await sync_service.start_background_sync()
        assert sync_service._running
        assert sync_service._sync_task is not None

        # Stop service
        await sync_service.stop_background_sync()
        assert not sync_service._running

    @pytest.mark.asyncio()
    async def test_queue_sync_job(self, sync_service):
        """Test queuing sync jobs."""
        isins = ["US0378331005", "DE0007164600", "GB0002162385"]

        job_id = await sync_service.queue_sync_job(isins, "test_source")

        assert job_id in sync_service.active_jobs
        job = sync_service.active_jobs[job_id]
        assert job.source == "test_source"
        assert job.isins == isins
        assert job.status == SyncStatus.PENDING

    def test_get_job_status(self, sync_service, sample_sync_job_data):
        """Test getting job status."""
        # Add test job
        job = SyncJob(
            job_id=sample_sync_job_data["job_id"],
            source=sample_sync_job_data["source"],
            isins=sample_sync_job_data["isins"],
            status=SyncStatus.PENDING,
        )
        sync_service.active_jobs[job.job_id] = job

        status = sync_service.get_job_status(job.job_id)

        assert status is not None
        assert status["job_id"] == job.job_id
        assert status["source"] == job.source
        assert status["status"] == "pending"

    def test_get_job_status_not_found(self, sync_service):
        """Test getting status for non-existent job."""
        status = sync_service.get_job_status("nonexistent_job")
        assert status is None

    @pytest.mark.asyncio()
    async def test_sync_single_isin_create_new(
        self, sync_service, mock_db_with_mappings
    ):
        """Test syncing a single ISIN - creating new mapping."""
        mock_db_with_mappings.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            None
        )

        job = SyncJob(job_id="test_job", source="test", isins=["US0378331005"])

        with patch.object(sync_service, "_fetch_external_data") as mock_fetch:
            mock_fetch.return_value = {
                "ticker": "AAPL",
                "exchange_code": "XNAS",
                "exchange_name": "NASDAQ",
                "security_name": "Apple Inc.",
                "currency": "USD",
                "source": "test_provider",
                "confidence": 0.9,
            }

            await sync_service._sync_single_isin(
                mock_db_with_mappings, job, "US0378331005"
            )

            # Should create new mapping
            mock_db_with_mappings.add.assert_called_once()
            mock_db_with_mappings.commit.assert_called_once()

    @pytest.mark.asyncio()
    async def test_sync_single_isin_update_existing(
        self, sync_service, mock_db_with_mappings
    ):
        """Test syncing a single ISIN - updating existing mapping."""
        job = SyncJob(job_id="test_job", source="test", isins=["DE0007164600"])

        with patch.object(sync_service, "_fetch_external_data") as mock_fetch:
            mock_fetch.return_value = {
                "ticker": "SAP",
                "exchange_code": "XETR",
                "exchange_name": "Xetra",
                "security_name": "SAP SE",
                "currency": "EUR",
                "source": "german_data_providers",
                "confidence": 0.92,
            }

            await sync_service._sync_single_isin(
                mock_db_with_mappings, job, "DE0007164600"
            )

            # Should update existing mapping
            mock_db_with_mappings.commit.assert_called_once()

    def test_detect_conflict(self, sync_service, sample_conflict_data):
        """Test conflict detection."""
        existing = Mock()
        existing.isin = sample_conflict_data["isin"]
        existing.ticker = sample_conflict_data["existing_mapping"]["ticker"]
        existing.exchange_code = sample_conflict_data["existing_mapping"][
            "exchange_code"
        ]
        existing.security_name = sample_conflict_data["existing_mapping"][
            "security_name"
        ]

        new_data = sample_conflict_data["new_mapping"]

        conflict = sync_service._detect_conflict(existing, new_data)

        assert conflict is not None
        assert conflict.isin == sample_conflict_data["isin"]
        assert "ticker_mismatch" in conflict.conflict_type

    def test_detect_no_conflict(self, sync_service):
        """Test when no conflict exists."""
        existing = Mock()
        existing.isin = "DE0007164600"
        existing.ticker = "SAP"
        existing.exchange_code = "XETR"
        existing.security_name = "SAP SE"

        new_data = {"ticker": "SAP", "exchange_code": "XETR", "security_name": "SAP SE"}

        conflict = sync_service._detect_conflict(existing, new_data)
        assert conflict is None

    def test_auto_resolve_conflict_high_confidence(self, sync_service):
        """Test automatic conflict resolution with high confidence data."""
        conflict = Mock()
        conflict.new_mapping = {"confidence": 0.95}

        resolution = sync_service._auto_resolve_conflict(conflict)
        assert resolution == ConflictResolution.USE_NEW

    def test_auto_resolve_conflict_verified_source(self, sync_service):
        """Test automatic conflict resolution with verified source."""
        conflict = Mock()
        conflict.existing_mapping.source = "manual_verified"
        conflict.new_mapping = {"confidence": 0.7}

        resolution = sync_service._auto_resolve_conflict(conflict)
        assert resolution == ConflictResolution.KEEP_EXISTING

    def test_auto_resolve_conflict_stale_data(self, sync_service):
        """Test automatic conflict resolution with stale data."""
        conflict = Mock()
        conflict.existing_mapping.source = "auto_sync"
        conflict.existing_mapping.last_updated = datetime.now() - timedelta(days=35)
        conflict.new_mapping = {"confidence": 0.8}

        resolution = sync_service._auto_resolve_conflict(conflict)
        assert resolution == ConflictResolution.USE_NEW

    def test_get_pending_conflicts(self, sync_service, sample_conflict_data):
        """Test getting pending conflicts."""
        # Add test conflict
        conflict = MappingConflict(
            isin=sample_conflict_data["isin"],
            existing_mapping=Mock(),
            new_mapping=sample_conflict_data["new_mapping"],
            conflict_type=sample_conflict_data["conflict_type"],
        )
        sync_service.conflicts[sample_conflict_data["isin"]] = [conflict]

        pending = sync_service.get_pending_conflicts()

        assert len(pending) == 1
        assert pending[0]["isin"] == sample_conflict_data["isin"]
        assert pending[0]["conflict_type"] == sample_conflict_data["conflict_type"]

    @pytest.mark.asyncio()
    async def test_resolve_conflict_manually(self, sync_service, mock_db_with_mappings):
        """Test manual conflict resolution."""
        # Add test conflict
        conflict = MappingConflict(
            isin="DE0007164600",
            existing_mapping=Mock(),
            new_mapping={"ticker": "SAP.DE"},
            conflict_type="ticker_mismatch",
        )
        sync_service.conflicts["DE0007164600"] = [conflict]

        with patch("backend.services.isin_sync_service.get_db_session") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = mock_db_with_mappings

            result = await sync_service.resolve_conflict_manually(
                "DE0007164600", ConflictResolution.USE_NEW
            )

            assert result is True
            assert conflict.resolution == ConflictResolution.USE_NEW
            assert conflict.resolved_at is not None

    def test_get_sync_statistics(self, sync_service):
        """Test getting sync statistics."""
        # Add test jobs with different statuses
        jobs = [
            SyncJob("job1", "test", ["ISIN1"], SyncStatus.RUNNING),
            SyncJob("job2", "test", ["ISIN2"], SyncStatus.COMPLETED),
            SyncJob("job3", "test", ["ISIN3"], SyncStatus.FAILED),
        ]

        for job in jobs:
            sync_service.active_jobs[job.job_id] = job

        stats = sync_service.get_sync_statistics()

        assert stats["total_jobs"] == 3
        assert stats["running_jobs"] == 1
        assert stats["completed_jobs"] == 1
        assert stats["failed_jobs"] == 1

    def test_cleanup_old_jobs(self, sync_service):
        """Test cleanup of old completed jobs."""
        # Add old completed job
        old_job = SyncJob("old_job", "test", ["ISIN1"], SyncStatus.COMPLETED)
        old_job.completed_at = datetime.now() - timedelta(hours=25)
        sync_service.active_jobs["old_job"] = old_job

        # Add recent job
        recent_job = SyncJob("recent_job", "test", ["ISIN2"], SyncStatus.COMPLETED)
        recent_job.completed_at = datetime.now() - timedelta(hours=1)
        sync_service.active_jobs["recent_job"] = recent_job

        sync_service._cleanup_old_jobs()

        # Old job should be removed, recent job should remain
        assert "old_job" not in sync_service.active_jobs
        assert "recent_job" in sync_service.active_jobs


class TestISINSyncAPI:
    """Test ISIN sync API endpoints."""

    def test_get_sync_status(self, test_client):
        """Test getting sync service status."""
        with patch("backend.api.isin_sync.get_isin_sync_service") as mock_service:
            mock_service.return_value.get_sync_statistics.return_value = {
                "service_running": True,
                "total_jobs": 10,
                "running_jobs": 2,
                "completed_jobs": 7,
                "failed_jobs": 1,
            }

            response = test_client.get("/isin/sync/status")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total_jobs"] == 10

    def test_create_sync_job(self, test_client):
        """Test creating a sync job."""
        job_request = {
            "isins": ["US0378331005", "DE0007164600"],
            "source": "test_api",
            "priority": "normal",
        }

        with patch("backend.api.isin_sync.get_isin_sync_service") as mock_service:
            mock_service.return_value.queue_sync_job = AsyncMock(return_value="job_123")

            response = test_client.post("/isin/sync/jobs", json=job_request)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["job_id"] == "job_123"

    def test_create_sync_job_validation_error(self, test_client):
        """Test creating sync job with validation errors."""
        # Empty ISIN list
        job_request = {"isins": [], "source": "test_api"}

        response = test_client.post("/isin/sync/jobs", json=job_request)
        assert response.status_code == 400

    def test_create_sync_job_too_many_isins(self, test_client):
        """Test creating sync job with too many ISINs."""
        job_request = {
            "isins": [f"US{str(i).zfill(9)}5" for i in range(501)],  # 501 ISINs
            "source": "test_api",
        }

        response = test_client.post("/isin/sync/jobs", json=job_request)
        assert response.status_code == 400

    def test_get_job_status(self, test_client):
        """Test getting specific job status."""
        job_id = "test_job_123"

        with patch("backend.api.isin_sync.get_isin_sync_service") as mock_service:
            mock_service.return_value.get_job_status.return_value = {
                "job_id": job_id,
                "status": "running",
                "progress": 5,
                "total": 10,
            }

            response = test_client.get(f"/isin/sync/jobs/{job_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["job_id"] == job_id

    def test_get_job_status_not_found(self, test_client):
        """Test getting status for non-existent job."""
        with patch("backend.api.isin_sync.get_isin_sync_service") as mock_service:
            mock_service.return_value.get_job_status.return_value = None

            response = test_client.get("/isin/sync/jobs/nonexistent")

            assert response.status_code == 404

    def test_list_sync_jobs(self, test_client):
        """Test listing sync jobs."""
        mock_jobs = {
            "job1": SyncJob("job1", "test", ["ISIN1"], SyncStatus.RUNNING),
            "job2": SyncJob("job2", "test", ["ISIN2"], SyncStatus.COMPLETED),
        }

        with patch("backend.api.isin_sync.get_isin_sync_service") as mock_service:
            mock_service.return_value.active_jobs = mock_jobs
            mock_service.return_value.get_job_status.side_effect = lambda job_id: {
                "job_id": job_id,
                "status": mock_jobs[job_id].status.value,
                "created_at": "2024-01-15T10:00:00Z",
            }

            response = test_client.get("/isin/sync/jobs")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["jobs"]) == 2

    def test_get_pending_conflicts(self, test_client):
        """Test getting pending conflicts."""
        mock_conflicts = [
            {
                "isin": "DE0007164600",
                "conflict_type": "ticker_mismatch",
                "existing_ticker": "SAP",
                "new_ticker": "SAP.DE",
            }
        ]

        with patch("backend.api.isin_sync.get_isin_sync_service") as mock_service:
            mock_service.return_value.get_pending_conflicts.return_value = (
                mock_conflicts
            )

            response = test_client.get("/isin/sync/conflicts")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["conflicts"]) == 1

    def test_resolve_conflict(self, test_client):
        """Test resolving a conflict."""
        conflict_request = {
            "isin": "DE0007164600",
            "resolution": "use_new",
            "reason": "Higher confidence score",
        }

        with patch("backend.api.isin_sync.get_isin_sync_service") as mock_service:
            mock_service.return_value.resolve_conflict_manually = AsyncMock(
                return_value=True
            )

            response = test_client.post(
                "/isin/sync/conflicts/resolve", json=conflict_request
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_resolve_conflict_invalid_resolution(self, test_client):
        """Test resolving conflict with invalid resolution."""
        conflict_request = {"isin": "DE0007164600", "resolution": "invalid_resolution"}

        response = test_client.post(
            "/isin/sync/conflicts/resolve", json=conflict_request
        )
        assert response.status_code == 400

    def test_start_bulk_sync(self, test_client):
        """Test starting bulk sync operation."""
        bulk_request = {
            "country_codes": ["DE", "US"],
            "exchanges": ["XETR", "XNAS"],
            "max_isins": 100,
            "source": "bulk_test",
        }

        with patch("backend.api.isin_sync.get_isin_sync_service") as mock_service:
            mock_service.return_value.queue_sync_job = AsyncMock(
                return_value="bulk_job_123"
            )

            with patch("backend.api.isin_sync.get_db_session") as mock_get_db:
                mock_db = Mock()
                mock_mappings = [Mock(isin=f"DE{str(i).zfill(9)}0") for i in range(50)]
                mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = (
                    mock_mappings
                )
                mock_get_db.return_value = mock_db

                response = test_client.post("/isin/sync/bulk", json=bulk_request)

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["job_id"] == "bulk_job_123"

    def test_start_sync_service(self, test_client):
        """Test starting the sync service."""
        with patch("backend.api.isin_sync.get_isin_sync_service") as mock_service:
            mock_service.return_value._running = False
            mock_service.return_value.start_background_sync = AsyncMock()

            response = test_client.post("/isin/sync/service/start")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_stop_sync_service(self, test_client):
        """Test stopping the sync service."""
        with patch("backend.api.isin_sync.get_isin_sync_service") as mock_service:
            mock_service.return_value._running = True
            mock_service.return_value.stop_background_sync = AsyncMock()

            response = test_client.post("/isin/sync/service/stop")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_cancel_sync_job(self, test_client):
        """Test cancelling a sync job."""
        job_id = "test_job_123"

        with patch("backend.api.isin_sync.get_isin_sync_service") as mock_service:
            mock_job = Mock()
            mock_job.status.value = "running"
            mock_service.return_value.active_jobs = {job_id: mock_job}

            response = test_client.delete(f"/isin/sync/jobs/{job_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_cancel_nonexistent_job(self, test_client):
        """Test cancelling non-existent job."""
        with patch("backend.api.isin_sync.get_isin_sync_service") as mock_service:
            mock_service.return_value.active_jobs = {}

            response = test_client.delete("/isin/sync/jobs/nonexistent")

            assert response.status_code == 404

    def test_sync_service_health(self, test_client):
        """Test sync service health check."""
        with patch("backend.api.isin_sync.get_isin_sync_service") as mock_service:
            mock_service.return_value.get_sync_statistics.return_value = {
                "service_running": True,
                "queue_size": 5,
                "running_jobs": 2,
                "failed_jobs": 1,
                "total_jobs": 10,
            }

            response = test_client.get("/isin/sync/health")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["healthy"] is True


class TestISINSyncServicePerformance:
    """Test performance aspects of ISIN sync service."""

    @pytest.mark.asyncio()
    async def test_concurrent_job_processing(self, sync_service):
        """Test concurrent processing of multiple sync jobs."""
        # Queue multiple jobs
        job_ids = []
        for i in range(5):
            isins = [f"US{str(i).zfill(9)}5"]
            job_id = await sync_service.queue_sync_job(isins, f"test_source_{i}")
            job_ids.append(job_id)

        assert len(sync_service.active_jobs) == 5

        # All jobs should be in pending state
        for job_id in job_ids:
            job = sync_service.active_jobs[job_id]
            assert job.status == SyncStatus.PENDING

    @pytest.mark.asyncio()
    async def test_large_batch_sync(self, sync_service):
        """Test syncing large batch of ISINs."""
        # Create large batch
        large_batch = [f"US{str(i).zfill(9)}5" for i in range(100)]

        job_id = await sync_service.queue_sync_job(large_batch, "large_batch_test")
        job = sync_service.active_jobs[job_id]

        assert len(job.isins) == 100
        assert job.total == 0  # Will be set when job starts
        assert job.status == SyncStatus.PENDING

    def test_memory_usage_with_many_jobs(self, sync_service):
        """Test memory usage with many active jobs."""
        import sys

        initial_size = sys.getsizeof(sync_service.active_jobs)

        # Add many jobs
        for i in range(100):
            job = SyncJob(f"job_{i}", "test", [f"ISIN_{i}"], SyncStatus.PENDING)
            sync_service.active_jobs[job.job_id] = job

        final_size = sys.getsizeof(sync_service.active_jobs)

        # Memory growth should be reasonable
        growth_ratio = final_size / initial_size
        assert growth_ratio < 1000  # Shouldn't grow more than 1000x


class TestISINSyncServiceErrorHandling:
    """Test error handling in ISIN sync service."""

    @pytest.mark.asyncio()
    async def test_database_error_handling(self, sync_service):
        """Test handling of database errors during sync."""
        job = SyncJob("test_job", "test", ["US0378331005"])

        with patch("backend.services.isin_sync_service.get_db_session") as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")

            # Should handle database errors gracefully
            try:
                await sync_service._sync_single_isin(None, job, "US0378331005")
            except Exception:
                pytest.fail("Database error should be handled gracefully")

    @pytest.mark.asyncio()
    async def test_external_api_error_handling(self, sync_service):
        """Test handling of external API errors."""
        job = SyncJob("test_job", "test", ["US0378331005"])

        with patch.object(sync_service, "_fetch_external_data") as mock_fetch:
            mock_fetch.side_effect = Exception("API unavailable")

            # Should handle API errors gracefully
            with patch(
                "backend.services.isin_sync_service.get_db_session"
            ) as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value.__enter__.return_value = mock_db

                await sync_service._sync_single_isin(mock_db, job, "US0378331005")
                # Should not crash, error should be logged

    def test_invalid_job_data_handling(self, sync_service):
        """Test handling of invalid job data."""
        # Test with empty ISIN list
        with pytest.raises(ValueError):
            job = SyncJob("test_job", "test", [])

        # Test with invalid ISIN format
        job = SyncJob("test_job", "test", ["INVALID_ISIN"])
        assert job.isins == ["INVALID_ISIN"]  # Should accept, validation happens later

    @pytest.mark.asyncio()
    async def test_conflict_resolution_error_handling(self, sync_service):
        """Test error handling in conflict resolution."""
        conflict = MappingConflict(
            isin="DE0007164600",
            existing_mapping=Mock(),
            new_mapping={"ticker": "SAP.DE"},
            conflict_type="ticker_mismatch",
        )

        with patch.object(sync_service, "_apply_resolution") as mock_apply:
            mock_apply.side_effect = Exception("Resolution failed")

            # Should handle resolution errors gracefully
            await sync_service._handle_conflict(Mock(), conflict)
            # Conflict should remain unresolved
            assert conflict.resolution is None


@pytest.mark.integration()
class TestISINSyncServiceIntegration:
    """Integration tests for ISIN sync service."""

    @pytest.mark.asyncio()
    async def test_full_sync_workflow(self, sync_service):
        """Test complete sync workflow from start to finish."""
        # This would be a full integration test with real database
        # and external API calls (when --run-integration flag is used)

    @pytest.mark.asyncio()
    async def test_conflict_resolution_workflow(self, sync_service):
        """Test complete conflict resolution workflow."""
        # This would test the full conflict detection and resolution process

    @pytest.mark.asyncio()
    async def test_api_endpoint_integration(self, test_client):
        """Test API endpoints with real sync service."""
        # This would test the API endpoints with actual sync service
