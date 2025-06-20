# Financial Dashboard Documentation

Welcome to the comprehensive documentation for the Financial Dashboard project - a hybrid financial portfolio management system with AI-powered insights through MCP (Model Context Protocol) integration.

## 📚 Documentation Structure

### 📖 Core Documentation
- [**README.md**](../README.md) - Main project overview and features
- [**CLAUDE.md**](CLAUDE.md) - Development guidance for Claude Code AI assistant
- [**CONTRIBUTING.md**](CONTRIBUTING.md) - Contribution guidelines and development process
- [**SECURITY.md**](SECURITY.md) - Security guidelines and audit checklist
- [**CHANGELOG.md**](CHANGELOG.md) - Version history and release notes
- [**TODO.md**](TODO.md) - Project roadmap and pending tasks

### 🚀 Quick Start Guides
- [**Quick Start Guide**](guides/QUICK_START.md) - Get up and running quickly
- [**Frontend Guide**](guides/FRONTEND_GUIDE.md) - Streamlit frontend setup and usage

### 🤖 MCP (AI Integration)
- [**MCP Server Guide**](mcp/MCP_SERVER.md) - Complete MCP server documentation
- [**MCP Setup**](mcp/MCP_SETUP.md) - Basic MCP configuration
- [**MCP Fix Summary**](mcp/MCP_SERVER_FIX_SUMMARY.md) - Recent fixes and improvements

### 🛠️ Technical Documentation
- [**Authentication System**](technical/AUTHENTICATION.md) - Auth system design and implementation
- [**Backend Authentication**](technical/BACKEND_AUTH.md) - Backend auth module documentation
- [**Task Queue System**](technical/TASK_QUEUE.md) - Celery task queue configuration
- [**Semantic Versioning**](technical/SEMANTIC_VERSIONING.md) - Versioning guidelines
- [**European Tickers**](technical/EUROPEAN_TICKERS.md) - European market support
- [**Position Management**](technical/POSITION_MANAGEMENT.md) - Portfolio position handling
- [**ISIN Support Plan**](technical/isin_support_plan.md) - International securities identifier support

### 🚢 Deployment & Operations
- [**Production Deployment**](deployment/PRODUCTION_DEPLOYMENT.md) - Production deployment guide
- [**Service Management**](deployment/SERVICE_MANAGEMENT.md) - Managing backend services

### 🔧 Setup & Configuration
- [**Claude Desktop Setup**](setup/CLAUDE_DESKTOP_SETUP.md) - Configure Claude Desktop with MCP server

### 🐛 Troubleshooting
- [**MCP Troubleshooting**](troubleshooting/MCP_TROUBLESHOOTING.md) - Common MCP issues and solutions
- [**Claude Config Fix**](troubleshooting/CLAUDE_CONFIG_FIX.md) - Claude Desktop configuration fixes

### 📊 Status Reports
- [**System Status**](status/SYSTEM_STATUS.md) - Current system status and health
- [**Production Test Report**](status/PRODUCTION_TEST_REPORT.md) - Production readiness validation
- [**Technical Debt Audit**](status/technical_debt_audit.md) - Technical debt assessment

### 🔨 Development Fixes
- [**Authentication Fixed**](fixes/AUTHENTICATION_FIXED.md) - Authentication system fixes
- [**Cash Issue Resolved**](fixes/CASH_ISSUE_RESOLVED.md) - Cash account system fixes
- [**MCP Authentication Fixed**](fixes/MCP_AUTHENTICATION_FIXED.md) - MCP server auth fixes
- [**MCP Fully Fixed**](fixes/MCP_FULLY_FIXED.md) - Complete MCP system fixes
- [**Portfolio Issues Resolved**](fixes/PORTFOLIO_ISSUES_RESOLVED.md) - Portfolio management fixes
- [**Linting Fixes Summary**](fixes/linting_fixes_summary.md) - Code quality improvements

### 📄 PRD & Architecture
- [**Product Requirements Document**](PRD.md) - Complete product specification and architecture

## 🏗️ Project Architecture

The Financial Dashboard follows a hybrid architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   Claude        │    │   FastAPI       │
│   Frontend      │◄──►│   Desktop       │◄──►│   Backend       │
│   (Port 8501)   │    │   + MCP Server  │    │   (Port 8000)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────────────────┐
                    │     Infrastructure          │
                    │  • PostgreSQL Database      │
                    │  • Redis (Caching)         │
                    │  • Celery (Task Queue)     │
                    │  • Market Data Providers   │
                    └─────────────────────────────┘
```

## 🎯 Development Phases

### ✅ Phase 1: MVP (Completed)
- Basic Streamlit dashboard
- PostgreSQL database setup
- Manual data entry
- Simple visualizations

### ✅ Phase 2: Enhanced Features (Completed)
- FastAPI backend integration
- Celery task queue system
- Redis caching
- Advanced charting capabilities
- Historical data tracking

### ✅ Phase 3: AI Integration (Completed)
- MCP server implementation
- AI-powered portfolio insights
- Natural language queries
- Automated recommendations

## 🚀 Getting Started

1. **Choose your path:**
   - 🏃‍♂️ **Quick Setup**: Follow the [Quick Start Guide](guides/QUICK_START.md)
   - 🤖 **AI Features**: Set up [MCP Server](mcp/MCP_SERVER.md) for Claude integration
   - 🏭 **Production**: Use the [Production Deployment Guide](deployment/PRODUCTION_DEPLOYMENT.md)

2. **Key entry points:**
   - **Developers**: Start with [CONTRIBUTING.md](CONTRIBUTING.md)
   - **Operations**: Check [Service Management](deployment/SERVICE_MANAGEMENT.md)
   - **Security**: Review [SECURITY.md](SECURITY.md)

## 🔍 Finding Information

### By Topic
- **Authentication**: [Authentication System](technical/AUTHENTICATION.md)
- **MCP Setup**: [MCP Server Guide](mcp/MCP_SERVER.md)
- **Deployment**: [Production Deployment](deployment/PRODUCTION_DEPLOYMENT.md)
- **Troubleshooting**: [Troubleshooting Section](#-troubleshooting)

### By Role
- **End Users**: [Quick Start](guides/QUICK_START.md) → [Frontend Guide](guides/FRONTEND_GUIDE.md)
- **Developers**: [CONTRIBUTING.md](CONTRIBUTING.md) → [Technical Docs](#-technical-documentation)
- **DevOps**: [Deployment](#-deployment--operations) → [Service Management](deployment/SERVICE_MANAGEMENT.md)
- **AI Enthusiasts**: [MCP Documentation](#-mcp-ai-integration)

## 📈 Current Status

- ✅ **Core Features**: Complete and production-ready
- ✅ **Security**: Comprehensive audit completed
- ✅ **MCP Integration**: 13 AI-powered tools available
- ✅ **Testing**: Extensive test coverage
- 🔄 **Real Market Data**: Integration in progress
- 📋 **Production**: Ready for deployment

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines, development setup, and coding standards.

## 🔒 Security

This project takes security seriously. See [SECURITY.md](SECURITY.md) for security guidelines and audit procedures.

## 📞 Support

- **Issues**: Create an issue in the GitHub repository
- **Documentation**: Check this documentation index
- **Security**: Follow responsible disclosure in [SECURITY.md](SECURITY.md)
