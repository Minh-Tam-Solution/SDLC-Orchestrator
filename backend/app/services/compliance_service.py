"""
=========================================================================
Compliance Service - Shared Compliance Framework Management
SDLC Orchestrator - Sprint 156 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: April 7, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5
Reference: ADR-051

Purpose:
Provides shared compliance framework management across 3 regulatory standards:
- NIST AI RMF (GOVERN, MAP, MEASURE, MANAGE)
- EU AI Act (4-level risk classification)
- ISO 42001 (38 management system controls)

Operations:
- List/get compliance frameworks with control counts
- List/create/update compliance assessments per project per control
- Pagination, filtering, and structured logging throughout

Performance Targets:
- List frameworks: <100ms
- List assessments: <200ms
- Create/update assessment: <200ms

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

from app.models.compliance import (
    AssessmentStatus,
    ComplianceAssessment,
    ComplianceControl,
    ComplianceFramework,
)
from app.models.user import User
from app.schemas.compliance_framework import (
    AssessmentCreate,
    AssessmentListResponse,
    AssessmentResponse,
    AssessmentUpdate,
    ControlResponse,
    FrameworkListResponse,
    FrameworkResponse,
    UserSummary,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Custom Exceptions
# =============================================================================


class ComplianceServiceError(Exception):
    """Base exception for compliance service errors."""

    pass


class ComplianceNotFoundError(ComplianceServiceError):
    """Exception raised when a compliance resource is not found."""

    pass


class ComplianceValidationError(ComplianceServiceError):
    """Exception raised when compliance data fails validation."""

    pass


# =============================================================================
# Compliance Service
# =============================================================================


class ComplianceService:
    """
    Service for managing compliance frameworks, controls, and assessments.

    Provides shared compliance operations used by NIST AI RMF, EU AI Act,
    and ISO 42001 route handlers. Centralizes framework lookup, assessment
    CRUD, and pagination logic.

    Responsibilities:
        - Framework registry queries (list, get by code)
        - Assessment CRUD with project/control scoping
        - Pagination and filtering for assessment lists
        - Assessor tracking and timestamp management

    Usage:
        service = ComplianceService(db)
        frameworks = await service.list_frameworks(active_only=True)
        assessment = await service.create_assessment(data, assessor_id)

    SASE Compliance:
        - Implements compliance management from ADR-051
        - Links to Evidence Vault via evidence_ids
        - Supports OPA-based automated evaluation
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize ComplianceService with database session.

        Args:
            db: SQLAlchemy async database session
        """
        self.db = db

    # =========================================================================
    # Framework Operations
    # =========================================================================

    async def list_frameworks(
        self,
        active_only: bool = True,
    ) -> FrameworkListResponse:
        """
        List compliance frameworks with optional active-only filtering.

        Retrieves all registered compliance frameworks (NIST AI RMF,
        EU AI Act, ISO 42001) with their metadata and control counts.

        Args:
            active_only: If True, return only active frameworks.
                Defaults to True.

        Returns:
            FrameworkListResponse containing the list of frameworks
            and total count.

        Example:
            service = ComplianceService(db)
            result = await service.list_frameworks(active_only=True)
            for fw in result.items:
                print(f"{fw.code}: {fw.total_controls} controls")
        """
        logger.info(
            "Listing compliance frameworks",
            extra={"active_only": active_only},
        )

        query = select(ComplianceFramework)

        if active_only:
            query = query.where(ComplianceFramework.is_active.is_(True))

        query = query.order_by(ComplianceFramework.code.asc())

        result = await self.db.execute(query)
        frameworks = result.scalars().all()

        items = [
            FrameworkResponse(
                id=fw.id,
                code=fw.code,
                name=fw.name,
                version=fw.version,
                description=fw.description,
                total_controls=fw.total_controls,
                is_active=fw.is_active,
                created_at=fw.created_at,
                updated_at=fw.updated_at,
            )
            for fw in frameworks
        ]

        logger.info(
            "Listed %d compliance frameworks",
            len(items),
            extra={"active_only": active_only, "count": len(items)},
        )

        return FrameworkListResponse(
            items=items,
            total=len(items),
        )

    async def get_framework(
        self,
        code: str,
    ) -> FrameworkResponse:
        """
        Get a compliance framework by its unique code.

        Looks up the framework and returns it along with a live count
        of associated controls from the compliance_controls table.

        Args:
            code: Framework code string (e.g., "NIST_AI_RMF",
                "EU_AI_ACT", "ISO_42001").

        Returns:
            FrameworkResponse with framework details and current
            control count.

        Raises:
            ComplianceNotFoundError: If no framework matches the
                given code.

        Example:
            service = ComplianceService(db)
            nist = await service.get_framework("NIST_AI_RMF")
            print(f"{nist.name} v{nist.version}: {nist.total_controls} controls")
        """
        logger.info(
            "Getting compliance framework",
            extra={"framework_code": code},
        )

        query = select(ComplianceFramework).where(
            ComplianceFramework.code == code
        )

        result = await self.db.execute(query)
        framework = result.scalar_one_or_none()

        if not framework:
            raise ComplianceNotFoundError(
                f"Compliance framework with code '{code}' not found"
            )

        # Get live control count from the controls table
        count_query = select(func.count(ComplianceControl.id)).where(
            ComplianceControl.framework_id == framework.id
        )
        count_result = await self.db.execute(count_query)
        control_count = count_result.scalar() or 0

        logger.info(
            "Found framework %s with %d controls",
            code,
            control_count,
            extra={"framework_code": code, "control_count": control_count},
        )

        return FrameworkResponse(
            id=framework.id,
            code=framework.code,
            name=framework.name,
            version=framework.version,
            description=framework.description,
            total_controls=control_count,
            is_active=framework.is_active,
            created_at=framework.created_at,
            updated_at=framework.updated_at,
        )

    # =========================================================================
    # Assessment Operations
    # =========================================================================

    async def list_assessments(
        self,
        project_id: UUID,
        framework_code: Optional[str] = None,
        status_filter: Optional[AssessmentStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> AssessmentListResponse:
        """
        List compliance assessments with filtering and pagination.

        Returns assessments for a given project, optionally filtered
        by framework code and/or assessment status. Results include
        the associated control and assessor information.

        Args:
            project_id: UUID of the project to list assessments for.
            framework_code: Optional framework code to filter by
                (e.g., "NIST_AI_RMF"). When provided, only assessments
                for controls belonging to that framework are returned.
            status_filter: Optional AssessmentStatus enum to filter by
                (e.g., AssessmentStatus.COMPLIANT).
            limit: Maximum number of results to return. Defaults to 20.
            offset: Number of results to skip. Defaults to 0.

        Returns:
            AssessmentListResponse with paginated assessment items,
            total count, and pagination metadata.

        Example:
            service = ComplianceService(db)
            result = await service.list_assessments(
                project_id=project.id,
                framework_code="EU_AI_ACT",
                status_filter=AssessmentStatus.NON_COMPLIANT,
                limit=10,
                offset=0,
            )
            print(f"Found {result.total} assessments, showing {len(result.items)}")
        """
        logger.info(
            "Listing compliance assessments",
            extra={
                "project_id": str(project_id),
                "framework_code": framework_code,
                "status_filter": status_filter.value if status_filter else None,
                "limit": limit,
                "offset": offset,
            },
        )

        # Build filter conditions
        conditions: List = [
            ComplianceAssessment.project_id == project_id,
        ]

        # If filtering by framework, join through controls to framework
        if framework_code:
            framework_query = select(ComplianceFramework.id).where(
                ComplianceFramework.code == framework_code
            )
            framework_result = await self.db.execute(framework_query)
            framework_id = framework_result.scalar_one_or_none()

            if not framework_id:
                raise ComplianceNotFoundError(
                    f"Compliance framework with code '{framework_code}' not found"
                )

            # Get control IDs for this framework
            control_ids_query = select(ComplianceControl.id).where(
                ComplianceControl.framework_id == framework_id
            )
            control_ids_result = await self.db.execute(control_ids_query)
            control_ids = [row[0] for row in control_ids_result.all()]

            if control_ids:
                conditions.append(
                    ComplianceAssessment.control_id.in_(control_ids)
                )
            else:
                # No controls for this framework means no assessments
                return AssessmentListResponse(
                    items=[],
                    total=0,
                    limit=limit,
                    offset=offset,
                    has_more=False,
                )

        if status_filter:
            conditions.append(
                ComplianceAssessment.status == status_filter.value
            )

        # Count total matching assessments
        count_query = select(func.count(ComplianceAssessment.id)).where(
            and_(*conditions)
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Fetch paginated assessments with relationships
        query = (
            select(ComplianceAssessment)
            .where(and_(*conditions))
            .options(
                selectinload(ComplianceAssessment.control),
                selectinload(ComplianceAssessment.assessor),
            )
            .order_by(ComplianceAssessment.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(query)
        assessments = result.scalars().all()

        items = [
            await self._to_assessment_response(assessment)
            for assessment in assessments
        ]

        logger.info(
            "Listed %d of %d compliance assessments",
            len(items),
            total,
            extra={
                "project_id": str(project_id),
                "returned": len(items),
                "total": total,
            },
        )

        return AssessmentListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=offset + len(items) < total,
        )

    async def create_assessment(
        self,
        data: AssessmentCreate,
        assessor_id: UUID,
    ) -> AssessmentResponse:
        """
        Create a new compliance assessment for a project control.

        Validates that the referenced control exists, then creates
        the assessment record with the specified status and evidence.
        Sets the assessed_at timestamp if the status is beyond
        NOT_STARTED.

        Args:
            data: AssessmentCreate schema with project_id, control_id,
                status, evidence_ids, and optional notes.
            assessor_id: UUID of the user performing the assessment.

        Returns:
            AssessmentResponse with the newly created assessment.

        Raises:
            ComplianceNotFoundError: If the referenced control does
                not exist.
            ComplianceValidationError: If a duplicate assessment
                already exists for the same project and control.

        Example:
            data = AssessmentCreate(
                project_id=project.id,
                control_id=control.id,
                status=AssessmentStatus.IN_PROGRESS,
                evidence_ids=[evidence_1.id],
                notes="Initial assessment started",
            )
            assessment = await service.create_assessment(data, user.id)
        """
        logger.info(
            "Creating compliance assessment",
            extra={
                "project_id": str(data.project_id),
                "control_id": str(data.control_id),
                "assessor_id": str(assessor_id),
                "status": data.status.value,
            },
        )

        # Validate control exists
        control_query = select(ComplianceControl).where(
            ComplianceControl.id == data.control_id
        )
        control_result = await self.db.execute(control_query)
        control = control_result.scalar_one_or_none()

        if not control:
            raise ComplianceNotFoundError(
                f"Compliance control with ID '{data.control_id}' not found"
            )

        # Check for duplicate assessment (same project + control)
        duplicate_query = select(ComplianceAssessment.id).where(
            and_(
                ComplianceAssessment.project_id == data.project_id,
                ComplianceAssessment.control_id == data.control_id,
            )
        )
        duplicate_result = await self.db.execute(duplicate_query)
        existing = duplicate_result.scalar_one_or_none()

        if existing:
            raise ComplianceValidationError(
                f"Assessment already exists for project '{data.project_id}' "
                f"and control '{data.control_id}'. Use update instead."
            )

        # Determine assessed_at based on status
        assessed_at = None
        if data.status != AssessmentStatus.NOT_STARTED:
            assessed_at = datetime.utcnow()

        assessment = ComplianceAssessment(
            project_id=data.project_id,
            control_id=data.control_id,
            status=data.status.value,
            evidence_ids=data.evidence_ids or [],
            assessor_id=assessor_id,
            notes=data.notes,
            auto_evaluated=False,
            assessed_at=assessed_at,
        )

        self.db.add(assessment)
        await self.db.commit()
        await self.db.refresh(assessment)

        logger.info(
            "Created compliance assessment %s",
            assessment.id,
            extra={
                "assessment_id": str(assessment.id),
                "project_id": str(data.project_id),
                "control_id": str(data.control_id),
                "status": data.status.value,
            },
        )

        return await self._to_assessment_response(assessment)

    async def update_assessment(
        self,
        assessment_id: UUID,
        data: AssessmentUpdate,
        assessor_id: UUID,
    ) -> AssessmentResponse:
        """
        Update an existing compliance assessment.

        Applies partial updates to the assessment. Only fields present
        in the update payload are modified. Updates the assessor_id,
        assessed_at timestamp, and updated_at on every update.

        Args:
            assessment_id: UUID of the assessment to update.
            data: AssessmentUpdate schema with optional status,
                evidence_ids, and notes fields.
            assessor_id: UUID of the user performing the update.

        Returns:
            AssessmentResponse with the updated assessment.

        Raises:
            ComplianceNotFoundError: If the assessment does not exist.

        Example:
            data = AssessmentUpdate(
                status=AssessmentStatus.COMPLIANT,
                evidence_ids=[evidence_1.id, evidence_2.id],
                notes="All evidence reviewed and verified",
            )
            updated = await service.update_assessment(
                assessment.id, data, user.id
            )
        """
        logger.info(
            "Updating compliance assessment",
            extra={
                "assessment_id": str(assessment_id),
                "assessor_id": str(assessor_id),
            },
        )

        # Fetch existing assessment
        query = select(ComplianceAssessment).where(
            ComplianceAssessment.id == assessment_id
        )
        result = await self.db.execute(query)
        assessment = result.scalar_one_or_none()

        if not assessment:
            raise ComplianceNotFoundError(
                f"Compliance assessment with ID '{assessment_id}' not found"
            )

        # Apply partial updates from the schema
        update_fields = data.model_dump(exclude_unset=True)

        if "status" in update_fields and update_fields["status"] is not None:
            assessment.status = update_fields["status"].value

        if "evidence_ids" in update_fields:
            assessment.evidence_ids = update_fields["evidence_ids"] or []

        if "notes" in update_fields:
            assessment.notes = update_fields["notes"]

        # Always update assessor and timestamps on modification
        assessment.assessor_id = assessor_id
        assessment.assessed_at = datetime.utcnow()
        assessment.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(assessment)

        logger.info(
            "Updated compliance assessment %s",
            assessment_id,
            extra={
                "assessment_id": str(assessment_id),
                "status": assessment.status,
            },
        )

        return await self._to_assessment_response(assessment)

    # =========================================================================
    # Private Helpers
    # =========================================================================

    async def _to_assessment_response(
        self,
        assessment: ComplianceAssessment,
    ) -> AssessmentResponse:
        """
        Convert a ComplianceAssessment model to an AssessmentResponse schema.

        Resolves the associated control and assessor relationships,
        loading them from the database if not already eagerly loaded.

        Args:
            assessment: ComplianceAssessment SQLAlchemy model instance.

        Returns:
            AssessmentResponse Pydantic schema with control and
            assessor details populated.
        """
        # Build control response if relationship is loaded
        control_response = None
        if hasattr(assessment, "control") and assessment.control:
            ctrl = assessment.control
            control_response = ControlResponse(
                id=ctrl.id,
                framework_id=ctrl.framework_id,
                control_code=ctrl.control_code,
                category=ctrl.category,
                title=ctrl.title,
                description=ctrl.description,
                severity=ctrl.severity,
                gate_mapping=ctrl.gate_mapping,
                evidence_required=ctrl.evidence_required or [],
                opa_policy_code=ctrl.opa_policy_code,
                sort_order=ctrl.sort_order,
                created_at=ctrl.created_at,
                updated_at=ctrl.updated_at,
            )
        elif assessment.control_id:
            ctrl_query = select(ComplianceControl).where(
                ComplianceControl.id == assessment.control_id
            )
            ctrl_result = await self.db.execute(ctrl_query)
            ctrl = ctrl_result.scalar_one_or_none()
            if ctrl:
                control_response = ControlResponse(
                    id=ctrl.id,
                    framework_id=ctrl.framework_id,
                    control_code=ctrl.control_code,
                    category=ctrl.category,
                    title=ctrl.title,
                    description=ctrl.description,
                    severity=ctrl.severity,
                    gate_mapping=ctrl.gate_mapping,
                    evidence_required=ctrl.evidence_required or [],
                    opa_policy_code=ctrl.opa_policy_code,
                    sort_order=ctrl.sort_order,
                    created_at=ctrl.created_at,
                    updated_at=ctrl.updated_at,
                )

        # Build assessor summary if relationship is loaded
        assessor_summary = None
        if hasattr(assessment, "assessor") and assessment.assessor:
            user = assessment.assessor
            assessor_summary = UserSummary(
                id=user.id,
                name=user.full_name or user.email,
                email=user.email,
            )
        elif assessment.assessor_id:
            user = await self.db.get(User, assessment.assessor_id)
            if user:
                assessor_summary = UserSummary(
                    id=user.id,
                    name=user.full_name or user.email,
                    email=user.email,
                )

        return AssessmentResponse(
            id=assessment.id,
            project_id=assessment.project_id,
            control_id=assessment.control_id,
            status=assessment.status,
            evidence_ids=assessment.evidence_ids or [],
            assessor_id=assessment.assessor_id,
            notes=assessment.notes,
            auto_evaluated=assessment.auto_evaluated,
            opa_result=assessment.opa_result,
            assessed_at=assessment.assessed_at,
            created_at=assessment.created_at,
            updated_at=assessment.updated_at,
            control=control_response,
            assessor=assessor_summary,
        )
