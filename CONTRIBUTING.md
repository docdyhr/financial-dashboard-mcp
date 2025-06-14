# 🤝 Contributing to Financial Dashboard MCP

Thank you for your interest in contributing! This guide will help you get started with contributing to our financial dashboard project.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)
- [Release Process](#release-process)

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 13+
- Redis 6+
- Docker and Docker Compose (optional)
- Git

### Development Setup

1. **Fork and clone the repository:**

   ```bash
   git clone https://github.com/YOUR_USERNAME/financial-dashboard-mcp.git
   cd financial-dashboard-mcp
   ```

2. **Set up the development environment:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Install pre-commit hooks:**

   ```bash
   pre-commit install
   pre-commit install --hook-type commit-msg
   ```

4. **Set up environment variables:**

   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

5. **Run database migrations:**

   ```bash
   alembic upgrade head
   ```

## 🔄 Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feat/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Your Changes

- Write clean, well-documented code
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run tests
pytest

# Run linting
make lint

# Check formatting
make format

# Run type checking
make type-check
```

### 4. Commit Your Changes

Use [Conventional Commits](https://conventionalcommits.org/) format:

```bash
git add .
git commit -m "feat(api): add portfolio export functionality"
```

### 5. Push and Create Pull Request

```bash
git push origin feat/your-feature-name
# Create PR through GitHub UI
```

## 📝 Commit Message Guidelines

We follow the [Conventional Commits](https://conventionalcommits.org/) specification for automatic versioning and changelog generation.

### Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Purpose | Version Bump |
|------|---------|--------------|
| `feat` | New feature | Minor |
| `fix` | Bug fix | Patch |
| `docs` | Documentation only | None |
| `style` | Formatting, missing semicolons, etc. | None |
| `refactor` | Code change that neither fixes bug nor adds feature | None |
| `perf` | Performance improvement | Patch |
| `test` | Adding missing tests | None |
| `chore` | Updating build tasks, package manager configs, etc. | None |
| `ci` | Changes to CI configuration | None |
| `build` | Changes that affect the build system | None |
| `revert` | Reverts a previous commit | None |

### Scopes

Use these scopes to indicate which part of the codebase is affected:

- `api` - Backend API changes
- `frontend` - Streamlit UI changes
- `database` - Database models or migrations
- `tasks` - Celery task queue changes
- `mcp` - MCP server changes
- `docker` - Docker configuration
- `docs` - Documentation
- `config` - Configuration files
- `scripts` - Utility scripts

### Examples

```bash
# Feature addition (minor version bump)
git commit -m "feat(api): add portfolio export endpoint"

# Bug fix (patch version bump)
git commit -m "fix(frontend): resolve chart rendering on mobile"

# Breaking change (major version bump)
git commit -m "feat!: redesign API authentication

BREAKING CHANGE: The authentication system has been completely redesigned.
All existing API tokens will be invalidated."

# Documentation update (no version bump)
git commit -m "docs: update installation guide"

# Chore (no version bump)
git commit -m "chore: update dependencies"
```

## 🎨 Code Style

### Python Code Style

We use the following tools for code formatting and linting:

- **Black** for code formatting
- **isort** for import sorting
- **Ruff** for fast linting
- **mypy** for type checking

### Pre-commit Hooks

Pre-commit hooks automatically run these tools before each commit:

```bash
# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

### Style Guidelines

1. **Follow PEP 8** for Python code style
2. **Use type hints** for all function parameters and return values
3. **Write docstrings** for all public functions and classes
4. **Keep functions small** and focused on a single responsibility
5. **Use descriptive variable names**
6. **Add comments** for complex business logic

### Example Code Style

```python
from typing import Optional, List
from decimal import Decimal

def calculate_portfolio_value(
    positions: List[Position],
    include_cash: bool = True
) -> Decimal:
    """
    Calculate the total value of a portfolio.

    Args:
        positions: List of portfolio positions
        include_cash: Whether to include cash positions

    Returns:
        Total portfolio value as Decimal

    Raises:
        ValueError: If positions list is empty
    """
    if not positions:
        raise ValueError("Positions list cannot be empty")

    total_value = Decimal("0")
    for position in positions:
        if include_cash or position.asset_type != AssetType.CASH:
            total_value += position.current_value

    return total_value
```

## 🧪 Testing

### Test Types

1. **Unit Tests**: Test individual functions and methods
2. **Integration Tests**: Test component interactions
3. **API Tests**: Test HTTP endpoints
4. **Database Tests**: Test database operations

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=backend --cov=frontend --cov=mcp_server

# Run specific test
pytest tests/test_api.py::test_portfolio_summary
```

### Test Guidelines

1. **Write tests for all new features**
2. **Test edge cases and error conditions**
3. **Use descriptive test names**
4. **Mock external dependencies**
5. **Keep tests independent and isolated**

### Example Test

```python
import pytest
from decimal import Decimal
from backend.services.portfolio import PortfolioService

class TestPortfolioService:
    def test_calculate_total_value_with_positions(self):
        """Test portfolio value calculation with valid positions."""
        # Arrange
        service = PortfolioService()
        positions = [
            create_test_position("AAPL", Decimal("150.00"), 10),
            create_test_position("GOOGL", Decimal("2500.00"), 5),
        ]

        # Act
        total_value = service.calculate_total_value(positions)

        # Assert
        expected = Decimal("14000.00")  # (150 * 10) + (2500 * 5)
        assert total_value == expected
```

## 📚 Documentation

### Types of Documentation

1. **Code Documentation**: Docstrings and inline comments
2. **API Documentation**: OpenAPI/Swagger specifications
3. **User Documentation**: Setup and usage guides
4. **Developer Documentation**: Architecture and contributing guides

### Documentation Guidelines

1. **Keep documentation up to date** with code changes
2. **Use clear, concise language**
3. **Include examples** where helpful
4. **Document breaking changes** in pull requests
5. **Update CHANGELOG.md** for user-facing changes (automated)

## 🚀 Release Process

Releases are fully automated using semantic versioning:

### Automatic Releases

1. **Commit using conventional format** to `main` branch
2. **GitHub Actions** analyzes commit messages
3. **Version is bumped** automatically (patch/minor/major)
4. **CHANGELOG.md** is updated with new entries
5. **Git tag** is created (e.g., `v1.2.3`)
6. **GitHub release** is published
7. **Docker images** are built and pushed

### Manual Release (Emergency)

Only for emergency situations:

```bash
# Using commitizen
cz bump

# Using semantic-release
semantic-release version

# Create hotfix
git checkout -b hotfix/critical-fix
# Make fix, commit, and create PR to main
```

## 🐛 Bug Reports

### Before Submitting

1. **Search existing issues** to avoid duplicates
2. **Test with the latest version**
3. **Gather relevant information**

### Bug Report Template

```markdown
**Bug Description**
A clear description of what the bug is.

**Steps to Reproduce**
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment**
- OS: [e.g., macOS 12.0]
- Python: [e.g., 3.11.0]
- Browser: [e.g., Chrome 96.0]
- Version: [e.g., 1.2.3]
```

## 💡 Feature Requests

### Feature Request Template

```markdown
**Feature Description**
A clear description of the feature you'd like to see.

**Use Case**
Describe the problem this feature would solve.

**Proposed Solution**
Your idea for implementing this feature.

**Alternatives Considered**
Any alternative solutions you've considered.

**Additional Context**
Any other context or screenshots about the feature.
```

## 📞 Getting Help

- 💬 **Discussions**: Use GitHub Discussions for questions
- 🐛 **Issues**: Create an issue for bugs or feature requests
- 📧 **Email**: Contact maintainers for security issues
- 📖 **Documentation**: Check existing docs first

## 🏆 Recognition

Contributors will be recognized in:

- **CHANGELOG.md** for significant contributions
- **README.md** contributors section
- **GitHub releases** for their contributions

## 📜 Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/). By participating, you agree to uphold this code.

---

Thank you for contributing to Financial Dashboard MCP! 🚀
