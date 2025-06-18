#!/usr/bin/env python3
"""Monitor price updates happening in real-time."""

import sys
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import get_db_session
from backend.models.asset import Asset
from backend.models.position import Position
from backend.models.user import User


def monitor_prices(refresh_interval=10):
    """Monitor asset prices in real-time."""
    print("📊 Price Monitor - Press Ctrl+C to stop")
    print("=" * 60)

    try:
        while True:
            # Clear screen (works on Unix-like systems)
            print("\033[2J\033[H")

            print(f"📊 Price Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)

            with get_db_session() as db:
                # Get user
                user = db.query(User).filter(User.email == "user@example.com").first()
                if not user:
                    print("❌ User not found!")
                    break

                # Get positions
                positions = (
                    db.query(Position)
                    .filter(Position.user_id == user.id)
                    .join(Asset)
                    .order_by(Asset.ticker)
                    .all()
                )

                if not positions:
                    print("No positions found.")
                else:
                    print(f"\n💼 Portfolio for {user.email}:")
                    print("-" * 60)
                    print(
                        f"{'Ticker':<10} {'Quantity':<12} {'Price':<12} {'Value':<15} {'Last Updated'}"
                    )
                    print("-" * 60)

                    total_value = 0
                    for position in positions:
                        asset = position.asset
                        value = float(position.quantity * (asset.current_price or 0))
                        total_value += value

                        last_update = asset.updated_at.strftime("%H:%M:%S")

                        print(
                            f"{asset.ticker:<10} "
                            f"{float(position.quantity):<12.2f} "
                            f"${float(asset.current_price or 0):<11.2f} "
                            f"${value:<14,.2f} "
                            f"{last_update}"
                        )

                    print("-" * 60)
                    print(f"{'TOTAL':<10} {'':<12} {'':<12} ${total_value:<14,.2f}")

                # Show recent price updates
                print("\n📈 Recent Price Updates (last 5):")
                recent_assets = (
                    db.query(Asset)
                    .filter(Asset.current_price.isnot(None))
                    .order_by(Asset.updated_at.desc())
                    .limit(5)
                    .all()
                )

                for asset in recent_assets:
                    update_time = asset.updated_at.strftime("%H:%M:%S")
                    print(f"   {asset.ticker}: ${asset.current_price} @ {update_time}")

            print(f"\n⏱️  Refreshing in {refresh_interval} seconds...")
            time.sleep(refresh_interval)

    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped.")


if __name__ == "__main__":
    monitor_prices()
