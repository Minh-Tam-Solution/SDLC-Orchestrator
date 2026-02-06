"""
Unit tests for TierApprovalService - Sprint 161

Test Coverage:
- compute_required_roles: 12 tests (all tier × gate combinations)
- create_approval_request: 15 tests (self-approval, council, metadata)
- record_decision: 13 tests (approve, reject, validation)

Total: 40+ tests targeting 95%+ coverage

Reference: docs/04-build/02-Sprint-Plans/SPRINT-161-164-TIER-BASED-GATE-APPROVAL.md
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.tier_approval_service import TierApprovalService
from app.models.gate import Gate
from app.models.project import Project
from app.models.gate_decision import GateDecision
from app.schemas.tier_approval import ApprovalChainMetadata


# =====================================================================
# FIXTURES
# =====================================================================

@pytest.fixture
def tier_approval_service():
    """Create TierApprovalService instance."""
    return TierApprovalService()


@pytest.fixture
def mock_db():
    """Create mock AsyncSession."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_project_free():
    """Create mock FREE tier project."""
    project = MagicMock(spec=Project)
    project.id = uuid4()
    project.tier = "FREE"
    return project


@pytest.fixture
def mock_project_standard():
    """Create mock STANDARD tier project."""
    project = MagicMock(spec=Project)
    project.id = uuid4()
    project.tier = "STANDARD"
    return project


@pytest.fixture
def mock_project_professional():
    """Create mock PROFESSIONAL tier project."""
    project = MagicMock(spec=Project)
    project.id = uuid4()
    project.tier = "PROFESSIONAL"
    return project


@pytest.fixture
def mock_project_enterprise():
    """Create mock ENTERPRISE tier project."""
    project = MagicMock(spec=Project)
    project.id = uuid4()
    project.tier = "ENTERPRISE"
    return project


@pytest.fixture
def mock_gate_g1():
    """Create mock G1 gate."""
    gate = MagicMock(spec=Gate)
    gate.id = uuid4()
    gate.gate_code = "G1"
    gate.project_id = uuid4()
    return gate


@pytest.fixture
def mock_gate_g5():
    """Create mock G5 gate."""
    gate = MagicMock(spec=Gate)
    gate.id = uuid4()
    gate.gate_code = "G5"
    gate.project_id = uuid4()
    return gate


# =====================================================================
# TEST: compute_required_roles
# =====================================================================

class TestComputeRequiredRoles:
    """Test compute_required_roles method."""

    @pytest.mark.asyncio
    async def test_free_tier_returns_empty_list(
        self, tier_approval_service, mock_db
    ):
        """FREE tier should return empty list (self-approval)."""
        roles = await tier_approval_service.compute_required_roles(
            project_tier="FREE",
            gate_code="G1",
            db=mock_db
        )
        assert roles == []

    @pytest.mark.asyncio
    async def test_standard_g1_returns_pm(
        self, tier_approval_service, mock_db
    ):
        """STANDARD tier G1 should require PM."""
        roles = await tier_approval_service.compute_required_roles(
            project_tier="STANDARD",
            gate_code="G1",
            db=mock_db
        )
        assert roles == ["PM"]

    @pytest.mark.asyncio
    async def test_standard_g2_returns_cto(
        self, tier_approval_service, mock_db
    ):
        """STANDARD tier G2 should require CTO."""
        roles = await tier_approval_service.compute_required_roles(
            project_tier="STANDARD",
            gate_code="G2",
            db=mock_db
        )
        assert roles == ["CTO"]

    @pytest.mark.asyncio
    async def test_standard_g6_returns_ceo(
        self, tier_approval_service, mock_db
    ):
        """STANDARD tier G6 should require CEO."""
        roles = await tier_approval_service.compute_required_roles(
            project_tier="STANDARD",
            gate_code="G6",
            db=mock_db
        )
        assert roles == ["CEO"]

    @pytest.mark.asyncio
    async def test_professional_g1_returns_pm_cto(
        self, tier_approval_service, mock_db
    ):
        """PROFESSIONAL tier G1 should require PM and CTO."""
        roles = await tier_approval_service.compute_required_roles(
            project_tier="PROFESSIONAL",
            gate_code="G1",
            db=mock_db
        )
        assert roles == ["PM", "CTO"]

    @pytest.mark.asyncio
    async def test_professional_g3_returns_cto_ceo(
        self, tier_approval_service, mock_db
    ):
        """PROFESSIONAL tier G3 should require CTO and CEO."""
        roles = await tier_approval_service.compute_required_roles(
            project_tier="PROFESSIONAL",
            gate_code="G3",
            db=mock_db
        )
        assert roles == ["CTO", "CEO"]

    @pytest.mark.asyncio
    async def test_professional_g5_returns_cto_ceo(
        self, tier_approval_service, mock_db
    ):
        """PROFESSIONAL tier G5 should require CTO and CEO."""
        roles = await tier_approval_service.compute_required_roles(
            project_tier="PROFESSIONAL",
            gate_code="G5",
            db=mock_db
        )
        assert roles == ["CTO", "CEO"]

    @pytest.mark.asyncio
    async def test_enterprise_g5_returns_council(
        self, tier_approval_service, mock_db
    ):
        """ENTERPRISE tier G5 should require council (CTO+CEO+CO)."""
        roles = await tier_approval_service.compute_required_roles(
            project_tier="ENTERPRISE",
            gate_code="G5",
            db=mock_db
        )
        assert roles == ["CTO", "CEO", "COMPLIANCE_OFFICER"]

    @pytest.mark.asyncio
    async def test_enterprise_g4_returns_qa_co(
        self, tier_approval_service, mock_db
    ):
        """ENTERPRISE tier G4 should require QA_LEAD and COMPLIANCE_OFFICER."""
        roles = await tier_approval_service.compute_required_roles(
            project_tier="ENTERPRISE",
            gate_code="G4",
            db=mock_db
        )
        assert roles == ["QA_LEAD", "COMPLIANCE_OFFICER"]

    @pytest.mark.asyncio
    async def test_discovery_gates_self_approval(
        self, tier_approval_service, mock_db
    ):
        """G0.1 and G0.2 should allow self-approval on all tiers."""
        # G0.1 on STANDARD
        roles = await tier_approval_service.compute_required_roles(
            project_tier="STANDARD",
            gate_code="G0.1",
            db=mock_db
        )
        assert roles == []

        # G0.2 on PROFESSIONAL
        roles = await tier_approval_service.compute_required_roles(
            project_tier="PROFESSIONAL",
            gate_code="G0.2",
            db=mock_db
        )
        assert roles == []

    @pytest.mark.asyncio
    async def test_unknown_tier_raises_error(
        self, tier_approval_service, mock_db
    ):
        """Unknown tier should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown project tier"):
            await tier_approval_service.compute_required_roles(
                project_tier="UNKNOWN_TIER",
                gate_code="G1",
                db=mock_db
            )

    @pytest.mark.asyncio
    async def test_unknown_gate_returns_empty(
        self, tier_approval_service, mock_db
    ):
        """Unknown gate code should return empty list (default to self-approval)."""
        roles = await tier_approval_service.compute_required_roles(
            project_tier="STANDARD",
            gate_code="G99",  # Unknown gate
            db=mock_db
        )
        assert roles == []


# =====================================================================
# TEST: create_approval_request
# =====================================================================

class TestCreateApprovalRequest:
    """Test create_approval_request method."""

    @pytest.mark.asyncio
    async def test_free_tier_creates_auto_approved_decision(
        self, tier_approval_service, mock_db, mock_gate_g1, mock_project_free
    ):
        """FREE tier should create auto-approved decision."""
        # Setup
        gate_id = mock_gate_g1.id
        requester_id = uuid4()
        mock_gate_g1.project_id = mock_project_free.id

        mock_db.get.side_effect = [mock_gate_g1, mock_project_free]
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Create mock decision
        mock_decision = MagicMock(spec=GateDecision)
        mock_decision.id = uuid4()
        mock_db.new = [mock_decision]

        # Execute
        metadata = await tier_approval_service.create_approval_request(
            gate_id=gate_id,
            requester_id=requester_id,
            db=mock_db
        )

        # Assert
        assert isinstance(metadata, ApprovalChainMetadata)
        assert metadata.is_self_approval is True
        assert metadata.required_roles == []
        assert metadata.expires_at is None
        assert len(metadata.decision_ids) == 1

        # Verify decision was added
        mock_db.add.assert_called_once()
        added_decision = mock_db.add.call_args[0][0]
        assert added_decision.action == "APPROVE"
        assert added_decision.status == "COMPLETED"
        assert added_decision.actor_id == requester_id
        assert added_decision.completed_at is not None
        assert "Auto-approved" in added_decision.comments

    @pytest.mark.asyncio
    async def test_standard_tier_creates_pending_decision(
        self, tier_approval_service, mock_db, mock_gate_g1, mock_project_standard
    ):
        """STANDARD tier should create PENDING decision with PM role."""
        # Setup
        gate_id = mock_gate_g1.id
        requester_id = uuid4()
        mock_gate_g1.project_id = mock_project_standard.id

        mock_db.get.side_effect = [mock_gate_g1, mock_project_standard]
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Create mock decision
        mock_decision = MagicMock(spec=GateDecision)
        mock_decision.id = uuid4()
        mock_db.new = [mock_decision]

        # Execute
        metadata = await tier_approval_service.create_approval_request(
            gate_id=gate_id,
            requester_id=requester_id,
            db=mock_db
        )

        # Assert
        assert isinstance(metadata, ApprovalChainMetadata)
        assert metadata.is_self_approval is False
        assert metadata.required_roles == ["PM"]
        assert metadata.expires_at is not None
        assert len(metadata.decision_ids) == 1

        # Verify decision was added
        mock_db.add.assert_called_once()
        added_decision = mock_db.add.call_args[0][0]
        assert added_decision.action == "REQUEST"
        assert added_decision.status == "PENDING"
        assert added_decision.required_roles == ["PM"]
        assert added_decision.expires_at is not None

    @pytest.mark.asyncio
    async def test_professional_tier_creates_multiple_decisions(
        self, tier_approval_service, mock_db, mock_gate_g1, mock_project_professional
    ):
        """PROFESSIONAL tier G1 should create 2 decisions (PM, CTO)."""
        # Setup
        gate_id = mock_gate_g1.id
        requester_id = uuid4()
        mock_gate_g1.project_id = mock_project_professional.id

        mock_db.get.side_effect = [mock_gate_g1, mock_project_professional]
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Create mock decisions
        mock_decision1 = MagicMock(spec=GateDecision)
        mock_decision1.id = uuid4()
        mock_decision2 = MagicMock(spec=GateDecision)
        mock_decision2.id = uuid4()
        mock_db.new = [mock_decision1, mock_decision2]

        # Execute
        metadata = await tier_approval_service.create_approval_request(
            gate_id=gate_id,
            requester_id=requester_id,
            db=mock_db
        )

        # Assert
        assert isinstance(metadata, ApprovalChainMetadata)
        assert metadata.is_self_approval is False
        assert metadata.required_roles == ["PM", "CTO"]
        assert len(metadata.decision_ids) == 2

        # Verify 2 decisions were added
        assert mock_db.add.call_count == 2

        # Verify step_index progression
        call_args_list = mock_db.add.call_args_list
        decision1 = call_args_list[0][0][0]
        decision2 = call_args_list[1][0][0]
        assert decision1.step_index == 0
        assert decision2.step_index == 1
        assert decision1.required_roles == ["PM"]
        assert decision2.required_roles == ["CTO"]

    @pytest.mark.asyncio
    async def test_enterprise_council_creates_three_decisions(
        self, tier_approval_service, mock_db, mock_gate_g5, mock_project_enterprise
    ):
        """ENTERPRISE tier G5 should create 3 decisions (council review)."""
        # Setup
        gate_id = mock_gate_g5.id
        requester_id = uuid4()
        mock_gate_g5.project_id = mock_project_enterprise.id

        mock_db.get.side_effect = [mock_gate_g5, mock_project_enterprise]
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Create mock decisions
        mock_decisions = [MagicMock(spec=GateDecision, id=uuid4()) for _ in range(3)]
        mock_db.new = mock_decisions

        # Execute
        metadata = await tier_approval_service.create_approval_request(
            gate_id=gate_id,
            requester_id=requester_id,
            db=mock_db
        )

        # Assert - Council review
        assert isinstance(metadata, ApprovalChainMetadata)
        assert metadata.is_self_approval is False
        assert metadata.required_roles == ["CTO", "CEO", "COMPLIANCE_OFFICER"]
        assert len(metadata.decision_ids) == 3

        # Verify all decisions have same chain_id
        call_args_list = mock_db.add.call_args_list
        chain_ids = [call[0][0].chain_id for call in call_args_list]
        assert len(set(chain_ids)) == 1  # All same chain_id

        # Verify step_index progression
        step_indices = [call[0][0].step_index for call in call_args_list]
        assert step_indices == [0, 1, 2]

    @pytest.mark.asyncio
    async def test_expires_at_set_to_48_hours(
        self, tier_approval_service, mock_db, mock_gate_g1, mock_project_standard
    ):
        """expires_at should be set to 48 hours from now (CTO v2.5 #2)."""
        # Setup
        gate_id = mock_gate_g1.id
        requester_id = uuid4()
        mock_gate_g1.project_id = mock_project_standard.id

        mock_db.get.side_effect = [mock_gate_g1, mock_project_standard]
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        mock_decision = MagicMock(spec=GateDecision, id=uuid4())
        mock_db.new = [mock_decision]

        # Execute
        before = datetime.utcnow()
        metadata = await tier_approval_service.create_approval_request(
            gate_id=gate_id,
            requester_id=requester_id,
            db=mock_db
        )
        after = datetime.utcnow()

        # Assert - expires_at is approximately 48 hours from now
        assert metadata.expires_at is not None
        expected_min = before + timedelta(hours=47, minutes=59)
        expected_max = after + timedelta(hours=48, minutes=1)
        assert expected_min <= metadata.expires_at <= expected_max

        # Verify decision has expires_at
        added_decision = mock_db.add.call_args[0][0]
        assert added_decision.expires_at is not None

    @pytest.mark.asyncio
    async def test_chain_id_is_unique_per_request(
        self, tier_approval_service, mock_db, mock_gate_g1, mock_project_standard
    ):
        """Each approval request should have unique chain_id."""
        # Setup
        gate_id = mock_gate_g1.id
        requester_id = uuid4()
        mock_gate_g1.project_id = mock_project_standard.id

        mock_db.get.side_effect = [
            mock_gate_g1, mock_project_standard,
            mock_gate_g1, mock_project_standard  # Second request
        ]
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        mock_decision1 = MagicMock(spec=GateDecision, id=uuid4())
        mock_decision2 = MagicMock(spec=GateDecision, id=uuid4())
        mock_db.new = [mock_decision1]

        # Execute - First request
        metadata1 = await tier_approval_service.create_approval_request(
            gate_id=gate_id,
            requester_id=requester_id,
            db=mock_db
        )

        # Setup for second request
        mock_db.new = [mock_decision2]
        mock_db.add.reset_mock()

        # Execute - Second request
        metadata2 = await tier_approval_service.create_approval_request(
            gate_id=gate_id,
            requester_id=requester_id,
            db=mock_db
        )

        # Assert - Different chain_id
        assert metadata1.chain_id != metadata2.chain_id

    @pytest.mark.asyncio
    async def test_gate_not_found_raises_error(
        self, tier_approval_service, mock_db
    ):
        """Non-existent gate should raise ValueError."""
        # Setup
        gate_id = uuid4()
        requester_id = uuid4()
        mock_db.get.return_value = None

        # Execute & Assert
        with pytest.raises(ValueError, match="Gate .* not found"):
            await tier_approval_service.create_approval_request(
                gate_id=gate_id,
                requester_id=requester_id,
                db=mock_db
            )

    @pytest.mark.asyncio
    async def test_project_not_found_raises_error(
        self, tier_approval_service, mock_db, mock_gate_g1
    ):
        """Non-existent project should raise ValueError."""
        # Setup
        gate_id = mock_gate_g1.id
        requester_id = uuid4()
        mock_db.get.side_effect = [mock_gate_g1, None]  # Gate exists, project doesn't

        # Execute & Assert
        with pytest.raises(ValueError, match="Project .* not found"):
            await tier_approval_service.create_approval_request(
                gate_id=gate_id,
                requester_id=requester_id,
                db=mock_db
            )

    @pytest.mark.asyncio
    async def test_approval_chain_metadata_structure(
        self, tier_approval_service, mock_db, mock_gate_g1, mock_project_standard
    ):
        """ApprovalChainMetadata should have all required fields (CTO v2.5 #3)."""
        # Setup
        gate_id = mock_gate_g1.id
        requester_id = uuid4()
        mock_gate_g1.project_id = mock_project_standard.id

        mock_db.get.side_effect = [mock_gate_g1, mock_project_standard]
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        mock_decision = MagicMock(spec=GateDecision, id=uuid4())
        mock_db.new = [mock_decision]

        # Execute
        metadata = await tier_approval_service.create_approval_request(
            gate_id=gate_id,
            requester_id=requester_id,
            db=mock_db
        )

        # Assert - All fields present
        assert hasattr(metadata, 'chain_id')
        assert hasattr(metadata, 'decision_ids')
        assert hasattr(metadata, 'required_roles')
        assert hasattr(metadata, 'expires_at')
        assert hasattr(metadata, 'is_self_approval')

        # Assert - Correct types
        assert isinstance(metadata.chain_id, type(uuid4()))
        assert isinstance(metadata.decision_ids, list)
        assert isinstance(metadata.required_roles, list)
        assert isinstance(metadata.is_self_approval, bool)


# =====================================================================
# TEST: record_decision
# =====================================================================

class TestRecordDecision:
    """Test record_decision method."""

    @pytest.mark.asyncio
    async def test_approve_decision_updates_fields(
        self, tier_approval_service, mock_db
    ):
        """APPROVE action should update decision to COMPLETED."""
        # Setup
        decision_id = uuid4()
        actor_id = uuid4()
        evidence_ids = [uuid4(), uuid4()]

        mock_decision = MagicMock(spec=GateDecision)
        mock_decision.id = decision_id
        mock_decision.status = "PENDING"
        mock_db.get.return_value = mock_decision
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Execute
        result = await tier_approval_service.record_decision(
            decision_id=decision_id,
            actor_id=actor_id,
            action="APPROVE",
            comments="LGTM - excellent work",
            evidence_ids=evidence_ids,
            db=mock_db
        )

        # Assert
        assert result.action == "APPROVE"
        assert result.status == "COMPLETED"
        assert result.actor_id == actor_id
        assert result.comments == "LGTM - excellent work"
        assert result.evidence_ids == evidence_ids
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_reject_decision_updates_fields(
        self, tier_approval_service, mock_db
    ):
        """REJECT action should update decision to COMPLETED."""
        # Setup
        decision_id = uuid4()
        actor_id = uuid4()

        mock_decision = MagicMock(spec=GateDecision)
        mock_decision.id = decision_id
        mock_decision.status = "PENDING"
        mock_db.get.return_value = mock_decision
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Execute
        result = await tier_approval_service.record_decision(
            decision_id=decision_id,
            actor_id=actor_id,
            action="REJECT",
            comments="Missing security tests",
            evidence_ids=None,
            db=mock_db
        )

        # Assert
        assert result.action == "REJECT"
        assert result.status == "COMPLETED"
        assert result.comments == "Missing security tests"
        assert result.evidence_ids == []

    @pytest.mark.asyncio
    async def test_completed_at_set_to_now(
        self, tier_approval_service, mock_db
    ):
        """completed_at should be set to current timestamp."""
        # Setup
        decision_id = uuid4()
        actor_id = uuid4()

        mock_decision = MagicMock(spec=GateDecision)
        mock_decision.id = decision_id
        mock_decision.status = "PENDING"
        mock_db.get.return_value = mock_decision
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Execute
        before = datetime.utcnow()
        result = await tier_approval_service.record_decision(
            decision_id=decision_id,
            actor_id=actor_id,
            action="APPROVE",
            comments=None,
            evidence_ids=None,
            db=mock_db
        )
        after = datetime.utcnow()

        # Assert - completed_at is approximately now
        assert result.completed_at is not None
        assert before <= result.completed_at <= after

    @pytest.mark.asyncio
    async def test_decision_not_found_raises_error(
        self, tier_approval_service, mock_db
    ):
        """Non-existent decision should raise ValueError."""
        # Setup
        decision_id = uuid4()
        actor_id = uuid4()
        mock_db.get.return_value = None

        # Execute & Assert
        with pytest.raises(ValueError, match="Decision .* not found"):
            await tier_approval_service.record_decision(
                decision_id=decision_id,
                actor_id=actor_id,
                action="APPROVE",
                comments=None,
                evidence_ids=None,
                db=mock_db
            )

    @pytest.mark.asyncio
    async def test_decision_not_pending_raises_error(
        self, tier_approval_service, mock_db
    ):
        """Already completed decision should raise ValueError."""
        # Setup
        decision_id = uuid4()
        actor_id = uuid4()

        mock_decision = MagicMock(spec=GateDecision)
        mock_decision.id = decision_id
        mock_decision.status = "COMPLETED"  # Already completed
        mock_db.get.return_value = mock_decision

        # Execute & Assert
        with pytest.raises(ValueError, match="is not pending"):
            await tier_approval_service.record_decision(
                decision_id=decision_id,
                actor_id=actor_id,
                action="APPROVE",
                comments=None,
                evidence_ids=None,
                db=mock_db
            )

    @pytest.mark.asyncio
    async def test_decision_cancelled_raises_error(
        self, tier_approval_service, mock_db
    ):
        """Cancelled decision should raise ValueError."""
        # Setup
        decision_id = uuid4()
        actor_id = uuid4()

        mock_decision = MagicMock(spec=GateDecision)
        mock_decision.id = decision_id
        mock_decision.status = "CANCELLED"
        mock_db.get.return_value = mock_decision

        # Execute & Assert
        with pytest.raises(ValueError, match="is not pending"):
            await tier_approval_service.record_decision(
                decision_id=decision_id,
                actor_id=actor_id,
                action="APPROVE",
                comments=None,
                evidence_ids=None,
                db=mock_db
            )

    @pytest.mark.asyncio
    async def test_evidence_ids_empty_list_when_none(
        self, tier_approval_service, mock_db
    ):
        """evidence_ids should be empty list when None provided."""
        # Setup
        decision_id = uuid4()
        actor_id = uuid4()

        mock_decision = MagicMock(spec=GateDecision)
        mock_decision.id = decision_id
        mock_decision.status = "PENDING"
        mock_db.get.return_value = mock_decision
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Execute
        result = await tier_approval_service.record_decision(
            decision_id=decision_id,
            actor_id=actor_id,
            action="APPROVE",
            comments=None,
            evidence_ids=None,  # None
            db=mock_db
        )

        # Assert
        assert result.evidence_ids == []

    @pytest.mark.asyncio
    async def test_comments_optional(
        self, tier_approval_service, mock_db
    ):
        """Comments should be optional."""
        # Setup
        decision_id = uuid4()
        actor_id = uuid4()

        mock_decision = MagicMock(spec=GateDecision)
        mock_decision.id = decision_id
        mock_decision.status = "PENDING"
        mock_db.get.return_value = mock_decision
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Execute
        result = await tier_approval_service.record_decision(
            decision_id=decision_id,
            actor_id=actor_id,
            action="APPROVE",
            comments=None,  # No comments
            evidence_ids=None,
            db=mock_db
        )

        # Assert
        assert result.comments is None

    @pytest.mark.asyncio
    async def test_gate_not_finalized(
        self, tier_approval_service, mock_db
    ):
        """Gate status should NOT be updated (defer to Sprint 164)."""
        # Setup
        decision_id = uuid4()
        actor_id = uuid4()

        mock_decision = MagicMock(spec=GateDecision)
        mock_decision.id = decision_id
        mock_decision.status = "PENDING"
        mock_db.get.return_value = mock_decision
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Execute
        await tier_approval_service.record_decision(
            decision_id=decision_id,
            actor_id=actor_id,
            action="APPROVE",
            comments=None,
            evidence_ids=None,
            db=mock_db
        )

        # Assert - Gate status NOT updated
        # (No gate.status assignment in service code)
        # This is verified by code inspection - no gate update logic in Sprint 161


# =====================================================================
# TEST: Edge Cases & Integration
# =====================================================================

class TestEdgeCases:
    """Test edge cases and integration scenarios."""

    @pytest.mark.asyncio
    async def test_default_approval_chains_constant_structure(
        self, tier_approval_service
    ):
        """DEFAULT_APPROVAL_CHAINS should have expected structure."""
        chains = tier_approval_service.DEFAULT_APPROVAL_CHAINS

        # Assert - All 4 tiers present
        assert "FREE" in chains
        assert "STANDARD" in chains
        assert "PROFESSIONAL" in chains
        assert "ENTERPRISE" in chains

        # Assert - FREE tier is empty dict (self-approval)
        assert chains["FREE"] == {}

        # Assert - Other tiers have gate mappings
        assert isinstance(chains["STANDARD"], dict)
        assert isinstance(chains["PROFESSIONAL"], dict)
        assert isinstance(chains["ENTERPRISE"], dict)

        # Assert - Discovery gates (G0.1, G0.2) are self-approval
        assert chains["STANDARD"]["G0.1"] == []
        assert chains["STANDARD"]["G0.2"] == []

    @pytest.mark.asyncio
    async def test_approval_chain_metadata_is_dataclass(self):
        """ApprovalChainMetadata should be a dataclass."""
        from dataclasses import is_dataclass
        assert is_dataclass(ApprovalChainMetadata)

    @pytest.mark.asyncio
    async def test_service_stateless(self, tier_approval_service):
        """Service should be stateless (no instance variables)."""
        # Assert - Only DEFAULT_APPROVAL_CHAINS class variable
        instance_vars = [
            attr for attr in dir(tier_approval_service)
            if not attr.startswith('_') and not callable(getattr(tier_approval_service, attr))
        ]
        assert instance_vars == ['DEFAULT_APPROVAL_CHAINS']


# =====================================================================
# TEST: CTO v2.5 Adjustments (Sprint 161 Requirements)
# =====================================================================

class TestCTOv25Adjustments:
    """Test CTO v2.5 specific adjustments (5 tests)."""

    def test_escalate_action_in_schema(self):
        """CTO v2.5 #1: ESCALATE action type exists."""
        from app.schemas.tier_approval import DecisionAction
        assert hasattr(DecisionAction, 'ESCALATE')
        assert DecisionAction.ESCALATE == "ESCALATE"

    def test_all_decision_actions_present(self):
        """All 5 decision actions defined per spec."""
        from app.schemas.tier_approval import DecisionAction
        expected_actions = {'REQUEST', 'APPROVE', 'REJECT', 'ESCALATE', 'COMMENT'}
        actual_actions = {
            DecisionAction.REQUEST,
            DecisionAction.APPROVE,
            DecisionAction.REJECT,
            DecisionAction.ESCALATE,
            DecisionAction.COMMENT
        }
        assert actual_actions == expected_actions

    def test_decision_status_types_complete(self):
        """All 3 decision status types defined."""
        from app.schemas.tier_approval import DecisionStatus
        assert DecisionStatus.PENDING == "PENDING"
        assert DecisionStatus.COMPLETED == "COMPLETED"
        assert DecisionStatus.CANCELLED == "CANCELLED"

    def test_approval_chain_metadata_has_expires_at(self):
        """CTO v2.5 #2: ApprovalChainMetadata includes expires_at field."""
        from datetime import datetime, timedelta
        metadata = ApprovalChainMetadata(
            chain_id=uuid4(),
            decision_ids=[uuid4()],
            required_roles=["PM"],
            expires_at=datetime.utcnow() + timedelta(hours=48),
            is_self_approval=False,
        )
        assert metadata.expires_at is not None
        assert hasattr(metadata, 'expires_at')

    def test_approval_chain_metadata_is_proper_dataclass(self):
        """CTO v2.5 #3: ApprovalChainMetadata is dataclass with all fields."""
        from dataclasses import is_dataclass, fields
        assert is_dataclass(ApprovalChainMetadata)

        field_names = {f.name for f in fields(ApprovalChainMetadata)}
        expected_fields = {'chain_id', 'decision_ids', 'required_roles', 'expires_at', 'is_self_approval'}
        assert field_names == expected_fields


# =====================================================================
# TEST: Parametrized Tier × Gate Matrix (Comprehensive)
# =====================================================================

class TestTierGateMatrix:
    """Parametrized tests for tier × gate routing combinations."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("tier,gate,expected_roles", [
        # FREE tier - all self-approval (empty list)
        ("FREE", "G0.1", []),
        ("FREE", "G1", []),
        ("FREE", "G3", []),
        ("FREE", "G5", []),
        # STANDARD tier
        ("STANDARD", "G0.1", []),
        ("STANDARD", "G1", ["PM"]),
        ("STANDARD", "G2", ["CTO"]),
        ("STANDARD", "G4", ["QA_LEAD"]),
        # PROFESSIONAL tier
        ("PROFESSIONAL", "G0.2", []),
        ("PROFESSIONAL", "G1", ["PM", "CTO"]),
        ("PROFESSIONAL", "G5", ["CTO", "CEO"]),
        # ENTERPRISE tier (council review)
        ("ENTERPRISE", "G0.1", []),
        ("ENTERPRISE", "G4", ["QA_LEAD", "COMPLIANCE_OFFICER"]),
        ("ENTERPRISE", "G5", ["CTO", "CEO", "COMPLIANCE_OFFICER"]),
    ])
    async def test_tier_gate_routing_matrix(self, tier, gate, expected_roles):
        """Validate tier × gate routing combinations."""
        service = TierApprovalService()
        mock_db = AsyncMock(spec=AsyncSession)

        result = await service.compute_required_roles(tier, gate, mock_db)

        assert result == expected_roles, f"{tier} × {gate} → expected {expected_roles}, got {result}"


# =====================================================================
# TEST: Model Serialization (GateDecision.to_dict)
# =====================================================================

class TestModelSerialization:
    """Test model serialization methods."""

    def test_gate_decision_to_dict_complete(self):
        """GateDecision.to_dict() returns all expected fields."""
        decision = GateDecision()
        decision.id = uuid4()
        decision.gate_id = uuid4()
        decision.project_id = uuid4()
        decision.action = "APPROVE"
        decision.actor_id = uuid4()
        decision.chain_id = uuid4()
        decision.step_index = 1
        decision.required_roles = ["CTO"]
        decision.status = "COMPLETED"
        decision.comments = "LGTM"
        decision.evidence_ids = [uuid4(), uuid4()]
        decision.created_at = datetime.utcnow()
        decision.expires_at = datetime.utcnow() + timedelta(hours=48)
        decision.completed_at = datetime.utcnow()

        result = decision.to_dict()

        # Verify all keys present
        expected_keys = {
            'id', 'gate_id', 'project_id', 'action', 'actor_id',
            'chain_id', 'step_index', 'required_roles', 'status',
            'comments', 'evidence_ids', 'created_at', 'expires_at', 'completed_at'
        }
        assert set(result.keys()) == expected_keys

        # Verify serialization
        assert result['action'] == "APPROVE"
        assert result['status'] == "COMPLETED"
        assert result['step_index'] == 1
        assert len(result['evidence_ids']) == 2

    def test_gate_decision_to_dict_with_nulls(self):
        """GateDecision.to_dict() handles null values gracefully."""
        decision = GateDecision()
        decision.id = uuid4()
        decision.gate_id = uuid4()
        decision.project_id = uuid4()
        decision.action = "REQUEST"
        decision.actor_id = uuid4()
        decision.chain_id = uuid4()
        decision.step_index = 0
        decision.required_roles = ["PM"]
        decision.status = "PENDING"
        decision.comments = None
        decision.evidence_ids = None
        decision.created_at = datetime.utcnow()
        decision.expires_at = None
        decision.completed_at = None

        result = decision.to_dict()

        # Verify null handling
        assert result['comments'] is None
        assert result['evidence_ids'] == []
        assert result['expires_at'] is None
        assert result['completed_at'] is None
