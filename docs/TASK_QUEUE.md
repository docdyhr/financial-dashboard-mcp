# Task Queue Setup (Celery + Redis)

The Financial Dashboard uses Celery with Redis as the message broker for background task processing. This enables asynchronous operations like market data fetching, portfolio analytics, and scheduled updates.

## Architecture

- **Celery**: Distributed task queue for asynchronous processing
- **Redis**: Message broker and result backend
- **Celery Beat**: Scheduler for periodic tasks
- **Flower**: Web-based monitoring tool (optional)

## Components

### 1. Task Types

#### Market Data Tasks

- `fetch_market_data`: Fetch historical data for multiple symbols
- `update_portfolio_prices`: Update current prices for portfolio assets
- `fetch_asset_info`: Get detailed information for a single asset

#### Portfolio Analytics Tasks

- `calculate_portfolio_performance`: Compute performance metrics
- `create_portfolio_snapshot`: Create daily portfolio snapshots
- `generate_portfolio_report`: Generate comprehensive reports

### 2. Scheduled Tasks (Celery Beat)

Automatic periodic tasks configured in `backend/tasks/schedule.py`:

- **Hourly Price Updates**: Update portfolio prices during market hours (9 AM - 4 PM ET)
- **Daily Snapshots**: Create portfolio snapshots at market close (4:30 PM ET)
- **Extended Hours Updates**: Price updates every 30 minutes (6 AM - 8 PM ET)
- **Weekly Cleanup**: Portfolio maintenance on Sundays

### 3. Task Management API

RESTful endpoints for task control:

``` text
POST /api/v1/tasks/market-data        # Submit market data fetch
POST /api/v1/tasks/portfolio-prices   # Update portfolio prices
POST /api/v1/tasks/asset-info         # Fetch asset information
POST /api/v1/tasks/portfolio-performance  # Calculate performance
POST /api/v1/tasks/portfolio-snapshot # Create snapshots

GET  /api/v1/tasks/status/{task_id}   # Check task status
DELETE /api/v1/tasks/cancel/{task_id} # Cancel running task
GET  /api/v1/tasks/active             # List active tasks
GET  /api/v1/tasks/workers            # Worker statistics
```

## Setup and Usage

### Local Development

#### Prerequisites

1. Redis server running locally
2. Python environment with dependencies installed

#### Start Redis (macOS with Homebrew)

```bash
brew services start redis
```

#### Start Task Queue Components

```bash
# All-in-one startup script
./scripts/start_task_queue.sh

# Or manually:
# Worker
celery -A backend.tasks worker --loglevel=info

# Beat scheduler
celery -A backend.tasks beat --loglevel=info

# Flower monitoring (optional)
celery -A backend.tasks flower --port=5555
```

#### Using the CLI

```bash
# Update all portfolio prices
python backend/tasks/cli.py update-prices

# Fetch market data for specific symbols
python backend/tasks/cli.py fetch-market-data -s AAPL -s GOOGL -s MSFT

# Calculate portfolio performance for user 1
python backend/tasks/cli.py calculate-performance -u 1 -d 30

# Check task status
python backend/tasks/cli.py status <task-id>

# List active tasks
python backend/tasks/cli.py list-active

# Show worker statistics
python backend/tasks/cli.py worker-stats
```

### Docker Deployment

The `docker-compose.yml` includes all necessary services:

```bash
# Start all services including task queue
docker-compose up -d

# Scale workers for high load
docker-compose up -d --scale celery_worker=3

# View logs
docker-compose logs celery_worker
docker-compose logs celery_beat
docker-compose logs flower
```

### Production Configuration

#### Environment Variables

```bash
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
REDIS_URL=redis://localhost:6379/0
```

#### Recommended Settings

- Use Redis Sentinel for high availability
- Configure Redis persistence (AOF + RDB)
- Set up monitoring with Flower or Prometheus
- Use multiple worker processes for parallel execution
- Configure task routing for different priorities

## Task Development

### Creating New Tasks

1. **Define the task** in appropriate module (`backend/tasks/`)

```python
@celery_app.task(bind=True, name="my_custom_task")
def my_custom_task(self, param1: str, param2: int) -> dict:
    try:
        # Task logic here
        current_task.update_state(
            state="PROGRESS",
            meta={"status": "Processing..."}
        )

        result = {"status": "completed", "data": "result"}
        return result

    except Exception as e:
        current_task.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise
```

2. **Add task manager method** in `backend/tasks/manager.py`

```python
def submit_my_custom_task(self, param1: str, param2: int) -> str:
    task = self.celery_app.send_task(
        "my_custom_task",
        args=[param1, param2]
    )
    return task.id
```

3. **Add API endpoint** in `backend/api/tasks.py`

```python
@router.post("/my-task")
async def submit_my_task(request: MyTaskRequest):
    task_id = task_manager.submit_my_custom_task(
        request.param1, request.param2
    )
    return TaskResponse(task_id=task_id, status="submitted")
```

### Adding Scheduled Tasks

Update `backend/tasks/schedule.py`:

```python
beat_schedule = {
    "my-scheduled-task": {
        "task": "my_custom_task",
        "schedule": crontab(minute=0, hour=8),  # Daily at 8 AM
        "args": ["default_param", 42],
    },
}
```

## Monitoring and Debugging

### Flower Dashboard

- URL: <http://localhost:5555> (local) or <http://your-domain:5555>
- Features: Task monitoring, worker stats, task history, real-time updates

### Log Files

- Worker logs: `logs/celery_worker.log`
- Beat logs: `logs/celery_beat.log`
- Flower logs: `logs/flower.log`

### Common Issues

1. **Tasks not executing**: Check Redis connection and worker status
2. **Memory issues**: Increase worker memory or restart workers periodically
3. **Stuck tasks**: Use `celery -A backend.tasks purge` to clear queue
4. **Beat not scheduling**: Ensure only one beat process is running

### Performance Tuning

- **Worker concurrency**: Adjust based on CPU cores and I/O requirements
- **Task routing**: Use different queues for CPU vs I/O intensive tasks
- **Result expiration**: Set appropriate `result_expires` in configuration
- **Prefetch settings**: Tune `worker_prefetch_multiplier` for workload

## Security Considerations

- Use authentication for Flower in production
- Secure Redis with password and network restrictions
- Validate all task inputs to prevent injection attacks
- Use task rate limiting for external API calls
- Monitor for unusual task patterns or failures

---

For more details, see the individual task modules in `backend/tasks/` and the API documentation.
