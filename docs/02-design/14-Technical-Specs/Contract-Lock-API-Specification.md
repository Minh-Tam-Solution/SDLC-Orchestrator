# Contract Lock API Specification

**Sprint**: 53
**Version**: 1.0.0
**Date**: December 25, 2025
**Status**: DRAFT - Pending CTO Approval
**Authority**: Backend Team
**Priority**: P0 - Core Feature

---

## 1. Overview

### 1.1 Purpose

Contract Lock ensures **spec immutability** during code generation. When a user locks their AppBlueprint specification:

1. A SHA256 hash is calculated and stored
2. The specification becomes read-only
3. Code generation can proceed with guaranteed consistency
4. Any modification attempt is blocked until unlock

### 1.2 Problem Statement

**Without Contract Lock**:
- User modifies blueprint during generation
- Generated code becomes inconsistent with modified spec
- Partial generation with mismatched expectations
- No audit trail of what spec was used for generation

**With Contract Lock**:
- Spec is frozen at generation start
- Hash verification ensures consistency
- Clear audit trail (who locked, when, what hash)
- Automatic unlock on successful completion

### 1.3 Key Metrics

| Metric | Target |
|--------|--------|
| Lock operation latency | <100ms |
| Hash calculation time (10KB spec) | <10ms |
| Hash collision probability | <10^-38 (SHA256) |
| Lock state consistency | 100% |

---

## 2. API Endpoints

### 2.1 Lock Specification

**Endpoint**: `POST /api/v1/onboarding/{id}/lock`

**Purpose**: Lock the AppBlueprint specification, making it immutable until unlock.

**Request**:
```http
POST /api/v1/onboarding/550e8400-e29b-41d4-a716-446655440000/lock HTTP/1.1
Host: api.sdlc-orchestrator.dev
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{}
```

**Response (200 OK)**:
```json
{
  "locked": true,
  "spec_hash": "sha256:a7f3c2d1e5b4f6a8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
  "locked_at": "2025-12-26T10:00:00.000Z",
  "locked_by": "user-uuid-123",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses**:

| Status | Code | Description |
|--------|------|-------------|
| 400 | ALREADY_LOCKED | Spec is already locked |
| 401 | UNAUTHORIZED | Invalid or missing token |
| 403 | FORBIDDEN | User doesn't have permission to lock |
| 404 | NOT_FOUND | Onboarding session not found |
| 409 | GENERATION_IN_PROGRESS | Cannot lock during active generation |

**Error Response Example (400 ALREADY_LOCKED)**:
```json
{
  "error": {
    "code": "ALREADY_LOCKED",
    "message": "Specification is already locked",
    "details": {
      "locked_at": "2025-12-26T09:00:00.000Z",
      "locked_by": "other-user-uuid",
      "spec_hash": "sha256:..."
    }
  }
}
```

### 2.2 Unlock Specification

**Endpoint**: `POST /api/v1/onboarding/{id}/unlock`

**Purpose**: Unlock the AppBlueprint specification, allowing modifications again.

**Request**:
```http
POST /api/v1/onboarding/550e8400-e29b-41d4-a716-446655440000/unlock HTTP/1.1
Host: api.sdlc-orchestrator.dev
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "unlock_reason": "Generation completed successfully"
}
```

**Unlock Reasons** (enum):
- `generation_completed` - Automatic unlock after successful generation
- `generation_failed` - Manual unlock after failed generation
- `manual_unlock` - User explicitly requested unlock
- `timeout` - Lock expired (after 1 hour of inactivity)
- `admin_override` - Admin forced unlock

**Response (200 OK)**:
```json
{
  "locked": false,
  "unlocked_at": "2025-12-26T10:30:00.000Z",
  "unlocked_by": "user-uuid-123",
  "unlock_reason": "generation_completed",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses**:

| Status | Code | Description |
|--------|------|-------------|
| 400 | NOT_LOCKED | Spec is not currently locked |
| 401 | UNAUTHORIZED | Invalid or missing token |
| 403 | FORBIDDEN | Only the user who locked can unlock (or admin) |
| 404 | NOT_FOUND | Onboarding session not found |
| 409 | GENERATION_IN_PROGRESS | Cannot unlock during active generation |

### 2.3 Get Lock Status

**Endpoint**: `GET /api/v1/onboarding/{id}/status`

**Purpose**: Get current lock status and generation status of an onboarding session.

**Request**:
```http
GET /api/v1/onboarding/550e8400-e29b-41d4-a716-446655440000/status HTTP/1.1
Host: api.sdlc-orchestrator.dev
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "pho24_restaurant",
  "version": "1.0.0",
  "business_domain": "restaurant",
  "locked": true,
  "spec_hash": "sha256:a7f3c2d1e5b4f6a8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
  "locked_at": "2025-12-26T10:00:00.000Z",
  "locked_by": "user-uuid-123",
  "lock_expires_at": "2025-12-26T11:00:00.000Z",
  "generation_status": "in_progress",
  "generation_progress": {
    "files_completed": 5,
    "total_files_estimated": 15,
    "current_file": "app/models/menu.py",
    "started_at": "2025-12-26T10:05:00.000Z"
  },
  "last_generation": {
    "session_id": "gen-session-123",
    "status": "completed",
    "completed_at": "2025-12-26T09:30:00.000Z",
    "total_files": 12,
    "total_lines": 450
  }
}
```

### 2.4 Verify Hash (Internal)

**Endpoint**: `POST /api/v1/onboarding/{id}/verify-hash`

**Purpose**: Verify that the current spec matches the locked hash. Used internally before generation.

**Request**:
```http
POST /api/v1/onboarding/550e8400-e29b-41d4-a716-446655440000/verify-hash HTTP/1.1
Host: api.sdlc-orchestrator.dev
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "expected_hash": "sha256:a7f3c2d1e5b4f6a8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
}
```

**Response (200 OK - Match)**:
```json
{
  "verified": true,
  "current_hash": "sha256:a7f3c2d1e5b4f6a8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
  "expected_hash": "sha256:a7f3c2d1e5b4f6a8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
}
```

**Response (409 Conflict - Mismatch)**:
```json
{
  "error": {
    "code": "HASH_MISMATCH",
    "message": "Specification has been modified since locking",
    "details": {
      "current_hash": "sha256:different_hash...",
      "expected_hash": "sha256:a7f3c2d1e5b4f6a8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
      "recommendation": "Re-lock the specification before generation"
    }
  }
}
```

---

## 3. Data Models

### 3.1 Database Schema

```sql
-- Table: onboarding_sessions (existing, with new columns)
ALTER TABLE onboarding_sessions ADD COLUMN IF NOT EXISTS spec_hash VARCHAR(256);
ALTER TABLE onboarding_sessions ADD COLUMN IF NOT EXISTS locked BOOLEAN DEFAULT FALSE;
ALTER TABLE onboarding_sessions ADD COLUMN IF NOT EXISTS locked_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE onboarding_sessions ADD COLUMN IF NOT EXISTS locked_by UUID REFERENCES users(id);
ALTER TABLE onboarding_sessions ADD COLUMN IF NOT EXISTS lock_expires_at TIMESTAMP WITH TIME ZONE;

-- Index for efficient lock status queries
CREATE INDEX IF NOT EXISTS idx_onboarding_locked ON onboarding_sessions(locked);
CREATE INDEX IF NOT EXISTS idx_onboarding_lock_expires ON onboarding_sessions(lock_expires_at) WHERE locked = true;

-- Table: lock_audit_log (new)
CREATE TABLE IF NOT EXISTS lock_audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  onboarding_session_id UUID NOT NULL REFERENCES onboarding_sessions(id) ON DELETE CASCADE,
  action VARCHAR(20) NOT NULL,  -- 'lock', 'unlock', 'auto_unlock', 'force_unlock'
  actor_id UUID NOT NULL REFERENCES users(id),
  spec_hash VARCHAR(256),
  reason VARCHAR(500),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_lock_audit_session ON lock_audit_log(onboarding_session_id);
CREATE INDEX idx_lock_audit_created ON lock_audit_log(created_at);
```

### 3.2 SQLAlchemy Model

```python
# backend/app/models/onboarding.py

from sqlalchemy import Boolean, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from typing import Optional
import uuid

class OnboardingSession(Base):
    __tablename__ = "onboarding_sessions"

    # ... existing fields ...

    # Contract Lock fields (Sprint 53)
    spec_hash: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
        comment="SHA256 hash of the AppBlueprint JSON when locked"
    )
    locked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        comment="Whether the spec is currently locked"
    )
    locked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when spec was locked"
    )
    locked_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        comment="User who locked the spec"
    )
    lock_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the lock automatically expires (1 hour default)"
    )

    # Relationships
    locked_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[locked_by],
        back_populates="locked_sessions"
    )
    lock_audit_logs: Mapped[list["LockAuditLog"]] = relationship(
        "LockAuditLog",
        back_populates="onboarding_session",
        order_by="LockAuditLog.created_at.desc()"
    )

    # Indexes
    __table_args__ = (
        Index('idx_onboarding_lock_expires', 'lock_expires_at', postgresql_where=locked==True),
    )


class LockAuditLog(Base):
    """Audit log for lock/unlock operations."""
    __tablename__ = "lock_audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    onboarding_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("onboarding_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    action: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="lock, unlock, auto_unlock, force_unlock"
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    spec_hash: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True
    )
    reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        index=True
    )
    metadata: Mapped[dict] = mapped_column(
        JSONB,
        default=dict
    )

    # Relationships
    onboarding_session: Mapped["OnboardingSession"] = relationship(
        "OnboardingSession",
        back_populates="lock_audit_logs"
    )
    actor: Mapped["User"] = relationship("User")
```

### 3.3 Pydantic Schemas

```python
# backend/app/schemas/onboarding.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID


class SpecLockRequest(BaseModel):
    """Request to lock a specification. No body required."""
    pass


class SpecLockResponse(BaseModel):
    """Response after locking a specification."""
    locked: bool
    spec_hash: str = Field(..., pattern=r"^sha256:[a-f0-9]{64}$")
    locked_at: datetime
    locked_by: UUID
    session_id: UUID

    class Config:
        json_schema_extra = {
            "example": {
                "locked": True,
                "spec_hash": "sha256:a7f3c2d1e5b4f6a8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
                "locked_at": "2025-12-26T10:00:00.000Z",
                "locked_by": "550e8400-e29b-41d4-a716-446655440000",
                "session_id": "550e8400-e29b-41d4-a716-446655440001"
            }
        }


UnlockReason = Literal[
    "generation_completed",
    "generation_failed",
    "manual_unlock",
    "timeout",
    "admin_override"
]


class SpecUnlockRequest(BaseModel):
    """Request to unlock a specification."""
    unlock_reason: UnlockReason = Field(
        ...,
        description="Reason for unlocking the specification"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "unlock_reason": "generation_completed"
            }
        }


class SpecUnlockResponse(BaseModel):
    """Response after unlocking a specification."""
    locked: bool
    unlocked_at: datetime
    unlocked_by: UUID
    unlock_reason: UnlockReason
    session_id: UUID


class GenerationProgress(BaseModel):
    """Current generation progress."""
    files_completed: int = Field(..., ge=0)
    total_files_estimated: int = Field(..., ge=0)
    current_file: Optional[str] = None
    started_at: datetime


class LastGeneration(BaseModel):
    """Summary of last completed generation."""
    session_id: str
    status: Literal["completed", "failed", "cancelled"]
    completed_at: datetime
    total_files: int
    total_lines: int


class OnboardingStatusResponse(BaseModel):
    """Full status of an onboarding session with lock info."""
    id: UUID
    name: str
    version: str
    business_domain: str
    locked: bool
    spec_hash: Optional[str] = None
    locked_at: Optional[datetime] = None
    locked_by: Optional[UUID] = None
    lock_expires_at: Optional[datetime] = None
    generation_status: Literal["idle", "in_progress", "completed", "failed"]
    generation_progress: Optional[GenerationProgress] = None
    last_generation: Optional[LastGeneration] = None


class HashVerifyRequest(BaseModel):
    """Request to verify spec hash."""
    expected_hash: str = Field(..., pattern=r"^sha256:[a-f0-9]{64}$")


class HashVerifyResponse(BaseModel):
    """Response for hash verification."""
    verified: bool
    current_hash: str
    expected_hash: str
```

---

## 4. Service Implementation

### 4.1 Contract Lock Service

```python
# backend/app/services/contract_lock_service.py

import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.onboarding import OnboardingSession, LockAuditLog
from app.schemas.onboarding import (
    SpecLockResponse,
    SpecUnlockResponse,
    OnboardingStatusResponse,
    HashVerifyResponse,
    UnlockReason
)
from app.core.exceptions import (
    AlreadyLockedError,
    NotLockedError,
    ForbiddenError,
    NotFoundError,
    GenerationInProgressError,
    HashMismatchError
)

# Lock expires after 1 hour of inactivity
LOCK_EXPIRY_HOURS = 1


class ContractLockService:
    """Service for managing contract spec locks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def lock(
        self,
        session_id: UUID,
        user_id: UUID
    ) -> SpecLockResponse:
        """
        Lock an onboarding session's specification.

        Args:
            session_id: The onboarding session to lock
            user_id: The user performing the lock

        Returns:
            SpecLockResponse with lock details

        Raises:
            NotFoundError: Session doesn't exist
            AlreadyLockedError: Session is already locked
            GenerationInProgressError: Generation is in progress
        """
        session = await self._get_session(session_id)

        if session.locked:
            raise AlreadyLockedError(
                session_id=session_id,
                locked_at=session.locked_at,
                locked_by=session.locked_by
            )

        # Check if generation is in progress
        if await self._is_generation_in_progress(session_id):
            raise GenerationInProgressError(session_id=session_id)

        # Calculate spec hash
        spec_json = json.dumps(session.app_blueprint, sort_keys=True, ensure_ascii=False)
        spec_hash = f"sha256:{hashlib.sha256(spec_json.encode()).hexdigest()}"

        # Lock the session
        now = datetime.utcnow()
        session.locked = True
        session.spec_hash = spec_hash
        session.locked_at = now
        session.locked_by = user_id
        session.lock_expires_at = now + timedelta(hours=LOCK_EXPIRY_HOURS)

        # Create audit log
        audit_log = LockAuditLog(
            onboarding_session_id=session_id,
            action="lock",
            actor_id=user_id,
            spec_hash=spec_hash,
            reason=None,
            metadata={"source": "api"}
        )
        self.db.add(audit_log)

        await self.db.commit()
        await self.db.refresh(session)

        return SpecLockResponse(
            locked=True,
            spec_hash=spec_hash,
            locked_at=session.locked_at,
            locked_by=user_id,
            session_id=session_id
        )

    async def unlock(
        self,
        session_id: UUID,
        user_id: UUID,
        reason: UnlockReason,
        is_admin: bool = False
    ) -> SpecUnlockResponse:
        """
        Unlock an onboarding session's specification.

        Args:
            session_id: The onboarding session to unlock
            user_id: The user performing the unlock
            reason: Reason for unlocking
            is_admin: Whether the user has admin privileges

        Returns:
            SpecUnlockResponse with unlock details

        Raises:
            NotFoundError: Session doesn't exist
            NotLockedError: Session is not locked
            ForbiddenError: User cannot unlock (not owner or admin)
            GenerationInProgressError: Generation is in progress
        """
        session = await self._get_session(session_id)

        if not session.locked:
            raise NotLockedError(session_id=session_id)

        # Check permission (owner or admin can unlock)
        if session.locked_by != user_id and not is_admin:
            raise ForbiddenError(
                message="Only the user who locked the spec or an admin can unlock",
                session_id=session_id
            )

        # Check if generation is in progress (unless admin override)
        if await self._is_generation_in_progress(session_id) and reason != "admin_override":
            raise GenerationInProgressError(session_id=session_id)

        # Unlock the session
        now = datetime.utcnow()
        old_hash = session.spec_hash
        session.locked = False
        session.spec_hash = None
        session.locked_at = None
        session.locked_by = None
        session.lock_expires_at = None

        # Create audit log
        audit_log = LockAuditLog(
            onboarding_session_id=session_id,
            action="unlock" if reason != "admin_override" else "force_unlock",
            actor_id=user_id,
            spec_hash=old_hash,
            reason=reason,
            metadata={"source": "api", "is_admin": is_admin}
        )
        self.db.add(audit_log)

        await self.db.commit()

        return SpecUnlockResponse(
            locked=False,
            unlocked_at=now,
            unlocked_by=user_id,
            unlock_reason=reason,
            session_id=session_id
        )

    async def get_status(self, session_id: UUID) -> OnboardingStatusResponse:
        """Get full status of an onboarding session including lock info."""
        session = await self._get_session(session_id)

        # Get generation status
        generation_status = await self._get_generation_status(session_id)
        generation_progress = None
        last_generation = None

        if generation_status == "in_progress":
            generation_progress = await self._get_generation_progress(session_id)
        else:
            last_generation = await self._get_last_generation(session_id)

        return OnboardingStatusResponse(
            id=session.id,
            name=session.app_blueprint.get("name", ""),
            version=session.app_blueprint.get("version", "1.0.0"),
            business_domain=session.app_blueprint.get("business_domain", ""),
            locked=session.locked,
            spec_hash=session.spec_hash,
            locked_at=session.locked_at,
            locked_by=session.locked_by,
            lock_expires_at=session.lock_expires_at,
            generation_status=generation_status,
            generation_progress=generation_progress,
            last_generation=last_generation
        )

    async def verify_hash(
        self,
        session_id: UUID,
        expected_hash: str
    ) -> HashVerifyResponse:
        """
        Verify that current spec matches expected hash.

        Used internally before code generation to ensure consistency.
        """
        session = await self._get_session(session_id)

        # Calculate current hash
        spec_json = json.dumps(session.app_blueprint, sort_keys=True, ensure_ascii=False)
        current_hash = f"sha256:{hashlib.sha256(spec_json.encode()).hexdigest()}"

        verified = current_hash == expected_hash

        if not verified:
            raise HashMismatchError(
                current_hash=current_hash,
                expected_hash=expected_hash,
                session_id=session_id
            )

        return HashVerifyResponse(
            verified=True,
            current_hash=current_hash,
            expected_hash=expected_hash
        )

    async def auto_unlock_expired(self) -> int:
        """
        Auto-unlock all expired locks.
        Should be called by a background job.

        Returns:
            Number of sessions unlocked
        """
        now = datetime.utcnow()
        stmt = select(OnboardingSession).where(
            OnboardingSession.locked == True,
            OnboardingSession.lock_expires_at < now
        )
        result = await self.db.execute(stmt)
        expired_sessions = result.scalars().all()

        count = 0
        for session in expired_sessions:
            await self.unlock(
                session_id=session.id,
                user_id=session.locked_by,  # Use original locker as actor
                reason="timeout",
                is_admin=True  # System action
            )
            count += 1

        return count

    # Private helper methods

    async def _get_session(self, session_id: UUID) -> OnboardingSession:
        """Get session by ID or raise NotFoundError."""
        stmt = select(OnboardingSession).where(OnboardingSession.id == session_id)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            raise NotFoundError(
                resource_type="OnboardingSession",
                resource_id=session_id
            )

        return session

    async def _is_generation_in_progress(self, session_id: UUID) -> bool:
        """Check if there's an active generation for this session."""
        # Query generation_sessions table for active status
        # This would depend on your generation tracking implementation
        return False  # Placeholder

    async def _get_generation_status(self, session_id: UUID) -> str:
        """Get current generation status."""
        # Query generation status from generation_sessions table
        return "idle"  # Placeholder

    async def _get_generation_progress(self, session_id: UUID):
        """Get current generation progress."""
        return None  # Placeholder

    async def _get_last_generation(self, session_id: UUID):
        """Get last completed generation summary."""
        return None  # Placeholder
```

### 4.2 Hash Calculation

```python
# backend/app/utils/hash.py

import hashlib
import json
from typing import Any, Dict


def calculate_spec_hash(blueprint: Dict[str, Any]) -> str:
    """
    Calculate SHA256 hash of an AppBlueprint.

    The blueprint is serialized to JSON with sorted keys and
    no ASCII escaping to ensure consistent hashing.

    Args:
        blueprint: The AppBlueprint dictionary

    Returns:
        Hash string in format "sha256:<64-char-hex>"
    """
    # Serialize with consistent ordering
    spec_json = json.dumps(
        blueprint,
        sort_keys=True,
        ensure_ascii=False,
        separators=(',', ':')  # No extra whitespace
    )

    # Calculate SHA256
    hash_bytes = hashlib.sha256(spec_json.encode('utf-8'))

    return f"sha256:{hash_bytes.hexdigest()}"


def verify_spec_hash(blueprint: Dict[str, Any], expected_hash: str) -> bool:
    """
    Verify that a blueprint matches an expected hash.

    Args:
        blueprint: The AppBlueprint dictionary
        expected_hash: Expected hash in format "sha256:<64-char-hex>"

    Returns:
        True if hash matches, False otherwise
    """
    current_hash = calculate_spec_hash(blueprint)
    return current_hash == expected_hash
```

---

## 5. API Routes

```python
# backend/app/api/routes/onboarding.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.contract_lock_service import ContractLockService
from app.schemas.onboarding import (
    SpecLockRequest,
    SpecLockResponse,
    SpecUnlockRequest,
    SpecUnlockResponse,
    OnboardingStatusResponse,
    HashVerifyRequest,
    HashVerifyResponse
)
from app.core.exceptions import (
    AlreadyLockedError,
    NotLockedError,
    ForbiddenError,
    NotFoundError,
    GenerationInProgressError,
    HashMismatchError
)

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.post(
    "/{session_id}/lock",
    response_model=SpecLockResponse,
    status_code=status.HTTP_200_OK,
    summary="Lock contract specification",
    description="Lock the AppBlueprint specification to prevent modifications during generation."
)
async def lock_spec(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SpecLockResponse:
    """Lock a specification."""
    service = ContractLockService(db)

    try:
        return await service.lock(
            session_id=session_id,
            user_id=current_user.id
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": str(e)}
        )
    except AlreadyLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "ALREADY_LOCKED",
                "message": str(e),
                "details": {
                    "locked_at": e.locked_at.isoformat() if e.locked_at else None,
                    "locked_by": str(e.locked_by) if e.locked_by else None
                }
            }
        )
    except GenerationInProgressError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "GENERATION_IN_PROGRESS", "message": str(e)}
        )


@router.post(
    "/{session_id}/unlock",
    response_model=SpecUnlockResponse,
    status_code=status.HTTP_200_OK,
    summary="Unlock contract specification",
    description="Unlock the AppBlueprint specification to allow modifications."
)
async def unlock_spec(
    session_id: UUID,
    request: SpecUnlockRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SpecUnlockResponse:
    """Unlock a specification."""
    service = ContractLockService(db)

    try:
        return await service.unlock(
            session_id=session_id,
            user_id=current_user.id,
            reason=request.unlock_reason,
            is_admin=current_user.is_admin
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": str(e)}
        )
    except NotLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "NOT_LOCKED", "message": str(e)}
        )
    except ForbiddenError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": str(e)}
        )
    except GenerationInProgressError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "GENERATION_IN_PROGRESS", "message": str(e)}
        )


@router.get(
    "/{session_id}/status",
    response_model=OnboardingStatusResponse,
    summary="Get onboarding session status",
    description="Get full status including lock state and generation progress."
)
async def get_status(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> OnboardingStatusResponse:
    """Get session status."""
    service = ContractLockService(db)

    try:
        return await service.get_status(session_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": str(e)}
        )


@router.post(
    "/{session_id}/verify-hash",
    response_model=HashVerifyResponse,
    summary="Verify spec hash",
    description="Verify that current spec matches expected hash. Used before generation."
)
async def verify_hash(
    session_id: UUID,
    request: HashVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> HashVerifyResponse:
    """Verify spec hash."""
    service = ContractLockService(db)

    try:
        return await service.verify_hash(
            session_id=session_id,
            expected_hash=request.expected_hash
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": str(e)}
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "HASH_MISMATCH",
                "message": "Specification has been modified since locking",
                "details": {
                    "current_hash": e.current_hash,
                    "expected_hash": e.expected_hash,
                    "recommendation": "Re-lock the specification before generation"
                }
            }
        )
```

---

## 6. Testing

### 6.1 Unit Tests

```python
# backend/tests/services/test_contract_lock_service.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from app.services.contract_lock_service import ContractLockService
from app.core.exceptions import AlreadyLockedError, NotLockedError


class TestContractLockService:
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        return ContractLockService(mock_db)

    @pytest.mark.asyncio
    async def test_lock_success(self, service, mock_db):
        """Test successful lock operation."""
        session_id = uuid4()
        user_id = uuid4()

        # Mock session not locked
        mock_session = MagicMock()
        mock_session.locked = False
        mock_session.app_blueprint = {"name": "test", "version": "1.0.0"}

        # Setup mock
        service._get_session = AsyncMock(return_value=mock_session)
        service._is_generation_in_progress = AsyncMock(return_value=False)

        result = await service.lock(session_id, user_id)

        assert result.locked == True
        assert result.spec_hash.startswith("sha256:")
        assert len(result.spec_hash) == 71  # "sha256:" + 64 hex chars

    @pytest.mark.asyncio
    async def test_lock_already_locked(self, service):
        """Test lock fails when already locked."""
        session_id = uuid4()
        user_id = uuid4()

        # Mock session already locked
        mock_session = MagicMock()
        mock_session.locked = True
        mock_session.locked_at = datetime.utcnow()
        mock_session.locked_by = uuid4()

        service._get_session = AsyncMock(return_value=mock_session)

        with pytest.raises(AlreadyLockedError):
            await service.lock(session_id, user_id)

    @pytest.mark.asyncio
    async def test_unlock_success(self, service, mock_db):
        """Test successful unlock operation."""
        session_id = uuid4()
        user_id = uuid4()

        # Mock session locked by same user
        mock_session = MagicMock()
        mock_session.locked = True
        mock_session.locked_by = user_id
        mock_session.spec_hash = "sha256:abc123..."

        service._get_session = AsyncMock(return_value=mock_session)
        service._is_generation_in_progress = AsyncMock(return_value=False)

        result = await service.unlock(session_id, user_id, "manual_unlock")

        assert result.locked == False
        assert result.unlock_reason == "manual_unlock"

    @pytest.mark.asyncio
    async def test_unlock_not_locked(self, service):
        """Test unlock fails when not locked."""
        session_id = uuid4()
        user_id = uuid4()

        mock_session = MagicMock()
        mock_session.locked = False

        service._get_session = AsyncMock(return_value=mock_session)

        with pytest.raises(NotLockedError):
            await service.unlock(session_id, user_id, "manual_unlock")


class TestHashCalculation:
    def test_consistent_hash(self):
        """Test that same blueprint produces same hash."""
        from app.utils.hash import calculate_spec_hash

        blueprint = {"name": "test", "modules": [{"name": "a"}, {"name": "b"}]}

        hash1 = calculate_spec_hash(blueprint)
        hash2 = calculate_spec_hash(blueprint)

        assert hash1 == hash2

    def test_different_content_different_hash(self):
        """Test that different blueprints produce different hashes."""
        from app.utils.hash import calculate_spec_hash

        blueprint1 = {"name": "test1"}
        blueprint2 = {"name": "test2"}

        hash1 = calculate_spec_hash(blueprint1)
        hash2 = calculate_spec_hash(blueprint2)

        assert hash1 != hash2

    def test_key_order_independent(self):
        """Test that key order doesn't affect hash."""
        from app.utils.hash import calculate_spec_hash

        blueprint1 = {"name": "test", "version": "1.0"}
        blueprint2 = {"version": "1.0", "name": "test"}

        hash1 = calculate_spec_hash(blueprint1)
        hash2 = calculate_spec_hash(blueprint2)

        assert hash1 == hash2
```

### 6.2 Integration Tests

```python
# backend/tests/api/test_contract_lock.py

import pytest
from httpx import AsyncClient
from uuid import uuid4

from app.main import app


class TestContractLockAPI:
    @pytest.fixture
    def auth_headers(self, valid_token):
        return {"Authorization": f"Bearer {valid_token}"}

    @pytest.mark.asyncio
    async def test_lock_unlock_flow(self, client: AsyncClient, auth_headers, test_session):
        """Test complete lock -> unlock flow."""
        # Lock
        response = await client.post(
            f"/api/v1/onboarding/{test_session.id}/lock",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["locked"] == True
        assert data["spec_hash"].startswith("sha256:")

        # Get status
        response = await client.get(
            f"/api/v1/onboarding/{test_session.id}/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["locked"] == True

        # Unlock
        response = await client.post(
            f"/api/v1/onboarding/{test_session.id}/unlock",
            headers=auth_headers,
            json={"unlock_reason": "manual_unlock"}
        )
        assert response.status_code == 200
        assert response.json()["locked"] == False

    @pytest.mark.asyncio
    async def test_lock_already_locked_error(self, client: AsyncClient, auth_headers, locked_session):
        """Test error when trying to lock already locked spec."""
        response = await client.post(
            f"/api/v1/onboarding/{locked_session.id}/lock",
            headers=auth_headers
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "ALREADY_LOCKED"
```

---

## 7. Alembic Migration

```python
# backend/alembic/versions/2025_12_26_add_contract_lock.py
"""Add contract lock fields to onboarding_sessions

Revision ID: 53a_contract_lock
Revises: 52_cli_magic_mode
Create Date: 2025-12-26 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '53a_contract_lock'
down_revision = '52_cli_magic_mode'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add contract lock columns to onboarding_sessions
    op.add_column(
        'onboarding_sessions',
        sa.Column('spec_hash', sa.String(256), nullable=True)
    )
    op.add_column(
        'onboarding_sessions',
        sa.Column('locked', sa.Boolean(), server_default='false', nullable=False)
    )
    op.add_column(
        'onboarding_sessions',
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        'onboarding_sessions',
        sa.Column('locked_by', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column(
        'onboarding_sessions',
        sa.Column('lock_expires_at', sa.DateTime(timezone=True), nullable=True)
    )

    # Add foreign key
    op.create_foreign_key(
        'fk_onboarding_locked_by_user',
        'onboarding_sessions',
        'users',
        ['locked_by'],
        ['id']
    )

    # Create indexes
    op.create_index(
        'idx_onboarding_locked',
        'onboarding_sessions',
        ['locked']
    )
    op.create_index(
        'idx_onboarding_lock_expires',
        'onboarding_sessions',
        ['lock_expires_at'],
        postgresql_where=sa.text('locked = true')
    )

    # Create lock_audit_log table
    op.create_table(
        'lock_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('onboarding_session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('spec_hash', sa.String(256), nullable=True),
        sa.Column('reason', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}', nullable=False),
        sa.ForeignKeyConstraint(['onboarding_session_id'], ['onboarding_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id']),
    )

    op.create_index('idx_lock_audit_session', 'lock_audit_log', ['onboarding_session_id'])
    op.create_index('idx_lock_audit_created', 'lock_audit_log', ['created_at'])


def downgrade() -> None:
    # Drop lock_audit_log table
    op.drop_index('idx_lock_audit_created')
    op.drop_index('idx_lock_audit_session')
    op.drop_table('lock_audit_log')

    # Drop indexes
    op.drop_index('idx_onboarding_lock_expires')
    op.drop_index('idx_onboarding_locked')

    # Drop foreign key
    op.drop_constraint('fk_onboarding_locked_by_user', 'onboarding_sessions', type_='foreignkey')

    # Drop columns
    op.drop_column('onboarding_sessions', 'lock_expires_at')
    op.drop_column('onboarding_sessions', 'locked_by')
    op.drop_column('onboarding_sessions', 'locked_at')
    op.drop_column('onboarding_sessions', 'locked')
    op.drop_column('onboarding_sessions', 'spec_hash')
```

---

## 8. Security Considerations

### 8.1 Authorization

- Only authenticated users can lock/unlock
- Only the user who locked can unlock (unless admin)
- Admin can force-unlock any spec
- Audit log tracks all actions

### 8.2 Hash Security

- SHA256 provides cryptographic security
- Collision probability is negligible (<10^-38)
- Hash is calculated server-side (no client trust)

### 8.3 Lock Expiry

- Locks auto-expire after 1 hour
- Background job cleans up expired locks
- Prevents orphaned locks from abandoned sessions

---

## 9. Success Criteria

- [ ] Lock operation latency <100ms
- [ ] Hash calculation <10ms for 10KB spec
- [ ] 100% hash verification accuracy
- [ ] Audit log captures all lock/unlock events
- [ ] Auto-unlock on generation complete
- [ ] Lock expiry prevents orphaned locks
- [ ] Integration tests pass 100%

---

**Document Status**: DRAFT
**Author**: AI Development Partner
**Reviewer**: CTO (Pending)
**Last Updated**: December 25, 2025
