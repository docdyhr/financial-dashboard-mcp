"""Test script for task queue functionality."""
import sys
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.tasks.manager import task_manager


def test_market_data_task():
    """Test market data fetch task."""
    print("🧪 Testing market data fetch...")

    symbols = ["AAPL", "GOOGL"]
    task_id = task_manager.submit_market_data_update(symbols, "1d")
    print(f"   Submitted task: {task_id}")

    # Monitor task for a bit
    for i in range(10):
        status = task_manager.get_task_status(task_id)
        print(f"   Status: {status['status']}")

        if status["ready"]:
            if status.get("successful"):
                print("   ✅ Market data task completed successfully!")
                result = status.get("result", {})
                print(
                    f"   Result: {result.get('status')} - {result.get('total_processed', 0)} symbols processed"
                )
            else:
                print("   ❌ Market data task failed!")
                print(f"   Error: {status.get('error')}")
            break

        time.sleep(2)
    else:
        print("   ⏱️  Task still running after 20 seconds")

    return task_id


def test_asset_info_task():
    """Test asset info fetch task."""
    print("🧪 Testing asset info fetch...")

    task_id = task_manager.submit_asset_info_fetch("AAPL")
    print(f"   Submitted task: {task_id}")

    # Monitor task for a bit
    for i in range(10):
        status = task_manager.get_task_status(task_id)
        print(f"   Status: {status['status']}")

        if status["ready"]:
            if status.get("successful"):
                print("   ✅ Asset info task completed successfully!")
                result = status.get("result", {})
                print(f"   Current price: ${result.get('current_price', 'N/A')}")
            else:
                print("   ❌ Asset info task failed!")
                print(f"   Error: {status.get('error')}")
            break

        time.sleep(2)
    else:
        print("   ⏱️  Task still running after 20 seconds")

    return task_id


def test_worker_stats():
    """Test worker statistics."""
    print("🧪 Testing worker statistics...")

    stats = task_manager.get_worker_stats()
    if "error" in stats:
        print(f"   ❌ Error getting stats: {stats['error']}")
        return False

    print(f"   Total workers: {stats.get('total_workers', 0)}")
    print(f"   Active tasks: {stats.get('total_active_tasks', 0)}")

    if stats.get("total_workers", 0) > 0:
        print("   ✅ Workers are running!")
        return True
    print("   ⚠️  No workers found - make sure Celery worker is running")
    return False


def test_active_tasks():
    """Test active task listing."""
    print("🧪 Testing active task listing...")

    active_tasks = task_manager.get_active_tasks()
    print(f"   Found {len(active_tasks)} active tasks")

    if active_tasks:
        for task in active_tasks[:3]:  # Show first 3
            print(f"   - {task['name']} ({task['task_id'][:8]}...)")

    return True


def main():
    """Run all tests."""
    print("🚀 Task Queue Test Suite")
    print("=" * 50)

    # Test worker connectivity first
    if not test_worker_stats():
        print("\n❌ Workers not available. Please start Celery worker first:")
        print("   celery -A backend.tasks worker --loglevel=info")
        return

    print()

    # Test basic task functionality
    test_market_data_task()
    print()

    test_asset_info_task()
    print()

    test_active_tasks()
    print()

    print("✅ Task queue tests completed!")
    print("\n📊 Next steps:")
    print("   1. Check Flower dashboard: http://localhost:5555")
    print("   2. Monitor logs in logs/ directory")
    print("   3. Try the CLI: python backend/tasks/cli.py --help")


if __name__ == "__main__":
    main()
