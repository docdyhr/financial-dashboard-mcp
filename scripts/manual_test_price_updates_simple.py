#!/usr/bin/env python3
"""Simple test for price updates with mock data."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
import random
import sys

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import get_db_session
from backend.models.asset import Asset
from backend.models.position import Position
from backend.models.user import User


def update_prices_with_mock_data():
    """Update asset prices with mock data for demonstration."""
    print("🚀 Updating portfolio prices with mock data...")

    with get_db_session() as db:
        # Get all assets
        assets = db.query(Asset).all()

        if not assets:
            print("❌ No assets found in database!")
            return

        print(f"\n📊 Updating prices for {len(assets)} assets:")

        # Mock price changes for demonstration
        for asset in assets:
            # Skip assets without prices
            if asset.current_price is None:
                continue

            old_price = float(asset.current_price)

            # Generate a random price change between -5% and +5%
            change_percent = random.uniform(-0.05, 0.05)
            new_price = old_price * (1 + change_percent)

            # Update the asset price
            asset.current_price = Decimal(str(round(new_price, 2)))
            asset.updated_at = datetime.now()

            change_symbol = "📈" if change_percent > 0 else "📉"
            print(
                f"   {asset.ticker}: ${old_price:.2f} → ${new_price:.2f} ({change_percent*100:+.2f}%) {change_symbol}"
            )

        # Commit changes
        db.commit()
        print("\n✅ Price updates committed to database!")

        # Show portfolio summary for each user
        users = db.query(User).all()
        for user in users:
            positions = db.query(Position).filter(Position.user_id == user.id).all()
            if positions:
                print(f"\n💼 Portfolio for {user.email}:")
                total_value = Decimal("0")
                total_cost = Decimal("0")

                for position in positions:
                    asset = position.asset
                    current_value = position.quantity * asset.current_price
                    cost_basis = position.total_cost_basis
                    gain_loss = current_value - cost_basis
                    gain_loss_pct = (
                        (gain_loss / cost_basis * 100) if cost_basis > 0 else 0
                    )

                    total_value += current_value
                    total_cost += cost_basis

                    print(
                        f"   {asset.ticker}: {position.quantity} shares @ ${asset.current_price}"
                    )
                    print(
                        f"      Value: ${current_value:,.2f} | Cost: ${cost_basis:,.2f} | P&L: ${gain_loss:,.2f} ({gain_loss_pct:+.2f}%)"
                    )

                total_gain_loss = total_value - total_cost
                total_gain_loss_pct = (
                    (total_gain_loss / total_cost * 100) if total_cost > 0 else 0
                )

                print(f"\n   📊 Total Portfolio Value: ${total_value:,.2f}")
                print(f"   💰 Total Cost Basis: ${total_cost:,.2f}")
                print(
                    f"   📈 Total P&L: ${total_gain_loss:,.2f} ({total_gain_loss_pct:+.2f}%)"
                )


def show_current_prices():
    """Display current prices from the database."""
    print("\n🔍 Current prices in database:")

    with get_db_session() as db:
        # Only show assets with prices
        assets = db.query(Asset).filter(Asset.current_price.isnot(None)).all()
        for asset in assets:
            print(
                f"   {asset.ticker}: ${asset.current_price} (Last updated: {asset.updated_at.strftime('%Y-%m-%d %H:%M:%S')})"
            )


if __name__ == "__main__":
    print("📈 Mock Price Update Test")
    print("=" * 50)

    # Show current prices
    show_current_prices()

    # Update prices with mock data
    update_prices_with_mock_data()

    # Show updated prices
    show_current_prices()
