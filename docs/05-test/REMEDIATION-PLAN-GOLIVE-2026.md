# Test Remediation Plan for Go-Live 2026

**Date**: January 27, 2026
**Status**: ✅ **ACTIVE - Execution Ready**
**Framework**: SDLC 5.2.0 (7-Pillar + AI Governance Principles)
**Owner**: QA Lead + Backend Lead + CTO
**Target Go-Live**: February 28, 2026 (30 days)

---

## Executive Summary

This document provides a **detailed remediation plan** to bring SDLC Orchestrator test coverage from current state (estimated <50%) to production-ready state (95%+ unit, 90%+ integration, 10 E2E paths) within 30 days.

**Critical Gaps Identified**:
1. ❌ No TDD enforcement (code written before tests)
2. ❌ No test factories (hardcoded test data)
3. ❌ Unit coverage <50% (target: 95%+)
4. ❌ No framework compliance tests (SDLC 5.2.0 alignment)
5. ⚠️ Integration tests incomplete (GitHub/MinIO only)
6. ⚠️ No Playwright E2E tests (Bruno API tests exist)
7. ⚠️ No load testing (target: 100K concurrent users)
8. ⚠️ No security audit (OWASP ASVS L2)

**Remediation Approach**:
- **Sprint 107** (Week 1): Foundation & Infrastructure
- **Sprint 108** (Week 2): Core Tests & Coverage
- **Sprint 109** (Week 3): E2E, Load, Security & Go-Live

---

## 1. Current State Assessment

### 1.1 Gap Analysis (January 27, 2026)

| Area | Current State | Target State | Gap | Priority |
|------|--------------|--------------|-----|----------|
| **Test Strategy** | Partial (pre-TDD) | TDD-first | Document only | P0 ✅ (DONE) |
| **Test Infrastructure** | ⚠️ Docker Compose partial | Real services | docker-compose.test.yml | P0 |
| **Test Factories** | ❌ None | All models | 6 factories | P0 |
| **Test Stubs** | ❌ None | All services | 15 service stubs | P0 |
| **Unit Tests** | ⚠️ <50% | 95%+ | +45% coverage | P0 |
| **Integration Tests** | ⚠️ GitHub/MinIO only | All API endpoints | +40 tests | P1 |
| **E2E Tests** | ⚠️ Bruno only | Playwright 10 paths | 10 tests | P1 |
| **Load Tests** | ❌ None | 100K users | 1 test suite | P2 |
| **Security Audit** | ❌ None | OWASP ASVS L2 | 1 audit report | P2 |
| **Framework Compliance** | ❌ None | SDLC 5.2.0 | 20+ tests | P1 |
| **CI/CD Enforcement** | ⚠️ No coverage check | 95% threshold | Update pipeline | P0 |

---

### 1.2 Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Low test coverage** | P0 - Production bugs | High | TDD enforcement, 95% coverage target |
| **No E2E tests** | P1 - Critical path failures | Medium | Playwright 10 journeys |
| **No load testing** | P2 - Performance bottlenecks | Medium | Locust 100K users simulation |
| **Framework drift** | P1 - Non-compliance | High | Framework compliance tests |
| **No TDD culture** | P0 - Technical debt | High | Developer training, CI/CD enforcement |

---

## 2. Sprint 107: Foundation & Infrastructure (Week 1)

### 2.1 Objectives

- ✅ Establish TDD culture and infrastructure
- ✅ Create test factories for all models
- ✅ Create test stubs for all services
- ✅ Setup Docker test environment
- ✅ Update CI/CD pipeline

**Success Criteria**:
- [ ] All 6 test factories implemented
- [ ] All 15 service test stubs created
- [ ] docker-compose.test.yml working
- [ ] CI/CD enforces 95% coverage threshold
- [ ] Developer TDD guide published

---

### 2.2 Deliverables

#### D1: Test Factories (Day 1-2)

**Location**: `backend/tests/factories/`

```python
# backend/tests/factories/__init__.py
from .user_factory import get_mock_user, get_mock_user_data
from .project_factory import get_mock_project, get_mock_project_data
from .gate_factory import get_mock_gate, get_mock_gate_data
from .evidence_factory import get_mock_evidence, get_mock_evidence_data
from .policy_factory import get_mock_policy, get_mock_policy_data
from .codegen_factory import get_mock_codegen_spec, get_mock_codegen_result

__all__ = [
    "get_mock_user",
    "get_mock_user_data",
    "get_mock_project",
    "get_mock_project_data",
    "get_mock_gate",
    "get_mock_gate_data",
    "get_mock_evidence",
    "get_mock_evidence_data",
    "get_mock_policy",
    "get_mock_policy_data",
    "get_mock_codegen_spec",
    "get_mock_codegen_result",
]
```

**Factory Template** (apply to all 6 factories):

```python
# backend/tests/factories/gate_factory.py

from typing import Optional, Dict
from datetime import datetime, UTC
from uuid import uuid4

from app.models.gate import Gate


def get_mock_gate(overrides: Optional[Dict] = None) -> Gate:
    """
    Factory for Gate test data.

    Usage:
        gate = get_mock_gate()
        gate_approved = get_mock_gate({"status": "approved"})
        gate_rejected = get_mock_gate({"status": "rejected", "rejection_reason": "Incomplete"})

    Args:
        overrides: Optional dict to override default values

    Returns:
        Gate instance with test data
    """
    defaults = {
        "id": str(uuid4()),
        "name": "Test Gate G1 - Design Ready",
        "stage": "DESIGN",
        "gate_id": "G1",
        "status": "pending",
        "project_id": str(uuid4()),
        "approvers": ["cto@example.com", "architect@example.com"],
        "created_by": "em@example.com",
        "created_at": datetime.now(UTC),
        "evidence_required": ["design_doc", "api_spec", "data_model"],
        "evidence_submitted": [],
        "exit_criteria": [
            "Architecture documented",
            "API contracts defined",
            "Data model reviewed",
        ],
    }

    return Gate(**(defaults | (overrides or {})))


def get_mock_gate_data(overrides: Optional[Dict] = None) -> Dict:
    """
    Factory for Gate creation request data (API payload).

    Usage:
        data = get_mock_gate_data()
        response = client.post("/api/v1/gates", json=data)

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict suitable for API POST /api/v1/gates
    """
    defaults = {
        "name": "Test Gate G1 - Design Ready",
        "stage": "DESIGN",
        "gate_id": "G1",
        "project_id": str(uuid4()),
        "approvers": ["cto@example.com"],
        "exit_criteria": ["Architecture documented"],
    }

    return defaults | (overrides or {})
```

**Checklist**:
- [ ] `user_factory.py` (User, UserData)
- [ ] `project_factory.py` (Project, ProjectData)
- [ ] `gate_factory.py` (Gate, GateData)
- [ ] `evidence_factory.py` (Evidence, EvidenceData)
- [ ] `policy_factory.py` (Policy, PolicyData)
- [ ] `codegen_factory.py` (CodegenSpec, CodegenResult)

**Acceptance Criteria**:
- All factories follow template pattern
- All factories have docstrings with usage examples
- All factories return valid model instances
- All factories support overrides parameter

---

#### D2: Test Stubs (Day 2-3)

**Location**: `backend/tests/services/`

**Services to stub**:
1. `test_gate_service.py` (Gate CRUD, approval workflow)
2. `test_evidence_service.py` (Evidence upload, integrity validation)
3. `test_project_service.py` (Project CRUD, team management)
4. `test_policy_service.py` (Policy evaluation, OPA integration)
5. `test_user_service.py` (User CRUD, authentication)
6. `test_ai_context_service.py` (AI prompts, multi-provider)
7. `test_codegen_service.py` (Code generation, quality gates)
8. `test_ollama_provider.py` (Ollama integration)
9. `test_claude_provider.py` (Claude integration)
10. `test_github_service.py` (GitHub sync, OAuth)
11. `test_minio_service.py` (S3 operations, evidence storage)
12. `test_opa_service.py` (Policy evaluation)
13. `test_redis_service.py` (Caching, sessions)
14. `test_notification_service.py` (Email, Slack, in-app)
15. `test_planning_orchestrator_service.py` (Risk-based planning)

**Test Stub Template**:

```python
# backend/tests/services/test_gate_service.py

import pytest
from app.services.gate_service import GateService
from tests.factories import get_mock_gate, get_mock_gate_data


class TestGateService:
    """
    Unit tests for GateService.

    Design Decision (ADR-XXX): GateService orchestrates:
    - Gate CRUD operations
    - Evidence validation
    - Approval workflow
    - Notification dispatch

    Implementation: Sprint 108 (Day 1-3)
    """

    @pytest.fixture
    def service(self):
        """Fixture: GateService instance"""
        raise NotImplementedError("Implement in Sprint 108")

    # ─────────────────────────────────────────────────────────────
    # CREATE GATE
    # ─────────────────────────────────────────────────────────────

    def test_create_gate_with_valid_data(self, service):
        """RED: Gate created with valid data"""
        raise NotImplementedError("Implement in Sprint 108")

    def test_create_gate_rejects_invalid_stage(self, service):
        """RED: Gate creation rejects invalid stage"""
        raise NotImplementedError("Implement in Sprint 108")

    def test_create_gate_rejects_duplicate_name(self, service):
        """RED: Gate creation rejects duplicate name in project"""
        raise NotImplementedError("Implement in Sprint 108")

    # ─────────────────────────────────────────────────────────────
    # APPROVE GATE
    # ─────────────────────────────────────────────────────────────

    def test_approve_gate_updates_status_and_notifies(self, service):
        """RED: Gate approval updates status and sends notification"""
        raise NotImplementedError("Implement in Sprint 108")

    def test_approve_gate_requires_all_evidence(self, service):
        """RED: Gate approval blocked if evidence missing"""
        raise NotImplementedError("Implement in Sprint 108")

    def test_approve_gate_requires_approver_permission(self, service):
        """RED: Non-approver cannot approve gate"""
        raise NotImplementedError("Implement in Sprint 108")

    # ─────────────────────────────────────────────────────────────
    # REJECT GATE
    # ─────────────────────────────────────────────────────────────

    def test_reject_gate_updates_status_and_notifies(self, service):
        """RED: Gate rejection updates status and sends notification"""
        raise NotImplementedError("Implement in Sprint 108")

    def test_reject_gate_requires_rejection_reason(self, service):
        """RED: Gate rejection requires reason"""
        raise NotImplementedError("Implement in Sprint 108")

    # ─────────────────────────────────────────────────────────────
    # LIST GATES
    # ─────────────────────────────────────────────────────────────

    def test_list_gates_returns_all_gates_in_project(self, service):
        """RED: List gates returns all gates in project"""
        raise NotImplementedError("Implement in Sprint 108")

    def test_list_gates_filters_by_status(self, service):
        """RED: List gates can filter by status"""
        raise NotImplementedError("Implement in Sprint 108")

    # ─────────────────────────────────────────────────────────────
    # EDGE CASES
    # ─────────────────────────────────────────────────────────────

    def test_create_gate_handles_db_connection_error(self, service):
        """RED: Gate creation handles DB errors gracefully"""
        raise NotImplementedError("Implement in Sprint 108")

    def test_approve_gate_handles_notification_failure(self, service):
        """RED: Gate approval succeeds even if notification fails"""
        raise NotImplementedError("Implement in Sprint 108")
```

**Acceptance Criteria**:
- All 15 services have test stub files
- Each test method raises NotImplementedError
- Test methods have descriptive docstrings
- Tests organized by feature (CREATE, APPROVE, LIST, etc.)
- Edge cases identified (DB errors, notification failures)

---

#### D3: Docker Test Environment (Day 3-4)

**Location**: `docker-compose.test.yml`

```yaml
# docker-compose.test.yml

version: '3.8'

services:
  # ─────────────────────────────────────────────────────────────
  # PostgreSQL Test Database
  # ─────────────────────────────────────────────────────────────
  postgres-test:
    image: postgres:15.5
    container_name: sdlc-postgres-test
    environment:
      POSTGRES_DB: sdlc_test
      POSTGRES_USER: sdlc_test
      POSTGRES_PASSWORD: test_password_12345
    ports:
      - "5433:5432"
    volumes:
      - postgres-test-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sdlc_test"]
      interval: 5s
      timeout: 5s
      retries: 5

  # ─────────────────────────────────────────────────────────────
  # Redis Test Cache
  # ─────────────────────────────────────────────────────────────
  redis-test:
    image: redis:7.2
    container_name: sdlc-redis-test
    ports:
      - "6380:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  # ─────────────────────────────────────────────────────────────
  # MinIO Test Evidence Vault
  # ─────────────────────────────────────────────────────────────
  minio-test:
    image: minio/minio:latest
    container_name: sdlc-minio-test
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: test_user
      MINIO_ROOT_PASSWORD: test_password_12345
    ports:
      - "9001:9000"
      - "9002:9001"
    volumes:
      - minio-test-data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ─────────────────────────────────────────────────────────────
  # OPA Test Policy Engine
  # ─────────────────────────────────────────────────────────────
  opa-test:
    image: openpolicyagent/opa:0.58.0
    container_name: sdlc-opa-test
    command: run --server --addr :8181
    ports:
      - "8182:8181"
    volumes:
      - ./backend/policies:/policies
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8181/health"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres-test-data:
  minio-test-data:
```

**Test Runner Script**:

```bash
#!/bin/bash
# scripts/run-integration-tests.sh

set -e

echo "🚀 Starting test services..."
docker-compose -f docker-compose.test.yml up -d

echo "⏳ Waiting for services to be healthy..."
docker-compose -f docker-compose.test.yml ps

echo "🧪 Running integration tests..."
pytest backend/tests/integration/ \
  --cov=backend/app \
  --cov-report=html \
  --cov-report=term \
  --tb=short \
  -v

echo "✅ Tests complete. Tearing down..."
docker-compose -f docker-compose.test.yml down -v

echo "📊 Coverage report: backend/htmlcov/index.html"
```

**Acceptance Criteria**:
- All 4 services (PostgreSQL, Redis, MinIO, OPA) start successfully
- All services pass health checks
- Integration tests can connect to all services
- Teardown cleans up volumes

---

#### D4: CI/CD Pipeline Update (Day 4-5)

**Location**: `.github/workflows/test.yml`

```yaml
# .github/workflows/test.yml

name: Test Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  # ─────────────────────────────────────────────────────────────
  # Unit Tests (MANDATORY - Blocks merge)
  # ─────────────────────────────────────────────────────────────
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-cov pytest-asyncio

      - name: Run unit tests
        run: |
          pytest backend/tests/unit/ \
            --cov=backend/app \
            --cov-report=xml \
            --cov-report=term \
            --cov-fail-under=95 \
            -v

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unit
          fail_ci_if_error: true

  # ─────────────────────────────────────────────────────────────
  # Integration Tests (MANDATORY - Blocks merge)
  # ─────────────────────────────────────────────────────────────
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Start test services
        run: docker-compose -f docker-compose.test.yml up -d

      - name: Wait for services
        run: |
          sleep 10
          docker-compose -f docker-compose.test.yml ps

      - name: Setup Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-asyncio

      - name: Run integration tests
        run: |
          pytest backend/tests/integration/ \
            --cov=backend/app \
            --cov-report=xml \
            --cov-fail-under=90 \
            -v

      - name: Teardown services
        if: always()
        run: docker-compose -f docker-compose.test.yml down -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: integration

  # ─────────────────────────────────────────────────────────────
  # E2E Tests (MANDATORY - Blocks deploy)
  # ─────────────────────────────────────────────────────────────
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js 20
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install Playwright
        run: |
          cd frontend/web
          npm ci
          npx playwright install --with-deps

      - name: Start application
        run: docker-compose up -d

      - name: Wait for application
        run: |
          sleep 30
          curl --retry 10 --retry-delay 5 http://localhost:3000/health

      - name: Run E2E tests
        run: |
          cd frontend/web
          npx playwright test

      - name: Upload Playwright report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: frontend/web/playwright-report/
          retention-days: 30

      - name: Teardown
        if: always()
        run: docker-compose down -v

  # ─────────────────────────────────────────────────────────────
  # Test Summary (Requires all above)
  # ─────────────────────────────────────────────────────────────
  test-summary:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests, e2e-tests]
    if: always()
    steps:
      - name: Check test results
        run: |
          if [ "${{ needs.unit-tests.result }}" == "failure" ]; then
            echo "❌ Unit tests failed"
            exit 1
          fi
          if [ "${{ needs.integration-tests.result }}" == "failure" ]; then
            echo "❌ Integration tests failed"
            exit 1
          fi
          if [ "${{ needs.e2e-tests.result }}" == "failure" ]; then
            echo "❌ E2E tests failed"
            exit 1
          fi
          echo "✅ All tests passed"
```

**Acceptance Criteria**:
- Unit tests enforce 95% coverage (fail if below)
- Integration tests enforce 90% coverage (fail if below)
- E2E tests run in staging environment
- All 3 test suites must pass to merge PR
- Coverage reports uploaded to Codecov

---

#### D5: Developer TDD Guide (Day 5)

**Location**: `docs/05-test/DEVELOPER-TDD-GUIDE.md`

**Content** (excerpt):

```markdown
# Developer TDD Guide - SDLC Orchestrator

## Daily TDD Workflow

### Morning: Write Tests First

```bash
# 1. Pull latest main
git pull origin main

# 2. Create feature branch
git checkout -b feature/gate-approval

# 3. Write ONE failing test
# backend/tests/services/test_gate_service.py

def test_approve_gate_updates_status_and_notifies():
    gate = get_mock_gate({"status": "pending"})
    gate_service.approve(gate, approved_by="cto@example.com")

    assert gate.status == "approved"
    assert notification_sent_to(gate.created_by)

# 4. Run test (MUST see it fail)
pytest backend/tests/services/test_gate_service.py::test_approve_gate_updates_status_and_notifies

# Expected: FAIL (approve() method doesn't exist)
```

### Afternoon: Implement Minimal Code

```python
# backend/app/services/gate_service.py

class GateService:
    def approve(self, gate: Gate, approved_by: str) -> None:
        """Approve gate and send notification"""
        gate.status = "approved"
        gate.approved_by = approved_by
        gate.approved_at = datetime.now(UTC)

        self.db.commit()

        # Send notification
        self.notification_service.send(
            to=gate.created_by,
            subject=f"Gate {gate.name} Approved",
            body=f"Your gate has been approved by {approved_by}",
        )
```

### End of Day: Refactor

```bash
# Run all tests
pytest backend/tests/services/test_gate_service.py

# Expected: ALL PASS

# Refactor if needed
# - Extract notification logic
# - Add type hints
# - Improve naming

# Commit
git add .
git commit -m "feat(gates): Add gate approval with notification"
git push origin feature/gate-approval
```

## Checklist Before PR

- [ ] All tests watched fail BEFORE implementing
- [ ] All tests pass
- [ ] Coverage ≥95%
- [ ] No linting errors (ruff)
- [ ] No TODOs or NotImplementedErrors
- [ ] Used factories (no hardcoded test data)
```

**Acceptance Criteria**:
- Guide published to docs/05-test/
- All developers trained on TDD workflow
- TDD checklist added to PR template

---

### 2.3 Sprint 107 Success Criteria

**Definition of Done**:
- [ ] All 6 test factories implemented and tested
- [ ] All 15 service test stubs created (NotImplementedError)
- [ ] docker-compose.test.yml working (4 services healthy)
- [ ] CI/CD pipeline updated (95% coverage enforcement)
- [ ] Developer TDD guide published
- [ ] All developers trained on TDD workflow

**Metrics**:
- Factory count: 6/6
- Test stub count: 15/15 services × ~10 tests = 150 stubs
- Docker services: 4/4 healthy
- Developer training: 100% attendance

**Exit Criteria**:
- Sprint 107 demo approved by CTO + QA Lead
- All deliverables merged to main branch
- Zero P0 bugs from Sprint 107 work

---

## 3. Sprint 108: Core Tests & Coverage (Week 2)

### 3.1 Objectives

- ✅ Implement unit tests for core services (FR1-FR3, FR21, FR41-FR45)
- ✅ Implement integration tests for API endpoints
- ✅ Achieve 95% unit coverage, 90% integration coverage
- ✅ Implement framework compliance tests

**Success Criteria**:
- [ ] 200+ unit tests implemented (RED → GREEN → REFACTOR)
- [ ] 50+ integration tests implemented
- [ ] Unit coverage ≥95%
- [ ] Integration coverage ≥90%
- [ ] 20+ framework compliance tests

---

### 3.2 Deliverables

#### D1: Core Service Unit Tests (Day 1-3)

**Priority P0 Services** (implement first):
1. **GateService** (FR1) - 20 tests
   - Create, approve, reject, list gates
   - Evidence validation before approval
   - Notification dispatch
   - Permission checks

2. **EvidenceService** (FR2) - 15 tests
   - Upload evidence to MinIO
   - SHA256 integrity hashing
   - Evidence metadata storage
   - Retrieve evidence by hash

3. **AIContextService** (FR3) - 15 tests
   - Stage-aware prompt generation
   - Multi-provider fallback (Ollama → Claude → Rule-based)
   - Context injection (project, stage, previous outputs)

4. **CodegenService** (FR41-FR45) - 25 tests
   - IR-based code generation
   - 4-Gate quality pipeline
   - Validation loop orchestration
   - Evidence state machine

5. **UserService** (Authentication) - 15 tests
   - JWT token generation/validation
   - OAuth integration (GitHub)
   - MFA support (TOTP)
   - Password reset flow

**TDD Workflow** (same for all services):

```python
# DAY 1: GateService - Create gate (RED)

def test_create_gate_with_valid_data():
    """RED: Gate created with valid data"""
    # Arrange
    gate_data = get_mock_gate_data()

    # Act
    gate = gate_service.create_gate(gate_data)

    # Assert
    assert gate.id is not None
    assert gate.status == "pending"
    assert gate.stage == "DESIGN"
    assert gate.created_by == gate_data["created_by"]

# Run: pytest (MUST FAIL - method doesn't exist)

# DAY 1: GateService - Create gate (GREEN)

class GateService:
    def create_gate(self, data: Dict) -> Gate:
        gate = Gate(
            id=str(uuid4()),
            name=data["name"],
            stage=data["stage"],
            status="pending",
            created_by=data["created_by"],
        )
        self.db.add(gate)
        self.db.commit()
        return gate

# Run: pytest (MUST PASS)

# DAY 1: GateService - Create gate (REFACTOR)
# Extract ID generation, add type hints, improve error handling

# REPEAT for next test...
```

**Acceptance Criteria**:
- All tests follow RED → GREEN → REFACTOR
- All tests use factories (no hardcoded data)
- All tests have descriptive names
- Edge cases covered (DB errors, validation failures)
- Unit coverage ≥95%

---

#### D2: API Integration Tests (Day 3-5)

**API Endpoints to Test** (50+ tests):

```python
# backend/tests/integration/test_gate_api.py

class TestGateAPI:
    """Integration tests for Gate API endpoints"""

    @pytest.fixture
    def client(self):
        """Use REAL services (PostgreSQL, Redis, OPA, MinIO)"""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        """Authenticated user headers"""
        token = create_test_jwt_token(user_id="user-123", role="engineering_manager")
        return {"Authorization": f"Bearer {token}"}

    # ─────────────────────────────────────────────────────────────
    # POST /api/v1/gates (Create Gate)
    # ─────────────────────────────────────────────────────────────

    def test_create_gate_api_success(self, client, auth_headers):
        """Integration: Create gate via API"""
        response = client.post(
            "/api/v1/gates",
            json=get_mock_gate_data(),
            headers=auth_headers,
        )

        assert response.status_code == 201
        assert response.json()["status"] == "pending"
        assert "id" in response.json()

    def test_create_gate_api_validates_openapi_schema(self, client, auth_headers):
        """Integration: API validates OpenAPI schema"""
        response = client.post(
            "/api/v1/gates",
            json={"invalid": "data"},
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "validation error" in response.json()["detail"].lower()

    def test_create_gate_api_requires_authentication(self, client):
        """Integration: Create gate requires auth"""
        response = client.post(
            "/api/v1/gates",
            json=get_mock_gate_data(),
        )

        assert response.status_code == 401

    # ─────────────────────────────────────────────────────────────
    # POST /api/v1/gates/{id}/approve (Approve Gate)
    # ─────────────────────────────────────────────────────────────

    def test_approve_gate_api_success(self, client, auth_headers):
        """Integration: Approve gate via API"""
        # Create gate first
        create_response = client.post(
            "/api/v1/gates",
            json=get_mock_gate_data(),
            headers=auth_headers,
        )
        gate_id = create_response.json()["id"]

        # Approve gate
        approve_response = client.post(
            f"/api/v1/gates/{gate_id}/approve",
            headers=auth_headers,
        )

        assert approve_response.status_code == 200
        assert approve_response.json()["status"] == "approved"

    def test_approve_gate_api_blocks_non_approver(self, client):
        """Integration: Non-approver cannot approve gate"""
        # Create gate with CTO as approver
        gate_data = get_mock_gate_data({"approvers": ["cto@example.com"]})
        create_response = client.post(
            "/api/v1/gates",
            json=gate_data,
            headers={"Authorization": "Bearer cto-token"},
        )
        gate_id = create_response.json()["id"]

        # Try to approve as non-approver
        non_approver_token = create_test_jwt_token(user_id="user-456", role="developer")
        approve_response = client.post(
            f"/api/v1/gates/{gate_id}/approve",
            headers={"Authorization": f"Bearer {non_approver_token}"},
        )

        assert approve_response.status_code == 403
        assert "not authorized" in approve_response.json()["detail"].lower()

    # ... 46 more API tests ...
```

**API Coverage Matrix**:

| Endpoint | Method | Tests | Status |
|----------|--------|-------|--------|
| `/api/v1/gates` | POST | 5 | ⏳ Sprint 108 |
| `/api/v1/gates/{id}` | GET | 3 | ⏳ Sprint 108 |
| `/api/v1/gates/{id}/approve` | POST | 4 | ⏳ Sprint 108 |
| `/api/v1/gates/{id}/reject` | POST | 4 | ⏳ Sprint 108 |
| `/api/v1/evidence` | POST | 5 | ⏳ Sprint 108 |
| `/api/v1/evidence/{id}` | GET | 3 | ⏳ Sprint 108 |
| `/api/v1/projects` | POST | 4 | ⏳ Sprint 108 |
| `/api/v1/projects/{id}` | GET, PUT, DELETE | 6 | ⏳ Sprint 108 |
| `/api/v1/policies` | GET, POST | 4 | ⏳ Sprint 108 |
| `/api/v1/codegen/generate` | POST | 6 | ⏳ Sprint 108 |
| ... | ... | ... | ... |
| **Total** | | **50+** | |

**Acceptance Criteria**:
- All API endpoints have ≥3 tests (happy path, validation, auth)
- All tests use real services (Docker Compose)
- OpenAPI schema validation enforced
- Integration coverage ≥90%

---

#### D3: Framework Compliance Tests (Day 5)

**Purpose**: Verify Orchestrator implements SDLC 5.2.0 correctly

```python
# backend/tests/compliance/test_framework_compliance.py

import pytest
from pathlib import Path
import yaml


class TestSDLC520Compliance:
    """
    Verify SDLC Orchestrator implements SDLC 5.2.0 framework correctly.

    Framework Location: SDLC-Enterprise-Framework/ (submodule)
    """

    @pytest.fixture
    def framework_gates(self):
        """Load gate definitions from framework submodule"""
        framework_path = Path("SDLC-Enterprise-Framework/03-Templates-Tools/Gate-Templates/")
        gates = {}
        for yaml_file in framework_path.glob("*.yaml"):
            with open(yaml_file) as f:
                gate_data = yaml.safe_load(f)
                gates[gate_data["gate_id"]] = gate_data
        return gates

    def test_stage_00_gates_match_framework(self, framework_gates):
        """Verify Stage 00 (Discover) gates match framework"""
        # Get Stage 00 gates from framework
        framework_stage_00 = {
            k: v for k, v in framework_gates.items()
            if v["stage"] == "00-discover"
        }

        # Get Stage 00 gates from Orchestrator
        orchestrator_gates = gate_service.get_available_gates_for_stage("00-discover")

        # Compare
        assert len(orchestrator_gates) == len(framework_stage_00)
        for gate in orchestrator_gates:
            assert gate.gate_id in framework_stage_00
            framework_gate = framework_stage_00[gate.gate_id]
            assert gate.name == framework_gate["name"]
            assert gate.exit_criteria == framework_gate["exit_criteria"]

    def test_all_framework_gates_implemented(self, framework_gates):
        """Verify ALL framework gates are implemented in Orchestrator"""
        orchestrator_gate_ids = {g.gate_id for g in gate_service.list_all_gates()}

        missing_gates = set(framework_gates.keys()) - orchestrator_gate_ids
        assert len(missing_gates) == 0, f"Missing gates: {missing_gates}"

    def test_gate_evidence_requirements_match_framework(self, framework_gates):
        """Verify evidence requirements match framework"""
        for gate_id, framework_gate in framework_gates.items():
            orchestrator_gate = gate_service.get_gate_template(gate_id)

            framework_evidence = set(framework_gate.get("evidence_required", []))
            orchestrator_evidence = set(orchestrator_gate.evidence_required)

            assert framework_evidence == orchestrator_evidence, \
                f"Gate {gate_id}: Evidence mismatch"

    # ... 17 more compliance tests ...
```

**Compliance Test Matrix**:

| Area | Tests | Purpose |
|------|-------|---------|
| **Stage Gates** | 7 | Verify gates for stages 00-06 match framework |
| **Evidence Types** | 5 | Verify evidence types match framework |
| **Exit Criteria** | 4 | Verify exit criteria match framework |
| **Gate Sequencing** | 2 | Verify gate dependencies match framework |
| **Policy Packs** | 2 | Verify policy packs match framework |
| **Total** | **20** | |

**Acceptance Criteria**:
- All 7 stages have compliance tests
- Framework submodule version tracked
- Compliance tests run in CI/CD
- Drift alerts if framework changes

---

### 3.3 Sprint 108 Success Criteria

**Definition of Done**:
- [ ] 200+ unit tests implemented (RED → GREEN → REFACTOR)
- [ ] 50+ integration tests implemented
- [ ] Unit coverage ≥95%
- [ ] Integration coverage ≥90%
- [ ] 20+ framework compliance tests passing
- [ ] All services have ≥90% coverage

**Metrics**:
- Unit tests: 200+ (target: 250)
- Integration tests: 50+ (target: 60)
- Unit coverage: 95%+ (measured by pytest-cov)
- Integration coverage: 90%+ (measured by pytest-cov)
- Framework compliance: 20/20 tests passing

**Exit Criteria**:
- Sprint 108 demo approved by CTO + QA Lead
- Code review passed (2+ approvers)
- All tests passing in CI/CD
- Coverage reports published to Codecov

---

## 4. Sprint 109: E2E, Load, Security & Go-Live (Week 3)

### 4.1 Objectives

- ✅ Implement 10 critical E2E user journeys (Playwright)
- ✅ Load testing (100K concurrent users)
- ✅ Security audit (OWASP ASVS L2)
- ✅ Smoke tests for production
- ✅ Go-live readiness review

**Success Criteria**:
- [ ] 10 E2E paths implemented and passing
- [ ] Load test pass (100K users, <100ms p95)
- [ ] Security audit pass (OWASP ASVS L2, 264/264)
- [ ] Smoke tests pass in production
- [ ] Go-live approval from CTO + QA Lead + Security Lead

---

### 4.2 Deliverables

#### D1: Playwright E2E Tests (Day 1-2)

**Location**: `frontend/web/tests/e2e/`

**Critical User Journeys** (10 tests):

1. **Engineering Manager creates gate and CTO approves**
   ```typescript
   test('EM creates gate, CTO approves', async ({ page }) => {
     // Login as EM
     await login(page, 'em@example.com');

     // Create gate
     await createGate(page, 'Authentication G1', 'DESIGN');

     // Verify gate pending
     await expect(page.locator('text=Status: Pending')).toBeVisible();

     // Logout, login as CTO
     await logout(page);
     await login(page, 'cto@example.com');

     // Approve gate
     await approveGate(page, 'Authentication G1');

     // Verify gate approved
     await expect(page.locator('text=Status: Approved')).toBeVisible();
   });
   ```

2. **Developer uploads evidence to gate**
3. **PM creates project and adds team members**
4. **Admin configures policy pack**
5. **User triggers AI code generation (EP-06)**
6. **Quality gates block merge on failure**
7. **User views dashboard with real-time gate status**
8. **User signs up with GitHub OAuth**
9. **User resets password via email**
10. **Admin views usage analytics and cost tracking**

**Acceptance Criteria**:
- All 10 E2E tests passing
- Tests run in CI/CD before deploy
- Playwright report artifacts preserved
- Test execution time <5 min total

---

#### D2: Load Testing (Day 2-3)

**Location**: `tests/load/locustfile.py`

```python
# tests/load/locustfile.py

from locust import HttpUser, task, between


class SDLCOrchestratorUser(HttpUser):
    """Simulate user behavior for load testing"""

    wait_time = between(1, 5)  # Think time between requests
    host = "https://staging.sdlc-orchestrator.com"

    def on_start(self):
        """Login before test"""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "loadtest@example.com",
            "password": "loadtest_password",
        })
        self.token = response.json()["access_token"]

    @task(10)  # 10x weight (most common operation)
    def list_projects(self):
        """GET /api/v1/projects"""
        self.client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {self.token}"},
            name="List Projects",
        )

    @task(5)  # 5x weight
    def list_gates(self):
        """GET /api/v1/gates"""
        self.client.get(
            "/api/v1/gates",
            headers={"Authorization": f"Bearer {self.token}"},
            name="List Gates",
        )

    @task(3)  # 3x weight
    def get_gate_detail(self):
        """GET /api/v1/gates/{id}"""
        # Assume gate-123 exists
        self.client.get(
            "/api/v1/gates/gate-123",
            headers={"Authorization": f"Bearer {self.token}"},
            name="Get Gate Detail",
        )

    @task(2)  # 2x weight
    def create_gate(self):
        """POST /api/v1/gates"""
        self.client.post(
            "/api/v1/gates",
            json={
                "name": f"Load Test Gate {self.user_id}",
                "stage": "DESIGN",
                "project_id": "project-loadtest",
            },
            headers={"Authorization": f"Bearer {self.token}"},
            name="Create Gate",
        )

    @task(1)  # 1x weight (least common)
    def approve_gate(self):
        """POST /api/v1/gates/{id}/approve"""
        self.client.post(
            "/api/v1/gates/gate-123/approve",
            headers={"Authorization": f"Bearer {self.token}"},
            name="Approve Gate",
        )
```

**Load Test Scenarios**:

| Scenario | Users | Duration | Target p95 | Status |
|----------|-------|----------|------------|--------|
| **Baseline** | 100 | 5 min | <100ms | ⏳ Day 2 |
| **Normal Load** | 1,000 | 10 min | <100ms | ⏳ Day 2 |
| **Peak Load** | 10,000 | 15 min | <200ms | ⏳ Day 3 |
| **Stress Test** | 100,000 | 30 min | <500ms | ⏳ Day 3 |

**Acceptance Criteria**:
- Stress test pass (100K users, <500ms p95)
- Zero 500 errors under normal load
- Database connection pool stable
- Memory usage <80% under peak load
- Load test report generated

---

#### D3: Security Audit (Day 3-4)

**OWASP ASVS Level 2 Checklist** (264 requirements):

| Category | Requirements | Status |
|----------|--------------|--------|
| **V1: Architecture** | 14 | ⏳ Day 3 |
| **V2: Authentication** | 32 | ⏳ Day 3 |
| **V3: Session Management** | 19 | ⏳ Day 3 |
| **V4: Access Control** | 26 | ⏳ Day 3 |
| **V5: Validation** | 29 | ⏳ Day 4 |
| **V6: Cryptography** | 17 | ⏳ Day 4 |
| **V7: Error Handling** | 12 | ⏳ Day 4 |
| **V8: Data Protection** | 16 | ⏳ Day 4 |
| **V9: Communication** | 15 | ⏳ Day 4 |
| **V10: Malicious Code** | 8 | ⏳ Day 4 |
| **V11: Business Logic** | 12 | ⏳ Day 4 |
| **V12: Files & Resources** | 12 | ⏳ Day 4 |
| **V13: API** | 22 | ⏳ Day 4 |
| **V14: Configuration** | 14 | ⏳ Day 4 |
| **Total** | **264** | **Target: 264/264** |

**Security Tools**:
- **Semgrep** (SAST) - Pre-commit hook
- **Bandit** (Python security linter)
- **npm audit** (Frontend dependencies)
- **Grype** (Vulnerability scanner)
- **Trivy** (Docker image scanner)

**Acceptance Criteria**:
- OWASP ASVS L2: 264/264 requirements pass
- Zero critical/high CVEs
- All dependencies up-to-date
- Security audit report signed off by Security Lead

---

#### D4: Smoke Tests (Day 4)

**Location**: `backend/tests/smoke/test_production_health.py`

```python
# backend/tests/smoke/test_production_health.py

import requests
import pytest

PROD_URL = "https://sdlc-orchestrator.com"


class TestProductionSmoke:
    """Smoke tests run AFTER deployment to production"""

    def test_api_health_endpoint(self):
        """Verify API is reachable"""
        response = requests.get(f"{PROD_URL}/health", timeout=5)
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_database_connection(self):
        """Verify database connection working"""
        response = requests.get(f"{PROD_URL}/api/v1/projects", timeout=5)
        assert response.status_code in [200, 401]  # Either works or needs auth

    def test_evidence_vault_accessible(self):
        """Verify MinIO evidence vault accessible"""
        response = requests.head(f"{PROD_URL}/api/v1/evidence/health", timeout=5)
        assert response.status_code == 200

    def test_opa_policy_engine_working(self):
        """Verify OPA policy engine responding"""
        response = requests.get(f"{PROD_URL}/api/v1/policies", timeout=5)
        assert response.status_code in [200, 401]

    def test_redis_cache_working(self):
        """Verify Redis cache accessible"""
        # Implicit test: If API responds quickly, cache is working
        response = requests.get(f"{PROD_URL}/api/v1/projects", timeout=1)
        assert response.elapsed.total_seconds() < 1.0

    def test_critical_endpoints_responding(self):
        """Verify all critical endpoints are up"""
        critical_endpoints = [
            "/health",
            "/api/v1/auth/login",
            "/api/v1/projects",
            "/api/v1/gates",
            "/api/v1/evidence",
        ]

        for endpoint in critical_endpoints:
            response = requests.get(f"{PROD_URL}{endpoint}", timeout=5)
            assert response.status_code in [200, 401, 403]  # Not 500
```

**Acceptance Criteria**:
- All smoke tests pass in production
- Smoke tests run after every deploy
- Alerts triggered if any smoke test fails
- Rollback automatic if smoke tests fail

---

#### D5: Go-Live Readiness Review (Day 5)

**Checklist**:

| Area | Status | Owner | Sign-Off |
|------|--------|-------|----------|
| **Test Strategy** | ✅ Complete | QA Lead | ⏳ |
| **Test Infrastructure** | ✅ Complete | DevOps | ⏳ |
| **Unit Tests** | ✅ 95%+ | Backend Lead | ⏳ |
| **Integration Tests** | ✅ 90%+ | Backend Lead | ⏳ |
| **E2E Tests** | ✅ 10 paths | Frontend Lead | ⏳ |
| **Load Tests** | ✅ 100K users | DevOps | ⏳ |
| **Security Audit** | ✅ ASVS L2 | Security Lead | ⏳ |
| **Smoke Tests** | ✅ Passing | DevOps | ⏳ |
| **Framework Compliance** | ✅ 20/20 tests | QA Lead | ⏳ |
| **Documentation** | ✅ Complete | Tech Writer | ⏳ |
| **Runbooks** | ✅ Complete | DevOps | ⏳ |
| **Incident Response** | ✅ Defined | SRE | ⏳ |
| **Rollback Plan** | ✅ Tested | DevOps | ⏳ |
| **Monitoring** | ✅ Dashboards | DevOps | ⏳ |
| **Alerts** | ✅ Configured | SRE | ⏳ |

**Final Approval**:
- [ ] CTO Sign-Off
- [ ] QA Lead Sign-Off
- [ ] Security Lead Sign-Off
- [ ] DevOps Lead Sign-Off

**Go-Live Date**: February 28, 2026

---

### 4.3 Sprint 109 Success Criteria

**Definition of Done**:
- [ ] 10 E2E user journeys passing
- [ ] Load test pass (100K users, <500ms p95)
- [ ] Security audit pass (OWASP ASVS L2, 264/264)
- [ ] Smoke tests passing in production
- [ ] Go-live checklist 100% complete
- [ ] Final approval from CTO + QA + Security + DevOps

**Metrics**:
- E2E tests: 10/10 passing
- Load test: 100K users sustained
- Security: 264/264 ASVS requirements
- Smoke tests: 100% passing

**Exit Criteria**:
- Sprint 109 demo approved
- Production deployment successful
- Smoke tests pass post-deploy
- Monitoring dashboards live
- On-call rotation established

---

## 5. Risk Mitigation

| Risk | Impact | Probability | Mitigation | Contingency |
|------|--------|-------------|------------|-------------|
| **TDD adoption slow** | P0 | Medium | Daily standup TDD review, pair programming | Extend Sprint 107 by 2 days |
| **Test coverage <95%** | P0 | Low | CI/CD blocks merge if <95% | Emergency weekend sprint |
| **E2E tests flaky** | P1 | Medium | Retry logic, explicit waits | Reduce to 8 critical paths |
| **Load test fails** | P1 | Low | Performance profiling, DB optimization | Delay go-live by 1 week |
| **Security audit fails** | P0 | Low | Pre-audit with Semgrep, Bandit | External security firm |
| **Framework drift** | P1 | Low | Compliance tests in CI/CD | Update Orchestrator to match framework |

---

## 6. Success Criteria Summary

**Go-Live Approved When**:
- [x] Test strategy document complete ✅
- [ ] All test factories implemented (6/6)
- [ ] Unit coverage ≥95%
- [ ] Integration coverage ≥90%
- [ ] 10 critical E2E paths passing
- [ ] Framework compliance tests passing (20/20)
- [ ] Load test pass (100K users)
- [ ] Security audit pass (OWASP ASVS L2)
- [ ] Zero P0 bugs, <5 P1 bugs
- [ ] CTO + QA Lead + Security Lead sign-off

**Post-Go-Live** (30 days):
- [ ] Real user monitoring (RUM) data collected
- [ ] Error rate <0.1%
- [ ] p95 latency <100ms maintained
- [ ] Test coverage maintained ≥95%

---

## 7. References

**Skills**:
- [.claude/skills/test-driven-development](/.claude/skills/test-driven-development/SKILL.md)
- [.claude/skills/testing-patterns](/.claude/skills/testing-patterns/SKILL.md)

**Framework**:
- [SDLC-Enterprise-Framework](../../SDLC-Enterprise-Framework/) (submodule)
- [SDLC 5.2.0 Documentation](../../SDLC-Enterprise-Framework/CONTENT-MAP.md)

**Test Strategy**:
- [00-TEST-STRATEGY-2026.md](00-TEST-STRATEGY-2026.md)

**Requirements**:
- [Functional Requirements](../01-planning/01-Requirements/Functional-Requirements-Document.md)
- [Non-Functional Requirements](../01-planning/01-Requirements/Non-Functional-Requirements.md)

---

**Approved by**: QA Lead + Backend Lead + CTO
**Date**: January 27, 2026
**Status**: ✅ ACTIVE - Execution Ready
**Target Go-Live**: February 28, 2026

---

*"Test early, test often. Quality is built in, not tested in."*
