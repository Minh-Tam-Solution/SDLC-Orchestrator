# SDLC Orchestrator - Development Makefile
# Version: 1.0.0
# Purpose: Simplify common dev commands for local development

.PHONY: help up down restart logs clean install test lint format migrate seed backup

# Default target - show help
help:
	@echo "╔═══════════════════════════════════════════════════════════════╗"
	@echo "║  SDLC Orchestrator - Development Commands                    ║"
	@echo "╚═══════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📦 Setup & Installation:"
	@echo "  make install          Install all dependencies (backend + frontend)"
	@echo "  make install-backend  Install Python dependencies only"
	@echo "  make install-frontend Install Node.js dependencies only"
	@echo ""
	@echo "🚀 Development:"
	@echo "  make up              Start all services (Docker + backend + frontend)"
	@echo "  make down            Stop all services"
	@echo "  make restart         Restart all services"
	@echo "  make logs            Show logs from all services"
	@echo "  make clean           Clean all artifacts (containers, cache, build)"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  make test            Run all tests (backend + frontend)"
	@echo "  make test-backend    Run backend tests only"
	@echo "  make test-frontend   Run frontend tests only"
	@echo "  make lint            Run linters (backend + frontend)"
	@echo "  make format          Format code (black + prettier)"
	@echo ""
	@echo "💾 Database:"
	@echo "  make migrate         Run database migrations"
	@echo "  make migrate-create  Create new migration"
	@echo "  make seed            Seed database with test data"
	@echo "  make db-reset        Reset database (drop + migrate + seed)"
	@echo "  make backup          Backup database to ./backups/"
	@echo ""
	@echo "🔍 Debugging:"
	@echo "  make logs-backend    Show backend logs"
	@echo "  make logs-frontend   Show frontend logs"
	@echo "  make logs-docker     Show Docker service logs"
	@echo "  make shell-backend   Open backend shell"
	@echo "  make shell-db        Open PostgreSQL shell"
	@echo ""

# ============================================================================
# Setup & Installation
# ============================================================================

install: install-backend install-frontend
	@echo "✅ All dependencies installed"

install-backend:
	@echo "📦 Installing backend dependencies..."
	cd backend && python -m pip install --upgrade pip
	cd backend && pip install -r requirements.txt
	@echo "✅ Backend dependencies installed"

install-frontend:
	@echo "📦 Installing frontend dependencies..."
	cd frontend/web && npm install
	@echo "✅ Frontend dependencies installed"

# ============================================================================
# Development - Docker Services
# ============================================================================

up:
	@echo "🚀 Starting SDLC Orchestrator services..."
	docker-compose up -d
	@echo "⏳ Waiting for services to be healthy..."
	@sleep 5
	@docker-compose ps
	@echo ""
	@echo "✅ Services started:"
	@echo "  - PostgreSQL:  http://localhost:5432"
	@echo "  - Redis:       http://localhost:6379"
	@echo "  - MinIO:       http://localhost:9000 (Console: http://localhost:9001)"
	@echo "  - OPA:         http://localhost:8181"
	@echo "  - Prometheus:  http://localhost:9090"
	@echo "  - Grafana:     http://localhost:3000 (admin/admin_changeme)"
	@echo ""
	@echo "🔧 Next steps:"
	@echo "  1. make migrate    # Run database migrations"
	@echo "  2. make seed       # Seed test data"
	@echo "  3. make dev        # Start backend + frontend dev servers"

down:
	@echo "🛑 Stopping all services..."
	docker-compose down
	@echo "✅ All services stopped"

restart: down up

logs:
	docker-compose logs -f

logs-docker:
	docker-compose logs -f postgres redis minio opa prometheus grafana

clean:
	@echo "🧹 Cleaning artifacts..."
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete"

# ============================================================================
# Development - Backend & Frontend
# ============================================================================

dev-backend:
	@echo "🚀 Starting backend dev server..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "🚀 Starting frontend dev server..."
	cd frontend/web && npm run dev

dev:
	@echo "🚀 Starting backend + frontend..."
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:5173"
	@make -j2 dev-backend dev-frontend

# ============================================================================
# Testing & Quality
# ============================================================================

test: test-backend test-frontend
	@echo "✅ All tests passed"

test-backend:
	@echo "🧪 Running backend tests..."
	cd backend && pytest tests/ -v --cov=app --cov-report=term --cov-report=html

test-frontend:
	@echo "🧪 Running frontend tests..."
	cd frontend/web && npm run test

lint: lint-backend lint-frontend
	@echo "✅ All linting passed"

lint-backend:
	@echo "🔍 Linting backend..."
	cd backend && flake8 app/ tests/
	cd backend && mypy app/

lint-frontend:
	@echo "🔍 Linting frontend..."
	cd frontend/web && npm run lint

format:
	@echo "✨ Formatting code..."
	cd backend && black app/ tests/
	cd backend && isort app/ tests/
	cd frontend/web && npm run format
	@echo "✅ Code formatted"

# ============================================================================
# Database Operations
# ============================================================================

migrate:
	@echo "💾 Running database migrations..."
	cd backend && alembic upgrade head
	@echo "✅ Migrations complete"

migrate-create:
	@echo "💾 Creating new migration..."
	@read -p "Migration name: " name; \
	cd backend && alembic revision --autogenerate -m "$$name"

seed:
	@echo "🌱 Seeding database..."
	cd backend && python scripts/seed_data.py
	@echo "✅ Database seeded"

db-reset:
	@echo "🔄 Resetting database..."
	docker-compose exec postgres psql -U sdlc_user -d sdlc_orchestrator -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	@make migrate
	@make seed
	@echo "✅ Database reset complete"

backup:
	@echo "💾 Backing up database..."
	@mkdir -p backups
	@BACKUP_FILE=backups/sdlc_orchestrator_$$(date +%Y%m%d_%H%M%S).sql; \
	docker-compose exec -T postgres pg_dump -U sdlc_user sdlc_orchestrator > $$BACKUP_FILE; \
	echo "✅ Backup saved to $$BACKUP_FILE"

# ============================================================================
# Debugging & Utilities
# ============================================================================

logs-backend:
	@echo "📋 Backend logs (Ctrl+C to exit)..."
	cd backend && tail -f logs/app.log

logs-frontend:
	@echo "📋 Frontend logs..."
	docker-compose logs -f frontend

shell-backend:
	@echo "🐚 Opening backend Python shell..."
	cd backend && python

shell-db:
	@echo "🐚 Opening PostgreSQL shell..."
	docker-compose exec postgres psql -U sdlc_user -d sdlc_orchestrator

shell-redis:
	@echo "🐚 Opening Redis shell..."
	docker-compose exec redis redis-cli -a $$(grep REDIS_PASSWORD .env | cut -d '=' -f2 || echo "changeme_redis_password")

shell-minio:
	@echo "🐚 MinIO Console: http://localhost:9001"
	@echo "  User: $$(grep MINIO_ROOT_USER .env | cut -d '=' -f2 || echo 'minioadmin')"
	@echo "  Pass: $$(grep MINIO_ROOT_PASSWORD .env | cut -d '=' -f2 || echo 'minioadmin_changeme')"

# ============================================================================
# Policy Pack Management
# ============================================================================

policy-validate:
	@echo "🔍 Validating policy packs..."
	docker-compose exec opa opa test /policies -v
	@echo "✅ All policy packs valid"

policy-load:
	@echo "📥 Loading policy packs into OPA..."
	curl -X PUT --data-binary @policy-packs/rego/lite.rego http://localhost:8181/v1/policies/lite
	curl -X PUT --data-binary @policy-packs/rego/standard.rego http://localhost:8181/v1/policies/standard
	curl -X PUT --data-binary @policy-packs/rego/enterprise.rego http://localhost:8181/v1/policies/enterprise
	@echo "✅ Policy packs loaded"

# ============================================================================
# Security Scanning & Auditing (Week 5)
# ============================================================================

security-audit:
	@echo "🔒 Running comprehensive security audit..."
	@echo "  - Semgrep SAST scan (OWASP Top 10)"
	@echo "  - Grype vulnerability scan (CVE database)"
	@echo "  - Syft SBOM generation (CycloneDX)"
	@echo "  - Gitleaks secrets detection"
	@bash scripts/security-audit.sh
	@echo "✅ Security audit complete. Check reports/security/ for results"

security-scan-quick:
	@echo "🔍 Running quick security scan (Semgrep only)..."
	cd backend && semgrep --config=auto --config=p/owasp-top-ten --config=p/python .
	@echo "✅ Quick scan complete"

security-sbom:
	@echo "📦 Generating Software Bill of Materials (SBOM)..."
	@mkdir -p reports/security
	cd backend && syft packages dir:. -o cyclonedx-json > ../reports/security/sbom-$$(date +%Y%m%d_%H%M%S).json
	@echo "✅ SBOM generated: reports/security/sbom-*.json"

security-vuln-scan:
	@echo "🛡️  Scanning for vulnerabilities (Grype)..."
	@mkdir -p reports/security
	@cd backend && syft packages dir:. -o cyclonedx-json | grype --output json --file ../reports/security/grype-$$(date +%Y%m%d_%H%M%S).json
	@echo "✅ Vulnerability scan complete. Check reports/security/ for results"

security-secrets:
	@echo "🔐 Scanning for hardcoded secrets..."
	@if command -v gitleaks > /dev/null; then \
		mkdir -p reports/security; \
		gitleaks detect --source . --report-path reports/security/gitleaks-$$(date +%Y%m%d_%H%M%S).json --no-banner; \
		echo "✅ Secrets scan complete. Check reports/security/ for results"; \
	else \
		echo "⚠️  gitleaks not installed. Install with: https://github.com/gitleaks/gitleaks#installation"; \
	fi

# ============================================================================
# Production Build
# ============================================================================

build:
	@echo "🏗️ Building production images..."
	docker build -t sdlc-orchestrator-backend:latest -f backend/Dockerfile backend/
	docker build -t sdlc-orchestrator-frontend:latest -f frontend/web/Dockerfile frontend/web/
	@echo "✅ Production images built"

deploy-staging:
	@echo "🚀 Deploying to staging..."
	@echo "⚠️ Not implemented yet - requires staging environment setup"

deploy-prod:
	@echo "🚀 Deploying to production..."
	@echo "⚠️ Not implemented yet - requires production environment setup"

# ============================================================================
# Monitoring & Health Checks
# ============================================================================

health:
	@echo "🏥 Checking service health..."
	@echo ""
	@echo "PostgreSQL:"
	@docker-compose exec postgres pg_isready -U sdlc_user || echo "❌ Down"
	@echo ""
	@echo "Redis:"
	@docker-compose exec redis redis-cli -a $$(grep REDIS_PASSWORD .env | cut -d '=' -f2 || echo "changeme_redis_password") ping || echo "❌ Down"
	@echo ""
	@echo "MinIO:"
	@curl -s http://localhost:9000/minio/health/live > /dev/null && echo "✅ Up" || echo "❌ Down"
	@echo ""
	@echo "OPA:"
	@curl -s http://localhost:8181/health > /dev/null && echo "✅ Up" || echo "❌ Down"
	@echo ""
	@echo "Prometheus:"
	@curl -s http://localhost:9090/-/healthy > /dev/null && echo "✅ Up" || echo "❌ Down"
	@echo ""
	@echo "Grafana:"
	@curl -s http://localhost:3000/api/health > /dev/null && echo "✅ Up" || echo "❌ Down"

metrics:
	@echo "📊 Opening metrics dashboards..."
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Grafana:    http://localhost:3000"
	open http://localhost:9090 http://localhost:3000

# ============================================================================
# Quick Start (First Time Setup)
# ============================================================================

quickstart:
	@echo "╔═══════════════════════════════════════════════════════════════╗"
	@echo "║  SDLC Orchestrator - Quick Start                             ║"
	@echo "╚═══════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📋 Step 1/5: Copying .env file..."
	@cp .env.example .env
	@echo "⚠️  IMPORTANT: Edit .env and set your API keys!"
	@echo ""
	@echo "📋 Step 2/5: Installing dependencies..."
	@make install
	@echo ""
	@echo "📋 Step 3/5: Starting Docker services..."
	@make up
	@echo ""
	@echo "📋 Step 4/5: Running migrations..."
	@make migrate
	@echo ""
	@echo "📋 Step 5/5: Seeding database..."
	@make seed
	@echo ""
	@echo "✅ Quick start complete!"
	@echo ""
	@echo "🔧 Next steps:"
	@echo "  1. Edit .env and add your API keys (ANTHROPIC_API_KEY, etc.)"
	@echo "  2. Run 'make dev' to start backend + frontend"
	@echo "  3. Open http://localhost:5173 in your browser"
