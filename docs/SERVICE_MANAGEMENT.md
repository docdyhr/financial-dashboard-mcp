# Service Management Guide

This guide provides comprehensive instructions for setting up, starting, stopping, and troubleshooting all services required by the Financial Dashboard application.

## Overview

The Financial Dashboard consists of multiple interconnected services:

- **PostgreSQL**: Database for persistent storage
- **Redis**: In-memory cache and message broker
- **FastAPI Backend**: Core API server
- **Celery Worker**: Background task processing
- **Celery Beat**: Scheduled task execution
- **Flower**: Celery monitoring UI
- **Streamlit Frontend**: User interface
- **MCP Server**: AI integration for Claude Desktop

## Quick Start

### Prerequisites

Ensure you have the following installed:

```bash
# macOS
brew install postgresql redis python

# Ubuntu/Debian
sudo apt-get install postgresql redis-server python3 python3-pip

# Check installations
python3 --version    # Should be 3.11+
postgres --version   # Should be 14+
redis-server --version
```

### Starting All Services

```bash
# Navigate to project directory
cd /path/to/financial-dashboard-mcp

# Start all services at once
./scripts/services.sh start all
```

This will:
1. ✅ Initialize PostgreSQL database if needed
2. ✅ Start Redis server
3. ✅ Launch FastAPI backend
4. ✅ Start Celery worker and beat scheduler
5. ✅ Launch Flower monitoring UI
6. ✅ Start Streamlit frontend
7. ✅ Run database migrations

### Checking Service Status

```bash
./scripts/services.sh status
```

Expected output:
```
[INFO] Service Status:
==================================
postgres:    ✅ RUNNING (port 5432)
redis:       ✅ RUNNING (port 6379)
backend:     ✅ RUNNING (port 8000)
celery:      ✅ RUNNING
celery-beat: ✅ RUNNING
flower:      ✅ RUNNING (port 5555)
frontend:    ✅ RUNNING (port 8501)
mcp:         ❌ STOPPED (normal - only runs on demand)
```

### Service URLs

Once running, access the services at:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:8501 | None |
| **Backend API** | http://localhost:8000 | None |
| **API Documentation** | http://localhost:8000/docs | None |
| **Flower (Celery Monitor)** | http://localhost:5555 | admin:admin |
| **PostgreSQL** | postgresql://financial_user:dev_password@localhost:5432/financial_dashboard | financial_user:dev_password |
| **Redis** | redis://localhost:6379/0 | None |

## Individual Service Management

### Starting Individual Services

```bash
# Start specific services
./scripts/services.sh start postgres
./scripts/services.sh start redis
./scripts/services.sh start backend
./scripts/services.sh start celery
./scripts/services.sh start flower
./scripts/services.sh start frontend
```

### Stopping Services

```bash
# Stop all services
./scripts/services.sh stop all

# Stop specific service
./scripts/services.sh stop celery
```

### Restarting Services

```bash
# Restart all services
./scripts/services.sh restart all

# Restart specific service
./scripts/services.sh restart backend
```

## Health Checks

### Automated Health Checks

```bash
./scripts/services.sh health
```

This checks:
- ✅ PostgreSQL: Database connectivity
- ✅ Redis: PING response
- ✅ Backend: HTTP health endpoint
- ✅ Frontend: Streamlit health endpoint
- ✅ Flower: UI accessibility

### Manual Health Checks

```bash
# PostgreSQL
psql -h localhost -U financial_user -d financial_dashboard -c '\q'

# Redis
redis-cli ping

# Backend API
curl http://localhost:8000/health

# Frontend
curl http://localhost:8501/_stcore/health

# Flower
curl -u admin:admin http://localhost:5555
```

## Logs and Debugging

### Viewing Logs

```bash
# View all logs
./scripts/services.sh logs all

# Follow specific service logs
./scripts/services.sh logs celery
./scripts/services.sh logs backend
./scripts/services.sh logs postgres

# Direct log file access
tail -f logs/celery.log
tail -f logs/backend.log
tail -f logs/postgres.log
```

### Log Locations

All logs are stored in the `logs/` directory:

```
logs/
├── backend.log         # FastAPI backend
├── celery.log         # Celery worker
├── celery-beat.log    # Celery scheduler
├── flower.log         # Flower monitoring
├── frontend.log       # Streamlit frontend
├── mcp.log           # MCP server
├── postgres.log      # PostgreSQL database
├── redis.log         # Redis server
└── service_manager.log # Service management script
```

## Database Management

### Running Migrations

```bash
# Run database migrations
./scripts/services.sh migrate

# Or manually with Alembic
alembic upgrade head
```

### Database Access

```bash
# Connect to database
psql -h localhost -U financial_user -d financial_dashboard

# Common SQL commands
\l                    # List databases
\dt                   # List tables
\d table_name         # Describe table
SELECT * FROM assets; # Query data
```

### Database Reset

```bash
# Reset database (destructive!)
alembic downgrade base
alembic upgrade head
```

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Error**: `Address already in use: port XXXX`

**Solution**:
```bash
# Find process using port
lsof -i :8000
lsof -i :5432

# Kill process
kill -9 <PID>

# Or use the service manager
./scripts/services.sh stop all
```

#### 2. PostgreSQL Won't Start

**Error**: `PostgreSQL failed to start`

**Solutions**:
```bash
# Check if data directory exists
ls -la data/postgres/

# Reinitialize if needed
rm -rf data/postgres
./scripts/services.sh start postgres

# Check PostgreSQL logs
tail -f logs/postgres.log
```

#### 3. Celery Connection Error

**Error**: `kombu.exceptions.OperationalError: [Errno 61] Connection refused`

**Solutions**:
```bash
# Ensure Redis is running
./scripts/services.sh start redis

# Check Redis connectivity
redis-cli ping

# Restart Celery
./scripts/services.sh restart celery
```

#### 4. Backend Import Errors

**Error**: `ModuleNotFoundError` or `ImportError`

**Solutions**:
```bash
# Install dependencies
pip install -e .

# Check Python path
echo $PYTHONPATH

# Activate virtual environment
source .venv/bin/activate
```

#### 5. Frontend Won't Start

**Error**: Streamlit connection errors

**Solutions**:
```bash
# Check backend is running
curl http://localhost:8000/health

# Check environment variables
cat .env | grep BACKEND_URL

# Restart frontend
./scripts/services.sh restart frontend
```

### Environment Issues

#### Missing .env File

```bash
# Copy example file
cp .env.example .env

# Edit configuration
nano .env
```

#### Invalid Environment Variables

Check for these common issues in `.env`:
- ✅ No spaces around `=`
- ✅ No trailing commas in arrays
- ✅ Proper URL formats
- ✅ Valid port numbers

### Performance Issues

#### High CPU Usage

```bash
# Check Celery worker load
./scripts/services.sh logs celery

# Reduce Celery concurrency
# Edit scripts/services.sh, change --concurrency=2 to --concurrency=1
```

#### Memory Issues

```bash
# Monitor memory usage
top -p $(pgrep -f "python")

# Restart services to free memory
./scripts/services.sh restart all
```

## Development Workflow

### Starting Development Environment

```bash
# 1. Start core services
./scripts/services.sh start postgres
./scripts/services.sh start redis

# 2. Start backend in development mode
./scripts/services.sh start backend

# 3. Start task processing
./scripts/services.sh start celery
./scripts/services.sh start flower

# 4. Start frontend
./scripts/services.sh start frontend
```

### Code Changes

- **Backend changes**: Service auto-reloads with `--reload` flag
- **Frontend changes**: Streamlit auto-reloads on file changes
- **Task changes**: Restart Celery worker: `./scripts/services.sh restart celery`

### Testing

```bash
# Run tests
make test

# Test specific component
python scripts/test_frontend_components.py
python scripts/test_mcp_server.py

# Test services
./scripts/services.sh health
```

## Production Considerations

### Security

1. **Change default passwords**:
   - PostgreSQL: `financial_user:dev_password`
   - Flower: `admin:admin`

2. **Update secret keys**:
   - `SECRET_KEY` in .env
   - `MCP_AUTH_TOKEN` in .env

3. **Configure firewall**:
   - Only expose necessary ports
   - Use HTTPS in production

### Performance

1. **Database optimization**:
   - Tune PostgreSQL configuration
   - Add database indexes
   - Regular VACUUM operations

2. **Celery scaling**:
   - Increase worker concurrency
   - Use multiple worker nodes
   - Monitor task queue length

3. **Caching**:
   - Configure Redis persistence
   - Implement application-level caching
   - Use Redis clustering for scale

### Monitoring

1. **Service monitoring**:
   ```bash
   # Continuous monitoring
   watch -n 10 './scripts/services.sh status'
   ```

2. **Log aggregation**:
   - Centralize logs with tools like ELK stack
   - Set up log rotation
   - Monitor error patterns

3. **Alerts**:
   - Set up health check alerts
   - Monitor disk space and memory
   - Track application metrics

## Alternative: Docker Deployment

For a containerized deployment:

```bash
# Build images
make docker-build

# Start all services
make docker-up

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
make docker-down
```

## Service Dependencies

```mermaid
graph TD
    A[PostgreSQL] --> C[Backend]
    B[Redis] --> C[Backend]
    B --> D[Celery Worker]
    B --> E[Celery Beat]
    B --> F[Flower]
    C --> G[Frontend]
    C --> H[MCP Server]
    D --> F
```

## Command Reference

| Command | Description |
|---------|-------------|
| `./scripts/services.sh start all` | Start all services |
| `./scripts/services.sh stop all` | Stop all services |
| `./scripts/services.sh restart all` | Restart all services |
| `./scripts/services.sh status` | Show service status |
| `./scripts/services.sh health` | Run health checks |
| `./scripts/services.sh logs [service]` | View service logs |
| `./scripts/services.sh urls` | Show service URLs |
| `./scripts/services.sh migrate` | Run database migrations |
| `./scripts/services.sh help` | Show help |

## Support

For additional help:

1. **Check logs**: `./scripts/services.sh logs all`
2. **Run health checks**: `./scripts/services.sh health`
3. **Review documentation**: All `.md` files in `docs/` directory
4. **Test components**: Run test scripts in `scripts/` directory

The service management system is designed to be robust and handle most common scenarios automatically. For complex issues, examine the logs and use the individual service commands to isolate problems.
