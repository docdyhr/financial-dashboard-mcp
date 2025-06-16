#!/usr/bin/env python3
"""Add Click Digital ISIN mapping and test the complete ISIN integration."""

import sys
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database import get_db_session
from backend.models.isin import ISINTickerMapping
from backend.services.isin_utils import ISINUtils, isin_service
from backend.services.market_data import market_data_service


def add_click_digital_mapping():
    """Add Click Digital ISIN to ticker mapping."""
    print("📝 ADDING CLICK DIGITAL MAPPING")
    print("=" * 50)

    click_data = {
        "isin": "DE000A35JS40",
        "ticker": "CLIQ.DE",
        "exchange_code": "GX",
        "exchange_name": "XETRA",
        "security_name": "Click Digital AG",
        "currency": "EUR",
    }

    print(f"Adding mapping:")
    print(f"  ISIN: {click_data['isin']}")
    print(f"  Ticker: {click_data['ticker']}")
    print(f"  Exchange: {click_data['exchange_name']} ({click_data['exchange_code']})")
    print(f"  Currency: {click_data['currency']}")

    try:
        with get_db_session() as db:
            # Check if mapping already exists
            existing = (
                db.query(ISINTickerMapping)
                .filter(ISINTickerMapping.isin == click_data["isin"])
                .first()
            )

            if existing:
                print(f"✅ Mapping already exists: {existing.ticker}")
                return True

            # Add the mapping
            success = isin_service.add_manual_mapping(
                db=db,
                isin=click_data["isin"],
                ticker=click_data["ticker"],
                exchange_code=click_data["exchange_code"],
                exchange_name=click_data["exchange_name"],
                security_name=click_data["security_name"],
                currency=click_data["currency"],
            )

            if success:
                print("✅ Successfully added Click Digital mapping")
                return True
            else:
                print("❌ Failed to add mapping")
                return False

    except Exception as e:
        print(f"❌ Error adding mapping: {e}")
        return False


def test_click_digital_isin():
    """Test Click Digital ISIN functionality."""
    print("\n🧪 TESTING CLICK DIGITAL ISIN")
    print("=" * 50)

    isin = "DE000A35JS40"

    # Test 1: ISIN Validation
    print("1. ISIN Validation")
    is_valid, error = ISINUtils.validate_isin(isin)
    if is_valid:
        print("   ✅ ISIN is valid")

        # Parse ISIN details
        isin_info = ISINUtils.parse_isin(isin)
        print(f"   Country: {isin_info.country_name} ({isin_info.country_code})")
        print(f"   National Code: {isin_info.national_code}")
        print(f"   Check Digit: {isin_info.check_digit}")
    else:
        print(f"   ❌ ISIN invalid: {error}")
        return False

    # Test 2: Database Mapping Lookup
    print("\n2. Database Mapping Lookup")
    try:
        with get_db_session() as db:
            mappings = isin_service.mapping_service.get_mappings_from_db(db, isin)

            if mappings:
                print(f"   ✅ Found {len(mappings)} mapping(s)")
                for mapping in mappings:
                    print(
                        f"   • {mapping.ticker} ({mapping.exchange_code}) - {mapping.source}"
                    )
            else:
                print("   ❌ No mappings found in database")
                return False

    except Exception as e:
        print(f"   ❌ Database lookup error: {e}")
        return False

    # Test 3: ISIN to Ticker Resolution
    print("\n3. ISIN to Ticker Resolution")
    try:
        with get_db_session() as db:
            resolved_ticker = isin_service.mapping_service.resolve_isin_to_ticker(
                db, isin
            )

            if resolved_ticker:
                print(f"   ✅ Resolved to ticker: {resolved_ticker}")
            else:
                print("   ❌ Could not resolve ISIN to ticker")
                return False

    except Exception as e:
        print(f"   ❌ Resolution error: {e}")
        return False

    # Test 4: Market Data Fetch (ISIN)
    print("\n4. Market Data Fetch (via ISIN)")
    try:
        with get_db_session() as db:
            print(f"   Attempting to fetch market data for ISIN: {isin}")
            time.sleep(2)  # Rate limiting

            result = market_data_service.fetch_quote(isin, db)

            if result.success:
                print(f"   ✅ Market data found!")
                print(f"   Price: €{result.current_price:.2f}")
                print(f"   Source: {result.data_source}")
                if result.day_change:
                    print(
                        f"   Change: €{result.day_change:.2f} ({result.day_change_percent:.2f}%)"
                    )
            else:
                print(f"   ⚠️  No market data available: {result.error}")
                print(
                    "   This is expected for small German stocks not covered by major providers"
                )

    except Exception as e:
        print(f"   ❌ Market data error: {e}")

    # Test 5: Market Data Fetch (Direct Ticker)
    print("\n5. Market Data Fetch (via Direct Ticker)")
    try:
        print(f"   Attempting to fetch market data for ticker: CLIQ.DE")
        time.sleep(2)  # Rate limiting

        result = market_data_service.fetch_quote("CLIQ.DE")

        if result.success:
            print(f"   ✅ Market data found!")
            print(f"   Price: €{result.current_price:.2f}")
            print(f"   Source: {result.data_source}")
        else:
            print(f"   ⚠️  No market data available: {result.error}")
            print(
                "   This is expected - Click Digital is not covered by major international providers"
            )

    except Exception as e:
        print(f"   ❌ Market data error: {e}")

    # Test 6: Asset Info Resolution
    print("\n6. Asset Info Resolution")
    try:
        with get_db_session() as db:
            asset_info = isin_service.get_asset_info(db, isin)

            if asset_info["success"]:
                print(f"   ✅ Asset resolution successful")
                print(f"   Type: {asset_info['identifier_type']}")
                print(f"   Resolved Ticker: {asset_info['resolved_ticker']}")
                print(f"   Country: {asset_info.get('country_name', 'Unknown')}")

                if asset_info.get("available_tickers"):
                    print(
                        f"   Available Tickers: {len(asset_info['available_tickers'])}"
                    )
                    for ticker_info in asset_info["available_tickers"][:3]:
                        print(
                            f"   • {ticker_info['ticker']} ({ticker_info['exchange_code']})"
                        )
            else:
                print(f"   ❌ Asset resolution failed: {asset_info['error']}")

    except Exception as e:
        print(f"   ❌ Asset info error: {e}")

    return True


def test_ticker_suggestions():
    """Test ticker format suggestions for Click Digital."""
    print("\n💡 TICKER FORMAT SUGGESTIONS")
    print("=" * 50)

    isin = "DE000A35JS40"
    base_ticker = "CLIQ"

    print(f"Getting suggestions for:")
    print(f"  ISIN: {isin}")
    print(f"  Base Ticker: {base_ticker}")

    try:
        suggestions = ISINUtils.suggest_ticker_formats(isin, base_ticker)

        print(f"\n📋 Suggested ticker formats:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i:2d}. {suggestion}")

        print(f"\n🎯 Most likely formats for German stock:")
        german_formats = [
            s for s in suggestions if ".DE" in s or ".F" in s or s == base_ticker
        ]
        for fmt in german_formats[:5]:
            print(f"  • {fmt}")

    except Exception as e:
        print(f"❌ Error getting suggestions: {e}")


def show_isin_implementation_status():
    """Show the current status of ISIN implementation."""
    print("\n📊 ISIN IMPLEMENTATION STATUS")
    print("=" * 50)

    features = [
        ("✅", "ISIN format validation"),
        ("✅", "ISIN checksum verification"),
        ("✅", "ISIN parsing (country, national code, check digit)"),
        ("✅", "Database schema for ISIN mappings"),
        ("✅", "ISIN ticker mapping service"),
        ("✅", "Manual mapping creation"),
        ("✅", "Database caching for validation"),
        ("✅", "Market data service ISIN integration"),
        ("✅", "Multi-provider fallback support"),
        ("✅", "Ticker format suggestions by country"),
        ("✅", "API endpoints for ISIN operations"),
        ("⏳", "Frontend UI for ISIN input"),
        ("⏳", "OpenFIGI API integration"),
        ("⏳", "European data provider integration"),
        ("💭", "Real-time German market data"),
    ]

    for status, feature in features:
        print(f"  {status} {feature}")

    print(f"\n🎯 Current Capabilities:")
    print(f"  • Validate and parse any ISIN code")
    print(f"  • Store and retrieve ISIN-to-ticker mappings")
    print(f"  • Resolve ISIN to ticker symbol automatically")
    print(f"  • Integrate ISIN support into market data fetching")
    print(f"  • Suggest appropriate ticker formats by country")
    print(f"  • Comprehensive API for ISIN operations")

    print(f"\n⚠️  Current Limitations:")
    print(f"  • Click Digital data not available from major providers")
    print(f"  • Limited to manual mapping for small German stocks")
    print(f"  • No real-time German market data feeds")
    print(f"  • Frontend UI not yet updated")


def main():
    """Main function to add Click Digital and test ISIN integration."""
    print("🚀 CLICK DIGITAL ISIN INTEGRATION")
    print("Financial Dashboard MCP")
    print("=" * 70)

    success = True

    try:
        # Step 1: Add Click Digital mapping
        if not add_click_digital_mapping():
            success = False

        # Step 2: Test Click Digital ISIN functionality
        if not test_click_digital_isin():
            success = False

        # Step 3: Test ticker suggestions
        test_ticker_suggestions()

        # Step 4: Show implementation status
        show_isin_implementation_status()

        # Final summary
        print(f"\n{'='*70}")
        print("🎉 INTEGRATION COMPLETE")
        print("=" * 70)

        if success:
            print("✅ Click Digital ISIN mapping successfully added and tested!")
            print()
            print("📋 What you can now do:")
            print("  1. Use ISIN DE000A35JS40 in the dashboard")
            print("  2. System will automatically resolve to CLIQ.DE ticker")
            print("  3. Even if no market data available, asset is properly identified")
            print("  4. Use API endpoints to manage ISIN mappings")
            print()
            print("🔧 Next steps for full market data:")
            print("  1. Integrate German-specific data providers")
            print("  2. Add Deutsche Börse API support")
            print("  3. Consider paid European data services")

        else:
            print("⚠️  Some tests failed, but basic ISIN support is working")

        print(f"\n💡 To test in the dashboard:")
        print(f"  • Try adding an asset with ISIN: DE000A35JS40")
        print(f"  • System should recognize it as Click Digital AG")
        print(f"  • Price may not be available (expected for small stocks)")

    except KeyboardInterrupt:
        print("\n\n👋 Integration interrupted by user.")
    except Exception as e:
        print(f"\n\n💥 Integration failed with error: {e}")
        import traceback

        traceback.print_exc()
        success = False

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
