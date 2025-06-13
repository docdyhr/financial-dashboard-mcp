"""Celery periodic task scheduler configuration."""
from celery.schedules import crontab

from backend.config import get_settings

settings = get_settings()

# Celery beat schedule for periodic tasks
beat_schedule = {
    # Update portfolio prices every hour during market hours (9 AM - 4 PM ET)
    "update-portfolio-prices-hourly": {
        "task": "update_portfolio_prices",
        "schedule": crontab(minute=0, hour="9-16"),  # Every hour from 9 AM to 4 PM
        "args": [None],  # Update for all users
    },
    # Create daily portfolio snapshots at market close (4:30 PM ET)
    "create-daily-snapshots": {
        "task": "create_portfolio_snapshot",
        "schedule": crontab(minute=30, hour=16),  # 4:30 PM ET
        "args": [None],  # Create for all users
    },
    # Comprehensive price update every 30 minutes during extended hours
    "update-prices-extended": {
        "task": "update_portfolio_prices",
        "schedule": crontab(minute="*/30", hour="6-20"),  # Every 30 min, 6 AM - 8 PM
        "args": [None],
    },
    # Weekly portfolio performance reports on Sundays at 8 PM
    "weekly-cleanup": {
        "task": "create_portfolio_snapshot",
        "schedule": crontab(minute=0, hour=20, day_of_week=0),  # Sunday 8 PM
        "args": [None],
    },
}
