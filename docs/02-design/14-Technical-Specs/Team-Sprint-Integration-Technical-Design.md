# Sprint 76 Technical Design Document

**Document ID:** TDS-076
**Version:** 1.0.0
**Date:** January 18, 2026
**Status:** DESIGN - Ready for Implementation
**Author:** AI Council + Backend Lead
**Reviewer:** CTO
**Framework:** SDLC 6.1.0 P5 (SASE Integration)

---

## Executive Summary

Sprint 76 focuses on resolving remaining team-sprint integration gaps (GAP 2, GAP 3) and establishing the foundation for AI-powered sprint assistance. This document provides detailed technical specifications for all 5 days of implementation.

---

## Table of Contents

1. [Day 1: Backlog Assignee Validation (GAP 2)](#day-1-backlog-assignee-validation-gap-2)
2. [Day 2: SASE Sprint Context (GAP 3)](#day-2-sase-sprint-context-gap-3)
3. [Day 3: SASE Policy Updates](#day-3-sase-policy-updates)
4. [Day 4: AI Sprint Assistant Foundation](#day-4-ai-sprint-assistant-foundation)
5. [Day 5: Sprint Analytics Dashboard](#day-5-sprint-analytics-dashboard)
6. [Database Schema Changes](#database-schema-changes)
7. [API Contract](#api-contract)
8. [Test Strategy](#test-strategy)

---

## Day 1: Backlog Assignee Validation (GAP 2)

### Problem Statement

Currently, backlog items can be assigned to any user in the system, regardless of whether they are members of the project's team. This violates the SDLC 6.1.0 team governance principle that only team members should work on project items.

### Solution Design

#### 1.1 New Service Method: `validate_assignee_membership()`

**File:** `backend/app/services/backlog_service.py` (NEW)

```python
"""
=========================================================================
Backlog Service - Backlog Item Management with Team Validation
SDLC Orchestrator - Sprint 76 (GAP 2 Resolution)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE
Authority: Backend Lead + CTO Approved
Reference: SPRINT-76-SASE-WORKFLOW-INTEGRATION.md
=========================================================================
"""

from uuid import UUID
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.backlog_item import BacklogItem
from app.models.project import Project
from app.models.sprint import Sprint
from app.models.team import Team
from app.models.team_member import TeamMember


class BacklogServiceError(Exception):
    """Base exception for BacklogService."""
    pass


class AssigneeNotTeamMemberError(BacklogServiceError):
    """Assignee is not a member of the project team."""
    def __init__(self, user_id: UUID, team_id: UUID, project_name: str):
        self.user_id = user_id
        self.team_id = team_id
        super().__init__(
            f"User {user_id} is not a member of team for project '{project_name}'. "
            f"Only team members can be assigned to backlog items."
        )


class BacklogService:
    """
    Service for backlog item operations with team validation.

    GAP 2 Resolution:
    - Validates assignees are team members before assignment
    - Supports legacy projects without teams (allows any assignee)
    - Integrates with SASE role validation
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_assignee_membership(
        self,
        project_id: UUID,
        assignee_id: Optional[UUID],
    ) -> bool:
        """
        Validate that assignee is a member of the project's team.

        GAP 2 Resolution: Ensures backlog items can only be assigned
        to users who are active members of the project team.

        Args:
            project_id: Project UUID
            assignee_id: User UUID to validate (None = unassigned, always valid)

        Returns:
            True if assignee is valid (team member or no team assigned)

        Raises:
            AssigneeNotTeamMemberError: If assignee is not a team member
        """
        # No assignee = always valid
        if assignee_id is None:
            return True

        # Get project with team relation
        project_result = await self.db.execute(
            select(Project)
            .options(selectinload(Project.team).selectinload(Team.members))
            .where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()

        if not project:
            raise ValueError(f"Project {project_id} not found")

        # No team assigned = allow any assignee (legacy behavior)
        if not project.team:
            return True

        # Check if assignee is a team member
        is_member = any(
            member.user_id == assignee_id and member.deleted_at is None
            for member in project.team.members
        )

        if not is_member:
            raise AssigneeNotTeamMemberError(
                user_id=assignee_id,
                team_id=project.team.id,
                project_name=project.name,
            )

        return True

    async def get_assignable_users(
        self,
        project_id: UUID,
    ) -> List[dict]:
        """
        Get list of users who can be assigned to backlog items.

        Returns team members if project has a team, otherwise empty list
        (frontend should show user search for legacy projects).

        Args:
            project_id: Project UUID

        Returns:
            List of assignable user dicts with id, name, email, role
        """
        project_result = await self.db.execute(
            select(Project)
            .options(
                selectinload(Project.team)
                .selectinload(Team.members)
                .selectinload(TeamMember.user)
            )
            .where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()

        if not project or not project.team:
            return []

        assignable_users = []
        for member in project.team.members:
            if member.deleted_at is None and member.user:
                assignable_users.append({
                    "id": str(member.user_id),
                    "full_name": member.user.full_name,
                    "email": member.user.email,
                    "role": member.role,
                    "can_assign_backlog": member.can_assign_backlog,
                })

        return assignable_users
```

#### 1.2 Planning Routes Updates

**File:** `backend/app/api/routes/planning.py` (MODIFY)

Update `create_backlog_item()` and `update_backlog_item()`:

```python
# Add import
from app.services.backlog_service import BacklogService, AssigneeNotTeamMemberError

# Modify create_backlog_item endpoint (around line 1260)
@router.post("/backlog", response_model=BacklogItemResponse, status_code=status.HTTP_201_CREATED)
async def create_backlog_item(
    data: BacklogItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new backlog item."""
    await check_project_access(db, data.project_id, current_user, require_write=True)

    # GAP 2: Validate assignee is team member
    if data.assignee_id:
        backlog_service = BacklogService(db)
        try:
            await backlog_service.validate_assignee_membership(
                project_id=data.project_id,
                assignee_id=data.assignee_id,
            )
        except AssigneeNotTeamMemberError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    # ... rest of existing code


# Modify update_backlog_item endpoint (around line 1437)
@router.put("/backlog/{item_id}", response_model=BacklogItemResponse)
async def update_backlog_item(
    item_id: UUID,
    data: BacklogItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a backlog item."""
    # ... existing code to get item

    # GAP 2: Validate new assignee is team member
    if data.assignee_id is not None:
        backlog_service = BacklogService(db)
        try:
            await backlog_service.validate_assignee_membership(
                project_id=item.project_id,
                assignee_id=data.assignee_id,
            )
        except AssigneeNotTeamMemberError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        item.assignee_id = data.assignee_id

    # ... rest of existing code


# New endpoint: Get assignable users
@router.get("/projects/{project_id}/assignable-users")
async def get_assignable_users(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get list of users who can be assigned to backlog items.

    Returns team members for projects with teams.
    """
    await check_project_access(db, project_id, current_user)

    backlog_service = BacklogService(db)
    users = await backlog_service.get_assignable_users(project_id)

    return {
        "project_id": str(project_id),
        "assignable_users": users,
        "total": len(users),
    }
```

#### 1.3 Frontend: Assignee Dropdown Update

**File:** `frontend/web/src/hooks/usePlanning.ts` (MODIFY)

Add hook for assignable users:

```typescript
// Add to usePlanning.ts

/** Assignable user type */
export interface AssignableUser {
  id: string;
  full_name: string;
  email: string;
  role: string;
  can_assign_backlog: boolean;
}

/** Get assignable users for a project */
export function useAssignableUsers(projectId: string | null) {
  return useQuery({
    queryKey: planningKeys.assignableUsers(projectId!),
    queryFn: async () => {
      const response = await apiClient.get(
        `/planning/projects/${projectId}/assignable-users`
      );
      return response.data as {
        project_id: string;
        assignable_users: AssignableUser[];
        total: number;
      };
    },
    enabled: !!projectId,
  });
}

// Add to planningKeys
export const planningKeys = {
  // ... existing keys
  assignableUsers: (projectId: string) =>
    [...planningKeys.all, "assignable-users", projectId] as const,
};
```

#### 1.4 Test Cases (12 tests)

**File:** `backend/tests/integration/test_backlog_assignee.py` (NEW)

```python
"""
Integration tests for Backlog Assignee Validation (GAP 2)
Sprint 76 Day 1

Tests:
1. Create item with team member assignee - SUCCESS
2. Create item with non-team-member assignee - FAIL
3. Create item with no assignee - SUCCESS
4. Update item assignee to team member - SUCCESS
5. Update item assignee to non-member - FAIL
6. Legacy project (no team) - any assignee allowed
7. Get assignable users for team project
8. Get assignable users for legacy project (empty)
9. Validate owner can be assigned
10. Validate admin can be assigned
11. Validate member can be assigned
12. AI agent cannot be assigned (member_type check)
"""

import pytest
from uuid import uuid4

@pytest.mark.asyncio
class TestBacklogAssigneeValidation:

    async def test_create_item_team_member_success(
        self, client, auth_headers, team_project, team_member
    ):
        """Team member can be assigned to backlog item."""
        response = await client.post(
            "/api/v1/planning/backlog",
            json={
                "project_id": str(team_project.id),
                "type": "task",
                "title": "Test task",
                "priority": "P1",
                "assignee_id": str(team_member.user_id),
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["assignee_id"] == str(team_member.user_id)

    async def test_create_item_non_member_fail(
        self, client, auth_headers, team_project, non_member_user
    ):
        """Non-team-member cannot be assigned to backlog item."""
        response = await client.post(
            "/api/v1/planning/backlog",
            json={
                "project_id": str(team_project.id),
                "type": "task",
                "title": "Test task",
                "priority": "P1",
                "assignee_id": str(non_member_user.id),
            },
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "not a member" in response.json()["detail"]

    async def test_create_item_no_assignee_success(
        self, client, auth_headers, team_project
    ):
        """Item without assignee is always valid."""
        response = await client.post(
            "/api/v1/planning/backlog",
            json={
                "project_id": str(team_project.id),
                "type": "task",
                "title": "Unassigned task",
                "priority": "P2",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["assignee_id"] is None

    async def test_update_assignee_to_member_success(
        self, client, auth_headers, backlog_item, team_member
    ):
        """Can update assignee to team member."""
        response = await client.put(
            f"/api/v1/planning/backlog/{backlog_item.id}",
            json={"assignee_id": str(team_member.user_id)},
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_update_assignee_to_non_member_fail(
        self, client, auth_headers, backlog_item, non_member_user
    ):
        """Cannot update assignee to non-member."""
        response = await client.put(
            f"/api/v1/planning/backlog/{backlog_item.id}",
            json={"assignee_id": str(non_member_user.id)},
            headers=auth_headers,
        )
        assert response.status_code == 400

    async def test_legacy_project_any_assignee(
        self, client, auth_headers, legacy_project, any_user
    ):
        """Legacy project without team allows any assignee."""
        response = await client.post(
            "/api/v1/planning/backlog",
            json={
                "project_id": str(legacy_project.id),
                "type": "task",
                "title": "Legacy task",
                "priority": "P1",
                "assignee_id": str(any_user.id),
            },
            headers=auth_headers,
        )
        assert response.status_code == 201

    async def test_get_assignable_users_team_project(
        self, client, auth_headers, team_project
    ):
        """Get assignable users returns team members."""
        response = await client.get(
            f"/api/v1/planning/projects/{team_project.id}/assignable-users",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["total"] > 0
        assert all("role" in u for u in response.json()["assignable_users"])

    async def test_get_assignable_users_legacy_project(
        self, client, auth_headers, legacy_project
    ):
        """Get assignable users returns empty for legacy project."""
        response = await client.get(
            f"/api/v1/planning/projects/{legacy_project.id}/assignable-users",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["total"] == 0
```

---

## Day 2: SASE Sprint Context (GAP 3)

### Problem Statement

SASE approval workflows currently operate without sprint context. When a deployment or code review is requested, the SASE policies cannot verify if the requester is a member of the sprint's team.

### Solution Design

#### 2.1 Sprint Context Schema

**File:** `backend/app/schemas/sase.py` (NEW)

```python
"""
SASE Integration Schemas - Sprint Context
Sprint 76 (GAP 3 Resolution)
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class TeamMemberContext(BaseModel):
    """Team member context for SASE policies."""
    user_id: UUID
    role: str  # owner, admin, member, ai_agent
    can_approve_gates: bool
    can_assign_backlog: bool


class PhaseContext(BaseModel):
    """Phase context for sprint."""
    id: UUID
    name: str
    number: int
    roadmap_id: UUID


class GateStatusContext(BaseModel):
    """Gate status for sprint."""
    g_sprint: str  # pending, passed, failed
    g_sprint_close: str


class SprintContext(BaseModel):
    """
    Sprint context for SASE policy evaluation.

    GAP 3 Resolution: Provides complete sprint context including
    team members, gate status, and phase information.
    """
    sprint_id: UUID
    sprint_number: int
    sprint_name: str
    project_id: UUID
    project_name: str
    team_id: Optional[UUID] = None
    team_name: Optional[str] = None
    team_members: List[TeamMemberContext] = []
    phase: Optional[PhaseContext] = None
    gates: GateStatusContext
    status: str  # planning, in_progress, completed, closed
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SASEApprovalRequest(BaseModel):
    """
    SASE approval request with sprint context.

    Updated for Sprint 76 GAP 3:
    - Added sprint_id for sprint-aware policy evaluation
    - team_context computed from sprint
    """
    resource_type: str  # deployment, code_review, release
    resource_id: UUID
    action: str  # deploy_staging, deploy_prod, approve_pr
    requester_id: UUID
    sprint_id: Optional[UUID] = None  # GAP 3: Sprint context

    # Computed from sprint context (populated by service)
    sprint_context: Optional[SprintContext] = None


class SASEApprovalResponse(BaseModel):
    """SASE approval response."""
    allowed: bool
    reason: str
    policy_name: str
    evaluated_at: datetime
    sprint_context_used: bool = False
```

#### 2.2 Sprint Context Provider Service

**File:** `backend/app/services/sase_sprint_integration.py` (NEW)

```python
"""
=========================================================================
SASE Sprint Integration - Sprint Context for SASE Workflows
SDLC Orchestrator - Sprint 76 (GAP 3 Resolution)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE
Authority: Backend Lead + CTO Approved
=========================================================================
"""

from uuid import UUID
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.phase import Phase
from app.models.project import Project
from app.models.roadmap import Roadmap
from app.models.sprint import Sprint
from app.models.team import Team
from app.models.team_member import TeamMember
from app.schemas.sase import (
    SprintContext,
    TeamMemberContext,
    PhaseContext,
    GateStatusContext,
)


class SprintContextProvider:
    """
    Provides sprint context to SASE approval workflows.

    GAP 3 Resolution: SASE policies can now access:
    - Sprint team members and roles
    - Sprint phase and roadmap context
    - Sprint gate status
    - Project information

    Usage:
        provider = SprintContextProvider(db)
        context = await provider.get_sprint_context(sprint_id)

        # Use in SASE policy evaluation
        opa_input = {
            "sprint_context": context.dict(),
            "requester_id": str(requester_id),
            "action": "deploy_staging",
        }
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_sprint_context(
        self,
        sprint_id: UUID,
    ) -> Optional[SprintContext]:
        """
        Get comprehensive sprint context for SASE policy evaluation.

        Loads:
        - Sprint details
        - Phase and roadmap info
        - Project with team members
        - Gate status

        Args:
            sprint_id: Sprint UUID

        Returns:
            SprintContext or None if sprint not found
        """
        result = await self.db.execute(
            select(Sprint)
            .options(
                selectinload(Sprint.phase).selectinload(Phase.roadmap),
                selectinload(Sprint.project)
                .selectinload(Project.team)
                .selectinload(Team.members)
                .selectinload(TeamMember.user),
            )
            .where(Sprint.id == sprint_id)
        )
        sprint = result.scalar_one_or_none()

        if not sprint:
            return None

        # Build team member context
        team_members = []
        if sprint.project.team:
            for member in sprint.project.team.members:
                if member.deleted_at is None:
                    team_members.append(
                        TeamMemberContext(
                            user_id=member.user_id,
                            role=member.role,
                            can_approve_gates=member.can_approve_sprint_gate,
                            can_assign_backlog=member.can_assign_backlog,
                        )
                    )

        # Build phase context
        phase_context = None
        if sprint.phase:
            phase_context = PhaseContext(
                id=sprint.phase.id,
                name=sprint.phase.name,
                number=sprint.phase.number,
                roadmap_id=sprint.phase.roadmap_id,
            )

        # Build gate status
        gates = GateStatusContext(
            g_sprint=sprint.g_sprint_status or "pending",
            g_sprint_close=sprint.g_sprint_close_status or "pending",
        )

        return SprintContext(
            sprint_id=sprint.id,
            sprint_number=sprint.number,
            sprint_name=sprint.name,
            project_id=sprint.project_id,
            project_name=sprint.project.name,
            team_id=sprint.project.team.id if sprint.project.team else None,
            team_name=sprint.project.team.name if sprint.project.team else None,
            team_members=team_members,
            phase=phase_context,
            gates=gates,
            status=sprint.status,
            start_date=sprint.start_date,
            end_date=sprint.end_date,
        )

    async def is_requester_in_sprint_team(
        self,
        sprint_id: UUID,
        requester_id: UUID,
    ) -> bool:
        """
        Check if requester is a member of the sprint's project team.

        Args:
            sprint_id: Sprint UUID
            requester_id: User UUID making the request

        Returns:
            True if requester is team member or project has no team
        """
        context = await self.get_sprint_context(sprint_id)

        if not context:
            return False

        # No team = allow (legacy behavior)
        if not context.team_id:
            return True

        return any(
            member.user_id == requester_id
            for member in context.team_members
        )

    async def can_requester_deploy(
        self,
        sprint_id: UUID,
        requester_id: UUID,
        environment: str = "staging",
    ) -> dict:
        """
        Check if requester can deploy from this sprint.

        Rules:
        - staging: G-Sprint must be approved, requester in team
        - production: G-Sprint and G-Sprint-Close must be approved

        Args:
            sprint_id: Sprint UUID
            requester_id: User UUID
            environment: staging or production

        Returns:
            dict with allowed, reason, context
        """
        context = await self.get_sprint_context(sprint_id)

        if not context:
            return {
                "allowed": False,
                "reason": "Sprint not found",
            }

        # Check team membership
        is_member = await self.is_requester_in_sprint_team(sprint_id, requester_id)
        if not is_member:
            return {
                "allowed": False,
                "reason": "Requester is not a member of the sprint team",
            }

        # Check gate status
        if environment == "staging":
            if context.gates.g_sprint != "passed":
                return {
                    "allowed": False,
                    "reason": "G-Sprint gate must be approved for staging deployment",
                }
        elif environment == "production":
            if context.gates.g_sprint != "passed":
                return {
                    "allowed": False,
                    "reason": "G-Sprint gate must be approved for production deployment",
                }
            if context.gates.g_sprint_close != "passed":
                return {
                    "allowed": False,
                    "reason": "G-Sprint-Close gate must be approved for production deployment",
                }

        return {
            "allowed": True,
            "reason": f"Deployment to {environment} allowed",
            "context": context.dict(),
        }
```

#### 2.3 Test Cases (10 tests)

**File:** `backend/tests/integration/test_sase_sprint.py` (NEW)

```python
"""
Integration tests for SASE Sprint Context (GAP 3)
Sprint 76 Day 2
"""

import pytest

@pytest.mark.asyncio
class TestSASESprintContext:

    async def test_get_sprint_context_success(self, sprint_context_provider, test_sprint):
        """Get sprint context with all relations."""
        context = await sprint_context_provider.get_sprint_context(test_sprint.id)

        assert context is not None
        assert context.sprint_id == test_sprint.id
        assert context.sprint_number == test_sprint.number
        assert context.project_id == test_sprint.project_id
        assert len(context.team_members) > 0

    async def test_get_sprint_context_not_found(self, sprint_context_provider):
        """Return None for non-existent sprint."""
        from uuid import uuid4
        context = await sprint_context_provider.get_sprint_context(uuid4())
        assert context is None

    async def test_is_requester_in_team_member(
        self, sprint_context_provider, test_sprint, team_member
    ):
        """Team member is recognized."""
        is_member = await sprint_context_provider.is_requester_in_sprint_team(
            test_sprint.id, team_member.user_id
        )
        assert is_member is True

    async def test_is_requester_in_team_non_member(
        self, sprint_context_provider, test_sprint, non_member_user
    ):
        """Non-member is not recognized."""
        is_member = await sprint_context_provider.is_requester_in_sprint_team(
            test_sprint.id, non_member_user.id
        )
        assert is_member is False

    async def test_deploy_staging_g_sprint_approved(
        self, sprint_context_provider, approved_sprint, team_member
    ):
        """Can deploy to staging if G-Sprint approved."""
        result = await sprint_context_provider.can_requester_deploy(
            approved_sprint.id, team_member.user_id, "staging"
        )
        assert result["allowed"] is True

    async def test_deploy_staging_g_sprint_pending(
        self, sprint_context_provider, pending_sprint, team_member
    ):
        """Cannot deploy to staging if G-Sprint pending."""
        result = await sprint_context_provider.can_requester_deploy(
            pending_sprint.id, team_member.user_id, "staging"
        )
        assert result["allowed"] is False
        assert "G-Sprint" in result["reason"]

    async def test_deploy_staging_non_member(
        self, sprint_context_provider, approved_sprint, non_member_user
    ):
        """Non-member cannot deploy."""
        result = await sprint_context_provider.can_requester_deploy(
            approved_sprint.id, non_member_user.id, "staging"
        )
        assert result["allowed"] is False
        assert "not a member" in result["reason"]

    async def test_deploy_production_requires_both_gates(
        self, sprint_context_provider, approved_sprint, team_member
    ):
        """Production deploy requires both gates."""
        result = await sprint_context_provider.can_requester_deploy(
            approved_sprint.id, team_member.user_id, "production"
        )
        # approved_sprint has g_sprint passed but g_sprint_close pending
        assert result["allowed"] is False
        assert "G-Sprint-Close" in result["reason"]

    async def test_deploy_production_both_gates_passed(
        self, sprint_context_provider, closed_sprint, team_member
    ):
        """Can deploy to production if both gates passed."""
        result = await sprint_context_provider.can_requester_deploy(
            closed_sprint.id, team_member.user_id, "production"
        )
        assert result["allowed"] is True

    async def test_legacy_project_no_team(
        self, sprint_context_provider, legacy_sprint, any_user
    ):
        """Legacy project without team allows any requester."""
        is_member = await sprint_context_provider.is_requester_in_sprint_team(
            legacy_sprint.id, any_user.id
        )
        assert is_member is True
```

---

## Day 3: SASE Policy Updates

### OPA Policies for Sprint Context

**File:** `policy-packs/rego/sprint_policies.rego` (NEW)

```rego
# Sprint-aware SASE Policies
# SDLC Orchestrator - Sprint 76
# Framework: SDLC 6.1.0 P5 (SASE Integration)

package sdlc.sprint

import future.keywords.if
import future.keywords.in

# Default deny
default deploy_allowed := false
default code_review_allowed := false

# Get team member IDs from sprint context
sprint_team_members := {m.user_id | m := input.sprint_context.team_members[_]}

# Deploy to staging requires:
# 1. G-Sprint gate approved
# 2. Requester is team member
deploy_allowed if {
    input.environment == "staging"
    input.sprint_context.gates.g_sprint == "passed"
    input.requester_id in sprint_team_members
}

# Deploy to production requires:
# 1. Both G-Sprint and G-Sprint-Close approved
# 2. Requester is team member with admin/owner role
deploy_allowed if {
    input.environment == "production"
    input.sprint_context.gates.g_sprint == "passed"
    input.sprint_context.gates.g_sprint_close == "passed"
    requester_can_deploy_prod
}

requester_can_deploy_prod if {
    some m in input.sprint_context.team_members
    m.user_id == input.requester_id
    m.role in {"owner", "admin"}
}

# Code review allowed for team members
code_review_allowed if {
    input.sprint_context != null
    input.requester_id in sprint_team_members
}

# Error messages
deploy_denied_reason := reason if {
    not deploy_allowed
    not input.sprint_context
    reason := "No sprint context provided"
} else := reason if {
    not deploy_allowed
    input.environment == "staging"
    input.sprint_context.gates.g_sprint != "passed"
    reason := "G-Sprint gate not approved"
} else := reason if {
    not deploy_allowed
    input.environment == "production"
    input.sprint_context.gates.g_sprint_close != "passed"
    reason := "G-Sprint-Close gate not approved for production"
} else := reason if {
    not deploy_allowed
    not (input.requester_id in sprint_team_members)
    reason := "Requester is not a sprint team member"
} else := reason if {
    not deploy_allowed
    reason := "Deployment not allowed"
}
```

---

## Day 4: AI Sprint Assistant Foundation

### Sprint Assistant Service

**File:** `backend/app/services/sprint_assistant.py` (NEW)

See Sprint 76 plan for full implementation.

Key methods:
- `calculate_velocity()` - Historical velocity from completed sprints
- `get_sprint_health()` - Completion rate, blocked items, risk level
- `suggest_priorities()` - AI-powered backlog prioritization

---

## Day 5: Sprint Analytics Dashboard

### New API Endpoints

```yaml
GET /planning/projects/{project_id}/velocity
  description: Get velocity metrics from last N sprints
  response:
    average: number
    trend: "increasing" | "decreasing" | "stable"
    history: number[]

GET /planning/sprints/{sprint_id}/health
  description: Get sprint health indicators
  response:
    completion_rate: number
    blocked_count: number
    risk_level: "low" | "medium" | "high"
    days_remaining: number

GET /planning/sprints/{sprint_id}/suggestions
  description: Get AI prioritization suggestions
  response:
    suggestions:
      - type: string
        message: string
        severity: "info" | "warning" | "error"
```

### Frontend Components

- `SprintVelocityChart.tsx` - Line chart showing velocity trend
- `SprintHealthWidget.tsx` - Health indicators with risk level

---

## Database Schema Changes

No new tables required. Existing models support all Day 1-5 features.

---

## API Contract Summary

| Day | Endpoint | Method | Description |
|-----|----------|--------|-------------|
| 1 | `/planning/projects/{id}/assignable-users` | GET | List team members for assignment |
| 1 | `/planning/backlog` | POST | Create with assignee validation |
| 1 | `/planning/backlog/{id}` | PUT | Update with assignee validation |
| 2 | `/sase/evaluate` | POST | SASE evaluation with sprint context |
| 5 | `/planning/projects/{id}/velocity` | GET | Velocity metrics |
| 5 | `/planning/sprints/{id}/health` | GET | Sprint health |
| 5 | `/planning/sprints/{id}/suggestions` | GET | AI suggestions |

---

## Test Strategy

| Day | Test File | Tests | Focus |
|-----|-----------|-------|-------|
| 1 | `test_backlog_assignee.py` | 12 | GAP 2 validation |
| 2 | `test_sase_sprint.py` | 10 | GAP 3 context |
| 3 | `test_sase_policies.py` | 8 | OPA policy evaluation |
| 4 | `test_sprint_assistant.py` | 6 | Velocity, health |
| 5 | `test_sprint_analytics.py` | 6 | API endpoints |
| **Total** | | **42** | |

---

## Implementation Order

1. **Day 1** (GAP 2): BacklogService → planning.py updates → tests
2. **Day 2** (GAP 3): sase.py schemas → SprintContextProvider → tests
3. **Day 3**: OPA policies → policy tests
4. **Day 4**: SprintAssistantService → tests
5. **Day 5**: Analytics API → Frontend components → final tests

---

**Document Status:** ✅ DESIGN COMPLETE - Ready for Implementation

**Approvals Required:**
- [ ] CTO Technical Review
- [ ] Backend Lead Sign-off
- [ ] G-Sprint Gate Approval (before Sprint 76 start)
