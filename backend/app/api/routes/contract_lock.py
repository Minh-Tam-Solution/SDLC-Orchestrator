"""
=========================================================================
Contract Lock API Routes - Sprint 53 Day 4
SDLC Orchestrator - Specification Immutability

Version: 1.0.0
Date: December 26, 2025
Status: ACTIVE - Sprint 53 Implementation
Authority: Backend Team + CTO Approved
Foundation: Contract-Lock-API-Specification.md

Purpose:
REST API endpoints for contract lock operations:
- POST /api/v1/onboarding/{session_id}/lock - Lock specification
- POST /api/v1/onboarding/{session_id}/unlock - Unlock specification
- GET /api/v1/onboarding/{session_id}/status - Get lock status
- POST /api/v1/onboarding/{session_id}/verify-hash - Verify hash

References:
- docs/02-design/14-Technical-Specs/Contract-Lock-API-Specification.md
=========================================================================
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.contract_lock import (
    SpecLockRequest,
    SpecUnlockRequest,
    HashVerifyRequest,
    SpecLockResponse,
    SpecUnlockResponse,
    HashVerifyResponse,
    ContractLockStatus,
    OnboardingStatusResponse,
    LockAuditLogResponse,
    UnlockReason,
)
from app.services.contract_lock_service import (
    ContractLockService,
    AlreadyLockedError,
    NotLockedError,
    ForbiddenError,
    NotFoundError,
    GenerationInProgressError,
    HashMismatchError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/onboarding",
    tags=["Contract Lock"],
)


# ============================================================================
# Dependencies
# ============================================================================


async def get_lock_service(
    db: AsyncSession = Depends(get_db),
) -> ContractLockService:
    """Get ContractLockService instance."""
    return ContractLockService(db)


def check_admin(user: User) -> bool:
    """Check if user has admin role."""
    if not user.roles:
        return False
    admin_roles = {"admin", "owner", "cto", "architect"}
    return bool(set(user.roles) & admin_roles)


# ============================================================================
# Lock/Unlock Endpoints
# ============================================================================


@router.post(
    "/{session_id}/lock",
    response_model=SpecLockResponse,
    status_code=status.HTTP_200_OK,
    summary="Lock specification",
    description="""
Lock an onboarding session's specification for code generation.

This freezes the AppBlueprint and calculates a SHA256 hash for integrity.
Once locked:
- Specification cannot be modified
- Code generation uses the locked spec
- Hash can be verified at any time

Lock expires after 1 hour if generation is not started (auto-cleanup).
""",
)
async def lock_specification(
    session_id: UUID,
    request: SpecLockRequest,
    current_user: User = Depends(get_current_active_user),
    service: ContractLockService = Depends(get_lock_service),
) -> SpecLockResponse:
    """
    Lock specification for code generation.

    Args:
        session_id: Onboarding session UUID
        request: Lock request with optional reason

    Returns:
        SpecLockResponse with spec_hash and version

    Raises:
        404: Session not found
        409: Already locked
        409: Generation in progress
    """
    logger.info(
        f"Lock requested for session {session_id} by user {current_user.email}"
    )

    try:
        return await service.lock(
            session_id=session_id,
            user_id=current_user.id,
            user_email=current_user.email,
            reason=request.reason,
        )

    except NotFoundError as e:
        logger.warning(f"Lock failed - not found: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": e.code,
                "message": e.message,
                "details": e.details,
            },
        )

    except AlreadyLockedError as e:
        logger.warning(f"Lock failed - already locked: {e.details}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": e.code,
                "message": e.message,
                "details": e.details,
            },
        )

    except GenerationInProgressError as e:
        logger.warning(f"Lock failed - generation in progress: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": e.code,
                "message": e.message,
                "details": e.details,
            },
        )

    except Exception as e:
        logger.exception(f"Lock failed with unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": f"Failed to lock specification: {str(e)}",
            },
        )


@router.post(
    "/{session_id}/unlock",
    response_model=SpecUnlockResponse,
    status_code=status.HTTP_200_OK,
    summary="Unlock specification",
    description="""
Unlock an onboarding session's specification.

Only the user who locked the spec or an admin can unlock.
Requires a reason for audit trail.

Unlock reasons:
- modification_needed: Need to update the blueprint
- generation_failed: Generation failed, need to retry
- admin_override: Admin unlocking for recovery
- session_expired: Session expired (auto-unlock)
""",
)
async def unlock_specification(
    session_id: UUID,
    request: SpecUnlockRequest,
    current_user: User = Depends(get_current_active_user),
    service: ContractLockService = Depends(get_lock_service),
) -> SpecUnlockResponse:
    """
    Unlock specification.

    Args:
        session_id: Onboarding session UUID
        request: Unlock request with reason

    Returns:
        SpecUnlockResponse

    Raises:
        404: Session not found
        409: Not locked
        403: Forbidden (not owner or admin)
        409: Generation in progress
    """
    logger.info(
        f"Unlock requested for session {session_id} by user {current_user.email}, "
        f"reason={request.reason}"
    )

    is_admin = check_admin(current_user)

    try:
        return await service.unlock(
            session_id=session_id,
            user_id=current_user.id,
            user_email=current_user.email,
            reason=request.reason,
            is_admin=is_admin,
        )

    except NotFoundError as e:
        logger.warning(f"Unlock failed - not found: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": e.code,
                "message": e.message,
                "details": e.details,
            },
        )

    except NotLockedError as e:
        logger.warning(f"Unlock failed - not locked: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": e.code,
                "message": e.message,
                "details": e.details,
            },
        )

    except ForbiddenError as e:
        logger.warning(f"Unlock failed - forbidden: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": e.code,
                "message": e.message,
                "details": e.details,
            },
        )

    except GenerationInProgressError as e:
        logger.warning(f"Unlock failed - generation in progress: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": e.code,
                "message": e.message,
                "details": e.details,
            },
        )

    except Exception as e:
        logger.exception(f"Unlock failed with unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": f"Failed to unlock specification: {str(e)}",
            },
        )


# ============================================================================
# Status Endpoints
# ============================================================================


@router.get(
    "/{session_id}/lock-status",
    response_model=ContractLockStatus,
    summary="Get lock status",
    description="Get the current lock status of an onboarding session.",
)
async def get_lock_status(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: ContractLockService = Depends(get_lock_service),
) -> ContractLockStatus:
    """
    Get lock status for a session.

    Args:
        session_id: Onboarding session UUID

    Returns:
        ContractLockStatus with lock details

    Raises:
        404: Session not found
    """
    try:
        return await service.get_status(session_id)

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": e.code,
                "message": e.message,
                "details": e.details,
            },
        )


@router.get(
    "/{session_id}/status",
    response_model=OnboardingStatusResponse,
    summary="Get full session status",
    description="""
Get full status of an onboarding session including:
- Lock status
- Generation status
- Blueprint metadata
""",
)
async def get_session_status(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: ContractLockService = Depends(get_lock_service),
) -> OnboardingStatusResponse:
    """
    Get full session status.

    Args:
        session_id: Onboarding session UUID

    Returns:
        OnboardingStatusResponse with full status

    Raises:
        404: Session not found
    """
    try:
        return await service.get_full_status(session_id)

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": e.code,
                "message": e.message,
                "details": e.details,
            },
        )


# ============================================================================
# Hash Verification Endpoint
# ============================================================================


@router.post(
    "/{session_id}/verify-hash",
    response_model=HashVerifyResponse,
    summary="Verify spec hash",
    description="""
Verify that the current specification matches an expected hash.

Used internally before code generation to ensure the locked spec
has not been modified. Also useful for audit/compliance.
""",
)
async def verify_hash(
    session_id: UUID,
    request: HashVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    service: ContractLockService = Depends(get_lock_service),
) -> HashVerifyResponse:
    """
    Verify spec hash matches expected value.

    Args:
        session_id: Onboarding session UUID
        request: Expected hash to verify

    Returns:
        HashVerifyResponse with match result

    Raises:
        404: Session not found
    """
    logger.info(
        f"Hash verification for session {session_id}: "
        f"expected={request.expected_hash[:20]}..."
    )

    try:
        return await service.verify_hash(
            session_id=session_id,
            expected_hash=request.expected_hash,
        )

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": e.code,
                "message": e.message,
                "details": e.details,
            },
        )


# ============================================================================
# Audit Log Endpoint
# ============================================================================


@router.get(
    "/{session_id}/lock-audit",
    response_model=LockAuditLogResponse,
    summary="Get lock audit log",
    description="Get the audit log of all lock/unlock operations for a session.",
)
async def get_lock_audit(
    session_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    service: ContractLockService = Depends(get_lock_service),
) -> LockAuditLogResponse:
    """
    Get lock audit log.

    Args:
        session_id: Onboarding session UUID
        limit: Max entries to return (1-100, default 50)
        offset: Offset for pagination (default 0)

    Returns:
        LockAuditLogResponse with entries

    Raises:
        404: Session not found
    """
    try:
        return await service.get_audit_log(
            session_id=session_id,
            limit=limit,
            offset=offset,
        )

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": e.code,
                "message": e.message,
                "details": e.details,
            },
        )


# ============================================================================
# Admin Endpoints
# ============================================================================


@router.post(
    "/{session_id}/force-unlock",
    response_model=SpecUnlockResponse,
    summary="Force unlock (admin)",
    description="Force unlock a specification. Requires admin privileges.",
)
async def force_unlock(
    session_id: UUID,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    service: ContractLockService = Depends(get_lock_service),
) -> SpecUnlockResponse:
    """
    Force unlock a specification (admin only).

    Args:
        session_id: Onboarding session UUID
        reason: Optional reason for force unlock

    Returns:
        SpecUnlockResponse

    Raises:
        403: Not an admin
        404: Session not found
        409: Not locked
    """
    if not check_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ADMIN_REQUIRED",
                "message": "Admin privileges required for force unlock",
            },
        )

    logger.warning(
        f"Force unlock requested for session {session_id} by admin {current_user.email}"
    )

    try:
        return await service.unlock(
            session_id=session_id,
            user_id=current_user.id,
            user_email=current_user.email,
            reason=UnlockReason.ADMIN_OVERRIDE,
            is_admin=True,
        )

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": e.code,
                "message": e.message,
                "details": e.details,
            },
        )

    except NotLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": e.code,
                "message": e.message,
                "details": e.details,
            },
        )
