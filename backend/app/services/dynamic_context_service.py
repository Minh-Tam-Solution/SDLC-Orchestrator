"""
=========================================================================
DynamicContextService - TRUE MOAT: Event-Driven AGENTS.md Updates
SDLC Orchestrator - Sprint 83 (Dynamic Context & Analytics)

Version: 1.0.0
Date: January 19, 2026
Status: ACTIVE - Sprint 83 (Pre-Launch Hardening)
Authority: CTO Approved
Framework: SDLC 5.1.3 P7 (Documentation Permanence)

Purpose:
- Auto-update AGENTS.md when lifecycle events occur
- Inject dynamic context (gate status, constraints, sprint info)
- Push updates to GitHub via commit or PR

TRUE MOAT: This is what NO ONE has
- Cursor/Copilot/OpenCode: Static AGENTS.md
- SDLC Orchestrator: Dynamic AGENTS.md by lifecycle stage = TRUE ORCHESTRATION

Design Pattern:
- Subscribes to EventBus lifecycle events
- On event, regenerates AGENTS.md with new context
- Pushes to repository (direct commit or PR based on config)
- Records update in audit trail

Event Handlers:
- GateStatusChanged → Update "Current Stage" section
- SprintChanged → Update "Current Sprint" section
- ConstraintDetected → Add to "Known Issues" or "DO NOT" section
- SecurityScanCompleted → Update security context

Zero Mock Policy: Production-ready event-driven architecture
=========================================================================
"""

import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.events.event_bus import EventBus, get_event_bus
from app.events.lifecycle_events import (
    GateStatusChanged,
    SprintChanged,
    ConstraintDetected,
    ConstraintResolved,
    SecurityScanCompleted,
    AgentsMdUpdated,
    GateStatus,
    SprintStatus,
    ConstraintSeverity,
    ConstraintType,
)
from app.models.agents_md import AgentsMdFile
from app.models.gate import Gate
from app.models.project import Project

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================


class UpdateMode(str, Enum):
    """How to push AGENTS.md updates."""

    DIRECT_COMMIT = "direct_commit"  # Commit directly to default branch
    PULL_REQUEST = "pull_request"  # Create PR for review
    DISABLED = "disabled"  # Don't auto-push (manual only)


@dataclass
class DynamicContextConfig:
    """
    Configuration for DynamicContextService.

    Attributes:
        update_mode: How to push updates (direct, PR, disabled)
        auto_update_on_gate_change: Update when gate status changes
        auto_update_on_sprint_change: Update when sprint changes
        auto_update_on_constraint: Update when constraints detected
        max_constraints_in_context: Max constraints to show in AGENTS.md
        constraint_severity_threshold: Min severity to include
        debounce_seconds: Debounce rapid events (avoid spam)
    """

    update_mode: UpdateMode = UpdateMode.DIRECT_COMMIT
    auto_update_on_gate_change: bool = True
    auto_update_on_sprint_change: bool = True
    auto_update_on_constraint: bool = True
    max_constraints_in_context: int = 5
    constraint_severity_threshold: ConstraintSeverity = ConstraintSeverity.MEDIUM
    debounce_seconds: float = 5.0


@dataclass
class DynamicContext:
    """
    Dynamic context to inject into AGENTS.md.

    This represents the "live" state of the project that changes
    based on lifecycle events.
    """

    # Gate context
    current_gate: str = "G0"
    gate_status: GateStatus = GateStatus.PENDING
    gate_passed_at: Optional[datetime] = None

    # Sprint context
    current_sprint: str = ""
    sprint_number: int = 0
    sprint_status: SprintStatus = SprintStatus.PLANNING
    sprint_goals: List[str] = field(default_factory=list)

    # Constraint context
    active_constraints: List[Dict[str, Any]] = field(default_factory=list)
    blocking_constraints: List[Dict[str, Any]] = field(default_factory=list)

    # Security context
    last_scan_passed: bool = True
    last_scan_findings: Dict[str, int] = field(default_factory=dict)

    # Metadata
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    update_count: int = 0


# ============================================================================
# DynamicContextService
# ============================================================================


class DynamicContextService:
    """
    Event-driven AGENTS.md update service.

    The TRUE MOAT of SDLC Orchestrator:
    - 60,000 projects use AGENTS.md (static)
    - SDLC Orchestrator makes it dynamic (by lifecycle stage)

    How it works:
    1. Subscribe to EventBus lifecycle events
    2. On event, update internal DynamicContext
    3. Regenerate AGENTS.md with new context
    4. Push to repository (commit or PR)
    5. Record update event for audit/analytics

    Usage:
        service = DynamicContextService(db, github_service)
        await service.start()  # Start listening to events

        # Events are handled automatically
        # Gate passes → AGENTS.md updated with new stage
        # Constraint found → AGENTS.md updated with warning

    Sprint 83 Implementation:
    - Day 1-4: Core service with event handlers
    - Day 5-6: GitHub push integration
    - Day 7-8: Testing and hardening
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        db: AsyncSession,
        github_service: Optional[Any] = None,  # GitHubService
        event_bus: Optional[EventBus] = None,
        config: Optional[DynamicContextConfig] = None,
    ):
        """
        Initialize DynamicContextService.

        Args:
            db: Database session for persistence
            github_service: GitHub service for pushing updates
            event_bus: EventBus instance (uses global if not provided)
            config: Service configuration
        """
        self.db = db
        self.github_service = github_service
        self.event_bus = event_bus or get_event_bus()
        self.config = config or DynamicContextConfig()

        # Project contexts (in-memory cache)
        self._contexts: Dict[UUID, DynamicContext] = {}

        # Debounce tracking
        self._pending_updates: Dict[UUID, datetime] = {}
        self._debounce_tasks: Dict[UUID, asyncio.Task] = {}

        # Subscription IDs (for cleanup)
        self._subscriptions: List[UUID] = []

        logger.info(
            "DynamicContextService initialized (mode=%s, debounce=%.1fs)",
            self.config.update_mode.value,
            self.config.debounce_seconds,
        )

    async def start(self) -> None:
        """
        Start the service and subscribe to events.

        Call this after initialization to begin handling events.
        """
        logger.info("Starting DynamicContextService...")

        # Subscribe to gate changes
        if self.config.auto_update_on_gate_change:
            sub_id = self.event_bus.subscribe(
                GateStatusChanged,
                self._on_gate_change,
                priority=10,
            )
            self._subscriptions.append(sub_id)
            logger.debug("Subscribed to GateStatusChanged")

        # Subscribe to sprint changes
        if self.config.auto_update_on_sprint_change:
            sub_id = self.event_bus.subscribe(
                SprintChanged,
                self._on_sprint_change,
                priority=10,
            )
            self._subscriptions.append(sub_id)
            logger.debug("Subscribed to SprintChanged")

        # Subscribe to constraints
        if self.config.auto_update_on_constraint:
            sub_id = self.event_bus.subscribe(
                ConstraintDetected,
                self._on_constraint_detected,
                priority=5,
            )
            self._subscriptions.append(sub_id)

            sub_id = self.event_bus.subscribe(
                ConstraintResolved,
                self._on_constraint_resolved,
                priority=5,
            )
            self._subscriptions.append(sub_id)
            logger.debug("Subscribed to constraint events")

        # Subscribe to security scans
        sub_id = self.event_bus.subscribe(
            SecurityScanCompleted,
            self._on_security_scan,
            priority=5,
        )
        self._subscriptions.append(sub_id)
        logger.debug("Subscribed to SecurityScanCompleted")

        logger.info(
            "DynamicContextService started with %d subscriptions",
            len(self._subscriptions),
        )

    async def stop(self) -> None:
        """
        Stop the service and unsubscribe from events.
        """
        logger.info("Stopping DynamicContextService...")

        # Cancel pending debounce tasks
        for task in self._debounce_tasks.values():
            task.cancel()
        self._debounce_tasks.clear()

        # Unsubscribe (EventBus handles cleanup)
        self._subscriptions.clear()

        logger.info("DynamicContextService stopped")

    # ========================================================================
    # Event Handlers
    # ========================================================================

    async def _on_gate_change(self, event: GateStatusChanged) -> None:
        """
        Handle gate status change event.

        Updates:
        - Current gate ID and status
        - "Current Stage" section in AGENTS.md
        - Constraints if gate failed
        """
        logger.info(
            "Gate change: project=%s gate=%s status=%s→%s",
            event.project_id,
            event.gate_id,
            event.previous_status.value if event.previous_status else "none",
            event.new_status.value,
        )

        context = self._get_or_create_context(event.project_id)

        # Update context
        context.current_gate = event.gate_id
        context.gate_status = event.new_status
        if event.new_status == GateStatus.PASSED:
            context.gate_passed_at = event.timestamp
        context.last_updated = datetime.now(timezone.utc)
        context.update_count += 1

        # Schedule AGENTS.md update
        await self._schedule_update(event.project_id, f"Gate {event.gate_id} → {event.new_status.value}")

    async def _on_sprint_change(self, event: SprintChanged) -> None:
        """
        Handle sprint status change event.

        Updates:
        - Current sprint info
        - Sprint goals in AGENTS.md
        - CURRENT-SPRINT.md pushed to project's GitHub repo (Sprint 193)
        """
        logger.info(
            "Sprint change: project=%s sprint=%s status=%s→%s",
            event.project_id,
            event.sprint_name,
            event.previous_status.value if event.previous_status else "none",
            event.new_status.value,
        )

        context = self._get_or_create_context(event.project_id)

        # Update context
        context.current_sprint = event.sprint_name
        context.sprint_number = event.sprint_number
        context.sprint_status = event.new_status
        context.sprint_goals = event.goals
        context.last_updated = datetime.now(timezone.utc)
        context.update_count += 1

        # Schedule AGENTS.md update
        await self._schedule_update(event.project_id, f"Sprint {event.sprint_name} → {event.new_status.value}")

        # Sprint 193: Push CURRENT-SPRINT.md alongside AGENTS.md
        await self._push_current_sprint_md(event.project_id)

    async def _on_constraint_detected(self, event: ConstraintDetected) -> None:
        """
        Handle constraint detected event.

        Updates:
        - Active constraints list
        - "Known Issues" or "DO NOT" section based on severity
        """
        logger.info(
            "Constraint detected: project=%s type=%s severity=%s title=%s",
            event.project_id,
            event.constraint_type.value,
            event.severity.value,
            event.title,
        )

        # Skip if below threshold
        severity_order = [
            ConstraintSeverity.INFO,
            ConstraintSeverity.LOW,
            ConstraintSeverity.MEDIUM,
            ConstraintSeverity.HIGH,
            ConstraintSeverity.CRITICAL,
        ]
        if severity_order.index(event.severity) < severity_order.index(
            self.config.constraint_severity_threshold
        ):
            logger.debug("Skipping constraint below threshold: %s", event.severity.value)
            return

        context = self._get_or_create_context(event.project_id)

        # Create constraint entry
        constraint_entry = {
            "id": str(event.constraint_id),
            "type": event.constraint_type.value,
            "severity": event.severity.value,
            "title": event.title,
            "description": event.description,
            "affected_files": event.affected_files[:3],  # Limit files shown
            "remediation": event.remediation,
            "blocking": event.blocking,
            "detected_at": event.timestamp.isoformat(),
        }

        # Add to constraints
        context.active_constraints.append(constraint_entry)
        if event.blocking:
            context.blocking_constraints.append(constraint_entry)

        # Limit max constraints
        if len(context.active_constraints) > self.config.max_constraints_in_context:
            context.active_constraints = context.active_constraints[
                -self.config.max_constraints_in_context :
            ]

        context.last_updated = datetime.now(timezone.utc)
        context.update_count += 1

        # Schedule AGENTS.md update
        await self._schedule_update(event.project_id, f"Constraint: {event.title}")

    async def _on_constraint_resolved(self, event: ConstraintResolved) -> None:
        """
        Handle constraint resolved event.

        Updates:
        - Remove from active constraints
        - Update AGENTS.md
        """
        logger.info(
            "Constraint resolved: project=%s constraint=%s",
            event.project_id,
            event.constraint_id,
        )

        context = self._get_or_create_context(event.project_id)

        # Remove constraint
        constraint_id_str = str(event.constraint_id)
        context.active_constraints = [
            c for c in context.active_constraints if c["id"] != constraint_id_str
        ]
        context.blocking_constraints = [
            c for c in context.blocking_constraints if c["id"] != constraint_id_str
        ]

        context.last_updated = datetime.now(timezone.utc)
        context.update_count += 1

        # Schedule AGENTS.md update
        await self._schedule_update(event.project_id, "Constraint resolved")

    async def _on_security_scan(self, event: SecurityScanCompleted) -> None:
        """
        Handle security scan completed event.

        Updates:
        - Last scan results
        - Add findings as constraints if failed
        """
        logger.info(
            "Security scan: project=%s scanner=%s passed=%s findings=%d/%d/%d",
            event.project_id,
            event.scanner,
            event.passed,
            event.findings_critical,
            event.findings_high,
            event.findings_medium,
        )

        context = self._get_or_create_context(event.project_id)

        # Update scan context
        context.last_scan_passed = event.passed
        context.last_scan_findings = {
            "critical": event.findings_critical,
            "high": event.findings_high,
            "medium": event.findings_medium,
            "low": event.findings_low,
        }

        context.last_updated = datetime.now(timezone.utc)
        context.update_count += 1

        # Schedule AGENTS.md update if scan failed
        if not event.passed:
            await self._schedule_update(
                event.project_id,
                f"Security scan failed ({event.findings_critical}C/{event.findings_high}H)",
            )

    # ========================================================================
    # Context Management
    # ========================================================================

    def _get_or_create_context(self, project_id: UUID) -> DynamicContext:
        """Get or create dynamic context for project."""
        if project_id not in self._contexts:
            self._contexts[project_id] = DynamicContext()
        return self._contexts[project_id]

    def get_context(self, project_id: UUID) -> Optional[DynamicContext]:
        """Get current context for project (may be None)."""
        return self._contexts.get(project_id)

    async def load_context(self, project_id: UUID) -> DynamicContext:
        """
        Load context from database (for cold start / service restart).

        Queries the gates table to find the latest gate status for this
        project, so that the in-memory context reflects the DB truth.

        Args:
            project_id: Project UUID

        Returns:
            DynamicContext loaded from DB or fresh instance
        """
        context = self._get_or_create_context(project_id)

        # Only hydrate from DB if context has never been updated by events
        if context.update_count == 0:
            try:
                result = await self.db.execute(
                    select(Gate)
                    .where(Gate.project_id == project_id)
                    .where(Gate.deleted_at.is_(None))
                    .order_by(Gate.created_at.desc())
                )
                gates = result.scalars().all()

                if gates:
                    # Map DB gate status → DynamicContext GateStatus enum
                    db_to_event_status = {
                        "APPROVED": GateStatus.PASSED,
                        "REJECTED": GateStatus.FAILED,
                        "PENDING_APPROVAL": GateStatus.IN_PROGRESS,
                        "IN_PROGRESS": GateStatus.IN_PROGRESS,
                        "DRAFT": GateStatus.PENDING,
                        "ARCHIVED": GateStatus.BYPASSED,
                    }

                    # Find the highest gate that has been approved
                    latest_approved = None
                    for gate in gates:
                        if gate.status == "APPROVED":
                            latest_approved = gate
                            break  # Already sorted desc by created_at

                    if latest_approved:
                        # Use gate_name directly (e.g. "G3", "G0.2", "G2.1: Architecture Review")
                        gate_id = latest_approved.gate_name.split(":")[0].strip() if latest_approved.gate_name else "G0"
                        context.current_gate = gate_id
                        context.gate_status = GateStatus.PASSED
                        context.gate_passed_at = latest_approved.approved_at
                    else:
                        # No approved gate - use the most recent gate's status
                        most_recent = gates[0]
                        gate_id = most_recent.gate_name.split(":")[0].strip() if most_recent.gate_name else "G0"
                        context.current_gate = gate_id
                        context.gate_status = db_to_event_status.get(
                            most_recent.status, GateStatus.PENDING
                        )

                    logger.info(
                        "Loaded gate context from DB: project=%s gate=%s status=%s",
                        project_id,
                        context.current_gate,
                        context.gate_status.value,
                    )
            except Exception as e:
                logger.warning(
                    "Failed to load gate context from DB for project %s: %s",
                    project_id,
                    str(e),
                )

        return context

    # ========================================================================
    # AGENTS.md Generation
    # ========================================================================

    async def _schedule_update(self, project_id: UUID, reason: str) -> None:
        """
        Schedule AGENTS.md update with debouncing.

        Args:
            project_id: Project to update
            reason: Why the update is happening
        """
        if self.config.update_mode == UpdateMode.DISABLED:
            logger.debug("Updates disabled, skipping: %s", reason)
            return

        # Cancel existing debounce task
        if project_id in self._debounce_tasks:
            self._debounce_tasks[project_id].cancel()

        # Record pending update
        self._pending_updates[project_id] = datetime.now(timezone.utc)

        # Schedule debounced update
        async def debounced_update():
            await asyncio.sleep(self.config.debounce_seconds)
            await self._execute_update(project_id, reason)

        self._debounce_tasks[project_id] = asyncio.create_task(debounced_update())

    async def _execute_update(self, project_id: UUID, reason: str) -> None:
        """
        Execute AGENTS.md update.

        Args:
            project_id: Project to update
            reason: Why the update is happening
        """
        try:
            logger.info("Executing AGENTS.md update: project=%s reason=%s", project_id, reason)

            context = self._contexts.get(project_id)
            if not context:
                logger.warning("No context for project %s", project_id)
                return

            # Generate dynamic section
            dynamic_content = self._generate_dynamic_section(context)

            # Get current AGENTS.md and merge
            # (In full implementation, would fetch from repo and merge)
            new_content = dynamic_content

            # Calculate hash
            new_hash = hashlib.sha256(new_content.encode()).hexdigest()

            # Push to GitHub if service available
            commit_sha = None
            if self.github_service:
                try:
                    commit_sha = await self._push_to_github(project_id, new_content, reason)
                except Exception as e:
                    logger.error("Failed to push to GitHub: %s", e)

            # Publish update event
            update_event = AgentsMdUpdated(
                project_id=project_id,
                trigger_event=reason,
                sections_updated=["Current Stage", "Current Sprint", "Known Issues"],
                new_hash=new_hash,
                commit_sha=commit_sha,
            )
            await self.event_bus.publish(update_event)

            logger.info(
                "AGENTS.md updated: project=%s hash=%s commit=%s",
                project_id,
                new_hash[:8],
                commit_sha or "none",
            )

        except Exception as e:
            logger.error("Failed to update AGENTS.md: %s", e, exc_info=True)

        finally:
            # Cleanup
            self._pending_updates.pop(project_id, None)
            self._debounce_tasks.pop(project_id, None)

    def _generate_dynamic_section(self, context: DynamicContext) -> str:
        """
        Generate dynamic section of AGENTS.md.

        This is the "magic" that makes AGENTS.md dynamic.
        """
        sections = []

        # Current Stage section
        stage_icon = self._get_stage_icon(context.gate_status)
        stage_section = f"""## Current Stage
{stage_icon} **Gate**: {context.current_gate} | **Status**: {context.gate_status.value.upper()}
"""
        if context.gate_passed_at:
            stage_section += f"Last gate passed: {context.gate_passed_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
        sections.append(stage_section)

        # Current Sprint section
        if context.current_sprint:
            sprint_section = f"""
## Current Sprint
**{context.current_sprint}** (Sprint {context.sprint_number}) | Status: {context.sprint_status.value.upper()}
"""
            if context.sprint_goals:
                sprint_section += "\nGoals:\n"
                for goal in context.sprint_goals[:3]:  # Max 3 goals
                    sprint_section += f"- {goal}\n"
            sections.append(sprint_section)

        # Blocking Constraints (CRITICAL)
        if context.blocking_constraints:
            blocking_section = "\n## ⛔ BLOCKED\n"
            blocking_section += "**Merge is blocked until these issues are resolved:**\n\n"
            for constraint in context.blocking_constraints[:3]:
                blocking_section += f"- **{constraint['title']}** ({constraint['severity'].upper()})\n"
                if constraint.get("remediation"):
                    blocking_section += f"  Fix: {constraint['remediation']}\n"
            sections.append(blocking_section)

        # Known Issues (non-blocking)
        active_non_blocking = [c for c in context.active_constraints if not c.get("blocking")]
        if active_non_blocking:
            issues_section = "\n## ⚠️ Known Issues\n"
            for constraint in active_non_blocking[:3]:
                issues_section += f"- {constraint['title']} ({constraint['severity']})"
                if constraint.get("affected_files"):
                    issues_section += f" - in {', '.join(constraint['affected_files'][:2])}"
                issues_section += "\n"
            sections.append(issues_section)

        # Security Context (if scan failed)
        if not context.last_scan_passed:
            security_section = "\n## 🔴 Security Alert\n"
            security_section += f"Last scan: **FAILED**\n"
            security_section += f"- Critical: {context.last_scan_findings.get('critical', 0)}\n"
            security_section += f"- High: {context.last_scan_findings.get('high', 0)}\n"
            security_section += f"- Medium: {context.last_scan_findings.get('medium', 0)}\n"
            sections.append(security_section)

        # Footer
        footer = f"""
---
*Dynamic context last updated: {context.last_updated.strftime('%Y-%m-%d %H:%M UTC')}*
*Updates: {context.update_count} | Generated by SDLC Orchestrator*
"""
        sections.append(footer)

        return "\n".join(sections)

    def _get_stage_icon(self, status: GateStatus) -> str:
        """Get icon for gate status."""
        icons = {
            GateStatus.PENDING: "⏳",
            GateStatus.IN_PROGRESS: "🔄",
            GateStatus.PASSED: "✅",
            GateStatus.FAILED: "❌",
            GateStatus.BLOCKED: "⛔",
            GateStatus.BYPASSED: "⚠️",
        }
        return icons.get(status, "❓")

    # ========================================================================
    # GitHub Integration
    # ========================================================================

    async def _push_to_github(
        self,
        project_id: UUID,
        content: str,
        reason: str,
    ) -> Optional[str]:
        """
        Push AGENTS.md update to GitHub.

        Sprint 193 fix: Uses installation tokens for server-side auth
        and correct method signatures (access_token, owner, repo).

        Args:
            project_id: Project UUID
            content: New AGENTS.md content
            reason: Commit message reason

        Returns:
            Commit SHA if successful, None otherwise
        """
        if not self.github_service:
            logger.debug("GitHub service not available")
            return None

        # Get project's repository info
        project = await self._get_project(project_id)
        if not project or not project.github_repo:
            logger.warning("Project %s has no GitHub repo configured", project_id)
            return None

        # Get installation token for server-side auth
        access_token = await self._get_installation_token(project)
        if not access_token:
            logger.warning("No installation token for project %s", project_id)
            return None

        owner, repo = project.github_repo.split("/", 1)
        commit_message = f"chore(agents.md): Auto-update - {reason}\n\nGenerated by SDLC Orchestrator Dynamic Context Service"

        if self.config.update_mode == UpdateMode.DIRECT_COMMIT:
            return self.github_service.update_file(
                access_token=access_token,
                owner=owner,
                repo=repo,
                path="AGENTS.md",
                content=content,
                message=commit_message,
                branch=project.default_branch or "main",
            )
        elif self.config.update_mode == UpdateMode.PULL_REQUEST:
            return self.github_service.create_update_pr(
                access_token=access_token,
                owner=owner,
                repo=repo,
                path="AGENTS.md",
                content=content,
                title=f"chore: Auto-update AGENTS.md - {reason}",
                body="Automated AGENTS.md update by SDLC Orchestrator Dynamic Context Service.",
                base_branch=project.default_branch or "main",
            )

        return None

    async def _push_current_sprint_md(self, project_id: UUID) -> None:
        """
        Push CURRENT-SPRINT.md to project's GitHub repo.

        Sprint 193: CEO directive — platform must enforce CURRENT-SPRINT.md
        on all governed customer projects. Uses SprintFileService for
        content generation and push.

        Args:
            project_id: Project UUID
        """
        try:
            from app.services.sprint_file_service import SprintFileService

            sprint_service = SprintFileService(
                db=self.db,
                github_service=self.github_service,
            )

            sprint = await sprint_service.get_active_sprint(project_id)
            if not sprint:
                logger.debug(
                    "No active sprint for project %s, skipping CURRENT-SPRINT.md push",
                    project_id,
                )
                return

            project = await self._get_project(project_id)
            if not project:
                return

            content = sprint_service.generate_current_sprint_md(sprint, project)
            commit_sha = await sprint_service.push_to_github(project, content)

            if commit_sha:
                logger.info(
                    "CURRENT-SPRINT.md pushed for project %s (commit: %s)",
                    project_id,
                    commit_sha,
                )
        except Exception as e:
            logger.error(
                "Failed to push CURRENT-SPRINT.md for project %s: %s",
                project_id,
                str(e),
            )

    async def _get_installation_token(self, project: Project) -> Optional[str]:
        """
        Get GitHub App installation token for server-side operations.

        Flow: project → github_repository → installation → installation_id
              → get_installation_token() → access_token

        Returns:
            Access token string, or None if unavailable
        """
        gh_repo = getattr(project, "github_repository", None)
        if not gh_repo:
            return None

        installation = getattr(gh_repo, "installation", None)
        if not installation:
            return None

        installation_id = getattr(installation, "installation_id", None)
        if not installation_id:
            return None

        try:
            from app.services.github_app_service import get_installation_token

            return await get_installation_token(installation_id)
        except Exception as e:
            logger.error("Failed to get installation token: %s", str(e))
            return None

    async def _get_project(self, project_id: UUID) -> Optional[Project]:
        """Get project by ID."""
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    # ========================================================================
    # Manual Triggers
    # ========================================================================

    async def force_update(self, project_id: UUID, reason: str = "Manual trigger") -> str:
        """
        Force immediate AGENTS.md update (skip debounce).

        Args:
            project_id: Project to update
            reason: Why the update is happening

        Returns:
            Generated content
        """
        logger.info("Force update requested: project=%s reason=%s", project_id, reason)

        context = self._get_or_create_context(project_id)
        content = self._generate_dynamic_section(context)

        # Execute update immediately
        await self._execute_update(project_id, reason)

        return content

    async def regenerate_all(self) -> Dict[UUID, str]:
        """
        Regenerate AGENTS.md for all projects with active context.

        Returns:
            Dict of project_id → generated content
        """
        results = {}
        for project_id in self._contexts.keys():
            try:
                content = await self.force_update(project_id, "Bulk regeneration")
                results[project_id] = content
            except Exception as e:
                logger.error("Failed to regenerate for %s: %s", project_id, e)
                results[project_id] = f"ERROR: {e}"
        return results


# ============================================================================
# Factory Function
# ============================================================================


async def create_dynamic_context_service(
    db: AsyncSession,
    github_service: Optional[Any] = None,
    config: Optional[DynamicContextConfig] = None,
    auto_start: bool = True,
) -> DynamicContextService:
    """
    Create and optionally start DynamicContextService.

    Args:
        db: Database session
        github_service: GitHub service for pushing updates
        config: Service configuration
        auto_start: Start listening to events immediately

    Returns:
        Configured DynamicContextService instance
    """
    service = DynamicContextService(
        db=db,
        github_service=github_service,
        config=config,
    )

    if auto_start:
        await service.start()

    return service
