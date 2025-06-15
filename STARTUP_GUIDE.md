# Financial Dashboard - Quick Start Guide

## Prerequisites

- Python 3.11.13
- PostgreSQL (for database)
- Redis (for Celery tasks)
- Docker (optional, for containerized setup)

## Quick Setup

### 1. Clone and Setup Environment

```bash
git clone https://github.com/docdyhr/financial-dashboard-mcp.git
cd financial-dashboard-mcp
```

### 2. Install Dependencies

```bash
# Create virtual environment (automatically activated with direnv)
python -m venv .venv
source .venv/bin/activate

# Install all dependencies
make install-dev
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings:
# - DATABASE_URL (PostgreSQL connection)
# - REDIS_URL (Redis connection)
# - API keys for financial data providers
```

### 4. Start Services

#### Option A: Local Development

```bash
# Terminal 1: Backend API
make run-backend
# Available at http://localhost:8000

# Terminal 2: Frontend Dashboard
make run-frontend
# Available at http://localhost:8501

# Terminal 3: Celery Worker (optional)
make run-celery

# Terminal 4: Celery Beat Scheduler (optional)
make run-celery-beat
```

#### Option B: Docker Setup

```bash
# Build and start all services
make docker-up

# Stop services
make docker-down
```

## Essential Commands

### Development

```bash
make format      # Format code
make lint        # Run linters
make test        # Run tests
make test-cov    # Run tests with coverage
```

### Database

```bash
make migrate-create message="add new table"  # Create migration
make migrate-up                               # Apply migrations
make migrate-down                             # Rollback migration
```

### Monitoring

```bash
make run-flower  # Celery task monitor at http://localhost:5555
```

## Accessing the Application

- **Frontend Dashboard**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Celery Flower**: http://localhost:5555 (when running)

## Common Issues & Solutions

### Port Already in Use

```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use different ports in .env
BACKEND_PORT=8001
FRONTEND_PORT=8502
```

### Database Connection Failed

1. Ensure PostgreSQL is running:
   ```bash
   # macOS
   brew services start postgresql

   # Linux
   sudo systemctl start postgresql
   ```

2. Check DATABASE_URL in .env:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/financial_dashboard
   ```

### Redis Connection Failed

1. Ensure Redis is running:
   ```bash
   # macOS
   brew services start redis

   # Linux
   sudo systemctl start redis
   ```

2. Check REDIS_URL in .env:
   ```
   REDIS_URL=redis://localhost:6379/0
   ```

### Missing Dependencies

```bash
# Reinstall all dependencies
make clean
make install-dev
```

### Pre-commit Hook Failures

```bash
# Run pre-commit manually
pre-commit run --all-files

# Skip hooks temporarily
git commit --no-verify
```

## First Time Usage

1. **Create Initial Portfolio**: Navigate to "Portfolio" in the sidebar
2. **Add Assets**: Use "Add Asset" to input stocks, bonds, or cash positions
3. **View Dashboard**: Return to main dashboard for portfolio overview
4. **Set Up Data Sources**: Configure API keys in Settings for real-time data

## Development Workflow

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and test: `make test`
3. Format and lint: `make format lint`
4. Commit with conventional commits: `git commit -m "feat: add new feature"`
5. Push and create PR: `git push -u origin feature/your-feature`

## Getting Help

- Check logs: `docker logs financial-dashboard-backend` (if using Docker)
- API docs: http://localhost:8000/docs
- Project documentation: See `/docs` directory
- Report issues: https://github.com/docdyhr/financial-dashboard-mcp/issues
