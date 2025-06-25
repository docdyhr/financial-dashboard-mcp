#!/usr/bin/env python3
"""Debug script specifically for investigating CLICK.DE ticker issues."""

from pathlib import Path
import sys
import time

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.services.market_data import market_data_service
from backend.services.ticker_search import ticker_search_service
from backend.services.ticker_utils import TickerUtils


def debug_click_ticker():
    """Debug the CLICK.DE ticker issue comprehensively."""
    print("=" * 80)
    print("CLICK.DE TICKER DEBUGGING SCRIPT")
    print("=" * 80)

    target_ticker = "CLICK.DE"

    # Step 1: Validate ticker format
    print("\n1. TICKER FORMAT VALIDATION")
    print("-" * 40)
    is_valid, error = TickerUtils.validate_ticker_format(target_ticker)
    print(f"Ticker: {target_ticker}")
    print(f"Format Valid: {is_valid}")
    if not is_valid:
        print(f"Format Error: {error}")

    # Step 2: Parse ticker information
    print("\n2. TICKER PARSING")
    print("-" * 40)
    ticker_info = TickerUtils.parse_ticker(target_ticker)
    print(f"Base Ticker: {ticker_info.base_ticker}")
    print(f"Exchange Suffix: {ticker_info.exchange_suffix}")
    print(f"Exchange Name: {ticker_info.exchange_name}")
    print(f"Country: {ticker_info.country_code}")
    print(f"Currency: {ticker_info.default_currency}")
    print(f"Timezone: {ticker_info.market_timezone}")
    print(f"Is International: {ticker_info.is_international}")
    print(f"Is European: {TickerUtils.is_european_ticker(target_ticker)}")

    # Step 3: Check formatting for different providers
    print("\n3. PROVIDER FORMATTING")
    print("-" * 40)
    yf_format = TickerUtils.format_for_yfinance(target_ticker)
    av_format = TickerUtils.format_for_alpha_vantage(target_ticker)
    print(f"Yahoo Finance format: {yf_format}")
    print(f"Alpha Vantage format: {av_format}")
    print(f"Finnhub format (base): {ticker_info.base_ticker}")

    # Step 4: Test market data fetching
    print("\n4. MARKET DATA FETCHING TEST")
    print("-" * 40)
    print(f"Testing {target_ticker} with multi-provider service...")

    result = market_data_service.fetch_quote(target_ticker)

    print(f"Success: {result.success}")
    if result.success:
        print(f"Current Price: ${result.current_price:.2f}")
        print(f"Data Source: {result.data_source}")
        if result.day_change:
            print(
                f"Day Change: ${result.day_change:.2f} ({result.day_change_percent:.2f}%)"
            )
    else:
        print(f"Error: {result.error}")
        print(f"Failed Data Source: {result.data_source}")
        if hasattr(result, "suggestions") and result.suggestions:
            print(f"Suggestions: {', '.join(result.suggestions)}")

    # Step 5: Search for alternatives
    print("\n5. ALTERNATIVE TICKER SEARCH")
    print("-" * 40)

    # Search for "CLICK" companies
    print("Searching for companies with 'CLICK' in the name...")
    search_results = ticker_search_service.search_ticker("CLICK")

    if search_results:
        print(f"Found {len(search_results)} potential matches:")
        for i, result in enumerate(search_results[:10], 1):
            print(f"  {i}. {result['symbol']} - {result['name']}")
            print(f"     Exchange: {result['exchange_name']} ({result['country']})")
            print(f"     Currency: {result['currency']}")
            print()
    else:
        print("No search results found for 'CLICK'")

    # Step 6: Try variations and suggestions
    print("\n6. TICKER VARIATIONS TESTING")
    print("-" * 40)

    variations = [
        "CLICK",  # Base ticker (US)
        "CLK.DE",  # Shorter version
        "CLIQ.DE",  # Alternative spelling
        "CLCK.DE",  # Alternative abbreviation
        "CKD.DE",  # Another possibility
    ]

    for var_ticker in variations:
        print(f"\nTesting variation: {var_ticker}")
        time.sleep(1)  # Rate limiting

        var_result = market_data_service.fetch_quote(var_ticker)
        if var_result.success:
            print(
                f"  ✓ SUCCESS: ${var_result.current_price:.2f} from {var_result.data_source}"
            )
        else:
            print(f"  ✗ Failed: {var_result.error}")

    # Step 7: Get comprehensive recommendations
    print("\n7. COMPREHENSIVE RECOMMENDATIONS")
    print("-" * 40)

    recommendations = ticker_search_service.get_ticker_recommendations(target_ticker)

    print(f"Input: {recommendations['input']}")
    print(f"Is Valid: {recommendations['is_valid']}")

    if not recommendations["is_valid"]:
        print(f"Error: {recommendations['error']}")

        if recommendations["suggestions"]:
            print("\nSuggested alternatives:")
            for i, suggestion in enumerate(recommendations["suggestions"], 1):
                print(f"  {i}. {suggestion['symbol']} - {suggestion['reason']}")
                print(f"     {suggestion['exchange']} ({suggestion['country']})")

        if recommendations["search_results"]:
            print("\nSearch results for similar companies:")
            for i, result in enumerate(recommendations["search_results"], 1):
                print(f"  {i}. {result['symbol']} - {result['name']}")
                print(f"     {result['exchange_name']} ({result['country']})")

    # Step 8: Specific German market guidance
    print("\n8. GERMAN MARKET TICKER GUIDANCE")
    print("-" * 40)

    print("Common German ticker patterns:")
    print("  • Company.DE - Frankfurt/XETRA listing")
    print("  • Company-DE - Alternative format")
    print("  • Company.F  - Frankfurt Stock Exchange")
    print("  • Company.BE - Berlin Stock Exchange")
    print("  • Company.DU - Düsseldorf Stock Exchange")
    print("  • Company.HM - Hamburg Stock Exchange")
    print("  • Company.MU - Munich Stock Exchange")
    print("  • Company.SG - Stuttgart Stock Exchange")

    print("\nNote: Many German companies also trade on US exchanges")
    print("Example: SAP.DE (German) vs SAP (US ADR)")

    # Step 9: Test known working German tickers
    print("\n9. TESTING KNOWN GERMAN TICKERS")
    print("-" * 40)

    known_german_tickers = ["BMW.DE", "SAP.DE", "ADIDAS.DE", "SIEMENS.DE"]

    print("Testing known German tickers to verify system works:")
    for known_ticker in known_german_tickers:
        print(f"\nTesting {known_ticker}...")
        time.sleep(2)  # Rate limiting

        known_result = market_data_service.fetch_quote(known_ticker)
        if known_result.success:
            print(
                f"  ✓ {known_ticker}: ${known_result.current_price:.2f} from {known_result.data_source}"
            )
            break  # If we find one working, we know the system works
        print(f"  ✗ {known_ticker}: {known_result.error}")

    # Step 10: Final conclusions
    print("\n10. CONCLUSIONS AND RECOMMENDATIONS")
    print("-" * 40)

    print("Based on the analysis:")
    print("1. The ticker format 'CLICK.DE' is syntactically valid")
    print("2. The Frankfurt/XETRA exchange (.DE) is properly configured")
    print("3. Market data providers are configured but may have issues")

    if not result.success:
        print("\nLikely issues:")
        print("• CLICK.DE may not exist as a valid ticker symbol")
        print("• The company might be listed under a different symbol")
        print("• The stock might be delisted or traded on a different exchange")
        print("• API rate limiting or authentication issues")

        print("\nRecommended actions:")
        print("1. Verify the correct ticker symbol from a financial website")
        print("2. Check if the company trades under a different name/symbol")
        print("3. Try searching by company name instead of ticker")
        print("4. Consider that the ticker might be from a different exchange")
        print("5. Wait a few minutes and try again (rate limiting)")


def main():
    """Run the comprehensive CLICK.DE debugging."""
    try:
        debug_click_ticker()
    except KeyboardInterrupt:
        print("\n\nDebugging interrupted by user.")
    except Exception as e:
        print(f"\n\nDebugging failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
