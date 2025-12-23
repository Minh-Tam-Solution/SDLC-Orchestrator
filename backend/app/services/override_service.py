"""
Override Service - VCR (Version Controlled Resolution) Workflow

SDLC Stage: 04 - BUILD
Sprint: 43 - Policy Guards & Evidence UI
Framework: SDLC 5.1.1
Epic: EP-02 AI Safety Layer v1

Purpose:
Business logic for the Override workflow:
- Create override requests
- Admin queue management
- Approve/reject overrides
- Audit trail logging
- Expiry management

VCR Workflow:
1. Developer requests override (failed validation)
2. Request enters admin queue (PENDING)
3. Admin/Manager reviews and approves/rejects
4. If approved, update AICodeEvent.validation_result to 'overridden'
5. All actions logged in audit trail

Business Rules:
- Only ADMIN, MANAGER, SECURITY_LEAD can approve/reject
- EMERGENCY overrides require post-merge review within 24h
- Requests expire after 7 days if not actioned
- Reason must be >= 50 characters
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.analytics import AICodeEvent
from app.models.override import (
    OverrideAuditAction,
    OverrideAuditLog,
    OverrideStatus,
    OverrideType,
    ValidationOverride,
)
from app.models.project import Project
from app.models.user import User

logger = logging.getLogger(__name__)

# Constants
OVERRIDE_EXPIRY_DAYS = 7
MIN_REASON_LENGTH = 50
MAX_REASON_LENGTH = 2000
APPROVER_ROLES = {"admin", "manager", "security", "cto", "ceo"}


class OverrideServiceError(Exception):
    """Base exception for override service errors."""
    pass


class OverrideNotFoundError(OverrideServiceError):
    """Override not found."""
    pass


class OverrideValidationError(OverrideServiceError):
    """Validation error for override request."""
    pass


class OverridePermissionError(OverrideServiceError):
    """Permission denied for override action."""
    pass


class OverrideService:
    """
    Service class for managing validation overrides.

    Provides:
    - Override request creation
    - Admin queue retrieval
    - Approve/reject operations
    - Audit logging
    - Expiry management
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Override Request Management
    # =========================================================================

    async def create_override_request(
        self,
        event_id: UUID,
        override_type: OverrideType,
        reason: str,
        requested_by: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ValidationOverride:
        """
        Create a new override request for a failed validation event.

        Args:
            event_id: ID of the AI code event
            override_type: Type of override (false_positive, approved_risk, emergency)
            reason: Justification for the override (min 50 chars)
            requested_by: User making the request
            ip_address: Client IP address for audit
            user_agent: Client user agent for audit

        Returns:
            Created ValidationOverride

        Raises:
            OverrideValidationError: If validation fails
            OverrideNotFoundError: If event not found
        """
        # Validate reason length
        if len(reason) < MIN_REASON_LENGTH:
            raise OverrideValidationError(
                f"Reason must be at least {MIN_REASON_LENGTH} characters"
            )
        if len(reason) > MAX_REASON_LENGTH:
            raise OverrideValidationError(
                f"Reason must be at most {MAX_REASON_LENGTH} characters"
            )

        # Fetch event
        result = await self.db.execute(
            select(AICodeEvent).where(AICodeEvent.id == event_id)
        )
        event = result.scalar_one_or_none()

        if not event:
            raise OverrideNotFoundError(f"Event with ID {event_id} not found")

        # Verify event has failed validation
        if event.validation_result not in ("failed", "warning"):
            raise OverrideValidationError(
                "Override can only be requested for failed or warning validations"
            )

        # Check for existing pending override
        result = await self.db.execute(
            select(ValidationOverride).where(
                and_(
                    ValidationOverride.event_id == event_id,
                    ValidationOverride.status == OverrideStatus.PENDING,
                )
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise OverrideValidationError(
                "An override request is already pending for this event"
            )

        # Calculate expiry
        expires_at = datetime.utcnow() + timedelta(days=OVERRIDE_EXPIRY_DAYS)

        # Extract failed validators from violations
        failed_validators = []
        if event.violations:
            for v in event.violations:
                if isinstance(v, dict) and v.get("validator"):
                    failed_validators.append(v["validator"])

        # Create override
        override = ValidationOverride(
            event_id=event_id,
            project_id=event.project_id,
            override_type=override_type,
            reason=reason,
            status=OverrideStatus.PENDING,
            requested_by_id=requested_by.id,
            requested_at=datetime.utcnow(),
            expires_at=expires_at,
            pr_number=event.pr_id,
            pr_title=f"PR #{event.pr_id}" if event.pr_id else "Direct Commit",
            failed_validators=json.dumps(failed_validators),
            post_merge_review_required=override_type == OverrideType.EMERGENCY,
        )

        self.db.add(override)
        await self.db.flush()

        # Create audit log
        audit_log = OverrideAuditLog(
            override_id=override.id,
            action=OverrideAuditAction.REQUEST_CREATED,
            action_by_id=requested_by.id,
            action_at=datetime.utcnow(),
            new_status=OverrideStatus.PENDING,
            comment=f"Override request created: {override_type.value}",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=json.dumps({
                "override_type": override_type.value,
                "event_id": str(event_id),
                "pr_number": event.pr_id,
            }),
        )
        self.db.add(audit_log)

        await self.db.commit()
        await self.db.refresh(override)

        logger.info(
            f"Override request created: {override.id} for event {event_id} by {requested_by.email}"
        )

        return override

    async def get_override(self, override_id: UUID) -> Optional[ValidationOverride]:
        """Get override by ID with related data."""
        result = await self.db.execute(
            select(ValidationOverride)
            .options(
                selectinload(ValidationOverride.event),
                selectinload(ValidationOverride.requested_by),
                selectinload(ValidationOverride.resolved_by),
            )
            .where(ValidationOverride.id == override_id)
        )
        return result.scalar_one_or_none()

    async def get_override_by_event(self, event_id: UUID) -> Optional[ValidationOverride]:
        """Get latest override for an event."""
        result = await self.db.execute(
            select(ValidationOverride)
            .where(ValidationOverride.event_id == event_id)
            .order_by(ValidationOverride.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_overrides_for_event(self, event_id: UUID) -> list[ValidationOverride]:
        """Get all overrides for an event (history)."""
        result = await self.db.execute(
            select(ValidationOverride)
            .where(ValidationOverride.event_id == event_id)
            .order_by(ValidationOverride.created_at.desc())
        )
        return list(result.scalars().all())

    # =========================================================================
    # Admin Queue Management
    # =========================================================================

    async def get_pending_queue(
        self,
        project_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ValidationOverride], int]:
        """
        Get pending override requests for admin queue.

        Args:
            project_id: Filter by project (optional)
            limit: Max results
            offset: Pagination offset

        Returns:
            Tuple of (overrides list, total count)
        """
        # Build base query
        query = (
            select(ValidationOverride)
            .options(
                selectinload(ValidationOverride.event),
                selectinload(ValidationOverride.requested_by),
                selectinload(ValidationOverride.project),
            )
            .where(
                and_(
                    ValidationOverride.status == OverrideStatus.PENDING,
                    ValidationOverride.is_expired == False,
                )
            )
        )

        count_query = select(func.count()).select_from(ValidationOverride).where(
            and_(
                ValidationOverride.status == OverrideStatus.PENDING,
                ValidationOverride.is_expired == False,
            )
        )

        if project_id:
            query = query.where(ValidationOverride.project_id == project_id)
            count_query = count_query.where(ValidationOverride.project_id == project_id)

        # Order by oldest first (FIFO)
        query = query.order_by(ValidationOverride.created_at.asc())
        query = query.offset(offset).limit(limit)

        # Execute
        result = await self.db.execute(query)
        overrides = list(result.scalars().all())

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        return overrides, total

    async def get_recent_decisions(
        self,
        project_id: Optional[UUID] = None,
        limit: int = 20,
    ) -> list[ValidationOverride]:
        """Get recent override decisions for reference."""
        query = (
            select(ValidationOverride)
            .options(
                selectinload(ValidationOverride.requested_by),
                selectinload(ValidationOverride.resolved_by),
            )
            .where(
                ValidationOverride.status.in_([
                    OverrideStatus.APPROVED,
                    OverrideStatus.REJECTED,
                ])
            )
        )

        if project_id:
            query = query.where(ValidationOverride.project_id == project_id)

        query = query.order_by(ValidationOverride.resolved_at.desc())
        query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # Approve/Reject Operations
    # =========================================================================

    async def approve_override(
        self,
        override_id: UUID,
        approver: User,
        comment: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ValidationOverride:
        """
        Approve an override request.

        Args:
            override_id: ID of the override to approve
            approver: User approving the override
            comment: Optional approval comment
            ip_address: Client IP for audit
            user_agent: Client user agent for audit

        Returns:
            Updated ValidationOverride

        Raises:
            OverrideNotFoundError: If override not found
            OverridePermissionError: If user lacks permission
            OverrideValidationError: If override cannot be approved
        """
        # Check approver role
        if not self._has_approver_role(approver):
            raise OverridePermissionError(
                "Only admins, managers, or security leads can approve overrides"
            )

        # Fetch override
        override = await self.get_override(override_id)
        if not override:
            raise OverrideNotFoundError(f"Override with ID {override_id} not found")

        # Validate status
        if override.status != OverrideStatus.PENDING:
            raise OverrideValidationError(
                f"Cannot approve override with status {override.status.value}"
            )

        if override.is_expired:
            raise OverrideValidationError("Cannot approve expired override")

        # Update override
        override.status = OverrideStatus.APPROVED
        override.resolved_by_id = approver.id
        override.resolved_at = datetime.utcnow()
        override.resolution_comment = comment

        # Update AICodeEvent validation_result to 'overridden'
        await self.db.execute(
            update(AICodeEvent)
            .where(AICodeEvent.id == override.event_id)
            .values(validation_result="overridden")
        )

        # Create audit log
        audit_log = OverrideAuditLog(
            override_id=override.id,
            action=OverrideAuditAction.APPROVED,
            action_by_id=approver.id,
            action_at=datetime.utcnow(),
            previous_status=OverrideStatus.PENDING,
            new_status=OverrideStatus.APPROVED,
            comment=comment or "Override approved",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(audit_log)

        await self.db.commit()
        await self.db.refresh(override)

        logger.info(
            f"Override {override_id} approved by {approver.email}"
        )

        return override

    async def reject_override(
        self,
        override_id: UUID,
        rejector: User,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ValidationOverride:
        """
        Reject an override request.

        Args:
            override_id: ID of the override to reject
            rejector: User rejecting the override
            reason: Rejection reason (required)
            ip_address: Client IP for audit
            user_agent: Client user agent for audit

        Returns:
            Updated ValidationOverride

        Raises:
            OverrideNotFoundError: If override not found
            OverridePermissionError: If user lacks permission
            OverrideValidationError: If override cannot be rejected
        """
        # Validate reason
        if not reason or len(reason) < 10:
            raise OverrideValidationError("Rejection reason must be at least 10 characters")

        # Check rejector role
        if not self._has_approver_role(rejector):
            raise OverridePermissionError(
                "Only admins, managers, or security leads can reject overrides"
            )

        # Fetch override
        override = await self.get_override(override_id)
        if not override:
            raise OverrideNotFoundError(f"Override with ID {override_id} not found")

        # Validate status
        if override.status != OverrideStatus.PENDING:
            raise OverrideValidationError(
                f"Cannot reject override with status {override.status.value}"
            )

        # Update override
        override.status = OverrideStatus.REJECTED
        override.resolved_by_id = rejector.id
        override.resolved_at = datetime.utcnow()
        override.resolution_comment = reason

        # Create audit log
        audit_log = OverrideAuditLog(
            override_id=override.id,
            action=OverrideAuditAction.REJECTED,
            action_by_id=rejector.id,
            action_at=datetime.utcnow(),
            previous_status=OverrideStatus.PENDING,
            new_status=OverrideStatus.REJECTED,
            comment=reason,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(audit_log)

        await self.db.commit()
        await self.db.refresh(override)

        logger.info(
            f"Override {override_id} rejected by {rejector.email}: {reason}"
        )

        return override

    async def cancel_override(
        self,
        override_id: UUID,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ValidationOverride:
        """
        Cancel an override request (by requester).

        Args:
            override_id: ID of the override to cancel
            user: User cancelling (must be requester)
            ip_address: Client IP for audit
            user_agent: Client user agent for audit

        Returns:
            Updated ValidationOverride
        """
        override = await self.get_override(override_id)
        if not override:
            raise OverrideNotFoundError(f"Override with ID {override_id} not found")

        # Only requester or admin can cancel
        if override.requested_by_id != user.id and not self._has_approver_role(user):
            raise OverridePermissionError(
                "Only the requester or an admin can cancel an override request"
            )

        if override.status != OverrideStatus.PENDING:
            raise OverrideValidationError(
                f"Cannot cancel override with status {override.status.value}"
            )

        # Update override
        override.status = OverrideStatus.CANCELLED
        override.resolved_at = datetime.utcnow()
        override.resolution_comment = "Cancelled by requester"

        # Create audit log
        audit_log = OverrideAuditLog(
            override_id=override.id,
            action=OverrideAuditAction.REQUEST_CANCELLED,
            action_by_id=user.id,
            action_at=datetime.utcnow(),
            previous_status=OverrideStatus.PENDING,
            new_status=OverrideStatus.CANCELLED,
            comment="Override request cancelled",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(audit_log)

        await self.db.commit()
        await self.db.refresh(override)

        logger.info(f"Override {override_id} cancelled by {user.email}")

        return override

    # =========================================================================
    # Expiry Management
    # =========================================================================

    async def expire_old_requests(self) -> int:
        """
        Mark expired override requests.

        Called by scheduled job (daily).

        Returns:
            Number of expired requests
        """
        now = datetime.utcnow()

        # Find expired pending requests
        result = await self.db.execute(
            select(ValidationOverride).where(
                and_(
                    ValidationOverride.status == OverrideStatus.PENDING,
                    ValidationOverride.expires_at < now,
                    ValidationOverride.is_expired == False,
                )
            )
        )
        expired_overrides = list(result.scalars().all())

        for override in expired_overrides:
            override.status = OverrideStatus.EXPIRED
            override.is_expired = True
            override.resolved_at = now

            # Create audit log
            audit_log = OverrideAuditLog(
                override_id=override.id,
                action=OverrideAuditAction.EXPIRED,
                action_at=now,
                previous_status=OverrideStatus.PENDING,
                new_status=OverrideStatus.EXPIRED,
                comment=f"Override request expired after {OVERRIDE_EXPIRY_DAYS} days",
            )
            self.db.add(audit_log)

        await self.db.commit()

        if expired_overrides:
            logger.info(f"Expired {len(expired_overrides)} override requests")

        return len(expired_overrides)

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_override_stats(
        self,
        project_id: Optional[UUID] = None,
        days: int = 30,
    ) -> dict:
        """Get override statistics for dashboard."""
        date_start = datetime.utcnow() - timedelta(days=days)

        base_filter = ValidationOverride.created_at >= date_start
        if project_id:
            base_filter = and_(base_filter, ValidationOverride.project_id == project_id)

        # Total count
        total_result = await self.db.execute(
            select(func.count()).select_from(ValidationOverride).where(base_filter)
        )
        total = total_result.scalar() or 0

        # By status
        status_result = await self.db.execute(
            select(
                ValidationOverride.status,
                func.count().label("count"),
            )
            .where(base_filter)
            .group_by(ValidationOverride.status)
        )
        by_status = {row.status.value: row.count for row in status_result.all()}

        # By type
        type_result = await self.db.execute(
            select(
                ValidationOverride.override_type,
                func.count().label("count"),
            )
            .where(base_filter)
            .group_by(ValidationOverride.override_type)
        )
        by_type = {row.override_type.value: row.count for row in type_result.all()}

        # Calculate rates
        approved = by_status.get("approved", 0)
        rejected = by_status.get("rejected", 0)
        resolved = approved + rejected
        approval_rate = (approved / resolved * 100) if resolved > 0 else 0

        return {
            "total": total,
            "by_status": by_status,
            "by_type": by_type,
            "approval_rate": approval_rate,
            "pending": by_status.get("pending", 0),
            "days": days,
        }

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _has_approver_role(self, user: User) -> bool:
        """Check if user has an approver role."""
        if user.is_superuser:
            return True

        user_roles = set(user.role_names) if hasattr(user, 'role_names') else set()
        return bool(user_roles & APPROVER_ROLES)


# Factory function
def get_override_service(db: AsyncSession) -> OverrideService:
    """Create OverrideService instance."""
    return OverrideService(db)
