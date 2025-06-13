#!/usr/bin/env python3
"""Demo script to populate the database with sample portfolio data."""

import time

import requests

# Configuration
BACKEND_URL = "http://localhost:8000"
SAMPLE_POSITIONS = [
    {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "quantity": 50,
        "purchase_price": 150.00,
        "purchase_date": "2024-01-15",
        "asset_type": "Stock",
    },
    {
        "symbol": "GOOGL",
        "name": "Alphabet Inc.",
        "quantity": 25,
        "purchase_price": 2800.00,
        "purchase_date": "2024-02-01",
        "asset_type": "Stock",
    },
    {
        "symbol": "MSFT",
        "name": "Microsoft Corporation",
        "quantity": 75,
        "purchase_price": 400.00,
        "purchase_date": "2024-01-30",
        "asset_type": "Stock",
    },
    {
        "symbol": "TSLA",
        "name": "Tesla Inc.",
        "quantity": 30,
        "purchase_price": 800.00,
        "purchase_date": "2024-03-15",
        "asset_type": "Stock",
    },
    {
        "symbol": "SPY",
        "name": "SPDR S&P 500 ETF Trust",
        "quantity": 100,
        "purchase_price": 450.00,
        "purchase_date": "2024-02-15",
        "asset_type": "ETF",
    },
]


def check_backend_health():
    """Check if backend is accessible."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def add_sample_positions():
    """Add sample positions to the portfolio."""
    print("🔄 Adding sample portfolio positions...")

    for position in SAMPLE_POSITIONS:
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/portfolio/positions", json=position, timeout=10
            )

            if response.status_code == 200:
                print(
                    f"✅ Added position: {position['symbol']} ({position['quantity']} shares)"
                )
            else:
                print(f"❌ Failed to add {position['symbol']}: {response.status_code}")
                if response.text:
                    print(f"   Error: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Error adding {position['symbol']}: {e}")

        time.sleep(0.5)  # Small delay between requests


def trigger_market_data_update():
    """Trigger market data update for all positions."""
    print("\n🔄 Updating market data for all positions...")

    symbols = [pos["symbol"] for pos in SAMPLE_POSITIONS]

    try:
        response = requests.post(
            f"{BACKEND_URL}/api/tasks/market-data/fetch",
            json={"symbols": symbols},
            timeout=10,
        )

        if response.status_code == 200:
            task_data = response.json()
            task_id = task_data.get("task_id", "N/A")
            print(f"✅ Market data update started! Task ID: {task_id}")

            # Wait a moment and check task status
            time.sleep(3)

            status_response = requests.get(
                f"{BACKEND_URL}/api/tasks/{task_id}/status", timeout=5
            )

            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"📊 Task status: {status_data.get('status', 'Unknown')}")

        else:
            print(f"❌ Failed to trigger market data update: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error triggering market data update: {e}")


def create_portfolio_snapshot():
    """Create a portfolio snapshot."""
    print("\n📸 Creating portfolio snapshot...")

    try:
        response = requests.post(
            f"{BACKEND_URL}/api/tasks/portfolio/snapshot",
            json={"user_id": 1},
            timeout=10,
        )

        if response.status_code == 200:
            task_data = response.json()
            task_id = task_data.get("task_id", "N/A")
            print(f"✅ Portfolio snapshot started! Task ID: {task_id}")
        else:
            print(f"❌ Failed to create snapshot: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating snapshot: {e}")


def run_portfolio_analytics():
    """Run portfolio analytics."""
    print("\n📈 Running portfolio analytics...")

    try:
        response = requests.post(
            f"{BACKEND_URL}/api/tasks/portfolio/analytics",
            json={"user_id": 1},
            timeout=10,
        )

        if response.status_code == 200:
            task_data = response.json()
            task_id = task_data.get("task_id", "N/A")
            print(f"✅ Portfolio analytics started! Task ID: {task_id}")
        else:
            print(f"❌ Failed to run analytics: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error running analytics: {e}")


def display_portfolio_summary():
    """Display current portfolio summary."""
    print("\n📊 Portfolio Summary:")
    print("=" * 50)

    try:
        # Get portfolio summary
        response = requests.get(f"{BACKEND_URL}/api/portfolio/summary", timeout=10)

        if response.status_code == 200:
            summary = response.json()
            print(f"💰 Total Portfolio Value: ${summary.get('total_value', 0):,.2f}")
            print(f"💵 Cash Position: ${summary.get('cash_position', 0):,.2f}")
            print(f"📈 Total Positions: {summary.get('total_positions', 0)}")
            print(f"📊 YTD Return: {summary.get('ytd_return_pct', 0):.2f}%")
        else:
            print("❌ Could not fetch portfolio summary")

        # Get positions
        response = requests.get(f"{BACKEND_URL}/api/portfolio/positions", timeout=10)

        if response.status_code == 200:
            positions = response.json()
            print(f"\n📋 Current Positions ({len(positions)}):")

            for pos in positions:
                symbol = pos.get("symbol", "N/A")
                quantity = pos.get("quantity", 0)
                current_price = pos.get("current_price", 0)
                market_value = pos.get("market_value", 0)
                pnl_pct = pos.get("unrealized_pnl_pct", 0)

                print(
                    f"  • {symbol}: {quantity} shares @ ${current_price:.2f} = ${market_value:,.2f} ({pnl_pct:+.1f}%)"
                )
        else:
            print("❌ Could not fetch positions")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching portfolio data: {e}")


def main():
    """Main demo function."""
    print("🚀 Financial Dashboard Demo Setup")
    print("=" * 50)

    # Check backend health
    print("🔍 Checking backend connectivity...")
    if not check_backend_health():
        print("❌ Backend is not accessible!")
        print("   Please make sure the backend is running:")
        print("   docker-compose up -d")
        return

    print("✅ Backend is accessible!")

    # Add sample data
    add_sample_positions()

    # Update market data
    trigger_market_data_update()

    # Create snapshot
    create_portfolio_snapshot()

    # Run analytics
    run_portfolio_analytics()

    # Wait a moment for tasks to complete
    print("\n⏳ Waiting for background tasks to complete...")
    time.sleep(5)

    # Display summary
    display_portfolio_summary()

    print("\n🎉 Demo setup complete!")
    print("=" * 50)
    print("📱 Frontend URLs:")
    print("  • Dashboard: http://localhost:8501")
    print("  • API Docs: http://localhost:8000/docs")
    print("  • Task Monitor: http://localhost:5555")
    print("\n💡 Try refreshing the Streamlit dashboard to see the data!")


if __name__ == "__main__":
    main()
