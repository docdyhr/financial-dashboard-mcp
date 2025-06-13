"""Task management and monitoring."""
import logging
from typing import Any

from celery.result import AsyncResult

from backend.tasks import celery_app

logger = logging.getLogger(__name__)


class TaskManager:
    """Manages task execution and monitoring."""

    def __init__(self):
        self.celery_app = celery_app

    def submit_market_data_update(self, symbols: list[str], period: str = "1d") -> str:
        """Submit market data fetch task."""
        task = self.celery_app.send_task("fetch_market_data", args=[symbols, period])
        logger.info(f"Submitted market data task {task.id} for symbols: {symbols}")
        return task.id

    def submit_portfolio_price_update(self, user_id: int | None = None) -> str:
        """Submit portfolio price update task."""
        task = self.celery_app.send_task("update_portfolio_prices", args=[user_id])
        logger.info(
            f"Submitted portfolio price update task {task.id} for user: {user_id}"
        )
        return task.id

    def submit_asset_info_fetch(self, ticker: str) -> str:
        """Submit asset info fetch task."""
        task = self.celery_app.send_task("fetch_asset_info", args=[ticker])
        logger.info(f"Submitted asset info task {task.id} for ticker: {ticker}")
        return task.id

    def submit_portfolio_performance_calculation(
        self, user_id: int, days_back: int = 30
    ) -> str:
        """Submit portfolio performance calculation task."""
        task = self.celery_app.send_task(
            "calculate_portfolio_performance", args=[user_id, days_back]
        )
        logger.info(
            f"Submitted portfolio performance task {task.id} for user: {user_id}"
        )
        return task.id

    def submit_portfolio_snapshot_creation(self, user_id: int | None = None) -> str:
        """Submit portfolio snapshot creation task."""
        task = self.celery_app.send_task("create_portfolio_snapshot", args=[user_id])
        logger.info(f"Submitted portfolio snapshot task {task.id} for user: {user_id}")
        return task.id

    def get_task_status(self, task_id: str) -> dict[str, Any]:
        """Get task status and result."""
        try:
            result = AsyncResult(task_id, app=self.celery_app)

            status_info = {
                "task_id": task_id,
                "status": result.status,
                "ready": result.ready(),
                "successful": result.successful() if result.ready() else None,
                "failed": result.failed() if result.ready() else None,
            }

            if result.ready():
                if result.successful():
                    status_info["result"] = result.result
                elif result.failed():
                    status_info["error"] = str(result.result)
            # Task is still running, check for progress updates
            elif hasattr(result, "info") and result.info:
                status_info["progress"] = result.info

            return status_info

        except Exception as e:
            logger.error(f"Error getting task status for {task_id}: {e!s}")
            return {"task_id": task_id, "status": "ERROR", "error": str(e)}

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        try:
            self.celery_app.control.revoke(task_id, terminate=True)
            logger.info(f"Cancelled task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e!s}")
            return False

    def get_active_tasks(self) -> list[dict[str, Any]]:
        """Get list of active tasks."""
        try:
            active_tasks = []
            inspect = self.celery_app.control.inspect()

            # Get active tasks from all workers
            active = inspect.active()
            if active:
                for worker, tasks in active.items():
                    for task in tasks:
                        active_tasks.append(
                            {
                                "task_id": task["id"],
                                "name": task["name"],
                                "worker": worker,
                                "args": task.get("args", []),
                                "kwargs": task.get("kwargs", {}),
                                "time_start": task.get("time_start"),
                            }
                        )

            return active_tasks

        except Exception as e:
            logger.error(f"Error getting active tasks: {e!s}")
            return []

    def get_worker_stats(self) -> dict[str, Any]:
        """Get worker statistics."""
        try:
            inspect = self.celery_app.control.inspect()

            stats = {"workers": {}, "total_workers": 0, "total_active_tasks": 0}

            # Get worker stats
            worker_stats = inspect.stats()
            if worker_stats:
                for worker, worker_info in worker_stats.items():
                    stats["workers"][worker] = {
                        "status": "online",
                        "total_tasks": worker_info.get("total", {}).get("tasks", 0),
                        "pool_processes": worker_info.get("pool", {}).get(
                            "processes", 0
                        ),
                        "rusage": worker_info.get("rusage", {}),
                    }
                    stats["total_workers"] += 1

            # Get active task count
            active = inspect.active()
            if active:
                for worker, tasks in active.items():
                    stats["total_active_tasks"] += len(tasks)

            return stats

        except Exception as e:
            logger.error(f"Error getting worker stats: {e!s}")
            return {"error": str(e)}


# Global task manager instance
task_manager = TaskManager()
