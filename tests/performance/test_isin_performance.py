"""Performance and load tests for ISIN system components.

This module contains performance tests, benchmarks, and load tests
for the ISIN validation, mapping, and sync services.
"""

import asyncio
import gc
import statistics
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch

import psutil
import pytest

from backend.services.enhanced_market_data import EnhancedMarketDataService
from backend.services.isin_sync_service import ISINSyncService
from backend.services.isin_utils import ISINService, ISINUtils
from tests.factories import ISINFactory, TestDataGenerator


@pytest.mark.benchmark
@pytest.mark.performance
class TestISINValidationPerformance:
    """Performance tests for ISIN validation."""

    def test_single_validation_performance(self, benchmark):
        """Benchmark single ISIN validation performance."""
        isin = ISINFactory.get_known_valid_isin()

        result = benchmark(ISINUtils.validate_isin, isin)
        assert result[0] is True  # Should be valid

    def test_batch_validation_performance(self, benchmark, performance_test_data):
        """Benchmark batch ISIN validation performance."""
        isins = performance_test_data["small_batch"]

        def validate_batch(isin_list):
            results = []
            for isin in isin_list:
                results.append(ISINUtils.validate_isin(isin))
            return results

        results = benchmark(validate_batch, isins)
        assert len(results) == len(isins)

    @pytest.mark.slow
    def test_large_batch_validation_performance(self, performance_test_data):
        """Test validation performance with large batches."""
        large_batch = performance_test_data["large_batch"]

        start_time = time.time()

        results = []
        for isin in large_batch:
            is_valid, error = ISINUtils.validate_isin(isin)
            results.append((is_valid, error))

        end_time = time.time()
        elapsed = end_time - start_time

        # Performance requirements
        assert (
            elapsed < 10.0
        ), f"Large batch validation took {elapsed:.2f}s, should be under 10s"
        assert len(results) == len(large_batch)

        # Calculate performance metrics
        avg_time_per_isin = elapsed / len(large_batch)
        throughput = len(large_batch) / elapsed

        print("Performance metrics:")
        print(f"  Total time: {elapsed:.3f}s")
        print(f"  Average time per ISIN: {avg_time_per_isin*1000:.2f}ms")
        print(f"  Throughput: {throughput:.0f} ISINs/second")

        # Assert performance requirements
        assert avg_time_per_isin < 0.01, "Average validation time should be under 10ms"
        assert throughput > 100, "Throughput should be over 100 ISINs/second"

    def test_validation_memory_usage(self, performance_test_data):
        """Test memory usage during validation."""
        medium_batch = performance_test_data["medium_batch"]

        # Measure memory before
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # Perform validations
        results = []
        for isin in medium_batch:
            results.append(ISINUtils.validate_isin(isin))

        # Measure memory after
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = memory_after - memory_before

        print("Memory usage:")
        print(f"  Before: {memory_before:.1f}MB")
        print(f"  After: {memory_after:.1f}MB")
        print(f"  Growth: {memory_growth:.1f}MB")

        # Memory growth should be reasonable
        assert memory_growth < 50, f"Memory growth {memory_growth:.1f}MB too high"

        # Clean up
        del results
        gc.collect()

    def test_concurrent_validation_performance(self, performance_test_data):
        """Test performance under concurrent load."""
        medium_batch = performance_test_data["medium_batch"]
        num_threads = 4

        def validate_chunk(chunk):
            return [ISINUtils.validate_isin(isin) for isin in chunk]

        # Split batch into chunks
        chunk_size = len(medium_batch) // num_threads
        chunks = [
            medium_batch[i : i + chunk_size]
            for i in range(0, len(medium_batch), chunk_size)
        ]

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(validate_chunk, chunk) for chunk in chunks]
            results = []
            for future in as_completed(futures):
                results.extend(future.result())

        end_time = time.time()
        elapsed = end_time - start_time

        # Should be faster than sequential processing
        sequential_estimate = len(medium_batch) * 0.001  # Estimate 1ms per ISIN
        speedup = sequential_estimate / elapsed

        print("Concurrent validation:")
        print(f"  Time: {elapsed:.3f}s")
        print(f"  Estimated speedup: {speedup:.1f}x")

        assert len(results) == len(medium_batch)
        assert speedup > 1.5, "Concurrent processing should provide speedup"


@pytest.mark.benchmark
@pytest.mark.performance
class TestISINMappingPerformance:
    """Performance tests for ISIN mapping operations."""

    def test_mapping_lookup_performance(self, benchmark):
        """Benchmark mapping lookup performance."""
        isin = ISINFactory.get_known_valid_isin()

        with patch("backend.services.isin_utils.get_db_session") as mock_get_db:
            mock_session = Mock()
            mock_mapping = Mock()
            mock_mapping.ticker = "AAPL"
            mock_mapping.confidence = 0.95
            mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
                mock_mapping
            )
            mock_get_db.return_value.__enter__.return_value = mock_session

            service = ISINService()
            result = benchmark(service.get_ticker_for_isin, isin)
            assert result == "AAPL"

    @pytest.mark.slow
    def test_bulk_mapping_lookup_performance(self, performance_test_data):
        """Test bulk mapping lookup performance."""
        large_batch = performance_test_data["large_batch"][:500]  # Limit for test

        with patch("backend.services.isin_utils.get_db_session") as mock_get_db:
            mock_session = Mock()
            mock_mapping = Mock()
            mock_mapping.ticker = "TEST"
            mock_mapping.confidence = 0.95
            mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
                mock_mapping
            )
            mock_get_db.return_value.__enter__.return_value = mock_session

            service = ISINService()

            start_time = time.time()

            results = []
            for isin in large_batch:
                ticker = service.get_ticker_for_isin(isin)
                results.append(ticker)

            end_time = time.time()
            elapsed = end_time - start_time

            print("Bulk mapping lookup:")
            print(f"  Total time: {elapsed:.3f}s")
            print(f"  Average per lookup: {elapsed/len(large_batch)*1000:.2f}ms")
            print(f"  Throughput: {len(large_batch)/elapsed:.0f} lookups/second")

            # Performance assertions
            avg_time = elapsed / len(large_batch)
            assert avg_time < 0.005, "Average lookup time should be under 5ms"
            assert len(results) == len(large_batch)


@pytest.mark.benchmark
@pytest.mark.performance
class TestISINSyncServicePerformance:
    """Performance tests for ISIN sync service."""

    @pytest.mark.asyncio
    async def test_sync_job_creation_performance(self, benchmark):
        """Benchmark sync job creation performance."""
        sync_service = ISINSyncService()
        test_isins = [ISINFactory.create_valid_isin() for _ in range(10)]

        async def create_job():
            return await sync_service.queue_sync_job(test_isins, "performance_test")

        job_id = await benchmark(create_job)
        assert job_id in sync_service.active_jobs

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_sync_jobs_performance(self):
        """Test performance under concurrent sync job load."""
        sync_service = ISINSyncService()
        num_concurrent_jobs = 10
        isins_per_job = 20

        async def create_multiple_jobs():
            tasks = []
            for i in range(num_concurrent_jobs):
                test_isins = [
                    ISINFactory.create_valid_isin() for _ in range(isins_per_job)
                ]
                task = sync_service.queue_sync_job(test_isins, f"concurrent_test_{i}")
                tasks.append(task)

            return await asyncio.gather(*tasks)

        start_time = time.time()
        job_ids = await create_multiple_jobs()
        end_time = time.time()

        elapsed = end_time - start_time
        print("Concurrent job creation:")
        print(f"  Total time: {elapsed:.3f}s")
        print(f"  Jobs created: {len(job_ids)}")
        print(f"  Average per job: {elapsed/len(job_ids)*1000:.2f}ms")

        assert len(job_ids) == num_concurrent_jobs
        assert elapsed < 5.0, "Job creation should be fast"

        # Cleanup
        sync_service.active_jobs.clear()

    def test_sync_statistics_performance(self, benchmark):
        """Benchmark sync statistics calculation performance."""
        sync_service = ISINSyncService()

        # Add many jobs for realistic scenario
        for i in range(100):
            from backend.services.isin_sync_service import SyncJob, SyncStatus

            job = SyncJob(f"job_{i}", "test", [f"ISIN_{i}"], SyncStatus.COMPLETED)
            sync_service.active_jobs[job.job_id] = job

        result = benchmark(sync_service.get_sync_statistics)
        assert result["total_jobs"] == 100


@pytest.mark.benchmark
@pytest.mark.performance
class TestMarketDataPerformance:
    """Performance tests for market data services."""

    @pytest.mark.asyncio
    async def test_quote_retrieval_performance(self, benchmark):
        """Benchmark market quote retrieval performance."""
        market_service = EnhancedMarketDataService()
        isin = ISINFactory.get_known_valid_isin()

        # Mock the ticker resolution and quote fetching
        with patch.object(market_service, "_resolve_isin_to_ticker") as mock_resolve:
            mock_resolve.return_value = "AAPL"

            with patch.object(market_service, "_fetch_quote_from_source") as mock_fetch:
                from backend.services.enhanced_market_data import (
                    DataSource,
                    MarketQuote,
                )

                mock_quote = MarketQuote(
                    symbol="AAPL",
                    isin=isin,
                    price=150.0,
                    currency="USD",
                    source=DataSource.YAHOO_FINANCE,
                )
                mock_fetch.return_value = mock_quote

                result = await benchmark(market_service.get_quote_by_isin, isin)
                assert result is not None
                assert result.symbol == "AAPL"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_batch_quote_retrieval_performance(self):
        """Test batch quote retrieval performance."""
        market_service = EnhancedMarketDataService()
        test_isins = [ISINFactory.create_valid_isin() for _ in range(50)]

        # Mock the services
        with patch.object(market_service, "_resolve_isin_to_ticker") as mock_resolve:
            mock_resolve.return_value = "TEST"

            with patch.object(market_service, "_fetch_quote_from_source") as mock_fetch:
                from backend.services.enhanced_market_data import (
                    DataSource,
                    MarketQuote,
                )

                mock_quote = MarketQuote(
                    symbol="TEST",
                    price=100.0,
                    currency="USD",
                    source=DataSource.YAHOO_FINANCE,
                )
                mock_fetch.return_value = mock_quote

                start_time = time.time()

                results = await market_service.get_quotes_batch(
                    test_isins, max_concurrent=5
                )

                end_time = time.time()
                elapsed = end_time - start_time

                print("Batch quote retrieval:")
                print(f"  Total time: {elapsed:.3f}s")
                print(f"  ISINs processed: {len(test_isins)}")
                print(f"  Average per quote: {elapsed/len(test_isins)*1000:.2f}ms")
                print(
                    f"  Successful quotes: {len([q for q in results.values() if q is not None])}"
                )

                assert len(results) == len(test_isins)
                assert elapsed < 30.0, "Batch processing should complete within 30s"


@pytest.mark.performance
@pytest.mark.slow
class TestSystemLoadTests:
    """System-wide load tests."""

    def test_high_concurrency_validation_load(self):
        """Test system under high concurrent validation load."""
        num_threads = 20
        validations_per_thread = 50

        def validation_worker(thread_id):
            results = []
            for i in range(validations_per_thread):
                isin = ISINFactory.create_valid_isin()
                is_valid, error = ISINUtils.validate_isin(isin)
                results.append((is_valid, error))
            return results

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(validation_worker, i) for i in range(num_threads)
            ]

            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())

        end_time = time.time()
        elapsed = end_time - start_time

        total_validations = num_threads * validations_per_thread
        throughput = total_validations / elapsed

        print("High concurrency load test:")
        print(f"  Threads: {num_threads}")
        print(f"  Total validations: {total_validations}")
        print(f"  Total time: {elapsed:.3f}s")
        print(f"  Throughput: {throughput:.0f} validations/second")

        assert len(all_results) == total_validations
        assert throughput > 500, "Should handle at least 500 validations/second"

    def test_memory_stress_test(self):
        """Test memory usage under stress."""
        # Create large amounts of test data
        large_dataset = TestDataGenerator.generate_performance_test_data()

        # Monitor memory usage
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # Process large batch multiple times
        for iteration in range(5):
            results = []
            for isin in large_dataset["large_batch"]:
                is_valid, error = ISINUtils.validate_isin(isin)
                results.append((is_valid, error))

            # Force garbage collection
            del results
            gc.collect()

        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = memory_after - memory_before

        print("Memory stress test:")
        print(f"  Memory before: {memory_before:.1f}MB")
        print(f"  Memory after: {memory_after:.1f}MB")
        print(f"  Memory growth: {memory_growth:.1f}MB")

        # Memory growth should be minimal
        assert memory_growth < 100, f"Memory growth {memory_growth:.1f}MB too high"

    @pytest.mark.asyncio
    async def test_async_operations_load(self):
        """Test async operations under load."""
        sync_service = ISINSyncService()
        num_operations = 100

        # Create many async operations
        async def async_operation(i):
            test_isins = [ISINFactory.create_valid_isin() for _ in range(5)]
            return await sync_service.queue_sync_job(test_isins, f"load_test_{i}")

        start_time = time.time()

        # Run operations concurrently
        tasks = [async_operation(i) for i in range(num_operations)]
        job_ids = await asyncio.gather(*tasks)

        end_time = time.time()
        elapsed = end_time - start_time

        print("Async operations load test:")
        print(f"  Operations: {num_operations}")
        print(f"  Total time: {elapsed:.3f}s")
        print(f"  Ops/second: {num_operations/elapsed:.0f}")

        assert len(job_ids) == num_operations
        assert elapsed < 10.0, "Async operations should complete quickly"

        # Cleanup
        sync_service.active_jobs.clear()


@pytest.mark.performance
class TestPerformanceRegression:
    """Regression tests for performance."""

    def test_validation_performance_regression(self, benchmark):
        """Ensure validation performance doesn't regress."""
        isin = ISINFactory.get_known_valid_isin()

        # Run benchmark
        result = benchmark(ISINUtils.validate_isin, isin)

        # Get benchmark stats
        stats = benchmark.stats
        mean_time = stats.mean

        # Performance regression thresholds
        assert (
            mean_time < 0.001
        ), f"Validation too slow: {mean_time:.6f}s (should be < 1ms)"
        assert result[0] is True

    def test_parsing_performance_regression(self, benchmark):
        """Ensure parsing performance doesn't regress."""
        isin = ISINFactory.get_known_valid_isin()

        result = benchmark(ISINUtils.parse_isin, isin)

        stats = benchmark.stats
        mean_time = stats.mean

        assert (
            mean_time < 0.002
        ), f"Parsing too slow: {mean_time:.6f}s (should be < 2ms)"
        assert result.isin == isin


def measure_performance(
    func: Callable, *args, iterations: int = 100, **kwargs
) -> dict[str, float]:
    """Utility function to measure performance metrics."""
    times = []

    for _ in range(iterations):
        start = time.perf_counter()
        func(*args, **kwargs)
        end = time.perf_counter()
        times.append(end - start)

    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "min": min(times),
        "max": max(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        "p95": sorted(times)[int(0.95 * len(times))],
        "p99": sorted(times)[int(0.99 * len(times))],
    }


def assert_performance_requirements(
    metrics: dict[str, float], max_mean: float, max_p95: float
):
    """Assert performance requirements are met."""
    assert (
        metrics["mean"] < max_mean
    ), f"Mean time {metrics['mean']:.6f}s exceeds {max_mean:.6f}s"
    assert (
        metrics["p95"] < max_p95
    ), f"P95 time {metrics['p95']:.6f}s exceeds {max_p95:.6f}s"

    # Additional checks
    assert metrics["max"] < max_p95 * 2, "Maximum time too high"
    assert (
        metrics["stdev"] < max_mean
    ), "Standard deviation too high (inconsistent performance)"
