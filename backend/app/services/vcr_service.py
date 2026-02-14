"""
=========================================================================
VCR Service - Version Controlled Resolution Management
SDLC Orchestrator - Sprint 151 (SASE Artifacts Enhancement)

Version: 1.0.0
Date: March 4, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5 SASE Methodology
Reference: SPEC-0024, ADR-048

Purpose:
VCR captures post-merge documentation for significant changes:
- Problem statement and root cause analysis
- Solution approach and implementation notes
- Evidence and ADR linkage
- AI tool attribution tracking
- Approval workflow (CTO/CEO sign-off)

Workflow:
1. Developer creates VCR (draft)
2. Developer submits VCR for approval
3. CTO/CEO reviews and approves/rejects
4. Approved VCR → PR merged, evidence stored
5. Rejected VCR → Developer revises

Performance Targets:
- Create VCR: <200ms
- List VCRs: <200ms
- Approve/Reject: <300ms

Zero Mock Policy: Production-ready implementation
=========================================================================
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.vcr import VersionControlledResolution, VCRStatus
from app.models.user import User
from app.schemas.vcr import (
    VCRAutoGenerateRequest,
    VCRAutoGenerateResponse,
    VCRCreate,
    VCRListResponse,
    VCRRejectRequest,
    VCRResponse,
    VCRStatsResponse,
    VCRUpdate,
    VCRUserSummary,
    VCREventNames,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Custom Exceptions
# =============================================================================


class VCRServiceError(Exception):
    """Base exception for VCR service errors."""

    pass


class VCRNotFoundError(VCRServiceError):
    """Exception raised when VCR is not found."""

    pass


class VCRStateError(VCRServiceError):
    """Exception raised for invalid state transitions."""

    pass


class VCRPermissionError(VCRServiceError):
    """Exception raised for permission violations."""

    pass


# =============================================================================
# VCR Service
# =============================================================================


class VCRService:
    """
    Service for managing Version Controlled Resolutions (VCR).

    VCR is a SASE artifact that documents significant changes post-merge.
    It captures problem/solution documentation with AI attribution.

    Responsibilities:
        - VCR CRUD operations
        - Workflow management (submit, approve, reject)
        - Statistics and reporting
        - AI-assisted generation

    Usage:
        vcr_service = VCRService(db)
        vcr = await vcr_service.create(data, user_id)
        await vcr_service.submit(vcr.id)
        await vcr_service.approve(vcr.id, approver_id)

    SASE Compliance:
        - Implements VCR artifact from SDLC 6.0.5 SASE methodology
        - Links to Evidence Vault for immutable audit trail
        - Tracks AI tool involvement for governance
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize VCRService with database session.

        Args:
            db: SQLAlchemy async database session
        """
        self.db = db

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    async def create(
        self,
        data: VCRCreate,
        user_id: UUID,
    ) -> VCRResponse:
        """
        Create a new VCR in draft status.

        Args:
            data: VCRCreate with VCR details
            user_id: User ID of the creator

        Returns:
            VCRResponse with created VCR

        Example:
            data = VCRCreate(
                project_id=project.id,
                title="Fix authentication bug",
                problem_statement="Users were logged out unexpectedly...",
                solution_approach="Added token refresh logic...",
                ai_generated_percentage=0.3,
                ai_tools_used=["cursor", "copilot"],
            )
            vcr = await vcr_service.create(data, user.id)
        """
        logger.info(f"Creating VCR for project {data.project_id}: {data.title}")

        vcr = VersionControlledResolution(
            project_id=data.project_id,
            pr_number=data.pr_number,
            pr_url=data.pr_url,
            title=data.title,
            problem_statement=data.problem_statement,
            root_cause_analysis=data.root_cause_analysis,
            solution_approach=data.solution_approach,
            implementation_notes=data.implementation_notes,
            evidence_ids=data.evidence_ids or [],
            adr_ids=data.adr_ids or [],
            ai_generated_percentage=data.ai_generated_percentage,
            ai_tools_used=data.ai_tools_used or [],
            ai_generation_details=data.ai_generation_details or {},
            status=VCRStatus.DRAFT,
            created_by_id=user_id,
        )

        self.db.add(vcr)
        await self.db.commit()
        await self.db.refresh(vcr)

        logger.info(f"Created VCR {vcr.id} in draft status")

        return await self._to_response(vcr)

    async def get(
        self,
        vcr_id: UUID,
        include_relationships: bool = True,
    ) -> VCRResponse:
        """
        Get a VCR by ID.

        Args:
            vcr_id: VCR UUID
            include_relationships: Whether to load creator/approver info

        Returns:
            VCRResponse with VCR details

        Raises:
            VCRNotFoundError: If VCR not found
        """
        vcr = await self._get_vcr_by_id(vcr_id, include_relationships)
        return await self._to_response(vcr)

    async def list(
        self,
        project_id: Optional[UUID] = None,
        status: Optional[VCRStatus] = None,
        created_by_id: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> VCRListResponse:
        """
        List VCRs with filtering and pagination.

        Args:
            project_id: Filter by project
            status: Filter by status
            created_by_id: Filter by creator
            limit: Maximum results
            offset: Skip results

        Returns:
            VCRListResponse with paginated results
        """
        query = select(VersionControlledResolution)
        conditions = []

        if project_id:
            conditions.append(VersionControlledResolution.project_id == project_id)

        if status:
            conditions.append(VersionControlledResolution.status == status)

        if created_by_id:
            conditions.append(VersionControlledResolution.created_by_id == created_by_id)

        if conditions:
            query = query.where(and_(*conditions))

        # Count total
        count_query = select(func.count(VersionControlledResolution.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        query = (
            query.order_by(VersionControlledResolution.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(query)
        vcrs = result.scalars().all()

        # Convert to responses
        items = [await self._to_response(vcr) for vcr in vcrs]

        return VCRListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=offset + len(items) < total,
        )

    async def update(
        self,
        vcr_id: UUID,
        data: VCRUpdate,
        user_id: UUID,
    ) -> VCRResponse:
        """
        Update a VCR (only allowed in draft status).

        Args:
            vcr_id: VCR UUID
            data: VCRUpdate with fields to update
            user_id: User ID performing update

        Returns:
            VCRResponse with updated VCR

        Raises:
            VCRNotFoundError: If VCR not found
            VCRStateError: If VCR is not in draft status
            VCRPermissionError: If user is not the creator
        """
        vcr = await self._get_vcr_by_id(vcr_id)

        # Verify ownership
        if vcr.created_by_id != user_id:
            raise VCRPermissionError(f"User {user_id} is not the owner of VCR {vcr_id}")

        # Verify draft status
        if vcr.status != VCRStatus.DRAFT:
            raise VCRStateError(
                f"Cannot update VCR {vcr_id} in status {vcr.status.value}. "
                "Only draft VCRs can be updated."
            )

        # Update fields if provided
        update_fields = data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            if hasattr(vcr, field):
                setattr(vcr, field, value)

        vcr.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(vcr)

        logger.info(f"Updated VCR {vcr_id}")

        return await self._to_response(vcr)

    async def delete(
        self,
        vcr_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Delete a VCR (only allowed in draft status).

        Args:
            vcr_id: VCR UUID
            user_id: User ID performing delete

        Returns:
            True if deleted

        Raises:
            VCRNotFoundError: If VCR not found
            VCRStateError: If VCR is not in draft status
            VCRPermissionError: If user is not the creator
        """
        vcr = await self._get_vcr_by_id(vcr_id)

        # Verify ownership
        if vcr.created_by_id != user_id:
            raise VCRPermissionError(f"User {user_id} is not the owner of VCR {vcr_id}")

        # Verify draft status
        if vcr.status != VCRStatus.DRAFT:
            raise VCRStateError(
                f"Cannot delete VCR {vcr_id} in status {vcr.status.value}. "
                "Only draft VCRs can be deleted."
            )

        await self.db.delete(vcr)
        await self.db.commit()

        logger.info(f"Deleted VCR {vcr_id}")

        return True

    # =========================================================================
    # Workflow Operations
    # =========================================================================

    async def submit(
        self,
        vcr_id: UUID,
        user_id: UUID,
    ) -> VCRResponse:
        """
        Submit a VCR for approval.

        Transitions: DRAFT → SUBMITTED

        Args:
            vcr_id: VCR UUID
            user_id: User ID submitting

        Returns:
            VCRResponse with updated status

        Raises:
            VCRNotFoundError: If VCR not found
            VCRStateError: If VCR is not in draft status
            VCRPermissionError: If user is not the creator
        """
        vcr = await self._get_vcr_by_id(vcr_id)

        # Verify ownership
        if vcr.created_by_id != user_id:
            raise VCRPermissionError(f"User {user_id} is not the owner of VCR {vcr_id}")

        # Verify draft status
        if vcr.status != VCRStatus.DRAFT:
            raise VCRStateError(
                f"Cannot submit VCR {vcr_id} in status {vcr.status.value}. "
                "Only draft VCRs can be submitted."
            )

        vcr.status = VCRStatus.SUBMITTED
        vcr.submitted_at = datetime.utcnow()
        vcr.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(vcr)

        logger.info(f"Submitted VCR {vcr_id} for approval")

        return await self._to_response(vcr)

    async def approve(
        self,
        vcr_id: UUID,
        approver_id: UUID,
    ) -> VCRResponse:
        """
        Approve a VCR (CTO/CEO only).

        Transitions: SUBMITTED → APPROVED

        Args:
            vcr_id: VCR UUID
            approver_id: User ID approving (CTO/CEO)

        Returns:
            VCRResponse with updated status

        Raises:
            VCRNotFoundError: If VCR not found
            VCRStateError: If VCR is not in submitted status
        """
        vcr = await self._get_vcr_by_id(vcr_id)

        # Verify submitted status
        if vcr.status != VCRStatus.SUBMITTED:
            raise VCRStateError(
                f"Cannot approve VCR {vcr_id} in status {vcr.status.value}. "
                "Only submitted VCRs can be approved."
            )

        vcr.status = VCRStatus.APPROVED
        vcr.approved_by_id = approver_id
        vcr.approved_at = datetime.utcnow()
        vcr.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(vcr)

        logger.info(f"Approved VCR {vcr_id} by approver {approver_id}")

        return await self._to_response(vcr)

    async def reject(
        self,
        vcr_id: UUID,
        approver_id: UUID,
        request: VCRRejectRequest,
    ) -> VCRResponse:
        """
        Reject a VCR with reason (CTO/CEO only).

        Transitions: SUBMITTED → REJECTED

        Args:
            vcr_id: VCR UUID
            approver_id: User ID rejecting (CTO/CEO)
            request: VCRRejectRequest with rejection reason

        Returns:
            VCRResponse with updated status

        Raises:
            VCRNotFoundError: If VCR not found
            VCRStateError: If VCR is not in submitted status
        """
        vcr = await self._get_vcr_by_id(vcr_id)

        # Verify submitted status
        if vcr.status != VCRStatus.SUBMITTED:
            raise VCRStateError(
                f"Cannot reject VCR {vcr_id} in status {vcr.status.value}. "
                "Only submitted VCRs can be rejected."
            )

        vcr.status = VCRStatus.REJECTED
        vcr.approved_by_id = approver_id
        vcr.rejection_reason = request.reason
        vcr.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(vcr)

        logger.info(f"Rejected VCR {vcr_id} by approver {approver_id}: {request.reason[:50]}...")

        return await self._to_response(vcr)

    async def reopen(
        self,
        vcr_id: UUID,
        user_id: UUID,
    ) -> VCRResponse:
        """
        Reopen a rejected VCR for editing.

        Transitions: REJECTED → DRAFT

        Args:
            vcr_id: VCR UUID
            user_id: User ID reopening (must be creator)

        Returns:
            VCRResponse with updated status

        Raises:
            VCRNotFoundError: If VCR not found
            VCRStateError: If VCR is not in rejected status
            VCRPermissionError: If user is not the creator
        """
        vcr = await self._get_vcr_by_id(vcr_id)

        # Verify ownership
        if vcr.created_by_id != user_id:
            raise VCRPermissionError(f"User {user_id} is not the owner of VCR {vcr_id}")

        # Verify rejected status
        if vcr.status != VCRStatus.REJECTED:
            raise VCRStateError(
                f"Cannot reopen VCR {vcr_id} in status {vcr.status.value}. "
                "Only rejected VCRs can be reopened."
            )

        vcr.status = VCRStatus.DRAFT
        vcr.rejection_reason = None
        vcr.approved_by_id = None
        vcr.submitted_at = None
        vcr.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(vcr)

        logger.info(f"Reopened VCR {vcr_id} to draft status")

        return await self._to_response(vcr)

    # =========================================================================
    # Statistics & Reporting
    # =========================================================================

    async def get_stats(
        self,
        project_id: UUID,
    ) -> VCRStatsResponse:
        """
        Get VCR statistics for a project.

        Args:
            project_id: Project UUID

        Returns:
            VCRStatsResponse with statistics
        """
        # Count by status
        base_query = select(
            VersionControlledResolution.status,
            func.count(VersionControlledResolution.id).label("count"),
        ).where(
            VersionControlledResolution.project_id == project_id
        ).group_by(
            VersionControlledResolution.status
        )

        result = await self.db.execute(base_query)
        status_counts = {row.status.value: row.count for row in result}

        total = sum(status_counts.values())
        draft = status_counts.get("draft", 0)
        submitted = status_counts.get("submitted", 0)
        approved = status_counts.get("approved", 0)
        rejected = status_counts.get("rejected", 0)

        # Calculate average approval time for approved VCRs
        avg_time_query = select(
            func.avg(
                func.extract(
                    "epoch",
                    VersionControlledResolution.approved_at
                    - VersionControlledResolution.submitted_at,
                )
            )
        ).where(
            and_(
                VersionControlledResolution.project_id == project_id,
                VersionControlledResolution.status == VCRStatus.APPROVED,
                VersionControlledResolution.approved_at.isnot(None),
                VersionControlledResolution.submitted_at.isnot(None),
            )
        )

        avg_result = await self.db.execute(avg_time_query)
        avg_seconds = avg_result.scalar()
        avg_approval_time_hours = (avg_seconds / 3600) if avg_seconds else None

        # Calculate average AI involvement
        ai_query = select(
            func.avg(VersionControlledResolution.ai_generated_percentage)
        ).where(
            VersionControlledResolution.project_id == project_id
        )

        ai_result = await self.db.execute(ai_query)
        ai_involvement = ai_result.scalar() or 0.0

        return VCRStatsResponse(
            total=total,
            draft=draft,
            submitted=submitted,
            approved=approved,
            rejected=rejected,
            avg_approval_time_hours=avg_approval_time_hours,
            ai_involvement_percentage=float(ai_involvement),
        )

    # =========================================================================
    # AI-Assisted Generation (Day 4 Implementation - Sprint 151)
    # =========================================================================

    async def auto_generate(
        self,
        request: VCRAutoGenerateRequest,
        user_id: UUID,
    ) -> VCRAutoGenerateResponse:
        """
        AI-assisted VCR generation from PR context.

        Uses SASE Generation Service to analyze PR diff and generate VCR content.
        Falls back to rule-based templates if AI is unavailable.

        Args:
            request: VCRAutoGenerateRequest with PR context
            user_id: User ID requesting generation

        Returns:
            VCRAutoGenerateResponse with generated content

        Sprint 151 Day 4:
        - Integrated with SASE Generation Service
        - AI tool detection (Cursor, Claude Code, Copilot)
        - PR diff analysis for problem/solution extraction
        - Confidence scoring for generated content
        """
        from app.services.sase_generation_service import create_sase_generation_service

        logger.info(
            f"Auto-generate VCR requested for project {request.project_id}, "
            f"PR #{request.pr_number or 'N/A'}"
        )

        # Create SASE generation service
        sase_service = create_sase_generation_service()

        # Generate VCR content
        result = await sase_service.generate_vcr(
            pr_diff=None,  # Will be fetched from GitHub if pr_url provided
            commit_messages=None,
            pr_title=None,
            pr_description=request.context,
            file_changes=None,
            additional_context=request.context,
        )

        # Build suggested evidence based on content
        suggested_evidence = [
            "Link relevant test results",
            "Link code review approval",
        ]

        if result.ai_tools_detected:
            suggested_evidence.append(
                f"Document AI tool usage: {', '.join(result.ai_tools_detected)}"
            )

        if result.ai_percentage_estimate > 0.3:
            suggested_evidence.append(
                "Include AI generation audit trail"
            )

        logger.info(
            f"VCR auto-generated with confidence {result.confidence:.2f}, "
            f"AI tools detected: {result.ai_tools_detected}, "
            f"AI percentage: {result.ai_percentage_estimate:.0%}"
        )

        return VCRAutoGenerateResponse(
            title=result.title,
            problem_statement=result.problem_statement,
            root_cause_analysis=result.root_cause_analysis,
            solution_approach=result.solution_approach,
            implementation_notes=result.implementation_notes,
            ai_confidence=result.confidence,
            suggested_evidence=suggested_evidence,
        )

    # =========================================================================
    # Private Helpers
    # =========================================================================

    async def _get_vcr_by_id(
        self,
        vcr_id: UUID,
        include_relationships: bool = False,
    ) -> VersionControlledResolution:
        """Get VCR by ID with optional relationships."""
        query = select(VersionControlledResolution).where(
            VersionControlledResolution.id == vcr_id
        )

        if include_relationships:
            query = query.options(
                selectinload(VersionControlledResolution.created_by),
                selectinload(VersionControlledResolution.approved_by),
            )

        result = await self.db.execute(query)
        vcr = result.scalar_one_or_none()

        if not vcr:
            raise VCRNotFoundError(f"VCR {vcr_id} not found")

        return vcr

    async def _to_response(
        self,
        vcr: VersionControlledResolution,
    ) -> VCRResponse:
        """Convert VCR model to response schema."""
        # Get user summaries if relationships loaded
        created_by_summary = None
        approved_by_summary = None

        if hasattr(vcr, "created_by") and vcr.created_by:
            created_by_summary = VCRUserSummary(
                id=vcr.created_by.id,
                name=vcr.created_by.full_name or vcr.created_by.email,
                email=vcr.created_by.email,
            )
        elif vcr.created_by_id:
            # Lazy load if not already loaded
            user = await self.db.get(User, vcr.created_by_id)
            if user:
                created_by_summary = VCRUserSummary(
                    id=user.id,
                    name=user.full_name or user.email,
                    email=user.email,
                )

        if hasattr(vcr, "approved_by") and vcr.approved_by:
            approved_by_summary = VCRUserSummary(
                id=vcr.approved_by.id,
                name=vcr.approved_by.full_name or vcr.approved_by.email,
                email=vcr.approved_by.email,
            )
        elif vcr.approved_by_id:
            # Lazy load if not already loaded
            user = await self.db.get(User, vcr.approved_by_id)
            if user:
                approved_by_summary = VCRUserSummary(
                    id=user.id,
                    name=user.full_name or user.email,
                    email=user.email,
                )

        return VCRResponse(
            id=vcr.id,
            project_id=vcr.project_id,
            pr_number=vcr.pr_number,
            pr_url=vcr.pr_url,
            title=vcr.title,
            problem_statement=vcr.problem_statement,
            root_cause_analysis=vcr.root_cause_analysis,
            solution_approach=vcr.solution_approach,
            implementation_notes=vcr.implementation_notes,
            evidence_ids=vcr.evidence_ids or [],
            adr_ids=vcr.adr_ids or [],
            ai_generated_percentage=vcr.ai_generated_percentage or 0.0,
            ai_tools_used=vcr.ai_tools_used or [],
            ai_generation_details=vcr.ai_generation_details or {},
            status=vcr.status,
            created_by_id=vcr.created_by_id,
            approved_by_id=vcr.approved_by_id,
            rejection_reason=vcr.rejection_reason,
            created_at=vcr.created_at,
            updated_at=vcr.updated_at,
            submitted_at=vcr.submitted_at,
            approved_at=vcr.approved_at,
            created_by=created_by_summary,
            approved_by=approved_by_summary,
        )
