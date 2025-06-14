# 🔢 Semantic Versioning Guide

This project follows [Semantic Versioning](https://semver.org/) with automated version management using conventional commits.

## 📋 Overview

Our semantic versioning system automatically:

- 🏷️ Generates version numbers based on commit messages
- 📝 Updates CHANGELOG.md with release notes
- 🚀 Creates GitHub releases with tags
- 🐳 Builds and publishes Docker images
- ✅ Ensures version consistency across files

## 🎯 Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Commit Types

| Type | Version Bump | Description | Example |
|------|--------------|-------------|---------|
| `feat` | **Minor** (0.1.0) | New feature | `feat(api): add portfolio export endpoint` |
| `fix` | **Patch** (0.0.1) | Bug fix | `fix(frontend): resolve chart rendering issue` |
| `perf` | **Patch** (0.0.1) | Performance improvement | `perf(database): optimize query performance` |
| `BREAKING CHANGE` | **Major** (1.0.0) | Breaking change | `feat!: redesign API structure` |
| `docs` | No bump | Documentation only | `docs: update installation guide` |
| `style` | No bump | Code style changes | `style: fix formatting in utils.py` |
| `refactor` | No bump | Code refactoring | `refactor(services): simplify error handling` |
| `test` | No bump | Test changes | `test: add integration tests for API` |
| `chore` | No bump | Maintenance tasks | `chore: update dependencies` |
| `ci` | No bump | CI/CD changes | `ci: add security scanning workflow` |
| `build` | No bump | Build system changes | `build: update Docker configuration` |

### Breaking Changes

To indicate a breaking change, add `!` after the type or include `BREAKING CHANGE:` in the footer:

```bash
# Using ! notation
feat!: redesign user authentication system

# Using footer
feat(auth): add OAuth2 support

BREAKING CHANGE: The authentication system has been completely redesigned.
Existing tokens will be invalid and users must re-authenticate.
```

## 📦 Version Bumping Examples

### Patch Release (Bug Fixes)

```bash
git commit -m "fix(api): resolve null pointer exception in portfolio endpoint"
# Result: 1.0.0 → 1.0.1
```

### Minor Release (New Features)

```bash
git commit -m "feat(dashboard): add real-time price alerts"
# Result: 1.0.1 → 1.1.0
```

### Major Release (Breaking Changes)

```bash
git commit -m "feat!: migrate to new API v2 structure

BREAKING CHANGE: API endpoints have been reorganized under /api/v2/.
Clients must update their base URLs."
# Result: 1.1.0 → 2.0.0
```

## 🚀 Release Process

### Automatic Releases

1. **Commit with conventional format** to `main` branch
2. **GitHub Actions detects** commit type
3. **Version is calculated** based on commit history
4. **CHANGELOG.md is updated** with new entries
5. **Git tag is created** (e.g., `v1.2.3`)
6. **GitHub release is published** with release notes
7. **Docker images are built** and pushed to registry
8. **Version files are updated** across the codebase

### Manual Release (Emergency)

For emergency releases or manual control:

```bash
# Using commitizen
cz bump

# Using semantic-release
semantic-release version

# Using bump2version
bump2version patch  # or minor, major
```

## 🔧 Tools Configuration

### Commitizen

Configuration in `pyproject.toml`:

- Enforces conventional commit format
- Generates changelog entries
- Handles version bumping

### Semantic Release

Configuration in `pyproject.toml`:

- Automates the entire release process
- Integrates with GitHub releases
- Publishes to package registries

### Pre-commit Hooks

- Validates commit message format
- Checks version consistency
- Runs code quality checks

## 📊 Version Consistency

The following files are automatically kept in sync:

- `pyproject.toml` (primary source)
- `backend/__init__.py` (Python package version)
- `CHANGELOG.md` (release history)
- Git tags (release markers)

## 🛠️ Development Workflow

### Feature Development

```bash
# Create feature branch
git checkout -b feat/add-portfolio-analytics

# Make changes and commit with conventional format
git commit -m "feat(analytics): add portfolio performance metrics"

# Push and create PR
git push origin feat/add-portfolio-analytics
# Create PR to main branch
```

### Hotfix Process

```bash
# Create hotfix branch
git checkout -b fix/critical-security-issue

# Make fix and commit
git commit -m "fix(auth): patch SQL injection vulnerability"

# Push and create PR with priority
git push origin fix/critical-security-issue
# Create PR to main branch - will trigger patch release
```

## 📈 Release Notes

Release notes are automatically generated from commit messages:

### Example Release Notes

```markdown
## [1.2.0] - 2024-01-15

### ✨ Features
- feat(api): add portfolio export functionality (#123)
- feat(dashboard): implement real-time notifications (#125)

### 🐛 Bug Fixes
- fix(frontend): resolve chart rendering on mobile devices (#124)
- fix(database): handle connection timeouts gracefully (#126)

### 📚 Documentation
- docs: update API documentation with new endpoints (#127)

### 🔧 Maintenance
- chore: update dependencies to latest versions (#128)
```

## 🏷️ Tagging Strategy

Git tags follow the format: `v<version>`

- `v1.0.0` - Major release
- `v1.1.0` - Minor release
- `v1.1.1` - Patch release
- `v2.0.0-rc.1` - Release candidate

## 🚨 Important Notes

### Do NOT

- ❌ Manually edit version numbers in files
- ❌ Create tags manually (let automation handle it)
- ❌ Skip conventional commit format on main branch
- ❌ Force push to main branch

### DO

- ✅ Use conventional commit format consistently
- ✅ Include descriptive commit messages
- ✅ Test changes before merging to main
- ✅ Review generated changelog entries
- ✅ Verify automated releases work correctly

## 🔍 Troubleshooting

### Version Mismatch Errors

```bash
# Check current versions
python scripts/check_version_consistency.py

# Fix manually if needed
sed -i 's/__version__ = ".*"/__version__ = "1.2.3"/' backend/__init__.py
```

### Failed Release

```bash
# Check GitHub Actions logs
# Manually trigger release if needed
gh workflow run release.yml

# Force version bump if automation fails
cz bump --yes
git push --tags
```

### Commit Message Validation

```bash
# Test commit message format locally
echo "feat: add new feature" | cz check

# Fix commit message in last commit
git commit --amend -m "feat(scope): proper commit message"
```

## 📚 References

- [Semantic Versioning Specification](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Commitizen Documentation](https://commitizen-tools.github.io/commitizen/)
- [Python Semantic Release](https://python-semantic-release.readthedocs.io/)
- [Keep a Changelog](https://keepachangelog.com/)

---

For questions about versioning, check the [Contributing Guidelines](../CONTRIBUTING.md) or create an issue.
