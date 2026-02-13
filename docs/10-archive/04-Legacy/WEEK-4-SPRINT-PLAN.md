# WEEK 4 SPRINT PLAN
## Backend API Implementation - Authentication + Gates APIs (14 Endpoints)

**Sprint**: Week 4 (Dec 3-6, 2025)
**Duration**: 4 days (Dec 3-6, excluding weekends)
**Team**: Backend Lead (1 FTE) + AI Development Partner
**Status**: ⏳ READY TO START (pending Gate G2 approval)

**Framework**: SDLC 5.1.3 Complete Lifecycle (10 Stages)
**Current Stage**: Stage 04 (BUILD |

---

## 🎯 SPRINT OBJECTIVES

### **Primary Goal**

Implement and test the first 14 API endpoints (Authentication + Gates) with production-ready quality:
- ✅ 6 Authentication endpoints (login, profile, refresh, logout, OAuth, MFA)
- ✅ 8 Gates endpoints (CRUD, submit, approve, list)
- ✅ 95%+ test coverage (unit + integration)
- ✅ <100ms p95 API latency (performance validated)
- ✅ Zero Mock Policy compliance (no placeholders)

### **Success Criteria**

**Technical**:
- [ ] All 14 endpoints working (100% success rate)
- [ ] 95%+ test coverage (pytest + pytest-asyncio)
- [ ] <100ms p95 API latency (pytest-benchmark)
- [ ] Zero P0/P1 bugs (production-blocking issues)
- [ ] Security validated (JWT, bcrypt, input validation)

**Quality**:
- [ ] Zero Mock Policy compliance (no `# TODO`, no `pass # implement later`)
- [ ] Code review passed (2+ approvers: Tech Lead + Backend Lead)
- [ ] Pre-commit hooks passing (ruff, mypy, black)
- [ ] CI/CD pipeline passing (lint, test, build)

**Documentation**:
- [ ] API documentation updated (OpenAPI spec examples)
- [ ] README updated (setup instructions, quick start)
- [ ] Troubleshooting guide updated (common issues)

---

## 📋 SPRINT BACKLOG

### **Day 1 (Dec 3)** - Authentication API (Part 1)

**Morning** (9am-12pm):
- [ ] **Task 1.1**: Environment setup validation (Docker Compose running, database migrated)
- [ ] **Task 1.2**: POST /auth/register - User registration with email + password
  - Input validation (Pydantic schema)
  - Password hashing (bcrypt, cost=12)
  - Duplicate email check
  - Success: 201 Created, Error: 400 Bad Request / 409 Conflict

- [ ] **Task 1.3**: POST /auth/login - JWT authentication
  - Email + password validation
  - JWT token generation (15min expiry)
  - Refresh token generation (30-day expiry)
  - Success: 200 OK with tokens, Error: 401 Unauthorized

**Afternoon** (1pm-5pm):
- [ ] **Task 1.4**: GET /auth/me - Get current user profile
  - JWT token validation (Bearer token)
  - User lookup (by user_id from token)
  - Success: 200 OK with user data, Error: 401 Unauthorized

- [ ] **Task 1.5**: Unit tests for Tasks 1.2-1.4 (pytest)
  - Test registration (valid + invalid inputs)
  - Test login (valid + invalid credentials)
  - Test profile retrieval (with + without token)

**End of Day 1**:
- [ ] 3 endpoints working (register, login, profile)
- [ ] ~60% test coverage
- [ ] Code review requested (Tech Lead)

---

### **Day 2 (Dec 4)** - Authentication API (Part 2)

**Morning** (9am-12pm):
- [ ] **Task 2.1**: POST /auth/refresh - Token refresh
  - Refresh token validation
  - New access token generation
  - Refresh token rotation (invalidate old, issue new)
  - Success: 200 OK with new tokens, Error: 401 Unauthorized

- [ ] **Task 2.2**: POST /auth/logout - Token revocation
  - Access token validation
  - Refresh token revocation (set is_revoked=true)
  - Success: 204 No Content, Error: 401 Unauthorized

**Afternoon** (1pm-5pm):
- [ ] **Task 2.3**: POST /auth/oauth/github - GitHub OAuth callback
  - OAuth code exchange (GitHub API)
  - User lookup or creation (by GitHub ID)
  - JWT token generation
  - Success: 200 OK with tokens, Error: 400 Bad Request

- [ ] **Task 2.4**: Integration tests for all 6 authentication endpoints
  - Test full auth flow (register → login → profile → logout)
  - Test token refresh (access token expired → refresh → new access token)
  - Test OAuth flow (GitHub callback → user creation → tokens)

**End of Day 2**:
- [ ] 6 authentication endpoints working (100% Auth API complete)
- [ ] ~90% test coverage (authentication)
- [ ] Performance validation (<500ms login, <200ms profile)

---

### **Day 3 (Dec 5)** - Gates API (Part 1)

**Morning** (9am-12pm):
- [ ] **Task 3.1**: POST /gates - Create gate
  - Input validation (gate_type, stage, project_id)
  - User authorization (project member check)
  - Gate creation (status=draft)
  - Success: 201 Created, Error: 400 Bad Request / 403 Forbidden

- [ ] **Task 3.2**: GET /gates/{gate_id} - Get gate details
  - Gate lookup (by ID)
  - User authorization (project member check)
  - Eager loading (relationships: approvals, evidence, policies)
  - Success: 200 OK, Error: 404 Not Found / 403 Forbidden

**Afternoon** (1pm-5pm):
- [ ] **Task 3.3**: PUT /gates/{gate_id} - Update gate
  - Gate lookup + authorization
  - Input validation (only draft gates can be updated)
  - Update gate fields (name, description, criteria)
  - Success: 200 OK, Error: 400 Bad Request / 403 Forbidden

- [ ] **Task 3.4**: GET /projects/{project_id}/gates - List project gates
  - User authorization (project member check)
  - Pagination (page, limit)
  - Filtering (status, stage, gate_type)
  - Success: 200 OK with paginated results, Error: 403 Forbidden

**End of Day 3**:
- [ ] 4 gates endpoints working (CRUD operations)
- [ ] ~70% test coverage (gates)
- [ ] Code review requested (Tech Lead)

---

### **Day 4 (Dec 6)** - Gates API (Part 2) + Testing

**Morning** (9am-12pm):
- [ ] **Task 4.1**: POST /gates/{gate_id}/submit - Submit gate for approval
  - Gate lookup + authorization
  - Status validation (draft → submitted)
  - Approval workflow initialization (create approval records)
  - Success: 200 OK, Error: 400 Bad Request / 403 Forbidden

- [ ] **Task 4.2**: POST /gates/{gate_id}/approve - Approve gate
  - Gate lookup + authorization (approver role check)
  - Multi-level approval logic (CTO → CPO → CEO)
  - Status update (submitted → approved or pending_approval)
  - Success: 200 OK, Error: 400 Bad Request / 403 Forbidden

**Afternoon** (1pm-5pm):
- [ ] **Task 4.3**: DELETE /gates/{gate_id} - Soft delete gate
  - Gate lookup + authorization (owner or admin)
  - Soft delete (set deleted_at timestamp)
  - Success: 204 No Content, Error: 403 Forbidden / 404 Not Found

- [ ] **Task 4.4**: GET /gates - List user's gates (across all projects)
  - User authorization (show only user's projects)
  - Pagination + filtering
  - Success: 200 OK with paginated results

- [ ] **Task 4.5**: Integration tests for all 8 gates endpoints
  - Test full gate workflow (create → update → submit → approve)
  - Test multi-level approval (CTO → CPO → CEO sequence)
  - Test authorization (project members vs non-members)

**End of Day 4**:
- [ ] 8 gates endpoints working (100% Gates API complete)
- [ ] ~95% test coverage (authentication + gates)
- [ ] Performance validation (<200ms CRUD, <300ms approval)

---

## 📊 SPRINT METRICS

### **Velocity Tracking**

| Day | Endpoints Completed | Tests Written | Coverage | Status |
|-----|---------------------|---------------|----------|--------|
| Day 1 | 3 (register, login, profile) | ~30 tests | 60% | ⏳ PENDING |
| Day 2 | 3 (refresh, logout, OAuth) | ~30 tests | 90% | ⏳ PENDING |
| Day 3 | 4 (create, get, update, list) | ~40 tests | 70% | ⏳ PENDING |
| Day 4 | 4 (submit, approve, delete, list) | ~40 tests | 95% | ⏳ PENDING |
| **TOTAL** | **14 endpoints** | **~140 tests** | **95%+** | **⏳ PENDING** |

### **Quality Gates**

**Code Quality**:
- [ ] Ruff linting: 0 errors (strict mode)
- [ ] Mypy type checking: 0 errors (strict mode)
- [ ] Black formatting: 100% compliant
- [ ] Pytest coverage: 95%+ (target met)

**Performance**:
- [ ] API latency p95: <100ms (CRUD operations)
- [ ] API latency p95: <500ms (authentication with bcrypt)
- [ ] Database queries: <10ms (simple SELECT), <50ms (JOIN)

**Security**:
- [ ] JWT validation: Working (15min expiry, refresh rotation)
- [ ] Password hashing: bcrypt cost=12 (OWASP compliant)
- [ ] Input validation: Pydantic schemas (SQL injection prevention)
- [ ] Authorization: RBAC working (project member checks)

---

## 🛠️ TECHNICAL IMPLEMENTATION GUIDE

### **Technology Stack**

**Backend**:
- FastAPI 0.109 (async, auto-docs)
- Python 3.11+ (type hints, async/await)
- PostgreSQL 15.5 (metadata database)
- SQLAlchemy 2.0 (async ORM)
- Pydantic 2.0 (schema validation)
- pytest + pytest-asyncio (testing)

**Authentication**:
- JWT (PyJWT library)
- bcrypt (password hashing)
- OAuth 2.0 (GitHub integration)

**Database**:
- Alembic (migrations)
- PgBouncer (connection pooling, optional for Week 4)

### **Project Structure**

```
backend/
├── app/
│   ├── api/
│   │   ├── dependencies.py           # JWT auth, RBAC dependencies
│   │   └── routes/
│   │       ├── auth.py               # 6 authentication endpoints
│   │       └── gates.py              # 8 gates endpoints
│   ├── models/
│   │   ├── user.py                   # User, Role, UserRole models
│   │   ├── gate.py                   # Gate, GateApproval models
│   │   └── project.py                # Project, ProjectMember models
│   ├── schemas/
│   │   ├── auth.py                   # Auth request/response schemas
│   │   └── gate.py                   # Gate request/response schemas
│   ├── core/
│   │   ├── config.py                 # Settings (Pydantic BaseSettings)
│   │   ├── security.py               # JWT, bcrypt utilities
│   │   └── database.py               # Async session management
│   └── main.py                       # FastAPI app initialization
├── tests/
│   ├── test_auth.py                  # Authentication tests
│   ├── test_gates.py                 # Gates tests
│   └── conftest.py                   # Pytest fixtures
├── alembic/
│   └── versions/
│       └── 001_initial_schema.py     # Database schema migration
├── requirements.txt                   # Python dependencies
└── pytest.ini                         # Pytest configuration
```

### **Code Standards**

**Type Hints** (100% coverage):
```python
from typing import Optional
from pydantic import BaseModel

async def create_gate(
    gate_data: GateCreate,
    current_user: User,
    db: AsyncSession
) -> Gate:
    """Create a new gate (production-ready, type-safe)."""
    # Implementation
```

**Error Handling** (comprehensive):
```python
from fastapi import HTTPException, status

if not gate:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Gate {gate_id} not found"
    )

if current_user.id not in project.member_ids:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not a member of this project"
    )
```

**Async/Await** (all I/O operations):
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def get_gate_by_id(gate_id: str, db: AsyncSession) -> Optional[Gate]:
    """Get gate by ID (async database query)."""
    result = await db.execute(
        select(Gate)
        .where(Gate.id == gate_id)
        .where(Gate.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()
```

---

## 🧪 TESTING STRATEGY

### **Unit Tests** (pytest)

**Test Coverage Target**: 95%+

**Example Test** (authentication):
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    """Test user registration with valid data."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "full_name": "Test User"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "password" not in data  # Password should not be returned

@pytest.mark.asyncio
async def test_register_user_duplicate_email(client: AsyncClient):
    """Test user registration with duplicate email."""
    # First registration
    await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "Password123!",
        "full_name": "Test User"
    })

    # Second registration (duplicate email)
    response = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "Password456!",
        "full_name": "Another User"
    })

    assert response.status_code == 409  # Conflict
    assert "already exists" in response.json()["detail"]
```

### **Integration Tests** (full workflow)

**Test Coverage Target**: 90%+

**Example Test** (gate workflow):
```python
@pytest.mark.asyncio
async def test_gate_full_workflow(client: AsyncClient, auth_headers: dict):
    """Test full gate workflow: create → submit → approve."""
    # 1. Create project
    project_response = await client.post(
        "/api/v1/projects",
        json={"name": "Test Project", "description": "Test"},
        headers=auth_headers
    )
    project_id = project_response.json()["id"]

    # 2. Create gate
    gate_response = await client.post(
        "/api/v1/gates",
        json={
            "name": "Gate G1",
            "gate_type": "planning",
            "stage": "01-planning",
            "project_id": project_id
        },
        headers=auth_headers
    )
    assert gate_response.status_code == 201
    gate_id = gate_response.json()["id"]

    # 3. Submit gate for approval
    submit_response = await client.post(
        f"/api/v1/gates/{gate_id}/submit",
        headers=auth_headers
    )
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "submitted"

    # 4. Approve gate (CTO)
    approve_response = await client.post(
        f"/api/v1/gates/{gate_id}/approve",
        json={"approver_role": "cto"},
        headers=auth_headers
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "pending_approval"  # Waiting for CPO
```

### **Performance Tests** (pytest-benchmark)

**Test Coverage Target**: <100ms p95 latency

**Example Test** (API latency):
```python
import pytest

@pytest.mark.benchmark
def test_login_performance(benchmark, client: AsyncClient):
    """Test login API latency (target: <500ms p95)."""
    result = benchmark(
        lambda: client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "Password123!"
        })
    )

    # Benchmark assertions
    assert benchmark.stats.stats.mean < 0.5  # Mean <500ms
    assert benchmark.stats.stats.percentile_95 < 0.5  # p95 <500ms
```

---

## 🚀 DEPLOYMENT CHECKLIST

### **Pre-Deployment** (Day 1 morning)

**Environment Setup**:
- [ ] Docker Compose running (8 services: backend, postgres, redis, minio, opa, grafana, prometheus, loki)
- [ ] Database migrated (21 tables created via Alembic)
- [ ] Seed data loaded (system roles: Owner, Admin, PM, Dev, QA, Viewer)
- [ ] Environment variables configured (.env file)

**Development Tools**:
- [ ] Pre-commit hooks installed (ruff, mypy, black)
- [ ] VS Code extensions installed (Python, Pylance, Ruff)
- [ ] API testing tool ready (Postman, Insomnia, or HTTPie)

### **During Development** (Day 1-4)

**Daily Checklist**:
- [ ] Morning: Pull latest main branch, run migrations
- [ ] Code: Follow Zero Mock Policy (no placeholders)
- [ ] Test: Write tests before code review (TDD preferred)
- [ ] Review: Request code review at end of day
- [ ] CI/CD: Ensure GitHub Actions passing (lint, test, build)

### **Post-Development** (Day 4 end)

**Final Validation**:
- [ ] All 14 endpoints working (100% success rate)
- [ ] Test coverage: 95%+ (pytest-cov report)
- [ ] Performance: <100ms p95 API latency (pytest-benchmark)
- [ ] Security: No critical vulnerabilities (Semgrep scan)
- [ ] Documentation: OpenAPI spec updated (Swagger UI)

---

## 📊 DAILY STANDUP FORMAT

### **Time**: 9am (15 minutes)

**Attendees**: Backend Lead + Tech Lead + AI Development Partner

**Agenda**:
1. **Yesterday** (5 min): What was completed?
2. **Today** (5 min): What will be worked on?
3. **Blockers** (5 min): Any blockers or risks?

**Example** (Day 2 standup):
- **Yesterday**: Completed 3 auth endpoints (register, login, profile), 60% test coverage
- **Today**: Implement refresh, logout, OAuth endpoints, reach 90% coverage
- **Blockers**: None (Docker Compose running smoothly)

---

## 🎯 SPRINT RISKS & MITIGATION

### **Risk 1: Authentication Complexity** (MEDIUM)

**Risk**: JWT + OAuth + MFA implementation more complex than estimated

**Mitigation**:
- Start with simple JWT authentication (Day 1)
- Add OAuth as optional (Day 2, can defer to Week 5 if needed)
- MFA is stretch goal (nice-to-have, not blocking)

**Status**: ✅ MITIGATED

---

### **Risk 2: Database Session Management** (LOW)

**Risk**: Async session lifecycle issues (connections not released)

**Mitigation**:
- Use proven pattern from Week 3 (`async with get_db()`)
- Explicit `await session.commit()` after yield
- Connection pooling configured (20 min, 30 max)

**Status**: ✅ MITIGATED (pattern tested in Week 3)

---

### **Risk 3: Test Coverage <95%** (LOW)

**Risk**: Running out of time for comprehensive test coverage

**Mitigation**:
- Write tests alongside implementation (TDD approach)
- Use pytest fixtures for common setup (conftest.py)
- Prioritize critical paths (auth flow, gate workflow)

**Status**: ✅ MITIGATED

---

## 📋 DEFINITION OF DONE

### **Endpoint Completion Criteria**

An endpoint is considered "done" when:
- [ ] ✅ **Implementation**: Production-ready code (no `# TODO`, no `pass`)
- [ ] ✅ **Type Hints**: 100% type hint coverage (mypy strict mode)
- [ ] ✅ **Error Handling**: All error cases handled (400, 401, 403, 404, 422, 500)
- [ ] ✅ **Unit Tests**: 95%+ coverage for this endpoint
- [ ] ✅ **Integration Tests**: End-to-end workflow tested
- [ ] ✅ **Performance**: <100ms p95 latency validated
- [ ] ✅ **Security**: Input validation, authorization checks
- [ ] ✅ **Documentation**: OpenAPI spec updated with examples
- [ ] ✅ **Code Review**: Approved by 2+ reviewers (Tech Lead + Backend Lead)
- [ ] ✅ **CI/CD**: GitHub Actions passing (lint, test, build)

### **Sprint Completion Criteria**

The sprint is considered "done" when:
- [ ] ✅ All 14 endpoints meet "Endpoint Completion Criteria"
- [ ] ✅ 95%+ overall test coverage (pytest-cov report)
- [ ] ✅ <100ms p95 API latency (pytest-benchmark)
- [ ] ✅ Zero P0/P1 bugs (production-blocking issues)
- [ ] ✅ Zero Mock Policy compliance (no placeholders)
- [ ] ✅ README updated (setup instructions, quick start)
- [ ] ✅ Demo prepared (for stakeholders)

---

## 🎉 SPRINT SUCCESS METRICS

### **Target Metrics** (Week 4 End)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Endpoints Completed** | 14/14 (100%) | Manual testing + integration tests |
| **Test Coverage** | 95%+ | pytest-cov report |
| **API Latency p95** | <100ms | pytest-benchmark |
| **Code Quality** | 9.5/10 | Tech Lead review |
| **Zero Mock Policy** | 100% | Code review validation |
| **Bugs (P0/P1)** | 0 | GitHub Issues count |
| **CI/CD Pipeline** | Passing | GitHub Actions status |

### **Stretch Goals** (Nice-to-Have)

- [ ] MFA implementation (TOTP with Google Authenticator)
- [ ] OAuth providers beyond GitHub (Google, Microsoft)
- [ ] API rate limiting (100 requests/min per user)
- [ ] Swagger UI theme customization
- [ ] Postman collection export

---

## 📅 NEXT SPRINT PREVIEW

### **Week 5 Sprint** (Dec 9-13, 2025)

**Objectives**:
- Evidence API (5 endpoints) - File upload, retrieval, verification
- Policies API (4 endpoints) - Policy packs, evaluation, OPA integration
- Projects API (5 endpoints) - Project CRUD, member management

**Total**: 14 endpoints (cumulative 28/28 endpoints complete)

**Target**: 95%+ test coverage, <100ms p95 latency, Zero Mock Policy

---

## 🔗 QUICK LINKS

### **Development Resources**

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [pytest Documentation](https://docs.pytest.org/)

### **Project Documentation**

- [API Specification (OpenAPI 3.0)](../../02-Design-Architecture/openapi.yml)
- [API Developer Guide](../../02-Design-Architecture/04-API-Design/API-DEVELOPER-GUIDE.md)
- [Database Schema (ERD)](../../01-Planning-Analysis/03-Data-Model/Data-Model-ERD.md)
- [Security Baseline](../../02-Design-Architecture/Security-Baseline.md)

### **Infrastructure**

- [Docker Deployment Guide](../../05-Deployment-Release/01-Deployment-Strategy/DOCKER-DEPLOYMENT-GUIDE.md)
- [Database Migration Strategy](../../05-Deployment-Release/01-Deployment-Strategy/DATABASE-MIGRATION-STRATEGY.md)

---

**Sprint Status**: ⏳ READY TO START (pending Gate G2 approval)
**Start Date**: December 3, 2025 (if Gate G2 approved)
**End Date**: December 6, 2025
**Next Sprint**: Week 5 (Dec 9-13, 2025)

---

*SDLC Orchestrator - First Governance-First Platform on SDLC 5.1.3. Zero Mock Policy enforced. Battle-tested patterns applied. Production excellence delivered.*

**"Gate G2 approved. Week 4 sprint ready. Let's build with discipline."** ⚔️ - Backend Lead

---

**Document Version**: 1.0.0
**Last Updated**: December 2, 2025
**Status**: ✅ READY FOR SPRINT KICKOFF
**Framework**: SDLC 5.1.3 Complete Lifecycle (10 Stages)
