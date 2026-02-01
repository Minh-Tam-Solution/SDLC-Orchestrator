# AI Coding Agent Instructions - SDLC Orchestrator

**Project**: SDLC Orchestrator - Operating System for Software 3.0  
**Version**: 1.2.0 (Sprint 105 - Launch Ready)  
**Framework**: SDLC 5.2.0 (Concentric Circles Model + AI Governance)

## 🎯 Project Context

SDLC Orchestrator is the **control plane that governs AI coders** (Cursor, Claude Code, Copilot). We don't compete with AI tools—we orchestrate them via Quality Gates, Evidence Vault, and Policy-as-Code (OPA).

**Core Value**: Reduce feature waste from 60-70% → <30% by enforcing evidence-based development.

**Software 3.0 Architecture (5 Layers)**:
1. **Infrastructure** (OSS): PostgreSQL, Redis, MinIO, OPA, Grafana
2. **Integration** (Thin adapters): OPA REST API, MinIO S3, GitHub API, Semgrep CLI
3. **Business Logic** (Core): Gate Engine, Evidence Vault, AI Context Engine
4. **EP-06 Codegen** (Innovation): IR-based code generation with 4-Gate Quality Pipeline
5. **AI Coders** (External): Cursor, Claude Code, Copilot—we orchestrate these

## 🏗️ Architecture & Code Organization

### Backend (Python FastAPI)
```
backend/
├── app/
│   ├── main.py                # FastAPI entry, lifespan, middleware
│   ├── api/v1/endpoints/      # Route handlers (64 endpoints)
│   ├── services/              # Business logic (24+ service classes)
│   ├── models/                # SQLAlchemy ORM models
│   ├── schemas/               # Pydantic models (request/response)
│   ├── core/config.py         # Settings (Pydantic BaseSettings)
│   ├── middleware/            # CORS, rate limiting, security headers
│   └── policies/              # OPA policy helpers
├── alembic/                   # Database migrations
├── tests/                     # pytest (94% coverage target)
└── pyproject.toml            # CLI packaging (sdlcctl)
```

**Service Layer Pattern**: All business logic in `services/` classes with dependency injection via FastAPI `Depends()`. Never put logic in route handlers—delegate to services.

**Example**: [backend/app/services/project_service.py](backend/app/services/project_service.py) shows full CRUD + GitHub integration pattern.

### Frontend (React + TypeScript)
```
frontend/
├── src/
│   ├── app/                   # Next.js app router pages
│   ├── components/            # shadcn/ui + custom components
│   ├── hooks/                 # React hooks (auth, projects, gates)
│   ├── contexts/              # Auth + Settings contexts
│   └── lib/                   # Utils (API client, auth)
├── e2e/                       # Playwright tests
└── playwright.config.ts       # E2E test config
```

**State Management**: TanStack Query (React Query) for server state. Context API for global state (auth, settings).

### Infrastructure
- **PostgreSQL 15.5** on port 15432 (shared `postgres-central`)
- **Redis 7.2** on port 6395 (caching + sessions)
- **MinIO** on ai-net network (evidence-vault bucket)
- **OPA 0.58** on port 8185 (policy engine)
- **Prometheus + Grafana** for observability

## 🔧 Development Workflows

### Setup & Running
```bash
# Start services (PostgreSQL, Redis, MinIO, OPA, Grafana)
make up

# Run migrations + seed data
make migrate
make seed

# Start backend dev server (uvicorn with reload)
make dev-backend  # http://localhost:8000

# Start frontend dev server
make dev-frontend  # http://localhost:5173
```

### Testing
```bash
# Run all tests
make test

# Backend tests (pytest + coverage)
make test-backend           # 94% coverage
make test-backend-strict    # Fail if <90%

# Frontend tests (Vitest + Playwright)
make test-frontend
```

**Test Structure**: Use `pytest` markers—`@pytest.mark.asyncio`, `@pytest.mark.integration`, `@pytest.mark.unit`. See [pytest.ini](pytest.ini) for full list.

**Fixtures**: `backend/tests/conftest.py` provides `test_db_session`, `test_client`, `test_user`, `admin_user`.

### Database Migrations
```bash
# Auto-generate migration (inspect models)
cd backend && alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

**Migration Policy**: Always review auto-generated migrations before committing. Add data migrations separately if needed.

## 🛡️ Critical Patterns & Conventions

### 1. Zero Mock Policy
**Never** use placeholders like `// TODO`, `pass`, or mock implementations in production code. All integrations must be real or use thin adapters.

- ✅ Real OPA HTTP calls via [backend/app/services/opa_service.py](backend/app/services/opa_service.py)
- ✅ Real MinIO S3 via [backend/app/utils/minio.py](backend/app/utils/minio.py)
- ❌ Fake/mock storage or policy evaluations

### 2. Code File Naming Standards
- **Python**: `snake_case.py` (max 50 chars) — e.g., `gate_service.py`
- **TypeScript**: `camelCase.tsx` or `PascalCase.tsx` — e.g., `GateCard.tsx`
- **Test files**: `test_<module>.py` or `<module>.test.tsx`

### 3. API Error Handling
All endpoints use structured HTTP exceptions:
```python
from fastapi import HTTPException, status

raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Project not found"
)
```

**Consistency**: Use `status_code` + `detail`. Never return plain strings.

### 4. Async/Await Pattern
All DB operations use SQLAlchemy AsyncSession:
```python
from sqlalchemy.ext.asyncio import AsyncSession

async def get_project(db: AsyncSession, project_id: int):
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()
```

**Never** mix sync/async DB calls—use `async with db.begin()` for transactions.

### 5. OPA Policy Integration
Policies in `backend/policy-packs/rego/`. To evaluate:
```python
from app.services.opa_service import get_opa_service

opa = get_opa_service()
result = await opa.evaluate_policy("sdlc.gates.g1", input_data)
```

**Policy Structure**: `sdlc.<domain>.<policy>` namespace. See [policy-packs/rego/](backend/policy-packs/rego/) for examples.

### 6. Evidence Vault Pattern
All evidence stored in MinIO with 8-state lifecycle:
```python
from app.services.evidence_service import get_evidence_service

evidence_svc = get_evidence_service(db)
evidence = await evidence_svc.upload_evidence(
    file=file,
    project_id=project_id,
    gate_id=gate_id,
    evidence_type="legal_clearance"
)
```

**States**: draft → pending → approved → archived (see [models/evidence.py](backend/app/models/evidence.py)).

## 📋 Common Tasks

### Adding a New API Endpoint
1. Define Pydantic schemas in `backend/app/schemas/<domain>.py`
2. Implement service logic in `backend/app/services/<domain>_service.py`
3. Create route handler in `backend/app/api/v1/endpoints/<domain>.py`
4. Register router in `backend/app/main.py`
5. Write tests in `backend/tests/unit/test_<domain>.py`

**Example**: See [api/v1/endpoints/projects.py](backend/app/api/v1/endpoints/projects.py) for full CRUD pattern.

### Adding a Database Model
1. Create model in `backend/app/models/<model_name>.py` (inherit `Base`)
2. Add relationships if needed (SQLAlchemy)
3. Run `alembic revision --autogenerate -m "Add <model>"`
4. Review migration, apply `alembic upgrade head`
5. Update schemas in `backend/app/schemas/<model_name>.py`

### Adding a Policy Pack
1. Create `.rego` file in `backend/policy-packs/rego/<domain>/`
2. Define policy: `package sdlc.<domain>.<policy>`
3. Load into OPA via API or volume mount (dev uses mount)
4. Test with `opa test policy-packs/rego/`

## 🚨 Security & Compliance

- **OWASP ASVS L2**: 98.4% coverage (264/264 requirements)
- **Authentication**: JWT + OAuth2 (GitHub, Google, Microsoft)
- **Authorization**: RBAC with 13 roles (see [models/user.py](backend/app/models/user.py))
- **Rate Limiting**: 100 req/min per user (see [middleware/rate_limiter.py](backend/app/middleware/rate_limiter.py))
- **SAST**: Semgrep with AI-specific security rules (see [backend/.semgrep.yml](backend/.semgrep.yml))

**AGPL Containment**: MinIO and Grafana accessed via network only—no code imports.

## 🔍 Debugging & Troubleshooting

### Logs
```bash
# Backend logs (uvicorn)
make logs-backend

# Docker service logs (PostgreSQL, Redis, MinIO, OPA)
make logs-docker

# Grafana dashboards
http://localhost:3000 (admin/admin_changeme)
```

### Common Issues
- **DB Connection Errors**: Check `postgres-central` is running on port 15432
- **MinIO Access Denied**: Ensure bucket `evidence-vault` exists and credentials match
- **OPA Policy Not Found**: Verify volume mount in [docker-compose.yml](docker-compose.yml) line 58
- **Redis Auth Failed**: Check `REDIS_PASSWORD` in `.env`

### Performance
- **API Latency Target**: <100ms p95
- **Dashboard Load**: <1s
- **Test Coverage**: 94% (backend), >90% (frontend)

## 📚 Key Documentation

- **Architecture**: [docs/02-design/ADR-003-API-Strategy.md](docs/02-design/ADR-003-API-Strategy.md)
- **Database Schema**: [docs/02-design/DATABASE-SCHEMA.md](docs/02-design/DATABASE-SCHEMA.md)
- **Security Baseline**: [docs/09-govern/OWASP-ASVS-L2.md](docs/09-govern/OWASP-ASVS-L2.md)
- **SDLC Framework**: [SDLC-Enterprise-Framework/README.md](SDLC-Enterprise-Framework/README.md)
- **Sprint Plans**: [docs/04-build/02-Sprint-Plans/](docs/04-build/02-Sprint-Plans/)

## 🎨 AI Governance Principles (SDLC 5.2.0)

1. **Framework-First**: Add features to SDLC Framework (methodology) before Orchestrator (automation)
2. **Planning Mode**: For changes >15 LOC, spawn sub-agents for pattern extraction before coding
3. **Model Selection**: Use Claude Opus 4.5 for large features, Sonnet for small fixes
4. **Evidence-Based**: Every decision must have traceable evidence in Evidence Vault
5. **Zero Vibecoding**: Enforce progressive routing (Green → Yellow → Orange → Red) via Quality Assurance System
6. **SASE Artifacts**: Generate CRP (Consultation), MRP (Merge-Readiness), VCR (Version Controlled Resolution)
7. **Agentic Grep > RAG**: Prefer direct codebase exploration over vector-based retrieval

## 🚀 Current Sprint Focus

**Sprint 105**: LAUNCH READY (99% web coverage, 550+ tests)  
**Next Milestone**: Soft Launch (March 1, 2026) → Public Launch (March 15, 2026)

**Active Work Areas**:
- Final polish for public launch
- SEO optimization
- Production deployment scripts
- User onboarding flows

---

**Last Updated**: January 28, 2026  
**Maintainer**: SDLC Orchestrator Team  
**License**: Apache 2.0 + AGPL containment for MinIO/Grafana
