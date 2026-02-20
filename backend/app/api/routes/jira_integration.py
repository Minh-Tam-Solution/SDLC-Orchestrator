"""
==========================================================================
Jira Integration Routes — Sprint 184 (PROFESSIONAL+ Tier)
SDLC Orchestrator

Routes:
  POST /api/v1/jira/connect  — Store Jira credentials (PROFESSIONAL tier)
  GET  /api/v1/jira/projects  — List Jira projects for this org
  POST /api/v1/jira/sync      — Sync sprint issues to Evidence Vault

Tier gate: /api/v1/jira → PROFESSIONAL (tier=3) enforced by TierGateMiddleware.
Route-level: get_current_active_user ensures authentication (401 if no token).

SDLC 6.1.0 — Sprint 184 P0 Deliverable
==========================================================================
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.models.jira_connection import JiraConnection
from app.services.integrations.jira_adapter import JiraAdapter, JiraConnectionError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jira", tags=["Jira Integration"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class JiraConnectRequest(BaseModel):
    """Request body for POST /jira/connect."""

    jira_base_url: str = Field(
        ...,
        description="Jira Cloud workspace URL (e.g., https://acme.atlassian.net)",
        examples=["https://acme.atlassian.net"],
    )
    jira_email: str = Field(
        ...,
        description="Atlassian account email used for Basic Auth",
        examples=["dev@acme.com"],
    )
    api_token: str = Field(
        ...,
        description="Jira API token (generated at id.atlassian.com)",
        min_length=1,
    )


class JiraConnectResponse(BaseModel):
    """Response body for POST /jira/connect."""

    organization_id: str
    jira_base_url: str
    jira_email: str
    connected: bool
    message: str


class JiraSyncRequest(BaseModel):
    """Request body for POST /jira/sync."""

    gate_id: UUID = Field(..., description="Target Gate UUID for evidence records")
    board_id: int = Field(..., description="Jira Software board ID")
    sprint_id: int = Field(..., description="Sprint ID within the board")


class JiraSyncResponse(BaseModel):
    """Response body for POST /jira/sync."""

    gate_id: str
    issues_synced: int
    evidence_ids: list[str]
    message: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "/connect",
    response_model=JiraConnectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Connect Jira workspace",
    description=(
        "Store Jira Cloud API credentials for the user's organization. "
        "API token is encrypted at-rest (Fernet AES-128-CBC). "
        "Credentials are tested against /rest/api/3/myself before saving. "
        "PROFESSIONAL+ tier required (enforced by TierGateMiddleware)."
    ),
)
async def jira_connect(
    body: JiraConnectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> JiraConnectResponse:
    """
    Connect Jira workspace by storing encrypted credentials.

    Validates credentials against Jira API before persisting.
    One connection per organization — subsequent calls update existing record.
    """
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization to connect Jira.",
        )

    org_id = str(current_user.organization_id)

    # Test credentials before storing
    adapter = JiraAdapter(
        base_url=body.jira_base_url,
        api_token=body.api_token,
        email=body.jira_email,
    )
    connection_ok = await adapter.test_connection()
    if not connection_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "jira_auth_failed",
                "message": (
                    "Failed to authenticate with Jira. "
                    "Verify your API token and email at "
                    "https://id.atlassian.com/manage-profile/security/api-tokens"
                ),
            },
        )

    # Encrypt API token at-rest
    encrypted_token = JiraConnection.encrypt_token(body.api_token)

    # Upsert: one connection per organization
    stmt = select(JiraConnection).where(JiraConnection.organization_id == org_id)
    existing = (await db.execute(stmt)).scalar_one_or_none()

    if existing:
        existing.jira_base_url = body.jira_base_url.rstrip("/")
        existing.jira_email = body.jira_email
        existing.api_token_enc = encrypted_token
        message = "Jira connection updated."
    else:
        existing = JiraConnection(
            organization_id=org_id,
            jira_base_url=body.jira_base_url.rstrip("/"),
            jira_email=body.jira_email,
            api_token_enc=encrypted_token,
        )
        db.add(existing)
        message = "Jira connection created."

    await db.commit()
    await db.refresh(existing)

    logger.info(
        "Jira connected: org=%s url=%s email=%s",
        org_id,
        body.jira_base_url,
        body.jira_email,
    )

    return JiraConnectResponse(
        organization_id=org_id,
        jira_base_url=existing.jira_base_url,
        jira_email=existing.jira_email,
        connected=True,
        message=message,
    )


@router.get(
    "/projects",
    response_model=list[dict[str, Any]],
    summary="List Jira projects",
    description=(
        "List all Jira projects accessible with this organization's API token. "
        "Requires a prior /jira/connect call. "
        "PROFESSIONAL+ tier required (enforced by TierGateMiddleware)."
    ),
)
async def jira_list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[dict[str, Any]]:
    """
    List Jira projects for the current organization's connected workspace.

    Calls JiraAdapter.list_projects() and returns the raw Jira project array.
    """
    adapter = await _get_adapter_for_user(current_user, db)

    try:
        projects = await adapter.list_projects()
    except Exception as exc:
        logger.error("Jira list_projects failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "jira_api_error",
                "message": f"Failed to fetch Jira projects: {exc}",
            },
        ) from exc

    return projects


@router.post(
    "/sync",
    response_model=JiraSyncResponse,
    summary="Sync sprint issues to Evidence Vault",
    description=(
        "Fetch issues from a Jira sprint and sync them as GateEvidence records. "
        "Idempotent: re-running updates existing evidence descriptions. "
        "PROFESSIONAL+ tier required (enforced by TierGateMiddleware)."
    ),
)
async def jira_sync(
    body: JiraSyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> JiraSyncResponse:
    """
    Sync Jira sprint issues to the SDLC Orchestrator Evidence Vault.

    Creates or updates GateEvidence records with source="jira".
    """
    adapter = await _get_adapter_for_user(current_user, db)

    try:
        issues = await adapter.get_sprint_issues(
            board_id=body.board_id,
            sprint_id=body.sprint_id,
        )
    except Exception as exc:
        logger.error("Jira get_sprint_issues failed board=%d sprint=%d: %s",
                     body.board_id, body.sprint_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "jira_api_error",
                "message": f"Failed to fetch Jira sprint issues: {exc}",
            },
        ) from exc

    evidence_records = await adapter.sync_to_evidence_vault(
        gate_id=body.gate_id,
        jira_issues=issues,
        db=db,
        uploaded_by=current_user.id,
    )

    evidence_ids = [str(r.id) for r in evidence_records if r.id is not None]

    return JiraSyncResponse(
        gate_id=str(body.gate_id),
        issues_synced=len(evidence_records),
        evidence_ids=evidence_ids,
        message=(
            f"Synced {len(evidence_records)} Jira issues from "
            f"board {body.board_id} sprint {body.sprint_id} "
            f"to gate {body.gate_id}."
        ),
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


async def _get_adapter_for_user(
    current_user: User, db: AsyncSession
) -> JiraAdapter:
    """
    Look up the JiraConnection for the user's organization and return a JiraAdapter.

    Raises HTTP 404 if no Jira connection has been configured for the organization.
    Raises HTTP 400 if user has no organization.
    """
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization to use Jira integration.",
        )

    org_id = str(current_user.organization_id)
    stmt = select(JiraConnection).where(JiraConnection.organization_id == org_id)
    connection = (await db.execute(stmt)).scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "jira_not_connected",
                "message": (
                    "No Jira connection found for this organization. "
                    "Call POST /api/v1/jira/connect first."
                ),
            },
        )

    plain_token = connection.get_plain_token()
    return JiraAdapter(
        base_url=connection.jira_base_url,
        api_token=plain_token,
        email=connection.jira_email,
    )
