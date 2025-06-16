"""Test the task queue with simulated market data to demonstrate functionality."""

import sys
from decimal import Decimal
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database import get_db_session  # noqa: E402
from backend.models.asset import Asset, AssetCategory, AssetType  # noqa: E402
from backend.models.position import Position  # noqa: E402
from backend.models.user import User  # noqa: E402
from backend.tasks.manager import task_manager  # noqa: E402


def setup_test_data():
    """Set up test data for task queue testing."""
    print("🏗️  Setting up test data...")

    with get_db_session() as db:
        # Create test user if not exists
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            test_user = User(
                email="test@example.com", full_name="Test User", is_active=True
            )  # type: ignore[call-arg]
            db.add(test_user)
            db.flush()

        # Create test assets if not exist
        test_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        assets = []

        for symbol in test_symbols:
            asset = db.query(Asset).filter(Asset.ticker == symbol).first()
            if not asset:
                asset = Asset(
                    ticker=symbol,
                    name=f"{symbol} Test Company",
                    asset_type=AssetType.STOCK,
                    category=AssetCategory.EQUITY,
                    current_price=150.00 + len(symbol) * 10,  # Simulate prices
                    currency="USD",
                )  # type: ignore[call-arg]
                db.add(asset)
                db.flush()
            assets.append(asset)

        # Create test positions if not exist
        for asset in assets:
            position = (
                db.query(Position)
                .filter(Position.user_id == test_user.id, Position.asset_id == asset.id)
                .first()
            )

            if not position:
                position = Position(
                    user_id=test_user.id,
                    asset_id=asset.id,
                    quantity=Decimal("10.0"),
                    average_cost_per_share=Decimal("145.00"),
                    total_cost_basis=Decimal("1450.00"),
                    account_name="Test Account",
                    is_active=True,
                )  # type: ignore[call-arg]
                db.add(position)

        db.commit()
        print(f"✅ Test data ready: User {test_user.id} with {len(assets)} assets")
        return test_user.id, [a.ticker for a in assets]


def test_portfolio_performance_task(user_id):
    """Test portfolio performance calculation."""
    print("\n🧪 Testing portfolio performance calculation...")

    task_id = task_manager.submit_portfolio_performance_calculation(user_id, 30)
    print(f"   Task submitted: {task_id}")

    # Monitor task
    import time

    for i in range(15):
        status = task_manager.get_task_status(task_id)
        print(f"   Status: {status['status']}")

        if status["ready"]:
            if status.get("successful"):
                print("   ✅ Portfolio performance task completed!")
                result = status.get("result", {})
                metrics = result.get("metrics", {})
                summary = metrics.get("portfolio_summary", {})

                print("   📊 Portfolio Summary:")
                print(
                    f"      Total Value: ${summary.get('total_current_value', 0):,.2f}"
                )
                print(
                    f"      Total Cost Basis: ${summary.get('total_cost_basis', 0):,.2f}"
                )
                print(
                    f"      Unrealized P&L: ${summary.get('total_unrealized_gain_loss', 0):,.2f}"
                )
                print(f"      Total Positions: {summary.get('total_positions', 0)}")

                positions = metrics.get("positions", [])
                if positions:
                    print(
                        f"   📈 Top Position: {positions[0]['ticker']} (${positions[0]['current_value']:,.2f})"
                    )

                return True
            print("   ❌ Portfolio performance task failed!")
            print(f"   Error: {status.get('error')}")
            return False

        time.sleep(1)

    print("   ⏱️  Task still running after 15 seconds")
    return False


def test_portfolio_snapshot_task(user_id):
    """Test portfolio snapshot creation."""
    print("\n🧪 Testing portfolio snapshot creation...")

    task_id = task_manager.submit_portfolio_snapshot_creation(user_id)
    print(f"   Task submitted: {task_id}")

    # Monitor task
    import time

    for i in range(10):
        status = task_manager.get_task_status(task_id)
        print(f"   Status: {status['status']}")

        if status["ready"]:
            if status.get("successful"):
                print("   ✅ Portfolio snapshot task completed!")
                result = status.get("result", {})
                print(f"   📸 Snapshots created: {result.get('snapshots_created', 0)}")
                print(f"   👥 Users processed: {result.get('total_users_processed', 0)}")
                return True
            print("   ❌ Portfolio snapshot task failed!")
            print(f"   Error: {status.get('error')}")
            return False

        time.sleep(1)

    print("   ⏱️  Task still running after 10 seconds")
    return False


def test_concurrent_tasks():
    """Test multiple tasks running concurrently."""
    print("\n🧪 Testing concurrent task execution...")

    # Submit multiple tasks
    tasks = []

    # Task 1: Market data (will likely fail due to rate limits, but shows error handling)
    task1_id = task_manager.submit_market_data_update(["AAPL"], "1d")
    tasks.append(("Market Data", task1_id))

    # Task 2: Asset info (will likely fail due to rate limits)
    task2_id = task_manager.submit_asset_info_fetch("GOOGL")
    tasks.append(("Asset Info", task2_id))

    print(f"   Submitted {len(tasks)} concurrent tasks")

    # Monitor all tasks
    import time

    completed = set()

    for i in range(20):
        for name, task_id in tasks:
            if task_id in completed:
                continue

            status = task_manager.get_task_status(task_id)

            if status["ready"]:
                completed.add(task_id)
                if status.get("successful"):
                    print(f"   ✅ {name} completed successfully")
                else:
                    print(f"   ❌ {name} failed: {status.get('error', 'Unknown error')}")

        if len(completed) == len(tasks):
            break

        if i % 5 == 0:
            active_tasks = task_manager.get_active_tasks()
            print(f"   🔄 Active tasks: {len(active_tasks)}")

        time.sleep(1)

    print(f"   📊 Final status: {len(completed)}/{len(tasks)} tasks completed")
    return len(completed) == len(tasks)


def test_worker_management():
    """Test worker statistics and management."""
    print("\n🧪 Testing worker management...")

    # Get worker stats
    stats = task_manager.get_worker_stats()
    print("   📈 Worker Statistics:")
    print(f"      Total Workers: {stats.get('total_workers', 0)}")
    print(f"      Active Tasks: {stats.get('total_active_tasks', 0)}")

    for worker, info in stats.get("workers", {}).items():
        print(
            f"      Worker {worker}: {info['status']} ({info['total_tasks']} total tasks)"
        )

    # Get active tasks
    active_tasks = task_manager.get_active_tasks()
    print(f"   🔄 Active Tasks: {len(active_tasks)}")

    if active_tasks:
        for task in active_tasks[:3]:  # Show first 3
            print(f"      - {task['name']} ({task['task_id'][:8]}...)")

    return stats.get("total_workers", 0) > 0


def main():
    """Run comprehensive task queue testing."""
    print("🚀 Comprehensive Task Queue Testing with Real Data")
    print("=" * 60)

    # Check worker status first
    if not test_worker_management():
        print("\n❌ No workers available. Please start Celery worker first:")
        print("   celery -A backend.tasks worker --loglevel=info")
        return

    print("\n🏗️  Setting up test environment...")

    try:
        # Set up test data
        user_id, symbols = setup_test_data()

        # Test various task types
        tests_passed = 0
        total_tests = 3

        # Test 1: Portfolio Performance
        if test_portfolio_performance_task(user_id):
            tests_passed += 1

        # Test 2: Portfolio Snapshot
        if test_portfolio_snapshot_task(user_id):
            tests_passed += 1

        # Test 3: Concurrent Tasks
        if test_concurrent_tasks():
            tests_passed += 1

        # Final summary
        print("\n📊 Test Summary:")
        print(f"   ✅ Passed: {tests_passed}/{total_tests} tests")
        print(
            f"   📈 Task Queue Status: {'Healthy' if tests_passed >= 2 else 'Needs Attention'}"
        )

        if tests_passed >= 2:
            print("\n🎉 Task queue is working well with real data!")
            print("\n🔄 Next Steps:")
            print("   1. Monitor tasks with Flower: http://localhost:5555")
            print("   2. Check database for created snapshots and performance data")
            print("   3. Try the CLI tools: python backend/tasks/cli.py --help")
            print("   4. Set up periodic tasks with Celery Beat")
        else:
            print(
                "\n⚠️  Task queue needs attention. Check worker logs and database connectivity."
            )

    except Exception as e:
        print(f"\n❌ Error during testing: {e!s}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
