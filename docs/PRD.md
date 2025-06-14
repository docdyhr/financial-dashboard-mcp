# Product Requirements Document (PRD)

## Project Title: Hybrid Financial Dashboard with AI Agent Integration

---

## Overview

This project aims to build a **single-user financial dashboard** to monitor and explore positions in **stocks, bonds, cash, and other assets**, with a focus on long-term scalability and AI integration via MCP (Model Context Protocol). The system will follow a **Hybrid architecture**, combining a **Streamlit front-end** for rapid development and **FastAPI + PostgreSQL backend** for robustness and scalability.

---

## Goals

- Display and update real-time portfolio performance
- Allow opportunity exploration (based on macro/micro data)
- Be compatible with AI agents via an MCP server
- Ensure modular, testable, and secure architecture
- Enable future transition to multi-user setup

---

## Architecture Overview

**Frontend:** Streamlit (Python)
**Backend:** FastAPI (Python)
**Database:** PostgreSQL
**Async Tasks:** Celery + Redis
**AI Integration:** MCP Server (Python SDK)
**Deployment:** Docker Compose (Streamlit, FastAPI, Redis, Celery, Postgres)

---

## Key Features

### MVP

- User-friendly dashboard (Streamlit) with:
  - Portfolio overview
  - Performance charts
  - Asset allocation
  - Filtering & what-if sliders
- FastAPI backend exposing:
  - Portfolio data endpoints
  - Performance calculation APIs
- PostgreSQL for persistent state
- Celery background tasks for:
  - Market data fetching
  - Scheduled portfolio analytics
- AI Assistant Integration:
  - MCP server connected to Postgres or FastAPI
  - Tools like `get_portfolio_summary`, `rebalance_portfolio`

### Future (Post-MVP)

- Replace Streamlit with React or Next.js frontend
- Add multi-user authentication (OAuth2/JWT)
- Advanced AI suggestions (e.g., opportunity scans)
- Real-time updates via WebSockets
- Admin panel and audit logs

---

## AI Agent Integration via MCP

- Use Anthropic’s open-source MCP server
- Tools available:
  - `get_positions()`
  - `get_asset_price(ticker)`
  - `recommend_allocation()`
- Security via token-based access
- Local MCP server or embedded in FastAPI

---

## Development Phases

### Phase 1: Core System Setup

- Scaffold FastAPI + Postgres backend
- Define DB schema (users, positions, transactions)
- Set up Celery + Redis
- Build Streamlit UI for dashboard
- Integrate yfinance/AlphaVantage for market data

### Phase 2: AI Integration

- Install MCP Python SDK
- Connect MCP to FastAPI or Postgres
- Register base tools
- Add MCP test scripts for Claude Desktop

### Phase 3: UI Improvements & Analytics

- Enhance dashboard interactivity (filters, plots)
- Add portfolio metrics (sharpe, allocation drift)
- Implement job tracking (task status from Celery)
- Cache heavy results (Redis or Streamlit cache)

### Phase 4: Prep for Scaling

- Add auth token to FastAPI endpoints
- Modularize logic (services, utils)
- Prepare CI/CD and docker-compose.yml
- Optional: draft OpenAPI spec for external API

---

## Technical Stack

- Python 3.11+
- FastAPI
- PostgreSQL
- SQLAlchemy / Pydantic
- Streamlit
- Celery + Redis
- Docker + Docker Compose
- MCP Server (Anthropic or custom)
- Pytest for testing

---

## Milestones

| Milestone | Description | ETA |
|----------|-------------|-----|
| Backend Setup | FastAPI, DB, task queue | Week 1 |
| Streamlit MVP | Basic dashboard UI | Week 2 |
| AI Agent Ready | MCP tools operational | Week 3 |
| Feature Complete | Caching, metrics, UI polish | Week 4 |
| Deployment Ready | Containerized + docs | Week 5 |

---

## Risks & Mitigations

- **Complexity**: Isolated services/components for easy testing
- **Performance**: Use Celery + Redis for async processing
- **AI Safety**: Expose limited MCP tools only
- **Future Multi-user**: Schema designed with `user_id` for scaling

---

## License

MIT License, open to community contributions via GitHub

---

## Authors

Initial implementation by [Your Name or GitHub handle]
