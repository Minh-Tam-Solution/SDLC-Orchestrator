"""
AI Detection Integration Tests - Sprint 42 Day 5

SDLC Stage: 04 - BUILD
Sprint: 42 - AI Detection & Validation Pipeline
Framework: SDLC 5.1.1
Day: 5 - Test Dataset Validation

Purpose:
Integration tests for AI detection service covering:
1. Full detection pipeline (metadata + commit + pattern)
2. Real-world PR scenarios
3. Edge cases and boundary conditions
4. Performance validation

Coverage Target: 95%+
"""

import asyncio
from uuid import uuid4

import pytest

from app.services.ai_detection import AIToolType, DetectionMethod
from app.services.ai_detection.service import GitHubAIDetectionService


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def detection_service():
    """Create detection service instance."""
    return GitHubAIDetectionService()


# ============================================================================
# Full Pipeline Integration Tests
# ============================================================================


class TestAIDetectionPipeline:
    """Integration tests for full AI detection pipeline."""

    @pytest.mark.asyncio
    async def test_cursor_pr_full_detection(self, detection_service):
        """Test full detection pipeline for Cursor-generated PR."""
        pr_data = {
            "title": "feat: implement user authentication with Cursor",
            "body": "This feature was generated using Cursor AI assistant.",
        }
        commits = [
            {"commit": {"message": "[cursor] add login endpoint"}},
            {"commit": {"message": "[cursor] add JWT validation"}},
        ]
        diff = "def authenticate(user, password):\n    pass"

        result = await detection_service.detect(pr_data, commits, diff)

        assert result.is_ai_generated is True
        assert result.detected_tool == AIToolType.CURSOR
        assert result.confidence >= 0.6
        assert result.detection_method == DetectionMethod.COMBINED
        assert "metadata" in result.strategies_used
        assert "commit" in result.strategies_used
        assert "pattern" in result.strategies_used

    @pytest.mark.asyncio
    async def test_copilot_pr_with_coauthor(self, detection_service):
        """Test detection of GitHub Copilot PR with co-authored-by."""
        pr_data = {
            "title": "feat: add user registration",
            "body": "Registration flow implementation",
        }
        commits = [
            {
                "commit": {
                    "message": "feat: add registration\n\nCo-authored-by: GitHub Copilot <noreply@github.com>"
                }
            }
        ]
        diff = "def register():\n    pass"

        result = await detection_service.detect(pr_data, commits, diff)

        assert result.is_ai_generated is True
        assert result.detected_tool == AIToolType.COPILOT
        assert result.confidence >= 0.9  # High confidence for co-authored-by

    @pytest.mark.asyncio
    async def test_claude_code_pr_detection(self, detection_service):
        """Test detection of Claude Code PR."""
        pr_data = {
            "title": "feat: implement API gateway",
            "body": "API gateway implementation.\n\n🤖 Generated with Claude Code",
        }
        commits = [{"commit": {"message": "feat: add gateway routes"}}]
        diff = "class APIGateway:\n    pass"

        result = await detection_service.detect(pr_data, commits, diff)

        assert result.is_ai_generated is True
        assert result.detected_tool == AIToolType.CLAUDE_CODE

    @pytest.mark.asyncio
    async def test_chatgpt_pr_detection(self, detection_service):
        """Test detection of ChatGPT/OpenAI PR."""
        pr_data = {
            "title": "refactor: optimize database queries (ChatGPT)",
            "body": "Query optimization using OpenAI GPT-4 suggestions.",
        }
        commits = [{"commit": {"message": "refactor: optimize SQL"}}]
        diff = "SELECT * FROM users"

        result = await detection_service.detect(pr_data, commits, diff)

        assert result.is_ai_generated is True
        assert result.detected_tool == AIToolType.CHATGPT

    @pytest.mark.asyncio
    async def test_human_pr_not_detected(self, detection_service):
        """Test that human-written PRs are not falsely detected."""
        pr_data = {
            "title": "fix: typo in README",
            "body": "Fixed spelling mistake in documentation.",
        }
        commits = [{"commit": {"message": "fix typo"}}]
        diff = "# Documentation\n"

        result = await detection_service.detect(pr_data, commits, diff)

        assert result.is_ai_generated is False
        assert result.detected_tool is None
        assert result.confidence < 0.5


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestAIDetectionEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_pr_data(self, detection_service):
        """Test detection with empty PR data."""
        pr_data = {"title": "", "body": ""}
        commits = []
        diff = ""

        result = await detection_service.detect(pr_data, commits, diff)

        assert result.is_ai_generated is False
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_none_values(self, detection_service):
        """Test detection with None values."""
        pr_data = {"title": None, "body": None}
        commits = [{"commit": {"message": None}}]
        diff = None

        result = await detection_service.detect(pr_data, commits, diff)

        assert result.is_ai_generated is False

    @pytest.mark.asyncio
    async def test_title_only_detection(self, detection_service):
        """Test detection with AI signal only in title."""
        pr_data = {"title": "feat: add feature [Cursor]", "body": ""}
        commits = []
        diff = ""

        result = await detection_service.detect(pr_data, commits, diff)

        assert result.is_ai_generated is True
        assert result.detected_tool == AIToolType.CURSOR

    @pytest.mark.asyncio
    async def test_body_only_detection(self, detection_service):
        """Test detection with AI signal only in body."""
        pr_data = {
            "title": "feat: add feature",
            "body": "Generated using Cursor AI.",
        }
        commits = []
        diff = ""

        result = await detection_service.detect(pr_data, commits, diff)

        assert result.is_ai_generated is True
        assert result.detected_tool == AIToolType.CURSOR

    @pytest.mark.asyncio
    async def test_commit_only_detection(self, detection_service):
        """Test detection with AI signal only in commits."""
        pr_data = {"title": "feat: add feature", "body": "Implementation."}
        commits = [
            {
                "commit": {
                    "message": "feat: add feature\n\nCo-authored-by: GitHub Copilot <noreply@github.com>"
                }
            }
        ]
        diff = ""

        result = await detection_service.detect(pr_data, commits, diff)

        assert result.is_ai_generated is True
        assert result.detected_tool == AIToolType.COPILOT

    @pytest.mark.asyncio
    async def test_multiple_ai_tools_mentioned(self, detection_service):
        """Test detection when multiple AI tools are mentioned."""
        pr_data = {
            "title": "feat: implement with Cursor and Copilot",
            "body": "Used both Cursor and GitHub Copilot for this feature.",
        }
        commits = [{"commit": {"message": "[cursor] initial implementation"}}]
        diff = ""

        result = await detection_service.detect(pr_data, commits, diff)

        # Should detect (any tool is fine, as long as AI is detected)
        assert result.is_ai_generated is True
        assert result.detected_tool is not None

    @pytest.mark.asyncio
    async def test_emoji_detection(self, detection_service):
        """Test detection of robot emoji (🤖) for Copilot."""
        pr_data = {"title": "feat: add feature 🤖", "body": ""}
        commits = []
        diff = ""

        result = await detection_service.detect(pr_data, commits, diff)

        assert result.is_ai_generated is True
        assert result.detected_tool == AIToolType.COPILOT


# ============================================================================
# Performance Tests
# ============================================================================


class TestAIDetectionPerformance:
    """Performance tests for AI detection service."""

    @pytest.mark.asyncio
    async def test_detection_latency(self, detection_service):
        """Test that detection completes within 600ms."""
        pr_data = {
            "title": "feat: implement feature with Cursor",
            "body": "Large feature implementation.\n" * 100,  # Large body
        }
        commits = [
            {"commit": {"message": f"commit {i}"}} for i in range(20)  # Many commits
        ]
        diff = "def func():\n    pass\n" * 100  # Large diff

        result = await detection_service.detect(pr_data, commits, diff)

        # Should complete within 600ms
        assert result.detection_duration_ms < 600

    @pytest.mark.asyncio
    async def test_concurrent_detections(self, detection_service):
        """Test concurrent detection requests."""
        pr_data = {"title": "feat: with Cursor", "body": "Cursor AI."}
        commits = [{"commit": {"message": "[cursor] add"}}]
        diff = ""

        # Run 10 concurrent detections
        tasks = [
            detection_service.detect(pr_data, commits, diff) for _ in range(10)
        ]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 10
        assert all(r.is_ai_generated is True for r in results)


# ============================================================================
# Evidence Validation Tests
# ============================================================================


class TestAIDetectionEvidence:
    """Tests for detection evidence structure."""

    @pytest.mark.asyncio
    async def test_evidence_structure(self, detection_service):
        """Test that evidence contains all expected fields."""
        pr_data = {"title": "feat: with Cursor", "body": "Cursor AI."}
        commits = [{"commit": {"message": "[cursor] add"}}]
        diff = ""

        result = await detection_service.detect(pr_data, commits, diff)

        evidence = result.detection_evidence
        assert "metadata" in evidence
        assert "commit" in evidence
        assert "pattern" in evidence
        assert "individual_confidences" in evidence
        assert "weighted_confidence" in evidence
        assert "max_confidence" in evidence

    @pytest.mark.asyncio
    async def test_strategies_used_list(self, detection_service):
        """Test that strategies_used is populated correctly."""
        pr_data = {"title": "feat: with Cursor", "body": ""}
        commits = []
        diff = ""

        result = await detection_service.detect(pr_data, commits, diff)

        assert isinstance(result.strategies_used, list)
        assert "metadata" in result.strategies_used
        assert "commit" in result.strategies_used
        assert "pattern" in result.strategies_used


# ============================================================================
# Tool-Specific Detection Tests
# ============================================================================


class TestToolSpecificDetection:
    """Tests for each supported AI tool."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "tool_name,keywords",
        [
            (AIToolType.CURSOR, ["cursor", "cursor.sh", "Cursor AI"]),
            (AIToolType.COPILOT, ["copilot", "GitHub Copilot", "co-pilot"]),
            (AIToolType.CLAUDE_CODE, ["claude", "Claude Code", "Anthropic"]),
            (AIToolType.CHATGPT, ["chatgpt", "ChatGPT", "OpenAI", "gpt-4"]),
            (AIToolType.WINDSURF, ["windsurf", "Windsurf", "Codeium"]),
            (AIToolType.CODY, ["cody", "Cody", "Sourcegraph"]),
            (AIToolType.TABNINE, ["tabnine", "Tabnine", "Tab Nine"]),
        ],
    )
    async def test_tool_detection(
        self, detection_service, tool_name, keywords
    ):
        """Test detection for each AI tool with various keywords."""
        for keyword in keywords:
            pr_data = {
                "title": f"feat: implement with {keyword}",
                "body": f"Generated using {keyword}.",
            }
            commits = []
            diff = ""

            result = await detection_service.detect(pr_data, commits, diff)

            assert result.is_ai_generated is True, f"Failed to detect {keyword}"
            assert result.detected_tool == tool_name, f"Wrong tool for {keyword}"
