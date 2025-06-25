#!/usr/bin/env python3
"""Manually trigger a price update task."""

from pathlib import Path
import sys

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import get_db_session
from backend.models.user import User
from backend.tasks.market_data import update_portfolio_prices


def trigger_update():
    """Trigger a price update for all users."""
    print("🚀 Triggering portfolio price update...")

    # Get user ID
    with get_db_session() as db:
        user = db.query(User).filter(User.email == "user@example.com").first()
        if not user:
            print("❌ User not found!")
            return

        user_id = user.id

    # Submit task to Celery
    try:
        result = update_portfolio_prices.delay(user_id=user_id)
        print(f"✅ Task submitted with ID: {result.id}")
        print("⏳ Waiting for completion...")

        # Wait for result
        task_result = result.get(timeout=30)

        print("\n✅ Task completed successfully!")
        print(f"   - Updated: {task_result['updated_count']} tickers")
        print(f"   - Failed: {task_result['failed_count']} tickers")
        print(f"   - Total tickers: {task_result['total_tickers']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure:")
        print("  1. Celery worker is running: docker-compose logs celery_worker")
        print("  2. Redis is accessible")
        print("  3. Internet connection is available for yfinance")


if __name__ == "__main__":
    trigger_update()
