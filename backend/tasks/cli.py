"""Management commands for task queue operations."""

import logging
from collections.abc import Sequence

import click

from backend.tasks.manager import task_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def cli() -> None:
    """Financial Dashboard Task Management CLI."""


@cli.command()
@click.option(
    "--symbols", "-s", multiple=True, help="Ticker symbols to fetch (e.g., AAPL GOOGL)"
)
@click.option(
    "--period", "-p", default="1d", help="Period for data fetch (default: 1d)"
)
def fetch_market_data(symbols: Sequence[str], period: str) -> None:
    """Fetch market data for specified symbols."""
    if not symbols:
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]  # Default symbols
        logger.info(f"No symbols specified, using defaults: {symbols}")

    symbols_list = list(symbols)
    logger.info(f"Submitting market data fetch for {len(symbols_list)} symbols")

    task_id = task_manager.submit_market_data_update(symbols_list, period)
    logger.info(f"Task submitted with ID: {task_id}")

    # Monitor task progress
    monitor_task(task_id)


@cli.command()
@click.option(
    "--user-id", "-u", type=int, help="User ID to update (omit for all users)"
)
def update_prices(user_id: int | None) -> None:
    """Update portfolio prices."""
    logger.info(f"Submitting portfolio price update for user: {user_id or 'all users'}")

    task_id = task_manager.submit_portfolio_price_update(user_id)
    logger.info(f"Task submitted with ID: {task_id}")

    # Monitor task progress
    monitor_task(task_id)


@cli.command()
@click.option("--ticker", "-t", required=True, help="Ticker symbol to fetch info for")
def fetch_asset_info(ticker: str) -> None:
    """Fetch detailed asset information."""
    logger.info(f"Submitting asset info fetch for: {ticker}")

    task_id = task_manager.submit_asset_info_fetch(ticker)
    logger.info(f"Task submitted with ID: {task_id}")

    # Monitor task progress
    monitor_task(task_id)


@cli.command()
@click.option("--user-id", "-u", type=int, required=True, help="User ID")
@click.option("--days", "-d", default=30, help="Days back for analysis (default: 30)")
def calculate_performance(user_id: int, days: int) -> None:
    """Calculate portfolio performance."""
    logger.info(f"Submitting portfolio performance calculation for user {user_id}")

    task_id = task_manager.submit_portfolio_performance_calculation(user_id, days)
    logger.info(f"Task submitted with ID: {task_id}")

    # Monitor task progress
    monitor_task(task_id)


@cli.command()
@click.option(
    "--user-id",
    "-u",
    type=int,
    help="User ID to create snapshot for (omit for all users)",
)
def create_snapshot(user_id: int | None) -> None:
    """Create portfolio snapshot."""
    logger.info(
        f"Submitting portfolio snapshot creation for user: {user_id or 'all users'}"
    )

    task_id = task_manager.submit_portfolio_snapshot_creation(user_id)
    logger.info(f"Task submitted with ID: {task_id}")

    # Monitor task progress
    monitor_task(task_id)


@cli.command()
@click.argument("task_id")
def status(task_id: str) -> None:
    """Check task status."""
    logger.info(f"Checking status for task: {task_id}")

    status_info = task_manager.get_task_status(task_id)

    print(f"\nTask ID: {status_info['task_id']}")
    print(f"Status: {status_info['status']}")
    print(f"Ready: {status_info['ready']}")

    if status_info.get("successful"):
        print("✅ Task completed successfully")
        if "result" in status_info:
            print(f"Result: {status_info['result']}")
    elif status_info.get("failed"):
        print("❌ Task failed")
        if "error" in status_info:
            print(f"Error: {status_info['error']}")
    elif "progress" in status_info:
        progress = status_info["progress"]
        print(f"Progress: {progress}")


@cli.command()
def list_active() -> None:
    """List active tasks."""
    logger.info("Fetching active tasks...")

    active_tasks = task_manager.get_active_tasks()

    if not active_tasks:
        print("No active tasks found.")
        return

    print(f"\nFound {len(active_tasks)} active tasks:")
    print("-" * 80)

    for task in active_tasks:
        print(f"Task ID: {task['task_id']}")
        print(f"Name: {task['name']}")
        print(f"Worker: {task['worker']}")
        print(f"Args: {task['args']}")
        if task.get("time_start"):
            print(f"Started: {task['time_start']}")
        print("-" * 40)


@cli.command()
def worker_stats() -> None:
    """Show worker statistics."""
    logger.info("Fetching worker statistics...")

    stats = task_manager.get_worker_stats()

    if "error" in stats:
        print(f"Error getting stats: {stats['error']}")
        return

    print(f"\nTotal Workers: {stats['total_workers']}")
    print(f"Total Active Tasks: {stats['total_active_tasks']}")
    print("\nWorker Details:")
    print("-" * 80)

    for worker, info in stats.get("workers", {}).items():
        print(f"Worker: {worker}")
        print(f"  Status: {info['status']}")
        print(f"  Total Tasks: {info['total_tasks']}")
        print(f"  Pool Processes: {info['pool_processes']}")
        print("-" * 40)


def monitor_task(task_id: str, max_wait: int = 300) -> None:
    """Monitor task progress until completion."""
    import time

    start_time = time.time()

    while time.time() - start_time < max_wait:
        status_info = task_manager.get_task_status(task_id)

        if status_info["ready"]:
            if status_info.get("successful"):
                logger.info("✅ Task completed successfully!")
                if "result" in status_info:
                    logger.info(f"Result: {status_info['result']}")
            else:
                logger.error("❌ Task failed!")
                if "error" in status_info:
                    logger.error(f"Error: {status_info['error']}")
            break
        if "progress" in status_info:
            progress = status_info["progress"]
            logger.info(f"Progress: {progress}")
        else:
            logger.info(f"Task status: {status_info['status']}")

        time.sleep(5)  # Check every 5 seconds
    else:
        logger.warning(f"Task monitoring timeout after {max_wait} seconds")


if __name__ == "__main__":
    cli()
