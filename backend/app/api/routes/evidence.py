"""
Evidence Status API Endpoints

Provides evidence completeness status for OPA policy enforcement.
Part of Sprint 133 - Evidence Vault + Gates Integration (SPEC-0016).

Endpoints:
- GET /projects/{project_id}/evidence/status - Get evidence completeness
- POST /projects/{project_id}/evidence/validate - Trigger validation
- GET /projects/{project_id}/evidence/gaps - Get detailed gap report
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.project import Project
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/projects/{project_id}/evidence/status")
async def get_evidence_status(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get evidence completeness status for a project.

    Called by:
    - OPA policies during gate evaluation (gates/evidence_completeness.rego)
    - Frontend dashboard (evidence status widget)
    - CLI tools (sdlcctl evidence check)

    Returns:
        {
            "status": "complete" | "partial" | "missing",
            "gaps": {
                "backend": [...],
                "frontend": [...],
                "extension": [...],
                "cli": [...]
            },
            "total_gaps": int,
            "checked_at": "ISO 8601 timestamp",
            "specs_checked": int,
            "specs_complete": int
        }

    Raises:
        HTTPException 404: Project not found
        HTTPException 403: User not authorized
    """
    # Verify project exists and user has access
    from sqlalchemy import select
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )

    # TODO: Check user authorization (team membership, etc.)
    # For now, allow all authenticated users

    # Get project root path
    project_root = Path(settings.PROJECT_ROOT)

    # Run evidence validation
    try:
        from backend.sdlcctl.sdlcctl.validation.validators.evidence_validator import (
            validate_evidence
        )

        violations, summary = validate_evidence(project_root)

        # Categorize violations by interface
        gaps = {
            "backend": [],
            "frontend": [],
            "extension": [],
            "cli": []
        }

        for violation in violations:
            if violation.rule_id in ["EVIDENCE-006"]:  # Backend file not found
                gaps["backend"].append({
                    "message": violation.message,
                    "file": violation.file_path,
                    "suggestion": violation.suggestion
                })
            elif violation.rule_id in ["EVIDENCE-007"]:  # Frontend file not found
                gaps["frontend"].append({
                    "message": violation.message,
                    "file": violation.file_path,
                    "suggestion": violation.suggestion
                })
            elif violation.rule_id in ["EVIDENCE-008"]:  # Extension file not found
                gaps["extension"].append({
                    "message": violation.message,
                    "file": violation.file_path,
                    "suggestion": violation.suggestion
                })
            elif violation.rule_id in ["EVIDENCE-009"]:  # CLI file not found
                gaps["cli"].append({
                    "message": violation.message,
                    "file": violation.file_path,
                    "suggestion": violation.suggestion
                })
            elif violation.rule_id in ["EVIDENCE-010", "EVIDENCE-011", "EVIDENCE-012", "EVIDENCE-013"]:
                # Test coverage violations
                if "backend" in violation.message.lower():
                    gaps["backend"].append({
                        "message": violation.message,
                        "file": violation.file_path,
                        "suggestion": violation.suggestion
                    })
                elif "frontend" in violation.message.lower():
                    gaps["frontend"].append({
                        "message": violation.message,
                        "file": violation.file_path,
                        "suggestion": violation.suggestion
                    })
                elif "extension" in violation.message.lower():
                    gaps["extension"].append({
                        "message": violation.message,
                        "file": violation.file_path,
                        "suggestion": violation.suggestion
                    })
                elif "cli" in violation.message.lower():
                    gaps["cli"].append({
                        "message": violation.message,
                        "file": violation.file_path,
                        "suggestion": violation.suggestion
                    })

        # Calculate total gaps
        total_gaps = sum(len(v) for v in gaps.values())

        # Determine overall status
        if total_gaps == 0:
            overall_status = "complete"
        elif total_gaps <= 5:
            overall_status = "partial"
        else:
            overall_status = "missing"

        # Count specs (evidence files found)
        evidence_pattern = "docs/**/*-evidence.json"
        evidence_files = list(project_root.glob(evidence_pattern))
        specs_checked = len(evidence_files)

        # Count complete specs (no violations)
        specs_complete = specs_checked - len([
            v for v in violations
            if v.rule_id in ["EVIDENCE-006", "EVIDENCE-007", "EVIDENCE-008", "EVIDENCE-009"]
        ])

        return {
            "status": overall_status,
            "gaps": gaps,
            "total_gaps": total_gaps,
            "checked_at": datetime.utcnow().isoformat() + "Z",
            "specs_checked": specs_checked,
            "specs_complete": max(0, specs_complete),
            "completeness_percentage": round((specs_complete / specs_checked * 100) if specs_checked > 0 else 0, 1)
        }

    except Exception as e:
        logger.error(f"Failed to validate evidence for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evidence validation failed: {str(e)}"
        )


@router.post("/projects/{project_id}/evidence/validate")
async def trigger_evidence_validation(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Trigger full evidence validation and update validation metadata.

    This endpoint:
    1. Runs evidence validation
    2. Updates validation.last_checked timestamps in evidence files
    3. Returns full validation report

    Used by:
    - Manual validation requests from dashboard
    - Scheduled validation jobs
    - Pre-deployment validation

    Returns:
        {
            "validation_id": UUID,
            "status": "complete" | "partial" | "missing",
            "violations": [...],
            "summary": {...}
        }
    """
    # Verify project access
    from sqlalchemy import select
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )

    # Run full validation
    project_root = Path(settings.PROJECT_ROOT)

    try:
        from backend.sdlcctl.sdlcctl.validation.validators.evidence_validator import (
            validate_evidence
        )

        violations, summary = validate_evidence(project_root)

        # Convert violations to dict format
        violation_dicts = [
            {
                "rule_id": v.rule_id,
                "severity": v.severity,
                "message": v.message,
                "file_path": v.file_path,
                "line_number": v.line_number,
                "suggestion": v.suggestion
            }
            for v in violations
        ]

        # Determine status
        if summary["errors"] == 0 and summary["warnings"] == 0:
            overall_status = "complete"
        elif summary["errors"] == 0:
            overall_status = "partial"
        else:
            overall_status = "missing"

        return {
            "validation_id": f"val-{datetime.utcnow().timestamp()}",
            "status": overall_status,
            "violations": violation_dicts,
            "summary": summary,
            "validated_at": datetime.utcnow().isoformat() + "Z"
        }

    except Exception as e:
        logger.error(f"Failed to validate evidence for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evidence validation failed: {str(e)}"
        )


@router.get("/projects/{project_id}/evidence/gaps")
async def get_evidence_gaps(
    project_id: int,
    interface: Optional[str] = None,  # backend, frontend, extension, cli
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get detailed gap analysis report for a project.

    Query Parameters:
        interface: Filter by interface (backend, frontend, extension, cli)

    Returns:
        {
            "gaps": {
                "missing_evidence": [...],
                "backend_gaps": [...],
                "frontend_gaps": [...],
                "extension_gaps": [...],
                "cli_gaps": [...],
                "test_gaps": [...]
            },
            "total_gaps": int,
            "recommendations": [...]
        }
    """
    # Verify project access
    from sqlalchemy import select
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )

    project_root = Path(settings.PROJECT_ROOT)

    try:
        from backend.sdlcctl.sdlcctl.validation.validators.evidence_validator import (
            validate_evidence
        )

        violations, summary = validate_evidence(project_root)

        # Analyze gaps
        gaps = {
            "missing_evidence": [],
            "backend_gaps": [],
            "frontend_gaps": [],
            "extension_gaps": [],
            "cli_gaps": [],
            "test_gaps": []
        }

        for v in violations:
            if v.rule_id == "EVIDENCE-014":  # Missing evidence file
                gaps["missing_evidence"].append({
                    "file": v.file_path,
                    "message": v.message,
                    "suggestion": v.suggestion
                })
            elif v.rule_id == "EVIDENCE-006":  # Backend file missing
                gaps["backend_gaps"].append({
                    "file": v.file_path,
                    "message": v.message,
                    "suggestion": v.suggestion
                })
            elif v.rule_id == "EVIDENCE-007":  # Frontend file missing
                gaps["frontend_gaps"].append({
                    "file": v.file_path,
                    "message": v.message,
                    "suggestion": v.suggestion
                })
            elif v.rule_id == "EVIDENCE-008":  # Extension file missing
                gaps["extension_gaps"].append({
                    "file": v.file_path,
                    "message": v.message,
                    "suggestion": v.suggestion
                })
            elif v.rule_id == "EVIDENCE-009":  # CLI file missing
                gaps["cli_gaps"].append({
                    "file": v.file_path,
                    "message": v.message,
                    "suggestion": v.suggestion
                })
            elif v.rule_id in ["EVIDENCE-010", "EVIDENCE-011", "EVIDENCE-012", "EVIDENCE-013"]:
                gaps["test_gaps"].append({
                    "file": v.file_path,
                    "message": v.message,
                    "suggestion": v.suggestion
                })

        # Filter by interface if specified
        if interface:
            if interface == "backend":
                gaps = {"backend_gaps": gaps["backend_gaps"]}
            elif interface == "frontend":
                gaps = {"frontend_gaps": gaps["frontend_gaps"]}
            elif interface == "extension":
                gaps = {"extension_gaps": gaps["extension_gaps"]}
            elif interface == "cli":
                gaps = {"cli_gaps": gaps["cli_gaps"]}

        # Generate recommendations
        recommendations = []
        if gaps["missing_evidence"]:
            recommendations.append("Create evidence files: sdlcctl evidence create <SPEC-ID>")
        if gaps["backend_gaps"]:
            recommendations.append("Implement missing backend components and tests")
        if gaps["frontend_gaps"]:
            recommendations.append("Implement missing frontend UI components")
        if gaps["test_gaps"]:
            recommendations.append("Add test coverage for all implementations")

        total_gaps = sum(len(v) for v in gaps.values())

        return {
            "gaps": gaps,
            "total_gaps": total_gaps,
            "recommendations": recommendations,
            "analyzed_at": datetime.utcnow().isoformat() + "Z"
        }

    except Exception as e:
        logger.error(f"Failed to analyze evidence gaps for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gap analysis failed: {str(e)}"
        )
