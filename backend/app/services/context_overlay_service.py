"""
=========================================================================
Context Overlay Service - Dynamic Context Delivery
SDLC Orchestrator - Sprint 80 (AGENTS.md Integration)

Version: 1.0.0
Date: January 19, 2026
Status: ACTIVE - Sprint 80 Implementation
Authority: Backend Lead + CTO Approved
Reference: ADR-029-AGENTS-MD-Integration-Strategy
Reference: TDS-080-001 AGENTS.md Technical Design

Purpose:
- Generate dynamic context overlays for AI coding tools
- Deliver via PR comments, CLI, VS Code, API
- NOT committed to git (runtime only)
- Track delivery for audit trail

Layer B (Dynamic):
- Current SDLC stage and gate status
- Sprint context (goal, velocity, days remaining)
- Active constraints (strict mode, security reviews)
- Delivered via multiple channels, not file commits

Security:
- No secrets in overlay content
- Rate limiting on generation
- Audit trail for all deliveries

Zero Mock Policy: Production-ready service implementation
=========================================================================
"""

import logging
from datetime import datetime, date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.agents_md import ContextOverlay as ContextOverlayModel
from app.models.project import Project
from app.models.sprint import Sprint
from app.models.gate import Gate

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================


class SprintContext(BaseModel):
    """Sprint context for overlay."""

    id: Optional[UUID] = None
    number: Optional[int] = None
    goal: Optional[str] = None
    velocity: Optional[float] = None
    days_remaining: Optional[int] = None
    status: Optional[str] = None


class Constraint(BaseModel):
    """Active constraint affecting development."""

    type: str  # strict_mode, security_review, agpl, incident, custom
    severity: str  # info, warning, error
    message: str
    affected_files: List[str] = []


class ContextOverlay(BaseModel):
    """
    Dynamic context overlay (NOT committed to git).

    Delivered via:
    - PR comments (visible to Cursor, Copilot)
    - CLI output (`sdlc context`)
    - VS Code Extension panel
    - API response
    - GitHub Check Run output
    """

    id: Optional[UUID] = None
    project_id: UUID
    generated_at: datetime
    stage_name: Optional[str] = None
    gate_status: Optional[str] = None
    sprint: Optional[SprintContext] = None
    constraints: List[Constraint] = []
    strict_mode: bool = False

    class Config:
        from_attributes = True


# ============================================================================
# ContextOverlayService
# ============================================================================


class ContextOverlayService:
    """
    Generate dynamic context overlays for AI coding tools.

    Implements ADR-029 Dynamic Overlay layer:
    - NOT committed to git (delivered at runtime)
    - Contains current SDLC stage, sprint, and constraints
    - Formatted for PR comments, CLI, VS Code, API

    Delivery Channels:
    - GitHub PR Comment: Posted when PR is created/updated
    - GitHub Check Run: Included in check output
    - CLI: `sdlc context` command
    - VS Code: Extension panel injection
    - API: Direct response

    Usage:
        service = ContextOverlayService(db)
        overlay = await service.get_overlay(project_id)
        comment = service.format_pr_comment(overlay)
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize ContextOverlayService.

        Args:
            db: Database session
        """
        self.db = db

    async def get_overlay(
        self,
        project_id: UUID,
        trigger_type: str = "api",
        trigger_ref: Optional[str] = None,
        save_to_db: bool = True,
    ) -> ContextOverlay:
        """
        Generate context overlay for project.

        Args:
            project_id: Project UUID
            trigger_type: What triggered the overlay (pr_webhook, cli, api, scheduled, manual)
            trigger_ref: Reference for trigger (PR number, CLI session ID)
            save_to_db: Whether to save overlay record

        Returns:
            ContextOverlay with current project context
        """
        constraints: List[Constraint] = []

        # Get project
        project = await self._get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        # Get current stage and gate
        stage_name, gate_status = await self._get_stage_and_gate(project_id)

        # Determine strict mode (post-G3)
        strict_mode = self._is_strict_mode(gate_status)
        if strict_mode:
            constraints.append(Constraint(
                type="strict_mode",
                severity="warning",
                message="Post-G3: Only bug fixes allowed. Feature work blocked.",
            ))

        # Get active sprint
        sprint_context = await self._get_sprint_context(project_id)

        # Add AGPL constraint (always active for SDLC Orchestrator)
        constraints.append(Constraint(
            type="agpl",
            severity="info",
            message="AGPL: MinIO/Grafana network-only access (no SDK imports)",
        ))

        # Build overlay
        overlay = ContextOverlay(
            project_id=project_id,
            generated_at=datetime.utcnow(),
            stage_name=stage_name,
            gate_status=gate_status,
            sprint=sprint_context,
            constraints=constraints,
            strict_mode=strict_mode,
        )

        # Save to database for audit
        if save_to_db:
            saved = await self._save_overlay(
                overlay=overlay,
                trigger_type=trigger_type,
                trigger_ref=trigger_ref,
            )
            overlay.id = saved.id

        return overlay

    async def _get_project(self, project_id: UUID) -> Optional[Project]:
        """Get project by ID."""
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def _get_stage_and_gate(
        self,
        project_id: UUID,
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Get current stage and latest gate status.

        Sprint 136 - SSOT Principle:
        - First check ContextOverlay table for manually set stage/gate
        - Fallback to calculating from Gate table if no manual entry
        """
        # Sprint 136: Check for existing context overlay (SSOT)
        overlay_result = await self.db.execute(
            select(ContextOverlayModel)
            .where(ContextOverlayModel.project_id == project_id)
            .where(ContextOverlayModel.trigger_type == "manual")  # Manual entries have priority
            .order_by(ContextOverlayModel.generated_at.desc())
            .limit(1)
        )
        manual_overlay = overlay_result.scalar_one_or_none()

        if manual_overlay and manual_overlay.stage_name:
            # Use manually set values (SSOT principle)
            return manual_overlay.stage_name, manual_overlay.gate_status

        # Fallback: Calculate from gates
        # Find the highest approved gate first (most meaningful status)
        approved_result = await self.db.execute(
            select(Gate)
            .where(Gate.project_id == project_id)
            .where(Gate.status == "APPROVED")
            .where(Gate.deleted_at.is_(None))
            .order_by(Gate.created_at.desc())
            .limit(1)
        )
        approved_gate = approved_result.scalar_one_or_none()

        if approved_gate:
            # Use gate_name directly (e.g. "G3", "G0.2", "G2.1: Architecture Review")
            gate_id = approved_gate.gate_name.split(":")[0].strip() if approved_gate.gate_name else "G0"
            stage_name = approved_gate.stage or "BUILD"
            gate_status = f"{gate_id} PASSED"
            return stage_name, gate_status

        # No approved gates - check for any pending/in-progress gate
        result = await self.db.execute(
            select(Gate)
            .where(Gate.project_id == project_id)
            .where(Gate.deleted_at.is_(None))
            .order_by(Gate.created_at.desc())
            .limit(1)
        )
        gate = result.scalar_one_or_none()

        if gate:
            gate_id = gate.gate_name.split(":")[0].strip() if gate.gate_name else "G0"
            # Map DB status to display status
            status_display = {
                "APPROVED": "PASSED",
                "REJECTED": "FAILED",
                "PENDING_APPROVAL": "PENDING",
                "IN_PROGRESS": "IN PROGRESS",
                "DRAFT": "DRAFT",
                "ARCHIVED": "ARCHIVED",
            }.get(gate.status, "PENDING")
            stage_name = gate.stage or "DISCOVER"
            gate_status = f"{gate_id} {status_display}"
            return stage_name, gate_status

        return "Stage 00 (DISCOVER)", "No gates evaluated"

    def _is_strict_mode(self, gate_status: Optional[str]) -> bool:
        """Determine if project is in strict mode (post-G3)."""
        if not gate_status:
            return False

        # Check if G3 or later gates have passed
        strict_gates = ["G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10"]
        for gate in strict_gates:
            if gate in gate_status and "PASSED" in gate_status:
                return True

        return False

    async def _get_sprint_context(
        self,
        project_id: UUID,
    ) -> Optional[SprintContext]:
        """Get active sprint context."""
        result = await self.db.execute(
            select(Sprint)
            .where(Sprint.project_id == project_id)
            .where(Sprint.status == "active")
            .order_by(Sprint.number.desc())
            .limit(1)
        )
        sprint = result.scalar_one_or_none()

        if sprint:
            days_remaining = None
            if sprint.end_date:
                delta = sprint.end_date - date.today()
                days_remaining = max(0, delta.days)

            return SprintContext(
                id=sprint.id,
                number=sprint.number,
                goal=sprint.goal,
                velocity=sprint.velocity_target,
                days_remaining=days_remaining,
                status=sprint.status,
            )

        return None

    async def _save_overlay(
        self,
        overlay: ContextOverlay,
        trigger_type: str,
        trigger_ref: Optional[str],
    ) -> ContextOverlayModel:
        """Save overlay record to database."""
        record = ContextOverlayModel(
            project_id=overlay.project_id,
            stage_name=overlay.stage_name,
            gate_status=overlay.gate_status,
            sprint_id=overlay.sprint.id if overlay.sprint else None,
            sprint_number=overlay.sprint.number if overlay.sprint else None,
            sprint_goal=overlay.sprint.goal if overlay.sprint else None,
            constraints=[c.dict() for c in overlay.constraints],
            strict_mode=overlay.strict_mode,
            generated_at=overlay.generated_at,
            trigger_type=trigger_type,
            trigger_ref=trigger_ref,
        )

        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)

        return record

    async def update_delivery_status(
        self,
        overlay_id: UUID,
        delivered_to_pr: bool = False,
        delivered_to_check_run: bool = False,
        pr_comment_id: Optional[int] = None,
        check_run_id: Optional[int] = None,
    ) -> None:
        """Update delivery status of overlay."""
        result = await self.db.execute(
            select(ContextOverlayModel).where(ContextOverlayModel.id == overlay_id)
        )
        record = result.scalar_one_or_none()

        if record:
            if delivered_to_pr:
                record.delivered_to_pr = True
            if delivered_to_check_run:
                record.delivered_to_check_run = True
            if pr_comment_id:
                record.pr_comment_id = pr_comment_id
            if check_run_id:
                record.check_run_id = check_run_id

            await self.db.commit()

    # =========================================================================
    # Formatting Methods
    # =========================================================================

    def format_pr_comment(self, overlay: ContextOverlay) -> str:
        """
        Format overlay as PR comment for AI tools.

        Uses structured HTML comments for parsing by automation.
        Visible to Cursor, Copilot, Claude Code via PR conversation.

        Args:
            overlay: Context overlay to format

        Returns:
            Markdown formatted PR comment
        """
        timestamp = overlay.generated_at.strftime('%b %d, %Y %H:%M UTC')

        # Stage and sprint info
        stage_text = overlay.stage_name or "Unknown"
        gate_text = overlay.gate_status or "N/A"

        sprint_text = "N/A"
        if overlay.sprint:
            sprint_text = f"Sprint {overlay.sprint.number}"
            if overlay.sprint.goal:
                # Truncate long goals
                goal = overlay.sprint.goal[:50] + "..." if len(overlay.sprint.goal) > 50 else overlay.sprint.goal
                sprint_text += f" - {goal}"
            if overlay.sprint.days_remaining is not None:
                sprint_text += f" ({overlay.sprint.days_remaining}d left)"

        # Constraints
        constraints_text = self._format_constraints_markdown(overlay.constraints)

        # Strict mode banner
        strict_banner = ""
        if overlay.strict_mode:
            strict_banner = "\n> 🔒 **STRICT MODE ACTIVE**: Only bug fixes allowed.\n"

        return f"""<!-- SDLC-CONTEXT-START -->
## 🎯 SDLC Context ({timestamp})
{strict_banner}
| Stage | Gate | Sprint |
|-------|------|--------|
| {stage_text} | {gate_text} | {sprint_text} |

### Active Constraints
{constraints_text}
---
*Generated by [SDLC Orchestrator](https://sdlc.dev) • [View Dashboard](#)*
<!-- SDLC-CONTEXT-END -->"""

    def _format_constraints_markdown(self, constraints: List[Constraint]) -> str:
        """Format constraints as markdown list."""
        if not constraints:
            return "- None\n"

        lines = []
        for c in constraints:
            icon = {"info": "ℹ️", "warning": "⚠️", "error": "🔴"}.get(c.severity, "•")
            type_name = c.type.replace('_', ' ').title()
            lines.append(f"- {icon} **{type_name}**: {c.message}")

            # Add affected files (limit to 3)
            if c.affected_files:
                for f in c.affected_files[:3]:
                    lines.append(f"  - `{f}`")
                if len(c.affected_files) > 3:
                    lines.append(f"  - ... and {len(c.affected_files) - 3} more")

        return "\n".join(lines) + "\n"

    def format_cli_output(self, overlay: ContextOverlay) -> str:
        """
        Format overlay for CLI terminal output.

        Args:
            overlay: Context overlay to format

        Returns:
            Terminal-formatted string with box drawing
        """
        lines = [
            "",
            "┌─────────────────────────────────────────────────────────┐",
            "│                   SDLC CONTEXT                          │",
            "├─────────────────────────────────────────────────────────┤",
        ]

        # Stage
        stage = overlay.stage_name or "Unknown"
        lines.append(f"│  📍 Stage: {stage:<45} │")

        # Gate
        gate = overlay.gate_status or "N/A"
        lines.append(f"│  🚪 Gate:  {gate:<45} │")

        # Strict mode
        if overlay.strict_mode:
            lines.append("│  🔒 MODE:  STRICT (bug fixes only)                     │")

        # Sprint
        if overlay.sprint:
            sprint_info = f"Sprint {overlay.sprint.number}"
            if overlay.sprint.days_remaining is not None:
                sprint_info += f" ({overlay.sprint.days_remaining}d left)"
            lines.append(f"│  📅 Sprint: {sprint_info:<43} │")

        lines.append("├─────────────────────────────────────────────────────────┤")
        lines.append("│  📋 Constraints:                                         │")

        # Constraints
        if overlay.constraints:
            for c in overlay.constraints:
                icon = {"info": "ℹ️", "warning": "⚠️", "error": "🔴"}.get(c.severity, "•")
                msg = c.message[:47] + "..." if len(c.message) > 50 else c.message
                lines.append(f"│    {icon} {msg:<51} │")
        else:
            lines.append("│    None                                                 │")

        lines.append("└─────────────────────────────────────────────────────────┘")
        lines.append("")

        return "\n".join(lines)

    def format_check_run_output(self, overlay: ContextOverlay) -> str:
        """
        Format overlay for GitHub Check Run output.

        Args:
            overlay: Context overlay to format

        Returns:
            Markdown formatted for Check Run summary
        """
        return self.format_pr_comment(overlay)

    def format_json(self, overlay: ContextOverlay) -> dict:
        """
        Format overlay as JSON for API/VS Code.

        Args:
            overlay: Context overlay to format

        Returns:
            Dictionary representation
        """
        return {
            "id": str(overlay.id) if overlay.id else None,
            "project_id": str(overlay.project_id),
            "generated_at": overlay.generated_at.isoformat(),
            "stage_name": overlay.stage_name,
            "gate_status": overlay.gate_status,
            "sprint": overlay.sprint.dict() if overlay.sprint else None,
            "constraints": [c.dict() for c in overlay.constraints],
            "strict_mode": overlay.strict_mode,
        }

    def format_vscode_panel(self, overlay: ContextOverlay) -> dict:
        """
        Format overlay for VS Code Extension panel.

        Args:
            overlay: Context overlay to format

        Returns:
            Structured data for VS Code rendering
        """
        return {
            "type": "sdlc_context",
            "version": "1.0.0",
            "data": {
                "stage": {
                    "name": overlay.stage_name,
                    "gate": overlay.gate_status,
                    "strict_mode": overlay.strict_mode,
                },
                "sprint": {
                    "number": overlay.sprint.number if overlay.sprint else None,
                    "goal": overlay.sprint.goal if overlay.sprint else None,
                    "days_remaining": overlay.sprint.days_remaining if overlay.sprint else None,
                } if overlay.sprint else None,
                "constraints": [
                    {
                        "type": c.type,
                        "severity": c.severity,
                        "message": c.message,
                        "icon": {"info": "info", "warning": "warning", "error": "error"}.get(c.severity, "info"),
                    }
                    for c in overlay.constraints
                ],
            },
            "generated_at": overlay.generated_at.isoformat(),
        }

    # =========================================================================
    # History Methods
    # =========================================================================

    async def get_history(
        self,
        project_id: UUID,
        limit: int = 10,
    ) -> List[ContextOverlayModel]:
        """Get overlay history for project."""
        result = await self.db.execute(
            select(ContextOverlayModel)
            .where(ContextOverlayModel.project_id == project_id)
            .order_by(ContextOverlayModel.generated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_pr(
        self,
        project_id: UUID,
        pr_number: int,
    ) -> Optional[ContextOverlayModel]:
        """Get overlay for specific PR."""
        result = await self.db.execute(
            select(ContextOverlayModel)
            .where(ContextOverlayModel.project_id == project_id)
            .where(ContextOverlayModel.trigger_ref == f"PR#{pr_number}")
            .order_by(ContextOverlayModel.generated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
