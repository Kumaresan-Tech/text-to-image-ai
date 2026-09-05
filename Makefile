# ============================================
# Text2Img — Unified Task Runner
# ============================================
# Usage: make <target>

.PHONY: help dev down build logs migrate seed clean test lint \
        backup restore health deploy-ec2 deploy-ecs deploy-vercel \
        shell-backend shell-redis shell-postgres

# Default target
help: ## Show this help
	@echo "Text2Img Development Commands"
	@echo "============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Development ────────────────────────────────

dev: ## Start all services (dev mode with hot reload)
	docker compose up -d
	@echo ""
	@echo "Services starting..."
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/api/docs"
	@echo "  Postgres:  localhost:5432"
	@echo "  Redis:     localhost:6379"

down: ## Stop all services
	docker compose down

build: ## Build all Docker images
	docker compose build

rebuild: ## Force rebuild all images (no cache)
	docker compose build --no-cache

logs: ## Tail logs from all services
	docker compose logs -f

logs-backend: ## Tail backend logs
	docker compose logs -f backend

logs-worker: ## Tail worker logs
	docker compose logs -f worker

# ── Database ───────────────────────────────────

migrate: ## Run database migrations
	docker compose exec backend alembic upgrade head

migrate-new: ## Create a new migration (usage: make migrate-new MSG="add users table")
	docker compose exec backend alembic revision --autogenerate -m "$(MSG)"

migrate-history: ## Show migration history
	docker compose exec backend alembic history

seed: ## Seed default plans and data
	docker compose exec backend python -c "import asyncio; from app.database import async_session; from app.services.credit_service import seed_default_plans; asyncio.run(seed_default_plans(async_session()))"

# ── Maintenance ────────────────────────────────

clean: ## Remove all containers, volumes, and images
	docker compose down -v --rmi all
	@echo "Cleaned all Docker resources"

clean-storage: ## Clear local storage files
	docker compose exec backend rm -rf /app/storage/*
	@echo "Cleared storage"

# ── Backups ────────────────────────────────────

backup: ## Backup PostgreSQL database
	./deploy/scripts/backup-postgres.sh ./backups

restore: ## Restore PostgreSQL from backup (usage: make restore FILE=backups/text2img_20260101.sql.gz)
	./deploy/scripts/restore-postgres.sh $(FILE)

# ── Monitoring ─────────────────────────────────

health: ## Run health checks on all services
	./deploy/scripts/health-check.sh

status: ## Show container status
	docker compose ps

stats: ## Show container resource usage
	docker stats --no-stream

# ── Shell Access ───────────────────────────────

shell-backend: ## Open a shell in the backend container
	docker compose exec backend bash

shell-redis: ## Open a Redis CLI session
	docker compose exec redis redis-cli

shell-postgres: ## Open a PostgreSQL psql session
	docker compose exec postgres psql -U $${POSTGRES_USER:-text2img} -d $${POSTGRES_DB:-text2img}

# ── Production Deployment ──────────────────────

deploy-ec2: ## Deploy to EC2 (usage: make deploy-ec2 HOST=1.2.3.4)
	./deploy/aws/deploy-ec2.sh $(HOST)

deploy-ecs: ## Deploy to ECS Fargate
	./deploy/aws/deploy-ecs.sh production

deploy-vercel: ## Deploy frontend to Vercel
	cd frontend && ../deploy/vercel/deploy-vercel.sh production

# ── Testing ────────────────────────────────────

test-backend: ## Run backend tests
	docker compose exec backend python -m pytest -v

test-backend-cov: ## Run backend tests with coverage report
	docker compose exec backend python -m pytest --cov=app --cov-report=term-missing --cov-report=html

test-backend-fast: ## Run backend tests (skip slow tests)
	docker compose exec backend python -m pytest -m "not slow" -v

lint: ## Run linting on frontend and backend
	docker compose exec frontend npm run lint
	docker compose exec backend ruff check app/

lint-fix: ## Auto-fix lint issues
	docker compose exec backend ruff check --fix app/
	docker compose exec backend ruff format app/

format: ## Format all code
	docker compose exec backend ruff format app/
	docker compose exec frontend npx prettier --write . 2>/dev/null || true

typecheck: ## Run TypeScript type checking
	docker compose exec frontend npm run type-check

check: lint typecheck test-backend-fast ## Run all checks (lint + typecheck + tests)

# ── Utilities ──────────────────────────────────

generate-secret: ## Generate a random secret key
	@python3 -c "import secrets; print(secrets.token_hex(32))"

copy-env: ## Copy .env.example to .env (safe, won't overwrite)
	@test -f .env && echo ".env already exists" || cp .env.example .env && echo "Created .env — edit with your values"
