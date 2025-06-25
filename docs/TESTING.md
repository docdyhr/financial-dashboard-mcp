# Testing Guide for Financial Dashboard MCP

This project has been configured with a comprehensive pytest testing setup for VS Code. This guide explains how to run tests and use the testing features.

## Quick Start

### Running Tests in VS Code

1. **Open the Test Explorer**: Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS) and run "Python: Configure Tests" if prompted.

2. **Run All Tests**: Use the VS Code Test Explorer or run the task "pytest: Run All Tests" from the Command Palette.

3. **Run Current File Tests**: Use `Ctrl+Shift+P` → "Tasks: Run Task" → "pytest: Run Current File"

4. **Debug Tests**: Use the debugger configurations provided in `.vscode/launch.json`

### Command Line Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_basic.py -v

# Run tests with coverage
python -m pytest tests/ --cov=backend --cov=frontend --cov-report=html

# Run only unit tests
python -m pytest -m unit -v

# Run only integration tests
python -m pytest -m integration -v

# Run with debugging (stops at first failure)
python -m pytest tests/ -x --pdb
```

## Configuration Files

### pytest.ini
- Contains pytest configuration
- Defines test markers for categorization
- Sets up coverage reporting
- Configures test discovery patterns

### .vscode/settings.json
- Configures Python testing in VS Code
- Sets pytest as the test framework
- Defines test arguments and paths
- Configures Python interpreter and linting

### .vscode/tasks.json
- Provides VS Code tasks for running tests
- Includes tasks for different test scenarios
- Configured with proper working directories

### .vscode/launch.json
- Debug configurations for tests
- Allows debugging specific test files or functions
- Configured with proper Python paths

## Test Structure

```
tests/
├── test_basic.py              # Basic functionality tests
├── test_backend.py            # FastAPI backend tests
├── test_cash_account_service.py # Cash account service tests
├── test_e2e_system.py         # End-to-end system tests
├── conftest.py                # Test fixtures and configuration
├── api/                       # API-specific tests
├── integration/               # Integration tests
├── unit/                      # Unit tests
└── ...
```

## Test Markers

Tests are categorized using pytest markers:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.frontend` - Frontend component tests
- `@pytest.mark.slow` - Tests that take more than 5 seconds
- `@pytest.mark.fast` - Quick tests (under 1 second)
- `@pytest.mark.database` - Tests requiring database access
- `@pytest.mark.external` - Tests making external API calls
- `@pytest.mark.financial` - Financial calculation tests
- `@pytest.mark.security` - Security-related tests

## Running Specific Test Categories

```bash
# Run only fast tests
python -m pytest -m fast

# Run all except slow tests
python -m pytest -m "not slow"

# Run API and integration tests
python -m pytest -m "api or integration"

# Run financial and database tests
python -m pytest -m "financial and database"
```

## Debugging Tests

### VS Code Debugging

1. Set breakpoints in your test files
2. Use the debug configurations:
   - "Debug Current Test File"
   - "Debug Specific Test Function"
   - "Debug All Tests"
3. Press F5 to start debugging

### Command Line Debugging

```bash
# Drop into debugger on first failure
python -m pytest tests/test_backend.py --pdb

# Debug specific test function
python -m pytest tests/test_backend.py::test_root_endpoint -s --pdb
```

## Coverage Reports

```bash
# Generate HTML coverage report
python -m pytest tests/ --cov=backend --cov=frontend --cov-report=html

# View coverage in browser
open htmlcov/index.html
```

## Test Environment

The tests use the following configuration:

- **Python Version**: 3.11+
- **Test Framework**: pytest 7.4+
- **Coverage**: pytest-cov
- **Environment**: Uses `.env` file for configuration
- **Database**: SQLite for testing (configured in conftest.py)

## Common Issues and Solutions

### Tests Not Discovered

1. Check Python interpreter in VS Code (bottom left corner)
2. Ensure `.venv/bin/python` is selected
3. Reload VS Code window: `Ctrl+Shift+P` → "Developer: Reload Window"

### Import Errors

1. Verify `PYTHONPATH` includes project root
2. Check virtual environment activation
3. Ensure all dependencies are installed: `pip install -r requirements-dev.txt`

### Database Errors

1. Check database connection string in `.env`
2. Ensure test database is accessible
3. Run database migrations if needed

### Slow Tests

1. Use `-m "not slow"` to exclude slow tests during development
2. Run slow tests separately: `-m slow`
3. Check external API rate limits

## VS Code Extensions

The following extensions are recommended for optimal testing experience:

- **Python** (`ms-python.python`) - Core Python support
- **Python Debugger** (`ms-python.debugpy`) - Enhanced debugging
- **Ruff** (`charliermarsh.ruff`) - Fast linting and formatting
- **Test Explorer UI** (`hbenl.vscode-test-explorer`) - Enhanced test UI
- **Code Runner** (`formulahendry.code-runner`) - Quick code execution

## Continuous Integration

This project is configured for CI/CD with:

- Automated test runs on pull requests
- Coverage reporting
- Code quality checks with Ruff
- Security scanning with Bandit

## Best Practices

1. **Write Descriptive Test Names**: Use clear, descriptive function names
2. **Use Fixtures**: Leverage pytest fixtures for test setup
3. **Mock External Dependencies**: Mock API calls and external services
4. **Test Edge Cases**: Include tests for error conditions and edge cases
5. **Keep Tests Fast**: Aim for fast feedback loops
6. **Organize Tests**: Use appropriate markers and directory structure
7. **Maintain Coverage**: Aim for >80% test coverage

## Troubleshooting

### Reset Test Configuration

1. Delete `.vscode/settings.json` test configuration
2. Run "Python: Configure Tests" from Command Palette
3. Select pytest and tests/ directory

### Clear Test Cache

```bash
# Clear pytest cache
rm -rf .pytest_cache/

# Clear Python cache
find . -name "__pycache__" -type d -exec rm -rf {} +
```

### Refresh Test Discovery

1. Open Command Palette (`Ctrl+Shift+P`)
2. Run "Python: Refresh Tests"
3. Or restart VS Code

For more detailed information, see the official pytest documentation: https://docs.pytest.org/
