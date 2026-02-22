"""
=========================================================================
Sprint Verification Service — Automated G-Sprint-Close Verification
SDLC Orchestrator - Sprint 193 (Security Hardening & Automation)

Version: 1.0.0
Date: February 22, 2026
Status: ACTIVE - Sprint 193 Phase 4
Authority: Backend Lead + CTO Approved
Framework: SDLC 6.1.1 Sprint Planning Governance

Purpose:
- Automate CURRENT-SPRINT.md verification for G-Sprint-Close gate
- Replace manual checkbox for 'current_sprint_updated' checklist item
- Create evidence records for audit trail
- Verify Rule 9 compliance (documentation within 24h of sprint end)

Design Decisions:
- Uses SprintFileService.verify_freshness() for GitHub API checks
- Evidence records stored for SOC 2 / HIPAA compliance audit trail
- Projects without GitHub repos get verification_skipped result
- Auto-evaluates checklist items with auto_verify=True flag

Zero Mock Policy: Production-ready verification with real GitHub API
=========================================================================
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.sprint import Sprint
from app.models.sprint_gate_evaluation import SprintGateEvaluation
from app.services.github_service import GitHubService
from app.services.sprint_file_service import SprintFileService

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of CURRENT-SPRINT.md verification."""

    passed: bool
    reason: str
    details: dict
    verified_at: datetime
    evidence_summary: str


class SprintVerificationService:
    """
    Automated G-Sprint-Close verification service.

    Replaces manual checkbox for 'current_sprint_updated' checklist item
    by checking CURRENT-SPRINT.md freshness via GitHub API.

    Integration point: Called during G-Sprint-Close submission in
    planning.py submit_gate_evaluation endpoint.
    """

    def __init__(self, db: AsyncSession, github_service: GitHubService):
        self.db = db
        self.github_service = github_service
        self.sprint_file_service = SprintFileService(
            db=db, github_service=github_service
        )

    async def verify_sprint_close_docs(
        self,
        sprint: Sprint,
        project: Project,
    ) -> VerificationResult:
        """
        Verify CURRENT-SPRINT.md is fresh before G-Sprint-Close.

        Checks:
        1. CURRENT-SPRINT.md exists in repo via GitHub API
        2. File references the correct sprint number
        3. Project has GitHub repo configured (skip if not)

        Args:
            sprint: Sprint being closed
            project: Project owning the sprint

        Returns:
            VerificationResult with passed/failed status and evidence
        """
        now = datetime.now(timezone.utc)

        # Guard: no GitHub repo configured
        if not project.github_repo:
            return VerificationResult(
                passed=True,
                reason="verification_skipped",
                details={
                    "skip_reason": "Project has no GitHub repo configured",
                    "sprint_number": sprint.number,
                },
                verified_at=now,
                evidence_summary=(
                    f"Sprint {sprint.number} G-Sprint-Close: "
                    "CURRENT-SPRINT.md verification skipped (no GitHub repo)"
                ),
            )

        # Check freshness via SprintFileService
        freshness = await self.sprint_file_service.verify_freshness(
            project=project,
            sprint=sprint,
        )

        if not freshness.get("file_exists"):
            return VerificationResult(
                passed=False,
                reason="file_not_found",
                details={
                    "sprint_number": sprint.number,
                    "repo": project.github_repo,
                    "expected_path": "docs/04-build/02-Sprint-Plans/CURRENT-SPRINT.md",
                    **freshness,
                },
                verified_at=now,
                evidence_summary=(
                    f"Sprint {sprint.number} G-Sprint-Close: "
                    f"CURRENT-SPRINT.md NOT FOUND in {project.github_repo}"
                ),
            )

        if not freshness.get("sprint_match"):
            return VerificationResult(
                passed=False,
                reason="stale_sprint_reference",
                details={
                    "sprint_number": sprint.number,
                    "repo": project.github_repo,
                    "file_sha": freshness.get("sha"),
                    **freshness,
                },
                verified_at=now,
                evidence_summary=(
                    f"Sprint {sprint.number} G-Sprint-Close: "
                    f"CURRENT-SPRINT.md in {project.github_repo} "
                    f"references wrong sprint (stale)"
                ),
            )

        return VerificationResult(
            passed=True,
            reason="current",
            details={
                "sprint_number": sprint.number,
                "repo": project.github_repo,
                "file_sha": freshness.get("sha"),
                **freshness,
            },
            verified_at=now,
            evidence_summary=(
                f"Sprint {sprint.number} G-Sprint-Close: "
                f"CURRENT-SPRINT.md verified in {project.github_repo} "
                f"(sha: {freshness.get('sha', 'N/A')[:8]})"
            ),
        )

    async def auto_evaluate_checklist_item(
        self,
        evaluation: SprintGateEvaluation,
        sprint: Sprint,
        project: Project,
    ) -> bool:
        """
        Auto-pass 'current_sprint_updated' checklist item if verified.

        Called during G-Sprint-Close submission. Finds checklist items
        with auto_verify=True flag and evaluates them automatically.

        Args:
            evaluation: SprintGateEvaluation with checklist
            sprint: Sprint being evaluated
            project: Project owning the sprint

        Returns:
            True if any items were auto-evaluated, False otherwise
        """
        result = await self.verify_sprint_close_docs(sprint, project)

        auto_evaluated = False

        for category_items in evaluation.checklist.values():
            for item in category_items:
                if not item.get("auto_verify"):
                    continue

                item_id = item.get("id", "")

                # Auto-evaluate current_sprint_updated
                if item_id == "current_sprint_updated":
                    item["passed"] = result.passed
                    item["auto_verified"] = True
                    item["verification_reason"] = result.reason
                    auto_evaluated = True
                    logger.info(
                        "Auto-verified '%s': passed=%s reason=%s",
                        item_id,
                        result.passed,
                        result.reason,
                    )

                # Auto-evaluate current_sprint_fresh (Rule 9 — 24h)
                elif item_id == "current_sprint_fresh":
                    item["passed"] = result.passed
                    item["auto_verified"] = True
                    item["verification_reason"] = result.reason
                    auto_evaluated = True

                # Auto-evaluate current_sprint_md_exists
                elif item_id == "current_sprint_md_exists":
                    file_exists = result.details.get("file_exists", False)
                    item["passed"] = file_exists
                    item["auto_verified"] = True
                    item["verification_reason"] = (
                        "file_exists" if file_exists else result.reason
                    )
                    auto_evaluated = True

        return auto_evaluated
