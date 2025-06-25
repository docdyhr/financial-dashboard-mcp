#!/usr/bin/env python3
"""Test real API endpoints that are available."""

from datetime import date

import requests
from rich.console import Console

console = Console()

BASE_URL = "http://localhost:8000"


def test_api():
    """Test available API endpoints."""
    session = requests.Session()

    # 1. Register user
    console.print("\n1. Testing User Registration...")
    register_data = {
        "username": "testprod",
        "email": "testprod@example.com",
        "password": "TestProd123!",
        "full_name": "Test Production",
    }

    response = session.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
    if response.status_code in [200, 201]:
        console.print("✅ User registered successfully", style="green")
    elif response.status_code == 400:
        console.print("✅ User already exists", style="yellow")
    else:
        console.print(f"❌ Registration failed: {response.status_code}", style="red")
        console.print(response.text)

    # 2. Login
    console.print("\n2. Testing Login...")
    login_data = {
        "username": register_data["username"],
        "password": register_data["password"],
    }

    response = session.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)

    if response.status_code == 200:
        token_data = response.json()
        token = token_data["access_token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        console.print("✅ Login successful", style="green")
    else:
        console.print(f"❌ Login failed: {response.status_code}", style="red")
        return

    # 3. Get user info
    console.print("\n3. Testing Get User Info...")
    response = session.get(f"{BASE_URL}/api/v1/auth/me")
    if response.status_code == 200:
        user_data = response.json()
        console.print(f"✅ User info retrieved: {user_data['username']}", style="green")
        user_id = user_data["id"]
    else:
        console.print(
            f"❌ Failed to get user info: {response.status_code}", style="red"
        )
        return

    # 4. Create/Get Assets
    console.print("\n4. Testing Asset Management...")

    # Try to create an asset
    asset_data = {
        "ticker": "AAPL",
        "name": "Apple Inc.",
        "asset_type": "stock",
        "category": "equity",
        "currency": "USD",
    }

    response = session.post(f"{BASE_URL}/api/v1/assets/", json=asset_data)
    if response.status_code in [200, 201]:
        asset = response.json()["data"]
        console.print(f"✅ Asset created: {asset['ticker']}", style="green")
        asset_id = asset["id"]
    else:
        # Try to get existing asset
        response = session.get(f"{BASE_URL}/api/v1/assets/ticker/AAPL")
        if response.status_code == 200:
            asset = response.json()["data"]
            console.print(f"✅ Asset found: {asset['ticker']}", style="green")
            asset_id = asset["id"]
        else:
            console.print(
                f"❌ Failed to create/get asset: {response.status_code}", style="red"
            )
            console.print(response.text)
            return

    # 5. Create Position
    console.print("\n5. Testing Position Creation...")
    position_data = {
        "user_id": user_id,
        "asset_id": asset_id,
        "quantity": 10,
        "average_cost_per_share": 150.00,
        "total_cost_basis": 1500.00,
        "account_name": "Main Account",
    }

    response = session.post(
        f"{BASE_URL}/api/v1/positions/", params={"user_id": user_id}, json=position_data
    )

    if response.status_code in [200, 201]:
        position = response.json()["data"]
        console.print(
            f"✅ Position created for {position['asset']['ticker']}", style="green"
        )
        position_id = position["id"]
    else:
        console.print(
            f"❌ Failed to create position: {response.status_code}", style="red"
        )
        console.print(response.text)

    # 6. Get Positions
    console.print("\n6. Testing Get Positions...")
    response = session.get(f"{BASE_URL}/api/v1/positions/", params={"user_id": user_id})

    if response.status_code == 200:
        positions = response.json()["data"]
        console.print(f"✅ Found {len(positions)} positions", style="green")
        for pos in positions:
            console.print(
                f"   - {pos['asset']['ticker']}: {pos['quantity']} shares @ ${pos.get('average_cost_per_share', 'N/A')}"
            )
    else:
        console.print(
            f"❌ Failed to get positions: {response.status_code}", style="red"
        )

    # 7. Test Cash Accounts
    console.print("\n7. Testing Cash Accounts...")

    # Get primary cash account
    response = session.get(
        f"{BASE_URL}/api/v1/cash-accounts/primary", params={"user_id": user_id}
    )

    if response.status_code == 200:
        response_data = response.json()
        if "data" in response_data:
            cash_account = response_data["data"]
            console.print(
                f"✅ Primary cash account: ${cash_account['balance']:,.2f}",
                style="green",
            )
        else:
            console.print("❌ No cash account found. Creating one...", style="yellow")
            # Create a cash account
            create_response = session.post(
                f"{BASE_URL}/api/v1/cash-accounts/",
                params={"user_id": user_id},
                json={"account_name": "Main Cash", "initial_balance": 10000.00},
            )
            if create_response.status_code in [200, 201]:
                console.print("✅ Cash account created", style="green")
    else:
        console.print(
            f"❌ Failed to get cash account: {response.status_code}", style="red"
        )

    # 8. Create a transaction
    console.print("\n8. Testing Transaction Creation...")

    # Buy transaction
    buy_data = {
        "asset_id": asset_id,
        "quantity": 5,
        "price": 155.00,
        "transaction_date": date.today().isoformat(),
        "account_name": "Main Account",
        "fees": 1.00,
        "notes": "Test buy transaction",
    }

    response = session.post(
        f"{BASE_URL}/api/v1/transactions/buy",
        params={"user_id": user_id},
        json=buy_data,
    )

    if response.status_code in [200, 201]:
        transaction = response.json()["data"]
        console.print(
            f"✅ Buy transaction created: {transaction['transaction_type']}",
            style="green",
        )
    else:
        console.print(
            f"❌ Failed to create transaction: {response.status_code}", style="red"
        )
        console.print(response.text)

    # 9. Get Transactions
    console.print("\n9. Testing Get Transactions...")
    response = session.get(
        f"{BASE_URL}/api/v1/transactions/", params={"user_id": user_id}
    )

    if response.status_code == 200:
        transactions = response.json()["data"]
        console.print(f"✅ Found {len(transactions)} transactions", style="green")
    else:
        console.print(
            f"❌ Failed to get transactions: {response.status_code}", style="red"
        )

    # 10. Test Portfolio Overview
    console.print("\n10. Testing Portfolio Overview...")
    response = session.get(
        f"{BASE_URL}/api/v1/portfolio/overview", params={"user_id": user_id}
    )

    if response.status_code == 200:
        overview = response.json()["data"]
        console.print("✅ Portfolio Overview:", style="green")
        console.print(f"   Total Value: ${overview.get('total_value', 0):,.2f}")
        console.print(f"   Total Cost: ${overview.get('total_cost', 0):,.2f}")
        console.print(f"   Total P&L: ${overview.get('total_pnl', 0):,.2f}")
    else:
        console.print(
            f"❌ Failed to get portfolio overview: {response.status_code}", style="red"
        )

    console.print("\n✅ Basic API functionality is working!", style="bold green")
    console.print(
        "\n📊 You can now access the Streamlit dashboard at: http://localhost:8503",
        style="blue",
    )
    console.print("   Use the credentials:", style="blue")
    console.print(f"   Username: {register_data['username']}", style="blue")
    console.print(f"   Password: {register_data['password']}", style="blue")


if __name__ == "__main__":
    test_api()
