"""
=========================================================================
GDPR API Routes — Sprint 186-187 (Data Residency + GDPR, ADR-063)
SDLC Orchestrator

Version: 1.1.0
Date: 2026-02-20
Status: ACTIVE — Sprint 187 P1 (Art.20 full export added)
Authority: CTO Approved (ADR-063, GDPR Art. 7/15/17/20)
Tier: ENTERPRISE for DPO endpoints; authenticated user for self-service

Purpose:
- Self-service DSAR submission (any authenticated user)
- DPO dashboard for managing DSAR queue (ENTERPRISE)
- Consent management (any authenticated user)
- Full machine-readable PII export — GDPR Art. 20 (Sprint 187)

Endpoints:
  POST /gdpr/dsar                  — submit a DSAR request
  GET  /gdpr/dsar/{id}             — check DSAR status
  GET  /gdpr/dsar                  — list all DSARs (DPO only)
  GET  /gdpr/me/data-export        — summary of data held about me (counts only)
  GET  /gdpr/me/data-export/full   — full Art.20 PII export (1 req/24h) [Sprint 187]
  POST /gdpr/me/consent            — record consent decision
  GET  /gdpr/me/consents           — list my active consents

HTTP Semantics (Expert 4, ADR-059):
  400 — validation error
  401 — not authenticated
  403 — wrong tier or not your own request
  404 — DSAR not found
  429 — rate limit exceeded (Art.20 export: 1 req/user/24h)
=========================================================================
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db, get_redis, require_roles
from app.models.user import User
from app.services.gdpr_service import GDPRService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gdpr", tags=["GDPR"])

# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

_VALID_REQUEST_TYPES = ("access", "erasure", "portability", "rectification")
_VALID_PURPOSES = ("essential", "analytics", "marketing", "ai_training", "third_party")


class DSARCreateRequest(BaseModel):
    request_type: str = Field(
        ...,
        description="GDPR request type: access | erasure | portability | rectification",
        examples=["access"],
    )
    requester_email: EmailStr = Field(
        ..., description="Contact email for this request"
    )
    description: Optional[str] = Field(
        None, description="Optional details about the request", max_length=2000
    )

    def model_post_init(self, __context: Any) -> None:
        if self.request_type not in _VALID_REQUEST_TYPES:
            raise ValueError(
                f"request_type must be one of {_VALID_REQUEST_TYPES}"
            )


class ConsentRequest(BaseModel):
    purpose: str = Field(
        ...,
        description=(
            "Processing purpose: "
            "essential | analytics | marketing | ai_training | third_party"
        ),
    )
    granted: bool = Field(..., description="True to give consent, False to withdraw")
    version: str = Field(
        ...,
        description="Privacy policy version in effect at consent time",
        examples=["v2.1"],
    )

    def model_post_init(self, __context: Any) -> None:
        if self.purpose not in _VALID_PURPOSES:
            raise ValueError(f"purpose must be one of {_VALID_PURPOSES}")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/dsar", status_code=status.HTTP_201_CREATED)
async def submit_dsar(
    body: DSARCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Submit a Data Subject request (GDPR Art. 15 / Art. 17).

    Creates a DSAR record with status=pending and a 30-day response deadline.
    The DPO team is notified and will process within the legal deadline.

    Request body:
        {
            "request_type": "access" | "erasure" | "portability" | "rectification",
            "requester_email": "user@example.com",
            "description": "optional"
        }

    Returns 201 with the created DSAR record including due_at timestamp.
    """
    svc = GDPRService(db)
    record = await svc.create_dsar(
        requester_email=str(body.requester_email),
        request_type=body.request_type,
        user_id=current_user.id,
        description=body.description,
    )

    logger.info(
        "DSAR submitted: id=%s type=%s user=%s",
        record["id"],
        body.request_type,
        current_user.id,
    )
    return record


@router.get("/dsar/{dsar_id}")
async def get_dsar_status(
    dsar_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Check the status of a DSAR request by ID.

    Returns the current status, DPO notes, and timestamps.
    Any authenticated user can check their own requests; DPO can check all.
    """
    try:
        uuid = UUID(dsar_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="dsar_id must be a valid UUID",
        )

    svc = GDPRService(db)
    record = await svc.get_dsar_status(uuid)

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DSAR request '{dsar_id}' not found",
        )

    # F-01: Enforce ownership — users can only read their own DSARs.
    # Superusers (DPO/admin) may read any request.
    record_user_id = record.get("user_id")
    if not current_user.is_superuser and record_user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you may only view your own DSAR requests.",
        )

    # Strip internal user_id from public response
    record.pop("user_id", None)
    return record


@router.get("/dsar")
async def list_dsar_requests(
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by status: pending | processing | completed | rejected | partial",
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    # F-02: DPO/admin role gate — prevents LITE/STANDARD users from accessing the DPO queue.
    # Allowed roles: CTO, CPO, CEO, ADMIN, DPO. Superusers bypass automatically.
    current_user: User = Depends(require_roles(["CTO", "CPO", "CEO", "ADMIN", "DPO"])),
) -> Dict[str, Any]:
    """
    List all DSAR requests (DPO dashboard).

    Returns paginated DSAR records, optionally filtered by status.
    Scoped to the current user's organization (F-01).
    Requires CTO / CPO / CEO / ADMIN / DPO role (F-02).
    """
    svc = GDPRService(db)
    records = await svc.list_dsar_requests(
        status=status_filter,
        limit=limit,
        offset=offset,
        # F-01: scope to caller's org so one tenant cannot see another org's DSARs
        organization_id=current_user.organization_id,
    )
    return {
        "items": records,
        "limit": limit,
        "offset": offset,
        "status_filter": status_filter,
    }


_EXPORT_RATE_LIMIT_SECONDS = 86400  # 24 hours — GDPR Art. 20 rate limit


@router.get("/me/data-export/full")
async def get_my_full_data_export(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis=Depends(get_redis),
) -> Dict[str, Any]:
    """
    Full machine-readable PII export for the authenticated user (GDPR Art. 20).

    Returns all personal data held across 5 categories:
      - user_profile (email, full_name, role, last_login)
      - consent_records (full consent history)
      - dsar_requests (submitted DSAR history)
      - agent_messages (messages sent by this user, up to 1000)
      - evidence_metadata (files uploaded by this user)

    Rate limit: 1 request per user per 24 hours.
    Returns 429 if the limit has been reached within the window.

    Reference: FR-045, GDPR Art. 20
    """
    # Rate limit check — Redis key: gdpr_export_rl:{user_id}
    rl_key = f"gdpr_export_rl:{current_user.id}"
    try:
        existing = await redis.get(rl_key)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Rate limit exceeded: GDPR Art. 20 full export is limited to "
                    "1 request per user per 24 hours. Please try again later."
                ),
            )
    except HTTPException:
        raise
    except Exception as exc:
        # Redis unavailable — fail open for the user, log for ops
        logger.warning("GDPR export rate-limit Redis check failed: %s", exc)

    svc = GDPRService(db)
    try:
        export_data = await svc.get_full_data_export(current_user.id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    # Set rate-limit key after successful export (fail-open if Redis unavailable)
    try:
        await redis.setex(rl_key, _EXPORT_RATE_LIMIT_SECONDS, "1")
    except Exception as exc:
        logger.warning("GDPR export rate-limit Redis set failed: %s", exc)

    logger.info(
        "GDPR Art.20 full export served: user=%s",
        current_user.id,
    )
    return export_data


@router.get("/me/data-export")
async def get_my_data_export(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get a summary of all data held about the authenticated user.

    Returns data category counts (GDPR Art. 15 self-service).
    For full PII export, submit a DSAR access request via POST /gdpr/dsar.
    """
    svc = GDPRService(db)
    return await svc.get_user_data_export(current_user.id)


@router.post("/me/consent", status_code=status.HTTP_201_CREATED)
async def record_consent(
    body: ConsentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Record a consent decision for a processing purpose (GDPR Art. 7).

    Request body:
        {
            "purpose": "analytics",
            "granted": true,
            "version": "v2.1"
        }

    Returns 201 with the created consent log record.
    """
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    svc = GDPRService(db)
    record = await svc.record_consent(
        user_id=current_user.id,
        purpose=body.purpose,
        granted=body.granted,
        version=body.version,
        ip_address=ip,
        user_agent=ua,
    )

    return record


@router.get("/me/consents")
async def get_my_consents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    List all active (not withdrawn) consent records for the authenticated user.
    """
    svc = GDPRService(db)
    consents = await svc.get_active_consents(current_user.id)
    return {"consents": consents, "user_id": str(current_user.id)}
