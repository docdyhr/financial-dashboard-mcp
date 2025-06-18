#!/usr/bin/env python3
"""Trigger a mock price update task for demonstration."""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import get_db_session
from backend.models.user import User
from backend.tasks.mock_market_data import update_portfolio_prices_mock


def trigger_mock_update():
    """Trigger a mock price update for demonstration."""
    print("🎭 Triggering MOCK portfolio price update...")
    print("   (Using simulated price changes for demonstration)")

    # Get user ID
    with get_db_session() as db:
        user = db.query(User).filter(User.email == "user@example.com").first()
        if not user:
            print("❌ User not found!")
            return

        user_id = user.id

    # Submit task to Celery
    try:
        result = update_portfolio_prices_mock.delay(user_id=user_id)
        print(f"✅ Task submitted with ID: {result.id}")
        print("⏳ Waiting for completion...")

        # Wait for result
        task_result = result.get(timeout=10)

        print("\n✅ Mock update completed successfully!")
        print(f"   - Updated: {task_result['updated_count']} assets")
        print(f"   - Total assets: {task_result['total_assets']}")
        print(f"   - Mock data: {task_result.get('mock_data', False)}")

        print(
            "\n📊 Price changes were simulated with random values between -2% and +2%"
        )
        print("   In production, real market data would be fetched from yfinance")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    trigger_mock_update()
