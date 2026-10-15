.PHONY: up down build seed test lint format migrate help

help:
	@echo "BetLens – available commands:"
	@echo "  make up       Start all services with Docker Compose"
	@echo "  make down     Stop all services"
	@echo "  make build    Rebuild Docker images"
	@echo "  make seed     Run database migrations and seed demo data"
	@echo "  make test     Run all tests (backend + frontend)"
	@echo "  make lint     Run linters (ruff, mypy, eslint)"
	@echo "  make format   Auto-format code (ruff, prettier)"
	@echo "  make migrate  Run Alembic migrations"

up:
	docker compose -f infra/docker-compose.yml up

down:
	docker compose -f infra/docker-compose.yml down

build:
	docker compose -f infra/docker-compose.yml build

seed:
	docker compose -f infra/docker-compose.yml exec api python -m app.db.seed

migrate:
	docker compose -f infra/docker-compose.yml exec api alembic upgrade head

test:
	@echo "── Backend tests ──"
	cd apps/api && pytest --tb=short -q
	@echo "── Frontend tests ──"
	cd apps/web && npm run test -- --run

lint:
	@echo "── Ruff ──"
	cd apps/api && ruff check .
	@echo "── Mypy ──"
	cd apps/api && mypy app
	@echo "── ESLint ──"
	cd apps/web && npm run lint

format:
	cd apps/api && ruff format .
	cd apps/web && npm run format