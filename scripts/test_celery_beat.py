#!/usr/bin/env python3
"""Test Celery Beat periodic task scheduling."""

import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.tasks import celery_app
from backend.tasks.schedule import beat_schedule


def show_beat_schedule():
    """Display the configured Celery beat schedule."""
    print("📅 Celery Beat Schedule Configuration")
    print("=" * 50)

    if not beat_schedule:
        print("❌ No beat schedule configured!")
        return

    for task_name, task_config in beat_schedule.items():
        print(f"\n📋 Task: {task_name}")
        print(f"   - Task function: {task_config['task']}")
        print(f"   - Schedule: {task_config['schedule']}")
        print(f"   - Arguments: {task_config.get('args', 'None')}")

        # Parse crontab schedule if available
        schedule = task_config["schedule"]
        if hasattr(schedule, "minute"):
            print("   - Cron details:")
            print(f"     • Minute: {schedule.minute}")
            print(f"     • Hour: {schedule.hour}")
            if hasattr(schedule, "day_of_week"):
                print(f"     • Day of week: {schedule.day_of_week}")


def test_manual_task_execution():
    """Test executing periodic tasks manually."""
    print("\n\n🧪 Testing Manual Task Execution")
    print("=" * 50)

    # Test update_portfolio_prices task
    print("\n1️⃣ Testing portfolio price update task...")

    try:
        from backend.tasks.market_data import update_portfolio_prices

        # Execute task asynchronously
        result = update_portfolio_prices.delay(user_id=None)
        print(f"   ✅ Task submitted: {result.id}")
        print("   ⏳ Waiting for result...")

        # Wait for result with timeout
        task_result = result.get(timeout=30)
        print("   ✅ Task completed!")
        print(f"   - Updated: {task_result['updated_count']} tickers")
        print(f"   - Failed: {task_result['failed_count']} tickers")

    except Exception as e:
        print(f"   ❌ Error: {e}")


def check_celery_beat_status():
    """Check if Celery beat is running."""
    print("\n\n🔍 Checking Celery Beat Status")
    print("=" * 50)

    try:
        # Check if Celery workers are available
        inspect = celery_app.control.inspect()
        stats = inspect.stats()

        if stats:
            print("✅ Celery workers are running:")
            for worker, info in stats.items():
                print(f"   - Worker: {worker}")
                print(f"     • Total tasks: {info.get('total', 0)}")
        else:
            print("❌ No Celery workers found!")
            print("   Run: docker-compose logs celery_worker")

        # Check scheduled tasks
        scheduled = inspect.scheduled()
        if scheduled:
            print("\n📅 Scheduled tasks:")
            for worker, tasks in scheduled.items():
                print(f"   Worker {worker}: {len(tasks)} scheduled tasks")

    except Exception as e:
        print(f"❌ Error checking Celery status: {e}")
        print("   Make sure Celery worker is running!")


def show_next_executions():
    """Calculate and show next execution times for periodic tasks."""
    print("\n\n⏰ Next Task Execution Times")
    print("=" * 50)

    from datetime import datetime, timedelta

    from celery.schedules import crontab

    now = datetime.now()
    print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    for task_name, task_config in beat_schedule.items():
        schedule = task_config["schedule"]

        if isinstance(schedule, crontab):
            print(f"\n📋 {task_name}:")

            # This is a simplified calculation
            if schedule.minute == 0 and schedule.hour == "9-16":
                print("   Runs every hour from 9 AM to 4 PM")
                next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(
                    hours=1
                )
                if 9 <= next_hour.hour <= 16:
                    print(f"   Next run: {next_hour.strftime('%Y-%m-%d %H:%M:%S')}")
            elif schedule.minute == "*/30":
                print("   Runs every 30 minutes")
                if now.minute < 30:
                    next_run = now.replace(minute=30, second=0, microsecond=0)
                else:
                    next_run = now.replace(
                        minute=0, second=0, microsecond=0
                    ) + timedelta(hours=1)
                print(f"   Next run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    print("🚀 Celery Beat Testing Tool")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Show configured schedule
    show_beat_schedule()

    # Check Celery status
    check_celery_beat_status()

    # Show next execution times
    show_next_executions()

    # Test manual execution
    print("\n\n💡 To start Celery beat scheduler, run:")
    print(
        "   docker-compose exec celery_beat celery -A backend.tasks beat --loglevel=info"
    )
    print("\n💡 To see Celery worker logs:")
    print("   docker-compose logs -f celery_worker")
    print("\n💡 To monitor tasks in Flower UI:")
    print("   Open http://localhost:5555")
