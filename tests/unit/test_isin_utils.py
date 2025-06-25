"""Comprehensive unit tests for ISIN utilities and validation.

This module tests the core ISIN functionality including validation,
parsing, caching, and mapping operations.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from backend.models.isin import ISINValidationCache
from backend.services.isin_utils import (
    ISINMapping,
    ISINMappingService,
    ISINService,
    ISINUtils,
)


class TestISINValidation:
    """Test ISIN validation functionality."""

    def test_validate_valid_isins(self, isin_test_cases):
        """Test validation of valid ISINs."""
        valid_cases = isin_test_cases["valid_cases"]

        for isin, expected_valid, description in valid_cases:
            is_valid, error = ISINUtils.validate_isin(isin)
            assert is_valid == expected_valid, f"Failed for {description}: {isin}"
            assert error is None, f"Unexpected error for valid ISIN {isin}: {error}"

    def test_validate_invalid_isins(self, isin_test_cases):
        """Test validation of invalid ISINs."""
        invalid_cases = isin_test_cases["invalid_cases"]

        for isin, expected_valid, description in invalid_cases:
            is_valid, error = ISINUtils.validate_isin(isin)
            assert is_valid == expected_valid, f"Failed for {description}: {isin}"
            assert error is not None, f"Expected error for invalid ISIN {isin}"
            assert isinstance(error, str), f"Error should be string for {isin}"

    def test_validate_edge_cases(self, isin_test_cases):
        """Test validation of edge case ISINs."""
        edge_cases = isin_test_cases["edge_cases"]

        for isin, expected_valid, description in edge_cases:
            is_valid, error = ISINUtils.validate_isin(isin)
            assert is_valid == expected_valid, f"Failed for {description}: {isin}"

    def test_validate_none_and_empty(self):
        """Test validation with None and empty inputs."""
        # None input
        is_valid, error = ISINUtils.validate_isin(None)
        assert not is_valid
        assert (
            error is not None and len(error) > 0
        ), f"Expected error message for None input, got: {error}"

        # Empty string
        is_valid, error = ISINUtils.validate_isin("")
        assert not is_valid
        assert (
            error is not None and len(error) > 0
        ), f"Expected error message for empty input, got: {error}"

        # Whitespace only
        is_valid, error = ISINUtils.validate_isin("   ")
        assert not is_valid
        assert (
            error is not None and len(error) > 0
        ), f"Expected error message for whitespace input, got: {error}"

    def test_check_digit_calculation(self):
        """Test ISIN check digit calculation."""
        # Known valid ISINs with correct check digits
        test_cases = [
            ("US0378331005", True),  # Apple
            ("DE0007164600", True),  # SAP
            ("GB0002162385", True),  # BP
            ("US0378331006", False),  # Apple with wrong check digit
            ("DE0007164601", False),  # SAP with wrong check digit
        ]

        for isin, expected_valid in test_cases:
            is_valid, check_digit = ISINUtils.validate_isin_checksum(isin)
            assert is_valid == expected_valid, f"Checksum validation failed for {isin}"

    def test_format_normalization(self):
        """Test ISIN format normalization."""
        # Test lowercase conversion - validate_isin should handle it
        is_valid, error = ISINUtils.validate_isin("us0378331005")
        assert is_valid, "Lowercase ISIN should be accepted and normalized"

        # Test whitespace removal
        is_valid, error = ISINUtils.validate_isin(" US0378331005 ")
        assert is_valid, "ISIN with whitespace should be accepted and trimmed"

        # Test mixed case
        is_valid, error = ISINUtils.validate_isin("uS0378331005")
        assert is_valid, "Mixed case ISIN should be accepted and normalized"


class TestISINParsing:
    """Test ISIN parsing functionality."""

    def test_parse_valid_isin(self, sample_isin_data):
        """Test parsing of valid ISINs."""
        valid_isins = sample_isin_data["valid_isins"]

        for isin in valid_isins:
            isin_info = ISINUtils.parse_isin(isin)

            assert isin_info is not None, f"Failed to parse valid ISIN: {isin}"
            assert isin_info.isin == isin
            assert len(isin_info.country_code) == 2
            assert len(isin_info.national_code) == 9
            assert len(isin_info.check_digit) == 1
            assert isin_info.is_valid

    def test_parse_invalid_isin(self, isin_test_cases):
        """Test parsing of invalid ISINs."""
        invalid_cases = isin_test_cases["invalid_cases"]

        for isin, _, description in invalid_cases:
            isin_info = ISINUtils.parse_isin(isin)
            assert not isin_info.is_valid, f"ISIN should be invalid: {description}"
            assert (
                isin_info.validation_error is not None
            ), f"Should have validation error: {description}"

    def test_parse_country_extraction(self):
        """Test country code extraction from ISINs."""
        test_cases = [
            ("US0378331005", "US", "United States"),
            ("DE0007164600", "DE", "Germany"),
            ("GB0002162385", "GB", "United Kingdom"),
            ("FR0000120073", "FR", "France"),
            ("NL0011794037", "NL", "Netherlands"),
        ]

        for isin, expected_country, expected_name in test_cases:
            isin_info = ISINUtils.parse_isin(isin)
            assert isin_info.country_code == expected_country
            # Note: Country name mapping would be tested separately

    def test_parse_national_code_extraction(self):
        """Test national code extraction."""
        isin = "US0378331005"
        isin_info = ISINUtils.parse_isin(isin)

        assert isin_info.national_code == "037833100"
        assert len(isin_info.national_code) == 9

    def test_parse_check_digit_extraction(self):
        """Test check digit extraction."""
        isin = "US0378331005"
        isin_info = ISINUtils.parse_isin(isin)

        assert isin_info.check_digit == "5"


class TestISINMappingService:
    """Test ISIN mapping service functionality."""

    @pytest.fixture
    def mapping_service(self):
        """Create ISIN mapping service instance."""
        return ISINMappingService()

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.rollback = Mock()
        return mock_session

    def test_create_mapping(self, mapping_service, sample_isin_data):
        """Test creating a new ISIN mapping."""
        isin = "US0378331005"
        mapping_data = sample_isin_data["isin_mappings"][isin]

        mapping = ISINMapping(
            isin=isin,
            ticker=mapping_data["ticker"],
            exchange_code=mapping_data["exchange"],
            exchange_name="NASDAQ",
            security_name=mapping_data["name"],
            currency=mapping_data["currency"],
            source="test",
            confidence=0.95,
        )

        assert mapping.isin == isin
        assert mapping.ticker == mapping_data["ticker"]
        assert mapping.exchange_code == mapping_data["exchange"]
        assert mapping.confidence == 0.95

    def test_mapping_validation(self, mapping_service):
        """Test mapping validation."""
        # Valid mapping
        valid_mapping = ISINMapping(
            isin="US0378331005",
            ticker="AAPL",
            exchange_code="XNAS",
            exchange_name="NASDAQ",
            security_name="Apple Inc.",
            currency="USD",
            source="test",
            confidence=0.95,
        )

        is_valid, errors = mapping_service.validate_mapping(valid_mapping)
        assert is_valid
        assert len(errors) == 0

        # Invalid mapping - bad ISIN
        invalid_mapping = ISINMapping(
            isin="INVALID",
            ticker="AAPL",
            exchange_code="XNAS",
            exchange_name="NASDAQ",
            security_name="Apple Inc.",
            currency="USD",
            source="test",
            confidence=0.95,
        )

        is_valid, errors = mapping_service.validate_mapping(invalid_mapping)
        assert not is_valid
        assert len(errors) > 0
        assert any("ISIN" in error for error in errors)

    @patch("backend.models.get_db")
    def test_save_mapping_to_db(self, mock_get_db, mapping_service, mock_db_session):
        """Test saving mapping to database."""
        mock_get_db.return_value.__enter__.return_value = mock_db_session

        mapping = ISINMapping(
            isin="US0378331005",
            ticker="AAPL",
            exchange_code="XNAS",
            exchange_name="NASDAQ",
            security_name="Apple Inc.",
            currency="USD",
            source="test",
            confidence=0.95,
        )

        result = mapping_service.save_mapping_to_db(mock_db_session, mapping)

        assert result is True
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @patch("backend.models.get_db")
    def test_get_mappings_from_db(self, mock_get_db, mapping_service, mock_db_session):
        """Test retrieving mappings from database."""
        # Mock database results
        mock_mapping = Mock()
        mock_mapping.isin = "US0378331005"
        mock_mapping.ticker = "AAPL"
        mock_mapping.exchange_code = "XNAS"
        mock_mapping.exchange_name = "NASDAQ"
        mock_mapping.security_name = "Apple Inc."
        mock_mapping.currency = "USD"
        mock_mapping.source = "test"
        mock_mapping.confidence = 0.95
        mock_mapping.is_active = True

        # Set up the mock query chain properly
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_mapping]
        mock_db_session.query.return_value = mock_query
        mock_get_db.return_value.__enter__.return_value = mock_db_session

        mappings = mapping_service.get_mappings_from_db(mock_db_session, "US0378331005")

        assert len(mappings) == 1
        assert mappings[0].isin == "US0378331005"
        assert mappings[0].ticker == "AAPL"


class TestISINService:
    """Test main ISIN service functionality."""

    @pytest.fixture
    def isin_service(self):
        """Create ISIN service instance."""
        return ISINService()

    @patch("backend.models.get_db")
    def test_get_ticker_for_isin(self, mock_get_db, isin_service):
        """Test getting ticker for ISIN."""
        # Mock database session
        mock_session = Mock()
        mock_get_db.return_value = iter([mock_session])

        # Mock the mapping service's get_mappings_from_db method
        mock_mapping = ISINMapping(
            isin="US0378331005",
            ticker="AAPL",
            exchange_code="XNAS",
            exchange_name="NASDAQ",
            security_name="Apple Inc.",
            currency="USD",
            source="test",
            confidence=0.95,
            is_active=True,
        )

        with patch.object(
            isin_service.mapping_service, "get_mappings_from_db"
        ) as mock_get_mappings:
            mock_get_mappings.return_value = [mock_mapping]
            ticker = isin_service.get_ticker_for_isin("US0378331005")
            assert ticker == "AAPL"

    @patch("backend.models.get_db")
    def test_get_ticker_for_isin_not_found(self, mock_get_db, isin_service):
        """Test getting ticker for ISIN when not found."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            None
        )
        mock_get_db.return_value.__enter__.return_value = mock_session

        ticker = isin_service.get_ticker_for_isin("UNKNOWN123")

        assert ticker is None

    def test_suggest_ticker_formats(self, isin_service):
        """Test ticker format suggestions."""
        suggestions = isin_service.suggest_ticker_formats("DE0007164600", "SAP")

        assert len(suggestions) > 0
        assert any(".DE" in suggestion for suggestion in suggestions)  # XETRA format
        assert "SAP" in suggestions  # Base ticker should be included

    @patch("backend.models.get_db")
    def test_resolve_identifier_isin(self, mock_get_db, isin_service):
        """Test resolving ISIN identifier."""
        mock_session = Mock()

        # Mock the mapping service's resolve_isin_to_ticker method
        with patch.object(
            isin_service.mapping_service, "resolve_isin_to_ticker"
        ) as mock_resolve:
            mock_resolve.return_value = "SAP"

            result = isin_service.resolve_identifier(mock_session, "DE0007164600")

            resolved_ticker, identifier_type, isin_info = result

            assert resolved_ticker == "SAP"
            assert identifier_type == "isin"
            assert isin_info is not None
            assert isin_info.country_code == "DE"

    def test_resolve_identifier_ticker(self, isin_service):
        """Test resolving ticker identifier."""
        # For ticker, it should return as-is if no ISIN mapping exists
        mock_session = Mock()
        result = isin_service.resolve_identifier(mock_session, "AAPL")

        resolved_ticker, identifier_type, isin_info = result

        assert resolved_ticker == "AAPL"
        assert identifier_type == "ticker"
        assert isin_info is None


class TestISINValidationCache:
    """Test ISIN validation cache functionality."""

    def test_cache_creation(self, sample_validation_cache):
        """Test creation of validation cache entries."""
        cache_data = sample_validation_cache[0]

        cache_entry = ISINValidationCache.create_from_validation(
            isin=cache_data["isin"],
            is_valid=cache_data["is_valid"],
            country_code=cache_data["country_code"],
            country_name=cache_data["country_name"],
        )

        assert cache_entry.isin == cache_data["isin"]
        assert cache_entry.is_valid == cache_data["is_valid"]
        assert cache_entry.country_code == cache_data["country_code"]

    def test_cache_freshness(self):
        """Test cache freshness checking."""
        # Fresh cache entry
        fresh_entry = ISINValidationCache()
        fresh_entry.cached_at = datetime.now()

        assert fresh_entry.is_fresh(24) is True

        # Stale cache entry
        stale_entry = ISINValidationCache()
        stale_entry.cached_at = datetime.now() - timedelta(hours=25)

        assert stale_entry.is_fresh(24) is False

    def test_cache_validation_error_storage(self):
        """Test storing validation errors in cache."""
        cache_entry = ISINValidationCache.create_from_validation(
            isin="INVALID123", is_valid=False, validation_error="Invalid ISIN format"
        )

        assert cache_entry.isin == "INVALID123"
        assert cache_entry.is_valid is False
        assert cache_entry.validation_error == "Invalid ISIN format"


class TestISINPerformance:
    """Test ISIN operation performance."""

    def test_validation_performance(self, performance_test_data):
        """Test ISIN validation performance."""
        import time

        small_batch = performance_test_data["small_batch"]
        expected_time = performance_test_data["expected_times"]["validation"]

        start_time = time.time()

        for isin in small_batch:
            ISINUtils.validate_isin(isin)

        elapsed_time = time.time() - start_time
        avg_time = elapsed_time / len(small_batch)

        # Allow 10x slower than expected for test environment
        assert avg_time < (
            expected_time * 10
        ), f"Validation too slow: {avg_time}s per ISIN"

    def test_batch_validation_performance(self, performance_test_data):
        """Test batch validation performance."""
        import time

        medium_batch = performance_test_data["medium_batch"][
            :50
        ]  # Use smaller batch for tests

        start_time = time.time()

        results = []
        for isin in medium_batch:
            is_valid, error = ISINUtils.validate_isin(isin)
            results.append((is_valid, error))

        elapsed_time = time.time() - start_time

        # Should process 50 ISINs in reasonable time
        assert (
            elapsed_time < 5.0
        ), f"Batch validation too slow: {elapsed_time}s for {len(medium_batch)} ISINs"
        assert len(results) == len(medium_batch)


class TestISINErrorHandling:
    """Test error handling in ISIN operations."""

    def test_invalid_input_types(self):
        """Test handling of invalid input types."""
        invalid_inputs = [123, [], {}, object(), True, False]

        for invalid_input in invalid_inputs:
            is_valid, error = ISINUtils.validate_isin(invalid_input)
            assert not is_valid
            assert error is not None

    def test_database_error_handling(self):
        """Test handling of database errors."""
        # Create a real service instance for this test
        real_service = ISINService()

        with patch("backend.models.get_db") as mock_get_db:
            # Simulate database connection error
            mock_get_db.side_effect = Exception("Database connection failed")

            # Should handle error gracefully
            ticker = real_service.get_ticker_for_isin("US0378331005")
            assert ticker is None

    def test_external_api_error_handling(self, mapping_service):
        """Test handling of external API errors."""
        # This would test error handling for external data provider APIs
        # when they're unavailable or return errors
        # Placeholder for external API error testing

    def test_malformed_data_handling(self):
        """Test handling of malformed data."""
        malformed_isins = [
            "US0378331005EXTRA",  # Too long with extra characters
            "US037833100\n5",  # Contains newline
            "US037833100\x005",  # Contains null byte
            "US037833100\t5",  # Contains tab
        ]

        for malformed_isin in malformed_isins:
            is_valid, error = ISINUtils.validate_isin(malformed_isin)
            assert not is_valid
            assert error is not None


class TestISINUtilsIntegration:
    """Integration tests for ISIN utilities."""

    @pytest.mark.integration
    def test_end_to_end_isin_processing(self, sample_isin_data):
        """Test complete ISIN processing workflow."""
        isin = "US0378331005"

        # Step 1: Validate ISIN
        is_valid, error = ISINUtils.validate_isin(isin)
        assert is_valid
        assert error is None

        # Step 2: Parse ISIN
        isin_info = ISINUtils.parse_isin(isin)
        assert isin_info.isin == isin
        assert isin_info.country_code == "US"

        # Step 3: Create mapping
        mapping = ISINMapping(
            isin=isin,
            ticker="AAPL",
            exchange_code="XNAS",
            exchange_name="NASDAQ",
            security_name="Apple Inc.",
            currency="USD",
            source="test",
            confidence=0.95,
        )

        assert mapping.isin == isin
        assert mapping.ticker == "AAPL"

    @pytest.mark.integration
    def test_bulk_processing(self, sample_isin_data):
        """Test bulk ISIN processing."""
        valid_isins = sample_isin_data["valid_isins"]

        results = []
        for isin in valid_isins:
            is_valid, error = ISINUtils.validate_isin(isin)
            results.append((isin, is_valid, error))

        # All should be valid
        valid_count = sum(1 for _, is_valid, _ in results if is_valid)
        assert valid_count == len(valid_isins)


# Performance benchmarks (optional, run with specific markers)
@pytest.mark.benchmark
class TestISINBenchmarks:
    """Benchmark tests for ISIN operations."""

    def test_validation_benchmark(self, benchmark, sample_isin_data):
        """Benchmark ISIN validation performance."""
        isin = sample_isin_data["valid_isins"][0]

        result = benchmark(ISINUtils.validate_isin, isin)
        assert result[0] is True  # Should be valid

    def test_parsing_benchmark(self, benchmark, sample_isin_data):
        """Benchmark ISIN parsing performance."""
        isin = sample_isin_data["valid_isins"][0]

        result = benchmark(ISINUtils.parse_isin, isin)
        assert result.isin == isin


# Regression tests
class TestISINRegression:
    """Regression tests for previously fixed bugs."""

    def test_check_digit_edge_cases(self):
        """Test check digit calculation edge cases."""
        # Previously failed cases that should now work
        edge_case_isins = [
            "US0000000000",  # All zeros in national code
            "US9999999999",  # All nines in national code
            "XS0000000000",  # International securities
        ]

        for isin in edge_case_isins:
            # Should not raise exception during validation
            try:
                is_valid, error = ISINUtils.validate_isin(isin)
                # Result doesn't matter, just shouldn't crash
            except Exception as e:
                pytest.fail(f"Validation crashed for {isin}: {e}")

    def test_unicode_handling(self):
        """Test handling of Unicode characters in ISINs."""
        unicode_isins = [
            "US0378331005",  # Normal ASCII
            "US0378331005",  # With Unicode spaces (U+2000)
            "ＵＳ０３７８３３１００５",  # Full-width characters
        ]

        for isin in unicode_isins:
            try:
                is_valid, error = ISINUtils.validate_isin(isin)
                # Should handle gracefully, not crash
            except UnicodeError:
                pytest.fail(f"Unicode error for ISIN: {isin}")
