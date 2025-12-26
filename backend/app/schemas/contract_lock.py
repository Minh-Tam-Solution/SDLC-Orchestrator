"""
=========================================================================
Contract Lock Schemas - Sprint 53 Day 4
SDLC Orchestrator - Specification Immutability

Version: 1.0.0
Date: December 26, 2025
Status: ACTIVE - Sprint 53 Implementation
Authority: Backend Team + CTO Approved
Foundation: Contract-Lock-API-Specification.md

Purpose:
- Lock/unlock request/response schemas
- Hash verification schemas
- Onboarding status with lock info
- Audit log schemas

References:
- docs/02-design/14-Technical-Specs/Contract-Lock-API-Specification.md
=========================================================================
"""

from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UnlockReason(str, Enum):
    """Valid reasons for unlocking a specification."""
    GENERATION_COMPLETED = "generation_completed"
    GENERATION_FAILED = "generation_failed"
    MANUAL_UNLOCK = "manual_unlock"
    TIMEOUT = "timeout"
    ADMIN_OVERRIDE = "admin_override"


class LockAction(str, Enum):
    """Lock audit log action types."""
    LOCK = "lock"
    UNLOCK = "unlock"
    AUTO_UNLOCK = "auto_unlock"
    FORCE_UNLOCK = "force_unlock"


# Request Schemas

class SpecLockRequest(BaseModel):
    """Request to lock a specification."""
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional reason for locking"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Ready for production deployment"
            }
        }


class SpecUnlockRequest(BaseModel):
    """Request to unlock a specification."""
    unlock_reason: UnlockReason = Field(
        default=UnlockReason.MANUAL_UNLOCK,
        description="Reason for unlocking the specification"
    )
    force: bool = Field(
        default=False,
        description="Force unlock even during generation (admin only)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "unlock_reason": "manual_unlock",
                "force": False
            }
        }


class HashVerifyRequest(BaseModel):
    """Request to verify spec hash."""
    expected_hash: str = Field(
        ...,
        pattern=r"^sha256:[a-f0-9]{64}$",
        description="Expected hash in format sha256:<64-hex-chars>"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "expected_hash": "sha256:a7f3c2d1e5b4f6a8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
            }
        }


# Response Schemas

class SpecLockResponse(BaseModel):
    """Response after locking a specification."""
    success: bool
    session_id: UUID
    is_locked: bool
    locked_at: datetime
    locked_by: str
    spec_hash: str = Field(..., pattern=r"^sha256:[a-f0-9]{64}$")
    version: int = Field(default=1, description="Lock version number")
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "is_locked": True,
                "locked_at": "2025-12-26T10:00:00.000Z",
                "locked_by": "user@example.com",
                "spec_hash": "sha256:a7f3c2d1e5b4f6a8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
                "version": 1,
                "message": "Specification locked successfully"
            }
        }


class SpecUnlockResponse(BaseModel):
    """Response after unlocking a specification."""
    success: bool
    session_id: UUID
    is_locked: bool
    unlocked_at: datetime
    unlocked_by: str
    unlock_reason: UnlockReason
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "is_locked": False,
                "unlocked_at": "2025-12-26T10:30:00.000Z",
                "unlocked_by": "user@example.com",
                "unlock_reason": "manual_unlock",
                "message": "Specification unlocked successfully"
            }
        }


class HashVerifyResponse(BaseModel):
    """Response for hash verification."""
    valid: bool
    match: bool
    current_hash: str
    expected_hash: str
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "match": True,
                "current_hash": "sha256:a7f3c2d1e5b4f6a8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
                "expected_hash": "sha256:a7f3c2d1e5b4f6a8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
                "message": "Hash verification successful"
            }
        }


# Status Schemas

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


class ContractLockStatus(BaseModel):
    """Contract lock status response."""
    session_id: UUID
    is_locked: bool
    locked_at: Optional[datetime] = None
    locked_by: Optional[str] = None
    spec_hash: Optional[str] = None
    version: Optional[int] = None
    lock_expires_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "is_locked": True,
                "locked_at": "2025-12-26T10:00:00.000Z",
                "locked_by": "user@example.com",
                "spec_hash": "sha256:a7f3c2d1...",
                "version": 1,
                "lock_expires_at": "2025-12-26T11:00:00.000Z"
            }
        }


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


# Audit Log Schemas

class LockAuditLogEntry(BaseModel):
    """Single audit log entry for lock operations."""
    id: UUID
    action: LockAction
    actor_id: UUID
    actor_email: Optional[str] = None
    spec_hash: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime
    metadata: dict = Field(default_factory=dict)


class LockAuditLogResponse(BaseModel):
    """Response containing lock audit history."""
    session_id: UUID
    entries: List[LockAuditLogEntry]
    total: int


# Error Detail Schemas

class LockErrorDetail(BaseModel):
    """Detailed error information for lock operations."""
    code: str
    message: str
    details: Optional[dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "code": "ALREADY_LOCKED",
                "message": "Specification is already locked",
                "details": {
                    "locked_at": "2025-12-26T09:00:00.000Z",
                    "locked_by": "other-user@example.com"
                }
            }
        }
