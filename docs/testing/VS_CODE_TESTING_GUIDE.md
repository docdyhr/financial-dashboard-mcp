# VS Code Testing Setup - Financial Dashboard MCP

## Overview

This document describes the VS Code testing setup for the Financial Dashboard MCP project. The testing framework is built around pytest with async support and comprehensive VS Code integration.

## Test Structure

```test
tests/
├── __init__.py
├── conftest.py                    # Pytest configuration and fixtures
├── test_vscode_integration.py     # VS Code integration validation tests
├── api/                          # API endpoint tests
├── auth/                         # Authentication tests
├── integration/                  # Integration tests
├── performance/                  # Performance tests
├── unit/                         # Unit tests
└── ...
```

## Configuration Files

### pytest.ini

- Configures pytest markers, asyncio mode, and test discovery
- Sets up strict mode for async tests
- Configures warning filters and environment variables

### .vscode/settings.json

- Enables pytest as the test framework
- Configures test discovery and execution
- Sets up proper Python environment paths
- Enables test gutters and debugging

### .vscode/launch.json

- Provides debug configurations for tests
- Includes configurations for:
  - Debug Current Test File
  - Debug Specific Test Function
  - Debug All Tests
  - Debug Fast Tests Only

### .vscode/tasks.json

- Provides VS Code tasks for running tests
- Includes tasks for:
  - Run All Tests
  - Run Current File
  - Run Fast Tests
  - Run with Coverage
  - Run Failed Tests Only
  - Test Discovery

## Test Markers

The project uses pytest markers to categorize tests:

- `@pytest.mark.unit` - Unit tests that test individual components
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.auth` - Authentication tests
- `@pytest.mark.fast` - Quick tests (< 1 second)
- `@pytest.mark.slow` - Longer-running tests
- `@pytest.mark.asyncio` - Async tests (required for all async test functions)
- `@pytest.mark.database` - Tests requiring database access
- `@pytest.mark.external` - Tests making external API calls

## Async Testing

All async test functions must be decorated with `@pytest.mark.asyncio`:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_operation()
    assert result is not None
```

## Running Tests

### VS Code Test Explorer

1. Open the Test Explorer in the Side Bar (beaker icon)
2. Tests are automatically discovered and displayed
3. Click the play button next to individual tests or test suites
4. View results inline with code

### VS Code Tasks

- `Ctrl+Shift+P` → `Tasks: Run Task`
- Select from available test tasks:
  - "pytest: Run All Tests"
  - "pytest: Run Current File"
  - "pytest: Run Fast Tests"
  - "pytest: Run with Coverage"
  - etc.

### Debug Tests

1. Set breakpoints in test files
2. Use debug configurations from launch.json:
   - "Debug Current Test File"
   - "Debug Specific Test Function"
3. Or use the debug button in Test Explorer

### Command Line

```bash
# Run all tests
.venv/bin/pytest tests/ -v

# Run specific test file
.venv/bin/pytest tests/test_auth.py -v

# Run with coverage
.venv/bin/pytest tests/ --cov=backend --cov=frontend --cov-report=html

# Run only fast tests
.venv/bin/pytest tests/ -m fast

# Run tests matching pattern
.venv/bin/pytest tests/ -k "test_auth" -v
```

## Test Development Guidelines

### Writing New Tests

1. Place tests in appropriate subdirectory
2. Use descriptive test names starting with `test_`
3. Add appropriate markers
4. For async tests, always add `@pytest.mark.asyncio`
5. Use fixtures for common setup
6. Keep tests isolated and independent

### Example Test Structure

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.unit
@pytest.mark.auth
class TestAuthentication:
    """Test authentication functionality."""

    @pytest.fixture
    def mock_user(self):
        """Mock user for testing."""
        return Mock(id=1, email="test@example.com")

    def test_valid_credentials(self, mock_user):
        """Test authentication with valid credentials."""
        # Test implementation
        assert True

    @pytest.mark.asyncio
    async def test_async_auth(self, mock_user):
        """Test async authentication."""
        result = await authenticate_user(mock_user)
        assert result is not None
```

## Test Coverage

Coverage reports are generated in:

- `htmlcov/` - HTML coverage report (open `htmlcov/index.html`)
- `coverage.xml` - XML format for CI/CD
- Terminal output with `--cov-report=term-missing`

## Troubleshooting

### Common Issues

1. **Async tests failing**
   - Ensure `@pytest.mark.asyncio` decorator is present
   - Check `asyncio_mode = strict` in pytest.ini

2. **Tests not discovered**
   - Check file naming (must start with `test_` or end with `_test.py`)
   - Verify `PYTHONPATH` is set correctly
   - Check `.vscode/settings.json` configuration

3. **Import errors**
   - Ensure virtual environment is activated
   - Check `PYTHONPATH` includes project root
   - Verify all dependencies are installed

4. **Test execution timeout**
   - Use `@pytest.mark.timeout` for long-running tests
   - Consider breaking down complex tests
   - Check for infinite loops or blocking operations

### Performance Tips

1. Use `@pytest.mark.fast` for quick tests
2. Run fast tests during development: `.venv/bin/pytest -m fast`
3. Use parallel execution: `.venv/bin/pytest -n auto`
4. Skip slow tests during development: `.venv/bin/pytest -m "not slow"`

### Environment Variables

Set in `.env` file or environment:

- `ENVIRONMENT=test` - Test environment
- `DATABASE_URL` - Test database URL
- `REDIS_URL` - Test Redis URL

## Integration with CI/CD

The testing setup is designed to work with continuous integration:

```bash
# CI command example
pytest tests/ --cov=backend --cov=frontend --cov-report=xml --junitxml=test-results.xml
```

## VS Code Extensions Recommended

- Python (Microsoft)
- Python Test Explorer
- Test Adapter Converter
- Coverage Gutters

## Summary

The VS Code testing setup provides:

- ✅ Automatic test discovery
- ✅ Integrated test runner
- ✅ Debug support for tests
- ✅ Coverage reporting
- ✅ Async test support
- ✅ Multiple test execution options
- ✅ Rich problem matching and error reporting

This setup enables efficient test-driven development with immediate feedback and comprehensive debugging capabilities.
