.PHONY: help install install-dev format lint type-check test test-cov clean run-backend run-frontend run-celery run-all docker-build docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make install-dev   - Install development dependencies"
	@echo "  make format        - Format code with black and isort"
	@echo "  make lint          - Run linting with ruff and flake8"
	@echo "  make type-check    - Run type checking with mypy"
	@echo "  make test          - Run tests"
	@echo "  make test-cov      - Run tests with coverage"
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
	mypy backend frontend mcp_server

test:
	pytest

test-cov:
	pytest --cov=backend --cov=frontend --cov=mcp_server --cov-report=html --cov-report=term

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
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

migrate-create:
	alembic revision --autogenerate -m "$(message)"

migrate-up:
	alembic upgrade head

migrate-down:
	alembic downgrade -1

db-reset:
	alembic downgrade base
	alembic upgrade head
