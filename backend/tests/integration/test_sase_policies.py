"""
=========================================================================
Integration Tests for SASE Sprint Policies (OPA)
SDLC Orchestrator - Sprint 76 Day 3

Version: 1.0.0
Date: January 18, 2026
Status: ACTIVE - Sprint 76 Implementation
Authority: Backend Lead + CTO Approved
Framework: SDLC 5.1.3 P5 (SASE Integration)
Reference: SPRINT-76-SASE-WORKFLOW-INTEGRATION.md

Purpose:
- Test OPA sprint policy evaluation
- Verify deployment authorization with gate checks
- Test team membership requirements
- Verify SE4H Coach gate approval restrictions

Test Coverage (8 tests):
1. test_deploy_staging_g_sprint_passed - Staging allowed with gate
2. test_deploy_staging_g_sprint_pending - Staging blocked without gate
3. test_deploy_staging_non_member - Non-member blocked
4. test_deploy_production_both_gates - Production requires both
5. test_deploy_production_missing_gate - Production blocked
6. test_deploy_production_non_admin - Non-admin blocked
7. test_code_review_team_member - Team member allowed
8. test_gate_approval_coach_only - Only coach can approve

Zero Mock Policy: Uses real OPA service for policy evaluation
=========================================================================
"""

import pytest
from typing import Any
from uuid import uuid4

from app.services.opa_service import OPAService
from app.schemas.sase import (
    SprintContext,
    TeamMemberContext,
    GateStatusContext,
)


# ==================== Test Data Builders ====================

def build_team_member(
    user_id: str = None,
    role: str = "member",
    can_approve_gates: bool = False,
    can_manage_backlog: bool = True,
) -> dict:
    """Build a team member context for testing."""
    return {
        "user_id": user_id or str(uuid4()),
        "role": role,
        "can_approve_gates": can_approve_gates,
        "can_manage_backlog": can_manage_backlog,
    }


def build_sprint_context(
    g_sprint: str = "pending",
    g_sprint_close: str = "pending",
    status: str = "planning",
    team_members: list = None,
) -> dict:
    """Build a sprint context for testing."""
    if team_members is None:
        team_members = [
            build_team_member(user_id="member-123", role="member"),
            build_team_member(user_id="owner-456", role="owner", can_approve_gates=True),
            build_team_member(user_id="admin-789", role="admin", can_approve_gates=True),
        ]

    return {
        "sprint_id": str(uuid4()),
        "sprint_number": 76,
        "sprint_name": "Test Sprint",
        "project_id": str(uuid4()),
        "project_name": "Test Project",
        "team_id": str(uuid4()),
        "team_name": "Test Team",
        "team_members": team_members,
        "gates": {
            "g_sprint": g_sprint,
            "g_sprint_close": g_sprint_close,
        },
        "status": status,
    }


def build_policy_input(
    action: str = "deploy_staging",
    requester_id: str = "member-123",
    sprint_context: dict = None,
    environment: str = None,
) -> dict:
    """Build OPA policy input for testing."""
    data = {
        "action": action,
        "requester_id": requester_id,
        "sprint_context": sprint_context or build_sprint_context(),
    }
    if environment:
        data["environment"] = environment
    return data


# ==================== Fixtures ====================

@pytest.fixture
def opa_service():
    """Create OPA service instance."""
    return OPAService()


@pytest.fixture
def pending_sprint_context() -> dict:
    """Sprint context with pending gates."""
    return build_sprint_context(
        g_sprint="pending",
        g_sprint_close="pending",
        status="planning",
    )


@pytest.fixture
def active_sprint_context() -> dict:
    """Sprint context with G-Sprint passed (active sprint)."""
    return build_sprint_context(
        g_sprint="passed",
        g_sprint_close="pending",
        status="active",
    )


@pytest.fixture
def completed_sprint_context() -> dict:
    """Sprint context with both gates passed (completed sprint)."""
    return build_sprint_context(
        g_sprint="passed",
        g_sprint_close="passed",
        status="completed",
    )


# ==================== Test Cases ====================

@pytest.mark.asyncio
class TestSASESprintPolicies:
    """Test OPA sprint policy evaluation."""

    # ==================== Staging Deployment Tests ====================

    async def test_deploy_staging_g_sprint_passed(
        self,
        opa_service: OPAService,
        active_sprint_context: dict,
    ):
        """
        Test 1: Staging deployment allowed when G-Sprint passed.

        SDLC 5.1.3 Rule #3: Sprint must be approved before execution.
        """
        policy_input = build_policy_input(
            action="deploy_staging",
            requester_id="member-123",
            sprint_context=active_sprint_context,
        )

        result = await opa_service.evaluate(
            policy="sdlc.sprint",
            input_data=policy_input,
            query="data.sdlc.sprint.deploy_allowed",
        )

        assert result["result"] is True

    async def test_deploy_staging_g_sprint_pending(
        self,
        opa_service: OPAService,
        pending_sprint_context: dict,
    ):
        """
        Test 2: Staging deployment blocked when G-Sprint pending.
        """
        policy_input = build_policy_input(
            action="deploy_staging",
            requester_id="member-123",
            sprint_context=pending_sprint_context,
        )

        result = await opa_service.evaluate(
            policy="sdlc.sprint",
            input_data=policy_input,
            query="data.sdlc.sprint.deploy_allowed",
        )

        assert result["result"] is False

    async def test_deploy_staging_non_member(
        self,
        opa_service: OPAService,
        active_sprint_context: dict,
    ):
        """
        Test 3: Non-member cannot deploy to staging.

        GAP 3: Team membership required for SASE authorization.
        """
        policy_input = build_policy_input(
            action="deploy_staging",
            requester_id="non-member-999",  # Not in team_members
            sprint_context=active_sprint_context,
        )

        result = await opa_service.evaluate(
            policy="sdlc.sprint",
            input_data=policy_input,
            query="data.sdlc.sprint.deploy_allowed",
        )

        assert result["result"] is False

    # ==================== Production Deployment Tests ====================

    async def test_deploy_production_both_gates_passed(
        self,
        opa_service: OPAService,
        completed_sprint_context: dict,
    ):
        """
        Test 4: Production deployment allowed when both gates passed.

        SDLC 5.1.3 Rules #2 and #3: Both gates required for production.
        """
        policy_input = build_policy_input(
            action="deploy_production",
            requester_id="owner-456",  # Admin/owner required for production
            sprint_context=completed_sprint_context,
        )

        result = await opa_service.evaluate(
            policy="sdlc.sprint",
            input_data=policy_input,
            query="data.sdlc.sprint.deploy_allowed",
        )

        assert result["result"] is True

    async def test_deploy_production_missing_gate(
        self,
        opa_service: OPAService,
        active_sprint_context: dict,
    ):
        """
        Test 5: Production deployment blocked when G-Sprint-Close pending.

        SDLC 5.1.3 Rule #2: Post-sprint documentation required.
        """
        policy_input = build_policy_input(
            action="deploy_production",
            requester_id="owner-456",
            sprint_context=active_sprint_context,  # g_sprint_close is pending
        )

        result = await opa_service.evaluate(
            policy="sdlc.sprint",
            input_data=policy_input,
            query="data.sdlc.sprint.deploy_allowed",
        )

        assert result["result"] is False

    async def test_deploy_production_non_admin(
        self,
        opa_service: OPAService,
        completed_sprint_context: dict,
    ):
        """
        Test 6: Non-admin member cannot deploy to production.

        Production deployments require owner/admin role.
        """
        policy_input = build_policy_input(
            action="deploy_production",
            requester_id="member-123",  # Regular member, not admin
            sprint_context=completed_sprint_context,
        )

        result = await opa_service.evaluate(
            policy="sdlc.sprint",
            input_data=policy_input,
            query="data.sdlc.sprint.deploy_allowed",
        )

        assert result["result"] is False

    # ==================== Code Review Tests ====================

    async def test_code_review_team_member(
        self,
        opa_service: OPAService,
        active_sprint_context: dict,
    ):
        """
        Test 7: Team member can perform code review.
        """
        policy_input = build_policy_input(
            action="code_review",
            requester_id="member-123",
            sprint_context=active_sprint_context,
        )

        result = await opa_service.evaluate(
            policy="sdlc.sprint",
            input_data=policy_input,
            query="data.sdlc.sprint.code_review_allowed",
        )

        assert result["result"] is True

    # ==================== Gate Approval Tests ====================

    async def test_gate_approval_coach_only(
        self,
        opa_service: OPAService,
        pending_sprint_context: dict,
    ):
        """
        Test 8: Only SE4H Coach (owner/admin) can approve gates.

        SDLC 5.1.3: Human owner/admin required for gate approval.
        """
        # Owner can approve
        owner_input = build_policy_input(
            action="approve_gate",
            requester_id="owner-456",
            sprint_context=pending_sprint_context,
        )

        owner_result = await opa_service.evaluate(
            policy="sdlc.sprint",
            input_data=owner_input,
            query="data.sdlc.sprint.gate_approval_allowed",
        )
        assert owner_result["result"] is True

        # Regular member cannot approve
        member_input = build_policy_input(
            action="approve_gate",
            requester_id="member-123",
            sprint_context=pending_sprint_context,
        )

        member_result = await opa_service.evaluate(
            policy="sdlc.sprint",
            input_data=member_input,
            query="data.sdlc.sprint.gate_approval_allowed",
        )
        assert member_result["result"] is False


@pytest.mark.asyncio
class TestSASESprintPolicyDenialReasons:
    """Test denial reason messages from OPA policies."""

    async def test_denial_reason_no_sprint_context(
        self,
        opa_service: OPAService,
    ):
        """Test denial reason when no sprint context provided."""
        policy_input = {
            "action": "deploy_staging",
            "requester_id": "member-123",
            "sprint_context": None,
        }

        result = await opa_service.evaluate(
            policy="sdlc.sprint",
            input_data=policy_input,
            query="data.sdlc.sprint.denial_reason",
        )

        assert "No sprint context" in result["result"]

    async def test_denial_reason_g_sprint_pending(
        self,
        opa_service: OPAService,
        pending_sprint_context: dict,
    ):
        """Test denial reason for pending G-Sprint gate."""
        policy_input = build_policy_input(
            action="deploy_staging",
            requester_id="member-123",
            sprint_context=pending_sprint_context,
        )

        result = await opa_service.evaluate(
            policy="sdlc.sprint",
            input_data=policy_input,
            query="data.sdlc.sprint.denial_reason",
        )

        assert "G-Sprint" in result["result"]
        assert "Rule #3" in result["result"]

    async def test_denial_reason_non_member(
        self,
        opa_service: OPAService,
        active_sprint_context: dict,
    ):
        """Test denial reason for non-team-member."""
        policy_input = build_policy_input(
            action="deploy_staging",
            requester_id="non-member-999",
            sprint_context=active_sprint_context,
        )

        result = await opa_service.evaluate(
            policy="sdlc.sprint",
            input_data=policy_input,
            query="data.sdlc.sprint.denial_reason",
        )

        assert "not a member" in result["result"]

    async def test_denial_reason_coach_required(
        self,
        opa_service: OPAService,
        pending_sprint_context: dict,
    ):
        """Test denial reason for gate approval by non-coach."""
        policy_input = build_policy_input(
            action="approve_gate",
            requester_id="member-123",  # Has can_approve_gates=false
            sprint_context=pending_sprint_context,
        )

        result = await opa_service.evaluate(
            policy="sdlc.sprint",
            input_data=policy_input,
            query="data.sdlc.sprint.denial_reason",
        )

        assert "SE4H Coach" in result["result"]


@pytest.mark.asyncio
class TestSASESprintPolicyResponse:
    """Test full response structure from OPA policies."""

    async def test_response_structure_allowed(
        self,
        opa_service: OPAService,
        active_sprint_context: dict,
    ):
        """Test response structure for allowed action."""
        policy_input = build_policy_input(
            action="deploy_staging",
            requester_id="member-123",
            sprint_context=active_sprint_context,
        )

        result = await opa_service.evaluate(
            policy="sdlc.sprint",
            input_data=policy_input,
            query="data.sdlc.sprint.response",
        )

        response = result["result"]
        assert response["allowed"] is True
        assert response["policy"] == "sdlc.sprint"
        assert response["is_team_member"] is True
        assert "checked_gates" in response
        assert response["checked_gates"]["g_sprint"] == "passed"

    async def test_response_structure_denied(
        self,
        opa_service: OPAService,
        pending_sprint_context: dict,
    ):
        """Test response structure for denied action."""
        policy_input = build_policy_input(
            action="deploy_staging",
            requester_id="member-123",
            sprint_context=pending_sprint_context,
        )

        result = await opa_service.evaluate(
            policy="sdlc.sprint",
            input_data=policy_input,
            query="data.sdlc.sprint.response",
        )

        response = result["result"]
        assert response["allowed"] is False
        assert response["policy"] == "sdlc.sprint"
        assert "G-Sprint" in response["reason"]
