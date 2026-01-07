# BFIH Backend Makefile
# Convenient commands for development, testing, and deployment

.PHONY: help setup test run docker-up docker-down clean lint format

# Variables
PYTHON := python3
VENV := venv
DOCKER_IMAGE := bfih-backend:latest
DOCKER_CONTAINER := bfih-api

# ============================================================================
# HELP
# ============================================================================

help:
	@echo "BFIH Backend - Available Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup           - Setup development environment"
	@echo "  make install         - Install dependencies"
	@echo "  make vector-store    - Initialize vector store"
	@echo ""
	@echo "Development:"
	@echo "  make run             - Start API server (local)"
	@echo "  make test            - Run tests"
	@echo "  make coverage        - Run tests with coverage report"
	@echo "  make lint            - Run code linting"
	@echo "  make format          - Format code with black"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build    - Build Docker image"
	@echo "  make docker-up       - Start services with docker-compose"
	@echo "  make docker-down     - Stop services"
	@echo "  make docker-logs     - View Docker logs"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean           - Clean up cache and temp files"
	@echo "  make check-env       - Verify environment configuration"
	@echo ""

# ============================================================================
# SETUP & INSTALLATION
# ============================================================================

setup: check-python
	@echo "Setting up development environment..."
	python -m venv $(VENV)
	. $(VENV)/bin/activate && pip install --upgrade pip
	. $(VENV)/bin/activate && pip install -r requirements.txt
	mkdir -p data/analyses data/scenarios data/status logs
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env - please edit with your API key"; fi
	@echo "✓ Setup complete!"

install:
	. $(VENV)/bin/activate && pip install -r requirements.txt

vector-store:
	. $(VENV)/bin/activate && python setup_vector_store.py

check-python:
	@command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required"; exit 1; }

# ============================================================================
# DEVELOPMENT
# ============================================================================

run:
	. $(VENV)/bin/activate && uvicorn bfih_api_server:app --reload --host 0.0.0.0 --port 8000

run-prod:
	. $(VENV)/bin/activate && uvicorn bfih_api_server:app --host 0.0.0.0 --port 8000 --workers 4

test:
	. $(VENV)/bin/activate && pytest test_bfih_backend.py -v

test-unit:
	. $(VENV)/bin/activate && pytest test_bfih_backend.py::TestDataModels -v
	. $(VENV)/bin/activate && pytest test_bfih_backend.py::TestStorageManager -v

test-integration:
	. $(VENV)/bin/activate && pytest test_bfih_backend.py::TestAPIEndpoints -v

coverage:
	. $(VENV)/bin/activate && pytest test_bfih_backend.py --cov=bfih --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	. $(VENV)/bin/activate && flake8 bfih_*.py --max-line-length=120
	. $(VENV)/bin/activate && mypy bfih_*.py --ignore-missing-imports || true

format:
	. $(VENV)/bin/activate && black bfih_*.py --line-length=120
	. $(VENV)/bin/activate && isort bfih_*.py

# ============================================================================
# DOCKER
# ============================================================================

docker-build:
	@echo "Building Docker image: $(DOCKER_IMAGE)"
	docker build -t $(DOCKER_IMAGE) .
	@echo "✓ Image built successfully"

docker-up:
	@echo "Starting services with docker-compose..."
	docker-compose up -d
	@echo "✓ Services started"
	@echo "  API: http://localhost:8000"
	@echo "  Postgres: localhost:5432"
	@echo "  Redis: localhost:6379"
	@echo "  Adminer: http://localhost:8080"

docker-down:
	@echo "Stopping services..."
	docker-compose down
	@echo "✓ Services stopped"

docker-logs:
	docker-compose logs -f bfih-api

docker-ps:
	docker-compose ps

docker-shell:
	docker-compose exec bfih-api /bin/bash

# ============================================================================
# HEALTH & STATUS
# ============================================================================

check-health:
	curl -s http://localhost:8000/api/health | jq . || echo "Backend not responding"

check-env:
	@echo "Checking environment configuration..."
	@grep -q OPENAI_API_KEY .env && echo "✓ OPENAI_API_KEY set" || echo "✗ OPENAI_API_KEY missing"
	@grep -q TREATISE_VECTOR_STORE_ID .env && echo "✓ TREATISE_VECTOR_STORE_ID set" || echo "✗ TREATISE_VECTOR_STORE_ID missing"
	@echo ""
	@echo "Python version:"
	@python3 --version
	@echo ""
	@echo "Virtual environment: $(VENV)"
	@if [ -d "$(VENV)" ]; then echo "✓ Virtual environment exists"; else echo "✗ Run 'make setup'"; fi

requirements-check:
	. $(VENV)/bin/activate && pip list | grep -E "openai|fastapi|uvicorn|sqlalchemy|redis"

# ============================================================================
# UTILITIES
# ============================================================================

clean:
	@echo "Cleaning up cache and temporary files..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage
	@echo "✓ Cleanup complete"

reset-data:
	@echo "Resetting data directory..."
	rm -rf data/analyses/*.json data/scenarios/*.json data/status/*
	mkdir -p data/analyses data/scenarios data/status
	@echo "✓ Data reset"

init-db:
	@echo "Initializing database..."
	docker-compose exec postgres psql -U bfih -d bfih_db -c "SELECT 1"
	@echo "✓ Database is ready"

# ============================================================================
# DEMO & QUICK TEST
# ============================================================================

demo:
	@echo "Running demo analysis..."
	. $(VENV)/bin/activate && python bfih_orchestrator.py

quick-test:
	@echo "Quick health check..."
	@curl -s http://localhost:8000/api/health | jq . || echo "❌ Backend not running"
	@echo ""
	@echo "To start backend: make run"

# ============================================================================
# SHORTCUTS
# ============================================================================

s: setup          # make s = make setup
i: install        # make i = make install
r: run           # make r = make run
t: test          # make t = make test
c: coverage      # make c = make coverage
l: lint          # make l = make lint
f: format        # make f = make format
d: docker-up     # make d = make docker-up
ddown: docker-down # make ddown = make docker-down

# ============================================================================
# .PHONY DECLARATIONS
# ============================================================================

.PHONY: help setup install vector-store check-python
.PHONY: run run-prod test test-unit test-integration coverage lint format
.PHONY: docker-build docker-up docker-down docker-logs docker-ps docker-shell
.PHONY: check-health check-env requirements-check
.PHONY: clean reset-data init-db
.PHONY: demo quick-test
.PHONY: s i r t c l f d ddown
