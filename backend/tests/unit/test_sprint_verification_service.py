"""
=========================================================================
Unit Tests for Sprint Verification Service — Phase 4
SDLC Orchestrator - Sprint 193 (Security Hardening & Automation)

SDLC Stage: 04 - BUILD
Sprint: 193 - Phase 4 Automated G-Sprint-Close Verification
Framework: SDLC 6.1.1

Purpose:
- Test SprintVerificationService.verify_sprint_close_docs()
- Test SprintVerificationService.auto_evaluate_checklist_item()
- Cover: no-repo skip, file missing, stale reference, fresh file
- Cover: auto-verify flag processing for 3 checklist item types
=========================================================================
"""

import copy
import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from app.models.sprint_gate_evaluation import (
    SprintGateEvaluation,
    G_SPRINT_CHECKLIST_TEMPLATE,
    G_SPRINT_CLOSE_CHECKLIST_TEMPLATE,
)
from app.services.sprint_verification_service import (
    SprintVerificationService,
    VerificationResult,
)


# =============================================================================
# Helpers
# =============================================================================


def make_sprint(number=193, **overrides):
    """Create a mock Sprint with sensible defaults."""
    sprint = Mock()
    sprint.id = overrides.get("id", uuid4())
    sprint.number = number
    sprint.name = overrides.get("name", f"Sprint {number}")
    sprint.goal = overrides.get("goal", "Test sprint goal")
    sprint.status = overrides.get("status", "active")
    sprint.project_id = overrides.get("project_id", uuid4())
    return sprint


def make_project(github_repo=None, **overrides):
    """Create a mock Project."""
    project = Mock()
    project.id = overrides.get("id", uuid4())
    project.name = overrides.get("name", "Test Project")
    project.github_repo = github_repo
    project.github_repo_full_name = github_repo
    project.github_repository = None
    return project


def make_evaluation(gate_type="g_sprint_close"):
    """Create a SprintGateEvaluation with real checklist template."""
    if gate_type == "g_sprint":
        checklist = copy.deepcopy(G_SPRINT_CHECKLIST_TEMPLATE)
    else:
        checklist = copy.deepcopy(G_SPRINT_CLOSE_CHECKLIST_TEMPLATE)

    evaluation = Mock(spec=SprintGateEvaluation)
    evaluation.id = uuid4()
    evaluation.sprint_id = uuid4()
    evaluation.gate_type = gate_type
    evaluation.status = "pending"
    evaluation.checklist = checklist
    evaluation.notes = None
    evaluation.evaluated_by = None
    evaluation.evaluated_at = None
    evaluation.created_at = None
    return evaluation


# =============================================================================
# Tests: verify_sprint_close_docs
# =============================================================================


class TestVerifySprintCloseDocs:
    """Test SprintVerificationService.verify_sprint_close_docs()."""

    @pytest.fixture
    def db(self):
        return AsyncMock()

    @pytest.fixture
    def github_service(self):
        return Mock()

    @pytest.mark.asyncio
    async def test_skips_when_no_github_repo(self, db, github_service):
        """Returns verification_skipped when project has no GitHub repo."""
        svc = SprintVerificationService(db=db, github_service=github_service)
        sprint = make_sprint(number=42)
        project = make_project(github_repo=None)

        result = await svc.verify_sprint_close_docs(sprint, project)

        assert result.passed is True
        assert result.reason == "verification_skipped"
        assert "no GitHub repo" in result.evidence_summary

    @pytest.mark.asyncio
    async def test_fails_when_file_not_found(self, db, github_service):
        """Returns file_not_found when CURRENT-SPRINT.md doesn't exist."""
        svc = SprintVerificationService(db=db, github_service=github_service)
        sprint = make_sprint(number=100)
        project = make_project(github_repo="acme/repo")

        with patch.object(
            svc.sprint_file_service,
            "verify_freshness",
            new_callable=AsyncMock,
            return_value={"file_exists": False, "reason": "not_found"},
        ):
            result = await svc.verify_sprint_close_docs(sprint, project)

        assert result.passed is False
        assert result.reason == "file_not_found"
        assert "NOT FOUND" in result.evidence_summary

    @pytest.mark.asyncio
    async def test_fails_when_sprint_reference_stale(self, db, github_service):
        """Returns stale_sprint_reference when file references wrong sprint."""
        svc = SprintVerificationService(db=db, github_service=github_service)
        sprint = make_sprint(number=100)
        project = make_project(github_repo="acme/repo")

        with patch.object(
            svc.sprint_file_service,
            "verify_freshness",
            new_callable=AsyncMock,
            return_value={
                "file_exists": True,
                "sprint_match": False,
                "sha": "abc123def456",
            },
        ):
            result = await svc.verify_sprint_close_docs(sprint, project)

        assert result.passed is False
        assert result.reason == "stale_sprint_reference"
        assert "stale" in result.evidence_summary

    @pytest.mark.asyncio
    async def test_passes_when_file_is_current(self, db, github_service):
        """Returns current when file exists and references correct sprint."""
        svc = SprintVerificationService(db=db, github_service=github_service)
        sprint = make_sprint(number=193)
        project = make_project(github_repo="acme/repo")

        with patch.object(
            svc.sprint_file_service,
            "verify_freshness",
            new_callable=AsyncMock,
            return_value={
                "file_exists": True,
                "sprint_match": True,
                "sha": "deadbeef12345678",
            },
        ):
            result = await svc.verify_sprint_close_docs(sprint, project)

        assert result.passed is True
        assert result.reason == "current"
        assert "verified" in result.evidence_summary
        assert "deadbeef" in result.evidence_summary

    @pytest.mark.asyncio
    async def test_result_includes_sprint_number_in_details(self, db, github_service):
        """All results include sprint_number in details."""
        svc = SprintVerificationService(db=db, github_service=github_service)
        sprint = make_sprint(number=55)
        project = make_project(github_repo=None)

        result = await svc.verify_sprint_close_docs(sprint, project)

        assert result.details["sprint_number"] == 55


# =============================================================================
# Tests: auto_evaluate_checklist_item
# =============================================================================


class TestAutoEvaluateChecklistItem:
    """Test SprintVerificationService.auto_evaluate_checklist_item()."""

    @pytest.fixture
    def db(self):
        return AsyncMock()

    @pytest.fixture
    def github_service(self):
        return Mock()

    @pytest.mark.asyncio
    async def test_auto_evaluates_g_sprint_close_items(self, db, github_service):
        """Auto-evaluates current_sprint_updated and current_sprint_fresh."""
        svc = SprintVerificationService(db=db, github_service=github_service)
        evaluation = make_evaluation("g_sprint_close")
        sprint = make_sprint(number=193)
        project = make_project(github_repo="acme/repo")

        with patch.object(
            svc,
            "verify_sprint_close_docs",
            new_callable=AsyncMock,
            return_value=VerificationResult(
                passed=True,
                reason="current",
                details={"file_exists": True, "sprint_match": True},
                verified_at=Mock(),
                evidence_summary="test",
            ),
        ):
            auto_eval = await svc.auto_evaluate_checklist_item(
                evaluation, sprint, project
            )

        assert auto_eval is True

        # Check current_sprint_updated was auto-verified
        doc_items = evaluation.checklist["documentation"]
        updated_item = next(
            i for i in doc_items if i["id"] == "current_sprint_updated"
        )
        assert updated_item["passed"] is True
        assert updated_item["auto_verified"] is True
        assert updated_item["verification_reason"] == "current"

        # Check current_sprint_fresh was auto-verified
        fresh_item = next(
            i for i in doc_items if i["id"] == "current_sprint_fresh"
        )
        assert fresh_item["passed"] is True
        assert fresh_item["auto_verified"] is True

    @pytest.mark.asyncio
    async def test_auto_evaluates_g_sprint_md_exists(self, db, github_service):
        """Auto-evaluates current_sprint_md_exists in G-Sprint template."""
        svc = SprintVerificationService(db=db, github_service=github_service)
        evaluation = make_evaluation("g_sprint")
        sprint = make_sprint(number=193)
        project = make_project(github_repo="acme/repo")

        with patch.object(
            svc,
            "verify_sprint_close_docs",
            new_callable=AsyncMock,
            return_value=VerificationResult(
                passed=True,
                reason="current",
                details={"file_exists": True, "sprint_match": True},
                verified_at=Mock(),
                evidence_summary="test",
            ),
        ):
            auto_eval = await svc.auto_evaluate_checklist_item(
                evaluation, sprint, project
            )

        assert auto_eval is True

        doc_items = evaluation.checklist["documentation"]
        md_exists_item = next(
            i for i in doc_items if i["id"] == "current_sprint_md_exists"
        )
        assert md_exists_item["passed"] is True
        assert md_exists_item["auto_verified"] is True
        assert md_exists_item["verification_reason"] == "file_exists"

    @pytest.mark.asyncio
    async def test_auto_evaluate_fails_items_when_not_found(self, db, github_service):
        """Items are marked as failed when file is not found."""
        svc = SprintVerificationService(db=db, github_service=github_service)
        evaluation = make_evaluation("g_sprint_close")
        sprint = make_sprint(number=99)
        project = make_project(github_repo="acme/repo")

        with patch.object(
            svc,
            "verify_sprint_close_docs",
            new_callable=AsyncMock,
            return_value=VerificationResult(
                passed=False,
                reason="file_not_found",
                details={"file_exists": False},
                verified_at=Mock(),
                evidence_summary="test",
            ),
        ):
            auto_eval = await svc.auto_evaluate_checklist_item(
                evaluation, sprint, project
            )

        assert auto_eval is True

        doc_items = evaluation.checklist["documentation"]
        updated_item = next(
            i for i in doc_items if i["id"] == "current_sprint_updated"
        )
        assert updated_item["passed"] is False
        assert updated_item["verification_reason"] == "file_not_found"

    @pytest.mark.asyncio
    async def test_skips_items_without_auto_verify_flag(self, db, github_service):
        """Items without auto_verify flag are not touched."""
        svc = SprintVerificationService(db=db, github_service=github_service)
        evaluation = make_evaluation("g_sprint_close")
        sprint = make_sprint(number=193)
        project = make_project(github_repo="acme/repo")

        # Count items with auto_verify=True before
        auto_verify_count = sum(
            1
            for items in evaluation.checklist.values()
            for item in items
            if item.get("auto_verify")
        )

        with patch.object(
            svc,
            "verify_sprint_close_docs",
            new_callable=AsyncMock,
            return_value=VerificationResult(
                passed=True,
                reason="current",
                details={"file_exists": True, "sprint_match": True},
                verified_at=Mock(),
                evidence_summary="test",
            ),
        ):
            await svc.auto_evaluate_checklist_item(evaluation, sprint, project)

        # Count items that were auto-verified
        verified_count = sum(
            1
            for items in evaluation.checklist.values()
            for item in items
            if item.get("auto_verified")
        )

        # Only items with auto_verify flag should be touched
        assert verified_count == auto_verify_count

        # Non-auto-verify items should still have passed=None
        work_items = evaluation.checklist["work"]
        for item in work_items:
            assert item.get("passed") is None

    @pytest.mark.asyncio
    async def test_no_auto_verify_returns_false(self, db, github_service):
        """Returns False when checklist has no auto_verify items."""
        svc = SprintVerificationService(db=db, github_service=github_service)
        sprint = make_sprint(number=193)
        project = make_project(github_repo="acme/repo")

        # Create evaluation with no auto_verify items
        evaluation = make_evaluation("g_sprint_close")
        for category_items in evaluation.checklist.values():
            for item in category_items:
                item.pop("auto_verify", None)

        with patch.object(
            svc,
            "verify_sprint_close_docs",
            new_callable=AsyncMock,
            return_value=VerificationResult(
                passed=True,
                reason="current",
                details={"file_exists": True},
                verified_at=Mock(),
                evidence_summary="test",
            ),
        ):
            result = await svc.auto_evaluate_checklist_item(
                evaluation, sprint, project
            )

        assert result is False
