#!/usr/bin/env python3
"""Comprehensive ISIN integration test script for Financial Dashboard."""

from pathlib import Path
import sys
import time

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database import get_db_session
from backend.models.isin import ISINTickerMapping
from backend.schemas.isin import ISINMappingCreate
from backend.services.isin_utils import ISINUtils, isin_service
from backend.services.market_data import market_data_service


def test_isin_validation():
    """Test ISIN validation functionality."""
    print("🧪 ISIN VALIDATION TESTS")
    print("=" * 60)

    test_cases = [
        ("DE000A35JS40", True, "Click Digital (Germany)"),
        ("US0378331005", True, "Apple Inc. (USA)"),
        ("GB0002162385", True, "BP plc (UK)"),
        ("FR0000120271", True, "Total SA (France)"),
        ("NL0000009165", True, "Unilever NV (Netherlands)"),
        ("CH0038863350", True, "Nestlé SA (Switzerland)"),
        ("INVALID12345", False, "Invalid format"),
        ("DE000A35JS41", False, "Wrong checksum"),
        ("", False, "Empty string"),
        ("TOOSHORT", False, "Too short"),
    ]

    passed = 0
    failed = 0

    for isin, expected_valid, description in test_cases:
        try:
            is_valid, error = ISINUtils.validate_isin(isin, use_cache=False)
            status = "✅" if is_valid == expected_valid else "❌"

            print(f"{status} {isin:12} | {description}")

            if is_valid == expected_valid:
                passed += 1
                if is_valid:
                    isin_info = ISINUtils.parse_isin(isin)
                    print(
                        f"   Country: {isin_info.country_name} ({isin_info.country_code})"
                    )
                    print(f"   National Code: {isin_info.national_code}")
            else:
                failed += 1
                print(f"   Expected: {expected_valid}, Got: {is_valid}")
                if error:
                    print(f"   Error: {error}")
        except Exception as e:
            failed += 1
            print(f"❌ {isin:12} | Exception: {e}")

    print(f"\n📊 Validation Results: {passed} passed, {failed} failed")
    return failed == 0


def test_isin_parsing():
    """Test ISIN parsing functionality."""
    print("\n🔍 ISIN PARSING TESTS")
    print("=" * 60)

    test_isins = [
        "DE000A35JS40",  # Click Digital
        "US0378331005",  # Apple
        "GB0002162385",  # BP
        "FR0000120271",  # Total
        "JP3633400001",  # SoftBank
    ]

    for isin in test_isins:
        print(f"\nParsing: {isin}")
        print("-" * 30)

        isin_info = ISINUtils.parse_isin(isin)

        if isin_info.is_valid:
            print("✅ Valid ISIN")
            print(f"   Country: {isin_info.country_name} ({isin_info.country_code})")
            print(f"   National Code: {isin_info.national_code}")
            print(f"   Check Digit: {isin_info.check_digit}")

            # Test ticker suggestions
            suggestions = ISINUtils.suggest_ticker_formats(isin, "TEST")
            print(f"   Suggested formats: {', '.join(suggestions[:3])}")
        else:
            print(f"❌ Invalid: {isin_info.validation_error}")


def test_database_operations():
    """Test ISIN database operations."""
    print("\n💾 DATABASE OPERATIONS TESTS")
    print("=" * 60)

    try:
        with get_db_session() as db:
            # Test mapping creation
            print("Testing mapping creation...")

            test_mapping = ISINMappingCreate(
                isin="DE000A35JS40",
                ticker="CLIQ.DE",
                exchange_code="GX",
                exchange_name="XETRA",
                security_name="Click Digital AG",
                currency="EUR",
                source="test",
                confidence=0.95,
            )

            # Add mapping using service
            success = isin_service.add_manual_mapping(
                db=db,
                isin=test_mapping.isin,
                ticker=test_mapping.ticker,
                exchange_code=test_mapping.exchange_code,
                exchange_name=test_mapping.exchange_name,
                security_name=test_mapping.security_name,
                currency=test_mapping.currency,
            )

            if success:
                print("✅ Successfully created test mapping")

                # Test retrieval
                mappings = isin_service.mapping_service.get_mappings_from_db(
                    db, test_mapping.isin
                )

                if mappings:
                    print(f"✅ Retrieved {len(mappings)} mappings")
                    for mapping in mappings:
                        print(
                            f"   {mapping.ticker} ({mapping.exchange_code}) - {mapping.confidence}"
                        )
                else:
                    print("❌ No mappings retrieved")

                # Test resolution
                resolved_ticker = isin_service.mapping_service.resolve_isin_to_ticker(
                    db, test_mapping.isin
                )

                if resolved_ticker:
                    print(f"✅ Resolved to ticker: {resolved_ticker}")
                else:
                    print("❌ Failed to resolve ISIN to ticker")

                # Clean up test data
                db.query(ISINTickerMapping).filter(
                    ISINTickerMapping.isin == test_mapping.isin,
                    ISINTickerMapping.source == "test",
                ).delete()
                db.commit()
                print("✅ Cleaned up test data")

            else:
                print("❌ Failed to create test mapping")

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

    return True


def test_market_data_integration():
    """Test ISIN integration with market data service."""
    print("\n📈 MARKET DATA INTEGRATION TESTS")
    print("=" * 60)

    test_cases = [
        ("US0378331005", "AAPL", "Apple - should work with ISIN"),
        ("DE000A35JS40", "CLIQ.DE", "Click Digital - might not have data"),
        ("AAPL", "AAPL", "Regular ticker - should work"),
        ("INVALID", "INVALID", "Invalid ticker - should fail"),
    ]

    with get_db_session() as db:
        # First, add a test mapping for Click Digital
        try:
            isin_service.add_manual_mapping(
                db=db,
                isin="DE000A35JS40",
                ticker="CLIQ.DE",
                exchange_code="GX",
                exchange_name="XETRA",
                security_name="Click Digital AG",
                currency="EUR",
            )
            print("✅ Added test mapping for Click Digital")
        except Exception as e:
            print(f"⚠️  Could not add test mapping: {e}")

        for identifier, expected_ticker, description in test_cases:
            print(f"\nTesting: {identifier} ({description})")
            print("-" * 50)

            try:
                # Add delay to respect rate limits
                time.sleep(2)

                result = market_data_service.fetch_quote(identifier, db)

                if result.success:
                    print(f"✅ Success - Price: ${result.current_price:.2f}")
                    print(f"   Data Source: {result.data_source}")
                    if result.day_change:
                        print(
                            f"   Change: ${result.day_change:.2f} ({result.day_change_percent:.2f}%)"
                        )
                else:
                    print(f"❌ Failed: {result.error}")
                    if hasattr(result, "suggestions") and result.suggestions:
                        print(f"   Suggestions: {', '.join(result.suggestions[:3])}")

            except Exception as e:
                print(f"❌ Exception: {e}")

        # Clean up test data
        try:
            db.query(ISINTickerMapping).filter(
                ISINTickerMapping.isin == "DE000A35JS40",
                ISINTickerMapping.source == "manual",
            ).delete()
            db.commit()
            print("\n✅ Cleaned up test mappings")
        except Exception as e:
            print(f"⚠️  Could not clean up: {e}")


def test_identifier_resolution():
    """Test identifier resolution functionality."""
    print("\n🔄 IDENTIFIER RESOLUTION TESTS")
    print("=" * 60)

    test_cases = [
        "US0378331005",  # Apple ISIN
        "AAPL",  # Apple ticker
        "DE000A35JS40",  # Click Digital ISIN (might not resolve)
        "CLIQ.DE",  # Click Digital ticker
        "INVALID",  # Invalid identifier
        "BADISISN123",  # Looks like ISIN but invalid
    ]

    with get_db_session() as db:
        for identifier in test_cases:
            print(f"\nResolving: {identifier}")
            print("-" * 30)

            try:
                asset_info = isin_service.get_asset_info(db, identifier)

                if asset_info["success"]:
                    print("✅ Success")
                    print(f"   Type: {asset_info['identifier_type']}")
                    print(f"   Resolved: {asset_info['resolved_ticker']}")

                    if asset_info.get("country_name"):
                        print(f"   Country: {asset_info['country_name']}")

                    if asset_info.get("available_tickers"):
                        print(
                            f"   Available tickers: {len(asset_info['available_tickers'])}"
                        )
                else:
                    print(f"❌ Failed: {asset_info['error']}")
                    print(f"   Error type: {asset_info.get('error_type', 'unknown')}")

            except Exception as e:
                print(f"❌ Exception: {e}")


def test_click_digital_specific():
    """Test specific Click Digital ISIN case."""
    print("\n🎯 CLICK DIGITAL SPECIFIC TESTS")
    print("=" * 60)

    click_isin = "DE000A35JS40"
    click_wkn = "A35JS4"

    print("Testing Click Digital:")
    print(f"  ISIN: {click_isin}")
    print(f"  WKN: {click_wkn}")
    print("  Expected Ticker: CLIQ.DE")
    print()

    # Validate ISIN
    is_valid, error = ISINUtils.validate_isin(click_isin)
    print(f"ISIN Validation: {'✅ Valid' if is_valid else f'❌ Invalid - {error}'}")

    if is_valid:
        # Parse ISIN
        isin_info = ISINUtils.parse_isin(click_isin)
        print(f"Country: {isin_info.country_name} ({isin_info.country_code})")
        print(f"National Code: {isin_info.national_code}")

        # Test ticker suggestions
        suggestions = ISINUtils.suggest_ticker_formats(click_isin, "CLIQ")
        print("Suggested ticker formats:")
        for i, suggestion in enumerate(suggestions[:5], 1):
            print(f"  {i}. {suggestion}")

        # Test with market data
        with get_db_session() as db:
            print("\nTesting market data fetch...")

            # Add manual mapping
            try:
                isin_service.add_manual_mapping(
                    db=db,
                    isin=click_isin,
                    ticker="CLIQ.DE",
                    exchange_code="GX",
                    exchange_name="XETRA",
                    security_name="Click Digital AG",
                    currency="EUR",
                )
                print("✅ Added manual mapping")
            except Exception as e:
                print(f"⚠️  Mapping already exists or error: {e}")

            # Test resolution
            try:
                time.sleep(2)  # Rate limiting
                result = market_data_service.fetch_quote(click_isin, db)

                if result.success:
                    print(f"✅ Market data found: €{result.current_price:.2f}")
                    print(f"   Source: {result.data_source}")
                else:
                    print(f"❌ No market data: {result.error}")
                    print("   This is expected for small German stocks")

            except Exception as e:
                print(f"❌ Market data error: {e}")

            # Clean up
            try:
                db.query(ISINTickerMapping).filter(
                    ISINTickerMapping.isin == click_isin
                ).delete()
                db.commit()
                print("✅ Cleaned up test data")
            except Exception as e:
                print(f"⚠️  Cleanup warning: {e}")


def run_performance_tests():
    """Run performance tests for ISIN operations."""
    print("\n⚡ PERFORMANCE TESTS")
    print("=" * 60)

    # Test validation performance
    test_isins = [
        "DE000A35JS40",
        "US0378331005",
        "GB0002162385",
        "FR0000120271",
        "NL0000009165",
        "CH0038863350",
        "JP3633400001",
        "AU000000CBA7",
        "CA0679011084",
    ] * 10  # 90 ISINs total

    print(f"Testing validation performance with {len(test_isins)} ISINs...")

    start_time = time.time()
    for isin in test_isins:
        ISINUtils.validate_isin(isin, use_cache=False)
    end_time = time.time()

    validation_time = end_time - start_time
    print(
        f"✅ Validation: {validation_time:.3f}s ({len(test_isins)/validation_time:.1f} ISINs/sec)"
    )

    # Test caching performance
    print("\nTesting cached validation...")
    start_time = time.time()
    for isin in test_isins:
        ISINUtils.validate_isin(isin, use_cache=True)
    end_time = time.time()

    cached_time = end_time - start_time
    print(
        f"✅ Cached validation: {cached_time:.3f}s ({len(test_isins)/cached_time:.1f} ISINs/sec)"
    )
    print(f"   Speedup: {validation_time/cached_time:.1f}x faster with caching")


def main():
    """Run all ISIN integration tests."""
    print("🚀 ISIN INTEGRATION TEST SUITE")
    print("Financial Dashboard MCP")
    print("=" * 80)

    tests = [
        ("ISIN Validation", test_isin_validation),
        ("ISIN Parsing", test_isin_parsing),
        ("Database Operations", test_database_operations),
        ("Market Data Integration", test_market_data_integration),
        ("Identifier Resolution", test_identifier_resolution),
        ("Click Digital Specific", test_click_digital_specific),
        ("Performance Tests", run_performance_tests),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n{'='*80}")
        print(f"🧪 RUNNING: {test_name}")
        print("=" * 80)

        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    # Final summary
    print(f"\n{'='*80}")
    print("📊 FINAL TEST RESULTS")
    print("=" * 80)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! ISIN integration is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Check the output above for details.")

    print("\n💡 IMPLEMENTATION STATUS:")
    print("✅ ISIN validation and parsing")
    print("✅ Database schema and models")
    print("✅ Market data service integration")
    print("✅ API endpoints (not tested here)")
    print("⏳ Frontend integration (pending)")
    print("⏳ External data provider integration (partial)")

    return failed == 0


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Tests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Test suite failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
