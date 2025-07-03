# Financial Dashboard MCP - Claude Code Context

This document provides essential context for Claude Code when working on the Financial Dashboard MCP project.

## Project Overview

Financial Dashboard MCP is a Python-based financial portfolio management application that integrates AI capabilities through the Model Context Protocol (MCP). It features:

- **Backend**: FastAPI REST API with PostgreSQL database
- **Frontend**: Streamlit web interface
- **AI Integration**: MCP server for intelligent financial analysis
- **Task Queue**: Celery with Redis for background processing
- **Authentication**: JWT-based with refresh tokens

## Quick Start Commands

```bash
# Setup development environment
make install-dev

# Run all services locally
make run-backend    # FastAPI on http://localhost:8000
make run-frontend   # Streamlit on http://localhost:8501

# Or use Docker
make docker-up
```

## Development Workflow

### Before Making Changes

1. **Always run tests first**: `make test-fast`
2. **Check current code quality**: `make lint`
3. **Ensure database is up to date**: `make migrate-up`

### While Coding

1. **Format code automatically**: `make format`
2. **Run type checking**: `make type-check`
3. **Run security checks**: `make security`
4. **Test specific modules**:
   - Unit tests: `make test-unit`
   - API tests: `make test-api`
   - Integration tests: `make test-integration`

### Before Committing

1. **Run full test suite**: `make test`
2. **Check coverage**: `make test-cov` (minimum 80% required)
3. **Run security scans**: `make security`
4. **Ensure all quality checks pass**: `make check-all` (includes security checks)

## Project Structure

```
backend/
├── api/          # FastAPI routes and endpoints
├── auth/         # Authentication and authorization
├── models/       # SQLAlchemy database models
├── schemas/      # Pydantic request/response schemas
├── services/     # Business logic layer
└── tasks/        # Celery background tasks

frontend/
├── components/   # Reusable UI components
├── pages/        # Streamlit page modules
└── services/     # API client and utilities

mcp_server/       # AI integration via MCP
tests/            # Comprehensive test suite
scripts/          # Utility and maintenance scripts
```

## Key Conventions

### Code Style
- **Python 3.11+** with type hints
- **Black** formatting (88 char lines)
- **Ruff** for linting with extensive rules
- **isort** for import organization
- Follow existing patterns in the codebase

### Testing
- Write tests for all new features
- Use pytest fixtures from `tests/conftest.py`
- Mark tests appropriately: `@pytest.mark.unit`, `@pytest.mark.integration`, etc.
- Test files should mirror source structure

### Database
- Use Alembic for migrations: `make migrate-create message="Add feature"`
- Always test migrations up and down
- Use SQLAlchemy models with proper relationships
- Follow existing naming conventions

### API Design
- RESTful endpoints with proper HTTP methods
- Use Pydantic schemas for validation
- Include comprehensive error handling
- Document endpoints with OpenAPI schemas

### Security
- Never commit secrets or API keys
- Use environment variables for configuration
- Validate all user inputs
- Use parameterized queries (SQLAlchemy handles this)
- Run security checks: `make security` (includes Bandit + Safety)
- Strict security mode: `make security-strict` (fails on any issues)
- Security reports saved to: `bandit-report.json` and `safety-report.json`

## Common Tasks

### Adding a New Feature
1. Create database models if needed
2. Generate and apply migrations
3. Create Pydantic schemas
4. Implement service layer logic
5. Add API endpoints
6. Create frontend components
7. Write comprehensive tests
8. Update documentation

### Debugging
- Backend logs: Check FastAPI console output
- Frontend logs: Check Streamlit console
- Database queries: Set `SQLALCHEMY_ECHO=true`
- Celery tasks: `make run-flower` for monitoring

### Performance
- Use database indexes appropriately
- Implement pagination for large datasets
- Cache expensive calculations
- Use Celery for long-running tasks
- Profile with `make test-benchmark`

## Important Notes

1. **ISIN Support**: The project uses a custom ISIN implementation for international securities. Always use the ISIN service for validation.

2. **Financial Calculations**: Use existing services in `backend/services/financial/` for calculations to ensure consistency.

3. **Market Data**: yfinance integration has rate limits. Use caching and batch requests.

4. **Authentication**: JWT tokens expire after 30 minutes. Refresh tokens last 7 days.

5. **Testing**: The project aims for 80% test coverage. New features should include tests.

## Environment Variables

Key environment variables (see `.env.example`):
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection for Celery
- `SECRET_KEY`: JWT signing key
- `ENVIRONMENT`: development/staging/production
- `LOG_LEVEL`: Logging verbosity

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure virtual environment is activated
2. **Database Errors**: Run `make db-reset` for clean slate
3. **Test Failures**: Check if database migrations are applied
4. **Type Errors**: Run `make type-check` to identify issues
5. **Docker Issues**: `make docker-down && make docker-build`

### Getting Help

- Check existing tests for usage examples
- Review API documentation at http://localhost:8000/docs
- Look for similar patterns in the codebase
- Run `make help` for all available commands

## Code Review Checklist

Before submitting changes:
- [ ] All tests pass (`make test`)
- [ ] Code is formatted (`make format`)
- [ ] No linting errors (`make lint`)
- [ ] Type checks pass (`make type-check`)
- [ ] Coverage meets minimum (`make test-cov`)
- [ ] Migrations are tested up and down
- [ ] Documentation is updated
- [ ] No security vulnerabilities introduced
- [ ] Performance impact considered
- [ ] Error handling is comprehensive
