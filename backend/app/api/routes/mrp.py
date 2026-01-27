"""
=========================================================================
MRP/VCR API Routes - SDLC Orchestrator
Sprint 102: MRP/VCR 5-Point Validation + 4-Tier Enforcement

Version: 1.0.0
Date: January 23, 2026
Status: ACTIVE - Sprint 102 Implementation
Authority: Backend Lead + CTO Approved
Reference: docs/04-build/02-Sprint-Plans/SPRINT-102-DESIGN.md

Endpoints:
- POST /mrp/validate: Validate MRP 5-point structure for PR
- GET /mrp/validate/{project_id}/{pr_id}: Get latest MRP validation
- GET /vcr/{project_id}/{pr_id}: Get latest VCR
- GET /vcr/{project_id}/{pr_id}/history: Get VCR history
- POST /policies/enforce: Enforce policies for PR
- GET /policies/tiers: Get all policy tiers
- GET /policies/compliance/{project_id}: Get tier compliance report
- POST /policies/compare: Compare two tiers

SDLC 5.2.0 Compliance:
- MRP 5-Point Evidence Structure
- 4-Tier Policy Enforcement
- VCR (Verification Completion Report)

Zero Mock Policy: Production-ready FastAPI routes
=========================================================================
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user
from app.policies.tier_policies import (
    PolicyTier,
    get_tier_policy,
    get_all_tiers,
    compare_tiers,
)
from app.schemas.mrp import (
    MRPValidation,
    TierComplianceReport,
    ValidateMRPRequest,
    ValidateMRPResponse,
    VCR,
    VCRHistoryResponse,
)
from app.services.mrp_validation_service import (
    MRPValidationService,
    create_mrp_validation_service,
)
from app.services.policy_enforcement_service import (
    PolicyEnforcementService,
    PolicyEnforcementResult,
    create_policy_enforcement_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mrp", tags=["MRP - Merge Readiness Protocol"])


# =============================================================================
# Dependency Injection
# =============================================================================


def get_mrp_service() -> MRPValidationService:
    """Get MRP validation service instance."""
    return create_mrp_validation_service()


def get_enforcement_service() -> PolicyEnforcementService:
    """Get policy enforcement service instance."""
    return create_policy_enforcement_service()


# =============================================================================
# Request/Response Models
# =============================================================================


class PolicyTierResponse(BaseModel):
    """Response for policy tier info."""
    tier: str = Field(..., description="Tier name")
    display_name: str = Field(..., description="Display name")
    description: str = Field(..., description="Tier description")
    target_audience: str = Field(..., description="Target audience")
    enforcement_mode: str = Field(..., description="Enforcement mode")
    test_coverage_required: int = Field(..., description="Test coverage required (%)")
    mrp_points_required: int = Field(..., description="MRP points required (0-5)")
    required_checks: list[str] = Field(..., description="List of required checks")


class AllTiersResponse(BaseModel):
    """Response for all tiers."""
    tiers: list[PolicyTierResponse] = Field(..., description="All policy tiers")


class CompareTiersRequest(BaseModel):
    """Request to compare two tiers."""
    current_tier: str = Field(..., description="Current tier")
    target_tier: str = Field(..., description="Target tier")


class CompareTiersResponse(BaseModel):
    """Response from tier comparison."""
    current_tier: str
    target_tier: str
    direction: str = Field(..., description="upgrade | downgrade | same")
    new_requirements: list[str]
    removed_requirements: list[str]
    stricter_thresholds: dict
    relaxed_thresholds: dict
    current_mrp_points: int
    target_mrp_points: int


class EnforcePoliciesRequest(BaseModel):
    """Request to enforce policies for PR."""
    project_id: UUID = Field(..., description="Project UUID")
    pr_id: str = Field(..., description="Pull request ID")
    tier_override: Optional[str] = Field(
        default=None,
        description="Override tier for testing",
    )
    commit_sha: Optional[str] = Field(
        default=None,
        description="Specific commit SHA",
    )


class EnforcePoliciesResponse(BaseModel):
    """Response from policy enforcement."""
    tier: str
    enforcement_mode: str
    should_block_merge: bool
    github_check_conclusion: str
    enforcement_actions: list[str]
    vcr: VCR


# =============================================================================
# MRP Validation Endpoints
# =============================================================================


@router.post(
    "/validate",
    response_model=ValidateMRPResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate MRP 5-point structure",
    description="""
    Validate MRP (Merge Readiness Protocol) 5-point evidence structure for a PR.

    The 5 MRP points:
    1. **Test Evidence**: Unit/integration test results and coverage
    2. **Lint Evidence**: ruff/eslint zero errors
    3. **Security Evidence**: bandit/grype vulnerability scan
    4. **Build Evidence**: Docker/package build success
    5. **Conformance Evidence**: Pattern alignment and ADR check

    Validation is performed against the project's policy tier.

    Performance: <30s (p95)
    """,
)
async def validate_mrp(
    body: ValidateMRPRequest,
    mrp_service: MRPValidationService = Depends(get_mrp_service),
    current_user: dict = Depends(get_current_user),
) -> ValidateMRPResponse:
    """
    Validate MRP 5-point structure for a PR.

    Args:
        body: Validation request with project_id and pr_id
        mrp_service: MRP validation service
        current_user: Authenticated user

    Returns:
        ValidateMRPResponse with MRP validation and optional VCR
    """
    logger.info(
        f"MRP validation request for project {body.project_id}, PR {body.pr_id} "
        f"by user {current_user.get('sub')}"
    )

    try:
        # Default to PROFESSIONAL tier for now
        # TODO: Get tier from project settings
        tier = PolicyTier.PROFESSIONAL

        # Validate MRP
        mrp_validation = await mrp_service.validate_mrp_5_points(
            project_id=body.project_id,
            pr_id=body.pr_id,
            tier=tier,
            commit_sha=body.commit_sha,
        )

        # Generate VCR
        user_id = None
        if current_user.get("sub"):
            try:
                user_id = UUID(current_user.get("sub"))
            except ValueError:
                pass

        vcr = await mrp_service.generate_vcr(
            mrp_validation=mrp_validation,
            project_id=body.project_id,
            pr_id=body.pr_id,
            created_by=user_id,
        )

        return ValidateMRPResponse(
            mrp_validation=mrp_validation,
            vcr=vcr,
            github_check_url=None,  # TODO: Implement GitHub check
        )

    except Exception as e:
        logger.error(f"MRP validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MRP validation failed: {str(e)}",
        )


@router.get(
    "/validate/{project_id}/{pr_id}",
    response_model=MRPValidation,
    summary="Get latest MRP validation",
    description="Retrieve the latest MRP validation for a PR.",
)
async def get_mrp_validation(
    project_id: UUID,
    pr_id: str,
    mrp_service: MRPValidationService = Depends(get_mrp_service),
    current_user: dict = Depends(get_current_user),
) -> MRPValidation:
    """
    Get latest MRP validation for a PR.

    Args:
        project_id: Project UUID
        pr_id: Pull request ID
        mrp_service: MRP validation service
        current_user: Authenticated user

    Returns:
        Latest MRPValidation
    """
    logger.info(f"Getting MRP validation for project {project_id}, PR {pr_id}")

    # TODO: Implement caching/storage lookup
    # For now, run fresh validation
    mrp = await mrp_service.validate_mrp_5_points(
        project_id=project_id,
        pr_id=pr_id,
        tier=PolicyTier.PROFESSIONAL,
    )

    return mrp


# =============================================================================
# VCR Endpoints
# =============================================================================


@router.get(
    "/vcr/{project_id}/{pr_id}",
    response_model=VCR,
    summary="Get latest VCR",
    description="Retrieve the latest VCR (Verification Completion Report) for a PR.",
)
async def get_vcr(
    project_id: UUID,
    pr_id: str,
    mrp_service: MRPValidationService = Depends(get_mrp_service),
    current_user: dict = Depends(get_current_user),
) -> VCR:
    """
    Get latest VCR for a PR.

    Args:
        project_id: Project UUID
        pr_id: Pull request ID
        mrp_service: MRP validation service
        current_user: Authenticated user

    Returns:
        Latest VCR
    """
    logger.info(f"Getting VCR for project {project_id}, PR {pr_id}")

    # TODO: Implement storage lookup
    # For now, generate fresh VCR
    mrp = await mrp_service.validate_mrp_5_points(
        project_id=project_id,
        pr_id=pr_id,
        tier=PolicyTier.PROFESSIONAL,
    )

    vcr = await mrp_service.generate_vcr(
        mrp_validation=mrp,
        project_id=project_id,
        pr_id=pr_id,
    )

    return vcr


@router.get(
    "/vcr/{project_id}/history",
    response_model=VCRHistoryResponse,
    summary="Get VCR history",
    description="Retrieve VCR history for a PR or project.",
)
async def get_vcr_history(
    project_id: UUID,
    pr_id: Optional[str] = Query(default=None, description="Filter by PR ID"),
    limit: int = Query(default=20, ge=1, le=100, description="Max results"),
    current_user: dict = Depends(get_current_user),
) -> VCRHistoryResponse:
    """
    Get VCR history for a project or PR.

    Args:
        project_id: Project UUID
        pr_id: Optional PR ID filter
        limit: Max results to return
        current_user: Authenticated user

    Returns:
        VCRHistoryResponse with list of VCRs
    """
    logger.info(f"Getting VCR history for project {project_id}, PR filter: {pr_id}")

    # TODO: Implement storage lookup
    # For now, return empty list
    return VCRHistoryResponse(
        vcrs=[],
        total=0,
        project_id=project_id,
        pr_id=pr_id,
    )


# =============================================================================
# Policy Endpoints
# =============================================================================


policies_router = APIRouter(prefix="/policies", tags=["MRP - Policy Enforcement"])


@policies_router.post(
    "/enforce",
    response_model=EnforcePoliciesResponse,
    summary="Enforce policies for PR",
    description="""
    Enforce 4-tier policies for a PR.

    This endpoint:
    1. Gets project's policy tier
    2. Runs MRP 5-point validation
    3. Generates VCR
    4. Determines enforcement action
    5. (Optionally) Updates GitHub check

    **Enforcement Modes**:
    - LITE: Advisory only, never blocks
    - STANDARD: Soft enforcement, warnings only
    - PROFESSIONAL: Hard enforcement, blocks on failure
    - ENTERPRISE: Strictest, zero tolerance

    Performance: <30s (p95)
    """,
)
async def enforce_policies(
    body: EnforcePoliciesRequest,
    enforcement_service: PolicyEnforcementService = Depends(get_enforcement_service),
    current_user: dict = Depends(get_current_user),
) -> EnforcePoliciesResponse:
    """
    Enforce policies for a PR.

    Args:
        body: Enforcement request
        enforcement_service: Policy enforcement service
        current_user: Authenticated user

    Returns:
        EnforcePoliciesResponse with enforcement result
    """
    logger.info(
        f"Policy enforcement request for project {body.project_id}, PR {body.pr_id} "
        f"by user {current_user.get('sub')}"
    )

    try:
        # Parse tier override
        tier = None
        if body.tier_override:
            try:
                tier = PolicyTier(body.tier_override.upper())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid tier: {body.tier_override}",
                )

        # Get user ID
        user_id = None
        if current_user.get("sub"):
            try:
                user_id = UUID(current_user.get("sub"))
            except ValueError:
                pass

        # Enforce policies
        result = await enforcement_service.enforce_pr_policies(
            project_id=body.project_id,
            pr_id=body.pr_id,
            tier=tier,
            commit_sha=body.commit_sha,
            created_by=user_id,
        )

        return EnforcePoliciesResponse(
            tier=result.tier,
            enforcement_mode=result.enforcement_mode,
            should_block_merge=result.should_block_merge,
            github_check_conclusion=result.github_check_conclusion,
            enforcement_actions=result.enforcement_actions,
            vcr=result.vcr,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Policy enforcement failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Policy enforcement failed: {str(e)}",
        )


@policies_router.get(
    "/tiers",
    response_model=AllTiersResponse,
    summary="Get all policy tiers",
    description="Retrieve all available policy tiers with their requirements.",
)
async def get_policy_tiers(
    current_user: dict = Depends(get_current_user),
) -> AllTiersResponse:
    """
    Get all available policy tiers.

    Returns:
        AllTiersResponse with all tier configurations
    """
    tiers = []
    for policy in get_all_tiers():
        tiers.append(PolicyTierResponse(
            tier=policy.tier.value,
            display_name=policy.display_name,
            description=policy.description,
            target_audience=policy.target_audience,
            enforcement_mode=policy.enforcement_mode,
            test_coverage_required=policy.test_coverage_required,
            mrp_points_required=policy.get_mrp_points_required(),
            required_checks=policy.get_required_checks(),
        ))

    return AllTiersResponse(tiers=tiers)


@policies_router.get(
    "/compliance/{project_id}",
    response_model=TierComplianceReport,
    summary="Get tier compliance report",
    description="Check if project meets current tier requirements.",
)
async def get_compliance_report(
    project_id: UUID,
    enforcement_service: PolicyEnforcementService = Depends(get_enforcement_service),
    current_user: dict = Depends(get_current_user),
) -> TierComplianceReport:
    """
    Get tier compliance report for a project.

    Args:
        project_id: Project UUID
        enforcement_service: Policy enforcement service
        current_user: Authenticated user

    Returns:
        TierComplianceReport with compliance status
    """
    logger.info(f"Getting compliance report for project {project_id}")

    report = await enforcement_service.check_tier_compliance(project_id=project_id)
    return report


@policies_router.post(
    "/compare",
    response_model=CompareTiersResponse,
    summary="Compare two tiers",
    description="Compare requirements between two tiers for upgrade/downgrade planning.",
)
async def compare_policy_tiers(
    body: CompareTiersRequest,
    current_user: dict = Depends(get_current_user),
) -> CompareTiersResponse:
    """
    Compare two policy tiers.

    Args:
        body: Comparison request with current and target tiers
        current_user: Authenticated user

    Returns:
        CompareTiersResponse with differences
    """
    try:
        comparison = compare_tiers(body.current_tier, body.target_tier)
        return CompareTiersResponse(**comparison)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# Health Check
# =============================================================================


@router.get(
    "/health",
    summary="Health check",
    description="Check MRP service health.",
)
async def health_check() -> dict:
    """
    Health check endpoint for MRP service.

    Returns:
        Health status dict
    """
    return {
        "status": "healthy",
        "service": "mrp-validation",
        "version": "1.0.0",
        "features": [
            "5-point-mrp-validation",
            "vcr-generation",
            "4-tier-policy-enforcement",
        ],
    }


# Include policies router in main router
router.include_router(policies_router)
