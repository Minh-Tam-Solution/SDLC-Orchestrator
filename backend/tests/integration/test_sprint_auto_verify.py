"""
Integration Test — Sprint 194 (CF-193-03): Submit → Auto-Verify G-Sprint-Close.

Tests the full flow:
1. Create sprint + project (mock DB objects)
2. Create SprintGateEvaluation with G-Sprint-Close checklist
3. Call SprintVerificationService.auto_evaluate_checklist_item()
4. Assert checklist items with auto_verify=True are auto-evaluated
5. Assert manual items remain untouched

Covers:
- Happy path: file exists + matches sprint → 3 auto-verify items pass
- File not found → current_sprint_updated + current_sprint_fresh fail
- Sprint mismatch → stale reference detected
- No GitHub repo → verification_skipped, items pass (graceful)
- Manual items never touched by auto-verify
"""

import copy
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.models.sprint_gate_evaluation import (
    G_SPRINT_CLOSE_CHECKLIST_TEMPLATE,
    SprintGateEvaluation,
)
from app.services.sprint_verification_service import SprintVerificationService


@pytest.fixture
def github_service():
    """Mock GitHubService."""
    return MagicMock()


@pytest.fixture
def db():
    """Mock async DB session."""
    return AsyncMock()


@pytest.fixture
def project_with_repo():
    """Project with GitHub repo configured."""
    p = MagicMock()
    p.id = uuid4()
    p.github_repo = "Acme-Corp/my-project"
    p.default_branch = "main"
    return p


@pytest.fixture
def project_no_repo():
    """Project WITHOUT GitHub repo."""
    p = MagicMock()
    p.id = uuid4()
    p.github_repo = None
    p.default_branch = "main"
    return p


@pytest.fixture
def active_sprint():
    """Active Sprint mock."""
    s = MagicMock()
    s.id = uuid4()
    s.number = 194
    s.name = "Sprint 194"
    s.status = "ACTIVE"
    return s


@pytest.fixture
def close_evaluation(active_sprint):
    """G-Sprint-Close evaluation with template checklist."""
    e = MagicMock(spec=SprintGateEvaluation)
    e.id = uuid4()
    e.sprint_id = active_sprint.id
    e.gate_type = "g_sprint_close"
    e.status = "pending"
    e.checklist = copy.deepcopy(G_SPRINT_CLOSE_CHECKLIST_TEMPLATE)
    return e


class TestAutoVerifyHappyPath:
    """Full happy-path: file exists, matches sprint, 3 items auto-pass."""

    @pytest.mark.asyncio
    async def test_auto_verify_passes_all_three_items(
        self, db, github_service, project_with_repo, active_sprint, close_evaluation
    ):
        """When file exists and matches sprint, all auto_verify items pass."""
        svc = SprintVerificationService(db, github_service)

        # Mock verify_freshness to return "file exists + sprint matches"
        with patch.object(
            svc.sprint_file_service,
            "verify_freshness",
            return_value={
                "file_exists": True,
                "sprint_match": True,
                "sha": "abc12345def67890",
            },
        ):
            result = await svc.auto_evaluate_checklist_item(
                evaluation=close_evaluation,
                sprint=active_sprint,
                project=project_with_repo,
            )

        assert result is True

        # Check all 3 auto_verify items in documentation category
        doc_items = close_evaluation.checklist["documentation"]
        auto_items = {i["id"]: i for i in doc_items if i.get("auto_verify")}

        assert auto_items["current_sprint_updated"]["passed"] is True
        assert auto_items["current_sprint_updated"]["auto_verified"] is True
        assert auto_items["current_sprint_updated"]["verification_reason"] == "current"

        assert auto_items["current_sprint_fresh"]["passed"] is True
        assert auto_items["current_sprint_fresh"]["auto_verified"] is True

    @pytest.mark.asyncio
    async def test_manual_items_untouched(
        self, db, github_service, project_with_repo, active_sprint, close_evaluation
    ):
        """Manual checklist items remain unchanged after auto-verify."""
        svc = SprintVerificationService(db, github_service)

        with patch.object(
            svc.sprint_file_service,
            "verify_freshness",
            return_value={"file_exists": True, "sprint_match": True, "sha": "abc"},
        ):
            await svc.auto_evaluate_checklist_item(
                evaluation=close_evaluation,
                sprint=active_sprint,
                project=project_with_repo,
            )

        # "work" category items should all still be passed=None
        for item in close_evaluation.checklist["work"]:
            assert item["passed"] is None
            assert "auto_verified" not in item

        # "quality" category items should still be passed=None
        for item in close_evaluation.checklist["quality"]:
            assert item["passed"] is None
            assert "auto_verified" not in item

        # Non-auto documentation items should still be passed=None
        doc_manual = [
            i
            for i in close_evaluation.checklist["documentation"]
            if not i.get("auto_verify")
        ]
        for item in doc_manual:
            assert item["passed"] is None
            assert "auto_verified" not in item


class TestAutoVerifyFileNotFound:
    """File not found in repo → auto-verify items fail."""

    @pytest.mark.asyncio
    async def test_file_not_found_fails_items(
        self, db, github_service, project_with_repo, active_sprint, close_evaluation
    ):
        """When CURRENT-SPRINT.md not found, relevant items fail."""
        svc = SprintVerificationService(db, github_service)

        with patch.object(
            svc.sprint_file_service,
            "verify_freshness",
            return_value={"file_exists": False, "sprint_match": False},
        ):
            result = await svc.auto_evaluate_checklist_item(
                evaluation=close_evaluation,
                sprint=active_sprint,
                project=project_with_repo,
            )

        assert result is True  # Items were evaluated (just failed)

        doc_items = close_evaluation.checklist["documentation"]
        auto_items = {i["id"]: i for i in doc_items if i.get("auto_verify")}

        assert auto_items["current_sprint_updated"]["passed"] is False
        assert auto_items["current_sprint_fresh"]["passed"] is False


class TestAutoVerifyStaleSprint:
    """File exists but references wrong sprint → stale reference."""

    @pytest.mark.asyncio
    async def test_stale_sprint_reference(
        self, db, github_service, project_with_repo, active_sprint, close_evaluation
    ):
        """When file references wrong sprint, updated+fresh fail but exists passes."""
        svc = SprintVerificationService(db, github_service)

        with patch.object(
            svc.sprint_file_service,
            "verify_freshness",
            return_value={
                "file_exists": True,
                "sprint_match": False,
                "sha": "old123",
            },
        ):
            result = await svc.auto_evaluate_checklist_item(
                evaluation=close_evaluation,
                sprint=active_sprint,
                project=project_with_repo,
            )

        assert result is True

        doc_items = close_evaluation.checklist["documentation"]
        auto_items = {i["id"]: i for i in doc_items if i.get("auto_verify")}

        # sprint_match=False → updated + fresh fail
        assert auto_items["current_sprint_updated"]["passed"] is False
        assert auto_items["current_sprint_updated"]["verification_reason"] == "stale_sprint_reference"
        assert auto_items["current_sprint_fresh"]["passed"] is False


class TestAutoVerifyNoGitHubRepo:
    """Project without GitHub repo → verification_skipped, items pass gracefully."""

    @pytest.mark.asyncio
    async def test_no_repo_skips_verification(
        self, db, github_service, project_no_repo, active_sprint, close_evaluation
    ):
        """When project has no GitHub repo, auto-verify items pass (skipped)."""
        svc = SprintVerificationService(db, github_service)

        result = await svc.auto_evaluate_checklist_item(
            evaluation=close_evaluation,
            sprint=active_sprint,
            project=project_no_repo,
        )

        assert result is True

        doc_items = close_evaluation.checklist["documentation"]
        auto_items = {i["id"]: i for i in doc_items if i.get("auto_verify")}

        # All auto-verify items pass because verification was skipped
        assert auto_items["current_sprint_updated"]["passed"] is True
        assert auto_items["current_sprint_updated"]["verification_reason"] == "verification_skipped"
        assert auto_items["current_sprint_fresh"]["passed"] is True
        assert auto_items["current_sprint_fresh"]["auto_verified"] is True


class TestVerifySprintCloseDocs:
    """Direct tests for verify_sprint_close_docs() result structure."""

    @pytest.mark.asyncio
    async def test_returns_verification_result_on_success(
        self, db, github_service, project_with_repo, active_sprint
    ):
        """Successful verification returns VerificationResult with passed=True."""
        svc = SprintVerificationService(db, github_service)

        with patch.object(
            svc.sprint_file_service,
            "verify_freshness",
            return_value={
                "file_exists": True,
                "sprint_match": True,
                "sha": "deadbeef12345678",
            },
        ):
            result = await svc.verify_sprint_close_docs(
                sprint=active_sprint, project=project_with_repo
            )

        assert result.passed is True
        assert result.reason == "current"
        assert "sprint_number" in result.details
        assert result.details["sprint_number"] == 194
        assert "deadbeef" in result.evidence_summary
        assert result.verified_at is not None

    @pytest.mark.asyncio
    async def test_no_repo_returns_skipped(
        self, db, github_service, project_no_repo, active_sprint
    ):
        """No GitHub repo returns passed=True with reason=verification_skipped."""
        svc = SprintVerificationService(db, github_service)

        result = await svc.verify_sprint_close_docs(
            sprint=active_sprint, project=project_no_repo
        )

        assert result.passed is True
        assert result.reason == "verification_skipped"
        assert "no GitHub repo" in result.evidence_summary

    @pytest.mark.asyncio
    async def test_file_not_found_returns_failed(
        self, db, github_service, project_with_repo, active_sprint
    ):
        """File not found returns passed=False with reason=file_not_found."""
        svc = SprintVerificationService(db, github_service)

        with patch.object(
            svc.sprint_file_service,
            "verify_freshness",
            return_value={"file_exists": False},
        ):
            result = await svc.verify_sprint_close_docs(
                sprint=active_sprint, project=project_with_repo
            )

        assert result.passed is False
        assert result.reason == "file_not_found"
        assert "NOT FOUND" in result.evidence_summary

    @pytest.mark.asyncio
    async def test_stale_reference_returns_failed(
        self, db, github_service, project_with_repo, active_sprint
    ):
        """Stale sprint reference returns passed=False."""
        svc = SprintVerificationService(db, github_service)

        with patch.object(
            svc.sprint_file_service,
            "verify_freshness",
            return_value={
                "file_exists": True,
                "sprint_match": False,
                "sha": "stale123",
            },
        ):
            result = await svc.verify_sprint_close_docs(
                sprint=active_sprint, project=project_with_repo
            )

        assert result.passed is False
        assert result.reason == "stale_sprint_reference"
        assert "stale" in result.evidence_summary
