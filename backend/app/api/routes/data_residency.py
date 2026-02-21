"""
=========================================================================
Data Residency API — Sprint 186 (Multi-Region, ADR-063, ENTERPRISE tier)
SDLC Orchestrator

Version: 1.0.0
Date: 2026-02-20
Status: ACTIVE — Sprint 186 P0
Authority: CTO Approved (ADR-063)
Tier: ENTERPRISE (enforced by TierGateMiddleware)

Purpose:
- Allow ENTERPRISE customers to select data storage region per project
- Expose available regions and current project region assignment
- Enforce GDPR: EU projects must remain in the EU MinIO bucket

Architecture (Expert 5 de-scope, Sprint 180 ADR-059):
  Storage-level residency only — MinIO/S3 bucket per region.
  DB remains single-region (Vietnam primary).
  Full multi-region DB deferred until first EU enterprise contract.

Endpoints:
  GET  /data-residency/regions                  — list available regions
  GET  /data-residency/projects/{id}/region     — get project region
  PUT  /data-residency/projects/{id}/region     — update project region
  GET  /data-residency/projects/{id}/storage    — get storage routing info

HTTP Semantics (Expert 4, ADR-059):
  403 — authenticated but wrong tier (not ENTERPRISE)
  404 — project not found
  409 — region change blocked (active GDPR hold)
=========================================================================
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.project import Project
from app.models.user import User
from app.services.storage_region_service import StorageRegionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-residency", tags=["data-residency"])

# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

_VALID_REGIONS = ("VN", "EU", "US")


class RegionUpdateRequest(BaseModel):
    """Request body for PUT /data-residency/projects/{id}/region."""

    data_region: str = Field(
        ...,
        description="Target storage region. One of: VN (Asia Pacific), EU (Frankfurt), US (future).",
        examples=["EU"],
    )

    def model_post_init(self, __context: Any) -> None:
        self.data_region = self.data_region.upper()
        if self.data_region not in _VALID_REGIONS:
            raise ValueError(
                f"data_region '{self.data_region}' is not valid. "
                f"Valid values: {list(_VALID_REGIONS)}"
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_project_or_404(
    project_id: str, db: AsyncSession, current_user: User
) -> Project:
    """Fetch project by UUID, enforce ownership, or raise 404/403.

    F-06: Adds organization_id check so ENTERPRISE users from one org cannot
    read or modify data-residency settings for another org's projects.
    Superusers bypass the ownership check.
    """
    from uuid import UUID

    try:
        pid = UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="project_id must be a valid UUID",
        )

    result = await db.execute(
        select(Project).where(Project.id == pid, Project.deleted_at.is_(None))
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found",
        )

    # F-06: Verify the caller belongs to the same organization as the project.
    if not current_user.is_superuser and str(project.organization_id) != str(
        current_user.organization_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: project does not belong to your organization.",
        )

    return project


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/regions")
async def list_regions(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    List all available storage regions.

    Returns the MinIO endpoint and bucket name for each supported region.
    ENTERPRISE tier only (enforced by TierGateMiddleware in main.py).

    Returns:
        {
            "regions": [
                {
                    "region": "VN",
                    "display_name": "Vietnam / Singapore (Asia Pacific)",
                    "endpoint_url": "http://minio:9000",
                    "bucket": "sdlc-evidence-vn",
                    "gdpr_compliant": false
                },
                ...
            ]
        }
    """
    svc = StorageRegionService()
    raw = svc.list_available_regions()

    display_names = {
        "VN": "Vietnam / Singapore (Asia Pacific)",
        "EU": "Frankfurt (EU — GDPR compliant)",
        "US": "US East (coming soon)",
    }
    gdpr_regions = {"EU"}

    regions = [
        {
            "region": r["region"],
            "display_name": display_names.get(r["region"], r["region"]),
            "endpoint_url": r["endpoint_url"],
            "bucket": r["bucket"],
            "gdpr_compliant": r["region"] in gdpr_regions,
        }
        for r in raw
    ]

    logger.info(
        "list_regions: user=%s returned %d regions", current_user.id, len(regions)
    )
    return {"regions": regions}


@router.get("/projects/{project_id}/region")
async def get_project_region(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get the current data storage region for a project.

    Returns:
        {
            "project_id": str,
            "project_name": str,
            "data_region": "VN" | "EU" | "US",
            "bucket": str,
            "endpoint_url": str
        }
    """
    project = await _get_project_or_404(project_id, db, current_user)
    svc = StorageRegionService()
    cfg = svc.get_region_config(project.data_region)

    return {
        "project_id": str(project.id),
        "project_name": project.name,
        "data_region": project.data_region,
        "bucket": cfg.bucket,
        "endpoint_url": cfg.endpoint_url,
    }


@router.put("/projects/{project_id}/region")
async def update_project_region(
    project_id: str,
    body: RegionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Update the data storage region for a project.

    Changing the region affects where NEW evidence files are stored.
    Existing evidence in the old bucket is NOT migrated automatically.
    Contact support for a full evidence migration.

    GDPR rule: Moving EU data OUT of the EU region is blocked if the
    project has active GDPR holds (future enforcement — Sprint 186 GDPR phase).

    Request body:
        { "data_region": "EU" }

    Returns:
        { "project_id": str, "old_region": str, "new_region": str }

    Raises:
        404: Project not found
        409: Region change blocked by active GDPR hold
    """
    project = await _get_project_or_404(project_id, db, current_user)
    old_region = project.data_region
    new_region = body.data_region

    if old_region == new_region:
        return {
            "project_id": str(project.id),
            "old_region": old_region,
            "new_region": new_region,
            "changed": False,
            "message": "Region unchanged.",
        }

    # GDPR guard: EU → non-EU transition requires explicit GDPR check
    # (Full GDPR hold enforcement deferred to Sprint 186 GDPR phase,
    # but the guard point is established here for future implementation.)
    if old_region == "EU" and new_region != "EU":
        logger.warning(
            "update_project_region: EU→%s for project %s by user %s — "
            "GDPR cross-border transfer check required",
            new_region,
            project_id,
            current_user.id,
        )
        # Future: check active GDPR holds; raise 409 if blocked.
        # For Sprint 186: log and allow (GDPR phase in same sprint).

    # Validate new region produces a valid config (guard against future
    # constraint drift between model and service)
    svc = StorageRegionService()
    new_cfg = svc.get_region_config(new_region)  # raises ValueError if unknown

    # Persist change
    project.data_region = new_region
    await db.commit()

    logger.info(
        "update_project_region: project=%s old=%s new=%s bucket=%s user=%s",
        project_id,
        old_region,
        new_region,
        new_cfg.bucket,
        current_user.id,
    )

    return {
        "project_id": str(project.id),
        "project_name": project.name,
        "old_region": old_region,
        "new_region": new_region,
        "new_bucket": new_cfg.bucket,
        "changed": True,
        "message": (
            f"Storage region updated to {new_region}. "
            "New evidence will be stored in the new region. "
            "Existing evidence is not migrated automatically."
        ),
    }


@router.get("/projects/{project_id}/storage")
async def get_project_storage_info(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get full storage routing information for a project.

    Includes region config, S3 path prefix, and GDPR compliance status.

    Returns:
        {
            "project_id": str,
            "data_region": str,
            "storage": {
                "endpoint_url": str,
                "bucket": str,
                "aws_region": str,
                "evidence_prefix": str,   // s3://bucket/evidence/project/{id}/
                "gdpr_compliant": bool
            }
        }
    """
    project = await _get_project_or_404(project_id, db, current_user)
    svc = StorageRegionService()
    cfg = svc.get_region_config(project.data_region)

    return {
        "project_id": str(project.id),
        "project_name": project.name,
        "data_region": project.data_region,
        "storage": {
            "endpoint_url": cfg.endpoint_url,
            "bucket": cfg.bucket,
            "aws_region": cfg.aws_region,
            "evidence_prefix": f"s3://{cfg.bucket}/evidence/project/{project.id}/",
            "gdpr_compliant": project.data_region == "EU",
        },
    }
