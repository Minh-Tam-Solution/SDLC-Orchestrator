"""
=========================================================================
PyTest Configuration - Shared Test Fixtures
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.1.0
Date: February 3, 2026
Status: ACTIVE - Sprint 142 (Test Remediation)
Authority: Backend Lead + CTO Approved
Foundation: Week 3 Day 1-4 APIs (23 endpoints)
Framework: SDLC 6.0.5 (RFC-SDLC-602 E2E API Testing)

Purpose:
- Shared test fixtures for integration tests
- Test database setup/teardown
- Authentication helpers (test users, JWT tokens)
- HTTP client configuration (httpx.AsyncClient)
- External service mocking (Redis, MinIO, OPA)

Test Stack:
- pytest (test framework)
- pytest-asyncio (async test support)
- httpx (async HTTP client)
- SQLAlchemy Async (database fixtures)

Zero Mock Policy: Production-ready integration tests
Note: External service mocks are for TEST ISOLATION only (RA-003, RA-004)
=========================================================================
"""

# ============================================================================
# CRITICAL: Set test environment BEFORE any app imports
# This prevents socket.gaierror when services try to connect to Docker hostnames
# RA-003, RA-004: External Service Mocking (Sprint 142)
# ============================================================================
import os

# Set test environment variables BEFORE importing app modules
# These override Docker hostnames with localhost for CI/local testing
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://sdlc_user:changeme_secure_password@localhost:5432/sdlc_orchestrator_test")
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("OPA_URL", "http://localhost:8181")
os.environ.setdefault("OLLAMA_URL", "")  # Disable Ollama in tests
os.environ.setdefault("CODEGEN_OLLAMA_URL", "")  # Disable Codegen Ollama in tests
os.environ.setdefault("SMTP_HOST", "")  # Disable SMTP in tests

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.orm import configure_mappers

# Mock Redis BEFORE importing app modules that use it
# This prevents connection attempts during module import
_mock_redis_client = MagicMock()
_mock_redis_client.ping.return_value = True
_mock_redis_client.get.return_value = None
_mock_redis_client.set.return_value = True
_mock_redis_client.delete.return_value = 1
_mock_redis_client.expire.return_value = True
_mock_redis_client.incr.return_value = 1
_mock_redis_client.decr.return_value = 0
_mock_redis_client.exists.return_value = 0
_mock_redis_client.keys.return_value = []
_mock_redis_client.pipeline.return_value = MagicMock()

# Patch redis module BEFORE app imports
patch("app.core.redis.redis_client", _mock_redis_client).start()
patch("app.core.redis.get_redis_client", lambda: _mock_redis_client).start()

from app.core.config import settings
from app.db.base_class import Base
# Import all models FIRST to ensure SQLAlchemy configures all relationships
# before app.main imports modules that reference models
import app.models  # noqa: F401

# Configure all mappers to resolve forward references (like "ComplianceScore" in Project)
# This MUST be called after importing all models and before using any model relationships
configure_mappers()

from app.models import User, Role
from app.main import app
from app.core.security import get_password_hash


def _ensure_asyncpg_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    return url


# ============================================================================
# Database Test Fixtures
# ============================================================================

# Test database URL (separate from development database)
TEST_DATABASE_URL = _ensure_asyncpg_url(settings.DATABASE_URL).replace(
    "sdlc_orchestrator", "sdlc_orchestrator_test"
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a fresh test engine for each test function."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    yield engine
    await engine.dispose()


async def _drop_all_cascade(connection):
    """Drop all tables, views, and enum types with CASCADE for clean test state."""
    from sqlalchemy import text
    # Drop all views first
    await connection.execute(text("""
        DO $$ DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT viewname FROM pg_views WHERE schemaname = 'public') LOOP
                EXECUTE 'DROP VIEW IF EXISTS ' || quote_ident(r.viewname) || ' CASCADE';
            END LOOP;
        END $$;
    """))
    # Drop all tables with CASCADE (this also drops associated indexes and constraints)
    await connection.execute(text("""
        DO $$ DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename != 'alembic_version') LOOP
                EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
            END LOOP;
        END $$;
    """))
    # Drop all enum types (so we can recreate them fresh)
    await connection.execute(text("""
        DO $$ DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT typname FROM pg_type WHERE typnamespace = 'public'::regnamespace AND typtype = 'e') LOOP
                EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
            END LOOP;
        END $$;
    """))


async def _create_enum_types(connection):
    """Pre-create PostgreSQL ENUM types before table creation.

    SQLAlchemy's create_all in async mode doesn't reliably handle ENUM creation order.
    We manually create them here to ensure they exist before table creation.
    """
    from sqlalchemy import text

    # Define all enum types used in models (from app/models/subscription.py)
    enum_definitions = [
        ("subscription_plan_enum", ["free", "founder", "standard", "enterprise"]),
        ("subscription_status_enum", ["active", "canceled", "past_due"]),
        ("payment_status_enum", ["pending", "completed", "failed"]),
    ]

    for enum_name, enum_values in enum_definitions:
        # Check if enum already exists
        result = await connection.execute(text(
            "SELECT 1 FROM pg_type WHERE typname = :name"
        ), {"name": enum_name})
        exists = result.scalar() is not None

        if not exists:
            values_str = ", ".join(f"'{v}'" for v in enum_values)
            await connection.execute(text(
                f"CREATE TYPE {enum_name} AS ENUM ({values_str})"
            ))


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.

    Usage:
        async def test_example(db_session):
            user = User(email="test@example.com")
            db_session.add(user)
            await db_session.commit()
    """
    # Create session factory for this engine
    TestAsyncSessionLocal = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    # Drop all tables, views, and types with CASCADE
    async with test_engine.begin() as conn:
        await _drop_all_cascade(conn)
        # Pre-create PostgreSQL ENUM types before table creation
        await _create_enum_types(conn)
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    # Drop all tables after test
    async with test_engine.begin() as conn:
        await _drop_all_cascade(conn)


# Alias for backward compatibility - some tests use test_db_session
@pytest_asyncio.fixture(scope="function")
async def test_db_session(db_session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """Alias for db_session for backward compatibility."""
    yield db_session


# ============================================================================
# HTTP Client Fixture
# ============================================================================


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    HTTP client for API testing.

    Usage:
        async def test_endpoint(client):
            response = await client.get("/health")
            assert response.status_code == 200
    """
    from httpx import ASGITransport

    # Override database dependency
    from app.db.session import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Create HTTP client using ASGITransport (httpx 0.20+ API)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    # Remove overrides
    app.dependency_overrides.clear()


# Alias for backward compatibility - some tests use test_client
@pytest_asyncio.fixture(scope="function")
async def test_client(client: AsyncClient) -> AsyncGenerator[AsyncClient, None]:
    """Alias for client for backward compatibility."""
    yield client


# ============================================================================
# User & Authentication Fixtures
# ============================================================================


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """
    Create a test user with standard role.

    Usage:
        async def test_auth(test_user):
            assert test_user.email == "test@example.com"
            assert test_user.is_active == True
    """
    from uuid import uuid4

    # Create standard role
    role = Role(
        id=uuid4(),
        role_name="user",
        description="Standard user role for testing",
        permissions={"read": True, "write": False, "admin": False},
    )
    db_session.add(role)
    await db_session.flush()

    # Create test user
    user = User(
        id=uuid4(),
        email="test@example.com",
        full_name="Test User",
        password_hash=get_password_hash("password123"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture(scope="function")
async def test_admin(db_session: AsyncSession) -> User:
    """
    Create a test admin user.

    Usage:
        async def test_admin_endpoint(test_admin):
            assert test_admin.email == "admin@example.com"
    """
    from uuid import uuid4

    # Create admin role
    role = Role(
        id=uuid4(),
        role_name="admin",
        description="Admin role for testing",
        permissions={"read": True, "write": True, "admin": True},
    )
    db_session.add(role)
    await db_session.flush()

    # Create admin user
    user = User(
        id=uuid4(),
        email="admin@example.com",
        full_name="Admin User",
        password_hash=get_password_hash("admin123"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


# Alias for backward compatibility - some tests use admin_user
@pytest_asyncio.fixture(scope="function")
async def admin_user(test_admin: User) -> User:
    """Alias for test_admin for backward compatibility."""
    return test_admin


@pytest_asyncio.fixture(scope="function")
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """
    Get authentication headers for test user.

    Usage:
        async def test_protected_endpoint(client, auth_headers):
            response = await client.get("/api/v1/auth/me", headers=auth_headers)
            assert response.status_code == 200
    """
    # Login to get JWT token
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    access_token = data["access_token"]

    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture(scope="function")
async def admin_headers(client: AsyncClient, test_admin: User) -> dict:
    """
    Get authentication headers for admin user.

    Usage:
        async def test_admin_endpoint(client, admin_headers):
            response = await client.get("/api/v1/admin/users", headers=admin_headers)
            assert response.status_code == 200
    """
    # Login to get JWT token
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    assert response.status_code == 200
    data = response.json()
    access_token = data["access_token"]

    return {"Authorization": f"Bearer {access_token}"}


# ============================================================================
# Sample Data Fixtures
# ============================================================================


@pytest_asyncio.fixture(scope="function")
async def sample_gate(db_session: AsyncSession, test_user: User):
    """
    Create a sample gate for testing.

    Usage:
        async def test_gate_endpoint(client, auth_headers, sample_gate):
            response = await client.get(f"/api/v1/gates/{sample_gate.id}", headers=auth_headers)
            assert response.status_code == 200
    """
    from uuid import uuid4
    from app.models.gate import Gate

    gate = Gate(
        id=uuid4(),
        gate_number="G1",
        gate_name="Test Gate - Week 3 Day 5",
        stage="WHAT",
        description="Test gate for integration tests",
        status="IN_PROGRESS",
        created_by=test_user.id,
    )
    db_session.add(gate)
    await db_session.commit()
    await db_session.refresh(gate)

    return gate


@pytest_asyncio.fixture(scope="function")
async def sample_policy(db_session: AsyncSession):
    """
    Create a sample policy for testing.

    Usage:
        async def test_policy_endpoint(client, auth_headers, sample_policy):
            response = await client.get(f"/api/v1/policies/{sample_policy.id}", headers=auth_headers)
            assert response.status_code == 200
    """
    from uuid import uuid4
    from app.models.policy import Policy

    policy = Policy(
        id=uuid4(),
        policy_name="Test Policy - FRD Completeness",
        policy_code="FRD_COMPLETENESS",
        stage="WHAT",
        description="Test policy for integration tests",
        rego_code='package sdlc.what.frd_completeness\ndefault allow = false\nallow { input.complete == true }',
        severity="ERROR",
        is_active=True,
        version="1.0.0",
    )
    db_session.add(policy)
    await db_session.commit()
    await db_session.refresh(policy)

    return policy


# ============================================================================
# External Service Mock Fixtures (RA-003, RA-004 - Sprint 142)
# NOTE: These mocks are for TEST ISOLATION only. Production code uses real services.
# ============================================================================


@pytest.fixture(autouse=True)
def mock_redis():
    """
    Auto-mock Redis for all tests to prevent socket.gaierror.

    RA-003: Fix socket.gaierror in Auth Tests

    This fixture:
    - Mocks Redis client before each test
    - Prevents connection attempts to external Redis server
    - Provides sensible default return values

    Note: This is TEST ISOLATION, not production mocking.
    Zero Mock Policy applies to production code only.
    """
    from unittest.mock import MagicMock, patch

    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.setex.return_value = True
    mock_client.delete.return_value = 1
    mock_client.expire.return_value = True
    mock_client.incr.return_value = 1
    mock_client.decr.return_value = 0
    mock_client.exists.return_value = 0
    mock_client.keys.return_value = []
    mock_client.ttl.return_value = -2  # Key doesn't exist
    mock_client.close.return_value = None

    # Mock pipeline for batch operations
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = []
    mock_pipeline.__enter__ = MagicMock(return_value=mock_pipeline)
    mock_pipeline.__exit__ = MagicMock(return_value=False)
    mock_client.pipeline.return_value = mock_pipeline

    with patch("app.core.redis.redis_client", mock_client), \
         patch("app.core.redis.get_redis_client", return_value=mock_client):
        yield mock_client


@pytest.fixture(autouse=True)
def mock_email_service():
    """
    Auto-mock SMTP email service for all tests.

    RA-004: Mock External Service Connections

    This fixture:
    - Mocks smtplib.SMTP to prevent connection attempts
    - Captures sent emails for verification in tests
    - Prevents socket.gaierror on SMTP hostname resolution

    Note: This is TEST ISOLATION, not production mocking.
    """
    from unittest.mock import MagicMock, patch

    mock_smtp = MagicMock()
    mock_smtp_instance = MagicMock()
    mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_smtp_instance)
    mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
    mock_smtp_instance.sendmail.return_value = {}
    mock_smtp_instance.send_message.return_value = {}

    with patch("smtplib.SMTP", mock_smtp), \
         patch("smtplib.SMTP_SSL", mock_smtp):
        yield mock_smtp_instance


@pytest.fixture(autouse=True)
def mock_external_http():
    """
    Auto-mock external HTTP calls that might cause socket errors.

    RA-004: Mock External Service Connections

    This fixture:
    - Mocks httpx/requests for external calls (OPA, MinIO, Ollama)
    - Only mocks external hosts, not test server (testserver)
    - Prevents socket.gaierror on hostname resolution

    Note: This is TEST ISOLATION, not production mocking.
    """
    import httpx
    from unittest.mock import MagicMock, patch, AsyncMock

    original_request = httpx.AsyncClient.request

    async def mock_request(self, method, url, **kwargs):
        """Only mock requests to external services, not to testserver."""
        url_str = str(url)

        # Allow requests to test server
        if "testserver" in url_str or "127.0.0.1" in url_str:
            return await original_request(self, method, url, **kwargs)

        # Mock responses for external services
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": True, "allow": True}
        mock_response.text = '{"result": true}'
        mock_response.content = b'{"result": true}'
        mock_response.headers = {}
        mock_response.is_success = True
        mock_response.raise_for_status = MagicMock()

        return mock_response

    with patch.object(httpx.AsyncClient, "request", mock_request):
        yield


@pytest.fixture
def mock_opa_client():
    """
    Mock OPA client for policy evaluation tests.

    RA-004: Mock External Service Connections

    Usage:
        async def test_policy_evaluation(mock_opa_client):
            mock_opa_client.evaluate.return_value = {"result": True, "allow": True}
            # Test policy evaluation

    Note: This is TEST ISOLATION, not production mocking.
    """
    from unittest.mock import MagicMock, AsyncMock

    mock_client = MagicMock()
    mock_client.evaluate = AsyncMock(return_value={"result": True, "allow": True})
    mock_client.compile_policy = AsyncMock(return_value=True)
    mock_client.upload_policy = AsyncMock(return_value=True)
    mock_client.health_check = AsyncMock(return_value=True)

    return mock_client


@pytest.fixture
def mock_minio_client():
    """
    Mock MinIO client for evidence storage tests.

    RA-004: Mock External Service Connections

    Usage:
        async def test_evidence_upload(mock_minio_client):
            mock_minio_client.put_object.return_value = "object-etag"
            # Test evidence upload

    Note: This is TEST ISOLATION, not production mocking.
    """
    from unittest.mock import MagicMock, AsyncMock

    mock_client = MagicMock()
    mock_client.put_object = MagicMock(return_value="test-etag")
    mock_client.get_object = MagicMock(return_value=MagicMock(read=lambda: b"test content"))
    mock_client.stat_object = MagicMock(return_value=MagicMock(size=100, etag="test-etag"))
    mock_client.remove_object = MagicMock(return_value=None)
    mock_client.bucket_exists = MagicMock(return_value=True)
    mock_client.make_bucket = MagicMock(return_value=None)

    return mock_client
