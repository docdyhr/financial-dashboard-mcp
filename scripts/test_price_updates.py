#!/usr/bin/env python3
"""Test real-time price updates for portfolio positions."""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yfinance as yf

from backend.database import get_db_session
from backend.models.position import Position
from backend.models.user import User


def test_price_updates():
    """Test updating prices for existing positions."""
    # First, let's check current prices using yfinance directly
    print("🔍 Fetching current market prices...")

    tickers = ["AAPL", "MSFT", "VOO", "BTC-USD"]
    for ticker in tickers:
        try:
            yf_ticker = yf.Ticker(ticker)
            hist = yf_ticker.history(period="1d")
            if not hist.empty:
                current_price = hist["Close"].iloc[-1]
                print(f"   {ticker}: ${current_price:.2f}")
            else:
                print(f"   {ticker}: No data available")
        except Exception as e:
            print(f"   {ticker}: Error - {e}")

    print("\n🚀 Running portfolio price update task...")

    # Get user ID
    with get_db_session() as db:
        user = db.query(User).filter(User.email == "user@example.com").first()
        if not user:
            print("❌ User not found!")
            return

        user_id = user.id

        # Show current asset prices in database
        print(f"\n📊 Current prices in database for user {user.email}:")
        positions = db.query(Position).filter(Position.user_id == user_id).all()
        for position in positions:
            asset = position.asset
            print(f"   {asset.ticker}: ${asset.current_price}")

    # Run the update task directly (without Celery for testing)
    try:
        # Call the task directly without Celery binding
        from backend.tasks.market_data import update_portfolio_prices

        task = update_portfolio_prices.s(user_id=user_id)
        result = task.apply().get()
        print("\n✅ Price update completed:")
        print(f"   - Updated: {result['updated_count']} tickers")
        print(f"   - Failed: {result['failed_count']} tickers")

        # Show updated prices
        with get_db_session() as db:
            print("\n📈 Updated prices in database:")
            positions = db.query(Position).filter(Position.user_id == user_id).all()
            total_value = 0
            for position in positions:
                asset = position.asset
                db.refresh(asset)  # Refresh to get updated data
                position_value = float(position.quantity * asset.current_price)
                total_value += position_value
                print(
                    f"   {asset.ticker}: ${asset.current_price} (Position value: ${position_value:,.2f})"
                )

            print(f"\n💰 Total portfolio value: ${total_value:,.2f}")

    except Exception as e:
        print(f"❌ Error updating prices: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_price_updates()
