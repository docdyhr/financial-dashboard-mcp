# Automated Testing Setup for Financial Dashboard MCP Project

You are a senior DevOps engineer who specializes in automated testing and code quality. I need to set up comprehensive automated testing for a **Financial Dashboard with AI Agent Integration** project to validate all AI-generated code before it goes to production.

## Project Context

- **Language**: Python 3.11+
- **Framework**: FastAPI (backend), Streamlit (frontend), Celery + Redis (task queue), MCP server (AI integration)
- **Database**: PostgreSQL
- **Current testing**: Basic unit and integration tests exist
- **Team size**: Small development team (1-3 developers)
- **Deployment**: Docker Compose with multi-service architecture
- **AI Integration**: MCP server with 13 AI-powered portfolio analysis tools
- **External Dependencies**: yfinance for market data, Redis for caching, PostgreSQL for persistence

### Project Architecture

```text
Streamlit UI → FastAPI Backend → PostgreSQL DB
     ↓
Celery + Redis Task Queue
     ↓
MCP Server (AI Assistant) → Claude Desktop
```

Please create a complete automated testing pipeline that includes:

## 1. **Unit Testing Setup**

- **pytest** configuration with fixtures for FastAPI, database, Redis, and MCP server
- Test templates for:
  - FastAPI endpoints and business logic
  - Celery task execution and scheduling
  - MCP server tools and AI integration points
  - Portfolio calculation algorithms and financial models
  - Market data parsing and validation
- Mock/stub utilities for:
  - External market data APIs (yfinance, AlphaVantage)
  - Redis cache operations
  - PostgreSQL database transactions
  - MCP server communication
  - Time-sensitive portfolio calculations
- Coverage reporting with **pytest-cov** (aim for 85%+ coverage)
- Specific test cases for financial calculation accuracy and edge cases

## 2. **Integration Testing**

- **FastAPI TestClient** for full API endpoint testing
- Database integration tests with test database isolation
- **Celery** task integration with Redis backend testing
- **MCP server** integration tests for all 13 AI tools:
  - Portfolio management tools (get_positions, add_position, update_position)
  - Market data tools (get_asset_price, calculate_performance, analyze_portfolio_risk)
  - Analytics tools (recommend_allocation, analyze_opportunity, rebalance_portfolio)
- **Docker Compose** test environment setup
- End-to-end scenarios covering:
  - Portfolio creation → market data fetch → performance calculation → AI analysis
  - Real-time data updates through the entire pipeline
  - Task queue processing for background operations

## 3. **Static Analysis Tools**

- **Black** for code formatting with strict line length (88 chars)
- **flake8** with financial domain-specific rules and complexity limits
- **mypy** for strict type checking across all modules
- **bandit** for security vulnerability scanning (critical for financial data)
- **isort** for import organization
- **pylint** with custom rules for financial calculation validation
- **Safety** for dependency vulnerability checking
- **pre-commit** hooks integrating all static analysis tools

## 4. **CI/CD Pipeline**

- **GitHub Actions** workflow with matrix testing for Python versions
- **Pre-commit hooks** blocking commits with failing lints/tests
- **Docker-based testing** pipeline matching production environment
- **Automated testing** on PR creation with detailed reporting
- **Quality gates** that block merging if:
  - Test coverage drops below 85%
  - Any security vulnerabilities detected
  - Static analysis failures
  - Integration tests fail
  - Performance benchmarks regress
- **Multi-stage pipeline**:
  - Stage 1: Linting and security scanning
  - Stage 2: Unit tests with coverage
  - Stage 3: Integration tests with full Docker stack
  - Stage 4: Performance and load testing
  - Stage 5: MCP server AI integration validation

## 5. **Code Quality Monitoring**

- **Performance regression detection** for portfolio calculations and API responses
- **Technical debt tracking** with SonarQube integration
- **Security dependency monitoring** with automated PR creation for updates
- **Financial calculation accuracy monitoring** with benchmark datasets
- **API performance monitoring** with response time thresholds
- **Memory usage monitoring** for large portfolio processing
- **MCP server response time tracking** for AI tool performance

## 6. **Specialized Financial Testing Requirements**

Include specific test cases for common AI coding mistakes in financial applications:

### **Financial Calculation Edge Cases:**

- Zero and negative portfolio values
- Currency precision and rounding errors
- Market data gaps and missing values
- Extreme market volatility scenarios
- Portfolio rebalancing edge cases
- Performance calculation with dividends and splits

### **Security and Data Validation:**

- SQL injection protection for user inputs
- Market data validation and sanitization
- Portfolio position validation (no negative holdings)
- Authentication token validation for MCP server
- Rate limiting for external API calls
- Encryption of sensitive financial data

### **AI Integration Reliability:**

- MCP server connection failure handling
- AI recommendation validation and bounds checking
- Fallback mechanisms when AI services are unavailable
- Timeout handling for long-running AI analysis
- Data consistency between AI recommendations and actual portfolio state

### **Market Data Integrity:**

- Real-time vs delayed data validation
- Market hours and trading day validation
- Currency conversion accuracy
- Asset price validation against reasonable bounds
- Historical data consistency checks

For each tool, provide:

- **Installation commands** with exact versions
- **Configuration files** with financial-specific settings
- **Example usage** with portfolio and market data scenarios
- **Integration steps** with existing Docker Compose workflow
- **Monitoring and alerting** setup for production environment

Make this bulletproof for catching issues in AI-generated financial code, with emphasis on data accuracy, security, and regulatory compliance considerations.
