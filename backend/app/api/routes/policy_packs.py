"""
Policy Packs API Router - Project Policy Configuration

SDLC Stage: 04 - BUILD
Sprint: 43 - Policy Guards & Evidence UI
Framework: SDLC 5.1.1 (10-Stage Lifecycle, 4-Tier Classification)
Epic: EP-02 AI Safety Layer v1

Purpose:
- Policy Pack CRUD operations
- Policy Rule management
- Policy evaluation for PRs
- Default policy pack creation

API Endpoints:
1. GET /projects/{project_id}/policy-pack - Get project's policy pack
2. POST /projects/{project_id}/policy-pack - Create/update policy pack
3. DELETE /projects/{project_id}/policy-pack - Delete policy pack
4. POST /projects/{project_id}/policy-pack/rules - Add policy rule
5. PUT /projects/{project_id}/policy-pack/rules/{policy_id} - Update rule
6. DELETE /projects/{project_id}/policy-pack/rules/{policy_id} - Delete rule
7. POST /projects/{project_id}/policy-pack/evaluate - Evaluate policies
8. POST /projects/{project_id}/policy-pack/init - Initialize default pack

Reference:
- docs/02-design/14-Technical-Specs/Policy-Guards-Design.md
- docs/04-build/05-SASE-Artifacts/BRS-2026-003-POLICY-GUARDS.yaml

Version: 1.0.0
Updated: December 2025
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.policy_pack import (
    PolicyEvaluationRequest,
    PolicyEvaluationResponse,
    PolicyPackCreate,
    PolicyPackResponse,
    PolicyPackUpdate,
    PolicyPackWithRules,
    PolicyRuleCreate,
    PolicyRuleResponse,
    PolicyRuleUpdate,
    PolicyTier,
)
from app.services.policy_pack_service import PolicyPackService

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Dependencies
# ============================================================================


async def get_policy_pack_service(
    db: AsyncSession = Depends(get_db),
) -> PolicyPackService:
    """Get PolicyPackService instance."""
    return PolicyPackService(db)


# ============================================================================
# Policy Pack Endpoints
# ============================================================================


@router.get(
    "/projects/{project_id}/policy-pack",
    response_model=PolicyPackWithRules,
    summary="Get project's policy pack",
    description="""
    Get the policy pack configuration for a project.

    **Response** (200 OK):
    - Policy pack with all rules
    - Validator configuration
    - Architecture rules

    **Response** (404 Not Found):
    - Project has no policy pack configured
    """,
)
async def get_policy_pack(
    project_id: UUID,
    service: PolicyPackService = Depends(get_policy_pack_service),
    current_user: User = Depends(get_current_active_user),
):
    """Get policy pack for a project."""
    pack = await service.get_by_project(project_id)

    if not pack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No policy pack found for project {project_id}",
        )

    # Convert to response with rules
    return PolicyPackWithRules(
        id=pack.id,
        project_id=pack.project_id,
        name=pack.name,
        description=pack.description,
        version=pack.version,
        tier=pack.tier,
        validators=pack.validators or [],
        coverage_threshold=pack.coverage_threshold,
        coverage_blocking=pack.coverage_blocking,
        forbidden_imports=pack.forbidden_imports or [],
        required_patterns=pack.required_patterns or [],
        policies_count=len(pack.rules) if pack.rules else 0,
        validators_count=len([v for v in (pack.validators or []) if v.get("enabled", True)]),
        created_at=pack.created_at,
        updated_at=pack.updated_at,
        created_by=pack.created_by,
        policies=[
            PolicyRuleResponse(
                id=rule.id,
                policy_pack_id=rule.policy_pack_id,
                policy_id=rule.policy_id,
                name=rule.name,
                description=rule.description,
                rego_policy=rule.rego_policy,
                severity=rule.severity,
                blocking=rule.blocking,
                enabled=rule.enabled,
                message_template=rule.message_template,
                tags=rule.tags or [],
                created_at=rule.created_at,
                updated_at=rule.updated_at,
            )
            for rule in (pack.rules or [])
        ],
    )


@router.post(
    "/projects/{project_id}/policy-pack",
    response_model=PolicyPackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update policy pack",
    description="""
    Create or update the policy pack for a project.

    **Request Body**:
    - name: Pack name
    - description: Pack description
    - version: Semantic version (e.g., "1.0.0")
    - tier: SDLC tier (lite, standard, professional, enterprise)
    - validators: Validator pipeline configuration
    - coverage_threshold: Min test coverage (0-100)
    - forbidden_imports: AGPL imports to block
    - policies: Custom OPA policies

    **Response** (201 Created):
    - Created/updated policy pack
    """,
)
async def create_policy_pack(
    project_id: UUID,
    pack_data: PolicyPackCreate,
    service: PolicyPackService = Depends(get_policy_pack_service),
    current_user: User = Depends(get_current_active_user),
):
    """Create or update policy pack for a project."""
    # Check permission
    if not await service.can_manage_policies(current_user, project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage policies for this project",
        )

    try:
        pack = await service.create_or_update(
            project_id=project_id,
            data=pack_data,
            user_id=current_user.id,
        )

        return PolicyPackResponse(
            id=pack.id,
            project_id=pack.project_id,
            name=pack.name,
            description=pack.description,
            version=pack.version,
            tier=pack.tier,
            validators=pack.validators or [],
            coverage_threshold=pack.coverage_threshold,
            coverage_blocking=pack.coverage_blocking,
            forbidden_imports=pack.forbidden_imports or [],
            required_patterns=pack.required_patterns or [],
            policies_count=len(pack.rules) if pack.rules else 0,
            validators_count=len([v for v in (pack.validators or []) if v.get("enabled", True)]),
            created_at=pack.created_at,
            updated_at=pack.updated_at,
            created_by=pack.created_by,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/projects/{project_id}/policy-pack",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete policy pack",
    description="""
    Delete the policy pack for a project.

    **Response** (204 No Content):
    - Policy pack deleted

    **Response** (404 Not Found):
    - Project has no policy pack
    """,
)
async def delete_policy_pack(
    project_id: UUID,
    service: PolicyPackService = Depends(get_policy_pack_service),
    current_user: User = Depends(get_current_active_user),
):
    """Delete policy pack for a project."""
    if not await service.can_manage_policies(current_user, project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage policies for this project",
        )

    pack = await service.get_by_project(project_id)
    if not pack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No policy pack found for project {project_id}",
        )

    await service.delete(pack.id)


# ============================================================================
# Policy Rule Endpoints
# ============================================================================


@router.post(
    "/projects/{project_id}/policy-pack/rules",
    response_model=PolicyRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add policy rule",
    description="""
    Add a custom policy rule to the project's policy pack.

    **Request Body**:
    - policy_id: Unique identifier (kebab-case)
    - name: Human-readable name
    - description: What the policy checks
    - rego_policy: OPA Rego code
    - severity: critical, high, medium, low, info
    - blocking: If true, violations block merge
    - message_template: Message on failure ({file}, {line} placeholders)
    - tags: Categorization tags

    **Response** (201 Created):
    - Created policy rule
    """,
)
async def add_policy_rule(
    project_id: UUID,
    rule_data: PolicyRuleCreate,
    service: PolicyPackService = Depends(get_policy_pack_service),
    current_user: User = Depends(get_current_active_user),
):
    """Add a policy rule to the project's pack."""
    if not await service.can_manage_policies(current_user, project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage policies for this project",
        )

    try:
        rule = await service.add_rule(project_id, rule_data)

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No policy pack found for project {project_id}",
            )

        return PolicyRuleResponse(
            id=rule.id,
            policy_pack_id=rule.policy_pack_id,
            policy_id=rule.policy_id,
            name=rule.name,
            description=rule.description,
            rego_policy=rule.rego_policy,
            severity=rule.severity,
            blocking=rule.blocking,
            enabled=rule.enabled,
            message_template=rule.message_template,
            tags=rule.tags or [],
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put(
    "/projects/{project_id}/policy-pack/rules/{policy_id}",
    response_model=PolicyRuleResponse,
    summary="Update policy rule",
    description="""
    Update an existing policy rule.

    **Path Parameters**:
    - project_id: Project UUID
    - policy_id: Policy identifier (e.g., "no-hardcoded-secrets")

    **Request Body** (all fields optional):
    - name: Updated name
    - description: Updated description
    - rego_policy: Updated Rego code
    - severity: Updated severity
    - blocking: Updated blocking status
    - enabled: Enable/disable rule

    **Response** (200 OK):
    - Updated policy rule
    """,
)
async def update_policy_rule(
    project_id: UUID,
    policy_id: str,
    rule_data: PolicyRuleUpdate,
    service: PolicyPackService = Depends(get_policy_pack_service),
    current_user: User = Depends(get_current_active_user),
):
    """Update a policy rule."""
    if not await service.can_manage_policies(current_user, project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage policies for this project",
        )

    pack = await service.get_by_project(project_id)
    if not pack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No policy pack found for project {project_id}",
        )

    rule = await service.update_rule(pack.id, policy_id, rule_data)

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy rule '{policy_id}' not found",
        )

    return PolicyRuleResponse(
        id=rule.id,
        policy_pack_id=rule.policy_pack_id,
        policy_id=rule.policy_id,
        name=rule.name,
        description=rule.description,
        rego_policy=rule.rego_policy,
        severity=rule.severity,
        blocking=rule.blocking,
        enabled=rule.enabled,
        message_template=rule.message_template,
        tags=rule.tags or [],
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@router.delete(
    "/projects/{project_id}/policy-pack/rules/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete policy rule",
    description="""
    Delete a policy rule from the project's pack.

    **Path Parameters**:
    - project_id: Project UUID
    - policy_id: Policy identifier

    **Response** (204 No Content):
    - Rule deleted

    **Response** (404 Not Found):
    - Rule not found
    """,
)
async def delete_policy_rule(
    project_id: UUID,
    policy_id: str,
    service: PolicyPackService = Depends(get_policy_pack_service),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a policy rule."""
    if not await service.can_manage_policies(current_user, project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage policies for this project",
        )

    deleted = await service.delete_rule(project_id, policy_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy rule '{policy_id}' not found",
        )


# ============================================================================
# Policy Evaluation Endpoint
# ============================================================================


@router.post(
    "/projects/{project_id}/policy-pack/evaluate",
    summary="Evaluate policies",
    description="""
    Evaluate all enabled policies against provided files.

    **Request Body**:
    - files: List of files with path and content
    - diff: Unified diff (optional)

    **Response** (200 OK):
    - Evaluation results for each policy
    - Pass/fail status
    - Violation details
    """,
)
async def evaluate_policies(
    project_id: UUID,
    request: PolicyEvaluationRequest,
    service: PolicyPackService = Depends(get_policy_pack_service),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Evaluate policies against files."""
    result = await service.evaluate(
        project_id=project_id,
        files=request.files,
        diff=request.diff,
    )

    return result


# ============================================================================
# Default Pack Initialization
# ============================================================================


@router.post(
    "/projects/{project_id}/policy-pack/init",
    response_model=PolicyPackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize default policy pack",
    description="""
    Create a default policy pack with AI safety policies.

    **Query Parameters**:
    - tier: SDLC tier (lite, standard, professional, enterprise)
          Default: standard

    **Default Policies**:
    - no-hardcoded-secrets: Detect secrets in code
    - architecture-boundaries: Enforce 4-layer architecture
    - no-forbidden-imports: Block AGPL imports

    **Response** (201 Created):
    - Created policy pack with default policies
    """,
)
async def init_default_pack(
    project_id: UUID,
    tier: PolicyTier = PolicyTier.STANDARD,
    service: PolicyPackService = Depends(get_policy_pack_service),
    current_user: User = Depends(get_current_active_user),
):
    """Initialize default policy pack for a project."""
    if not await service.can_manage_policies(current_user, project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage policies for this project",
        )

    # Check if pack already exists
    existing = await service.get_by_project(project_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project {project_id} already has a policy pack. Delete it first or update it.",
        )

    pack = await service.create_default_pack(
        project_id=project_id,
        tier=tier,
        created_by=current_user.id,
    )

    return PolicyPackResponse(
        id=pack.id,
        project_id=pack.project_id,
        name=pack.name,
        description=pack.description,
        version=pack.version,
        tier=pack.tier,
        validators=pack.validators or [],
        coverage_threshold=pack.coverage_threshold,
        coverage_blocking=pack.coverage_blocking,
        forbidden_imports=pack.forbidden_imports or [],
        required_patterns=pack.required_patterns or [],
        policies_count=len(pack.rules) if pack.rules else 0,
        validators_count=len([v for v in (pack.validators or []) if v.get("enabled", True)]),
        created_at=pack.created_at,
        updated_at=pack.updated_at,
        created_by=pack.created_by,
    )
