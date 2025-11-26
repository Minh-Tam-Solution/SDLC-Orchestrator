"""
Pytest Configuration and Shared Fixtures

File: tests/conftest.py
Version: 1.0.0
Date: December 12, 2025
Status: ACTIVE - Week 6 Day 1
Authority: Backend Lead + QA Lead
Framework: SDLC 4.9 Complete Lifecycle

Fixtures:
- event_loop: Async event loop for pytest-asyncio
- setup_test_database: Create test database schema
- db: Isolated database session (rollback after each test)
- app: FastAPI test application
- client: Async HTTP client for API testing
- test_user: Authenticated test user
- admin_user: Admin user with superuser privileges
- auth_headers: JWT authentication headers
- admin_headers: Admin JWT authentication headers
- test_project: Test project fixture
- test_gate: Test gate fixture
- approved_gate: Approved gate fixture
- test_evidence: Test evidence fixture
- test_policy: Test policy fixture
- test_file: Uploaded file fixture
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import AsyncGenerator, Generator
from uuid import UUID, uuid4

# Add backend directory to Python path for imports
backend_path = os.path.join(os.path.dirname(__file__), "..", "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import pytest
import pytest_asyncio
from faker import Faker
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.base_class import Base
from app.main import app as main_app
from app.models.user import User
from app.models.project import Project
from app.models.gate import Gate
from app.models.gate_evidence import GateEvidence as Evidence
from app.models.policy import Policy

# Initialize Faker for test data generation
fake = Faker()

# Test database URL (isolated from development)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://sdlc_user:changeme_secure_password@localhost:5432/sdlc_orchestrator_test"
)

# Create async engine for tests (NullPool to avoid connection issues)
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# ============================================================================
# SESSION-SCOPED FIXTURES (Setup/Teardown)
# ============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create event loop for async tests.

    Scope: session (reuse across all tests)
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    """
    Create test database schema before all tests.
    Drop all tables after all tests complete.

    Scope: session (run once)
    Autouse: true (automatic execution)
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Drop all tables after tests complete
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create database session for each test.

    Note: We don't use transaction rollback strategy here because it conflicts
    with fixtures that need to commit data (test_user, test_project, etc.).
    Instead, we rely on the test database being recreated per test session.

    Yields:
        AsyncSession: Database session
    """
    async with TestSessionLocal() as session:
        yield session
        # Close session after test
        await session.close()


# ============================================================================
# APPLICATION FIXTURES
# ============================================================================

@pytest.fixture
def app() -> FastAPI:
    """
    FastAPI test application with test database dependency override.

    Override app's get_db() to use test database instead of production database.
    This ensures all API requests during tests use the same test database
    as the test fixtures.

    Returns:
        FastAPI: Test application instance with overridden dependencies
    """
    from app.db.session import get_db

    # Override get_db dependency to use test database
    async def get_test_db():
        async with TestSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    main_app.dependency_overrides[get_db] = get_test_db

    yield main_app

    # Clean up overrides after test
    main_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client for API testing.

    Args:
        app: FastAPI test application

    Yields:
        AsyncClient: Async HTTP client
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac


# ============================================================================
# USER FIXTURES
# ============================================================================

@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    """
    Create test user for authentication tests.

    Credentials:
        - Email: test@example.com
        - Password: Test123!@#
        - Role: Regular user (not admin)

    Args:
        db: Database session

    Returns:
        User: Test user object
    """
    # Check if user already exists (from previous test)
    result = await db.execute(
        text("SELECT id FROM users WHERE email = 'test@example.com'")
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        # Delete existing user to ensure clean state
        await db.execute(
            text("DELETE FROM users WHERE email = 'test@example.com'")
        )
        await db.commit()

    user = User(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
        password_hash=get_password_hash("Test123!@#"),
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession) -> User:
    """
    Create admin user with superuser privileges.

    Credentials:
        - Email: admin@example.com
        - Password: Admin123!@#
        - Role: Superuser (admin)

    Args:
        db: Database session

    Returns:
        User: Admin user object
    """
    # Check if admin already exists (from previous test)
    result = await db.execute(
        text("SELECT id FROM users WHERE email = 'admin@example.com'")
    )
    existing_admin = result.scalar_one_or_none()

    if existing_admin:
        # Delete existing admin to ensure clean state
        await db.execute(
            text("DELETE FROM users WHERE email = 'admin@example.com'")
        )
        await db.commit()

    user = User(
        id=uuid4(),
        email="admin@example.com",
        name="Admin User",
        password_hash=get_password_hash("Admin123!@#"),
        is_active=True,
        is_superuser=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# ============================================================================
# AUTHENTICATION FIXTURES
# ============================================================================

@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """
    Get JWT authentication headers for test user.

    Args:
        client: Async HTTP client
        test_user: Test user fixture

    Returns:
        dict: Authorization headers with Bearer token
    """
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "Test123!@#"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"

    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient, admin_user: User) -> dict:
    """
    Get JWT authentication headers for admin user.

    Args:
        client: Async HTTP client
        admin_user: Admin user fixture

    Returns:
        dict: Authorization headers with Bearer token (admin)
    """
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!@#"},
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"

    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest_asyncio.fixture
async def access_token(client: AsyncClient, test_user: User) -> str:
    """
    Get JWT access token string for test user (for simple sync tests).

    Args:
        client: Async HTTP client
        test_user: Test user fixture

    Returns:
        str: JWT access token string (without Bearer prefix)
    """
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "Test123!@#"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"

    data = response.json()
    return data['access_token']


# ============================================================================
# PROJECT FIXTURES
# ============================================================================

@pytest_asyncio.fixture
async def test_project(db: AsyncSession, test_user: User) -> Project:
    """
    Create test project for gate/evidence tests.

    Also creates ProjectMember to give test_user access to the project.
    This prevents 403 Forbidden errors when accessing gates/evidence.

    Args:
        db: Database session
        test_user: Test user fixture

    Returns:
        Project: Test project object (with user as member)
    """
    from app.models.project import ProjectMember

    project = Project(
        id=uuid4(),
        name="Test Project",
        slug="test-project",  # Required field (nullable=False)
        description="Integration test project",
        owner_id=test_user.id,
        is_active=True,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    # Add test_user as project member (owner role)
    # This allows test_user to access gates, evidence, etc.
    member = ProjectMember(
        id=uuid4(),
        project_id=project.id,
        user_id=test_user.id,
        role="owner",
        invited_by=test_user.id,
        joined_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db.add(member)
    await db.commit()

    return project


# ============================================================================
# GATE FIXTURES
# ============================================================================

@pytest_asyncio.fixture
async def test_gate(db: AsyncSession, test_project: Project) -> Gate:
    """
    Create test gate in PENDING status.

    Args:
        db: Database session
        test_project: Test project fixture

    Returns:
        Gate: Test gate object (PENDING)
    """
    gate = Gate(
        id=uuid4(),
        project_id=test_project.id,
        gate_name="Test Gate G1",
        gate_type="G1_DESIGN_READY",  # Required field
        stage="WHAT",  # Correct field name (not stage_name)
        status="PENDING",
        exit_criteria=[],  # Required field
        description="Test gate for integration testing",
    )
    db.add(gate)
    await db.commit()
    await db.refresh(gate)
    return gate


@pytest_asyncio.fixture
async def approved_gate(db: AsyncSession, test_project: Project) -> Gate:
    """
    Create approved gate for testing downstream flows.

    Args:
        db: Database session
        test_project: Test project fixture

    Returns:
        Gate: Test gate object (APPROVED)
    """
    gate = Gate(
        id=uuid4(),
        project_id=test_project.id,
        gate_name="Test Gate G0",
        gate_type="G0_PROBLEM_DEFINITION",  # Required field
        stage="WHY",  # Correct field name (not stage_name)
        status="APPROVED",
        exit_criteria=[],  # Required field
        description="Approved gate for testing",
    )
    db.add(gate)
    await db.commit()
    await db.refresh(gate)
    return gate


# ============================================================================
# EVIDENCE FIXTURES
# ============================================================================

@pytest_asyncio.fixture
async def test_evidence(db: AsyncSession, test_gate: Gate, test_user: User) -> Evidence:
    """
    Create test evidence attached to gate.

    Args:
        db: Database session
        test_gate: Test gate fixture
        test_user: Test user fixture

    Returns:
        Evidence: Test evidence object
    """
    evidence = Evidence(
        id=uuid4(),
        gate_id=test_gate.id,
        file_name="test_evidence.pdf",
        file_size=1024,
        file_type="application/pdf",
        evidence_type="DESIGN_DOCUMENT",
        s3_key="evidence/test-gate/test_evidence.pdf",
        s3_bucket="sdlc-evidence",
        sha256_hash="a" * 64,  # Valid SHA256 format
        description="Integration test evidence",
        uploaded_by=test_user.id,
    )
    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)
    return evidence


# ============================================================================
# POLICY FIXTURES
# ============================================================================

@pytest_asyncio.fixture
async def test_policy(db: AsyncSession) -> Policy:
    """
    Create test policy for gate evaluation.

    Args:
        db: Database session

    Returns:
        Policy: Test policy object
    """
    # Check if policy already exists (from previous test)
    result = await db.execute(
        text("SELECT id FROM policies WHERE policy_code = 'TEST_POLICY'")
    )
    existing_policy = result.scalar_one_or_none()

    if existing_policy:
        # Delete existing policy to ensure clean state
        await db.execute(
            text("DELETE FROM policies WHERE policy_code = 'TEST_POLICY'")
        )
        await db.commit()

    policy = Policy(
        id=uuid4(),
        policy_name="Test Policy",  # Correct field name (not 'name')
        policy_code="TEST_POLICY",  # Required field
        description="Integration test policy",
        stage="WHAT",  # Correct field name (not 'stage_name')
        rego_code="""
package test_policy

default allow = false

allow {
    input.gate.status == "PENDING"
}
        """,
        is_active=True,
    )
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return policy


# ============================================================================
# FILE UPLOAD FIXTURES
# ============================================================================

@pytest.fixture
def test_file() -> dict:
    """
    Create test file for upload endpoints.

    Returns:
        dict: File data for multipart upload
    """
    return {
        "filename": "test_document.pdf",
        "content": b"Test PDF content",
        "content_type": "application/pdf",
    }
