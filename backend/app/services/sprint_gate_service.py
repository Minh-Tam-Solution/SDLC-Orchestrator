"""
=========================================================================
Sprint Gate Service - G-Sprint/G-Sprint-Close Gate Evaluation
SDLC Orchestrator - Sprint 74/75 (Planning Hierarchy + Team Authorization)

Version: 1.1.0
Date: January 18, 2026
Status: ACTIVE - Sprint 75 Enhancement
Authority: Backend Lead + CTO Approved
Reference: ADR-013-Planning-Hierarchy
Reference: SDLC-Sprint-Planning-Governance.md (SDLC 5.1.3)

Purpose:
- G-Sprint Gate evaluation logic (Sprint Planning)
- G-Sprint-Close Gate evaluation logic (Sprint Completion)
- 24-hour documentation deadline enforcement (Rule #2)
- Checklist-based validation per SDLC 5.1.3
- Team role authorization (Sprint 75 - GAP 1 Resolution)

SDLC 5.1.3 Compliance:
- Rule #1: Sprint numbers are immutable
- Rule #2: Post-sprint documentation within 24 hours
- Rule #3: Sprint planning requires approval
- Rule #7: Sprint goal must align with roadmap phase
- Rule #8: Strategic priorities explicit (P0/P1/P2)

Team Authorization (Sprint 75):
- Only team owner/admin (SE4H Coach) can approve sprint gates
- Project without team: fallback to project owner authorization
- Enforces human oversight for sprint governance

Zero Mock Policy: Production-ready service implementation
=========================================================================
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.backlog_item import BacklogItem
from app.models.phase import Phase
from app.models.project import Project
from app.models.roadmap import Roadmap
from app.models.sprint import Sprint
from app.models.sprint_gate_evaluation import (
    SprintGateEvaluation,
    G_SPRINT_CHECKLIST_TEMPLATE,
    G_SPRINT_CLOSE_CHECKLIST_TEMPLATE,
)
from app.models.team import Team
from app.models.team_member import TeamMember


class SprintGateService:
    """
    Service for Sprint Gate evaluation per SDLC 5.1.3 governance.

    Gates:
    - G-Sprint: Validates sprint plan before execution
    - G-Sprint-Close: Validates sprint completion with 24h deadline

    Usage:
        service = SprintGateService(db)
        result = await service.evaluate_g_sprint(sprint_id, user_id)
        result = await service.evaluate_g_sprint_close(sprint_id, user_id)
    """

    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db

    async def check_gate_approval_authorization(
        self,
        sprint: Sprint,
        user_id: UUID,
    ) -> dict:
        """
        Check if user is authorized to approve sprint gates.

        SDLC 5.1.3 Authorization Rules:
        1. If project has team: user must be team owner/admin (SE4H Coach)
        2. If project has no team: user must be project owner
        3. AI agents (SE4A) cannot approve gates

        Args:
            sprint: Sprint object with project relation
            user_id: User attempting to approve

        Returns:
            dict with 'authorized' (bool) and 'reason' (str)
        """
        # Get project with team relation
        project_result = await self.db.execute(
            select(Project)
            .options(selectinload(Project.team).selectinload(Team.members))
            .where(Project.id == sprint.project_id)
        )
        project = project_result.scalar_one_or_none()

        if not project:
            return {
                "authorized": False,
                "reason": "Project not found",
            }

        # If project has team, check team role
        if project.team:
            # Find user's membership in team
            team_member = None
            for member in project.team.members:
                if member.user_id == user_id and member.deleted_at is None:
                    team_member = member
                    break

            if not team_member:
                return {
                    "authorized": False,
                    "reason": "User is not a member of the project team",
                }

            if not team_member.can_approve_sprint_gate:
                return {
                    "authorized": False,
                    "reason": f"User role '{team_member.role}' cannot approve sprint gates. "
                              f"Only team owner/admin (SE4H Coach) can approve.",
                }

            return {
                "authorized": True,
                "reason": f"Authorized as team {team_member.role}",
                "team_id": str(project.team.id),
                "team_name": project.team.name,
                "member_role": team_member.role,
            }

        # Fallback: project without team - check project owner
        if project.owner_id == user_id:
            return {
                "authorized": True,
                "reason": "Authorized as project owner (no team assigned)",
            }

        return {
            "authorized": False,
            "reason": "Only project owner can approve gates for projects without team",
        }

    async def get_sprint(self, sprint_id: UUID) -> Optional[Sprint]:
        """Get sprint by ID with phase/roadmap relations."""
        result = await self.db.execute(
            select(Sprint)
            .options(
                selectinload(Sprint.phase).selectinload(Phase.roadmap)
            )
            .where(Sprint.id == sprint_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create_evaluation(
        self,
        sprint_id: UUID,
        gate_type: str,
    ) -> SprintGateEvaluation:
        """
        Get existing evaluation or create a new one from template.

        Args:
            sprint_id: Sprint UUID
            gate_type: 'g_sprint' or 'g_sprint_close'

        Returns:
            SprintGateEvaluation instance
        """
        result = await self.db.execute(
            select(SprintGateEvaluation).where(
                SprintGateEvaluation.sprint_id == sprint_id,
                SprintGateEvaluation.gate_type == gate_type,
            )
        )
        evaluation = result.scalar_one_or_none()

        if evaluation:
            return evaluation

        # Create new evaluation from template
        if gate_type == "g_sprint":
            evaluation = SprintGateEvaluation.create_g_sprint_evaluation(sprint_id)
        else:
            evaluation = SprintGateEvaluation.create_g_sprint_close_evaluation(sprint_id)

        self.db.add(evaluation)
        await self.db.flush()

        return evaluation

    async def auto_evaluate_g_sprint(
        self,
        sprint_id: UUID,
    ) -> dict:
        """
        Auto-evaluate G-Sprint gate checklist based on sprint data.

        Checks:
        - Alignment: Sprint goal exists, phase objective exists
        - Capacity: Team size set, capacity set
        - Dependencies: Sprint has backlog items
        - Documentation: Sprint plan committed

        Args:
            sprint_id: Sprint UUID to evaluate

        Returns:
            dict with auto-evaluated items and recommendations
        """
        sprint = await self.get_sprint(sprint_id)
        if not sprint:
            return {"error": "Sprint not found"}

        evaluation = await self.get_or_create_evaluation(sprint_id, "g_sprint")

        auto_checks = {
            "passed": [],
            "failed": [],
            "manual_required": [],
        }

        # Check alignment
        if sprint.goal and len(sprint.goal) >= 10:
            auto_checks["passed"].append("alignment_goal_defined")
        else:
            auto_checks["failed"].append("alignment_goal_defined")

        if sprint.phase and sprint.phase.objective:
            auto_checks["passed"].append("alignment_phase_objective")
        else:
            auto_checks["manual_required"].append("alignment_phase_objective")

        # Check capacity
        if sprint.team_size and sprint.team_size > 0:
            auto_checks["passed"].append("capacity_team_calculated")
        else:
            auto_checks["failed"].append("capacity_team_calculated")

        if sprint.capacity_points and sprint.capacity_points > 0:
            auto_checks["passed"].append("capacity_points_set")
        else:
            auto_checks["manual_required"].append("capacity_points_set")

        # Check dependencies - count backlog items
        backlog_count_result = await self.db.execute(
            select(func.count(BacklogItem.id)).where(
                BacklogItem.sprint_id == sprint_id
            )
        )
        backlog_count = backlog_count_result.scalar() or 0

        if backlog_count > 0:
            auto_checks["passed"].append("dependencies_backlog_defined")
        else:
            auto_checks["failed"].append("dependencies_backlog_defined")

        # Check P0 items exist
        p0_count_result = await self.db.execute(
            select(func.count(BacklogItem.id)).where(
                BacklogItem.sprint_id == sprint_id,
                BacklogItem.priority == "P0",
            )
        )
        p0_count = p0_count_result.scalar() or 0

        if p0_count > 0:
            auto_checks["passed"].append("alignment_priorities_explicit")
        else:
            auto_checks["manual_required"].append("alignment_priorities_explicit")

        # Check dates are set
        if sprint.start_date and sprint.end_date:
            auto_checks["passed"].append("documentation_dates_set")
        else:
            auto_checks["failed"].append("documentation_dates_set")

        return {
            "sprint_id": str(sprint_id),
            "gate_type": "g_sprint",
            "auto_checks": auto_checks,
            "total_passed": len(auto_checks["passed"]),
            "total_failed": len(auto_checks["failed"]),
            "total_manual": len(auto_checks["manual_required"]),
            "can_auto_pass": len(auto_checks["failed"]) == 0 and len(auto_checks["manual_required"]) == 0,
            "recommendations": self._get_recommendations(auto_checks),
        }

    async def auto_evaluate_g_sprint_close(
        self,
        sprint_id: UUID,
    ) -> dict:
        """
        Auto-evaluate G-Sprint-Close gate checklist based on sprint data.

        Checks:
        - Work: All items accounted for (done or carryover documented)
        - Quality: No P0 bugs in 'todo' or 'in_progress' status
        - Metrics: Sprint has end_date for deadline calculation
        - Documentation: Within 24h deadline (Rule #2)

        Args:
            sprint_id: Sprint UUID to evaluate

        Returns:
            dict with auto-evaluated items and recommendations
        """
        sprint = await self.get_sprint(sprint_id)
        if not sprint:
            return {"error": "Sprint not found"}

        evaluation = await self.get_or_create_evaluation(sprint_id, "g_sprint_close")

        auto_checks = {
            "passed": [],
            "failed": [],
            "manual_required": [],
        }

        # Check work completion
        incomplete_items_result = await self.db.execute(
            select(func.count(BacklogItem.id)).where(
                BacklogItem.sprint_id == sprint_id,
                BacklogItem.status.in_(["todo", "in_progress", "review"]),
            )
        )
        incomplete_count = incomplete_items_result.scalar() or 0

        if incomplete_count == 0:
            auto_checks["passed"].append("work_all_items_accounted")
        else:
            auto_checks["failed"].append("work_all_items_accounted")

        # Check no P0 bugs remaining
        p0_bugs_result = await self.db.execute(
            select(func.count(BacklogItem.id)).where(
                BacklogItem.sprint_id == sprint_id,
                BacklogItem.type == "bug",
                BacklogItem.priority == "P0",
                BacklogItem.status.in_(["todo", "in_progress"]),
            )
        )
        p0_bugs = p0_bugs_result.scalar() or 0

        if p0_bugs == 0:
            auto_checks["passed"].append("quality_no_p0_bugs")
        else:
            auto_checks["failed"].append("quality_no_p0_bugs")

        # Check documentation deadline (Rule #2)
        if sprint.end_date:
            deadline = datetime.combine(sprint.end_date, datetime.min.time()) + timedelta(hours=24)
            if datetime.utcnow() <= deadline:
                auto_checks["passed"].append("documentation_within_24h")
            else:
                auto_checks["failed"].append("documentation_within_24h")
        else:
            auto_checks["manual_required"].append("documentation_within_24h")

        # Check velocity can be calculated
        done_items_result = await self.db.execute(
            select(func.sum(BacklogItem.story_points)).where(
                BacklogItem.sprint_id == sprint_id,
                BacklogItem.status == "done",
            )
        )
        done_points = done_items_result.scalar() or 0

        if done_points > 0:
            auto_checks["passed"].append("metrics_velocity_calculated")
        else:
            auto_checks["manual_required"].append("metrics_velocity_calculated")

        return {
            "sprint_id": str(sprint_id),
            "gate_type": "g_sprint_close",
            "auto_checks": auto_checks,
            "total_passed": len(auto_checks["passed"]),
            "total_failed": len(auto_checks["failed"]),
            "total_manual": len(auto_checks["manual_required"]),
            "can_auto_pass": len(auto_checks["failed"]) == 0 and len(auto_checks["manual_required"]) == 0,
            "recommendations": self._get_recommendations(auto_checks),
            "metrics": {
                "incomplete_items": incomplete_count,
                "p0_bugs_remaining": p0_bugs,
                "completed_points": done_points,
                "documentation_deadline": sprint.documentation_deadline.isoformat() if sprint.documentation_deadline else None,
                "is_overdue": sprint.documentation_overdue,
            },
        }

    def _get_recommendations(self, auto_checks: dict) -> list[str]:
        """Generate recommendations based on failed/manual checks."""
        recommendations = []

        failed_items = {
            "alignment_goal_defined": "Define a clear sprint goal (min 10 characters)",
            "capacity_team_calculated": "Set team size for capacity planning",
            "dependencies_backlog_defined": "Add backlog items to the sprint",
            "documentation_dates_set": "Set sprint start and end dates",
            "work_all_items_accounted": "Complete or carry over all remaining items",
            "quality_no_p0_bugs": "Resolve all P0 bugs before closing sprint",
            "documentation_within_24h": "Complete documentation within 24h deadline (Rule #2)",
        }

        for item in auto_checks.get("failed", []):
            if item in failed_items:
                recommendations.append(failed_items[item])

        manual_items = {
            "alignment_phase_objective": "Verify sprint goal aligns with phase objective",
            "alignment_priorities_explicit": "Add at least one P0 priority item",
            "capacity_points_set": "Set story points capacity",
            "metrics_velocity_calculated": "Ensure some items are marked done",
        }

        for item in auto_checks.get("manual_required", []):
            if item in manual_items:
                recommendations.append(f"[Manual] {manual_items[item]}")

        return recommendations

    async def submit_evaluation(
        self,
        sprint_id: UUID,
        gate_type: str,
        user_id: UUID,
        notes: Optional[str] = None,
        skip_authorization: bool = False,
    ) -> dict:
        """
        Submit gate evaluation for final approval.

        This finalizes the evaluation and updates the sprint gate status.
        Requires team owner/admin (SE4H Coach) authorization per SDLC 5.1.3.

        Args:
            sprint_id: Sprint UUID
            gate_type: 'g_sprint' or 'g_sprint_close'
            user_id: Approver user UUID
            notes: Optional approval notes
            skip_authorization: Skip auth check (for system/admin use only)

        Returns:
            dict with evaluation result and sprint status
        """
        sprint = await self.get_sprint(sprint_id)
        if not sprint:
            return {"error": "Sprint not found", "success": False}

        # Sprint 75: Team Role Authorization (GAP 1)
        if not skip_authorization:
            auth_result = await self.check_gate_approval_authorization(sprint, user_id)
            if not auth_result["authorized"]:
                return {
                    "error": auth_result["reason"],
                    "success": False,
                    "authorization_failed": True,
                }

        evaluation = await self.get_or_create_evaluation(sprint_id, gate_type)

        if evaluation.status != "pending":
            return {
                "error": f"Evaluation already finalized with status: {evaluation.status}",
                "success": False,
            }

        # Update notes if provided
        if notes:
            evaluation.notes = notes

        # Finalize evaluation
        evaluation.finalize_evaluation(user_id)

        # Update sprint gate status
        if gate_type == "g_sprint":
            sprint.g_sprint_status = evaluation.status
            if evaluation.status == "passed":
                sprint.g_sprint_approved_by = user_id
                sprint.g_sprint_approved_at = datetime.utcnow()
        else:
            sprint.g_sprint_close_status = evaluation.status
            if evaluation.status == "passed":
                sprint.g_sprint_close_approved_by = user_id
                sprint.g_sprint_close_approved_at = datetime.utcnow()

        await self.db.commit()

        return {
            "success": True,
            "gate_type": gate_type,
            "status": evaluation.status,
            "evaluated_by": str(user_id),
            "evaluated_at": evaluation.evaluated_at.isoformat() if evaluation.evaluated_at else None,
            "sprint_can_start": sprint.can_start if gate_type == "g_sprint" else None,
            "sprint_can_close": sprint.can_close if gate_type == "g_sprint_close" else None,
        }

    async def get_sprint_governance_summary(
        self,
        sprint_id: UUID,
    ) -> dict:
        """
        Get comprehensive sprint governance summary.

        Returns:
        - Sprint details
        - G-Sprint gate status and evaluation
        - G-Sprint-Close gate status and evaluation
        - Backlog statistics
        - Compliance with SDLC 5.1.3 rules

        Args:
            sprint_id: Sprint UUID

        Returns:
            dict with complete governance summary
        """
        sprint = await self.get_sprint(sprint_id)
        if not sprint:
            return {"error": "Sprint not found"}

        # Get evaluations
        g_sprint_eval = await self.get_or_create_evaluation(sprint_id, "g_sprint")
        g_sprint_close_eval = await self.get_or_create_evaluation(sprint_id, "g_sprint_close")

        # Get backlog stats
        backlog_stats_result = await self.db.execute(
            select(
                func.count(BacklogItem.id),
                func.coalesce(func.sum(BacklogItem.story_points), 0),
            ).where(BacklogItem.sprint_id == sprint_id)
        )
        backlog_row = backlog_stats_result.one()

        # Get status breakdown
        status_breakdown_result = await self.db.execute(
            select(BacklogItem.status, func.count(BacklogItem.id))
            .where(BacklogItem.sprint_id == sprint_id)
            .group_by(BacklogItem.status)
        )
        status_breakdown = {row[0]: row[1] for row in status_breakdown_result}

        # Get priority breakdown
        priority_breakdown_result = await self.db.execute(
            select(BacklogItem.priority, func.count(BacklogItem.id))
            .where(BacklogItem.sprint_id == sprint_id)
            .group_by(BacklogItem.priority)
        )
        priority_breakdown = {row[0]: row[1] for row in priority_breakdown_result}

        return {
            "sprint": {
                "id": str(sprint.id),
                "number": sprint.number,
                "name": sprint.name,
                "goal": sprint.goal,
                "status": sprint.status,
                "start_date": sprint.start_date.isoformat() if sprint.start_date else None,
                "end_date": sprint.end_date.isoformat() if sprint.end_date else None,
                "can_start": sprint.can_start,
                "can_close": sprint.can_close,
            },
            "g_sprint": {
                "status": sprint.g_sprint_status,
                "approved_by": str(sprint.g_sprint_approved_by) if sprint.g_sprint_approved_by else None,
                "approved_at": sprint.g_sprint_approved_at.isoformat() if sprint.g_sprint_approved_at else None,
                "evaluation_status": g_sprint_eval.status,
                "checklist": g_sprint_eval.checklist,
            },
            "g_sprint_close": {
                "status": sprint.g_sprint_close_status,
                "approved_by": str(sprint.g_sprint_close_approved_by) if sprint.g_sprint_close_approved_by else None,
                "approved_at": sprint.g_sprint_close_approved_at.isoformat() if sprint.g_sprint_close_approved_at else None,
                "evaluation_status": g_sprint_close_eval.status,
                "checklist": g_sprint_close_eval.checklist,
                "documentation_deadline": sprint.documentation_deadline.isoformat() if sprint.documentation_deadline else None,
                "documentation_overdue": sprint.documentation_overdue,
            },
            "backlog": {
                "total_items": backlog_row[0],
                "total_points": backlog_row[1],
                "status_breakdown": status_breakdown,
                "priority_breakdown": priority_breakdown,
            },
            "compliance": {
                "rule_1_immutable_number": True,  # Enforced at DB level
                "rule_2_24h_documentation": not sprint.documentation_overdue,
                "rule_3_planning_approval": sprint.g_sprint_status == "passed",
                "rule_7_goal_alignment": bool(sprint.goal and sprint.phase and sprint.phase.objective),
                "rule_8_priorities_explicit": priority_breakdown.get("P0", 0) > 0,
            },
        }

    async def check_documentation_deadline(
        self,
        project_id: UUID,
    ) -> list[dict]:
        """
        Check all sprints in a project for documentation deadline violations.

        Returns list of sprints that are overdue for documentation.

        Args:
            project_id: Project UUID

        Returns:
            list of overdue sprint summaries
        """
        result = await self.db.execute(
            select(Sprint).where(
                Sprint.project_id == project_id,
                Sprint.status.in_(["active", "completed"]),
                Sprint.g_sprint_close_status == "pending",
            )
        )
        sprints = result.scalars().all()

        overdue_sprints = []
        for sprint in sprints:
            if sprint.documentation_overdue:
                overdue_sprints.append({
                    "sprint_id": str(sprint.id),
                    "number": sprint.number,
                    "name": sprint.name,
                    "end_date": sprint.end_date.isoformat() if sprint.end_date else None,
                    "documentation_deadline": sprint.documentation_deadline.isoformat() if sprint.documentation_deadline else None,
                    "hours_overdue": self._calculate_hours_overdue(sprint.documentation_deadline),
                    "action_required": "Complete G-Sprint-Close evaluation within 24h of sprint end (Rule #2)",
                })

        return overdue_sprints

    def _calculate_hours_overdue(self, deadline: Optional[datetime]) -> int:
        """Calculate how many hours past the deadline."""
        if not deadline:
            return 0
        if datetime.utcnow() <= deadline:
            return 0
        delta = datetime.utcnow() - deadline
        return int(delta.total_seconds() / 3600)
