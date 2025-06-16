"""Celery tasks for Financial Dashboard."""

from celery import Celery

from backend.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "financial_dashboard",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["backend.tasks"])

# Explicitly import task modules to ensure registration
from backend.tasks import market_data, portfolio

# Import beat schedule
try:
    from backend.tasks.schedule import beat_schedule

    celery_app.conf.beat_schedule = beat_schedule
except ImportError:
    pass
