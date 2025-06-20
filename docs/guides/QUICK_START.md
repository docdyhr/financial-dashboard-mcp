# Quick Start Guide

Get the Financial Dashboard running in under 5 minutes.

## Prerequisites

- Python 3.11.13
- PostgreSQL (running locally or via Docker)
- Redis (running locally or via Docker)

## 🚀 Fastest Setup (Recommended)

### 1. Clone and Setup

```bash
git clone https://github.com/docdyhr/financial-dashboard-mcp.git
cd financial-dashboard-mcp
```

### 2. One-Command Start

```bash
# This script handles everything: dependencies, services, and startup
./scripts/start_dashboard.sh
```

That's it! The script will:
- Install all dependencies
- Start PostgreSQL and Redis (if needed)
- Run database migrations
- Start all services in the background

**Access your dashboard:**
- 🌐 **Frontend**: http://localhost:8501
- 🔧 **API Docs**: http://localhost:8000/docs
- 📊 **Task Monitor**: http://localhost:5555

## 🛠️ Manual Setup (Advanced Users)

### 1. Environment Setup

```bash
# Activate virtual environment (auto-configured with direnv)
source .venv/bin/activate

# Install dependencies
make install-dev
```

### 2. Configure Environment

```bash
# Copy and edit configuration
cp .env.example .env

# Required settings:
# DATABASE_URL=postgresql://user:password@localhost:5432/financial_dashboard
# REDIS_URL=redis://localhost:6379/0
# MCP_AUTH_TOKEN=your-secure-random-token
```

### 3. Start Services

Choose your preferred method:

#### Option A: All Services at Once
```bash
make run-all  # Shows commands to run in separate terminals
```

#### Option B: Individual Services
```bash
# Terminal 1: Backend API
make run-backend

# Terminal 2: Frontend Dashboard
make run-frontend

# Terminal 3: Background Tasks
make run-celery

# Terminal 4: Task Scheduler
make run-celery-beat

# Terminal 5: Task Monitor
make run-flower
```

#### Option C: Docker (Complete Isolation)
```bash
make docker-up    # Start all services
make docker-logs  # View logs
make docker-down  # Stop all services
```

## 🎯 First Steps

### 1. Explore the Dashboard
- Navigate to http://localhost:8501
- Check the sidebar for different sections:
  - **Dashboard**: Portfolio overview
  - **Portfolio**: Manage your assets
  - **Analytics**: Performance metrics
  - **Settings**: Configuration options

### 2. Add Your First Assets
1. Go to **Portfolio** → **Add New Asset**
2. Enter sample data:
   - Symbol: `AAPL`
   - Quantity: `10`
   - Purchase Price: `150.00`
3. Click **Add Asset**

### 3. View Live Data
- Return to **Dashboard** to see your portfolio
- Real-time prices are fetched automatically
- Performance metrics update every 15 minutes

## 🤖 AI Integration (Claude Desktop)

### Setup MCP Server
1. Follow the detailed guide: [MCP Setup](MCP_SETUP.md)
2. Or use auto-configuration:
   ```bash
   python scripts/add_to_claude_config.py
   ```

### Test AI Features
Once configured, ask Claude:
- "Show me my current portfolio positions"
- "What's my portfolio performance this year?"
- "Recommend an allocation for moderate risk tolerance"

## 🔧 Common Commands

### Development
```bash
make format      # Format code (black, isort, ruff)
make lint        # Run linters (ruff, flake8, mypy)
make test        # Run test suite
make test-cov    # Run tests with coverage report
```

### Database
```bash
make migrate-up                              # Apply migrations
make migrate-create message="add new table" # Create migration
make db-reset                                # Reset database
```

### Services
```bash
make run-backend   # FastAPI backend (port 8000)
make run-frontend  # Streamlit frontend (port 8501)
make run-celery    # Background worker
make run-flower    # Task monitor (port 5555)
```

## 🚨 Troubleshooting

### Port Already in Use
```bash
# Find and kill process
lsof -ti:8501 | xargs kill -9  # Frontend
lsof -ti:8000 | xargs kill -9  # Backend

# Or change ports in .env
FRONTEND_PORT=8502
BACKEND_PORT=8001
```

### Database Connection Failed
```bash
# Start PostgreSQL
brew services start postgresql  # macOS
sudo systemctl start postgresql # Linux

# Check connection
psql -h localhost -p 5432 -U postgres
```

### Redis Connection Failed
```bash
# Start Redis
brew services start redis       # macOS
sudo systemctl start redis      # Linux

# Test connection
redis-cli ping  # Should return PONG
```

### Dependencies Issues
```bash
# Clean reinstall
make clean
make install-dev

# Or reset virtual environment
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
make install-dev
```

### Service Won't Start
```bash
# Check logs
tail -f logs/backend.log
tail -f logs/celery.log

# Or with Docker
docker logs financial-dashboard-backend
docker logs financial-dashboard-frontend
```

## 📊 System Health Check

Run comprehensive tests:
```bash
# Test all components
python scripts/test_full_stack.py

# Test MCP server
python scripts/test_mcp_standalone.py

# Test frontend components
python scripts/test_frontend_components.py
```

## 🎉 What's Next?

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Set up Claude Integration**: See [MCP Setup Guide](MCP_SETUP.md)
3. **Add Real Data**: Configure API keys in Settings
4. **Customize Dashboard**: Modify frontend components
5. **Advanced Features**: Check [System Status](../SYSTEM_STATUS.md) for all capabilities

## 📚 More Resources

- **[Frontend Guide](FRONTEND_GUIDE.md)** - Detailed dashboard usage
- **[Task Queue Documentation](TASK_QUEUE.md)** - Background processing
- **[Authentication Guide](AUTHENTICATION.md)** - Multi-user setup
- **[Contributing Guide](../CONTRIBUTING.md)** - Development workflow

## 🆘 Getting Help

- **API Issues**: Check http://localhost:8000/docs
- **Frontend Issues**: Check Streamlit logs at http://localhost:8501
- **Task Issues**: Monitor at http://localhost:5555
- **General Issues**: See [troubleshooting docs](MCP_TROUBLESHOOTING.md)
- **Report Bugs**: https://github.com/docdyhr/financial-dashboard-mcp/issues

---

**Success Indicators:**
- ✅ Frontend loads at http://localhost:8501
- ✅ API docs accessible at http://localhost:8000/docs
- ✅ Can add assets and see portfolio data
- ✅ Background tasks running (check http://localhost:5555)
- ✅ No errors in service logs

**Total Setup Time**: ~3-5 minutes with the automated script!
