"""
==========================================================================
Audit Trail Routes — Sprint 185 (Advanced Audit Trail, SOC2 Type II)
SDLC Orchestrator — ENTERPRISE Tier

Routes:
  GET  /api/v1/enterprise/audit           — list audit events (filtered, paginated)
  POST /api/v1/enterprise/audit/export    — export audit logs (CSV / JSON)

Tier gate: /api/v1/enterprise → ENTERPRISE (tier=4) enforced by TierGateMiddleware.
Route-level: get_current_active_user ensures authentication (401 if no token).

SOC2 Type II Controls Covered:
  CC6.1  — who accessed what resources (filter by actor_id, resource_type)
  CC7.2  — system monitoring events exportable for audit
  CC8.1  — change management trail (gate_action.action=approve)

SDLC 6.1.0 — Sprint 185 P0 Deliverable
Authority: CTO + CPO Approved (ADR-059)
==========================================================================
"""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.services.compliance.soc2_pack_service import SOC2PackService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enterprise/audit", tags=["Audit Trail"])

# ---------------------------------------------------------------------------
# Default pagination + retention constants
# ---------------------------------------------------------------------------

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500
AUDIT_RETENTION_DAYS = 90


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class AuditEventResponse(BaseModel):
    """Single audit event in list/export responses."""

    id: str
    event_type: str
    action: str
    actor_id: str | None
    actor_email: str | None
    organization_id: str | None
    resource_type: str | None
    resource_id: str | None
    detail: dict[str, Any] | None
    ip_address: str | None
    tier_at_event: str | None
    created_at: str  # ISO 8601 string (UTC)

    @classmethod
    def from_orm(cls, log: AuditLog) -> "AuditEventResponse":
        """Convert AuditLog ORM instance to response schema."""
        return cls(
            id=str(log.id),
            event_type=log.event_type,
            action=log.action,
            actor_id=log.actor_id,
            actor_email=log.actor_email,
            organization_id=log.organization_id,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            detail=log.detail,
            ip_address=log.ip_address,
            tier_at_event=log.tier_at_event,
            created_at=(
                log.created_at.isoformat()
                if log.created_at else ""
            ),
        )


class AuditListResponse(BaseModel):
    """Paginated audit event list."""

    events: list[AuditEventResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class AuditExportRequest(BaseModel):
    """Request body for POST /enterprise/audit/export."""

    format: str = Field(
        "json",
        description="Export format: 'json' or 'csv'",
        pattern="^(json|csv)$",
    )
    from_date: str | None = Field(
        None,
        description="Start of date range (ISO 8601 UTC, e.g. 2026-01-01T00:00:00Z)",
    )
    to_date: str | None = Field(
        None,
        description="End of date range (ISO 8601 UTC, e.g. 2026-02-01T00:00:00Z)",
    )
    event_type: str | None = Field(
        None,
        description="Filter by event_type (e.g. gate_action, evidence_access)",
    )
    actor_id: str | None = Field(
        None,
        description="Filter by actor UUID",
    )
    resource_type: str | None = Field(
        None,
        description="Filter by resource_type (e.g. gate, evidence, user)",
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=AuditListResponse,
    summary="List audit events",
    description=(
        "Return a paginated list of audit events for the requesting user's organization. "
        "Supports filtering by event_type, action, actor_id, resource_type, and date range. "
        "ENTERPRISE tier required (enforced by TierGateMiddleware). "
        "90-day retention window — events older than 90 days are archived, not returned here."
    ),
)
async def list_audit_events(
    # Filters
    event_type: str | None = Query(None, description="e.g. gate_action, evidence_access"),
    action: str | None = Query(None, description="e.g. approve, reject, download"),
    actor_id: str | None = Query(None, description="Filter by actor UUID"),
    resource_type: str | None = Query(None, description="e.g. gate, evidence, user"),
    resource_id: str | None = Query(None, description="Filter by specific resource UUID"),
    from_date: str | None = Query(None, description="ISO 8601 UTC start (e.g. 2026-01-01T00:00:00Z)"),
    to_date: str | None = Query(None, description="ISO 8601 UTC end (e.g. 2026-02-01T00:00:00Z)"),
    # Pagination
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Events per page"),
    # Auth
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AuditListResponse:
    """
    List audit events for the requesting user's organization.

    Always scoped to the user's organization_id — users cannot query
    other organizations' audit logs (tenant isolation).

    Events are returned in reverse chronological order (newest first).
    """
    org_id = str(current_user.organization_id) if current_user.organization_id else None

    # Build filter conditions
    conditions = []

    # Tenant isolation — ALWAYS filter by org (cannot be bypassed via query params)
    if org_id:
        conditions.append(AuditLog.organization_id == org_id)

    if event_type:
        conditions.append(AuditLog.event_type == event_type)
    if action:
        conditions.append(AuditLog.action == action)
    if actor_id:
        conditions.append(AuditLog.actor_id == actor_id)
    if resource_type:
        conditions.append(AuditLog.resource_type == resource_type)
    if resource_id:
        conditions.append(AuditLog.resource_id == resource_id)

    # Date range filters
    if from_date:
        try:
            from_dt = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
            conditions.append(AuditLog.created_at >= from_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "invalid_date", "field": "from_date",
                        "message": "from_date must be ISO 8601 UTC (e.g. 2026-01-01T00:00:00Z)"},
            )
    if to_date:
        try:
            to_dt = datetime.fromisoformat(to_date.replace("Z", "+00:00"))
            conditions.append(AuditLog.created_at <= to_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "invalid_date", "field": "to_date",
                        "message": "to_date must be ISO 8601 UTC (e.g. 2026-02-01T00:00:00Z)"},
            )

    where_clause = and_(*conditions) if conditions else True

    # Count total matching events
    count_stmt = select(func.count()).select_from(AuditLog).where(where_clause)
    total: int = (await db.execute(count_stmt)).scalar_one()

    # Fetch page
    offset = (page - 1) * page_size
    stmt = (
        select(AuditLog)
        .where(where_clause)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    logs = result.scalars().all()

    return AuditListResponse(
        events=[AuditEventResponse.from_orm(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(logs)) < total,
    )


@router.post(
    "/export",
    summary="Export audit log",
    description=(
        "Export audit events as JSON or CSV for compliance submission. "
        "Applies same org-scoping and filters as GET /enterprise/audit. "
        "Creates an export_event audit log entry for the export action itself (SOC2 CC7.2). "
        "ENTERPRISE tier required (enforced by TierGateMiddleware)."
    ),
)
async def export_audit_log(
    body: AuditExportRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """
    Export audit events for SOC2 / compliance submission.

    Returns:
        JSON: application/json file download
        CSV:  text/csv file download

    The export action itself is recorded as an audit event (SOC2 CC7.2).
    """
    # F-03 fix (Sprint 185 code review): extract real client IP from Request.
    # The previous `request_ip: str = "unknown"` parameter was never injected
    # by FastAPI (plain str params are not bound to request.client.host).
    # SOC2 CC7.2 requires "who did what from where" — IP is material.
    request_ip: str = (
        request.client.host if request.client else "unknown"
    )

    org_id = str(current_user.organization_id) if current_user.organization_id else None

    # Build filter conditions (same logic as list endpoint)
    conditions = []
    if org_id:
        conditions.append(AuditLog.organization_id == org_id)
    if body.event_type:
        conditions.append(AuditLog.event_type == body.event_type)
    if body.actor_id:
        conditions.append(AuditLog.actor_id == body.actor_id)
    if body.resource_type:
        conditions.append(AuditLog.resource_type == body.resource_type)
    if body.from_date:
        try:
            from_dt = datetime.fromisoformat(body.from_date.replace("Z", "+00:00"))
            conditions.append(AuditLog.created_at >= from_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "invalid_date", "field": "from_date"},
            )
    if body.to_date:
        try:
            to_dt = datetime.fromisoformat(body.to_date.replace("Z", "+00:00"))
            conditions.append(AuditLog.created_at <= to_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "invalid_date", "field": "to_date"},
            )

    where_clause = and_(*conditions) if conditions else True
    stmt = (
        select(AuditLog)
        .where(where_clause)
        .order_by(AuditLog.created_at.asc())
    )
    result = await db.execute(stmt)
    logs = list(result.scalars().all())

    export_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename_base = f"audit_export_{export_ts}"
    events_data = [AuditEventResponse.from_orm(log) for log in logs]

    # -------------------------------------------------------------------------
    # Record this export as an audit event itself (SOC2 CC7.2)
    # -------------------------------------------------------------------------
    export_event = AuditLog.create_event(
        event_type="export_event",
        action="export",
        actor_id=str(current_user.id) if current_user.id else None,
        actor_email=current_user.email,
        organization_id=org_id,
        resource_type="audit_log",
        detail={
            "format": body.format,
            "rows_exported": len(logs),
            "filters": {
                "event_type": body.event_type,
                "actor_id": body.actor_id,
                "resource_type": body.resource_type,
                "from_date": body.from_date,
                "to_date": body.to_date,
            },
        },
        ip_address=request_ip,
        tier_at_event=getattr(current_user, "effective_tier", None),
    )
    db.add(export_event)
    await db.commit()

    logger.info(
        "Audit export: org=%s actor=%s format=%s rows=%d",
        org_id, current_user.email, body.format, len(logs),
    )

    # -------------------------------------------------------------------------
    # Format response
    # -------------------------------------------------------------------------
    if body.format == "csv":
        output = io.StringIO()
        fieldnames = [
            "id", "event_type", "action", "actor_id", "actor_email",
            "organization_id", "resource_type", "resource_id",
            "detail", "ip_address", "tier_at_event", "created_at",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for ev in events_data:
            writer.writerow({
                "id": ev.id,
                "event_type": ev.event_type,
                "action": ev.action,
                "actor_id": ev.actor_id or "",
                "actor_email": ev.actor_email or "",
                "organization_id": ev.organization_id or "",
                "resource_type": ev.resource_type or "",
                "resource_id": ev.resource_id or "",
                "detail": json.dumps(ev.detail) if ev.detail else "",
                "ip_address": ev.ip_address or "",
                "tier_at_event": ev.tier_at_event or "",
                "created_at": ev.created_at,
            })

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename_base}.csv"',
                "X-Rows-Exported": str(len(logs)),
            },
        )

    # Default: JSON
    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "organization_id": org_id,
        "rows": len(logs),
        "events": [ev.model_dump() for ev in events_data],
    }
    return Response(
        content=json.dumps(payload, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename_base}.json"',
            "X-Rows-Exported": str(len(logs)),
        },
    )


# ---------------------------------------------------------------------------
# SOC2 Evidence Pack
# ---------------------------------------------------------------------------


class SOC2PackRequest(BaseModel):
    """Request body for POST /enterprise/soc2-pack."""

    from_date: str = Field(
        ...,
        description="Start of evidence period (ISO 8601 UTC, e.g. 2026-01-01T00:00:00Z)",
    )
    to_date: str = Field(
        ...,
        description="End of evidence period (ISO 8601 UTC, e.g. 2026-02-01T00:00:00Z)",
    )


@router.post(
    "/soc2-pack",
    summary="Generate SOC2 Type II evidence pack",
    description=(
        "Generate a SOC2 Type II evidence pack PDF by auto-collecting audit events "
        "mapped to Trust Service Criteria (CC1.1, CC6.1, CC6.2, CC6.6, CC7.2, CC8.1, A1.1, A1.2). "
        "Returns PDF as application/pdf download. "
        "The generation itself is recorded as an export_event audit log. "
        "ENTERPRISE tier required (enforced by TierGateMiddleware)."
    ),
    response_class=Response,
)
async def generate_soc2_pack(
    body: SOC2PackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """
    Generate a SOC2 Type II evidence pack PDF.

    Auto-collects audit events from the organization's audit log and maps them
    to SOC2 Trust Service Criteria. Returns a PDF ready for compliance submission.
    """
    org_id = str(current_user.organization_id) if current_user.organization_id else None
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "no_organization", "message": "User must belong to an organization."},
        )

    # Parse date range
    try:
        from_dt = datetime.fromisoformat(body.from_date.replace("Z", "+00:00"))
        to_dt = datetime.fromisoformat(body.to_date.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "invalid_date_range",
                "message": "from_date and to_date must be ISO 8601 UTC (e.g. 2026-01-01T00:00:00Z)",
            },
        ) from exc

    if from_dt >= to_dt:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "invalid_date_range", "message": "from_date must be before to_date"},
        )

    # Generate pack
    service = SOC2PackService(db)
    try:
        pack = await service.generate_pack(
            organization_id=org_id,
            from_date=from_dt,
            to_date=to_dt,
        )
    except Exception as exc:
        logger.error("SOC2 pack generation failed: org=%s %s", org_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "soc2_pack_error", "message": "SOC2 pack generation failed."},
        ) from exc

    # Record the pack generation in audit log
    gen_event = AuditLog.create_event(
        event_type="export_event",
        action="generate",
        actor_id=str(current_user.id) if current_user.id else None,
        actor_email=current_user.email,
        organization_id=org_id,
        resource_type="compliance_pack",
        detail={
            "pack_type": "SOC2_TYPE_II",
            "from_date": body.from_date,
            "to_date": body.to_date,
            "total_events": pack.total_events,
            "controls_covered": sum(1 for v in pack.summary.values() if v > 0),
            "pdf_size_bytes": len(pack.pdf_bytes),
        },
        tier_at_event=getattr(current_user, "effective_tier", None),
    )
    db.add(gen_event)
    await db.commit()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"soc2_evidence_pack_{ts}.pdf"

    return Response(
        content=pack.pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Events-Included": str(pack.total_events),
            "X-Controls-Covered": str(sum(1 for v in pack.summary.values() if v > 0)),
        },
    )
