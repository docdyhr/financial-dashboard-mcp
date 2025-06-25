#!/usr/bin/env python3
"""Simple ticker finder script to help users find correct ticker symbols."""

from pathlib import Path
import sys

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import time

import requests


def search_yahoo_finance(query):
    """Search for tickers using Yahoo Finance."""
    try:
        search_url = "https://query2.finance.yahoo.com/v1/finance/search"
        params = {
            "q": query,
            "quotesCount": 15,
            "newsCount": 0,
            "enableFuzzyQuery": True,
            "quotesQueryId": "tss_match_phrase_query",
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        quotes = data.get("quotes", [])

        results = []
        for quote in quotes:
            symbol = quote.get("symbol", "")
            name = quote.get("longname") or quote.get("shortname", "")
            exchange = quote.get("exchange", "")

            # Filter for relevant results
            if symbol and name:
                # Determine if it's European
                is_european = any(
                    symbol.endswith(suffix)
                    for suffix in [
                        ".L",
                        ".PA",
                        ".DE",
                        ".MI",
                        ".AS",
                        ".SW",
                        ".VI",
                        ".MC",
                    ]
                )

                results.append(
                    {
                        "symbol": symbol,
                        "name": name,
                        "exchange": exchange,
                        "is_european": is_european,
                    }
                )

        return results
    except Exception as e:
        print(f"Error searching: {e}")
        return []


def find_ticker(company_name):
    """Find ticker symbols for a company."""
    print(f"\n🔍 Searching for: '{company_name}'")
    print("=" * 60)

    results = search_yahoo_finance(company_name)

    if not results:
        print("❌ No results found")
        return

    # Separate European and other results
    european_results = [r for r in results if r["is_european"]]
    other_results = [r for r in results if not r["is_european"]]

    if european_results:
        print("\n🇪🇺 EUROPEAN RESULTS:")
        print("-" * 30)
        for i, result in enumerate(european_results, 1):
            print(f"{i:2d}. {result['symbol']:12} - {result['name']}")
            print(f"    Exchange: {result['exchange']}")

    if other_results:
        print("\n🌍 OTHER MARKETS:")
        print("-" * 30)
        for i, result in enumerate(other_results[:8], 1):  # Limit to 8 results
            print(f"{i:2d}. {result['symbol']:12} - {result['name']}")
            print(f"    Exchange: {result['exchange']}")


def main():
    """Main function."""
    print("🎯 TICKER FINDER")
    print("Find correct ticker symbols for companies")
    print("=" * 60)

    if len(sys.argv) > 1:
        # Use command line argument
        query = " ".join(sys.argv[1:])
        find_ticker(query)
    else:
        # Interactive mode
        print("\nExamples:")
        print("  • Enter 'Click' to find Click-related companies")
        print("  • Enter 'BMW' to find BMW")
        print("  • Enter 'Apple' to find Apple Inc.")
        print("  • Press Ctrl+C to exit")

        try:
            while True:
                query = input("\n📝 Enter company name (or 'quit' to exit): ").strip()

                if not query or query.lower() in ["quit", "exit", "q"]:
                    break

                find_ticker(query)
                time.sleep(1)  # Rate limiting

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
        except EOFError:
            print("\n\n👋 Goodbye!")


if __name__ == "__main__":
    main()
