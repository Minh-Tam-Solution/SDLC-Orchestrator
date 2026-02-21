"""
=========================================================================
CRP Service - Consultation Request Protocol Management
SDLC Orchestrator - Sprint 101 (Risk-Based Planning Trigger)

Version: 1.0.0
Date: January 23, 2026
Status: ACTIVE - Sprint 101 Implementation
Authority: Backend Lead + CTO Approved
Reference: docs/04-build/02-Sprint-Plans/SPRINT-101-DESIGN.md
Reference: SDLC 5.2.0 AI Governance - Consultation Request Protocol

Purpose:
- Create and manage consultation requests for high-risk changes
- Assign reviewers based on required expertise
- Track resolution workflow (approve/reject)
- Maintain audit trail for compliance

CRP Workflow:
1. AI detects high-risk change (risk_score > 70)
2. CRPService.create_consultation() called
3. Reviewer assigned based on expertise
4. Human reviews via dashboard
5. CRPService.resolve_consultation() records decision

Performance Targets:
- Create consultation: <500ms
- Query consultations: <200ms
- Resolve consultation: <500ms

Zero Mock Policy: Production-ready implementation
=========================================================================
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.consultation_request import ConsultationComment, ConsultationRequest
from app.models.user import User
from app.schemas.crp import (
    AddCommentRequest,
    AssignReviewerRequest,
    ConsultationCommentResponse,
    ConsultationFilters,
    ConsultationListResponse,
    ConsultationPriority,
    ConsultationResponse,
    ConsultationStatus,
    CreateConsultationRequest,
    ResolveConsultationRequest,
    ReviewerExpertise,
)
from app.schemas.risk_analysis import RiskAnalysis

logger = logging.getLogger(__name__)


class CRPService:
    """
    Manages Consultation Request Protocol (CRP) workflow.

    Key responsibilities:
    - Create consultation requests from risk analysis
    - Assign reviewers based on expertise
    - Track resolution (approve/reject)
    - Query and filter consultations

    Usage:
        crp_service = CRPService(db)
        consultation = await crp_service.create_consultation(
            request=CreateConsultationRequest(...),
            requester_id=user.id,
        )

    SDLC 5.2.0 Compliance:
        - Implements human oversight for high-risk AI changes
        - Maintains audit trail for compliance
        - Integrates with Evidence Vault
    """

    def __init__(self, db: AsyncSession):
        """Initialize CRPService with database session."""
        self.db = db

    async def create_consultation(
        self,
        request: CreateConsultationRequest,
        requester_id: UUID,
        risk_analysis: RiskAnalysis,
    ) -> ConsultationResponse:
        """
        Create a new consultation request.

        Called when RiskFactorDetectorService detects high-risk change.

        Args:
            request: CreateConsultationRequest with details
            requester_id: User ID of the requester
            risk_analysis: RiskAnalysis that triggered the consultation

        Returns:
            ConsultationResponse with created consultation

        Example:
            request = CreateConsultationRequest(
                project_id=project.id,
                risk_analysis_id=analysis.id,
                title="High-risk auth changes",
                description="Changes to authentication flow...",
            )
            consultation = await crp_service.create_consultation(
                request, user.id, analysis
            )
        """
        logger.info(
            f"Creating consultation for project {request.project_id}: {request.title}"
        )

        consultation = ConsultationRequest(
            project_id=request.project_id,
            pr_id=request.pr_id,
            risk_analysis_id=request.risk_analysis_id,
            risk_analysis=risk_analysis.model_dump(),
            title=request.title,
            description=request.description,
            priority=request.priority.value,
            required_expertise=[e.value for e in request.required_expertise],
            diff_url=request.diff_url,
            status=ConsultationStatus.PENDING.value,
            requester_id=requester_id,
        )

        self.db.add(consultation)
        await self.db.commit()
        await self.db.refresh(consultation)

        logger.info(f"Created consultation {consultation.id}")

        return await self._to_response(consultation)

    async def assign_reviewer(
        self,
        consultation_id: UUID,
        request: AssignReviewerRequest,
        assigned_by: UUID,
    ) -> ConsultationResponse:
        """
        Assign a reviewer to a consultation.

        Args:
            consultation_id: ID of the consultation
            request: AssignReviewerRequest with reviewer_id
            assigned_by: User ID who is assigning

        Returns:
            ConsultationResponse with updated consultation

        Raises:
            ValueError: If consultation not found or already resolved
        """
        consultation = await self._get_consultation_by_id(consultation_id)

        if consultation.is_resolved:
            raise ValueError(f"Consultation {consultation_id} is already resolved")

        consultation.assigned_reviewer_id = request.reviewer_id
        consultation.assigned_at = datetime.utcnow()
        consultation.status = ConsultationStatus.IN_REVIEW.value
        consultation.updated_at = datetime.utcnow()

        # Add assignment note as comment if provided
        if request.notes:
            comment = ConsultationComment(
                consultation_id=consultation_id,
                user_id=assigned_by,
                comment=f"Reviewer assigned: {request.notes}",
                is_resolution_note=False,
            )
            self.db.add(comment)

        await self.db.commit()
        await self.db.refresh(consultation)

        logger.info(f"Assigned reviewer {request.reviewer_id} to consultation {consultation_id}")

        return await self._to_response(consultation)

    async def resolve_consultation(
        self,
        consultation_id: UUID,
        request: ResolveConsultationRequest,
        resolved_by: UUID,
    ) -> ConsultationResponse:
        """
        Resolve a consultation (approve/reject).

        Args:
            consultation_id: ID of the consultation
            request: ResolveConsultationRequest with decision
            resolved_by: User ID who is resolving

        Returns:
            ConsultationResponse with resolved consultation

        Raises:
            ValueError: If consultation not found or already resolved
        """
        consultation = await self._get_consultation_by_id(consultation_id)

        if consultation.is_resolved:
            raise ValueError(f"Consultation {consultation_id} is already resolved")

        # Validate status transition
        valid_resolutions = [
            ConsultationStatus.APPROVED,
            ConsultationStatus.REJECTED,
            ConsultationStatus.CANCELLED,
        ]
        if request.status not in valid_resolutions:
            raise ValueError(f"Invalid resolution status: {request.status}")

        consultation.status = request.status.value
        consultation.resolution_notes = request.resolution_notes
        consultation.conditions = request.conditions
        consultation.resolved_at = datetime.utcnow()
        consultation.resolved_by_id = resolved_by
        consultation.updated_at = datetime.utcnow()

        # Add resolution note as comment
        comment = ConsultationComment(
            consultation_id=consultation_id,
            user_id=resolved_by,
            comment=f"**{request.status.value.upper()}**: {request.resolution_notes}",
            is_resolution_note=True,
        )
        self.db.add(comment)

        await self.db.commit()
        await self.db.refresh(consultation)

        logger.info(
            f"Resolved consultation {consultation_id} with status {request.status.value}"
        )

        return await self._to_response(consultation)

    async def add_comment(
        self,
        consultation_id: UUID,
        request: AddCommentRequest,
        user_id: UUID,
    ) -> ConsultationCommentResponse:
        """
        Add a comment to a consultation.

        Args:
            consultation_id: ID of the consultation
            request: AddCommentRequest with comment text
            user_id: User ID of the commenter

        Returns:
            ConsultationCommentResponse with created comment

        Raises:
            ValueError: If consultation not found
        """
        # Verify consultation exists
        await self._get_consultation_by_id(consultation_id)

        comment = ConsultationComment(
            consultation_id=consultation_id,
            user_id=user_id,
            comment=request.comment,
            is_resolution_note=request.is_resolution_note,
        )

        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)

        logger.info(f"Added comment to consultation {consultation_id}")

        return ConsultationCommentResponse(
            id=comment.id,
            consultation_id=comment.consultation_id,
            user_id=comment.user_id,
            comment=comment.comment,
            is_resolution_note=comment.is_resolution_note,
            created_at=comment.created_at,
        )

    async def get_consultation(
        self,
        consultation_id: UUID,
        include_comments: bool = True,
    ) -> ConsultationResponse:
        """
        Get a single consultation by ID.

        Args:
            consultation_id: ID of the consultation
            include_comments: Whether to include comments

        Returns:
            ConsultationResponse with consultation details
        """
        consultation = await self._get_consultation_by_id(
            consultation_id, include_comments=include_comments
        )
        return await self._to_response(consultation)

    async def list_consultations(
        self,
        filters: ConsultationFilters,
    ) -> ConsultationListResponse:
        """
        List consultations with filtering and pagination.

        Args:
            filters: ConsultationFilters with query parameters

        Returns:
            ConsultationListResponse with paginated results
        """
        query = select(ConsultationRequest)

        # Apply filters
        conditions = []

        if filters.project_id:
            conditions.append(ConsultationRequest.project_id == filters.project_id)

        if filters.status:
            conditions.append(ConsultationRequest.status == filters.status.value)

        if filters.priority:
            conditions.append(ConsultationRequest.priority == filters.priority.value)

        if filters.requester_id:
            conditions.append(ConsultationRequest.requester_id == filters.requester_id)

        if filters.reviewer_id:
            conditions.append(
                ConsultationRequest.assigned_reviewer_id == filters.reviewer_id
            )

        if filters.expertise:
            # Check if expertise is in required_expertise array
            conditions.append(
                ConsultationRequest.required_expertise.contains([filters.expertise.value])
            )

        if filters.search:
            search_pattern = f"%{filters.search}%"
            conditions.append(
                or_(
                    ConsultationRequest.title.ilike(search_pattern),
                    ConsultationRequest.description.ilike(search_pattern),
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        # Count total
        count_query = select(func.count(ConsultationRequest.id)).where(and_(*conditions)) if conditions else select(func.count(ConsultationRequest.id))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (filters.page - 1) * filters.page_size
        query = query.order_by(ConsultationRequest.created_at.desc())
        query = query.offset(offset).limit(filters.page_size)

        result = await self.db.execute(query)
        consultations = result.scalars().all()

        # Convert to responses
        responses = [await self._to_response(c) for c in consultations]

        return ConsultationListResponse(
            consultations=responses,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            has_more=offset + len(responses) < total,
        )

    async def get_pending_for_reviewer(
        self,
        reviewer_id: UUID,
    ) -> list[ConsultationResponse]:
        """
        Get pending consultations assigned to a reviewer.

        Args:
            reviewer_id: User ID of the reviewer

        Returns:
            List of pending consultations
        """
        query = (
            select(ConsultationRequest)
            .where(
                and_(
                    ConsultationRequest.assigned_reviewer_id == reviewer_id,
                    ConsultationRequest.status.in_([
                        ConsultationStatus.PENDING.value,
                        ConsultationStatus.IN_REVIEW.value,
                    ]),
                )
            )
            .order_by(ConsultationRequest.priority.desc(), ConsultationRequest.created_at.asc())
        )

        result = await self.db.execute(query)
        consultations = result.scalars().all()

        return [await self._to_response(c) for c in consultations]

    async def auto_assign_reviewer(
        self,
        consultation_id: UUID,
    ) -> Optional[UUID]:
        """
        Auto-assign a reviewer based on required expertise.

        This is a placeholder for future smart assignment logic.
        Currently returns None (manual assignment required).

        Args:
            consultation_id: ID of the consultation

        Returns:
            UUID of assigned reviewer or None
        """
        # TODO: Implement smart reviewer assignment based on:
        # 1. Required expertise
        # 2. Reviewer availability
        # 3. Reviewer workload
        # 4. Past review performance

        logger.info(
            f"Auto-assignment not implemented for consultation {consultation_id}. "
            "Manual assignment required."
        )
        return None

    # =========================================================================
    # AI-Assisted Generation (Sprint 151 Day 4)
    # =========================================================================

    async def auto_generate(
        self,
        context: str,
        code_snippet: Optional[str] = None,
        related_files: Optional[list[str]] = None,
        project_tech_stack: Optional[list[str]] = None,
    ) -> dict:
        """
        AI-assisted CRP generation from development context.

        Uses SASE Generation Service to analyze context and generate CRP content.
        Falls back to rule-based templates if AI is unavailable.

        Args:
            context: Description of the situation needing consultation
            code_snippet: Relevant code snippet
            related_files: List of related file paths
            project_tech_stack: Project's technology stack

        Returns:
            dict with generated CRP content:
                - title: Generated title
                - question: The specific question
                - context: Background information
                - options_considered: List of options
                - recommendation: Suggested approach
                - impact_assessment: Impact analysis
                - required_expertise: List of expertise types
                - priority_suggestion: Suggested priority
                - confidence: AI confidence score

        Sprint 151 Day 4:
        - Integrated with SASE Generation Service
        - Context analysis for expertise detection
        - Priority inference from keywords
        - Option generation with pros/cons
        """
        from app.services.sase_adapter import create_sase_generation_service

        logger.info("Auto-generate CRP requested")

        # Create SASE generation service
        sase_service = create_sase_generation_service()

        # Generate CRP content
        result = await sase_service.generate_crp(
            context=context,
            code_snippet=code_snippet,
            related_files=related_files,
            project_tech_stack=project_tech_stack,
        )

        logger.info(
            f"CRP auto-generated with confidence {result.confidence:.2f}, "
            f"expertise: {result.required_expertise}, "
            f"priority: {result.priority_suggestion}"
        )

        return {
            "title": result.title,
            "question": result.question,
            "context": result.context,
            "options_considered": result.options_considered,
            "recommendation": result.recommendation,
            "impact_assessment": result.impact_assessment,
            "required_expertise": result.required_expertise,
            "priority_suggestion": result.priority_suggestion,
            "confidence": result.confidence,
            "generation_time_ms": result.generation_time_ms,
            "provider_used": result.provider_used,
            "fallback_used": result.fallback_used,
        }

    # =========================================================================
    # Private Helpers
    # =========================================================================

    async def _get_consultation_by_id(
        self,
        consultation_id: UUID,
        include_comments: bool = False,
    ) -> ConsultationRequest:
        """Get consultation by ID with optional comments."""
        query = select(ConsultationRequest).where(
            ConsultationRequest.id == consultation_id
        )

        if include_comments:
            query = query.options(selectinload(ConsultationRequest.comments))

        result = await self.db.execute(query)
        consultation = result.scalar_one_or_none()

        if not consultation:
            raise ValueError(f"Consultation {consultation_id} not found")

        return consultation

    async def _to_response(
        self,
        consultation: ConsultationRequest,
    ) -> ConsultationResponse:
        """Convert model to response schema."""
        # Get user names (join query would be more efficient in production)
        requester_name = None
        reviewer_name = None

        if consultation.requester_id:
            requester = await self.db.get(User, consultation.requester_id)
            if requester:
                requester_name = requester.full_name or requester.email

        if consultation.assigned_reviewer_id:
            reviewer = await self.db.get(User, consultation.assigned_reviewer_id)
            if reviewer:
                reviewer_name = reviewer.full_name or reviewer.email

        # Convert comments if loaded
        comments = None
        if hasattr(consultation, 'comments') and consultation.comments is not None:
            comments = [
                ConsultationCommentResponse(
                    id=c.id,
                    consultation_id=c.consultation_id,
                    user_id=c.user_id,
                    comment=c.comment,
                    is_resolution_note=c.is_resolution_note,
                    created_at=c.created_at,
                )
                for c in consultation.comments
            ]

        return ConsultationResponse(
            id=consultation.id,
            project_id=consultation.project_id,
            pr_id=consultation.pr_id,
            risk_analysis_id=consultation.risk_analysis_id,
            risk_analysis=RiskAnalysis(**consultation.risk_analysis) if consultation.risk_analysis else None,
            title=consultation.title,
            description=consultation.description,
            priority=ConsultationPriority(consultation.priority),
            required_expertise=[ReviewerExpertise(e) for e in consultation.required_expertise],
            diff_url=consultation.diff_url,
            status=ConsultationStatus(consultation.status),
            requester_id=consultation.requester_id,
            requester_name=requester_name,
            assigned_reviewer_id=consultation.assigned_reviewer_id,
            reviewer_name=reviewer_name,
            resolution_notes=consultation.resolution_notes,
            conditions=consultation.conditions,
            resolved_at=consultation.resolved_at,
            resolved_by_id=consultation.resolved_by_id,
            created_at=consultation.created_at,
            updated_at=consultation.updated_at,
            comments=comments,
            comment_count=len(comments) if comments else consultation.comment_count,
        )
