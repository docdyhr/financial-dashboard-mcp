# TODO - Technical Debt and Improvements

## ✅ Recently Completed (June 2025)

### Major Technical Debt Resolution
- [x] **SQLAlchemy 2.0 Compatibility** - Fixed EuropeanExchange enum and UniqueConstraint issues
- [x] **Frontend Import Errors** - Added proper Python path handling and absolute imports
- [x] **Configuration Issues** - Fixed invalid version numbers in pyproject.toml
- [x] **Security Hardening** - Replaced hardcoded passwords with environment variables
- [x] **Cash Account System** - Implemented complete cash tracking in portfolio calculations
- [x] **Authentication Infrastructure** - Added JWT-based auth system with proper security
- [x] **Error Handling** - Replaced silent exception handling with proper logging
- [x] **Code Modernization** - Updated to SQLAlchemy DeclarativeBase and Pydantic V2

## High Priority Remaining Tasks

### 1. Testing & Quality Assurance

- [ ] Fix pytest marker warnings (markers defined but not recognized)
- [ ] Expand test coverage for new authentication system
- [ ] Add integration tests for cash account functionality
- [ ] Validate end-to-end system startup and functionality
- **Files affected**: `pytest.ini`, `tests/`

### 2. Production Deployment

- [ ] Validate Docker production configuration
- [ ] Test production secret management scripts
- [ ] Add monitoring and health check endpoints
- [ ] Create production deployment documentation
- **Files affected**: `docker/docker-compose.prod.yml`, `scripts/setup_production_secrets.sh`

### 3. Feature Completion

- [ ] Complete MCP server integration testing
- [ ] Implement remaining ISIN sync functionality  
- [ ] Add portfolio performance benchmarking
- [ ] Complete European market data support
- **Files affected**: `mcp_server/`, `backend/services/isin_sync_service.py`
- **Files affected**: All service and API files

## Medium Priority Improvements

### 5. Performance Optimization

- [ ] Implement caching strategy for frequently accessed data
- [ ] Add database query optimization and indexing
- [ ] Implement pagination for large result sets
- **Files affected**: `backend/services/`, `database/migrations/`

### 6. Test Coverage

- [ ] Add frontend component tests (currently 0% coverage)
- [ ] Add API endpoint integration tests
- [ ] Add MCP server component tests
- [ ] Achieve 80% test coverage target
- **Target**: Increase from 27.7% to 80%

### 7. Market Data Provider

- [ ] Implement proper European market data fetching
- [ ] Add fallback providers for market data
- [ ] Implement rate limiting and caching for external APIs
- **Files affected**: `backend/services/market_data.py`

### 8. Background Tasks

- [ ] Add proper task monitoring and failure handling
- [ ] Implement task retry logic with exponential backoff
- [ ] Add task result persistence and cleanup
- **Files affected**: `backend/tasks/`

## Low Priority Technical Debt

### 9. Code Organization

- [ ] Split large service classes into smaller, focused services
- [ ] Implement proper dependency injection
- [ ] Add service layer interfaces/protocols
- **Files affected**: `backend/services/portfolio.py`, `backend/services/position.py`

### 10. Database Schema

- [ ] Add proper database constraints and indexes
- [ ] Implement soft deletes for audit trail
- [ ] Add database migration testing
- **Files affected**: `database/migrations/`

### 11. Documentation

- [ ] Add API documentation with examples
- [ ] Create deployment guide
- [ ] Add troubleshooting guide
- **Files affected**: `docs/`

### 12. Frontend Improvements

- [ ] Implement proper error handling in Streamlit components
- [ ] Add loading states and user feedback
- [ ] Optimize data fetching and caching
- **Files affected**: `frontend/`

## Architecture Improvements

### 13. Microservices Preparation

- [ ] Implement service boundaries and contracts
- [ ] Add health checks and monitoring endpoints
- [ ] Prepare for horizontal scaling
- **Files affected**: Multiple

### 14. Security Enhancements

- [ ] Implement rate limiting
- [ ] Add input validation and sanitization
- [ ] Add security headers and CORS configuration
- **Files affected**: `backend/main.py`, `backend/middleware/`

### 15. Monitoring and Observability

- [ ] Add structured logging
- [ ] Implement metrics collection
- [ ] Add distributed tracing
- **Files affected**: Multiple

## Completed Items ✅

- [x] Fixed pyproject.toml version inconsistencies
- [x] Removed unused dependencies
- [x] Added constants.py for magic numbers
- [x] Improved configuration security
- [x] Added centralized exception handling
- [x] Removed duplicate Makefile targets
- [x] Cleaned up empty files
- [x] Enhanced .gitignore
- [x] Added basic test suite for core services
- [x] Updated CHANGELOG.md
- [x] Implemented actual cash account tracking (replaced hardcoded DEFAULT_CASH_BALANCE)
- [x] Added cash deposit/withdrawal functionality
- [x] Updated portfolio calculations to use real cash balances
- [x] Created comprehensive test suite for cash account service (13 tests)
- [x] Added database migration for cash accounts table
- [x] Integrated cash accounts API endpoints into main application

## Notes

- Items marked with 🔥 are blocking production deployment
- Items marked with ⚡ have performance implications
- Items marked with 🧪 require comprehensive testing before implementation
- Estimated effort: High (1-2 weeks), Medium (2-5 days), Low (1-2 days)
