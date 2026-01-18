"""
=========================================================================
Backlog Service - Business Logic for Backlog Item Operations
SDLC Orchestrator - Sprint 76 (SASE Workflow Integration)

Version: 1.0.0
Date: January 18, 2026
Status: ACTIVE - Sprint 76 Day 1 Implementation
Authority: Backend Lead + CTO Approved
Reference: SPRINT-76-TECHNICAL-DESIGN.md
Reference: SDLC-Sprint-Planning-Governance.md (SDLC 5.1.3)

Purpose:
- Service layer for backlog item CRUD operations
- GAP 2 Resolution: Assignee team membership validation
- Sprint context integration for SASE workflows
- Business logic for backlog prioritization

SDLC 5.1.3 Compliance:
- GAP 2: Backlog assignee must be project team member
- Rule #8: P0/P1/P2 priority enforcement
- G-Sprint-Close: All items accounted for

Zero Mock Policy: Production-ready service with async/await
=========================================================================
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.backlog_item import BacklogItem
from app.models.project import Project
from app.models.sprint import Sprint
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User


# =========================================================================
# Custom Exceptions
# =========================================================================


class BacklogServiceError(Exception):
    """Base exception for BacklogService errors."""
    pass


class BacklogItemNotFoundError(BacklogServiceError):
    """Backlog item not found."""
    def __init__(self, item_id: UUID):
        self.item_id = item_id
        super().__init__(f"Backlog item {item_id} not found")


class SprintNotFoundError(BacklogServiceError):
    """Sprint not found."""
    def __init__(self, sprint_id: UUID):
        self.sprint_id = sprint_id
        super().__init__(f"Sprint {sprint_id} not found")


class ProjectNotFoundError(BacklogServiceError):
    """Project not found."""
    def __init__(self, project_id: UUID):
        self.project_id = project_id
        super().__init__(f"Project {project_id} not found")


class AssigneeNotTeamMemberError(BacklogServiceError):
    """
    Assignee is not a member of the project team.

    GAP 2 Resolution: This error is raised when attempting to assign
    a backlog item to a user who is not a member of the project team.
    """
    def __init__(self, user_id: UUID, team_id: UUID, project_id: UUID):
        self.user_id = user_id
        self.team_id = team_id
        self.project_id = project_id
        super().__init__(
            f"User {user_id} is not a member of project team {team_id}. "
            f"Backlog items can only be assigned to team members. "
            f"(SDLC 5.1.3 GAP 2 Resolution)"
        )


class InvalidPriorityError(BacklogServiceError):
    """Invalid priority value."""
    def __init__(self, priority: str):
        self.priority = priority
        super().__init__(
            f"Invalid priority '{priority}'. "
            f"Must be P0, P1, or P2 per SDLC 5.1.3 Rule #8."
        )


class InvalidStatusTransitionError(BacklogServiceError):
    """Invalid status transition."""
    def __init__(self, current_status: str, new_status: str):
        self.current_status = current_status
        self.new_status = new_status
        super().__init__(
            f"Cannot transition from '{current_status}' to '{new_status}'"
        )


# =========================================================================
# BacklogService
# =========================================================================


class BacklogService:
    """
    Service layer for backlog item operations.

    Provides business logic for:
    - Backlog item CRUD operations
    - GAP 2: Assignee team membership validation
    - Priority management (Rule #8)
    - Sprint assignment validation
    - Status transitions

    All methods are async and use SQLAlchemy AsyncSession.

    SDLC 5.1.3 Compliance:
    - GAP 2 Resolution: validate_assignee_membership()
    - Rule #8: P0/P1/P2 priority enforcement
    - G-Sprint-Close: get_sprint_completion_status()
    """

    # Valid priorities per SDLC 5.1.3 Rule #8
    VALID_PRIORITIES = ("P0", "P1", "P2")

    # Valid statuses
    VALID_STATUSES = ("todo", "in_progress", "review", "done", "blocked")

    # Valid item types
    VALID_TYPES = ("story", "task", "bug", "spike")

    # Status transition rules
    STATUS_TRANSITIONS = {
        "todo": ["in_progress", "blocked"],
        "in_progress": ["review", "done", "blocked"],
        "review": ["in_progress", "done"],
        "done": [],  # Cannot transition from done
        "blocked": ["todo", "in_progress"],
    }

    def __init__(self, db: AsyncSession):
        """
        Initialize BacklogService.

        Args:
            db: Async database session
        """
        self.db = db

    # =========================================================================
    # GAP 2 Resolution: Assignee Team Membership Validation
    # =========================================================================

    async def validate_assignee_membership(
        self,
        sprint_id: Optional[UUID],
        project_id: UUID,
        assignee_id: UUID,
    ) -> bool:
        """
        Validate that assignee is a member of the project team.

        GAP 2 Resolution: Ensures backlog items can only be assigned
        to users who are members of the project team.

        Args:
            sprint_id: Optional sprint UUID (for sprint context)
            project_id: Project UUID
            assignee_id: User UUID to validate

        Returns:
            True if validation passes

        Raises:
            ProjectNotFoundError: If project not found
            AssigneeNotTeamMemberError: If assignee is not a team member

        SDLC 5.1.3 Compliance:
        - GAP 2: Backlog assignee must be project team member
        - Enforces team-based access control for work assignment

        Example:
            service = BacklogService(db)
            try:
                await service.validate_assignee_membership(
                    sprint_id=sprint.id,
                    project_id=project.id,
                    assignee_id=developer.id
                )
            except AssigneeNotTeamMemberError as e:
                # Handle non-team member assignment
                raise HTTPException(status_code=403, detail=str(e))
        """
        # Get project with team relation
        project_result = await self.db.execute(
            select(Project)
            .options(selectinload(Project.team))
            .where(
                Project.id == project_id,
                Project.deleted_at.is_(None),
            )
        )
        project = project_result.scalar_one_or_none()

        if not project:
            raise ProjectNotFoundError(project_id)

        # If project has no team, allow any assignee (legacy behavior)
        # This maintains backward compatibility for projects without teams
        if not project.team_id:
            return True

        # Check if assignee is a team member
        team_member_result = await self.db.execute(
            select(TeamMember)
            .where(
                TeamMember.team_id == project.team_id,
                TeamMember.user_id == assignee_id,
                TeamMember.deleted_at.is_(None),
            )
        )
        team_member = team_member_result.scalar_one_or_none()

        if not team_member:
            raise AssigneeNotTeamMemberError(
                user_id=assignee_id,
                team_id=project.team_id,
                project_id=project_id,
            )

        return True

    async def get_valid_assignees(
        self,
        project_id: UUID,
    ) -> List[Dict[str, Any]]:
        """
        Get list of valid assignees for a project.

        Returns all team members who can be assigned to backlog items.
        Used by frontend to populate assignee dropdown.

        Args:
            project_id: Project UUID

        Returns:
            List of dicts with user info:
            [
                {
                    "user_id": UUID,
                    "full_name": str,
                    "email": str,
                    "role": str,  # team role
                    "member_type": str,  # human/ai_agent
                }
            ]

        Note:
            If project has no team, returns empty list.
            Frontend should handle this by allowing any user selection.
        """
        # Get project with team
        project_result = await self.db.execute(
            select(Project)
            .where(
                Project.id == project_id,
                Project.deleted_at.is_(None),
            )
        )
        project = project_result.scalar_one_or_none()

        if not project or not project.team_id:
            return []

        # Get team members with user info
        members_result = await self.db.execute(
            select(TeamMember, User)
            .join(User, TeamMember.user_id == User.id)
            .where(
                TeamMember.team_id == project.team_id,
                TeamMember.deleted_at.is_(None),
            )
            .order_by(User.full_name)
        )
        members = members_result.all()

        return [
            {
                "user_id": member.TeamMember.user_id,
                "full_name": user.User.full_name or user.User.username,
                "email": user.User.email,
                "role": member.TeamMember.role,
                "member_type": member.TeamMember.member_type,
            }
            for member, user in [(m, m) for m in members]
        ]

    # =========================================================================
    # Backlog Item CRUD Operations
    # =========================================================================

    async def create_item(
        self,
        project_id: UUID,
        item_type: str,
        title: str,
        created_by: UUID,
        description: Optional[str] = None,
        acceptance_criteria: Optional[str] = None,
        priority: str = "P2",
        story_points: Optional[int] = None,
        sprint_id: Optional[UUID] = None,
        assignee_id: Optional[UUID] = None,
        parent_id: Optional[UUID] = None,
        labels: Optional[List[str]] = None,
    ) -> BacklogItem:
        """
        Create a new backlog item with validation.

        Args:
            project_id: Project UUID
            item_type: Item type (story, task, bug, spike)
            title: Item title
            created_by: Creator user UUID
            description: Optional description
            acceptance_criteria: Optional acceptance criteria
            priority: Priority (P0, P1, P2) - default P2
            story_points: Optional story point estimate
            sprint_id: Optional sprint assignment
            assignee_id: Optional assignee (validated against team)
            parent_id: Optional parent item for subtasks
            labels: Optional list of labels

        Returns:
            Created BacklogItem

        Raises:
            InvalidPriorityError: If priority is not P0/P1/P2
            AssigneeNotTeamMemberError: If assignee is not a team member

        SDLC 5.1.3 Compliance:
        - GAP 2: Validates assignee is team member
        - Rule #8: Validates priority is P0/P1/P2
        """
        # Validate priority (Rule #8)
        if priority not in self.VALID_PRIORITIES:
            raise InvalidPriorityError(priority)

        # Validate item type
        if item_type not in self.VALID_TYPES:
            raise BacklogServiceError(
                f"Invalid item type '{item_type}'. "
                f"Must be one of: {', '.join(self.VALID_TYPES)}"
            )

        # GAP 2: Validate assignee is team member
        if assignee_id:
            await self.validate_assignee_membership(
                sprint_id=sprint_id,
                project_id=project_id,
                assignee_id=assignee_id,
            )

        # Create item
        item = BacklogItem(
            project_id=project_id,
            sprint_id=sprint_id,
            parent_id=parent_id,
            type=item_type,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            priority=priority,
            story_points=story_points,
            status="todo",
            assignee_id=assignee_id,
            labels=labels or [],
            created_by=created_by,
        )

        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)

        return item

    async def update_item(
        self,
        item_id: UUID,
        **updates,
    ) -> BacklogItem:
        """
        Update a backlog item with validation.

        Args:
            item_id: Backlog item UUID
            **updates: Fields to update

        Returns:
            Updated BacklogItem

        Raises:
            BacklogItemNotFoundError: If item not found
            InvalidPriorityError: If priority is invalid
            AssigneeNotTeamMemberError: If new assignee is not team member
            InvalidStatusTransitionError: If status transition is invalid
        """
        # Get item
        item_result = await self.db.execute(
            select(BacklogItem).where(BacklogItem.id == item_id)
        )
        item = item_result.scalar_one_or_none()

        if not item:
            raise BacklogItemNotFoundError(item_id)

        # Validate priority if being updated
        if "priority" in updates:
            if updates["priority"] not in self.VALID_PRIORITIES:
                raise InvalidPriorityError(updates["priority"])

        # Validate status transition if being updated
        if "status" in updates:
            new_status = updates["status"]
            if new_status not in self.STATUS_TRANSITIONS.get(item.status, []):
                # Allow same status
                if new_status != item.status:
                    raise InvalidStatusTransitionError(item.status, new_status)

        # GAP 2: Validate assignee if being updated
        if "assignee_id" in updates and updates["assignee_id"]:
            await self.validate_assignee_membership(
                sprint_id=item.sprint_id,
                project_id=item.project_id,
                assignee_id=updates["assignee_id"],
            )

        # Apply updates
        for field, value in updates.items():
            if hasattr(item, field):
                setattr(item, field, value)

        item.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(item)

        return item

    async def assign_to_user(
        self,
        item_id: UUID,
        assignee_id: UUID,
    ) -> BacklogItem:
        """
        Assign backlog item to a user with team membership validation.

        Args:
            item_id: Backlog item UUID
            assignee_id: User UUID to assign

        Returns:
            Updated BacklogItem

        Raises:
            BacklogItemNotFoundError: If item not found
            AssigneeNotTeamMemberError: If assignee is not a team member

        SDLC 5.1.3 GAP 2 Resolution:
        This is the primary method for assigning work to team members.
        It ensures only valid team members can be assigned tasks.
        """
        return await self.update_item(item_id, assignee_id=assignee_id)

    async def move_to_sprint(
        self,
        item_id: UUID,
        sprint_id: Optional[UUID],
    ) -> BacklogItem:
        """
        Move backlog item to a sprint (or back to product backlog).

        Args:
            item_id: Backlog item UUID
            sprint_id: Sprint UUID (None = move to product backlog)

        Returns:
            Updated BacklogItem

        Raises:
            BacklogItemNotFoundError: If item not found
            SprintNotFoundError: If sprint not found
        """
        if sprint_id:
            # Validate sprint exists
            sprint_result = await self.db.execute(
                select(Sprint).where(Sprint.id == sprint_id)
            )
            if not sprint_result.scalar_one_or_none():
                raise SprintNotFoundError(sprint_id)

        return await self.update_item(item_id, sprint_id=sprint_id)

    # =========================================================================
    # Sprint Completion Analysis (G-Sprint-Close Support)
    # =========================================================================

    async def get_sprint_completion_status(
        self,
        sprint_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get sprint completion status for G-Sprint-Close gate.

        Returns metrics needed for G-Sprint-Close evaluation:
        - Total items and points
        - Completed vs incomplete items
        - Blocked items
        - P0/P1/P2 breakdown

        Args:
            sprint_id: Sprint UUID

        Returns:
            Dict with completion metrics:
            {
                "sprint_id": UUID,
                "total_items": int,
                "completed_items": int,
                "completion_rate": float,
                "total_points": int,
                "completed_points": int,
                "blocked_count": int,
                "p0_incomplete": int,
                "p1_incomplete": int,
                "items_by_status": {...},
                "ready_to_close": bool,
                "blockers": [...]
            }
        """
        # Get all items for sprint
        items_result = await self.db.execute(
            select(BacklogItem)
            .where(BacklogItem.sprint_id == sprint_id)
        )
        items = items_result.scalars().all()

        total_items = len(items)
        completed_items = sum(1 for i in items if i.status == "done")
        blocked_items = [i for i in items if i.status == "blocked"]

        total_points = sum(i.story_points or 0 for i in items)
        completed_points = sum(
            i.story_points or 0 for i in items if i.status == "done"
        )

        # Count incomplete by priority
        p0_incomplete = sum(
            1 for i in items
            if i.priority == "P0" and i.status != "done"
        )
        p1_incomplete = sum(
            1 for i in items
            if i.priority == "P1" and i.status != "done"
        )

        # Items by status
        items_by_status = {}
        for item in items:
            items_by_status[item.status] = items_by_status.get(item.status, 0) + 1

        # Determine if ready to close
        # Per SDLC 5.1.3: All P0 items must be done, no blocked items
        blockers = []
        if p0_incomplete > 0:
            blockers.append(f"{p0_incomplete} P0 items not completed")
        if len(blocked_items) > 0:
            blockers.append(f"{len(blocked_items)} items are blocked")

        ready_to_close = len(blockers) == 0

        completion_rate = (
            completed_items / total_items * 100
            if total_items > 0 else 0.0
        )

        return {
            "sprint_id": sprint_id,
            "total_items": total_items,
            "completed_items": completed_items,
            "completion_rate": round(completion_rate, 1),
            "total_points": total_points,
            "completed_points": completed_points,
            "blocked_count": len(blocked_items),
            "p0_incomplete": p0_incomplete,
            "p1_incomplete": p1_incomplete,
            "items_by_status": items_by_status,
            "ready_to_close": ready_to_close,
            "blockers": blockers,
            "blocked_items": [
                {"id": i.id, "title": i.title, "priority": i.priority}
                for i in blocked_items
            ],
        }

    async def get_carryover_candidates(
        self,
        sprint_id: UUID,
    ) -> List[BacklogItem]:
        """
        Get items that should be carried over to next sprint.

        Returns incomplete items sorted by priority for carryover planning.

        Args:
            sprint_id: Sprint UUID

        Returns:
            List of BacklogItem objects not in 'done' status
        """
        result = await self.db.execute(
            select(BacklogItem)
            .where(
                BacklogItem.sprint_id == sprint_id,
                BacklogItem.status != "done",
            )
            .order_by(
                BacklogItem.priority,  # P0 first
                BacklogItem.created_at,
            )
        )
        return list(result.scalars().all())

    # =========================================================================
    # Statistics and Analytics
    # =========================================================================

    async def get_project_backlog_stats(
        self,
        project_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get backlog statistics for a project.

        Args:
            project_id: Project UUID

        Returns:
            Dict with backlog statistics
        """
        # Total counts
        total_result = await self.db.execute(
            select(func.count(BacklogItem.id))
            .where(BacklogItem.project_id == project_id)
        )
        total_count = total_result.scalar() or 0

        # In sprint vs product backlog
        in_sprint_result = await self.db.execute(
            select(func.count(BacklogItem.id))
            .where(
                BacklogItem.project_id == project_id,
                BacklogItem.sprint_id.isnot(None),
            )
        )
        in_sprint_count = in_sprint_result.scalar() or 0

        # By priority
        priority_result = await self.db.execute(
            select(
                BacklogItem.priority,
                func.count(BacklogItem.id),
            )
            .where(BacklogItem.project_id == project_id)
            .group_by(BacklogItem.priority)
        )
        priority_counts = {row[0]: row[1] for row in priority_result.all()}

        # By status
        status_result = await self.db.execute(
            select(
                BacklogItem.status,
                func.count(BacklogItem.id),
            )
            .where(BacklogItem.project_id == project_id)
            .group_by(BacklogItem.status)
        )
        status_counts = {row[0]: row[1] for row in status_result.all()}

        # Total points
        points_result = await self.db.execute(
            select(func.sum(BacklogItem.story_points))
            .where(BacklogItem.project_id == project_id)
        )
        total_points = points_result.scalar() or 0

        return {
            "project_id": project_id,
            "total_items": total_count,
            "in_sprint": in_sprint_count,
            "in_backlog": total_count - in_sprint_count,
            "by_priority": priority_counts,
            "by_status": status_counts,
            "total_points": total_points,
        }
