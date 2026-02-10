# Testing Strategy - Governance System v2.0
## SPEC-0001 & SPEC-0002 Implementation Quality Assurance

**Version**: 2.0.0
**Status**: APPROVED
**Owner**: QA Lead + Tech Lead
**Created**: 2026-01-28
**Sprint**: 118 Track 2 - D4
**Related Specs**: SPEC-0001 (Anti-Vibecoding), SPEC-0002 (Specification Standard)
**Framework**: SDLC 6.0.0

---

## 📋 Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Coverage Goals](#test-coverage-goals)
3. [Unit Testing Strategy](#unit-testing-strategy)
4. [Integration Testing Strategy](#integration-testing-strategy)
5. [End-to-End Testing Strategy](#end-to-end-testing-strategy)
6. [Performance Testing Strategy](#performance-testing-strategy)
7. [Security Testing Strategy](#security-testing-strategy)
8. [Load Testing Strategy](#load-testing-strategy)
9. [Test Data Management](#test-data-management)
10. [CI/CD Integration](#cicd-integration)
11. [Test Metrics & Reporting](#test-metrics--reporting)
12. [Test Environment Strategy](#test-environment-strategy)

---

## 1. Testing Philosophy

### 1.1 Zero Mock Policy (NQH-Bot Lesson Applied)

```yaml
Principle: Test Real Integrations, Not Mocks

Background:
  NQH-Bot Crisis (2024):
    - 679 mock implementations
    - 78% failure rate in production
    - Root Cause: Mocks hid integration issues

SDLC Orchestrator Policy:
  ✅ REQUIRED:
    - Real PostgreSQL (Docker container)
    - Real Redis (Docker container)
    - Real OPA (Docker container with policies)
    - Real MinIO (Docker container with buckets)

  ❌ BANNED:
    - Mock databases (sqlite in-memory)
    - Mock cache (dict-based)
    - Mock policy engine
    - Mock object storage

  ⚠️ EXCEPTION (Only When Necessary):
    - External HTTP calls (GitHub API, Slack webhooks)
    - Time-dependent operations (freeze_time allowed)
    - Randomness (seed for deterministic tests)

Enforcement:
  - Pre-commit hook: Detect "mock" keywords in test files
  - Code review: Reject PRs with excessive mocking
  - CI/CD: Run tests against real services in Docker Compose
```

### 1.2 Test Pyramid Strategy

```
                    /\
                   /  \
                  / E2E \ ────────── 10% (10 critical user journeys)
                 /______\
                /        \
               / INTEGR.  \ ───────── 30% (API + DB + OPA + MinIO)
              /____________\
             /              \
            /      UNIT      \ ────── 60% (Business logic, validation)
           /________________\

Total Test Count: ~500 tests
Execution Time: <5 minutes (unit), <10 minutes (integration), <20 minutes (E2E)
```

**Rationale**:
- **Unit (60%)**: Fast feedback, isolate business logic bugs
- **Integration (30%)**: Contract validation, real service interaction
- **E2E (10%)**: Critical user journeys, production-like environment

### 1.3 Quality Gates

```yaml
Pre-commit (Local):
  ✅ Unit tests pass (exit code 0)
  ✅ Linting pass (ruff, mypy, eslint)
  ✅ Code formatting (ruff format, prettier)
  ⏱️ Execution Time: <30 seconds

CI/CD (Pull Request):
  ✅ Unit tests pass (95%+ coverage)
  ✅ Integration tests pass
  ✅ Security scan pass (Semgrep, Trivy)
  ✅ License scan pass (no AGPL imports)
  ✅ Performance benchmarks (<100ms p95 API latency)
  ⏱️ Execution Time: <5 minutes

Merge to Main:
  ✅ All CI/CD checks pass
  ✅ E2E tests pass (critical user journeys)
  ✅ Load tests pass (100 concurrent users)
  ✅ Code review approved (2+ reviewers)
  ⏱️ Execution Time: <20 minutes

Production Deployment:
  ✅ Smoke tests pass (staging environment)
  ✅ Database migration dry-run successful
  ✅ Rollback procedure validated
  ✅ CTO approval
  ⏱️ Execution Time: <10 minutes
```

---

## 2. Test Coverage Goals

### 2.1 Coverage Targets

```yaml
Overall Coverage (95% minimum):
  Backend:
    - Unit: 95%+ (statement coverage)
    - Integration: 90%+ (API endpoint coverage)
    - Total: 95%+ (combined)

  Frontend:
    - Unit: 90%+ (component coverage)
    - Integration: 85%+ (API integration coverage)
    - Total: 88%+ (combined)

Critical Components (100% mandatory):
  ✅ Vibecoding Index Calculation (5 signals)
  ✅ Progressive Routing Logic (4 zones)
  ✅ Kill Switch Triggers (3 triggers)
  ✅ Specification Validation (YAML frontmatter)
  ✅ Authentication & Authorization (RBAC)

Non-Critical Components (80% acceptable):
  - Dashboard UI components
  - Utility functions
  - Configuration loaders
```

### 2.2 Coverage by Module

```yaml
Backend Modules:

  app/services/vibecoding_service.py:
    Target: 100% (critical business logic)
    Tests:
      - test_calculate_index_green_zone (score < 20)
      - test_calculate_index_yellow_zone (score 20-40)
      - test_calculate_index_orange_zone (score 40-60)
      - test_calculate_index_red_zone (score >= 60)
      - test_calculate_index_5_signal_weights
      - test_progressive_routing_decision
      - test_kill_switch_trigger_rejection_rate
      - test_kill_switch_trigger_latency
      - test_kill_switch_trigger_security_cves

  app/services/specification_service.py:
    Target: 100% (critical validation)
    Tests:
      - test_validate_yaml_frontmatter_valid
      - test_validate_yaml_frontmatter_missing_required_fields
      - test_validate_yaml_frontmatter_invalid_spec_id_format
      - test_validate_yaml_frontmatter_invalid_tier
      - test_validate_functional_requirements_bdd_format
      - test_validate_acceptance_criteria_testable
      - test_get_tier_specific_requirements

  app/api/v1/governance.py:
    Target: 95% (API endpoints)
    Tests:
      - test_validate_spec_endpoint_200
      - test_validate_spec_endpoint_422_invalid_yaml
      - test_get_spec_metadata_200
      - test_get_spec_metadata_404
      - test_calculate_vibecoding_index_200
      - test_calculate_vibecoding_index_401_unauthorized
      - test_progressive_routing_decision_200
      - test_kill_switch_check_200
      - test_rate_limiting_429

  app/models/governance.py:
    Target: 90% (database models)
    Tests:
      - test_specification_model_create
      - test_specification_model_relationships
      - test_vibecoding_signal_model_jsonb_query
      - test_kill_switch_event_model_trigger

Frontend Modules:

  src/features/governance/VibecodingIndexCard.tsx:
    Target: 90% (UI component)
    Tests:
      - test_renders_green_zone_correctly
      - test_renders_yellow_zone_correctly
      - test_renders_orange_zone_correctly
      - test_renders_red_zone_correctly
      - test_displays_5_signal_breakdown
      - test_loading_state
      - test_error_state

  src/features/governance/SpecificationValidator.tsx:
    Target: 90% (validation UI)
    Tests:
      - test_validates_spec_on_submit
      - test_displays_validation_errors
      - test_displays_success_message
      - test_form_validation

  src/services/governanceApi.ts:
    Target: 95% (API integration)
    Tests:
      - test_calculate_vibecoding_index_api_call
      - test_validate_spec_api_call
      - test_error_handling_401
      - test_error_handling_500
```

---

## 3. Unit Testing Strategy

### 3.1 Backend Unit Tests (pytest)

**Framework**: pytest 7.4.0+ + pytest-asyncio

**Test Structure**:
```python
# tests/unit/services/test_vibecoding_service.py
import pytest
from datetime import datetime, timedelta
from app.services.vibecoding_service import VibecodingService
from app.models.governance import VibecodingSignal

@pytest.mark.asyncio
class TestVibecodingService:
    """Unit tests for VibecodingService"""

    async def test_calculate_index_green_zone(self, db_session, sample_submission):
        """
        GIVEN: A code submission with high quality signals
        WHEN: Vibecoding index is calculated
        THEN: Score should be < 20 (GREEN zone) and routing should be AUTO_MERGE
        """
        # Arrange
        service = VibecodingService(db_session)
        submission = sample_submission(
            intent_clarity=90,      # High quality
            code_ownership=85,
            context_completeness=95,
            ai_attestation=True,
            rejection_rate=0.05     # 5% rejection (low)
        )

        # Act
        result = await service.calculate_index(submission_id=submission.id)

        # Assert
        assert result.score < 20, f"Expected GREEN zone (<20), got {result.score}"
        assert result.routing == "AUTO_MERGE"
        assert result.zone == "GREEN"

        # Verify signal breakdown
        assert result.signals["intent_clarity"] == 90
        assert result.signals["code_ownership"] == 85
        assert result.signals["context_completeness"] == 95
        assert result.signals["ai_attestation"] is True
        assert result.signals["rejection_rate"] == 0.05

    async def test_calculate_index_5_signal_weights(self, db_session):
        """
        GIVEN: Known signal values
        WHEN: Vibecoding index is calculated
        THEN: Score should match expected weighted calculation

        Formula:
          score = (100 - intent_clarity) * 0.30 +
                  (100 - code_ownership) * 0.25 +
                  (100 - context_completeness) * 0.20 +
                  (0 if ai_attestation else 100) * 0.15 +
                  (rejection_rate * 100) * 0.10
        """
        # Arrange
        service = VibecodingService(db_session)

        # Known values: intent=80, ownership=70, context=90, attestation=True, rejection=0.10
        # Expected score:
        #   (100-80)*0.30 = 20*0.30 = 6.0
        #   (100-70)*0.25 = 30*0.25 = 7.5
        #   (100-90)*0.20 = 10*0.20 = 2.0
        #   (0)*0.15 = 0
        #   (10)*0.10 = 1.0
        #   Total: 6.0 + 7.5 + 2.0 + 0 + 1.0 = 16.5
        expected_score = 16.5

        # Act
        result = await service.calculate_index(
            intent_clarity=80,
            code_ownership=70,
            context_completeness=90,
            ai_attestation=True,
            rejection_rate=0.10
        )

        # Assert
        assert result.score == pytest.approx(expected_score, rel=1e-2), \
            f"Expected {expected_score}, got {result.score}"

    async def test_kill_switch_trigger_rejection_rate(self, db_session):
        """
        GIVEN: Rejection rate > 80% for 30 minutes
        WHEN: Kill switch is checked
        THEN: Kill switch should trigger and disable AI codegen
        """
        # Arrange
        service = VibecodingService(db_session)
        project_id = "PRJ-000001"

        # Simulate 30 minutes of high rejection rate (> 80%)
        now = datetime.utcnow()
        for i in range(30):
            timestamp = now - timedelta(minutes=i)
            await service.record_rejection(
                project_id=project_id,
                submission_id=f"SUB-{i:06d}",
                reason="Failed validation",
                timestamp=timestamp
            )

        # Act
        result = await service.check_kill_switch(project_id=project_id)

        # Assert
        assert result.triggered is True
        assert result.trigger_type == "rejection_rate"
        assert result.threshold == "80%"
        assert result.duration == "30 minutes"
        assert result.action == "Disable AI codegen for 24h"
        assert result.severity == "HIGH"

    async def test_progressive_routing_decision(self, db_session):
        """
        GIVEN: Vibecoding index scores in different zones
        WHEN: Routing decision is made
        THEN: Correct routing action should be assigned
        """
        service = VibecodingService(db_session)

        # Test cases: (score, expected_zone, expected_routing)
        test_cases = [
            (15, "GREEN", "AUTO_MERGE"),
            (25, "YELLOW", "HUMAN_REVIEW_REQUIRED"),
            (45, "ORANGE", "SENIOR_REVIEW_REQUIRED"),
            (75, "RED", "BLOCK_OR_COUNCIL"),
        ]

        for score, expected_zone, expected_routing in test_cases:
            # Act
            result = await service.determine_routing(score=score)

            # Assert
            assert result.zone == expected_zone, \
                f"Score {score}: Expected zone {expected_zone}, got {result.zone}"
            assert result.routing == expected_routing, \
                f"Score {score}: Expected routing {expected_routing}, got {result.routing}"
```

**Test Fixtures** (conftest.py):
```python
# tests/conftest.py
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.governance import Specification, VibecodingSignal

@pytest.fixture(scope="session")
async def db_engine():
    """Create test database engine"""
    engine = create_async_engine(
        "postgresql+asyncpg://test:test@localhost:5432/sdlc_test",
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(db_engine):
    """Create test database session"""
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
def sample_specification():
    """Factory for creating test specifications"""
    def _create_spec(**kwargs):
        return Specification(
            spec_id=kwargs.get("spec_id", "SPEC-0001"),
            title=kwargs.get("title", "Test Specification"),
            version=kwargs.get("version", "1.0.0"),
            status=kwargs.get("status", "DRAFT"),
            tier=kwargs.get("tier", ["PROFESSIONAL", "ENTERPRISE"]),
            pillar=kwargs.get("pillar", 2),
            owner=kwargs.get("owner", "QA Lead"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    return _create_spec

@pytest.fixture
def sample_submission(db_session):
    """Factory for creating test code submissions"""
    async def _create_submission(**kwargs):
        submission = VibecodingSignal(
            submission_id=kwargs.get("submission_id", "SUB-000001"),
            project_id=kwargs.get("project_id", "PRJ-000001"),
            intent_clarity=kwargs.get("intent_clarity", 80),
            code_ownership=kwargs.get("code_ownership", 75),
            context_completeness=kwargs.get("context_completeness", 85),
            ai_attestation=kwargs.get("ai_attestation", True),
            rejection_rate=kwargs.get("rejection_rate", 0.10),
            created_at=datetime.utcnow(),
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)
        return submission
    return _create_submission
```

### 3.2 Frontend Unit Tests (Vitest)

**Framework**: Vitest 1.1.0+ + React Testing Library

**Test Structure**:
```typescript
// tests/unit/features/governance/VibecodingIndexCard.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { VibecodingIndexCard } from '@/features/governance/VibecodingIndexCard'

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('VibecodingIndexCard', () => {
  it('renders green zone correctly', async () => {
    // Arrange
    const mockData = {
      submission_id: 'SUB-000001',
      score: 15,
      zone: 'GREEN',
      routing: 'AUTO_MERGE',
      signals: {
        intent_clarity: 90,
        code_ownership: 85,
        context_completeness: 95,
        ai_attestation: true,
        rejection_rate: 0.05,
      },
    }

    vi.mock('@/services/governanceApi', () => ({
      useVibecodingIndex: () => ({
        data: mockData,
        isLoading: false,
        error: null,
      }),
    }))

    // Act
    render(<VibecodingIndexCard submissionId="SUB-000001" />, {
      wrapper: createWrapper(),
    })

    // Assert
    await waitFor(() => {
      expect(screen.getByText('GREEN')).toBeInTheDocument()
      expect(screen.getByText('15')).toBeInTheDocument()
      expect(screen.getByText('AUTO_MERGE')).toBeInTheDocument()
      expect(screen.getByText(/Intent Clarity: 90/i)).toBeInTheDocument()
    })
  })

  it('renders red zone with correct styling', async () => {
    // Arrange
    const mockData = {
      score: 75,
      zone: 'RED',
      routing: 'BLOCK_OR_COUNCIL',
    }

    // Act
    render(<VibecodingIndexCard submissionId="SUB-000002" />)

    // Assert
    const zoneBadge = await screen.findByText('RED')
    expect(zoneBadge).toHaveClass('bg-red-100', 'text-red-800')
  })

  it('displays loading state', () => {
    // Arrange
    vi.mock('@/services/governanceApi', () => ({
      useVibecodingIndex: () => ({
        data: null,
        isLoading: true,
        error: null,
      }),
    }))

    // Act
    render(<VibecodingIndexCard submissionId="SUB-000001" />)

    // Assert
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
  })

  it('displays error state', async () => {
    // Arrange
    const mockError = new Error('Failed to fetch vibecoding index')

    vi.mock('@/services/governanceApi', () => ({
      useVibecodingIndex: () => ({
        data: null,
        isLoading: false,
        error: mockError,
      }),
    }))

    // Act
    render(<VibecodingIndexCard submissionId="SUB-000001" />)

    // Assert
    await waitFor(() => {
      expect(screen.getByText(/Failed to fetch/i)).toBeInTheDocument()
    })
  })
})
```

**Coverage Report Configuration**:
```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './tests/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'tests/',
        '**/*.config.*',
        '**/*.d.ts',
      ],
      thresholds: {
        lines: 90,
        functions: 90,
        branches: 85,
        statements: 90,
      },
    },
  },
})
```

---

## 4. Integration Testing Strategy

### 4.1 API Integration Tests

**Framework**: pytest + httpx (async HTTP client)

**Test Structure**:
```python
# tests/integration/api/test_governance_api.py
import pytest
import httpx
from datetime import datetime

@pytest.mark.integration
@pytest.mark.asyncio
class TestGovernanceAPI:
    """Integration tests for Governance API endpoints"""

    base_url = "http://localhost:8000"

    async def test_validate_spec_endpoint_valid_yaml(self, auth_token):
        """
        GIVEN: Valid YAML frontmatter
        WHEN: POST /api/v1/governance/specs/validate
        THEN: 200 OK with validation results
        """
        # Arrange
        valid_yaml = """
spec_id: SPEC-0001
title: Anti-Vibecoding Quality Assurance System
version: 1.0.0
status: APPROVED
tier: [PROFESSIONAL, ENTERPRISE]
pillar: 2
owner: QA Lead
last_updated: 2026-01-28
        """.strip()

        # Act
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/governance/specs/validate",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={"yaml_content": valid_yaml}
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["spec_id"] == "SPEC-0001"
        assert data["tier"] == ["PROFESSIONAL", "ENTERPRISE"]
        assert len(data["errors"]) == 0

    async def test_validate_spec_endpoint_missing_required_field(self, auth_token):
        """
        GIVEN: YAML frontmatter missing 'tier' field
        WHEN: POST /api/v1/governance/specs/validate
        THEN: 422 Unprocessable Entity with validation errors
        """
        # Arrange
        invalid_yaml = """
spec_id: SPEC-0001
title: Test Spec
version: 1.0.0
status: DRAFT
        """.strip()

        # Act
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/governance/specs/validate",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={"yaml_content": invalid_yaml}
            )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0
        assert any("tier" in error["field"] for error in data["errors"])

    async def test_calculate_vibecoding_index_integration(
        self, auth_token, db_session, sample_submission
    ):
        """
        GIVEN: Code submission with known signal values
        WHEN: POST /api/v1/governance/vibecoding/calculate
        THEN: 200 OK with calculated index and routing decision
        """
        # Arrange
        submission = await sample_submission(
            submission_id="SUB-999999",
            intent_clarity=80,
            code_ownership=70,
            context_completeness=90,
            ai_attestation=True,
            rejection_rate=0.10
        )

        request_data = {
            "submission_id": submission.submission_id,
            "project_id": submission.project_id,
            "tier": "PROFESSIONAL"
        }

        # Act
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/governance/vibecoding/calculate",
                headers={"Authorization": f"Bearer {auth_token}"},
                json=request_data,
                timeout=5.0
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["submission_id"] == "SUB-999999"
        assert "score" in data
        assert data["score"] == pytest.approx(16.5, rel=1e-2)
        assert data["zone"] == "GREEN"
        assert data["routing"] == "AUTO_MERGE"
        assert "signals" in data
        assert data["signals"]["intent_clarity"] == 80

    async def test_rate_limiting(self, auth_token):
        """
        GIVEN: Rate limit of 100 req/min
        WHEN: 101 requests made within 1 minute
        THEN: 429 Too Many Requests on 101st request
        """
        # Arrange
        endpoint = f"{self.base_url}/api/v1/governance/specs/SPEC-0001"

        # Act: Make 101 requests
        async with httpx.AsyncClient() as client:
            responses = []
            for i in range(101):
                response = await client.get(
                    endpoint,
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                responses.append(response.status_code)

        # Assert
        assert responses[:100] == [200] * 100  # First 100 succeed
        assert responses[100] == 429  # 101st fails with rate limit

    async def test_kill_switch_check_integration(self, auth_token, db_session):
        """
        GIVEN: Project with recent high rejection rate
        WHEN: POST /api/v1/governance/vibecoding/kill-switch/check
        THEN: 200 OK with kill switch status (triggered or not)
        """
        # Arrange
        project_id = "PRJ-000001"

        # Simulate high rejection rate (> 80% for 30 minutes)
        from datetime import datetime, timedelta
        from app.services.vibecoding_service import VibecodingService

        service = VibecodingService(db_session)
        now = datetime.utcnow()
        for i in range(30):
            await service.record_rejection(
                project_id=project_id,
                submission_id=f"SUB-{i:06d}",
                reason="Failed validation",
                timestamp=now - timedelta(minutes=i)
            )

        # Act
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/governance/vibecoding/kill-switch/check",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={"project_id": project_id}
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["triggered"] is True
        assert data["trigger_type"] == "rejection_rate"
        assert data["action"] == "Disable AI codegen for 24h"
        assert data["severity"] == "HIGH"
```

### 4.2 Database Integration Tests

**Test Structure**:
```python
# tests/integration/database/test_governance_models.py
import pytest
from datetime import datetime
from sqlalchemy import select
from app.models.governance import Specification, VibecodingSignal, KillSwitchEvent

@pytest.mark.integration
@pytest.mark.asyncio
class TestGovernanceModels:
    """Integration tests for database models and queries"""

    async def test_specification_creation_and_retrieval(self, db_session):
        """
        GIVEN: New specification data
        WHEN: Specification is created and committed
        THEN: Specification should be retrievable with correct values
        """
        # Arrange
        spec_data = {
            "spec_id": "SPEC-9999",
            "title": "Integration Test Spec",
            "version": "1.0.0",
            "status": "DRAFT",
            "tier": ["PROFESSIONAL", "ENTERPRISE"],
            "pillar": 2,
            "owner": "Test Owner",
            "frontmatter_metadata": {
                "tags": ["testing", "integration"],
                "dependencies": ["SPEC-0001", "SPEC-0002"]
            }
        }

        # Act
        spec = Specification(**spec_data)
        db_session.add(spec)
        await db_session.commit()
        await db_session.refresh(spec)

        # Retrieve
        result = await db_session.execute(
            select(Specification).where(Specification.spec_id == "SPEC-9999")
        )
        retrieved_spec = result.scalar_one()

        # Assert
        assert retrieved_spec.spec_id == "SPEC-9999"
        assert retrieved_spec.title == "Integration Test Spec"
        assert retrieved_spec.tier == ["PROFESSIONAL", "ENTERPRISE"]
        assert retrieved_spec.frontmatter_metadata["tags"] == ["testing", "integration"]

    async def test_vibecoding_signal_jsonb_query(self, db_session):
        """
        GIVEN: Multiple vibecoding signals with different metadata
        WHEN: JSONB query is executed to filter by signal values
        THEN: Correct signals should be returned
        """
        # Arrange: Create signals with different intent_clarity values
        signals = [
            VibecodingSignal(
                submission_id=f"SUB-{i:06d}",
                project_id="PRJ-000001",
                intent_clarity=i * 10,
                code_ownership=75,
                context_completeness=85,
                ai_attestation=True,
                rejection_rate=0.05,
                signal_metadata={"intent_score": i * 10}
            )
            for i in range(1, 11)  # intent_clarity: 10, 20, 30, ..., 100
        ]
        db_session.add_all(signals)
        await db_session.commit()

        # Act: Query signals with intent_clarity > 50
        result = await db_session.execute(
            select(VibecodingSignal)
            .where(VibecodingSignal.intent_clarity > 50)
            .order_by(VibecodingSignal.intent_clarity)
        )
        high_intent_signals = result.scalars().all()

        # Assert
        assert len(high_intent_signals) == 5  # 60, 70, 80, 90, 100
        assert high_intent_signals[0].intent_clarity == 60
        assert high_intent_signals[-1].intent_clarity == 100

    async def test_kill_switch_event_trigger(self, db_session):
        """
        GIVEN: Kill switch trigger criteria met
        WHEN: Kill switch event is recorded
        THEN: Event should be stored with correct status and metadata
        """
        # Arrange
        event_data = {
            "project_id": "PRJ-000001",
            "trigger_type": "rejection_rate",
            "threshold": "80%",
            "actual_value": "85%",
            "duration": "30 minutes",
            "action": "Disable AI codegen for 24h",
            "severity": "HIGH",
            "triggered_by": "system",
            "metadata": {
                "rejection_count": 85,
                "total_submissions": 100,
                "time_window": "30m"
            }
        }

        # Act
        event = KillSwitchEvent(**event_data)
        db_session.add(event)
        await db_session.commit()
        await db_session.refresh(event)

        # Assert
        assert event.project_id == "PRJ-000001"
        assert event.trigger_type == "rejection_rate"
        assert event.severity == "HIGH"
        assert event.metadata["rejection_count"] == 85
        assert event.triggered_at is not None

    async def test_foreign_key_relationships(self, db_session, sample_specification):
        """
        GIVEN: Specification with related functional requirements
        WHEN: Relationships are accessed
        THEN: Related data should be loaded correctly
        """
        # Arrange
        spec = sample_specification(spec_id="SPEC-0001")
        db_session.add(spec)
        await db_session.commit()

        # Add functional requirement
        from app.models.governance import FunctionalRequirement
        fr = FunctionalRequirement(
            specification_id=spec.id,
            requirement_id="FR-001",
            title="Calculate Vibecoding Index",
            description="System calculates vibecoding index using 5 signals",
            bdd_format="GIVEN code submission WHEN index calculated THEN score returned",
            priority="CRITICAL"
        )
        db_session.add(fr)
        await db_session.commit()

        # Act: Load spec with relationships
        result = await db_session.execute(
            select(Specification)
            .where(Specification.spec_id == "SPEC-0001")
        )
        spec_with_frs = result.scalar_one()
        await db_session.refresh(spec_with_frs, ["functional_requirements"])

        # Assert
        assert len(spec_with_frs.functional_requirements) == 1
        assert spec_with_frs.functional_requirements[0].requirement_id == "FR-001"
```

### 4.3 OPA Policy Integration Tests

**Test Structure**:
```python
# tests/integration/opa/test_opa_policies.py
import pytest
import httpx

@pytest.mark.integration
@pytest.mark.asyncio
class TestOPAPolicies:
    """Integration tests for OPA policy evaluation"""

    opa_url = "http://localhost:8181"

    async def test_vibecoding_routing_policy_green_zone(self):
        """
        GIVEN: Vibecoding index < 20
        WHEN: OPA policy is evaluated
        THEN: Routing should be 'auto_merge'
        """
        # Arrange
        policy_input = {
            "input": {
                "signals": {
                    "index": 15,
                    "intent_clarity": 90,
                    "code_ownership": 85,
                    "context_completeness": 95,
                    "ai_attestation": True,
                    "rejection_rate": 0.05
                },
                "project": {
                    "id": "PRJ-000001",
                    "tier": "PROFESSIONAL"
                }
            }
        }

        # Act
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.opa_url}/v1/data/governance/vibecoding",
                json=policy_input,
                timeout=1.0
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["routing"] == "auto_merge"
        assert data["result"]["allowed"] is True

    async def test_kill_switch_policy_rejection_rate_high(self):
        """
        GIVEN: Rejection rate > 80% for 30 minutes
        WHEN: Kill switch policy is evaluated
        THEN: Kill switch should trigger
        """
        # Arrange
        policy_input = {
            "input": {
                "metrics": {
                    "rejection_rate": 0.85,
                    "duration_minutes": 30,
                    "total_submissions": 100,
                    "rejected_count": 85
                },
                "project": {
                    "id": "PRJ-000001"
                }
            }
        }

        # Act
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.opa_url}/v1/data/governance/killswitch",
                json=policy_input,
                timeout=1.0
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["triggered"] is True
        assert data["result"]["trigger_type"] == "rejection_rate"
        assert data["result"]["action"] == "disable_ai_codegen"

    async def test_opa_policy_performance(self):
        """
        GIVEN: OPA policy endpoint
        WHEN: 100 requests are made
        THEN: All should complete in < 10ms p95
        """
        # Arrange
        latencies = []
        policy_input = {
            "input": {
                "signals": {"index": 25},
                "project": {"id": "PRJ-000001"}
            }
        }

        # Act
        async with httpx.AsyncClient() as client:
            for _ in range(100):
                start = datetime.now()
                await client.post(
                    f"{self.opa_url}/v1/data/governance/vibecoding",
                    json=policy_input
                )
                latency_ms = (datetime.now() - start).total_seconds() * 1000
                latencies.append(latency_ms)

        # Assert
        p95 = sorted(latencies)[94]  # 95th percentile
        assert p95 < 10, f"OPA p95 latency {p95}ms exceeds 10ms target"
```

### 4.4 MinIO Integration Tests

**Test Structure**:
```python
# tests/integration/minio/test_minio_storage.py
import pytest
import httpx
from datetime import datetime

@pytest.mark.integration
@pytest.mark.asyncio
class TestMinIOStorage:
    """Integration tests for MinIO S3 storage (AGPL-safe, network-only)"""

    minio_url = "http://localhost:9000"
    bucket = "spec-snapshots"

    async def test_upload_spec_snapshot(self, minio_credentials):
        """
        GIVEN: Specification YAML content
        WHEN: Uploaded to MinIO via S3 API
        THEN: Object should be stored and retrievable
        """
        # Arrange
        spec_id = "SPEC-0001"
        timestamp = datetime.utcnow().isoformat()
        object_name = f"{spec_id}/{timestamp}.yaml"
        content = """
spec_id: SPEC-0001
title: Test Spec
version: 1.0.0
        """.strip()

        # Act: Upload
        async with httpx.AsyncClient() as client:
            upload_response = await client.put(
                f"{self.minio_url}/{self.bucket}/{object_name}",
                content=content.encode('utf-8'),
                headers={"Content-Type": "application/x-yaml"},
                auth=(minio_credentials["access_key"], minio_credentials["secret_key"])
            )

        # Assert: Upload successful
        assert upload_response.status_code == 200

        # Act: Retrieve
        async with httpx.AsyncClient() as client:
            download_response = await client.get(
                f"{self.minio_url}/{self.bucket}/{object_name}",
                auth=(minio_credentials["access_key"], minio_credentials["secret_key"])
            )

        # Assert: Content matches
        assert download_response.status_code == 200
        assert download_response.text.strip() == content

    async def test_upload_performance_10mb(self, minio_credentials):
        """
        GIVEN: 10MB file
        WHEN: Uploaded to MinIO
        THEN: Upload should complete in < 2s (p95)
        """
        # Arrange
        content = b"x" * (10 * 1024 * 1024)  # 10MB
        object_name = "performance-test/10mb.bin"

        # Act
        start = datetime.now()
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.put(
                f"{self.minio_url}/{self.bucket}/{object_name}",
                content=content,
                headers={"Content-Type": "application/octet-stream"},
                auth=(minio_credentials["access_key"], minio_credentials["secret_key"])
            )
        latency_s = (datetime.now() - start).total_seconds()

        # Assert
        assert response.status_code == 200
        assert latency_s < 2.0, f"Upload took {latency_s}s, exceeds 2s target"
```

---

## 5. End-to-End Testing Strategy

### 5.1 E2E Testing Framework

**Framework**: Playwright 1.40.0+

**Test Structure**:
```typescript
// tests/e2e/governance/vibecoding-flow.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Vibecoding Index Calculation Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login as Platform Admin
    await page.goto('http://localhost:3000/login')
    await page.fill('input[name="email"]', 'admin@example.com')
    await page.fill('input[name="password"]', 'Admin123!')
    await page.click('button[type="submit"]')
    await page.waitForURL('**/dashboard')
  })

  test('E2E-001: Calculate vibecoding index for green zone submission', async ({ page }) => {
    /**
     * User Journey:
     * 1. Navigate to Governance Dashboard
     * 2. Submit code for evaluation
     * 3. View vibecoding index calculation
     * 4. Verify GREEN zone routing (auto-merge)
     */

    // Step 1: Navigate to Governance Dashboard
    await page.click('nav >> text=Governance')
    await expect(page).toHaveURL('**/governance')

    // Step 2: Submit code for evaluation
    await page.click('button:has-text("New Submission")')
    await page.fill('textarea[name="code"]', `
def hello_world():
    """Print hello world message"""
    print("Hello, World!")
    return 0

if __name__ == "__main__":
    hello_world()
    `.trim())

    // Fill metadata
    await page.selectOption('select[name="project"]', 'PRJ-000001')
    await page.selectOption('select[name="tier"]', 'PROFESSIONAL')

    // Submit
    await page.click('button:has-text("Evaluate")')

    // Step 3: Wait for calculation to complete
    await page.waitForSelector('.vibecoding-score', { timeout: 5000 })

    // Step 4: Verify GREEN zone
    const score = await page.textContent('.vibecoding-score')
    const scoreValue = parseInt(score || '0')
    expect(scoreValue).toBeLessThan(20)

    const zoneBadge = page.locator('.vibecoding-zone-badge')
    await expect(zoneBadge).toHaveText('GREEN')
    await expect(zoneBadge).toHaveClass(/bg-green/)

    const routing = page.locator('.routing-decision')
    await expect(routing).toHaveText(/AUTO_MERGE/i)
  })

  test('E2E-002: Kill switch triggers on high rejection rate', async ({ page }) => {
    /**
     * User Journey:
     * 1. Submit multiple failing validations (simulate high rejection rate)
     * 2. Check kill switch status
     * 3. Verify kill switch triggered
     * 4. Verify AI codegen disabled
     */

    // Step 1: Submit 30 failing validations
    await page.goto('http://localhost:3000/governance/submissions')

    for (let i = 0; i < 30; i++) {
      await page.click('button:has-text("New Submission")')
      await page.fill('textarea[name="code"]', 'invalid code\n'.repeat(10))
      await page.click('button:has-text("Evaluate")')
      await page.waitForSelector('.validation-failed', { timeout: 2000 })
      await page.click('button:has-text("Close")')
    }

    // Step 2: Check kill switch status
    await page.goto('http://localhost:3000/governance/kill-switch')

    // Step 3: Verify triggered
    await expect(page.locator('.kill-switch-status')).toHaveText(/TRIGGERED/i)
    await expect(page.locator('.trigger-reason')).toHaveText(/rejection rate > 80%/i)

    // Step 4: Verify AI codegen disabled
    await page.goto('http://localhost:3000/governance/submissions/new')
    const submitButton = page.locator('button:has-text("Evaluate")')
    await expect(submitButton).toBeDisabled()

    const warningMessage = page.locator('.kill-switch-warning')
    await expect(warningMessage).toBeVisible()
    await expect(warningMessage).toHaveText(/AI codegen disabled for 24h/i)
  })

  test('E2E-003: Specification validation with YAML frontmatter', async ({ page }) => {
    /**
     * User Journey:
     * 1. Navigate to Specification Validator
     * 2. Enter valid YAML frontmatter
     * 3. Submit for validation
     * 4. Verify validation success
     */

    // Step 1: Navigate
    await page.goto('http://localhost:3000/governance/spec-validator')

    // Step 2: Enter valid YAML
    const validYaml = `
spec_id: SPEC-9999
title: Test Specification
version: 1.0.0
status: DRAFT
tier: [PROFESSIONAL, ENTERPRISE]
pillar: 2
owner: QA Lead
last_updated: 2026-01-28
    `.trim()

    await page.fill('textarea[name="yaml_content"]', validYaml)

    // Step 3: Submit
    await page.click('button:has-text("Validate")')

    // Step 4: Verify success
    await expect(page.locator('.validation-status')).toHaveText(/Valid/i)
    await expect(page.locator('.validation-status')).toHaveClass(/text-green/)

    const errorList = page.locator('.validation-errors')
    await expect(errorList).toBeHidden()
  })
})
```

### 5.2 E2E Test Coverage

```yaml
Critical User Journeys (10 scenarios):

1. E2E-001: Vibecoding Index - Green Zone
   - Submit high-quality code
   - Verify score < 20
   - Verify AUTO_MERGE routing

2. E2E-002: Vibecoding Index - Red Zone
   - Submit low-quality code
   - Verify score >= 60
   - Verify BLOCK_OR_COUNCIL routing

3. E2E-003: Kill Switch - Rejection Rate Trigger
   - Submit 30 failing validations
   - Verify kill switch triggers
   - Verify AI codegen disabled

4. E2E-004: Specification Validation - Valid YAML
   - Enter valid YAML frontmatter
   - Submit for validation
   - Verify validation success

5. E2E-005: Specification Validation - Invalid YAML
   - Enter invalid YAML (missing required fields)
   - Submit for validation
   - Verify validation errors displayed

6. E2E-006: Tier Upgrade Request
   - Navigate to Tier Management
   - Request upgrade from STANDARD to PROFESSIONAL
   - Verify request submitted

7. E2E-007: Progressive Routing - Yellow Zone
   - Submit medium-quality code
   - Verify score 20-40
   - Verify HUMAN_REVIEW_REQUIRED routing

8. E2E-008: Vibecoding Signal Breakdown
   - Submit code
   - View signal breakdown (5 signals)
   - Verify weights (30%, 25%, 20%, 15%, 10%)

9. E2E-009: Multi-Currency Support
   - Update subscription with VND currency
   - Verify currency displayed correctly
   - Verify trial dates shown

10. E2E-010: Bilingual UI (EN/VI)
    - Switch language to Vietnamese
    - Verify all UI text translated
    - Submit code evaluation
    - Verify results in Vietnamese
```

---

## 6. Performance Testing Strategy

### 6.1 Performance Test Framework

**Framework**: pytest-benchmark + Locust

**Backend Performance Tests**:
```python
# tests/performance/test_api_latency.py
import pytest
from datetime import datetime

@pytest.mark.benchmark
def test_calculate_vibecoding_index_latency(benchmark, db_session, sample_submission):
    """
    GIVEN: Vibecoding index calculation endpoint
    WHEN: Benchmark test is run
    THEN: p95 latency should be < 100ms
    """
    # Arrange
    from app.services.vibecoding_service import VibecodingService
    service = VibecodingService(db_session)

    submission = sample_submission(
        intent_clarity=80,
        code_ownership=75,
        context_completeness=85
    )

    # Act & Assert
    result = benchmark(service.calculate_index, submission_id=submission.submission_id)

    # Verify result correctness
    assert result.score is not None
    assert 0 <= result.score <= 100

    # Benchmark stats automatically checked by pytest-benchmark
    # Target: < 100ms p95 (configured in pytest.ini)

@pytest.mark.benchmark
def test_database_query_latency(benchmark, db_session):
    """
    GIVEN: Database query for specification metadata
    WHEN: Benchmark test is run
    THEN: p95 latency should be < 50ms
    """
    from sqlalchemy import select
    from app.models.governance import Specification

    def query_specs():
        return db_session.execute(
            select(Specification).limit(100)
        ).scalars().all()

    # Act & Assert
    results = benchmark(query_specs)
    assert len(results) > 0
```

**Load Testing with Locust**:
```python
# tests/load/locustfile.py
from locust import HttpUser, task, between
import random

class GovernanceUser(HttpUser):
    wait_time = between(1, 3)
    host = "http://localhost:8000"

    def on_start(self):
        """Login and get JWT token"""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "Test123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(10)
    def calculate_vibecoding_index(self):
        """Calculate vibecoding index (70% of requests)"""
        submission_id = f"SUB-{random.randint(100000, 999999)}"
        self.client.post(
            "/api/v1/governance/vibecoding/calculate",
            headers=self.headers,
            json={
                "submission_id": submission_id,
                "project_id": "PRJ-000001",
                "tier": "PROFESSIONAL"
            },
            name="/vibecoding/calculate"
        )

    @task(5)
    def get_spec_metadata(self):
        """Get specification metadata (30% of requests)"""
        spec_id = random.choice(["SPEC-0001", "SPEC-0002", "SPEC-0012"])
        self.client.get(
            f"/api/v1/governance/specs/{spec_id}",
            headers=self.headers,
            name="/specs/{spec_id}"
        )

    @task(2)
    def validate_spec(self):
        """Validate YAML frontmatter (10% of requests)"""
        self.client.post(
            "/api/v1/governance/specs/validate",
            headers=self.headers,
            json={
                "yaml_content": "spec_id: SPEC-9999\ntitle: Test\nversion: 1.0.0"
            },
            name="/specs/validate"
        )

# Run with: locust -f locustfile.py --users 100 --spawn-rate 10 --run-time 5m
```

### 6.2 Performance Targets

```yaml
API Latency (p95):
  POST /api/v1/governance/specs/validate: < 50ms
  GET /api/v1/governance/specs/{spec_id}: < 30ms
  POST /api/v1/governance/vibecoding/calculate: < 100ms
  GET /api/v1/governance/vibecoding/{submission_id}: < 50ms
  POST /api/v1/governance/vibecoding/route: < 50ms
  POST /api/v1/governance/vibecoding/kill-switch/check: < 30ms
  GET /api/v1/governance/tiers/{project_id}: < 20ms
  POST /api/v1/governance/tiers/{project_id}/upgrade: < 50ms

Database Queries (p95):
  Simple SELECT: < 10ms
  JOIN (2 tables): < 50ms
  JSONB query: < 30ms
  Full-text search: < 100ms
  Aggregate query: < 200ms

External Services (p95):
  OPA policy evaluation: < 10ms
  MinIO upload (10MB): < 2s
  MinIO download (10MB): < 1s
  Redis GET: < 5ms
  Redis SET: < 10ms

Load Testing Targets:
  Concurrent Users: 100
  Requests per Second: 500
  Success Rate: > 99%
  Error Rate: < 1%
  Duration: 5 minutes sustained
```

---

## 7. Security Testing Strategy

### 7.1 Security Test Framework

**Framework**: pytest + Semgrep

**Security Tests**:
```python
# tests/security/test_authentication.py
import pytest
import httpx

@pytest.mark.security
@pytest.mark.asyncio
class TestAuthentication:
    """Security tests for authentication and authorization"""

    base_url = "http://localhost:8000"

    async def test_unauthenticated_request_returns_401(self):
        """
        GIVEN: Protected endpoint
        WHEN: Request without JWT token
        THEN: 401 Unauthorized
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/governance/vibecoding/calculate",
                json={"submission_id": "SUB-000001"}
            )

        assert response.status_code == 401
        assert "Unauthorized" in response.json()["detail"]

    async def test_expired_token_returns_401(self):
        """
        GIVEN: Expired JWT token
        WHEN: Request with expired token
        THEN: 401 Unauthorized with 'expired' message
        """
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIiwiZXhwIjoxNjAwMDAwMDAwfQ.invalidtoken"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/governance/vibecoding/calculate",
                headers={"Authorization": f"Bearer {expired_token}"},
                json={"submission_id": "SUB-000001"}
            )

        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    async def test_rbac_insufficient_permissions_returns_403(self, dev_user_token):
        """
        GIVEN: Tier upgrade endpoint (requires PM role)
        WHEN: DEV user attempts to upgrade tier
        THEN: 403 Forbidden
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/governance/tiers/PRJ-000001/upgrade",
                headers={"Authorization": f"Bearer {dev_user_token}"},
                json={"target_tier": "ENTERPRISE"}
            )

        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

    async def test_sql_injection_prevention(self, auth_token):
        """
        GIVEN: Spec ID with SQL injection payload
        WHEN: GET /api/v1/governance/specs/{spec_id}
        THEN: 404 Not Found (input sanitized, no SQL injection)
        """
        malicious_spec_id = "SPEC-0001' OR '1'='1"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/governance/specs/{malicious_spec_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )

        # Should return 404 (not found) or 400 (invalid format), NOT 200 with all specs
        assert response.status_code in [400, 404, 422]
        assert response.json().get("detail") is not None

    async def test_xss_prevention_in_spec_title(self, auth_token):
        """
        GIVEN: Specification title with XSS payload
        WHEN: Spec is validated and stored
        THEN: XSS payload should be escaped/sanitized
        """
        xss_yaml = """
spec_id: SPEC-9999
title: <script>alert('XSS')</script>
version: 1.0.0
status: DRAFT
tier: [PROFESSIONAL]
pillar: 2
owner: Test
        """.strip()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/governance/specs/validate",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={"yaml_content": xss_yaml}
            )

        assert response.status_code == 200
        data = response.json()

        # Title should be escaped or rejected
        assert "<script>" not in data["title"] or data["valid"] is False
```

### 7.2 SAST with Semgrep

**Semgrep Rules**:
```yaml
# .semgrep/governance-rules.yml
rules:
  - id: agpl-import-detection
    pattern-either:
      - pattern: from minio import $X
      - pattern: import minio
      - pattern: from grafana import $X
      - pattern: import grafana
    message: "AGPL library import detected. Use network-only access (HTTP API) instead."
    languages: [python]
    severity: ERROR

  - id: sql-injection-risk
    pattern-either:
      - pattern: f"SELECT * FROM ... WHERE {$X}"
      - pattern: f"INSERT INTO ... VALUES ({$X})"
    message: "Potential SQL injection. Use parameterized queries with SQLAlchemy."
    languages: [python]
    severity: WARNING

  - id: hardcoded-secret
    pattern-regex: "(password|secret|api_key)\\s*=\\s*['\"][^'\"]{8,}['\"]"
    message: "Hardcoded secret detected. Use environment variables or Vault."
    languages: [python, javascript, typescript]
    severity: ERROR

  - id: missing-jwt-verification
    pattern-either:
      - pattern: jwt.decode($TOKEN, verify=False)
      - pattern: jwt.decode($TOKEN, options={"verify_signature": False})
    message: "JWT signature verification disabled. Always verify tokens."
    languages: [python]
    severity: ERROR

  - id: yaml-unsafe-load
    pattern: yaml.load($X)
    message: "Unsafe YAML loading. Use yaml.safe_load() instead."
    languages: [python]
    severity: ERROR
```

**CI/CD Integration**:
```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on: [push, pull_request]

jobs:
  semgrep:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Semgrep
        run: |
          pip install semgrep
          semgrep --config=.semgrep/governance-rules.yml \
                  --config=p/owasp-top-ten \
                  --config=p/security-audit \
                  --error \
                  --verbose \
                  backend/app

  trivy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker Image
        run: docker build -t backend:test backend/
      - name: Run Trivy
        run: |
          docker run --rm \
            -v /var/run/docker.sock:/var/run/docker.sock \
            aquasec/trivy:latest image \
            --severity HIGH,CRITICAL \
            --exit-code 1 \
            backend:test
```

---

## 8. Load Testing Strategy

### 8.1 Load Test Scenarios

**Scenario 1: Normal Load (Baseline)**
```yaml
Users: 50 concurrent users
Spawn Rate: 5 users/second
Duration: 5 minutes
Requests:
  - 70% Vibecoding index calculation
  - 20% Specification metadata retrieval
  - 10% Specification validation

Expected Results:
  - Success Rate: > 99%
  - p95 Latency: < 100ms
  - Errors: < 1%
```

**Scenario 2: Peak Load (2x Normal)**
```yaml
Users: 100 concurrent users
Spawn Rate: 10 users/second
Duration: 10 minutes

Expected Results:
  - Success Rate: > 98%
  - p95 Latency: < 150ms
  - Errors: < 2%
```

**Scenario 3: Stress Test (Find Breaking Point)**
```yaml
Users: 500 concurrent users
Spawn Rate: 25 users/second
Duration: 5 minutes

Goal: Identify system breaking point
Monitor:
  - Database connection pool exhaustion
  - Redis memory usage
  - OPA CPU usage
  - API error rate spike
```

### 8.2 Load Test Execution

```bash
# Install Locust
pip install locust

# Run baseline load test
locust -f tests/load/locustfile.py \
       --users 50 \
       --spawn-rate 5 \
       --run-time 5m \
       --host http://localhost:8000 \
       --html=reports/load-test-baseline.html

# Run peak load test
locust -f tests/load/locustfile.py \
       --users 100 \
       --spawn-rate 10 \
       --run-time 10m \
       --host http://localhost:8000 \
       --html=reports/load-test-peak.html

# Run stress test (headless)
locust -f tests/load/locustfile.py \
       --users 500 \
       --spawn-rate 25 \
       --run-time 5m \
       --host http://localhost:8000 \
       --headless \
       --html=reports/load-test-stress.html
```

---

## 9. Test Data Management

### 9.1 Test Data Strategy

**Fixtures** (Shared Test Data):
```python
# tests/fixtures/governance_fixtures.py
import pytest
from datetime import datetime

@pytest.fixture
def spec_yaml_valid():
    """Valid YAML frontmatter for SPEC-0001"""
    return """
spec_id: SPEC-0001
title: Anti-Vibecoding Quality Assurance System
version: 1.0.0
status: APPROVED
tier: [PROFESSIONAL, ENTERPRISE]
pillar: 2
owner: QA Lead
last_updated: 2026-01-28
    """.strip()

@pytest.fixture
def spec_yaml_invalid_missing_tier():
    """Invalid YAML: missing 'tier' field"""
    return """
spec_id: SPEC-0001
title: Test Spec
version: 1.0.0
status: DRAFT
    """.strip()

@pytest.fixture
def vibecoding_signal_green_zone():
    """Vibecoding signal data for GREEN zone (score < 20)"""
    return {
        "submission_id": "SUB-000001",
        "project_id": "PRJ-000001",
        "intent_clarity": 90,
        "code_ownership": 85,
        "context_completeness": 95,
        "ai_attestation": True,
        "rejection_rate": 0.05
    }

@pytest.fixture
def vibecoding_signal_red_zone():
    """Vibecoding signal data for RED zone (score >= 60)"""
    return {
        "submission_id": "SUB-000002",
        "project_id": "PRJ-000001",
        "intent_clarity": 30,
        "code_ownership": 25,
        "context_completeness": 40,
        "ai_attestation": False,
        "rejection_rate": 0.90
    }
```

**Factories** (Dynamic Test Data):
```python
# tests/factories/governance_factories.py
import factory
from datetime import datetime, timedelta
import random

class SpecificationFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Specification
        sqlalchemy_session_persistence = "commit"

    spec_id = factory.Sequence(lambda n: f"SPEC-{n:04d}")
    title = factory.Faker("sentence", nb_words=5)
    version = "1.0.0"
    status = factory.Iterator(["DRAFT", "APPROVED", "DEPRECATED"])
    tier = factory.LazyFunction(lambda: random.choice([
        ["LITE", "STANDARD"],
        ["PROFESSIONAL", "ENTERPRISE"],
        ["LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"]
    ]))
    pillar = factory.LazyFunction(lambda: random.randint(1, 7))
    owner = factory.Faker("name")
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)

class VibecodingSignalFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = VibecodingSignal
        sqlalchemy_session_persistence = "commit"

    submission_id = factory.Sequence(lambda n: f"SUB-{n:06d}")
    project_id = factory.LazyFunction(lambda: f"PRJ-{random.randint(1, 100):06d}")
    intent_clarity = factory.LazyFunction(lambda: random.randint(0, 100))
    code_ownership = factory.LazyFunction(lambda: random.randint(0, 100))
    context_completeness = factory.LazyFunction(lambda: random.randint(0, 100))
    ai_attestation = factory.LazyFunction(lambda: random.choice([True, False]))
    rejection_rate = factory.LazyFunction(lambda: random.uniform(0, 1))
    created_at = factory.LazyFunction(datetime.utcnow)

# Usage in tests:
def test_with_factory(db_session):
    spec = SpecificationFactory.create(spec_id="SPEC-9999")
    assert spec.spec_id == "SPEC-9999"
```

### 9.2 Test Database Management

**Setup/Teardown**:
```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.database import Base

@pytest.fixture(scope="session")
async def test_db_engine():
    """Create test database engine (once per test session)"""
    engine = create_async_engine(
        "postgresql+asyncpg://test:test@localhost:5432/sdlc_test",
        echo=False,
        pool_size=20,
        max_overflow=40
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(test_db_engine):
    """Create isolated test session (rollback after each test)"""
    connection = await test_db_engine.connect()
    transaction = await connection.begin()

    session = AsyncSession(bind=connection, expire_on_commit=False)

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()
```

---

## 10. CI/CD Integration

### 10.1 GitHub Actions Workflows

**Test Workflow**:
```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  unit-tests-backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15.5
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: sdlc_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7.2-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install -r backend/requirements-test.txt

      - name: Run unit tests
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/sdlc_test
          REDIS_URL: redis://localhost:6379/0
        run: |
          cd backend
          pytest tests/unit \
            --cov=app \
            --cov-report=xml \
            --cov-report=term-missing \
            --cov-fail-under=95 \
            --verbose

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: backend/coverage.xml
          flags: backend-unit
          name: backend-unit-tests

  integration-tests-backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15.5
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: sdlc_test
        ports:
          - 5432:5432

      redis:
        image: redis:7.2-alpine
        ports:
          - 6379:6379

      opa:
        image: openpolicyagent/opa:0.58.0-rootless
        ports:
          - 8181:8181
        options: >-
          --entrypoint "/opa run --server --addr=:8181 /policies"

      minio:
        image: minio/minio:latest
        ports:
          - 9000:9000
        env:
          MINIO_ROOT_USER: test
          MINIO_ROOT_PASSWORD: testtest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install -r backend/requirements-test.txt

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/sdlc_test
          REDIS_URL: redis://localhost:6379/0
          OPA_URL: http://localhost:8181
          MINIO_URL: http://localhost:9000
          MINIO_ACCESS_KEY: test
          MINIO_SECRET_KEY: testtest
        run: |
          cd backend
          pytest tests/integration \
            --cov=app \
            --cov-report=xml \
            --cov-report=term-missing \
            --cov-fail-under=90 \
            --verbose

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: backend/coverage.xml
          flags: backend-integration
          name: backend-integration-tests

  unit-tests-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js 20
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: frontend/node_modules
          key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run unit tests
        run: |
          cd frontend
          npm run test:coverage

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: frontend/coverage/coverage-final.json
          flags: frontend-unit
          name: frontend-unit-tests

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js 20
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci
          npx playwright install --with-deps

      - name: Start services
        run: |
          docker-compose up -d
          sleep 10  # Wait for services to be ready

      - name: Run E2E tests
        run: |
          cd frontend
          npm run test:e2e

      - name: Upload Playwright report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Semgrep
        run: |
          pip install semgrep
          semgrep --config=.semgrep/governance-rules.yml \
                  --config=p/owasp-top-ten \
                  --error \
                  backend/app

      - name: Build Docker Image
        run: docker build -t backend:test backend/

      - name: Run Trivy
        run: |
          docker run --rm \
            -v /var/run/docker.sock:/var/run/docker.sock \
            aquasec/trivy:latest image \
            --severity HIGH,CRITICAL \
            --exit-code 1 \
            backend:test
```

### 10.2 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: unit-tests
        name: Run unit tests
        entry: bash -c 'cd backend && pytest tests/unit --exitfirst --verbose'
        language: system
        pass_filenames: false
        stages: [commit]

      - id: ruff-check
        name: Ruff linting
        entry: bash -c 'cd backend && ruff check app tests'
        language: system
        pass_filenames: false
        stages: [commit]

      - id: mypy
        name: MyPy type checking
        entry: bash -c 'cd backend && mypy app'
        language: system
        pass_filenames: false
        stages: [commit]

      - id: agpl-import-check
        name: Check for AGPL imports
        entry: bash -c 'if grep -rn "from minio import\|import minio\|from grafana import\|import grafana" backend/app; then echo "ERROR: AGPL library import detected!"; exit 1; fi'
        language: system
        pass_filenames: false
        stages: [commit]

      - id: mock-keyword-check
        name: Check for mock keywords in tests
        entry: bash -c 'if grep -rn "Mock()\|MagicMock()\|patch(" backend/tests/unit backend/tests/integration | grep -v "# allowed-mock"; then echo "WARNING: Mock usage detected. Use real services (Zero Mock Policy)"; exit 1; fi'
        language: system
        pass_filenames: false
        stages: [commit]

# Install: pre-commit install
```

---

## 11. Test Metrics & Reporting

### 11.1 Coverage Tracking

**Codecov Integration**:
```yaml
# codecov.yml
coverage:
  status:
    project:
      backend:
        target: 95%
        threshold: 1%
      frontend:
        target: 90%
        threshold: 1%
    patch:
      backend:
        target: 95%
      frontend:
        target: 90%

comment:
  layout: "header, diff, files"
  behavior: default
  require_changes: false

ignore:
  - "backend/tests"
  - "frontend/tests"
  - "**/*.config.*"
  - "**/*.d.ts"
```

### 11.2 Test Reporting Dashboard

**Grafana Dashboard** (Metrics):
```yaml
Test Execution Metrics:
  - Total test count (unit + integration + E2E)
  - Test success rate (%)
  - Test execution time (p50, p95, p99)
  - Coverage percentage (backend, frontend)
  - Flaky test count

CI/CD Pipeline Metrics:
  - Pipeline execution time (minutes)
  - Pipeline success rate (%)
  - Failed build count (per day)
  - Average time to fix failed build

Quality Metrics:
  - Bugs found by test type (unit, integration, E2E)
  - Production bugs (escaped tests)
  - Test ROI (bugs caught / test execution time)
```

**Test Report Format** (HTML):
```html
<!-- generated by pytest-html -->
<html>
  <head><title>Test Report - Governance v2.0</title></head>
  <body>
    <h1>Test Execution Summary</h1>
    <table>
      <tr>
        <th>Test Type</th>
        <th>Total</th>
        <th>Passed</th>
        <th>Failed</th>
        <th>Skipped</th>
        <th>Coverage</th>
      </tr>
      <tr>
        <td>Unit (Backend)</td>
        <td>250</td>
        <td>248</td>
        <td>2</td>
        <td>0</td>
        <td>96.2%</td>
      </tr>
      <tr>
        <td>Integration (Backend)</td>
        <td>100</td>
        <td>98</td>
        <td>2</td>
        <td>0</td>
        <td>92.5%</td>
      </tr>
      <tr>
        <td>Unit (Frontend)</td>
        <td>120</td>
        <td>118</td>
        <td>2</td>
        <td>0</td>
        <td>91.3%</td>
      </tr>
      <tr>
        <td>E2E</td>
        <td>10</td>
        <td>10</td>
        <td>0</td>
        <td>0</td>
        <td>N/A</td>
      </tr>
      <tr>
        <th>TOTAL</th>
        <th>480</th>
        <th>474</th>
        <th>6</th>
        <th>0</th>
        <th>95.1%</th>
      </tr>
    </table>

    <h2>Failed Tests</h2>
    <ul>
      <li>test_kill_switch_latency_trigger - AssertionError: Expected < 500ms, got 520ms</li>
      <li>test_spec_validation_performance - Timeout after 5s</li>
    </ul>
  </body>
</html>
```

---

## 12. Test Environment Strategy

### 12.1 Environment Configuration

```yaml
Local Development:
  Backend: localhost:8000
  Frontend: localhost:3000
  Database: localhost:5432 (Docker)
  Redis: localhost:6379 (Docker)
  OPA: localhost:8181 (Docker)
  MinIO: localhost:9000 (Docker)

CI/CD (GitHub Actions):
  Backend: container service
  Database: postgres:15.5 (service container)
  Redis: redis:7.2-alpine (service container)
  OPA: openpolicyagent/opa:0.58.0 (service container)
  MinIO: minio/minio:latest (service container)

Staging:
  Backend: https://api-staging.sdlc-orchestrator.com
  Frontend: https://staging.sdlc-orchestrator.com
  Database: RDS PostgreSQL (staging)
  Redis: ElastiCache (staging)
  OPA: Kubernetes pod
  MinIO: S3 bucket (staging)

Production:
  Backend: https://api.sdlc-orchestrator.com
  Frontend: https://app.sdlc-orchestrator.com
  Database: RDS PostgreSQL (production, multi-AZ)
  Redis: ElastiCache (production, multi-AZ)
  OPA: Kubernetes deployment (3 replicas)
  MinIO: S3 bucket (production, versioning enabled)
```

### 12.2 Docker Compose for Testing

```yaml
# docker-compose.test.yml
version: '3.9'

services:
  postgres-test:
    image: postgres:15.5
    environment:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: sdlc_test
    ports:
      - "5433:5432"
    volumes:
      - postgres_test_data:/var/lib/postgresql/data

  redis-test:
    image: redis:7.2-alpine
    ports:
      - "6380:6379"
    volumes:
      - redis_test_data:/data

  opa-test:
    image: openpolicyagent/opa:0.58.0-rootless
    command: run --server --addr=:8181 /policies
    ports:
      - "8182:8181"
    volumes:
      - ./backend/policies:/policies

  minio-test:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: test
      MINIO_ROOT_PASSWORD: testtest123
    ports:
      - "9050:9000"  # Test S3 API (avoid conflict with staging 9020)
      - "9051:9001"  # Test Console (avoid conflict with staging 9021)
    volumes:
      - minio_test_data:/data

volumes:
  postgres_test_data:
  redis_test_data:
  minio_test_data:

# Usage: docker-compose -f docker-compose.test.yml up -d
```

---

## 13. Test Execution Summary

### 13.1 Test Execution Plan

```yaml
Sprint 118 Implementation Phase (Feb 10-20):

  Week 1 (Feb 10-14):
    - Day 1-2: Unit tests for vibecoding service (95%+ coverage)
    - Day 3-4: Integration tests for API endpoints (90%+ coverage)
    - Day 5: E2E tests for critical user journeys (10 scenarios)

  Week 2 (Feb 17-20):
    - Day 1: Performance tests (API latency, database queries)
    - Day 2: Load tests (100 concurrent users)
    - Day 3: Security tests (SAST, penetration testing)
    - Day 4: Final QA + bug fixes

Gate Review (Feb 21):
  - All tests passing (95%+ coverage)
  - Performance targets met (<100ms p95)
  - Security scan passed (no HIGH/CRITICAL issues)
  - CTO approval
```

### 13.2 Success Criteria

```yaml
Definition of Done (Testing):
  ✅ Unit tests: 95%+ coverage
  ✅ Integration tests: 90%+ coverage
  ✅ E2E tests: 10 critical scenarios pass
  ✅ Performance tests: <100ms p95 API latency
  ✅ Load tests: 100 concurrent users, >99% success rate
  ✅ Security tests: 0 HIGH/CRITICAL vulnerabilities
  ✅ Zero Mock Policy: 100% compliance (real services only)
  ✅ CI/CD pipeline: <20min execution time
  ✅ Test reports: Generated and reviewed
  ✅ CTO approval: Testing strategy validated
```

---

**D4 Status**: ✅ COMPLETE
**Document Version**: 2.0.0
**Total Test Count**: ~500 tests (300 unit, 150 integration, 50 E2E)
**Target Coverage**: Backend 95%, Frontend 90%
**Estimated Execution Time**: <5min (unit), <10min (integration), <20min (E2E)
**Next Deliverable**: D5 - Implementation Phases (Feb 4-5)

---

**Sprint 118 Track 2 Progress**:
- ✅ D1: Database Schema Governance v2 (14 tables)
- ✅ D2: API Specification Governance v2 (12 endpoints)
- ✅ D3: Technical Dependencies (87 packages)
- ✅ D4: Testing Strategy (~500 tests, 95%+ coverage)
- ⏳ D5: Implementation Phases (Feb 4-5)
- ⏳ D6: Architecture Diagrams (Feb 6-7)
