"""
Compliance Audit PDF Export Route — Sprint 192 (Enterprise Hardening).

POST /api/v1/compliance/export/{project_id}
  - Generates a compliance audit PDF for the given project and date range
  - Requires authentication + project membership
  - Logs action="compliance_export" to audit_logs
  - Returns PDF bytes with application/pdf content type

Tier gate: /api/v1/compliance → covered by TierGateMiddleware parent prefix.
Route-level: get_current_active_user ensures authentication (401 if no token).

SDLC 6.1.0 — Sprint 192 P1 Deliverable
Authority: CTO + CPO Approved
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.services.compliance_export_service import ComplianceExportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compliance", tags=["Compliance Export"])


# ---------------------------------------------------------------------------
# Request schema
# ---------------------------------------------------------------------------


class ComplianceExportRequest(BaseModel):
    """Request body for compliance PDF export."""

    from_date: datetime = Field(
        ...,
        description="Start of audit period (UTC). ISO 8601 format.",
    )
    to_date: datetime = Field(
        ...,
        description="End of audit period (UTC). ISO 8601 format.",
    )


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------


async def _check_project_access(
    project_id: UUID,
    user: User,
    db: AsyncSession,
) -> Project:
    """Verify the user has access to the project (owner or member)."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"project {project_id} not found",
        )

    # Owner always has access
    if project.owner_id == user.id:
        return project

    # Check project membership
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user.id,
    )
    result = await db.execute(stmt)
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="not a member of this project",
        )

    return project


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.post(
    "/export/{project_id}",
    status_code=status.HTTP_200_OK,
    summary="Export compliance audit PDF",
    response_description="PDF document with compliance audit trail",
    responses={
        200: {"content": {"application/pdf": {}}},
        403: {"description": "Not a project member"},
        404: {"description": "Project not found"},
        422: {"description": "Invalid date range"},
        500: {"description": "PDF generation failed"},
    },
)
async def export_compliance_pdf(
    project_id: UUID,
    request: ComplianceExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Generate and return a compliance audit PDF for the project.

    The PDF includes:
    - Gate timeline (all quality gates with status transitions)
    - Evidence summary (all evidence files with SHA256 hashes)
    - Audit detail table (all audit events in the specified period)
    - Document integrity hash (SHA256 of the PDF)

    Requires project membership. Logs to audit_logs for compliance traceability.
    """
    await _check_project_access(project_id, current_user, db)

    # Log the export action to audit_logs
    try:
        from app.models.audit_log import AuditLog
        audit_entry = AuditLog(
            event_type="export_event",
            action="compliance_export",
            actor_id=str(current_user.id),
            actor_email=current_user.email,
            resource_type="project",
            resource_id=str(project_id),
            detail={
                "from_date": request.from_date.isoformat(),
                "to_date": request.to_date.isoformat(),
                "format": "pdf",
            },
        )
        db.add(audit_entry)
        await db.flush()
    except Exception as exc:
        logger.warning(
            "compliance_export: audit log failed project=%s error=%s",
            project_id, str(exc),
        )

    # Generate PDF
    try:
        service = ComplianceExportService(db)
        result = await service.generate_audit_pdf(
            project_id=project_id,
            from_date=request.from_date,
            to_date=request.to_date,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    logger.info(
        "compliance_export: success project=%s user=%s events=%d sha256=%s",
        project_id,
        current_user.email,
        result.total_events,
        result.sha256[:12],
    )

    return Response(
        content=result.pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="compliance-audit-{project_id}-'
                f'{result.from_date[:10]}.pdf"'
            ),
            "X-PDF-SHA256": result.sha256,
            "X-Total-Events": str(result.total_events),
            "X-Total-Gates": str(result.total_gates),
            "X-Total-Evidence": str(result.total_evidence),
        },
    )
