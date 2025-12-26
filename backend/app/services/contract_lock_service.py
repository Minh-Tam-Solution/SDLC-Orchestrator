"""
=========================================================================
Contract Lock Service - Sprint 53 Day 4
SDLC Orchestrator - Specification Immutability

Version: 1.0.0
Date: December 26, 2025
Status: ACTIVE - Sprint 53 Implementation
Authority: Backend Team + CTO Approved
Foundation: Contract-Lock-API-Specification.md

Purpose:
- Lock/unlock specification for code generation
- SHA256 hash calculation for integrity
- Audit logging for all lock operations
- Auto-expiry for orphaned locks

References:
- docs/02-design/14-Technical-Specs/Contract-Lock-API-Specification.md
=========================================================================
"""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

import logging
from app.schemas.contract_lock import (
    ContractLockStatus,
    GenerationProgress,
    HashVerifyResponse,
    LastGeneration,
    LockAction,
    LockAuditLogEntry,
    LockAuditLogResponse,
    OnboardingStatusResponse,
    SpecLockResponse,
    SpecUnlockResponse,
    UnlockReason,
)

logger = logging.getLogger(__name__)

# Lock expires after 1 hour of inactivity
LOCK_EXPIRY_HOURS = 1


class ContractLockError(Exception):
    """Base exception for contract lock operations."""
    def __init__(self, message: str, code: str, details: Optional[dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class AlreadyLockedError(ContractLockError):
    """Raised when trying to lock an already locked spec."""
    def __init__(
        self,
        session_id: UUID,
        locked_at: Optional[datetime] = None,
        locked_by: Optional[str] = None
    ):
        details = {
            "session_id": str(session_id),
            "locked_at": locked_at.isoformat() if locked_at else None,
            "locked_by": locked_by,
        }
        super().__init__(
            message="Specification is already locked",
            code="ALREADY_LOCKED",
            details=details
        )


class NotLockedError(ContractLockError):
    """Raised when trying to unlock a non-locked spec."""
    def __init__(self, session_id: UUID):
        super().__init__(
            message="Specification is not locked",
            code="NOT_LOCKED",
            details={"session_id": str(session_id)}
        )


class ForbiddenError(ContractLockError):
    """Raised when user doesn't have permission."""
    def __init__(self, message: str, session_id: Optional[UUID] = None):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            details={"session_id": str(session_id)} if session_id else {}
        )


class NotFoundError(ContractLockError):
    """Raised when session not found."""
    def __init__(self, session_id: UUID):
        super().__init__(
            message=f"Onboarding session {session_id} not found",
            code="NOT_FOUND",
            details={"session_id": str(session_id)}
        )


class GenerationInProgressError(ContractLockError):
    """Raised when generation is in progress."""
    def __init__(self, session_id: UUID):
        super().__init__(
            message="Cannot modify lock during active generation",
            code="GENERATION_IN_PROGRESS",
            details={"session_id": str(session_id)}
        )


class HashMismatchError(ContractLockError):
    """Raised when hash verification fails."""
    def __init__(
        self,
        current_hash: str,
        expected_hash: str,
        session_id: UUID
    ):
        super().__init__(
            message="Specification has been modified since locking",
            code="HASH_MISMATCH",
            details={
                "session_id": str(session_id),
                "current_hash": current_hash,
                "expected_hash": expected_hash,
                "recommendation": "Re-lock the specification before generation"
            }
        )


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


class ContractLockService:
    """
    Service for managing contract specification locks.

    Provides lock/unlock operations with:
    - SHA256 hash integrity verification
    - Audit logging for compliance
    - Auto-expiry to prevent orphaned locks
    - Permission checking (owner or admin)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def lock(
        self,
        session_id: UUID,
        user_id: UUID,
        user_email: str,
        reason: Optional[str] = None
    ) -> SpecLockResponse:
        """
        Lock an onboarding session's specification.

        Args:
            session_id: The onboarding session to lock
            user_id: The user performing the lock
            user_email: Email of the user for display
            reason: Optional reason for locking

        Returns:
            SpecLockResponse with lock details

        Raises:
            NotFoundError: Session doesn't exist
            AlreadyLockedError: Session is already locked
            GenerationInProgressError: Generation is in progress
        """
        # Get session with app_blueprint
        session_data = await self._get_session(session_id)

        if session_data["locked"]:
            raise AlreadyLockedError(
                session_id=session_id,
                locked_at=session_data.get("locked_at"),
                locked_by=session_data.get("locked_by_email")
            )

        # Check if generation is in progress
        if await self._is_generation_in_progress(session_id):
            raise GenerationInProgressError(session_id=session_id)

        # Calculate spec hash from blueprint
        blueprint = session_data.get("app_blueprint", {})
        if not blueprint:
            blueprint = {"name": "empty", "version": "0.0.0", "modules": []}

        spec_hash = calculate_spec_hash(blueprint)

        # Get current version (increment if exists)
        current_version = session_data.get("lock_version", 0) or 0
        new_version = current_version + 1

        # Lock the session
        now = datetime.now(timezone.utc)
        lock_expires = now + timedelta(hours=LOCK_EXPIRY_HOURS)

        await self._update_session_lock(
            session_id=session_id,
            locked=True,
            spec_hash=spec_hash,
            locked_at=now,
            locked_by=user_id,
            lock_expires_at=lock_expires,
            lock_version=new_version
        )

        # Create audit log
        await self._create_audit_log(
            session_id=session_id,
            action=LockAction.LOCK,
            actor_id=user_id,
            spec_hash=spec_hash,
            reason=reason,
            metadata={"source": "api", "version": new_version}
        )

        logger.info(
            f"Locked session {session_id} by user {user_email}, hash={spec_hash[:20]}..."
        )

        return SpecLockResponse(
            success=True,
            session_id=session_id,
            is_locked=True,
            locked_at=now,
            locked_by=user_email,
            spec_hash=spec_hash,
            version=new_version,
            message="Specification locked successfully"
        )

    async def unlock(
        self,
        session_id: UUID,
        user_id: UUID,
        user_email: str,
        reason: UnlockReason,
        is_admin: bool = False
    ) -> SpecUnlockResponse:
        """
        Unlock an onboarding session's specification.

        Args:
            session_id: The onboarding session to unlock
            user_id: The user performing the unlock
            user_email: Email of the user for display
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
        session_data = await self._get_session(session_id)

        if not session_data["locked"]:
            raise NotLockedError(session_id=session_id)

        # Check permission (owner or admin can unlock)
        locked_by = session_data.get("locked_by")
        if locked_by and locked_by != user_id and not is_admin:
            raise ForbiddenError(
                message="Only the user who locked the spec or an admin can unlock",
                session_id=session_id
            )

        # Check if generation is in progress (unless admin override)
        if await self._is_generation_in_progress(session_id):
            if reason != UnlockReason.ADMIN_OVERRIDE:
                raise GenerationInProgressError(session_id=session_id)

        # Unlock the session
        now = datetime.now(timezone.utc)
        old_hash = session_data.get("spec_hash")

        await self._update_session_lock(
            session_id=session_id,
            locked=False,
            spec_hash=None,
            locked_at=None,
            locked_by=None,
            lock_expires_at=None,
            lock_version=session_data.get("lock_version")  # Keep version
        )

        # Create audit log
        action = LockAction.FORCE_UNLOCK if reason == UnlockReason.ADMIN_OVERRIDE else LockAction.UNLOCK
        await self._create_audit_log(
            session_id=session_id,
            action=action,
            actor_id=user_id,
            spec_hash=old_hash,
            reason=reason.value,
            metadata={"source": "api", "is_admin": is_admin}
        )

        logger.info(
            f"Unlocked session {session_id} by user {user_email}, reason={reason.value}"
        )

        return SpecUnlockResponse(
            success=True,
            session_id=session_id,
            is_locked=False,
            unlocked_at=now,
            unlocked_by=user_email,
            unlock_reason=reason,
            message="Specification unlocked successfully"
        )

    async def get_status(self, session_id: UUID) -> ContractLockStatus:
        """Get lock status for a session."""
        session_data = await self._get_session(session_id)

        return ContractLockStatus(
            session_id=session_id,
            is_locked=session_data["locked"],
            locked_at=session_data.get("locked_at"),
            locked_by=session_data.get("locked_by_email"),
            spec_hash=session_data.get("spec_hash"),
            version=session_data.get("lock_version"),
            lock_expires_at=session_data.get("lock_expires_at")
        )

    async def get_full_status(self, session_id: UUID) -> OnboardingStatusResponse:
        """Get full status of an onboarding session including lock info."""
        session_data = await self._get_session(session_id)

        # Get blueprint info
        blueprint = session_data.get("app_blueprint", {})

        # Get generation status
        gen_status, gen_progress, last_gen = await self._get_generation_info(session_id)

        return OnboardingStatusResponse(
            id=session_id,
            name=blueprint.get("name", "Unknown"),
            version=blueprint.get("version", "1.0.0"),
            business_domain=blueprint.get("business_domain", ""),
            locked=session_data["locked"],
            spec_hash=session_data.get("spec_hash"),
            locked_at=session_data.get("locked_at"),
            locked_by=session_data.get("locked_by"),
            lock_expires_at=session_data.get("lock_expires_at"),
            generation_status=gen_status,
            generation_progress=gen_progress,
            last_generation=last_gen
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
        session_data = await self._get_session(session_id)

        # Calculate current hash
        blueprint = session_data.get("app_blueprint", {})
        if not blueprint:
            blueprint = {"name": "empty", "version": "0.0.0", "modules": []}

        current_hash = calculate_spec_hash(blueprint)
        match = current_hash == expected_hash

        if not match:
            logger.warning(
                f"Hash mismatch for session {session_id}: "
                f"expected={expected_hash[:20]}..., current={current_hash[:20]}..."
            )

        return HashVerifyResponse(
            valid=True,
            match=match,
            current_hash=current_hash,
            expected_hash=expected_hash,
            message="Hash verification successful" if match else "Hash mismatch detected"
        )

    async def get_audit_log(
        self,
        session_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> LockAuditLogResponse:
        """Get audit log for a session."""
        # Verify session exists
        await self._get_session(session_id)

        entries, total = await self._get_audit_entries(session_id, limit, offset)

        return LockAuditLogResponse(
            session_id=session_id,
            entries=entries,
            total=total
        )

    async def auto_unlock_expired(self) -> int:
        """
        Auto-unlock all expired locks.
        Should be called by a background job.

        Returns:
            Number of sessions unlocked
        """
        now = datetime.now(timezone.utc)

        # Find expired locked sessions
        expired_sessions = await self._get_expired_sessions(now)

        count = 0
        for session_id, locked_by in expired_sessions:
            try:
                await self._update_session_lock(
                    session_id=session_id,
                    locked=False,
                    spec_hash=None,
                    locked_at=None,
                    locked_by=None,
                    lock_expires_at=None,
                    lock_version=None
                )

                await self._create_audit_log(
                    session_id=session_id,
                    action=LockAction.AUTO_UNLOCK,
                    actor_id=locked_by,  # Use original locker as actor
                    spec_hash=None,
                    reason="Lock expired after 1 hour",
                    metadata={"source": "background_job", "expired_at": now.isoformat()}
                )

                count += 1
                logger.info(f"Auto-unlocked expired session {session_id}")

            except Exception as e:
                logger.error(f"Failed to auto-unlock session {session_id}: {e}")

        if count > 0:
            logger.info(f"Auto-unlocked {count} expired sessions")

        return count

    # ========================================
    # Private Helper Methods
    # ========================================

    async def _get_session(self, session_id: UUID) -> Dict[str, Any]:
        """
        Get session by ID or raise NotFoundError.

        Returns dict with session data including:
        - locked, spec_hash, locked_at, locked_by, lock_expires_at
        - app_blueprint, locked_by_email, lock_version
        """
        # In real implementation, this queries the onboarding_sessions table
        # For now, we use raw SQL to avoid model dependency issues

        query = """
            SELECT
                os.id,
                os.app_blueprint,
                os.locked,
                os.spec_hash,
                os.locked_at,
                os.locked_by,
                os.lock_expires_at,
                os.lock_version,
                u.email as locked_by_email
            FROM onboarding_sessions os
            LEFT JOIN users u ON os.locked_by = u.id
            WHERE os.id = :session_id
        """

        result = await self.db.execute(
            query,
            {"session_id": str(session_id)}
        )
        row = result.fetchone()

        if not row:
            raise NotFoundError(session_id=session_id)

        return {
            "id": row.id,
            "app_blueprint": row.app_blueprint or {},
            "locked": row.locked or False,
            "spec_hash": row.spec_hash,
            "locked_at": row.locked_at,
            "locked_by": row.locked_by,
            "locked_by_email": row.locked_by_email,
            "lock_expires_at": row.lock_expires_at,
            "lock_version": row.lock_version,
        }

    async def _update_session_lock(
        self,
        session_id: UUID,
        locked: bool,
        spec_hash: Optional[str],
        locked_at: Optional[datetime],
        locked_by: Optional[UUID],
        lock_expires_at: Optional[datetime],
        lock_version: Optional[int]
    ) -> None:
        """Update lock fields on a session."""
        query = """
            UPDATE onboarding_sessions
            SET
                locked = :locked,
                spec_hash = :spec_hash,
                locked_at = :locked_at,
                locked_by = :locked_by,
                lock_expires_at = :lock_expires_at,
                lock_version = :lock_version,
                updated_at = :updated_at
            WHERE id = :session_id
        """

        await self.db.execute(
            query,
            {
                "session_id": str(session_id),
                "locked": locked,
                "spec_hash": spec_hash,
                "locked_at": locked_at,
                "locked_by": str(locked_by) if locked_by else None,
                "lock_expires_at": lock_expires_at,
                "lock_version": lock_version,
                "updated_at": datetime.now(timezone.utc)
            }
        )
        await self.db.commit()

    async def _create_audit_log(
        self,
        session_id: UUID,
        action: LockAction,
        actor_id: UUID,
        spec_hash: Optional[str],
        reason: Optional[str],
        metadata: Dict[str, Any]
    ) -> None:
        """Create an audit log entry."""
        query = """
            INSERT INTO lock_audit_log
            (id, onboarding_session_id, action, actor_id, spec_hash, reason, metadata, created_at)
            VALUES
            (gen_random_uuid(), :session_id, :action, :actor_id, :spec_hash, :reason, :metadata, :created_at)
        """

        await self.db.execute(
            query,
            {
                "session_id": str(session_id),
                "action": action.value,
                "actor_id": str(actor_id),
                "spec_hash": spec_hash,
                "reason": reason,
                "metadata": json.dumps(metadata),
                "created_at": datetime.now(timezone.utc)
            }
        )
        await self.db.commit()

    async def _get_audit_entries(
        self,
        session_id: UUID,
        limit: int,
        offset: int
    ) -> Tuple[List[LockAuditLogEntry], int]:
        """Get audit log entries for a session."""
        # Count total
        count_query = """
            SELECT COUNT(*) FROM lock_audit_log
            WHERE onboarding_session_id = :session_id
        """
        result = await self.db.execute(count_query, {"session_id": str(session_id)})
        total = result.scalar() or 0

        # Get entries
        query = """
            SELECT
                l.id, l.action, l.actor_id, l.spec_hash, l.reason, l.metadata, l.created_at,
                u.email as actor_email
            FROM lock_audit_log l
            LEFT JOIN users u ON l.actor_id = u.id
            WHERE l.onboarding_session_id = :session_id
            ORDER BY l.created_at DESC
            LIMIT :limit OFFSET :offset
        """

        result = await self.db.execute(
            query,
            {"session_id": str(session_id), "limit": limit, "offset": offset}
        )
        rows = result.fetchall()

        entries = [
            LockAuditLogEntry(
                id=row.id,
                action=LockAction(row.action),
                actor_id=row.actor_id,
                actor_email=row.actor_email,
                spec_hash=row.spec_hash,
                reason=row.reason,
                created_at=row.created_at,
                metadata=row.metadata if isinstance(row.metadata, dict) else {}
            )
            for row in rows
        ]

        return entries, total

    async def _get_expired_sessions(self, now: datetime) -> List[Tuple[UUID, UUID]]:
        """Get list of expired locked sessions."""
        query = """
            SELECT id, locked_by
            FROM onboarding_sessions
            WHERE locked = true AND lock_expires_at < :now
        """

        result = await self.db.execute(query, {"now": now})
        rows = result.fetchall()

        return [(row.id, row.locked_by) for row in rows]

    async def _is_generation_in_progress(self, session_id: UUID) -> bool:
        """Check if there's an active generation for this session."""
        # Query generation_sessions table for active status
        query = """
            SELECT COUNT(*) FROM generation_sessions
            WHERE onboarding_session_id = :session_id
            AND status IN ('pending', 'generating', 'validating')
        """

        try:
            result = await self.db.execute(query, {"session_id": str(session_id)})
            count = result.scalar() or 0
            return count > 0
        except Exception:
            # Table might not exist yet
            return False

    async def _get_generation_info(
        self,
        session_id: UUID
    ) -> Tuple[str, Optional[GenerationProgress], Optional[LastGeneration]]:
        """Get generation status and progress info."""
        # Check for active generation
        active_query = """
            SELECT id, status, files_completed, total_files, current_file, started_at
            FROM generation_sessions
            WHERE onboarding_session_id = :session_id
            AND status IN ('pending', 'generating', 'validating')
            ORDER BY created_at DESC
            LIMIT 1
        """

        try:
            result = await self.db.execute(active_query, {"session_id": str(session_id)})
            active = result.fetchone()

            if active:
                progress = GenerationProgress(
                    files_completed=active.files_completed or 0,
                    total_files_estimated=active.total_files or 0,
                    current_file=active.current_file,
                    started_at=active.started_at
                )
                return "in_progress", progress, None

        except Exception:
            pass

        # Check for last completed generation
        last_query = """
            SELECT id, status, completed_at, total_files, total_lines
            FROM generation_sessions
            WHERE onboarding_session_id = :session_id
            AND status IN ('completed', 'failed', 'cancelled')
            ORDER BY completed_at DESC
            LIMIT 1
        """

        try:
            result = await self.db.execute(last_query, {"session_id": str(session_id)})
            last = result.fetchone()

            if last:
                last_gen = LastGeneration(
                    session_id=str(last.id),
                    status=last.status,
                    completed_at=last.completed_at,
                    total_files=last.total_files or 0,
                    total_lines=last.total_lines or 0
                )
                return last.status if last.status in ["completed", "failed"] else "idle", None, last_gen

        except Exception:
            pass

        return "idle", None, None
