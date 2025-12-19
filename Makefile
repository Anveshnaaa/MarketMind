.PHONY: help setup install start stop clean test lint type-check pipeline dashboard

help:
	@echo "Startup Market Analyzer - Makefile Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup          - Initial project setup"
	@echo "  make install        - Install dependencies with UV"
	@echo ""
	@echo "Docker:"
	@echo "  make start          - Start MongoDB cluster"
	@echo "  make stop           - Stop MongoDB cluster"
	@echo "  make clean          - Remove containers and volumes"
	@echo ""
	@echo "Development:"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Run linters"
	@echo "  make type-check     - Run MyPy type checking"
	@echo ""
	@echo "Pipeline:"
	@echo "  make pipeline       - Run complete data pipeline"
	@echo "  make dashboard      - Start Streamlit dashboard"

setup:
	@echo "Setting up project..."
	@uv sync
	@cp .env.example .env || true
	@echo "Setup complete!"

install:
	@uv sync

start:
	@echo "Starting MongoDB cluster..."
	@docker-compose up -d
	@echo "Waiting for replica set initialization..."
	@sleep 15
	@echo "MongoDB cluster started!"

stop:
	@echo "Stopping MongoDB cluster..."
	@docker-compose down

clean:
	@echo "Cleaning up Docker resources..."
	@docker-compose down -v
	@echo "Cleanup complete!"

test:
	@echo "Running tests..."
	@uv run pytest

lint:
	@echo "Running linters..."
	@uv run ruff check src tests
	@uv run black --check src tests

type-check:
	@echo "Running type checker..."
	@uv run mypy src

pipeline:
	@bash scripts/run_pipeline.sh

dashboard:
	@echo "Starting Streamlit dashboard..."
	@uv run streamlit run dashboard/app.py


