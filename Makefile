.PHONY: help install install-dev format lint type-check security security-strict test test-cov test-unit test-integration test-api test-frontend test-isin test-benchmark test-fast test-slow test-smoke test-all test-quality clean run-backend run-frontend run-celery run-all docker-build docker-up docker-down migrate-create migrate-up migrate-down test-db-setup test-db-teardown

help:
	@echo "Available commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make install-dev   - Install development dependencies"
	@echo "  make format        - Format code with black and isort"
	@echo "  make lint          - Run linting with ruff and flake8"
	@echo "  make type-check    - Run type checking with mypy"
	@echo "  make security      - Run security checks (bandit + safety)"
	@echo "  make security-strict - Run strict security checks (fails on issues)"
	@echo "  make test          - Run all tests"
	@echo "  make test-cov      - Run tests with coverage report"
	@echo "  make test-unit     - Run unit tests only"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-api      - Run API tests"
	@echo "  make test-frontend - Run frontend tests"
	@echo "  make test-isin     - Run ISIN-specific tests"
	@echo "  make test-benchmark - Run performance benchmarks"
	@echo "  make test-fast     - Run fast tests only"
	@echo "  make test-slow     - Run slow tests only"
	@echo "  make test-smoke    - Run smoke tests"
	@echo "  make test-all      - Run comprehensive test suite"
	@echo "  make test-quality  - Run test quality analysis and validation"
	@echo "  make clean         - Clean up generated files"
	@echo "  make run-backend   - Run FastAPI backend"
	@echo "  make run-frontend  - Run Streamlit frontend"
	@echo "  make run-celery    - Run Celery worker"
	@echo "  make run-all       - Run all services locally"
	@echo "  make docker-build  - Build Docker images"
	@echo "  make docker-up     - Start Docker services"
	@echo "  make docker-down   - Stop Docker services"

install:
	pip install -r requirements.txt

install-dev: install
	pip install -e ".[dev]"
	pre-commit install

format:
	black .
	isort .
	ruff check --fix .

lint:
	ruff check .
	flake8 .
	mypy .

type-check:
	mypy .

security:
	@echo "🔒 Running security checks..."
	@echo "Running Bandit security scan..."
	bandit -r backend/ mcp_server/ -ll -f json -o bandit-report.json || true
	@echo "Running dependency vulnerability check..."
	safety check --json --output safety-report.json || true
	@echo "Security checks complete. Reports saved to bandit-report.json and safety-report.json"

security-strict:
	@echo "🔒 Running strict security checks (will fail on any issues)..."
	bandit -r backend/ mcp_server/ -ll
	safety check

# Testing commands - optimized for both CLI and VS Code
test:
	.venv/bin/pytest

test-cov:
	.venv/bin/pytest --cov=backend --cov=frontend --cov=mcp_server --cov-report=html --cov-report=xml --cov-report=term-missing --cov-fail-under=80

test-unit:
	.venv/bin/pytest tests/unit/ -v -m "unit and not slow"

test-integration:
	.venv/bin/pytest tests/integration/ -v -m "integration" --run-integration

test-api:
	.venv/bin/pytest tests/api/ -v -m "api"

test-frontend:
	.venv/bin/pytest tests/frontend/ -v -m "frontend" || echo "Frontend tests not yet implemented"

test-isin:
	.venv/bin/pytest -v -m "isin or validation or mapping or sync"

test-benchmark:
	.venv/bin/pytest -v -m "benchmark" --benchmark-only

test-fast:
	.venv/bin/pytest -v -m "fast or (not slow)"

test-slow:
	.venv/bin/pytest -v -m "slow"

test-smoke:
	.venv/bin/pytest -v -m "smoke"

test-all:
	pytest tests/ -v --run-integration --cov=backend --cov=frontend --cov-report=html --cov-report=term-missing

test-quality:
	python scripts/test_quality_check.py --json-output test_quality_report.json

# Database migration commands
migrate-create:
	alembic revision --autogenerate -m "$(message)"

migrate-up:
	alembic upgrade head

migrate-down:
	alembic downgrade -1

# Test database setup
test-db-setup:
	@echo "Setting up test database..."
	ENVIRONMENT=test python -c "from backend.database import init_db; init_db()"

test-db-teardown:
	@echo "Cleaning up test database..."
	ENVIRONMENT=test python -c "from backend.database import drop_db; drop_db()"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf dist/
	rm -rf build/
	rm -rf tests/logs/
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

run-backend:
	uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	streamlit run frontend/app.py

run-celery:
	celery -A backend.tasks worker --loglevel=info

run-celery-beat:
	celery -A backend.tasks beat --loglevel=info

run-flower:
	celery -A backend.tasks flower

run-all:
	@echo "Starting all services..."
	@echo "Please run the following commands in separate terminals:"
	@echo "1. make run-backend"
	@echo "2. make run-frontend"
	@echo "3. make run-celery"
	@echo "4. make run-celery-beat"
	@echo "5. Redis: redis-server"
	@echo "6. PostgreSQL: ensure it's running"

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

db-reset:
	alembic downgrade base
	alembic upgrade head
