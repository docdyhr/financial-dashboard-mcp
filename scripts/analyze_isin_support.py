#!/usr/bin/env python3
"""Analyze ISIN support feasibility for the Financial Dashboard, specifically for CLIQ.DE/Click Digital."""

import sys
import time
from pathlib import Path

import requests

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def validate_isin(isin: str) -> tuple[bool, str]:
    """Validate ISIN format and checksum."""
    if not isin or len(isin) != 12:
        return False, "ISIN must be exactly 12 characters"

    # Check format: 2 letter country code + 9 alphanumeric + 1 check digit
    if not isin[:2].isalpha() or not isin[2:11].isalnum() or not isin[11].isdigit():
        return (
            False,
            "Invalid ISIN format (should be: 2 letters + 9 alphanumeric + 1 digit)",
        )

    # Simple checksum validation (Luhn algorithm for ISINs)
    # Convert letters to numbers (A=10, B=11, etc.)
    converted = ""
    for char in isin[:-1]:  # Exclude check digit
        if char.isalpha():
            converted += str(ord(char.upper()) - ord("A") + 10)
        else:
            converted += char

    # Apply Luhn algorithm
    total = 0
    for i, digit in enumerate(reversed(converted)):
        n = int(digit)
        if i % 2 == 0:  # Every second digit from right
            n *= 2
            if n > 9:
                n = n // 10 + n % 10
        total += n

    check_digit = (10 - (total % 10)) % 10
    is_valid = str(check_digit) == isin[11]

    return is_valid, (
        "Valid ISIN"
        if is_valid
        else f"Invalid checksum (expected {check_digit}, got {isin[11]})"
    )


def parse_isin(isin: str) -> dict:
    """Parse ISIN components."""
    if len(isin) != 12:
        return {"error": "Invalid ISIN length"}

    country_codes = {
        "DE": "Germany",
        "US": "United States",
        "GB": "United Kingdom",
        "FR": "France",
        "IT": "Italy",
        "ES": "Spain",
        "NL": "Netherlands",
        "CH": "Switzerland",
        "AT": "Austria",
        "BE": "Belgium",
        "SE": "Sweden",
        "DK": "Denmark",
        "NO": "Norway",
        "FI": "Finland",
        "IE": "Ireland",
        "LU": "Luxembourg",
        "PT": "Portugal",
        "GR": "Greece",
        "CA": "Canada",
        "JP": "Japan",
        "AU": "Australia",
        "HK": "Hong Kong",
        "SG": "Singapore",
    }

    return {
        "isin": isin,
        "country_code": isin[:2],
        "country_name": country_codes.get(isin[:2], "Unknown"),
        "national_code": isin[2:11],
        "check_digit": isin[11],
        "is_german": isin.startswith("DE"),
    }


def test_openfigi_api(isin: str) -> dict:
    """Test OpenFIGI API for ISIN to ticker mapping."""
    try:
        url = "https://api.openfigi.com/v3/mapping"
        headers = {
            "Content-Type": "application/json",
            "X-OPENFIGI-APIKEY": "",  # Free tier doesn't require API key
        }

        payload = [
            {
                "idType": "ID_ISIN",
                "idValue": isin,
                "exchCode": "GX",  # XETRA exchange code
            }
        ]

        response = requests.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0 and "data" in data[0]:
                results = data[0]["data"]
                return {"success": True, "results": results, "count": len(results)}
            else:
                return {
                    "success": False,
                    "error": "No mapping data found",
                    "response": data,
                }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
            }

    except Exception as e:
        return {"success": False, "error": f"Exception: {str(e)}"}


def test_isin_to_ticker_services(isin: str) -> dict:
    """Test various ISIN to ticker mapping services."""
    results = {}

    print(f"Testing ISIN to ticker mapping services for {isin}...")

    # Test OpenFIGI (free)
    print("  • Testing OpenFIGI API...")
    openfigi_result = test_openfigi_api(isin)
    results["openfigi"] = openfigi_result

    if openfigi_result["success"]:
        print(f"    ✓ Success: Found {openfigi_result['count']} mappings")
        for i, result in enumerate(openfigi_result["results"][:3]):  # Show first 3
            ticker = result.get("ticker", "N/A")
            exchange = result.get("exchCode", "N/A")
            name = result.get("name", "N/A")
            print(f"      {i+1}. {ticker} ({exchange}) - {name}")
    else:
        print(f"    ✗ Failed: {openfigi_result['error']}")

    time.sleep(1)  # Rate limiting

    return results


def analyze_click_digital_case():
    """Analyze the specific case of Click Digital (CLIQ.DE)."""
    print("🔍 CLICK DIGITAL (CLIQ.DE) ISIN ANALYSIS")
    print("=" * 60)

    isin = "DE000A35JS40"
    wkn = "A35JS4"
    ticker = "CLIQ.DE"

    print(f"Target Security:")
    print(f"  Company: Click Digital")
    print(f"  ISIN: {isin}")
    print(f"  WKN: {wkn}")
    print(f"  Expected Ticker: {ticker}")
    print(f"  Exchange: XETRA (Germany)")
    print()

    # Step 1: Validate ISIN
    print("1. ISIN VALIDATION")
    print("-" * 30)
    is_valid, message = validate_isin(isin)
    print(f"ISIN: {isin}")
    print(f"Valid: {is_valid}")
    print(f"Message: {message}")

    if is_valid:
        isin_info = parse_isin(isin)
        print(f"Country: {isin_info['country_name']} ({isin_info['country_code']})")
        print(f"National Code: {isin_info['national_code']}")
        print(f"Check Digit: {isin_info['check_digit']}")
    print()

    # Step 2: Test ISIN mapping services
    print("2. ISIN TO TICKER MAPPING")
    print("-" * 30)
    mapping_results = test_isin_to_ticker_services(isin)
    print()

    # Step 3: Analysis and recommendations
    print("3. ANALYSIS & RECOMMENDATIONS")
    print("-" * 30)

    # Check if we found any mappings
    found_mappings = False
    if mapping_results.get("openfigi", {}).get("success"):
        found_mappings = True
        print("✓ ISIN mapping service found ticker mappings")
    else:
        print("✗ No ticker mappings found via ISIN services")

    print()
    print("ISIN Support Assessment:")
    print()

    if found_mappings:
        print("✅ ISIN SUPPORT RECOMMENDED")
        print("   Reasons:")
        print("   • ISIN to ticker mapping services work")
        print("   • Could resolve ticker lookup issues")
        print("   • Provides alternative data source path")
        print("   • More reliable for European securities")
    else:
        print("⚠️  ISIN SUPPORT HAS LIMITED VALUE")
        print("   Reasons:")
        print("   • Free ISIN mapping services don't cover this security")
        print("   • Would require paid services for comprehensive coverage")
        print("   • The underlying issue is data provider coverage")

    print()
    print("Alternative Solutions:")
    print("• Use German-specific financial data providers")
    print("• Implement manual ticker-to-ISIN mapping database")
    print("• Add support for multiple ticker formats per security")
    print("• Partner with European financial data providers")

    return mapping_results


def assess_isin_implementation_effort():
    """Assess the effort required to implement ISIN support."""
    print("\n" + "=" * 60)
    print("ISIN IMPLEMENTATION ASSESSMENT")
    print("=" * 60)

    print("\n🏗️  IMPLEMENTATION COMPLEXITY")
    print("-" * 40)

    components = {
        "ISIN Validation": {
            "effort": "Low",
            "description": "Format validation and checksum verification",
            "time": "1-2 hours",
        },
        "ISIN Database Schema": {
            "effort": "Low",
            "description": "Add ISIN field to assets table",
            "time": "1 hour",
        },
        "ISIN to Ticker Mapping": {
            "effort": "Medium",
            "description": "Integration with mapping services (OpenFIGI, etc.)",
            "time": "4-6 hours",
        },
        "UI Updates": {
            "effort": "Medium",
            "description": "Support ISIN input in frontend forms",
            "time": "2-3 hours",
        },
        "Fallback Logic": {
            "effort": "Medium",
            "description": "Try ISIN mapping when ticker fails",
            "time": "3-4 hours",
        },
        "Testing & Documentation": {
            "effort": "Medium",
            "description": "Comprehensive testing with European securities",
            "time": "4-6 hours",
        },
    }

    total_effort = 0
    for component, details in components.items():
        effort_hours = details["time"].split("-")[0]  # Take lower bound
        total_effort += int(effort_hours)

        print(
            f"{component:25} | {details['effort']:6} | {details['time']:8} | {details['description']}"
        )

    print("-" * 80)
    print(f"ESTIMATED TOTAL EFFORT: {total_effort}-{total_effort + 10} hours")

    print("\n💰 COST-BENEFIT ANALYSIS")
    print("-" * 40)

    print("Benefits:")
    print("✓ Better support for European securities")
    print("✓ Alternative lookup method when tickers fail")
    print("✓ Global standard identifier support")
    print("✓ Improved user experience for European users")

    print("\nCosts:")
    print("• Development time (15-25 hours)")
    print("• Potential API costs for comprehensive mapping")
    print("• Additional complexity in codebase")
    print("• Maintenance of mapping services")

    print("\n🎯 RECOMMENDATION")
    print("-" * 40)
    print("IMPLEMENT BASIC ISIN SUPPORT")
    print()
    print("Phase 1 (Immediate - 8 hours):")
    print("• Add ISIN field to database")
    print("• Implement ISIN validation")
    print("• Allow ISIN input in UI")
    print("• Basic OpenFIGI integration")
    print()
    print("Phase 2 (Future - 10 hours):")
    print("• Advanced mapping services")
    print("• Caching of ISIN-ticker mappings")
    print("• Bulk ISIN lookup capabilities")
    print("• European data provider integration")


def main():
    """Main analysis function."""
    print("📊 ISIN SUPPORT ANALYSIS FOR FINANCIAL DASHBOARD")
    print("Analyzing feasibility for Click Digital (CLIQ.DE)")
    print("=" * 60)

    try:
        # Analyze the specific Click Digital case
        mapping_results = analyze_click_digital_case()

        # Assess implementation effort
        assess_isin_implementation_effort()

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        print("\nFor the specific case of CLIQ.DE (Click Digital):")
        if mapping_results.get("openfigi", {}).get("success"):
            print("✅ ISIN mapping found ticker information")
            print("✅ ISIN support would help with this security")
        else:
            print("⚠️  ISIN mapping did not find ticker information")
            print("⚠️  The issue may be that this security is too small/new")
            print("⚠️  Even with ISIN support, data might not be available")

        print("\nGeneral recommendation:")
        print("• Implement basic ISIN support (Phase 1)")
        print("• Improves European market coverage")
        print("• Relatively low implementation effort")
        print("• Provides fallback when ticker lookup fails")

    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user.")
    except Exception as e:
        print(f"\n\nAnalysis failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
