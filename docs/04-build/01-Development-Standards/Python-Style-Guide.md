# Python Style Guide - Backend Development Standards

**Version**: 1.0.0
**Date**: November 13, 2025
**Status**: ACTIVE - MANDATORY ENFORCEMENT
**Authority**: Backend Lead + CTO Approved
**Foundation**: PEP 8, PEP 257, PEP 484 (Type Hints)
**Framework**: SDLC 5.1.3 Complete Lifecycle (10 Stages)

---

## 🎯 Purpose

This document defines the mandatory Python coding standards for the SDLC Orchestrator backend. All Python code must follow these conventions to ensure consistency, maintainability, and quality.

**Tech Stack**:
- Python 3.11+ (with latest language features)
- FastAPI 0.104+ (async web framework)
- SQLAlchemy 2.0+ (async ORM)
- Pydantic 2.0+ (data validation)
- pytest + pytest-asyncio (testing)

---

## 📏 Code Formatting

### Automated Tools (REQUIRED)

All code must pass these automated formatters before commit:

```bash
# Install development dependencies
pip install black ruff mypy pytest pytest-cov

# Format code (automatic)
black backend/app/

# Lint code (check for errors)
ruff check backend/app/

# Type check (strict mode)
mypy backend/app/

# Run tests with coverage
pytest --cov=app --cov-report=term-missing
```

**Pre-commit hook enforces these checks** - commits will be rejected if any tool fails.

---

### Black (Code Formatter)

```python
# Configuration: pyproject.toml
[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.venv
  | __pycache__
  | alembic/versions
)/
'''
```

**Line Length**: 100 characters (balance readability vs screen space)

**Example**:
```python
# ✅ GOOD - Black formatted
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Create new project with validation."""
    existing = await db.execute(
        select(Project).where(
            Project.name == project.name,
            Project.organization_id == current_user.organization_id,
        )
    )

# ❌ BAD - Inconsistent formatting
async def create_project(project: ProjectCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> ProjectResponse:
    existing = await db.execute(select(Project).where(Project.name == project.name, Project.organization_id == current_user.organization_id))
```

---

### Ruff (Linter)

```python
# Configuration: pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort (import sorting)
    "N",   # pep8-naming
    "UP",  # pyupgrade (modern Python syntax)
    "B",   # flake8-bugbear (bug detection)
    "C4",  # flake8-comprehensions
    "SIM", # flake8-simplify
]
ignore = [
    "E501",  # Line too long (handled by black)
    "B008",  # Function call in default argument (FastAPI Depends)
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports in __init__.py
"tests/**/*.py" = ["S101"]  # Allow assert in tests
```

**Example**:
```python
# ✅ GOOD - Ruff compliant
from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User

# ❌ BAD - Import order wrong, unused import
from app.models.user import User
import os  # Unused
from fastapi import Depends, HTTPException
from datetime import datetime
```

---

## 🔤 Naming Conventions (PEP 8)

### Variables and Functions

```python
# ✅ GOOD - snake_case for variables and functions
user_id = "550e8400-e29b-41d4-a716-446655440000"
access_token = create_access_token(subject=user_id)

async def get_current_user(token: str) -> User:
    """Retrieve user from JWT token."""
    pass

# ❌ BAD - camelCase (JavaScript style)
userId = "550e8400-e29b-41d4-a716-446655440000"
accessToken = createAccessToken(subject=userId)

async def getCurrentUser(token: str) -> User:
    pass
```

---

### Classes

```python
# ✅ GOOD - PascalCase for classes
class UserService:
    """Service for user management operations."""

    async def create_user(self, user_data: UserCreate) -> User:
        """Create new user."""
        pass


class ProjectRepository:
    """Repository for project database operations."""
    pass


# ❌ BAD - snake_case or camelCase for classes
class user_service:
    pass

class projectRepository:
    pass
```

---

### Constants

```python
# ✅ GOOD - UPPER_CASE for constants
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB
DEFAULT_PAGE_SIZE = 50
ALLOWED_FILE_TYPES = {"pdf", "png", "jpg", "txt", "md"}

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 1
REFRESH_TOKEN_EXPIRE_DAYS = 30

# ❌ BAD - lowercase or PascalCase for constants
max_upload_size = 100 * 1024 * 1024
MaxUploadSize = 100 * 1024 * 1024
```

---

### Private/Protected Methods

```python
# ✅ GOOD - Single underscore prefix for "internal use"
class UserService:
    def create_user(self, user_data: UserCreate) -> User:
        """Public method - create user."""
        hashed_password = self._hash_password(user_data.password)
        return self._save_to_db(user_data, hashed_password)

    def _hash_password(self, password: str) -> str:
        """Private method - hash password (internal use only)."""
        return get_password_hash(password)

    def _save_to_db(self, user_data: UserCreate, password_hash: str) -> User:
        """Private method - save to database (internal use only)."""
        pass


# ❌ BAD - No prefix for internal methods
class UserService:
    def create_user(self, user_data: UserCreate) -> User:
        hashed_password = self.hash_password(user_data.password)  # Looks public
        return self.save_to_db(user_data, hashed_password)

    def hash_password(self, password: str) -> str:  # Should be _hash_password
        return get_password_hash(password)
```

---

## 📝 Type Hints (PEP 484) - MANDATORY

**100% type hint coverage required** - enforced by mypy in strict mode.

### Function Signatures

```python
# ✅ GOOD - Complete type hints
from typing import Optional
from uuid import UUID

async def get_user_by_id(
    user_id: UUID,
    db: AsyncSession
) -> Optional[User]:
    """
    Retrieve user by ID.

    Args:
        user_id: User UUID
        db: Database session

    Returns:
        User object if found, None otherwise
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


# ❌ BAD - Missing type hints
async def get_user_by_id(user_id, db):
    """Retrieve user by ID."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()
```

---

### Modern Type Hints (Python 3.10+)

```python
# ✅ GOOD - Python 3.10+ union syntax
def authenticate_user(username: str, password: str, db: Session) -> User | None:
    """Authenticate user (returns User or None)."""
    pass


def get_projects(org_id: str) -> list[Project]:
    """Get all projects (returns list of Project)."""
    pass


def parse_config(data: dict[str, Any]) -> Config:
    """Parse config (dict with string keys, any values)."""
    pass


# ❌ BAD - Old-style Optional/List/Dict (Python 3.9)
from typing import Optional, List, Dict, Any

def authenticate_user(username: str, password: str, db: Session) -> Optional[User]:
    pass

def get_projects(org_id: str) -> List[Project]:
    pass

def parse_config(data: Dict[str, Any]) -> Config:
    pass
```

---

### Pydantic Models (Data Validation)

```python
# ✅ GOOD - Pydantic v2 with type hints
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID
from datetime import datetime


class UserCreate(BaseModel):
    """Request schema for creating a user."""

    email: EmailStr  # Validates email format
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="developer", pattern="^(developer|qa|devops|pm|tl|em|cto)$")


class UserResponse(BaseModel):
    """Response schema for user data (no password)."""

    model_config = ConfigDict(from_attributes=True)  # Pydantic v2

    id: UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: datetime | None


# ❌ BAD - Missing validation, no type hints
class UserCreate(BaseModel):
    email: str  # Should be EmailStr
    password: str  # Should have min_length validation
    full_name: str
    role: str  # Should validate allowed values
```

---

## 📚 Docstrings (Google Style) - MANDATORY

All public functions/classes must have docstrings. Use **Google style** (not NumPy or reStructuredText).

### Function Docstrings

```python
# ✅ GOOD - Complete Google-style docstring
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """
    Create new project for organization.

    Args:
        project: Project data from request body (name, description)
        current_user: Authenticated user from JWT token
        db: Database session from dependency injection

    Returns:
        ProjectResponse with created project details (id, name, created_at)

    Raises:
        HTTPException 409: If project name already exists in organization
        HTTPException 403: If user lacks permission to create projects

    Example:
        >>> project_data = ProjectCreate(name="SDLC Orchestrator", description="Governance platform")
        >>> result = await create_project(project_data, current_user, db)
        >>> result.name
        'SDLC Orchestrator'

    Note:
        Project names must be unique within organization (case-insensitive).
        Only users with 'em', 'cto', or 'ceo' roles can create projects.
    """
    # Implementation here
    pass


# ❌ BAD - Missing or incomplete docstring
async def create_project(project, current_user, db):
    """Create project."""  # Too brief, missing Args/Returns/Raises
    pass
```

---

### Class Docstrings

```python
# ✅ GOOD - Complete class docstring
class UserService:
    """
    Service layer for user management operations.

    This service handles user creation, authentication, password resets,
    and MFA enrollment. It encapsulates business logic and database operations.

    Attributes:
        db: Database session (SQLAlchemy AsyncSession)
        logger: Logger instance for audit trail

    Example:
        >>> service = UserService(db=db_session)
        >>> user = await service.create_user(user_data)
        >>> user.email
        'john@example.com'

    Note:
        All methods are async and require an active database session.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize user service.

        Args:
            db: Database session for user operations
        """
        self.db = db
        self.logger = logging.getLogger(__name__)


# ❌ BAD - Missing class docstring
class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
```

---

## 🏗️ Code Structure

### File Organization

```python
"""
User API Endpoints - Authentication & User Management

Version: 1.0.0
Date: November 13, 2025
Status: ACTIVE - STAGE 03 (BUILD)
Authority: Backend Lead + CTO Approved
Foundation: ADR-002 (Authentication Model)
Framework: SDLC 5.1.3 Complete Lifecycle
"""

# 1. Standard library imports
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

# 2. Third-party imports
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 3. Local application imports
from app.core.config import settings
from app.core.security import create_access_token, get_current_user, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse

# 4. Constants
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

# 5. Logger
logger = logging.getLogger(__name__)

# 6. Router
router = APIRouter(prefix="/api/v1/users", tags=["users"])


# 7. Endpoints (grouped by functionality)
@router.post("/login", response_model=UserResponse)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """User login endpoint."""
    pass
```

---

### Function Length

```python
# ✅ GOOD - Single responsibility, ~30 lines max
async def authenticate_user(
    username: str,
    password: str,
    db: AsyncSession
) -> User | None:
    """Authenticate user with username and password."""
    if not username or not password:
        return None

    user = await _get_user_by_username(username, db)
    if not user or not user.is_active:
        return None

    if not verify_password(password, user.password_hash):
        return None

    await _update_last_login(user, db)
    return user


async def _get_user_by_username(username: str, db: AsyncSession) -> User | None:
    """Retrieve user by username (internal helper)."""
    result = await db.execute(
        select(User).where(User.username == username.lower().strip())
    )
    return result.scalar_one_or_none()


async def _update_last_login(user: User, db: AsyncSession) -> None:
    """Update user's last login timestamp (internal helper)."""
    user.last_login = datetime.utcnow()
    await db.commit()


# ❌ BAD - Too long (100+ lines), doing too much
async def authenticate_user(username, password, db):
    """Authenticate user (plus password reset, MFA, session management, etc)."""
    # 100+ lines of mixed responsibilities
    pass
```

---

## 🔒 Error Handling

### FastAPI Exception Handling

```python
# ✅ GOOD - Specific HTTP exceptions with details
from fastapi import HTTPException, status

@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create new project."""
    # Check if project name exists
    existing = await db.execute(
        select(Project).where(
            Project.name == project.name,
            Project.organization_id == current_user.organization_id,
        )
    )

    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project '{project.name}' already exists in organization",
        )

    # Check user permission
    if current_user.role not in {"em", "cto", "ceo"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Engineering Manager, CTO, or CEO can create projects",
        )

    # Create project
    db_project = Project(
        name=project.name,
        description=project.description,
        owner_id=current_user.id,
        organization_id=current_user.organization_id,
    )

    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)

    logger.info(f"Project created: {db_project.id} by user {current_user.id}")
    return ProjectResponse.from_orm(db_project)


# ❌ BAD - Generic exceptions, no details
@router.post("/projects")
async def create_project(project, current_user, db):
    try:
        db_project = Project(**project.dict())
        db.add(db_project)
        await db.commit()
        return db_project
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error creating project")
```

---

### Try-Except Blocks

```python
# ✅ GOOD - Specific exception handling with logging
from sqlalchemy.exc import IntegrityError, DBAPIError

async def create_user(user_data: UserCreate, db: AsyncSession) -> User:
    """Create new user with error handling."""
    try:
        db_user = User(
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            full_name=user_data.full_name,
        )

        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        logger.info(f"User created: {db_user.id} ({db_user.email})")
        return db_user

    except IntegrityError as e:
        await db.rollback()
        logger.warning(f"User creation failed - duplicate email: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{user_data.email}' already exists",
        )

    except DBAPIError as e:
        await db.rollback()
        logger.error(f"Database error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error - please try again later",
        )


# ❌ BAD - Bare except, no logging
async def create_user(user_data, db):
    try:
        db_user = User(**user_data.dict())
        db.add(db_user)
        await db.commit()
        return db_user
    except:  # Don't catch all exceptions
        raise HTTPException(status_code=500, detail="Error")
```

---

## 🧪 Testing Standards

### pytest Conventions

```python
# tests/test_auth.py
"""
Unit tests for authentication module.

Tests password hashing, JWT token generation, and user authentication.
"""

import pytest
from datetime import datetime, timedelta

from app.core.security import (
    create_access_token,
    decode_token,
    get_password_hash,
    verify_password,
)


# ✅ GOOD - Descriptive test names, AAA pattern (Arrange-Act-Assert)
def test_password_hashing_creates_different_hashes_for_same_password():
    """Test that bcrypt generates unique hashes for the same password."""
    # Arrange
    password = "supersecret123"

    # Act
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)

    # Assert
    assert hash1 != hash2  # Different salts
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True


def test_password_verification_rejects_incorrect_password():
    """Test that password verification fails for wrong password."""
    # Arrange
    password = "correctpassword"
    wrong_password = "wrongpassword"
    hashed = get_password_hash(password)

    # Act
    result = verify_password(wrong_password, hashed)

    # Assert
    assert result is False


def test_jwt_token_contains_correct_claims():
    """Test that JWT access token includes exp, iat, sub, type claims."""
    # Arrange
    user_id = "550e8400-e29b-41d4-a716-446655440000"

    # Act
    token = create_access_token(subject=user_id)
    payload = decode_token(token)

    # Assert
    assert payload["sub"] == user_id
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload


# ❌ BAD - Vague test names, no AAA structure
def test_password():
    hash1 = get_password_hash("password")
    hash2 = get_password_hash("password")
    assert hash1 != hash2
```

---

### pytest Fixtures

```python
# tests/conftest.py
"""Shared pytest fixtures for all tests."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.base_class import Base
from app.models.user import User


@pytest.fixture
async def db_session() -> AsyncSession:
    """
    Create test database session.

    Yields:
        AsyncSession for test database

    Note:
        Database is rolled back after each test (no persistent data).
    """
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost/test_db")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """
    Create test user.

    Returns:
        User object for testing
    """
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        full_name="Test User",
        role="developer",
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user
```

---

## 🔗 References

### Internal References

- [Zero Mock Policy](./Zero-Mock-Policy.md) - No placeholder code allowed
- [Code Review Guidelines](../02-Code-Review/Code-Review-Guidelines.md) - PR review process
- [Testing Architecture](../03-Testing-Strategy/Testing-Architecture.md) - Test coverage targets

### External References

- [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 257 - Docstring Conventions](https://peps.python.org/pep-0257/)
- [PEP 484 - Type Hints](https://peps.python.org/pep-0484/)
- [Black Code Formatter](https://black.readthedocs.io/)
- [Ruff Linter](https://docs.astral.sh/ruff/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

---

**Last Updated**: November 13, 2025
**Owner**: Backend Lead + CTO
**Status**: ✅ ACTIVE - MANDATORY ENFORCEMENT
**Next Review**: Sprint retrospectives (weekly)
