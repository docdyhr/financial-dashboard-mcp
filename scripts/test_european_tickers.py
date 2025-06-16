#!/usr/bin/env python3
"""Test script for European ticker support in the Financial Dashboard."""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.config import get_settings
from backend.services.market_data import AlphaVantageProvider, YFinanceProvider
from backend.services.ticker_utils import TickerUtils

# Sample European tickers for testing
EUROPEAN_TICKERS = [
    # London Stock Exchange
    "VODAFONE.L",  # Vodafone Group
    "BP.L",  # BP plc
    "SHELL.L",  # Shell plc
    "BARC.L",  # Barclays
    # Euronext Paris
    "ASML.PA",  # ASML Holding
    "LVMH.PA",  # LVMH
    "SAP.PA",  # SAP (also trades in Paris)
    "TOTALENERGIES.PA",  # TotalEnergies
    # Frankfurt/XETRA
    "SAP.DE",  # SAP SE
    "ADIDAS.DE",  # Adidas
    "BMW.DE",  # BMW
    "SIEMENS.DE",  # Siemens
    # Milan
    "ENEL.MI",  # Enel
    "FERRARI.MI",  # Ferrari
    "INTESA.MI",  # Intesa Sanpaolo
    # Amsterdam
    "ASML.AS",  # ASML (also trades in Amsterdam)
    "SHELL.AS",  # Shell (also trades in Amsterdam)
    # Swiss Exchange
    "NESTLE.SW",  # Nestlé
    "NOVARTIS.SW",  # Novartis
    # Nordic Exchanges
    "VOLVO-B.ST",  # Volvo (Stockholm)
    "NOKIA.HE",  # Nokia (Helsinki)
]

# Some US tickers for comparison
US_TICKERS = [
    "AAPL",  # Apple
    "MSFT",  # Microsoft
    "GOOGL",  # Alphabet
    "TSLA",  # Tesla
]


def test_ticker_parsing():
    """Test the ticker parsing functionality."""
    print("=" * 60)
    print("TESTING TICKER PARSING")
    print("=" * 60)

    all_tickers = EUROPEAN_TICKERS + US_TICKERS

    for ticker in all_tickers:
        print(f"\nTicker: {ticker}")
        print("-" * 40)

        # Test validation
        is_valid, error = TickerUtils.validate_ticker_format(ticker)
        print(f"Valid: {is_valid}")
        if not is_valid:
            print(f"Error: {error}")
            continue

        # Parse ticker
        ticker_info = TickerUtils.parse_ticker(ticker)
        print(f"Base: {ticker_info.base_ticker}")
        print(f"Exchange: {ticker_info.exchange_name}")
        print(f"Country: {ticker_info.country_code}")
        print(f"Currency: {ticker_info.default_currency}")
        print(f"Timezone: {ticker_info.market_timezone}")
        print(f"International: {ticker_info.is_international}")
        print(f"European: {TickerUtils.is_european_ticker(ticker)}")

        # Test formatting
        yf_format = TickerUtils.format_for_yfinance(ticker)
        av_format = TickerUtils.format_for_alpha_vantage(ticker)
        print(f"Yahoo Finance format: {yf_format}")
        print(f"Alpha Vantage format: {av_format}")


def test_market_data_fetching():
    """Test fetching market data for European tickers."""
    print("\n" + "=" * 60)
    print("TESTING MARKET DATA FETCHING")
    print("=" * 60)

    # Test with YFinance provider
    yf_provider = YFinanceProvider()

    # Test a few representative tickers
    test_tickers = [
        "AAPL",  # US ticker
        "VODAFONE.L",  # London
        "ASML.PA",  # Paris
        "SAP.DE",  # Frankfurt
        "FERRARI.MI",  # Milan
    ]

    for ticker in test_tickers:
        print(f"\nTesting {ticker} with Yahoo Finance...")
        print("-" * 50)

        try:
            result = yf_provider.fetch_quote(ticker)

            if result.success:
                print(f"✓ Success!")
                print(f"  Current Price: ${result.current_price:.2f}")
                if result.day_change:
                    print(
                        f"  Day Change: ${result.day_change:.2f} ({result.day_change_percent:.2f}%)"
                    )
                if result.volume:
                    print(f"  Volume: {result.volume:,}")
                print(f"  Data Source: {result.data_source}")
            else:
                print(f"✗ Failed: {result.error}")

        except Exception as e:
            print(f"✗ Exception: {e}")


def test_exchange_support():
    """Test supported exchanges information."""
    print("\n" + "=" * 60)
    print("SUPPORTED EXCHANGES")
    print("=" * 60)

    exchanges = TickerUtils.get_supported_exchanges()

    print("European Exchanges:")
    print("-" * 30)
    for suffix, info in exchanges.items():
        if suffix.startswith(".") and info["country"] in [
            "GB",
            "FR",
            "DE",
            "IT",
            "NL",
            "BE",
            "PT",
            "ES",
            "AT",
            "CH",
            "SE",
            "FI",
            "NO",
            "DK",
            "IS",
        ]:
            print(f"{suffix:8} {info['name']} ({info['country']}, {info['currency']})")

    print("\nOther International Exchanges:")
    print("-" * 30)
    for suffix, info in exchanges.items():
        if suffix.startswith(".") and info["country"] not in [
            "GB",
            "FR",
            "DE",
            "IT",
            "NL",
            "BE",
            "PT",
            "ES",
            "AT",
            "CH",
            "SE",
            "FI",
            "NO",
            "DK",
            "IS",
            "US",
        ]:
            print(f"{suffix:8} {info['name']} ({info['country']}, {info['currency']})")


def test_ticker_suggestions():
    """Test ticker format suggestions."""
    print("\n" + "=" * 60)
    print("TICKER FORMAT SUGGESTIONS")
    print("=" * 60)

    test_cases = [
        ("VODAFONE", "London"),
        ("ASML", "Paris"),
        ("SAP", "Frankfurt"),
        ("FERRARI", "Milan"),
        ("SHELL", "Amsterdam"),
        ("NESTLE", "Swiss"),
        ("VOLVO", "Stockholm"),
        ("AAPL", None),  # US ticker
    ]

    for base_ticker, exchange_hint in test_cases:
        suggested = TickerUtils.suggest_ticker_format(base_ticker, exchange_hint)
        print(f"{base_ticker:12} + {exchange_hint or 'None':12} → {suggested}")


def main():
    """Run all tests."""
    print("European Ticker Support Test")
    print("Financial Dashboard MCP")
    print("=" * 60)

    try:
        test_ticker_parsing()
        test_exchange_support()
        test_ticker_suggestions()

        # Only test market data fetching if we want to make actual API calls
        print(f"\n{'='*60}")
        response = input("Test live market data fetching? (y/N): ").strip().lower()
        if response == "y":
            test_market_data_fetching()
        else:
            print("Skipping live market data test.")

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
