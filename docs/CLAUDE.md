# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Hybrid Financial Dashboard project designed as a single-user system for monitoring and exploring financial positions (stocks, bonds, cash, and other assets). The project combines Streamlit for rapid UI development with a FastAPI backend for scalability and advanced features.

## Technology Stack

- **Python**: 3.11.13 (specified in `.python-version`)
- **Frontend**: Streamlit
- **Backend**: FastAPI
- **Database**: PostgreSQL
- **Task Queue**: Celery + Redis
- **AI Integration**: MCP Server (Model Context Protocol)
- **Containerization**: Docker + Docker Compose

## Architecture

The project follows a hybrid architecture approach:

1. **Streamlit UI Layer**: For rapid prototyping and interactive dashboards
2. **FastAPI Backend**: For data processing, API endpoints, and complex business logic
3. **PostgreSQL Database**: For persistent storage of financial data
4. **Celery + Redis**: For asynchronous task processing (data updates, calculations)
5. **MCP Server**: For AI-powered financial analysis and recommendations

## Development Phases

According to the PRD, the project follows these phases:

### Phase 1: MVP

- Basic Streamlit dashboard with portfolio overview
- PostgreSQL database setup
- Basic data ingestion for manual entries
- Simple visualizations

### Phase 2: Enhanced Features

- FastAPI backend integration
- Celery for async tasks
- Redis caching
- Advanced charting
- Historical tracking

### Phase 3: AI Integration

- MCP server implementation
- AI-powered insights
- Natural language queries
- Automated recommendations

## Project Structure (Planned)

```text
financial-dashboard-mcp/
├── frontend/               # Streamlit application
├── backend/               # FastAPI application
├── mcp_server/           # MCP server for AI integration
├── database/             # Database schemas and migrations
├── tasks/                # Celery tasks
├── tests/                # Test suite
├── docker/               # Docker configurations
└── docs/                 # Documentation
```

## Key Features to Implement

1. **Portfolio Management**: Track stocks, bonds, cash, and other assets
2. **Real-time Updates**: Live price updates for securities
3. **Historical Analysis**: Performance tracking over time
4. **AI Integration**: Natural language queries and intelligent recommendations
5. **Data Visualization**: Interactive charts and dashboards

## Development Commands

The project includes a Makefile for common development tasks:

```bash
# Environment setup
source .venv/bin/activate  # Already configured in .envrc

# Install dependencies
make install          # Install production dependencies
make install-dev      # Install dev dependencies + pre-commit hooks

# Code quality
make format          # Format code with black, isort, ruff
make lint            # Run linting checks
make type-check      # Run mypy type checking

# Testing
make test            # Run tests
make test-cov        # Run tests with coverage report

# Running services locally
make run-backend     # Run FastAPI backend (port 8000)
make run-frontend    # Run Streamlit frontend (port 8501)
make run-celery      # Run Celery worker
make run-celery-beat # Run Celery scheduler
make run-flower      # Run Celery monitoring UI (port 5555)

# Docker commands
make docker-build    # Build all Docker images
make docker-up       # Start all services with Docker
make docker-down     # Stop all Docker services

# Database migrations
make migrate-create message="your message"  # Create new migration
make migrate-up      # Apply migrations
make migrate-down    # Rollback last migration
```

## Quick Start

1. **Install dependencies:**

   ```bash
   make install-dev
   ```

2. **Set up environment:**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   # Generate secure keys for production:
   python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(64))"
   python -c "import secrets; print('MCP_AUTH_TOKEN=' + secrets.token_urlsafe(32))"
   openssl rand -base64 32  # For database and Flower passwords
   ```

3. **Run locally:**

   ```bash
   # Terminal 1: Backend
   make run-backend

   # Terminal 2: Frontend
   make run-frontend
   ```

4. **Run with Docker:**

   ```bash
   make docker-up
   ```

The application will be available at:

- Frontend: <http://localhost:8501>
- Backend API: <http://localhost:8000>
- API Docs: <http://localhost:8000/docs>
- Celery Flower: <http://localhost:5555> (when running)

## Configuration & Environment Variables

The project uses a comprehensive `.env` configuration file for all settings. Key configurations include:

### Core Settings
- **Database**: PostgreSQL connection with Docker configuration
- **Security**: JWT tokens, MCP authentication, session management
- **Services**: Redis/Celery for background tasks, API/Frontend ports

### Market Data Providers
- **Alpha Vantage**: Real-time stock data (free API key required)
- **Finnhub**: Market data and company fundamentals (free API key required)
- **Yahoo Finance**: Historical data and basic quotes (no API key needed)

### Demo Credentials
- **Username**: `user@example.com`
- **Password**: `demo123456`

### Environment Setup
1. Copy `.env.example` to `.env`
2. Generate secure keys for production
3. Configure market data API keys (optional for development)
4. Customize rate limits and cache settings as needed

## Important Notes

- **Production Ready**: 94.2% test pass rate, comprehensive technical debt resolution completed
- **Single-user System**: Designed for individual portfolio management
- **Data Privacy**: Focus on local storage and secure authentication
- **AI Integration**: Uses MCP (Model Context Protocol) for secure, context-aware assistance
- **Hybrid Architecture**: Rapid UI development with scalable backend
- **Modular Design**: 2,362 lines of monolithic code refactored into 10 focused modules
