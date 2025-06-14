# Financial Dashboard with AI Agent Integration

[![Version](https://img.shields.io/github/v/release/docdyhr/financial-dashboard-mcp?style=flat-square)](https://github.com/docdyhr/financial-dashboard-mcp/releases)
[![CI/CD](https://img.shields.io/github/actions/workflow/status/docdyhr/financial-dashboard-mcp/ci.yml?branch=main&style=flat-square&label=CI/CD)](https://github.com/docdyhr/financial-dashboard-mcp/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/docdyhr/financial-dashboard-mcp?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue?style=flat-square)](https://python.org)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)](https://github.com/psf/black)
[![Semantic Versioning](https://img.shields.io/badge/semver-2.0.0-green?style=flat-square)](https://semver.org/)
[![Conventional Commits](https://img.shields.io/badge/conventional%20commits-1.0.0-yellow?style=flat-square)](https://conventionalcommits.org)

A comprehensive financial dashboard system for monitoring and analyzing investment portfolios with AI-powered insights through MCP (Model Context Protocol) integration.

## Overview

This project provides a single-user financial dashboard to track and analyze positions in stocks, bonds, cash, and other assets. It combines a Streamlit frontend for rapid development with a FastAPI backend for scalability, and integrates AI capabilities through an MCP server for intelligent portfolio analysis and recommendations.

## Features

### Current (Production Ready) ✅

- **Portfolio Management**: Track stocks, bonds, cash, and other assets
- **Real-time Market Data**: Live market data integration via yfinance
- **Task Queue System**: Celery + Redis for background processing
- **Performance Analytics**: Portfolio performance tracking and calculations
- **Asset Allocation**: Portfolio composition analysis
- **Automated Scheduling**: Periodic market data updates and portfolio snapshots
- **CLI Management**: Command-line tools for task monitoring and management
- **API Management**: RESTful endpoints for all operations
- **Docker Deployment**: Complete containerized deployment setup
- **Comprehensive Testing**: Unit and integration tests with real data validation
- **Frontend Dashboard**: Complete Streamlit dashboard with interactive visualizations
- **AI Integration**: MCP server with 13 AI-powered tools for portfolio analysis
- **Code Quality**: Zero technical debt with complete type safety and linting compliance
- **Streamlined Dependencies**: Clean dependency management with production/dev separation

### MCP AI Tools 🤖

- **Portfolio Tools**: `get_positions`, `get_portfolio_summary`, `get_allocation`, `add_position`, `update_position`
- **Market Data Tools**: `get_asset_price`, `calculate_performance`, `analyze_portfolio_risk`, `get_market_trends`
- **Analytics Tools**: `recommend_allocation`, `analyze_opportunity`, `rebalance_portfolio`, `generate_insights`

### Planned

- Multi-user support with authentication
- Advanced portfolio analytics (VaR, advanced risk metrics)
- Market opportunity scanning with ML
- WebSocket real-time updates
- React/Next.js frontend migration

## Documentation

### Core Documentation
- **[Authentication Guide](docs/AUTHENTICATION.md)** - Comprehensive authentication and authorization implementation
- **[MCP Setup Guide](docs/MCP_SETUP.md)** - AI integration with Claude Desktop
- **[Task Queue Documentation](docs/TASK_QUEUE.md)** - Background processing setup
- **[Frontend Guide](docs/FRONTEND_GUIDE.md)** - Streamlit dashboard usage
- **[API Documentation](http://localhost:8000/docs)** - Interactive API documentation

### Technical Documentation
- **[System Status](SYSTEM_STATUS.md)** - Current project status and capabilities
- **[Contributing Guide](CONTRIBUTING.md)** - Development workflow and guidelines
- **[Changelog](CHANGELOG.md)** - Version history and changes
- **[TODO List](TODO.md)** - Project roadmap and planned features

## Architecture

``` text
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   Streamlit UI  │────▶│  FastAPI Backend│────▶│  PostgreSQL DB  │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │
                                │
                        ┌───────▼────────┐
                        │                │
                        │  Celery + Redis│
                        │   Task Queue   │
                        │                │
                        └────────────────┘
                                │
                        ┌───────▼────────┐     ┌─────────────────┐
                        │                │     │                 │
                        │   MCP Server   │────▶│  Claude Desktop │
                        │  (AI Assistant)│     │                 │
                        │                │     │                 │
                        └────────────────┘     └─────────────────┘
```

## Tech Stack

- **Frontend**: Streamlit (Python)
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Cache/Queue**: Redis + Celery
- **AI Integration**: MCP Server (Anthropic)
- **Market Data**: yfinance, AlphaVantage (optional)
- **Deployment**: Docker Compose
- **Language**: Python 3.11+

## Getting Started

### Prerequisites

- Python 3.11.13
- PostgreSQL
- Redis
- Docker and Docker Compose (for containerized deployment)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/docdyhr/financial-dashboard-mcp.git
cd financial-dashboard-mcp
```

1. Create and activate virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
# Production dependencies only (20+ essential packages)
pip install -r requirements.txt

# OR for development (includes testing, linting, etc.)
pip install -r requirements-dev.txt

# OR using pyproject.toml (recommended)
pip install -e .                    # Production
pip install -e ".[dev]"            # Development with all tools
```

4. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration

## Important: MCP Server Authentication

The MCP server requires a token for all API access. Set `MCP_AUTH_TOKEN` in your `.env` file:

```

MCP_AUTH_TOKEN=your-mcp-auth-token-here

```

- Use a strong, unique value in production.
- The same value must be used by clients (e.g., test scripts, frontend) in the `Authorization` header as `Bearer <token>`
```

5. Initialize the database:

```bash
alembic upgrade head
```

6. Start the services:

**Using Docker (Recommended):**

```bash
# Start all services (backend, worker, beat, flower, redis, postgres)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**For Local Development:**

```bash
# Terminal 1: Start FastAPI backend
uvicorn backend.main:app --reload

# Terminal 2: Start Celery worker
celery -A backend.tasks worker --loglevel=info

# Terminal 3: Start Celery beat (scheduler)
celery -A backend.tasks beat --loglevel=info

# Terminal 4: Start Streamlit frontend (when ready)
streamlit run frontend/app.py

# Terminal 5: Start MCP server (when ready)
python mcp_server/server.py
```

**Using the CLI Tool:**

```bash
# Submit tasks
python -m backend.tasks.cli submit market-data fetch --symbols AAPL,GOOGL,MSFT
python -m backend.tasks.cli submit portfolio analytics --user-id 1

# Monitor tasks
python -m backend.tasks.cli status <task-id>
python -m backend.tasks.cli list active
python -m backend.tasks.cli monitor

# Check worker stats
python -m backend.tasks.cli workers
```

## Project Structure

``` text
financial-dashboard-mcp/
├── frontend/               # Streamlit application
│   ├── app.py             # Main Streamlit app
│   ├── pages/             # Multi-page app structure
│   └── components/        # Reusable UI components
├── backend/               # FastAPI application
│   ├── main.py           # FastAPI app entry point
│   ├── api/              # API endpoints
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   └── tasks/            # Celery tasks
├── mcp_server/           # MCP server for AI integration
│   ├── server.py         # MCP server implementation
│   └── tools/            # MCP tool definitions
├── database/             # Database related files
│   ├── migrations/       # Alembic migrations
│   └── init.sql         # Initial schema
├── tests/                # Test suite
├── docker/               # Docker configurations
├── docs/                 # Documentation
│   ├── PRD.md           # Product Requirements Document
│   └── architecture.md   # Architecture details
├── .env.example          # Environment variables template
├── docker-compose.yml    # Docker compose configuration
├── requirements.txt      # Core production dependencies (20+ essential)
├── requirements-dev.txt  # Development dependencies (testing, linting, etc.)
├── pyproject.toml        # Python project configuration (single source of truth)
├── TODO.md              # Project roadmap and tasks
└── README.md            # This file
```

## Task Queue System

The system includes a robust task queue built on Celery + Redis for handling:

### Available Tasks

- **Market Data**: Fetch real-time prices, asset information, bulk data updates
- **Portfolio Analytics**: Calculate performance metrics, generate snapshots
- **Scheduled Jobs**: Hourly price updates, daily snapshots, weekly maintenance

### Monitoring Tools

- **Flower UI**: `http://localhost:5555` - Web-based task monitoring
- **CLI Tool**: Command-line task management and monitoring
- **API Endpoints**: RESTful task management via `/api/tasks/*`

### Key Features

- **Asynchronous Processing**: Non-blocking task execution
- **Error Handling**: Comprehensive error recovery and retry logic
- **Real-time Monitoring**: Live task status and worker health tracking
- **Scalability**: Horizontal worker scaling for high-volume processing

## MCP Integration with Claude Desktop

The project includes a comprehensive MCP (Model Context Protocol) server that enables AI-powered portfolio analysis through Claude Desktop.

### Setup

1. **Test the MCP server:**

   ```bash
   python scripts/test_mcp_server.py
   ```

2. **Configure Claude Desktop:**

   Add the following to your Claude Desktop configuration file:
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\\Claude\\claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "financial-dashboard": {
         "command": "python",
         "args": [
           "/full/path/to/financial-dashboard-mcp/scripts/start_mcp_server.py"
         ],
         "env": {
           "BACKEND_URL": "http://localhost:8000"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop** to load the MCP server.

### Available MCP Tools

#### Portfolio Management

- `get_positions` - Retrieve current portfolio positions with real-time data
- `get_portfolio_summary` - Get comprehensive portfolio overview and key metrics
- `get_allocation` - Get current portfolio allocation breakdown by asset type
- `add_position` - Add a new position to the portfolio
- `update_position` - Update an existing portfolio position

#### Market Data & Analytics

- `get_asset_price` - Get current price and basic info for an asset
- `calculate_performance` - Calculate portfolio performance for specific time periods
- `analyze_portfolio_risk` - Analyze portfolio risk metrics and volatility
- `get_market_trends` - Get current market trends and sector performance

#### AI-Powered Insights

- `recommend_allocation` - Get AI-powered portfolio allocation recommendations
- `analyze_opportunity` - Find investment opportunities based on criteria
- `rebalance_portfolio` - Generate portfolio rebalancing recommendations
- `generate_insights` - Generate AI-powered portfolio insights and recommendations

### Example Usage with Claude

Once configured, you can ask Claude natural language questions like:

- "Show me my current portfolio positions"
- "What's my portfolio performance this year?"
- "Recommend an allocation for moderate risk tolerance with a long-term horizon"
- "Analyze opportunities in growth stocks"
- "Should I rebalance my portfolio?"
- "Give me insights on my portfolio risk and diversification"
- "What's the current price of AAPL?"
- "Add 100 shares of MSFT at $380 per share"

For detailed setup instructions, see [docs/MCP_SETUP.md](docs/MCP_SETUP.md).

## API Documentation

Once the backend is running, API documentation is available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Task Monitor: `http://localhost:5555` (Flower)

## MCP Tools Available

The AI assistant can access these tools:

- `get_positions()` - Retrieve current portfolio positions
- `get_portfolio_summary()` - Get portfolio overview and metrics
- `get_asset_price(ticker)` - Fetch current asset prices
- `calculate_performance(period)` - Calculate returns for specified period
- `recommend_allocation()` - Get AI-powered allocation suggestions
- `analyze_opportunity(criteria)` - Find investment opportunities

## Task Queue (Celery + Redis)

The system includes a robust task queue for asynchronous operations:

- **Market Data Tasks**: Fetch real-time and historical market data
- **Portfolio Analytics**: Calculate performance metrics and generate reports
- **Scheduled Jobs**: Automatic price updates and portfolio snapshots
- **Background Processing**: Handle time-intensive operations without blocking the UI

Quick start:

```bash
# Start all task queue components
./scripts/start_task_queue.sh

# Or manually:
celery -A backend.tasks worker --loglevel=info
celery -A backend.tasks beat --loglevel=info
celery -A backend.tasks flower  # Monitoring dashboard
```

See [Task Queue Documentation](docs/TASK_QUEUE.md) for detailed setup and usage.

## Development

### Running Tests

```bash copy
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov=frontend

# Run specific test file
pytest tests/test_api.py
```

### Code Quality

```bash copy
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

### Database Migrations

```bash copy
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## Security

- All API endpoints require authentication (in production)
- MCP server access is token-based
- Sensitive data is encrypted at rest
- No API keys or secrets should be committed to the repository

## Project Status

🟢 **Production Ready**: Backend API, Task Queue System, Database Layer, Frontend Dashboard, MCP Server
🟡 **In Development**: Claude Desktop Integration Testing
🔴 **Planned**: Multi-user Support, Advanced Analytics, WebSocket Updates

The system is feature-complete with a production-ready backend infrastructure, comprehensive task queue system, interactive Streamlit dashboard, and fully functional MCP server for AI integration. All components have been tested and documented.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/) and [FastAPI](https://fastapi.tiangolo.com/)
- Task queue powered by [Celery](https://docs.celeryq.dev/) and [Redis](https://redis.io/)
- AI integration powered by [Anthropic's MCP](https://github.com/anthropics/mcp)
- Market data provided by [yfinance](https://github.com/ranaroussi/yfinance)

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.

## Roadmap

See [TODO.md](TODO.md) for the detailed project roadmap and upcoming features.

## 🔢 Versioning

This project follows [Semantic Versioning](https://semver.org/) with automated releases:

- 🏷️ **Automatic versioning** based on [Conventional Commits](https://conventionalcommits.org)
- 📝 **Automated changelog** generation
- 🚀 **GitHub releases** with Docker images
- ✅ **Version consistency** across all project files

### Commit Message Format

```text
<type>[optional scope]: <description>

Examples:
feat(api): add portfolio export functionality     → Minor release
fix(frontend): resolve chart rendering issue      → Patch release
feat!: redesign authentication system            → Major release
```

For detailed versioning guidelines, see [docs/SEMANTIC_VERSIONING.md](docs/SEMANTIC_VERSIONING.md).

---

**Note**: This project uses automated semantic versioning. Manual version bumps are not required.
