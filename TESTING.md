# Testing Guide

This guide explains how to run tests in the Financial Dashboard MCP project, whether from the command line or VS Code.

## Quick Start

### Simple Command Line Usage

```bash
# Run all tests (recommended)
.venv/bin/pytest

# Alternative: use the wrapper script
./pytest.sh

# Alternative: use make command
make test
```

### VS Code Integration

Tests are fully integrated with VS Code's testing interface:

1. **Test Discovery**: Tests are automatically discovered in the `tests/` directory
2. **Run Individual Tests**: Click the play button next to any test
3. **Run Test Files**: Click the play button next to any test file
4. **Debug Tests**: Click the debug button to debug any test

## Test Categories

### By Type
- **Unit Tests**: `pytest tests/unit/` - Fast, isolated component tests
- **Integration Tests**: `pytest tests/integration/` - Multi-component tests
- **API Tests**: `pytest tests/api/` - HTTP API endpoint tests

### By Markers
- **Fast Tests**: `pytest -m fast` - Tests that run quickly (<1 second)
- **Slow Tests**: `pytest -m slow` - Tests that take more time
- **Database Tests**: `pytest -m database` - Tests requiring database
- **External Tests**: `pytest -m external` - Tests making external API calls

### By Domain
- **ISIN Tests**: `pytest -m isin` - ISIN-specific functionality
- **Portfolio Tests**: `pytest -m portfolio` - Portfolio management
- **Auth Tests**: `pytest -m auth` - Authentication and authorization
- **Financial Tests**: `pytest -m financial` - Financial calculations

## Common Commands

```bash
# Run all tests with verbose output
.venv/bin/pytest -v

# Run tests with coverage report
.venv/bin/pytest --cov=backend --cov=frontend --cov=mcp_server --cov-report=html

# Run only fast tests
.venv/bin/pytest -m fast

# Run specific test file
.venv/bin/pytest tests/test_basic.py

# Run specific test function
.venv/bin/pytest tests/test_basic.py::test_basic_math

# Run tests matching pattern
.venv/bin/pytest -k "portfolio"

# Run tests with minimal output
.venv/bin/pytest -q

# Run tests and stop on first failure
.venv/bin/pytest -x
```

## Make Commands

The project includes convenient make commands:

```bash
make test              # Run all tests
make test-cov          # Run tests with coverage
make test-unit         # Run unit tests only
make test-integration  # Run integration tests
make test-api          # Run API tests
make test-fast         # Run fast tests only
make test-slow         # Run slow tests only
make test-smoke        # Run smoke tests
```

## Configuration

### Test Configuration Files

- **`pytest.ini`**: Main pytest configuration
- **`pyproject.toml`**: Modern Python project configuration
- **`tests/conftest.py`**: Test fixtures and setup
- **`.vscode/settings.json`**: VS Code testing integration

### Environment Variables

Tests run with these environment variables:
- `ENVIRONMENT=test`
- `PYTHONPATH=.` (project root)

### Test Data

- Test databases are created automatically
- Mock data is generated using Faker
- Test fixtures are defined in `conftest.py`

## VS Code Testing Features

### Available Features
- ✅ Test discovery and execution
- ✅ Individual test running
- ✅ Test debugging with breakpoints
- ✅ Test result display in Problems panel
- ✅ Test coverage visualization
- ✅ Parametrized test support

### VS Code Test Commands
- `Cmd+Shift+P` → "Python: Configure Tests" (if needed)
- `Cmd+Shift+P` → "Test: Run All Tests"
- `Cmd+Shift+P` → "Test: Run Failed Tests"

## Troubleshooting

### Common Issues

1. **ImportError**: Make sure you're using `.venv/bin/pytest`
2. **No tests discovered**: Check that test files start with `test_`
3. **VS Code not finding tests**: Reload window or check Python interpreter

### Virtual Environment Issues

```bash
# Ensure virtual environment is activated and pytest is installed
.venv/bin/pip install -e ".[dev]"

# Or reinstall testing dependencies
.venv/bin/pip install pytest pytest-asyncio pytest-cov
```

### Path Issues

If you encounter import errors:
```bash
# Set PYTHONPATH explicitly
export PYTHONPATH=/Users/thomas/Programming/financial-dashboard-mcp:$PYTHONPATH
.venv/bin/pytest
```

## Best Practices

### Writing Tests
1. Use descriptive test names
2. Follow the AAA pattern (Arrange, Act, Assert)
3. Use appropriate markers (`@pytest.mark.unit`, etc.)
4. Mock external dependencies
5. Keep tests independent and idempotent

### Running Tests
1. Always use the virtual environment's pytest
2. Run tests before committing code
3. Use coverage reports to identify untested code
4. Run different test categories during development

### CI/CD
Tests are designed to run in continuous integration environments with:
- Consistent virtual environment usage
- Proper environment variable setup
- Coverage reporting
- Multiple test categories

## Test Results

### Current Status
- ✅ 498 tests passing
- ⏭️ 4 tests skipped (integration tests requiring running services)
- ❌ 0 tests failing

### Coverage
Coverage reports are generated in `htmlcov/` directory when running with `--cov` flag.

## Support

For testing issues:
1. Check this guide first
2. Verify virtual environment setup
3. Check VS Code Python interpreter selection
4. Review test configuration files
5. Look at error messages in VS Code Problems panel
