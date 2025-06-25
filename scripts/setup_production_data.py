#!/usr/bin/env python3
"""Setup initial production data for testing."""

from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


from backend.auth.password import get_password_hash
from backend.models import Asset, User, get_db


def setup_production_data():
    """Setup initial production data."""
    db = next(get_db())

    try:
        # Create default assets with proper categories
        assets = [
            {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "asset_type": "stock",
                "category": "equity",
                "currency": "USD",
            },
            {
                "ticker": "GOOGL",
                "name": "Alphabet Inc.",
                "asset_type": "stock",
                "category": "equity",
                "currency": "USD",
            },
            {
                "ticker": "MSFT",
                "name": "Microsoft Corp.",
                "asset_type": "stock",
                "category": "equity",
                "currency": "USD",
            },
            {
                "ticker": "VOO",
                "name": "Vanguard S&P 500 ETF",
                "asset_type": "etf",
                "category": "equity",
                "currency": "USD",
            },
            {
                "ticker": "BTC-USD",
                "name": "Bitcoin",
                "asset_type": "crypto",
                "category": "alternative",
                "currency": "USD",
            },
            {
                "ticker": "GLD",
                "name": "SPDR Gold Trust",
                "asset_type": "commodity",
                "category": "commodity",
                "currency": "USD",
            },
        ]

        created_assets = []
        for asset_data in assets:
            # Check if asset exists
            existing = db.query(Asset).filter_by(ticker=asset_data["ticker"]).first()
            if not existing:
                asset = Asset(**asset_data)
                db.add(asset)
                created_assets.append(asset_data["ticker"])

        # Create demo user if not exists
        demo_user = db.query(User).filter_by(username="demo").first()
        if not demo_user:
            demo_user = User(
                username="demo",
                email="demo@example.com",
                hashed_password=get_password_hash("demo123"),
                full_name="Demo User",
                is_active=True,
            )
            db.add(demo_user)
            print("✅ Created demo user")

        db.commit()

        if created_assets:
            print(
                f"✅ Created {len(created_assets)} assets: {', '.join(created_assets)}"
            )
        else:
            print("✅ All assets already exist")

        # List all assets
        all_assets = db.query(Asset).all()
        print(f"\n📊 Total assets in database: {len(all_assets)}")
        for asset in all_assets:
            print(f"   - {asset.ticker}: {asset.name}")

    except Exception as e:
        print(f"❌ Error setting up data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Setting up production data...")
    setup_production_data()
