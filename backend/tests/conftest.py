"""
=========================================================================
PyTest Configuration - Shared Test Fixtures
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: November 18, 2025
Status: ACTIVE - Week 3 Day 5 Integration Testing
Authority: Backend Lead + CTO Approved
Foundation: Week 3 Day 1-4 APIs (23 endpoints)
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- Shared test fixtures for integration tests
- Test database setup/teardown
- Authentication helpers (test users, JWT tokens)
- HTTP client configuration (httpx.AsyncClient)

Test Stack:
- pytest (test framework)
- pytest-asyncio (async test support)
- httpx (async HTTP client)
- SQLAlchemy Async (database fixtures)

Zero Mock Policy: Production-ready integration tests
=========================================================================
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.orm import configure_mappers

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
