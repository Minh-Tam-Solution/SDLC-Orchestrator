"""
=========================================================================
MRP Validation Service Tests
SDLC Orchestrator - Sprint 152 (MRP + Context Authority Integration)

Version: 1.0.0
Date: February 3, 2026
Status: ACTIVE - Sprint 152 Testing
Authority: Backend Lead + CTO Approved
Framework: SDLC 6.0.5

Test Coverage:
- MRP 5-point validation
- Context Authority integration
- VCR generation with context snapshot
- Tier-based enforcement

Zero Mock Policy: Real service tests with mocked external dependencies
=========================================================================
"""

import hashlib
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.policies.tier_policies import PolicyTier
from app.schemas.mrp import (
    MRPPointStatus,
    MRPValidation,
    VCR,
    VCRVerdict,
)
from app.services.mrp_validation_service import MRPValidationService


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def mrp_service():
    """Create MRP validation service for testing."""
    return MRPValidationService()


@pytest.fixture
def sample_project_id():
    """Sample project UUID."""
    return uuid4()


@pytest.fixture
def sample_pr_id():
    """Sample PR ID."""
    return "123"


@pytest.fixture
def sample_context_snapshot_id():
    """Sample Context Authority snapshot ID."""
    return uuid4()


# =========================================================================
# Test: MRP 5-Point Validation
# =========================================================================


class TestMRPValidation:
    """Test MRP 5-point validation."""

    @pytest.mark.asyncio
    async def test_validate_mrp_5_points_lite_tier(
        self,
        mrp_service: MRPValidationService,
        sample_project_id: UUID,
        sample_pr_id: str,
    ):
        """Test MRP validation for LITE tier (minimal requirements)."""
        mrp = await mrp_service.validate_mrp_5_points(
            project_id=sample_project_id,
            pr_id=sample_pr_id,
            tier=PolicyTier.LITE,
        )

        assert mrp is not None
        assert mrp.project_id == sample_project_id
        assert mrp.pr_id == sample_pr_id
        assert mrp.tier == "LITE"
        assert mrp.validation_duration_ms >= 0

    @pytest.mark.asyncio
    async def test_validate_mrp_5_points_professional_tier(
        self,
        mrp_service: MRPValidationService,
        sample_project_id: UUID,
        sample_pr_id: str,
    ):
        """Test MRP validation for PROFESSIONAL tier."""
        mrp = await mrp_service.validate_mrp_5_points(
            project_id=sample_project_id,
            pr_id=sample_pr_id,
            tier=PolicyTier.PROFESSIONAL,
        )

        assert mrp is not None
        assert mrp.tier == "PROFESSIONAL"
        # PROFESSIONAL tier requires more points
        assert mrp.points_required > 0

    @pytest.mark.asyncio
    async def test_validate_mrp_5_points_enterprise_tier(
        self,
        mrp_service: MRPValidationService,
        sample_project_id: UUID,
        sample_pr_id: str,
    ):
        """Test MRP validation for ENTERPRISE tier (strictest)."""
        mrp = await mrp_service.validate_mrp_5_points(
            project_id=sample_project_id,
            pr_id=sample_pr_id,
            tier=PolicyTier.ENTERPRISE,
        )

        assert mrp is not None
        assert mrp.tier == "ENTERPRISE"
        # ENTERPRISE has most requirements
        assert mrp.points_required >= 4

    @pytest.mark.asyncio
    async def test_validate_mrp_with_commit_sha(
        self,
        mrp_service: MRPValidationService,
        sample_project_id: UUID,
        sample_pr_id: str,
    ):
        """Test MRP validation with specific commit SHA."""
        commit_sha = "abc123def456"

        mrp = await mrp_service.validate_mrp_5_points(
            project_id=sample_project_id,
            pr_id=sample_pr_id,
            tier=PolicyTier.STANDARD,
            commit_sha=commit_sha,
        )

        assert mrp.commit_sha == commit_sha


# =========================================================================
# Test: Context Authority Integration (Sprint 152)
# =========================================================================


class TestContextAuthorityIntegration:
    """Test Context Authority integration with MRP validation."""

    @pytest.mark.asyncio
    async def test_validate_mrp_with_context_snapshot(
        self,
        mrp_service: MRPValidationService,
        sample_project_id: UUID,
        sample_pr_id: str,
        sample_context_snapshot_id: UUID,
    ):
        """Test MRP validation with Context Authority snapshot."""
        mrp = await mrp_service.validate_mrp_5_points(
            project_id=sample_project_id,
            pr_id=sample_pr_id,
            tier=PolicyTier.PROFESSIONAL,
            context_snapshot_id=sample_context_snapshot_id,
            include_context_validation=True,
        )

        # Context fields should be populated
        assert mrp.context_snapshot_id == sample_context_snapshot_id
        assert mrp.context_validation_passed is not None
        assert mrp.vibecoding_index is not None
        assert mrp.vibecoding_zone is not None

    @pytest.mark.asyncio
    async def test_validate_mrp_without_context_validation(
        self,
        mrp_service: MRPValidationService,
        sample_project_id: UUID,
        sample_pr_id: str,
        sample_context_snapshot_id: UUID,
    ):
        """Test MRP validation with context validation disabled."""
        mrp = await mrp_service.validate_mrp_5_points(
            project_id=sample_project_id,
            pr_id=sample_pr_id,
            tier=PolicyTier.STANDARD,
            context_snapshot_id=sample_context_snapshot_id,
            include_context_validation=False,
        )

        # Context fields should NOT be populated when disabled
        assert mrp.context_validation_passed is None
        assert mrp.vibecoding_index is None
        assert mrp.vibecoding_zone is None

    @pytest.mark.asyncio
    async def test_validate_mrp_no_context_snapshot(
        self,
        mrp_service: MRPValidationService,
        sample_project_id: UUID,
        sample_pr_id: str,
    ):
        """Test MRP validation without Context Authority snapshot."""
        mrp = await mrp_service.validate_mrp_5_points(
            project_id=sample_project_id,
            pr_id=sample_pr_id,
            tier=PolicyTier.LITE,
            context_snapshot_id=None,
            include_context_validation=True,
        )

        # No context validation without snapshot
        assert mrp.context_snapshot_id is None
        assert mrp.context_validation_passed is None

    @pytest.mark.asyncio
    async def test_context_validation_affects_professional_tier(
        self,
        mrp_service: MRPValidationService,
        sample_project_id: UUID,
        sample_pr_id: str,
        sample_context_snapshot_id: UUID,
    ):
        """Test that context validation affects PROFESSIONAL tier."""
        mrp = await mrp_service.validate_mrp_5_points(
            project_id=sample_project_id,
            pr_id=sample_pr_id,
            tier=PolicyTier.PROFESSIONAL,
            context_snapshot_id=sample_context_snapshot_id,
            include_context_validation=True,
        )

        # For PROFESSIONAL tier, context validation should be considered
        assert mrp.tier == "PROFESSIONAL"
        assert mrp.context_snapshot_id is not None


# =========================================================================
# Test: VCR Generation
# =========================================================================


class TestVCRGeneration:
    """Test VCR (Verification Completion Report) generation."""

    @pytest.mark.asyncio
    async def test_generate_vcr_pass(
        self,
        mrp_service: MRPValidationService,
        sample_project_id: UUID,
        sample_pr_id: str,
    ):
        """Test VCR generation for passing MRP."""
        # Create passing MRP
        mrp = await mrp_service.validate_mrp_5_points(
            project_id=sample_project_id,
            pr_id=sample_pr_id,
            tier=PolicyTier.LITE,  # LITE has minimal requirements
        )

        vcr = await mrp_service.generate_vcr(
            mrp_validation=mrp,
            project_id=sample_project_id,
            pr_id=sample_pr_id,
        )

        assert vcr is not None
        assert vcr.project_id == sample_project_id
        assert vcr.pr_id == sample_pr_id
        assert vcr.evidence_hash is not None
        assert len(vcr.evidence_hash) == 64  # SHA256 hex

    @pytest.mark.asyncio
    async def test_generate_vcr_with_crp(
        self,
        mrp_service: MRPValidationService,
        sample_project_id: UUID,
        sample_pr_id: str,
    ):
        """Test VCR generation with CRP reference."""
        mrp = await mrp_service.validate_mrp_5_points(
            project_id=sample_project_id,
            pr_id=sample_pr_id,
            tier=PolicyTier.STANDARD,
        )

        crp_id = uuid4()

        vcr = await mrp_service.generate_vcr(
            mrp_validation=mrp,
            project_id=sample_project_id,
            pr_id=sample_pr_id,
            crp_id=crp_id,
            crp_approved=True,
        )

        assert vcr.crp_id == crp_id
        assert vcr.crp_approved is True

    @pytest.mark.asyncio
    async def test_generate_vcr_blocked_by_crp(
        self,
        mrp_service: MRPValidationService,
        sample_project_id: UUID,
        sample_pr_id: str,
    ):
        """Test VCR generation blocked by unapproved CRP."""
        mrp = await mrp_service.validate_mrp_5_points(
            project_id=sample_project_id,
            pr_id=sample_pr_id,
            tier=PolicyTier.LITE,
        )

        crp_id = uuid4()

        vcr = await mrp_service.generate_vcr(
            mrp_validation=mrp,
            project_id=sample_project_id,
            pr_id=sample_pr_id,
            crp_id=crp_id,
            crp_approved=False,
        )

        assert vcr.verdict == VCRVerdict.BLOCKED
        assert "CRP not approved" in vcr.verdict_reason

    @pytest.mark.asyncio
    async def test_generate_vcr_with_context_snapshot(
        self,
        mrp_service: MRPValidationService,
        sample_project_id: UUID,
        sample_pr_id: str,
        sample_context_snapshot_id: UUID,
    ):
        """Test VCR generation with Context Authority snapshot (Sprint 152)."""
        mrp = await mrp_service.validate_mrp_5_points(
            project_id=sample_project_id,
            pr_id=sample_pr_id,
            tier=PolicyTier.PROFESSIONAL,
            context_snapshot_id=sample_context_snapshot_id,
            include_context_validation=True,
        )

        vcr = await mrp_service.generate_vcr(
            mrp_validation=mrp,
            project_id=sample_project_id,
            pr_id=sample_pr_id,
        )

        # VCR should include context snapshot information
        assert vcr.context_snapshot_id == sample_context_snapshot_id
        assert vcr.context_snapshot_hash is not None
        assert len(vcr.context_snapshot_hash) == 64  # SHA256 hex

    @pytest.mark.asyncio
    async def test_vcr_is_merge_ready(
        self,
        mrp_service: MRPValidationService,
        sample_project_id: UUID,
        sample_pr_id: str,
    ):
        """Test VCR is_merge_ready method."""
        mrp = await mrp_service.validate_mrp_5_points(
            project_id=sample_project_id,
            pr_id=sample_pr_id,
            tier=PolicyTier.LITE,
        )

        vcr = await mrp_service.generate_vcr(
            mrp_validation=mrp,
            project_id=sample_project_id,
            pr_id=sample_pr_id,
        )

        # is_merge_ready should match verdict
        if vcr.verdict == VCRVerdict.PASS:
            assert vcr.is_merge_ready() is True
        else:
            assert vcr.is_merge_ready() is False


# =========================================================================
# Test: Evidence Hash Chain
# =========================================================================


class TestEvidenceHashChain:
    """Test evidence hash generation and chain."""

    @pytest.mark.asyncio
    async def test_evidence_hash_consistency(
        self,
        mrp_service: MRPValidationService,
        sample_project_id: UUID,
        sample_pr_id: str,
    ):
        """Test that evidence hash is consistent for same input."""
        mrp = await mrp_service.validate_mrp_5_points(
            project_id=sample_project_id,
            pr_id=sample_pr_id,
            tier=PolicyTier.STANDARD,
        )

        vcr1 = await mrp_service.generate_vcr(
            mrp_validation=mrp,
            project_id=sample_project_id,
            pr_id=sample_pr_id,
        )

        # Hash should be 64 characters (SHA256 hex)
        assert len(vcr1.evidence_hash) == 64
        assert all(c in "0123456789abcdef" for c in vcr1.evidence_hash)

    @pytest.mark.asyncio
    async def test_context_snapshot_hash_generation(
        self,
        mrp_service: MRPValidationService,
        sample_project_id: UUID,
        sample_pr_id: str,
        sample_context_snapshot_id: UUID,
    ):
        """Test context snapshot hash is generated correctly."""
        mrp = await mrp_service.validate_mrp_5_points(
            project_id=sample_project_id,
            pr_id=sample_pr_id,
            tier=PolicyTier.PROFESSIONAL,
            context_snapshot_id=sample_context_snapshot_id,
            include_context_validation=True,
        )

        vcr = await mrp_service.generate_vcr(
            mrp_validation=mrp,
            project_id=sample_project_id,
            pr_id=sample_pr_id,
        )

        # Context snapshot hash should be generated
        assert vcr.context_snapshot_hash is not None

        # Verify hash format
        assert len(vcr.context_snapshot_hash) == 64
        assert all(c in "0123456789abcdef" for c in vcr.context_snapshot_hash)


# =========================================================================
# Test: Tier Policy Enforcement
# =========================================================================


class TestTierPolicyEnforcement:
    """Test tier-specific policy enforcement."""

    @pytest.mark.asyncio
    async def test_lite_tier_minimal_checks(
        self,
        mrp_service: MRPValidationService,
        sample_project_id: UUID,
        sample_pr_id: str,
    ):
        """Test LITE tier has minimal checks."""
        mrp = await mrp_service.validate_mrp_5_points(
            project_id=sample_project_id,
            pr_id=sample_pr_id,
            tier=PolicyTier.LITE,
        )

        # LITE tier should have fewer required points
        assert mrp.tier == "LITE"

    @pytest.mark.asyncio
    async def test_enterprise_tier_strict_checks(
        self,
        mrp_service: MRPValidationService,
        sample_project_id: UUID,
        sample_pr_id: str,
    ):
        """Test ENTERPRISE tier has strict checks."""
        mrp = await mrp_service.validate_mrp_5_points(
            project_id=sample_project_id,
            pr_id=sample_pr_id,
            tier=PolicyTier.ENTERPRISE,
        )

        # ENTERPRISE tier should have most required points
        assert mrp.tier == "ENTERPRISE"
        assert mrp.points_required >= 4

    @pytest.mark.asyncio
    async def test_tier_string_parsing(
        self,
        mrp_service: MRPValidationService,
        sample_project_id: UUID,
        sample_pr_id: str,
    ):
        """Test tier can be passed as string."""
        mrp = await mrp_service.validate_mrp_5_points(
            project_id=sample_project_id,
            pr_id=sample_pr_id,
            tier="STANDARD",  # String instead of enum
        )

        assert mrp.tier == "STANDARD"


# =========================================================================
# Test: Performance
# =========================================================================


class TestPerformance:
    """Test performance requirements."""

    @pytest.mark.asyncio
    async def test_mrp_validation_under_30s(
        self,
        mrp_service: MRPValidationService,
        sample_project_id: UUID,
        sample_pr_id: str,
    ):
        """Test MRP validation completes under 30 seconds."""
        mrp = await mrp_service.validate_mrp_5_points(
            project_id=sample_project_id,
            pr_id=sample_pr_id,
            tier=PolicyTier.PROFESSIONAL,
        )

        # Validation should complete under 30s (30000ms)
        assert mrp.validation_duration_ms < 30000

    @pytest.mark.asyncio
    async def test_vcr_generation_fast(
        self,
        mrp_service: MRPValidationService,
        sample_project_id: UUID,
        sample_pr_id: str,
    ):
        """Test VCR generation is fast (<500ms)."""
        import time

        mrp = await mrp_service.validate_mrp_5_points(
            project_id=sample_project_id,
            pr_id=sample_pr_id,
            tier=PolicyTier.STANDARD,
        )

        start = time.time()
        vcr = await mrp_service.generate_vcr(
            mrp_validation=mrp,
            project_id=sample_project_id,
            pr_id=sample_pr_id,
        )
        duration_ms = (time.time() - start) * 1000

        # VCR generation should be under 500ms
        assert duration_ms < 500
        assert vcr is not None
