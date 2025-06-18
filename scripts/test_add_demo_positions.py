#!/usr/bin/env python3
"""Script to add demo positions directly to the database for testing."""

import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import get_db_session
from backend.models.asset import Asset, AssetCategory, AssetType
from backend.models.position import Position
from backend.models.user import User


def add_demo_positions():
    """Add demo positions for testing."""
    with get_db_session() as db:
        # Get the default user or create one
        user = db.query(User).filter(User.email == "user@example.com").first()
        if not user:
            # Get any user or create a demo user
            user = db.query(User).first()
            if not user:
                # Create a demo user
                from backend.auth.password import get_password_hash

                user = User(
                    email="demo@financial-dashboard.com",
                    username="demo",
                    full_name="Demo User",
                    hashed_password=get_password_hash("demo123"),
                    is_active=True,
                    is_verified=True,
                    is_superuser=False,
                    preferred_currency="USD",
                    timezone="UTC",
                )
                db.add(user)
                db.commit()
                print(f"✅ Created demo user: {user.email}")
            else:
                print(f"✅ Using existing user: {user.email}")

        print(f"✅ Found user: {user.email} (ID: {user.id})")

        # Demo positions to add
        demo_positions = [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "type": AssetType.STOCK,
                "category": AssetCategory.EQUITY,
                "quantity": 50,
                "purchase_price": 150.00,
                "purchase_date": datetime(2024, 1, 15),
            },
            {
                "symbol": "MSFT",
                "name": "Microsoft Corporation",
                "type": AssetType.STOCK,
                "category": AssetCategory.EQUITY,
                "quantity": 30,
                "purchase_price": 320.00,
                "purchase_date": datetime(2024, 2, 1),
            },
            {
                "symbol": "VOO",
                "name": "Vanguard S&P 500 ETF",
                "type": AssetType.ETF,
                "category": AssetCategory.EQUITY,
                "quantity": 25,
                "purchase_price": 400.00,
                "purchase_date": datetime(2024, 1, 5),
            },
            {
                "symbol": "BTC-USD",
                "name": "Bitcoin USD",
                "type": AssetType.CRYPTO,
                "category": AssetCategory.ALTERNATIVE,
                "quantity": 0.5,
                "purchase_price": 45000.00,
                "purchase_date": datetime(2024, 3, 1),
            },
        ]

        for pos_data in demo_positions:
            # Check if asset exists
            asset = db.query(Asset).filter(Asset.ticker == pos_data["symbol"]).first()

            if not asset:
                # Create asset
                asset = Asset(
                    ticker=pos_data["symbol"],
                    name=pos_data["name"],
                    asset_type=pos_data["type"],
                    category=pos_data["category"],
                    currency="USD",
                    current_price=Decimal(str(pos_data["purchase_price"])),
                    is_active=True,
                )
                db.add(asset)
                db.flush()
                print(f"✅ Created asset: {asset.ticker} - {asset.name}")

            # Check if position already exists
            existing_position = (
                db.query(Position)
                .filter(Position.user_id == user.id, Position.asset_id == asset.id)
                .first()
            )

            if existing_position:
                print(f"⚠️  Position already exists: {asset.ticker}")
                continue

            # Create position
            quantity = Decimal(str(pos_data["quantity"]))
            price = Decimal(str(pos_data["purchase_price"]))
            total_cost = quantity * price

            position = Position(
                user_id=user.id,
                asset_id=asset.id,
                quantity=quantity,
                average_cost_per_share=price,
                total_cost_basis=total_cost,
                is_active=True,
            )
            db.add(position)
            print(
                f"✅ Created position: {pos_data['quantity']} shares of {asset.ticker}"
            )

        # Commit all changes
        db.commit()
        print("\n✅ Demo positions added successfully!")

        # Display summary
        positions = db.query(Position).filter(Position.user_id == user.id).all()
        print(f"\n📊 Total positions for {user.email}: {len(positions)}")

        total_value = Decimal("0")
        for position in positions:
            value = position.quantity * position.asset.current_price
            total_value += value
            print(
                f"   - {position.asset.ticker}: {position.quantity} @ ${position.asset.current_price}"
            )

        print(f"\n💰 Total portfolio value: ${total_value:,.2f}")


if __name__ == "__main__":
    print("🚀 Adding demo positions to the database...")
    try:
        add_demo_positions()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
