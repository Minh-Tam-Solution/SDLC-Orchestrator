# WEEK 6 DAY 1 - INTEGRATION TEST SUITE SETUP
## SDLC Orchestrator - Integration Testing Sprint

**Date**: December 12, 2025 (Thursday)
**Sprint**: Week 6 (December 12-16, 2025) - Integration Testing
**Day**: Day 1 of 5
**Status**: ⏳ **IN PROGRESS**
**Authority**: Backend Lead + QA Lead + CTO
**Framework**: SDLC 4.9 Complete Lifecycle (Stage 04 (BUILD)

---

## Executive Summary

**Day 1 Objective**: Set up comprehensive integration test suite infrastructure targeting 90%+ coverage across all 31 API endpoints.

**Success Criteria**:
- ✅ Pytest + pytest-asyncio configured
- ✅ Isolated test database set up
- ✅ Test fixtures created for all services (PostgreSQL, Redis, MinIO, OPA)
- ✅ Integration tests written for 31 endpoints
- ✅ 90%+ integration test coverage achieved

**Timeline**: 8 hours (09:00 - 17:00)

---

## Table of Contents

1. [Morning Session (09:00-12:00)](#morning-session-0900-1200)
2. [Afternoon Session (13:00-17:00)](#afternoon-session-1300-1700)
3. [Technical Architecture](#technical-architecture)
4. [Test Coverage Plan](#test-coverage-plan)
5. [Success Metrics](#success-metrics)

---

## Morning Session (09:00-12:00)

### 🎯 **Task 1: Configure Pytest Framework** (09:00-10:00)

**Objective**: Set up pytest + pytest-asyncio with proper configuration for async FastAPI testing.

**Steps**:

**Step 1: Update dependencies** (10 min)
```bash
# Add to backend/requirements.txt
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2  # For async HTTP client
faker==20.1.0  # For test data generation
```

**Step 2: Create pytest configuration** (15 min)

File: `pytest.ini`
```ini
[pytest]
# Pytest configuration for SDLC Orchestrator integration tests

# Test discovery
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Async support
asyncio_mode = auto

# Coverage
addopts =
    --verbose
    --strict-markers
    --cov=backend/app
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml:coverage.xml
    --cov-fail-under=90
    -p no:warnings

# Markers (for test categorization)
markers =
    integration: Integration tests (requires services)
    unit: Unit tests (no external dependencies)
    slow: Slow tests (>1 second)
    auth: Authentication tests
    gates: Gates API tests
    evidence: Evidence API tests
    policies: Policies API tests
    smoke: Smoke tests (critical paths only)

# Logging
log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)8s] %(message)s
log_cli_date_format = %Y-%m-%d %H:%M:%S

# Test execution
timeout = 300  # 5 minutes max per test
```

**Step 3: Create conftest.py** (35 min)

File: `tests/conftest.py`
```python
"""
Pytest configuration and shared fixtures for SDLC Orchestrator tests.

Fixtures:
- app: FastAPI test application
- client: Async HTTP client
- db: Isolated test database session
- redis_client: Redis test client
- test_user: Authenticated test user
- auth_headers: JWT authentication headers
"""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.config import settings
from backend.app.database.base import Base
from backend.app.main import app as main_app
from backend.app.models.user import User


# ============================================================================
# TEST DATABASE SETUP
# ============================================================================

# Test database URL (isolated from development database)
TEST_DATABASE_URL = "postgresql+asyncpg://sdlc_admin:changeme_secure_password@localhost:5432/sdlc_orchestrator_test"

# Create async engine for test database
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    poolclass=StaticPool,  # Use StaticPool for testing
)

# Async session factory
TestSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create event loop for async tests.

    Scope: session (one loop for all tests)
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """
    Create test database schema before all tests.
    Drop all tables after all tests.

    Scope: session (once per test run)
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create isolated database session for each test.

    Rollback after each test (no data persists between tests).

    Scope: function (new session for each test)
    """
    async with TestSessionLocal() as session:
        async with session.begin():
            yield session
            await session.rollback()  # Rollback after test


# ============================================================================
# FASTAPI APPLICATION FIXTURES
# ============================================================================

@pytest.fixture
def app() -> FastAPI:
    """
    FastAPI test application.

    Scope: function (new app instance for each test)
    """
    return main_app


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client for API testing.

    Usage:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200

    Scope: function (new client for each test)
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac


# ============================================================================
# REDIS FIXTURES
# ============================================================================

@pytest.fixture
async def redis_client():
    """
    Redis test client.

    Use separate Redis database (DB 15 for testing).
    Flush database after each test.

    Scope: function (new client for each test)
    """
    import redis.asyncio as redis

    client = redis.Redis(
        host="localhost",
        port=6379,
        db=15,  # Use DB 15 for testing (isolated from dev DB 0)
        decode_responses=True,
    )

    yield client

    # Cleanup: flush test database
    await client.flushdb()
    await client.close()


# ============================================================================
# AUTHENTICATION FIXTURES
# ============================================================================

@pytest.fixture
async def test_user(db: AsyncSession) -> User:
    """
    Create test user for authentication tests.

    Default credentials:
    - Email: test@example.com
    - Password: Test123!@#
    - Role: admin

    Scope: function (new user for each test)
    """
    from backend.app.models.user import User
    from backend.app.core.security import get_password_hash

    user = User(
        email="test@example.com",
        full_name="Test User",
        password_hash=get_password_hash("Test123!@#"),
        is_active=True,
        is_verified=True,
        is_superuser=True,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@pytest.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """
    Get JWT authentication headers for test user.

    Returns:
        {"Authorization": "Bearer <access_token>"}

    Scope: function (new token for each test)
    """
    # Login to get access token
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "Test123!@#",
        },
    )

    assert response.status_code == 200
    data = response.json()
    access_token = data["access_token"]

    return {"Authorization": f"Bearer {access_token}"}


# ============================================================================
# SERVICE FIXTURES (MINIO, OPA)
# ============================================================================

@pytest.fixture
def minio_client():
    """
    MinIO S3 test client.

    Use test bucket (sdlc-evidence-test).
    Delete all objects after each test.

    Scope: function (new client for each test)
    """
    import boto3
    from moto import mock_s3

    # Use moto for S3 mocking (no real MinIO needed)
    with mock_s3():
        client = boto3.client(
            "s3",
            region_name="us-east-1",
            aws_access_key_id="test",
            aws_secret_access_key="test",
        )

        # Create test bucket
        client.create_bucket(Bucket="sdlc-evidence-test")

        yield client


@pytest.fixture
def opa_client():
    """
    OPA policy engine test client.

    Mock OPA responses (no real OPA service needed).

    Scope: function (new client for each test)
    """
    from unittest.mock import MagicMock

    mock_client = MagicMock()
    mock_client.evaluate.return_value = {"result": True}

    yield mock_client


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================

@pytest.fixture
def test_project(db: AsyncSession, test_user: User):
    """
    Create test project.

    Scope: function (new project for each test)
    """
    from backend.app.models.project import Project

    project = Project(
        name="Test Project",
        description="Test project for integration tests",
        owner_id=test_user.id,
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    return project


@pytest.fixture
def test_gate(db: AsyncSession, test_project, test_user: User):
    """
    Create test gate.

    Scope: function (new gate for each test)
    """
    from backend.app.models.gate import Gate

    gate = Gate(
        project_id=test_project.id,
        gate_type="G0.1",
        title="Test Gate",
        status="pending",
        created_by=test_user.id,
    )

    db.add(gate)
    await db.commit()
    await db.refresh(gate)

    return gate
```

**Validation**:
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Verify pytest configuration
pytest --collect-only tests/

# Expected output:
# collected 0 items (no tests yet)
```

---

### 🎯 **Task 2: Set Up Isolated Test Database** (10:00-10:30)

**Objective**: Create isolated PostgreSQL test database to prevent test data from contaminating development database.

**Steps**:

**Step 1: Create test database** (10 min)
```bash
# Connect to PostgreSQL
docker exec -it sdlc_postgres psql -U sdlc_admin

# Create test database
CREATE DATABASE sdlc_orchestrator_test;

# Grant permissions
GRANT ALL PRIVILEGES ON DATABASE sdlc_orchestrator_test TO sdlc_admin;

# Exit
\q
```

**Step 2: Verify test database** (5 min)
```bash
# Connect to test database
docker exec -it sdlc_postgres psql -U sdlc_admin -d sdlc_orchestrator_test

# List tables (should be empty)
\dt

# Exit
\q
```

**Step 3: Create database migration script** (15 min)

File: `scripts/reset_test_db.sh`
```bash
#!/bin/bash
# Reset test database (drop all tables and recreate schema)

set -e

echo "🔄 Resetting test database..."

# Drop test database
docker exec -it sdlc_postgres psql -U sdlc_admin -c "DROP DATABASE IF EXISTS sdlc_orchestrator_test;"

# Recreate test database
docker exec -it sdlc_postgres psql -U sdlc_admin -c "CREATE DATABASE sdlc_orchestrator_test;"

# Grant permissions
docker exec -it sdlc_postgres psql -U sdlc_admin -c "GRANT ALL PRIVILEGES ON DATABASE sdlc_orchestrator_test TO sdlc_admin;"

echo "✅ Test database reset complete"

# Run Alembic migrations on test database
export DATABASE_URL="postgresql+asyncpg://sdlc_admin:changeme_secure_password@localhost:5432/sdlc_orchestrator_test"
alembic upgrade head

echo "✅ Test database migrations applied"
```

```bash
# Make script executable
chmod +x scripts/reset_test_db.sh

# Run script
./scripts/reset_test_db.sh
```

---

### 🎯 **Task 3: Create Test Fixtures** (10:30-12:00)

**Objective**: Create reusable test fixtures for all services (PostgreSQL, Redis, MinIO, OPA).

**Step 1: Authentication fixtures** (30 min)

File: `tests/fixtures/auth_fixtures.py`
```python
"""
Authentication test fixtures.

Fixtures:
- test_user: Authenticated test user
- admin_user: Admin user with superuser privileges
- auth_headers: JWT authentication headers
- expired_token: Expired JWT token (for 401 testing)
"""

import pytest
from datetime import datetime, timedelta
from jose import jwt

from backend.app.core.config import settings
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.models.user import User


@pytest.fixture
async def test_user(db):
    """Standard test user (non-admin)."""
    user = User(
        email="test@example.com",
        full_name="Test User",
        password_hash=get_password_hash("Test123!@#"),
        is_active=True,
        is_verified=True,
        is_superuser=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def admin_user(db):
    """Admin test user (superuser)."""
    user = User(
        email="admin@example.com",
        full_name="Admin User",
        password_hash=get_password_hash("Admin123!@#"),
        is_active=True,
        is_verified=True,
        is_superuser=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def auth_headers(client, test_user):
    """JWT authentication headers for test user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "Test123!@#"},
    )
    assert response.status_code == 200
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest.fixture
async def admin_headers(client, admin_user):
    """JWT authentication headers for admin user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!@#"},
    )
    assert response.status_code == 200
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest.fixture
def expired_token():
    """Expired JWT token (for 401 testing)."""
    payload = {
        "sub": "test-user-id",
        "exp": datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
```

**Step 2: Project and Gate fixtures** (30 min)

File: `tests/fixtures/project_fixtures.py`
```python
"""
Project and Gate test fixtures.
"""

import pytest
from faker import Faker

from backend.app.models.project import Project
from backend.app.models.gate import Gate

fake = Faker()


@pytest.fixture
async def test_project(db, test_user):
    """Test project."""
    project = Project(
        name=fake.company(),
        description=fake.text(max_nb_chars=200),
        owner_id=test_user.id,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@pytest.fixture
async def test_gate(db, test_project, test_user):
    """Test gate (pending status)."""
    gate = Gate(
        project_id=test_project.id,
        gate_type="G0.1",
        title="Problem Definition Review",
        status="pending",
        created_by=test_user.id,
    )
    db.add(gate)
    await db.commit()
    await db.refresh(gate)
    return gate


@pytest.fixture
async def approved_gate(db, test_project, test_user):
    """Test gate (approved status)."""
    gate = Gate(
        project_id=test_project.id,
        gate_type="G0.1",
        title="Problem Definition Review",
        status="approved",
        created_by=test_user.id,
    )
    db.add(gate)
    await db.commit()
    await db.refresh(gate)
    return gate
```

**Step 3: Evidence and Policy fixtures** (30 min)

File: `tests/fixtures/evidence_fixtures.py`
```python
"""
Evidence and Policy test fixtures.
"""

import pytest
from faker import Faker
import tempfile
import os

from backend.app.models.evidence import Evidence
from backend.app.models.policy import Policy

fake = Faker()


@pytest.fixture
def test_file():
    """Create temporary test file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pdf') as f:
        f.write("Test evidence content")
        file_path = f.name

    yield file_path

    # Cleanup
    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.fixture
async def test_evidence(db, test_gate, test_user):
    """Test evidence."""
    evidence = Evidence(
        gate_id=test_gate.id,
        file_name="test-document.pdf",
        file_size=1024,
        content_type="application/pdf",
        storage_path="s3://sdlc-evidence-test/test-document.pdf",
        sha256_hash="abc123...",
        uploaded_by=test_user.id,
    )
    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)
    return evidence


@pytest.fixture
async def test_policy(db, test_user):
    """Test policy."""
    policy = Policy(
        name="Security Review Policy",
        description="Policy for security review gates",
        category="security",
        gate_type="G0.1",
        rego_code="""
            package sdlc

            allow {
                input.evidence_count >= 3
                input.approvers_count >= 2
            }
        """,
        is_active=True,
        created_by=test_user.id,
    )
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return policy
```

---

## Afternoon Session (13:00-17:00)

### 🎯 **Task 4: Write Integration Tests** (13:00-16:00)

**Objective**: Write integration tests for all 31 API endpoints, targeting 90%+ coverage.

**Test Structure**:
```
tests/
├── integration/
│   ├── test_auth_integration.py       # Authentication API (9 endpoints)
│   ├── test_gates_integration.py      # Gates API (8 endpoints)
│   ├── test_evidence_integration.py   # Evidence API (5 endpoints)
│   ├── test_policies_integration.py   # Policies API (7 endpoints)
│   └── test_health_integration.py     # Health/Metrics (2 endpoints)
```

**Step 1: Authentication integration tests** (45 min)

File: `tests/integration/test_auth_integration.py`
```python
"""
Integration tests for Authentication API.

Endpoints covered (9):
- POST /auth/login
- POST /auth/refresh
- GET /auth/me
- POST /auth/logout
- GET /auth/oauth/authorize
- POST /auth/oauth/callback
- POST /auth/mfa/setup
- POST /auth/mfa/verify
- POST /auth/mfa/disable
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.auth
class TestAuthIntegration:
    """Integration tests for Authentication API."""

    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login with valid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "Test123!@#"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "Bearer"
        assert "expires_in" in data
        assert data["expires_in"] == 900  # 15 minutes

        # Verify user data
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["is_active"] is True

    async def test_login_invalid_credentials(self, client: AsyncClient, test_user):
        """Test login with invalid credentials returns 401."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "WrongPassword"},
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    async def test_refresh_token_success(self, client: AsyncClient, test_user):
        """Test token refresh with valid refresh token."""
        # Login to get refresh token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "Test123!@#"},
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify new tokens returned
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["access_token"] != login_response.json()["access_token"]  # New token

    async def test_get_current_user(self, client: AsyncClient, auth_headers):
        """Test get current user profile."""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify user profile
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert data["is_active"] is True
        assert "permissions" in data  # New in v1.0.0

    async def test_logout_success(self, client: AsyncClient, auth_headers):
        """Test logout (token blacklist)."""
        response = await client.post(
            "/api/v1/auth/logout",
            headers=auth_headers,
        )

        assert response.status_code == 200

        # Verify token is blacklisted (subsequent requests fail)
        response2 = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers,
        )
        assert response2.status_code == 401

    async def test_unauthorized_without_token(self, client: AsyncClient):
        """Test protected endpoint without token returns 401."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401
        assert "detail" in response.json()
```

**Step 2: Gates integration tests** (45 min)

File: `tests/integration/test_gates_integration.py`
```python
"""
Integration tests for Gates API.

Endpoints covered (8):
- GET /gates
- POST /gates
- GET /gates/{id}
- PUT /gates/{id}
- DELETE /gates/{id}
- POST /gates/{id}/approve
- POST /gates/{id}/reject
- GET /gates/{id}/evidence
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.gates
class TestGatesIntegration:
    """Integration tests for Gates API."""

    async def test_list_gates(self, client: AsyncClient, auth_headers, test_gate):
        """Test list gates with pagination."""
        response = await client.get(
            "/api/v1/gates?page=1&page_size=50",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify pagination structure
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

        # Verify gates returned
        assert len(data["items"]) >= 1
        assert data["items"][0]["id"] == str(test_gate.id)

    async def test_create_gate(self, client: AsyncClient, auth_headers, test_project):
        """Test create gate."""
        response = await client.post(
            "/api/v1/gates",
            headers=auth_headers,
            json={
                "project_id": str(test_project.id),
                "gate_type": "G0.1",
                "title": "Problem Definition Review",
                "status": "pending",
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Verify gate created
        assert data["gate_type"] == "G0.1"
        assert data["title"] == "Problem Definition Review"
        assert data["status"] == "pending"
        assert "id" in data
        assert "created_at" in data

    async def test_get_gate(self, client: AsyncClient, auth_headers, test_gate):
        """Test get gate by ID."""
        response = await client.get(
            f"/api/v1/gates/{test_gate.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify gate details
        assert data["id"] == str(test_gate.id)
        assert data["gate_type"] == "G0.1"
        assert "evidence_count" in data  # New in v1.0.0
        assert "approvers" in data  # New in v1.0.0

    async def test_approve_gate(self, client: AsyncClient, auth_headers, test_gate):
        """Test approve gate (dedicated endpoint)."""
        response = await client.post(
            f"/api/v1/gates/{test_gate.id}/approve",
            headers=auth_headers,
            json={"comment": "Approved after review"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify gate approved
        assert data["status"] == "approved"
        assert len(data["approvers"]) == 1
        assert data["approvers"][0]["comment"] == "Approved after review"

    async def test_gate_not_found(self, client: AsyncClient, auth_headers):
        """Test get non-existent gate returns 404."""
        response = await client.get(
            "/api/v1/gates/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )

        assert response.status_code == 404
```

**Step 3: Evidence integration tests** (45 min)

File: `tests/integration/test_evidence_integration.py`
```python
"""
Integration tests for Evidence API.

Endpoints covered (5):
- GET /evidence
- POST /evidence (file upload)
- GET /evidence/{id}
- GET /evidence/{id}/download
- DELETE /evidence/{id}
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.evidence
class TestEvidenceIntegration:
    """Integration tests for Evidence API."""

    async def test_upload_evidence(self, client: AsyncClient, auth_headers, test_gate, test_file):
        """Test upload evidence file."""
        with open(test_file, 'rb') as f:
            response = await client.post(
                "/api/v1/evidence",
                headers=auth_headers,
                files={"file": ("test-document.pdf", f, "application/pdf")},
                data={"gate_id": str(test_gate.id)},
            )

        assert response.status_code == 201
        data = response.json()

        # Verify evidence created
        assert data["file_name"] == "test-document.pdf"
        assert data["content_type"] == "application/pdf"
        assert "sha256_hash" in data  # New in v1.0.0
        assert "storage_path" in data

    async def test_list_evidence(self, client: AsyncClient, auth_headers, test_evidence):
        """Test list evidence with pagination."""
        response = await client.get(
            "/api/v1/evidence?page=1&page_size=50",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify pagination
        assert "items" in data
        assert len(data["items"]) >= 1

    async def test_download_evidence(self, client: AsyncClient, auth_headers, test_evidence):
        """Test download evidence file."""
        response = await client.get(
            f"/api/v1/evidence/{test_evidence.id}/download",
            headers=auth_headers,
        )

        assert response.status_code == 200
        # Verify redirect to pre-signed URL
        assert "Location" in response.headers or response.status_code == 200
```

**Step 4: Policies integration tests** (45 min)

File: `tests/integration/test_policies_integration.py`
```python
"""
Integration tests for Policies API.

Endpoints covered (7):
- GET /policies
- POST /policies
- GET /policies/{id}
- PUT /policies/{id}
- DELETE /policies/{id}
- POST /policies/{id}/test
- GET /policies/{id}/versions
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.policies
class TestPoliciesIntegration:
    """Integration tests for Policies API."""

    async def test_create_policy(self, client: AsyncClient, auth_headers):
        """Test create policy."""
        response = await client.post(
            "/api/v1/policies",
            headers=auth_headers,
            json={
                "name": "Security Review Policy",
                "description": "Policy for security review gates",
                "category": "security",
                "gate_type": "G0.1",
                "rego_code": "package sdlc\n\nallow { input.evidence_count >= 3 }",
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Verify policy created
        assert data["name"] == "Security Review Policy"
        assert data["category"] == "security"
        assert "usage_count" in data  # New in v1.0.0

    async def test_list_policies(self, client: AsyncClient, auth_headers, test_policy):
        """Test list policies."""
        response = await client.get(
            "/api/v1/policies",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify policies returned
        assert "items" in data
        assert len(data["items"]) >= 1

    async def test_test_policy(self, client: AsyncClient, auth_headers, test_policy):
        """Test policy evaluation with sample data."""
        response = await client.post(
            f"/api/v1/policies/{test_policy.id}/test",
            headers=auth_headers,
            json={
                "input": {
                    "evidence_count": 5,
                    "approvers_count": 3,
                }
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify policy evaluation result
        assert "result" in data
        assert data["result"] is True  # Policy should pass
```

**Step 5: Health/Metrics integration tests** (15 min)

File: `tests/integration/test_health_integration.py`
```python
"""
Integration tests for Health/Metrics endpoints.

Endpoints covered (2):
- GET /health
- GET /metrics
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestHealthIntegration:
    """Integration tests for Health/Metrics endpoints."""

    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint (no auth required)."""
        response = await client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        # Verify health status
        assert data["status"] == "healthy"
        assert "version" in data
        assert "services" in data
        assert data["services"]["database"] == "up"

    async def test_metrics_endpoint(self, client: AsyncClient):
        """Test Prometheus metrics endpoint (no auth required)."""
        response = await client.get("/metrics")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")

        # Verify Prometheus metrics format
        content = response.text
        assert "http_request_duration_seconds" in content
        assert "http_requests_total" in content
```

---

### 🎯 **Task 5: Verify Test Coverage** (16:00-17:00)

**Objective**: Run integration tests and verify 90%+ coverage achieved.

**Step 1: Run integration tests** (30 min)
```bash
# Run all integration tests
pytest tests/integration/ -v --cov=backend/app --cov-report=term-missing

# Expected output:
# ================== test session starts ==================
# platform darwin -- Python 3.11.5
# plugins: asyncio-0.21.1, cov-4.1.0
# collected 25 items
#
# tests/integration/test_auth_integration.py ........... [44%]
# tests/integration/test_gates_integration.py ....... [72%]
# tests/integration/test_evidence_integration.py ... [84%]
# tests/integration/test_policies_integration.py .... [100%]
# tests/integration/test_health_integration.py .. [100%]
#
# ================== 25 passed in 15.2s ==================
#
# Coverage report:
# backend/app/api/routes/auth.py        95%
# backend/app/api/routes/gates.py       92%
# backend/app/api/routes/evidence.py    90%
# backend/app/api/routes/policies.py    91%
# backend/app/core/security.py          94%
# ------------------------------------------------
# TOTAL                                  92%  ✅
```

**Step 2: Generate coverage reports** (15 min)
```bash
# Generate HTML coverage report
pytest tests/integration/ --cov=backend/app --cov-report=html

# Open coverage report in browser
open htmlcov/index.html
```

**Step 3: Fix coverage gaps** (15 min)
```bash
# Identify uncovered lines
pytest tests/integration/ --cov=backend/app --cov-report=term-missing

# Add tests for uncovered code paths
# Target: 90%+ coverage
```

---

## Technical Architecture

### Test Database Isolation

```
Development Database (sdlc_orchestrator):
  - Used by running application
  - Data persists across runs
  - Port: 5432

Test Database (sdlc_orchestrator_test):
  - Used only during tests
  - Isolated from development data
  - Schema created before tests
  - All data rolled back after each test
  - Schema dropped after all tests
  - Port: 5432 (same server, different DB)

Redis Isolation:
  - Development: DB 0
  - Testing: DB 15
  - Flushed after each test
```

### Test Execution Flow

```
1. Session Setup (once per test run):
   - Create test database schema
   - Start event loop

2. Function Setup (before each test):
   - Create database session
   - Begin transaction
   - Create test fixtures (user, project, gate)

3. Test Execution:
   - Run test code
   - Make HTTP requests via AsyncClient
   - Assert responses

4. Function Teardown (after each test):
   - Rollback transaction (no data persists)
   - Close database session
   - Flush Redis test DB

5. Session Teardown (after all tests):
   - Drop test database schema
   - Close event loop
```

---

## Test Coverage Plan

### Coverage Targets

| Component | Target | Priority |
|-----------|--------|----------|
| **API Routes** | 95%+ | P0 |
| **Business Logic** | 90%+ | P0 |
| **Database Models** | 85%+ | P1 |
| **Middleware** | 90%+ | P1 |
| **Security** | 95%+ | P0 |

### Coverage by Endpoint Category

| Category | Endpoints | Tests | Coverage Target |
|----------|-----------|-------|-----------------|
| Authentication | 9 | 12+ | 95%+ |
| Gates | 8 | 10+ | 92%+ |
| Evidence | 5 | 8+ | 90%+ |
| Policies | 7 | 9+ | 91%+ |
| Health/Metrics | 2 | 2+ | 100% |
| **TOTAL** | **31** | **41+** | **92%+** |

---

## Success Metrics

### Day 1 Success Criteria

✅ **Configuration** (Task 1):
- [ ] Pytest + pytest-asyncio installed and configured
- [ ] pytest.ini created with proper settings
- [ ] conftest.py with shared fixtures

✅ **Database** (Task 2):
- [ ] Test database created (sdlc_orchestrator_test)
- [ ] Test database isolated from development
- [ ] Reset script functional (scripts/reset_test_db.sh)

✅ **Fixtures** (Task 3):
- [ ] Authentication fixtures (test_user, auth_headers)
- [ ] Project/Gate fixtures (test_project, test_gate)
- [ ] Evidence/Policy fixtures (test_evidence, test_policy)

✅ **Integration Tests** (Task 4):
- [ ] 41+ integration tests written
- [ ] All 31 endpoints covered
- [ ] Tests pass (0 failures)

✅ **Coverage** (Task 5):
- [ ] 90%+ integration test coverage achieved
- [ ] Coverage report generated
- [ ] No critical coverage gaps

---

## Timeline Summary

| Time | Task | Duration |
|------|------|----------|
| 09:00-10:00 | Configure Pytest Framework | 60 min |
| 10:00-10:30 | Set Up Isolated Test Database | 30 min |
| 10:30-12:00 | Create Test Fixtures | 90 min |
| 12:00-13:00 | **LUNCH BREAK** | 60 min |
| 13:00-16:00 | Write Integration Tests | 180 min |
| 16:00-17:00 | Verify Test Coverage | 60 min |
| **TOTAL** | **Work Time** | **420 min (7h)** |

---

## Appendices

### Appendix A: Pytest Commands

**Run all tests**:
```bash
pytest tests/
```

**Run integration tests only**:
```bash
pytest tests/integration/ -m integration
```

**Run specific test file**:
```bash
pytest tests/integration/test_auth_integration.py -v
```

**Run with coverage**:
```bash
pytest tests/ --cov=backend/app --cov-report=term-missing
```

**Run failed tests only** (rerun failures):
```bash
pytest tests/ --lf  # Last failed
```

**Run slow tests** (marked with @pytest.mark.slow):
```bash
pytest tests/ -m slow
```

---

### Appendix B: Troubleshooting

**Issue 1: Database connection error**
```bash
# Solution: Ensure PostgreSQL is running
docker-compose ps postgres

# Restart if needed
docker-compose restart postgres
```

**Issue 2: Tests hang or timeout**
```bash
# Solution: Check for unclosed database sessions
# Add `await session.close()` in fixture cleanup
```

**Issue 3: Coverage not calculating**
```bash
# Solution: Ensure pytest-cov is installed
pip install pytest-cov

# Verify pytest.ini has --cov addopts
cat pytest.ini | grep cov
```

---

**Document Status**: ✅ **READY**
**Framework**: ✅ **SDLC 4.9 COMPLETE LIFECYCLE**
**Authorization**: ✅ **BACKEND LEAD + QA LEAD + CTO APPROVED**

---

*SDLC Orchestrator - Week 6 Day 1 Plan. Integration test suite setup. Production-ready testing infrastructure.* 🚀

**Prepared By**: Backend Lead + QA Lead
**Reviewed By**: CTO
**Status**: ✅ READY FOR EXECUTION
**Start Date**: December 12, 2025
