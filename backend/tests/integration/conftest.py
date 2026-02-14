"""
=========================================================================
Integration Tests Conftest - Sprint 118 Track 2 Phase 5
SDLC Orchestrator - Stage 04 (BUILD)

Version: 2.1.0
Date: February 4, 2026
Status: ACTIVE - Sprint 154 E2E Testing
Authority: Backend Lead + CTO Approved
Framework: SDLC 6.0.5 Quality Assurance System

Purpose:
- Fixtures for API integration tests
- AsyncClient for HTTP testing
- Authentication fixtures
- Database session fixtures

Updated: Sprint 154 - Fixed mock_external_http to allow ASGITransport
=========================================================================
"""

import os
import sys
from typing import AsyncGenerator
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
import httpx
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.fixture(autouse=True)
def mock_external_http():
    """
    Override parent's mock_external_http to NOT interfere with ASGITransport.

    Integration tests use ASGITransport which doesn't make real HTTP calls,
    so we don't need to mock httpx at all. This fixture is a no-op that
    overrides the parent's autouse fixture.

    External service mocking (OPA, MinIO, Ollama) is handled by:
    - Environment variables (REDIS_URL=localhost, etc.)
    - Service-specific mock fixtures (mock_opa_client, etc.)
    """
    # No-op: Let ASGITransport handle requests directly to the FastAPI app
    yield


def pytest_configure(config):
    """Configure pytest for integration tests."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )


# ============================================================================
# Environment Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def integration_test_env():
    """Fixture to provide integration test environment info."""
    return {
        "ai_platform_ollama_url": os.getenv("AI_PLATFORM_OLLAMA_URL", "http://localhost:11434"),
        "ai_platform_minio_url": os.getenv("AI_PLATFORM_MINIO_URL", "http://localhost:9000"),
        "database_url": os.getenv(
            "TEST_DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/sdlc_test"
        ),
    }


# ============================================================================
# Application Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client for API integration tests.

    Uses the FastAPI app with ASGI transport for testing.
    """
    try:
        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    except ImportError:
        # Fallback: Create a minimal test client if app import fails
        # This allows tests to run even if full app setup isn't available
        async with AsyncClient(base_url="http://localhost:8000") as ac:
            yield ac


# ============================================================================
# Authentication Fixtures
# ============================================================================


@pytest.fixture
def test_user_data() -> dict:
    """Test user data for authentication."""
    return {
        "id": "test-user-001",
        "email": "test@example.com",
        "username": "testuser",
        "role": "developer",
        "team_id": "team-001",
    }


@pytest_asyncio.fixture
async def auth_headers(test_user_data: dict) -> dict:
    """
    Authentication headers for API requests.

    Generates a test JWT token for authenticated requests.
    In production tests, this would use real token generation.
    """
    try:
        from app.core.security import create_access_token
        from datetime import timedelta

        # Create a real JWT token for testing
        # Note: create_access_token takes subject (str or dict), not data keyword
        token = await create_access_token(
            subject=test_user_data["id"],
            expires_delta=timedelta(hours=1),
        )
        return {"Authorization": f"Bearer {token}"}
    except ImportError:
        # Fallback: Use a mock token format for testing structure
        # Tests using this should check for 401 responses
        import base64
        import json

        # Create a base64-encoded test token (not cryptographically valid)
        payload = {
            "sub": test_user_data["id"],
            "email": test_user_data["email"],
            "exp": 9999999999,
        }
        token_data = base64.b64encode(json.dumps(payload).encode()).decode()
        return {"Authorization": f"Bearer test.{token_data}.test"}


@pytest_asyncio.fixture
async def admin_auth_headers() -> dict:
    """
    Admin authentication headers for privileged operations.
    """
    try:
        from app.core.security import create_access_token
        from datetime import timedelta

        # Note: create_access_token takes subject (str or dict), not data keyword
        token = await create_access_token(
            subject="admin-user-001",
            expires_delta=timedelta(hours=1),
        )
        return {"Authorization": f"Bearer {token}"}
    except ImportError:
        return {"Authorization": "Bearer admin_test_token"}


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def db_session(integration_test_env: dict) -> AsyncGenerator[AsyncSession, None]:
    """
    Async database session for integration tests.

    Uses a separate test database and rolls back after each test.
    """
    try:
        from app.core.database import Base

        engine = create_async_engine(
            integration_test_env["database_url"],
            echo=False,
        )

        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            yield session
            await session.rollback()

    except Exception:
        # If database isn't available, skip tests that need it
        pytest.skip("Database not available for integration tests")


# ============================================================================
# Test Data Fixtures
# ============================================================================


@pytest.fixture
def sample_project_id() -> str:
    """Sample project ID for testing."""
    import uuid
    return f"proj-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def sample_spec_content() -> str:
    """Sample valid specification content."""
    return """---
spec_version: "1.0"
spec_id: SPEC-TEST-001
status: draft
tier: PROFESSIONAL
stage: 04-build
owner: test-team
created: 2026-01-29
last_updated: 2026-01-29
related_adrs: [ADR-041, ADR-022]
---

## 1. Overview
This is a test specification for integration testing.

## 2. Requirements
### 2.1 Functional Requirements (BDD)
- GIVEN a test scenario WHEN tests run THEN validation passes

### 2.2 Non-Functional Requirements
- Performance: <100ms p95 latency
- Security: OWASP ASVS L2 compliance

## 3. Acceptance Criteria
- [ ] All tests pass
- [ ] Coverage meets threshold
"""


@pytest.fixture
def sample_vibecoding_signals() -> dict:
    """Sample vibecoding signals for testing."""
    return {
        "intent_signal": 15,
        "ownership_signal": 10,
        "context_signal": 5,
        "ai_attestation_signal": 0,
        "rejection_history_signal": 0,
    }
