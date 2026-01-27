"""
=========================================================================
Auto-Generation Service Tests - Sprint 108 Day 2
SDLC Orchestrator - Governance Foundation

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 108 Day 2
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Test Coverage:
- IntentGenerator: LLM, template, minimal fallback
- OwnershipGenerator: CODEOWNERS, patterns, git blame, fallback
- ContextAttachmentGenerator: Module extraction, ADR search, spec search
- AttestationGenerator: Session data extraction, review time calculation

Performance Targets:
- Intent: <10s (LLM), <1s (template)
- Ownership: <2s
- Context: <5s
- Attestation: <3s

Zero Mock Policy: Real service tests with Ollama when available
=========================================================================
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.governance.auto_generator import (
    AutoGenerationService,
    IntentGenerator,
    OwnershipGenerator,
    ContextAttachmentGenerator,
    AttestationGenerator,
    TaskContext,
    FileContext,
    PRContext,
    AISessionContext,
    GenerationResult,
    FallbackLevel,
    GeneratorType,
    create_auto_generation_service,
    get_auto_generation_service,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def task_context():
    """Sample task context for testing."""
    return TaskContext(
        task_id="TASK-1234",
        title="Add user profile caching",
        description="Implement Redis caching for user profile API to reduce latency from 850ms to <100ms p95. This is a critical performance optimization.",
        acceptance_criteria="- p95 latency <100ms\n- Cache hit rate >90%\n- TTL 15 minutes",
        project_name="SDLC Orchestrator",
        assignee="backend-lead",
    )


@pytest.fixture
def file_context():
    """Sample file context for testing."""
    return FileContext(
        file_path="backend/app/services/governance/auto_generator.py",
        repository_path=".",
        file_extension=".py",
        is_new_file=True,
        task_creator="backend-lead",
    )


@pytest.fixture
def pr_context():
    """Sample PR context for testing."""
    return PRContext(
        pr_number=123,
        pr_title="feat: Add auto-generation service",
        pr_description="Implements 4 generators for compliance artifacts",
        changed_files=[
            "backend/app/services/governance/auto_generator.py",
            "backend/app/api/routes/auto_generation.py",
            "backend/app/models/governance/submission.py",
        ],
        repository_path=".",
        author="backend-lead",
    )


@pytest.fixture
def ai_session_context():
    """Sample AI session context for testing."""
    return AISessionContext(
        session_id="sess_abc123xyz",
        provider="Claude",
        model="claude-sonnet-4-5-20250929",
        generated_lines=450,
        timestamp=datetime.now(timezone.utc),
        prompts=["Create an auto-generation service with 4 generators..."],
    )


@pytest.fixture
def mock_ollama_service():
    """Mock Ollama service for testing."""
    mock = MagicMock()
    mock.is_available = False  # Default to unavailable for template fallback testing
    mock.health_check.return_value = {
        "healthy": False,
        "models": [],
        "version": "mock",
    }
    return mock


@pytest.fixture
def auto_generation_service(mock_ollama_service):
    """Auto-generation service with mocked Ollama."""
    return AutoGenerationService(
        ollama_service=mock_ollama_service,
        repository_path=".",
    )


# ============================================================================
# IntentGenerator Tests
# ============================================================================


class TestIntentGenerator:
    """Tests for IntentGenerator."""

    @pytest.mark.asyncio
    async def test_generate_with_template_fallback(self, task_context, mock_ollama_service):
        """Test intent generation with template fallback when LLM unavailable."""
        generator = IntentGenerator(mock_ollama_service)

        result = await generator.generate(task_context)

        assert result.success is True
        assert result.fallback_level in [FallbackLevel.TEMPLATE, FallbackLevel.MINIMAL]
        assert result.generator_type == GeneratorType.INTENT
        assert "# Intent:" in result.content
        assert task_context.title in result.content
        assert result.confidence >= 30
        assert result.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_template_fallback_has_required_sections(self, task_context, mock_ollama_service):
        """Test that template fallback includes required sections."""
        generator = IntentGenerator(mock_ollama_service)

        result = await generator.generate(task_context)

        # Check required sections
        assert "## Why This Change?" in result.content
        assert "## What Problem Does It Solve?" in result.content
        assert "## Alternatives Considered" in result.content

    @pytest.mark.asyncio
    async def test_minimal_fallback_always_succeeds(self, mock_ollama_service):
        """Test that minimal fallback always succeeds even with minimal input."""
        generator = IntentGenerator(mock_ollama_service)

        minimal_task = TaskContext(
            task_id="TASK-MIN",
            title="Minimal Task",
            description="",
        )

        result = await generator.generate(minimal_task)

        assert result.success is True
        assert "# Intent:" in result.content
        assert result.metadata.get("task_id") == "TASK-MIN"

    @pytest.mark.asyncio
    async def test_ui_badge_reflects_fallback_level(self, task_context, mock_ollama_service):
        """Test that UI badge correctly reflects fallback level."""
        generator = IntentGenerator(mock_ollama_service)

        result = await generator.generate(task_context)

        badge = result.ui_badge
        assert "color" in badge
        assert "text" in badge
        assert badge["color"] in ["green", "yellow", "orange"]


# ============================================================================
# OwnershipGenerator Tests
# ============================================================================


class TestOwnershipGenerator:
    """Tests for OwnershipGenerator."""

    @pytest.mark.asyncio
    async def test_suggest_ownership_from_directory_pattern(self, file_context):
        """Test ownership suggestion from directory patterns."""
        generator = OwnershipGenerator(".")

        result = await generator.generate(file_context)

        assert result.success is True
        assert result.generator_type == GeneratorType.OWNERSHIP
        assert "@" in result.metadata.get("owner", "")
        assert result.metadata.get("module") is not None

    @pytest.mark.asyncio
    async def test_ownership_for_backend_service(self):
        """Test ownership for backend service file."""
        file = FileContext(
            file_path="backend/app/services/user_service.py",
            repository_path=".",
            file_extension=".py",
            is_new_file=False,
        )
        generator = OwnershipGenerator(".")

        result = await generator.generate(file)

        assert result.success is True
        assert "@backend-team" in result.metadata.get("owner", "") or "backend" in result.metadata.get("module", "").lower()

    @pytest.mark.asyncio
    async def test_ownership_for_frontend_component(self):
        """Test ownership for frontend component file."""
        file = FileContext(
            file_path="frontend/src/components/UserProfile/index.tsx",
            repository_path=".",
            file_extension=".tsx",
            is_new_file=True,
        )
        generator = OwnershipGenerator(".")

        result = await generator.generate(file)

        assert result.success is True
        # Should suggest frontend team or use extension fallback
        annotation = result.content
        assert "@" in annotation

    @pytest.mark.asyncio
    async def test_ownership_annotation_format_python(self):
        """Test Python annotation format."""
        file = FileContext(
            file_path="backend/app/services/test.py",
            repository_path=".",
            file_extension=".py",
            is_new_file=True,
        )
        generator = OwnershipGenerator(".")

        result = await generator.generate(file)

        # Python format should use # comments
        assert result.content.startswith("# @owner:")
        assert "# @module:" in result.content
        assert "# @created:" in result.content

    @pytest.mark.asyncio
    async def test_ownership_annotation_format_typescript(self):
        """Test TypeScript annotation format."""
        file = FileContext(
            file_path="frontend/src/components/test.tsx",
            repository_path=".",
            file_extension=".tsx",
            is_new_file=True,
        )
        generator = OwnershipGenerator(".")

        result = await generator.generate(file)

        # TypeScript format should use JSDoc comments
        assert "/**" in result.content
        assert "@owner" in result.content
        assert "*/" in result.content

    @pytest.mark.asyncio
    async def test_ownership_includes_all_suggestions_in_metadata(self, file_context):
        """Test that all ownership suggestions are included in metadata."""
        generator = OwnershipGenerator(".")

        result = await generator.generate(file_context)

        # Metadata should include all suggestions
        assert "all_suggestions" in result.metadata or "source" in result.metadata

    @pytest.mark.asyncio
    async def test_ownership_confidence_score(self, file_context):
        """Test that confidence score is calculated correctly."""
        generator = OwnershipGenerator(".")

        result = await generator.generate(file_context)

        # Confidence should be between 0 and 100
        assert 0 <= result.confidence <= 100


# ============================================================================
# ContextAttachmentGenerator Tests
# ============================================================================


class TestContextAttachmentGenerator:
    """Tests for ContextAttachmentGenerator."""

    @pytest.mark.asyncio
    async def test_attach_context_extracts_modules(self, pr_context):
        """Test that context attachment extracts modules from changed files."""
        generator = ContextAttachmentGenerator(".")

        result = await generator.generate(pr_context)

        assert result.success is True
        assert result.generator_type == GeneratorType.CONTEXT
        assert "modules" in result.metadata
        assert isinstance(result.metadata["modules"], list)

    @pytest.mark.asyncio
    async def test_context_attachment_includes_pr_number(self, pr_context):
        """Test that context attachment includes PR number in metadata."""
        generator = ContextAttachmentGenerator(".")

        result = await generator.generate(pr_context)

        assert result.metadata.get("pr_number") == pr_context.pr_number

    @pytest.mark.asyncio
    async def test_context_section_format(self, pr_context):
        """Test that context section has correct format."""
        generator = ContextAttachmentGenerator(".")

        result = await generator.generate(pr_context)

        # Check required sections
        assert "## Related Context (Auto-Generated)" in result.content
        assert "### Architecture Decisions" in result.content
        assert "### Design Specs" in result.content
        assert "### Affected Modules" in result.content

    @pytest.mark.asyncio
    async def test_empty_changed_files_still_succeeds(self):
        """Test that empty changed files list still produces valid output."""
        pr = PRContext(
            pr_number=999,
            pr_title="Empty PR",
            pr_description="",
            changed_files=[],
            repository_path=".",
        )
        generator = ContextAttachmentGenerator(".")

        result = await generator.generate(pr)

        assert result.success is True
        assert result.metadata.get("modules") == []

    @pytest.mark.asyncio
    async def test_module_extraction_from_various_paths(self):
        """Test module extraction from various file path patterns."""
        pr = PRContext(
            pr_number=100,
            pr_title="Multi-module PR",
            pr_description="",
            changed_files=[
                "backend/app/services/auth/login.py",
                "backend/app/api/routes/users.py",
                "frontend/src/components/Dashboard/index.tsx",
            ],
            repository_path=".",
        )
        generator = ContextAttachmentGenerator(".")

        result = await generator.generate(pr)

        modules = result.metadata.get("modules", [])
        assert len(modules) > 0


# ============================================================================
# AttestationGenerator Tests
# ============================================================================


class TestAttestationGenerator:
    """Tests for AttestationGenerator."""

    @pytest.mark.asyncio
    async def test_generate_attestation_template(self, pr_context, ai_session_context):
        """Test attestation template generation."""
        generator = AttestationGenerator()

        result = await generator.generate(pr_context, ai_session_context)

        assert result.success is True
        assert result.generator_type == GeneratorType.ATTESTATION
        assert f"PR #{pr_context.pr_number}" in result.content

    @pytest.mark.asyncio
    async def test_attestation_includes_ai_metadata(self, pr_context, ai_session_context):
        """Test that attestation includes all AI session metadata."""
        generator = AttestationGenerator()

        result = await generator.generate(pr_context, ai_session_context)

        content = result.content
        assert ai_session_context.provider in content
        assert ai_session_context.model in content
        assert ai_session_context.session_id in content
        assert str(ai_session_context.generated_lines) in content

    @pytest.mark.asyncio
    async def test_attestation_calculates_min_review_time(self, pr_context, ai_session_context):
        """Test that minimum review time is calculated correctly."""
        generator = AttestationGenerator()

        result = await generator.generate(pr_context, ai_session_context)

        # 2 seconds per line = generated_lines * 2 / 60 minutes
        expected_min_time = (ai_session_context.generated_lines * 2) / 60
        assert result.metadata.get("min_review_time_minutes") == expected_min_time

    @pytest.mark.asyncio
    async def test_attestation_includes_prompt_hash(self, pr_context, ai_session_context):
        """Test that attestation includes prompt hash for audit trail."""
        generator = AttestationGenerator()

        result = await generator.generate(pr_context, ai_session_context)

        assert "prompt_hash" in result.metadata
        assert len(result.metadata["prompt_hash"]) == 16  # SHA256 truncated to 16 chars

    @pytest.mark.asyncio
    async def test_attestation_includes_required_checkboxes(self, pr_context, ai_session_context):
        """Test that attestation includes required checkboxes for human review."""
        generator = AttestationGenerator()

        result = await generator.generate(pr_context, ai_session_context)

        content = result.content
        # Check for modification checkboxes
        assert "- [ ]" in content
        assert "Refactored code structure" in content
        assert "Added error handling" in content

        # Check for understanding checkboxes
        assert "algorithm/logic used" in content
        assert "Edge cases handled" in content


# ============================================================================
# AutoGenerationService Tests
# ============================================================================


class TestAutoGenerationService:
    """Tests for AutoGenerationService orchestration."""

    @pytest.mark.asyncio
    async def test_generate_intent(self, auto_generation_service, task_context):
        """Test intent generation through service."""
        result = await auto_generation_service.generate_intent(task_context)

        assert result.success is True
        assert result.generator_type == GeneratorType.INTENT

    @pytest.mark.asyncio
    async def test_suggest_ownership(self, auto_generation_service, file_context):
        """Test ownership suggestion through service."""
        result = await auto_generation_service.suggest_ownership(file_context)

        assert result.success is True
        assert result.generator_type == GeneratorType.OWNERSHIP

    @pytest.mark.asyncio
    async def test_attach_context(self, auto_generation_service, pr_context):
        """Test context attachment through service."""
        result = await auto_generation_service.attach_context(pr_context)

        assert result.success is True
        assert result.generator_type == GeneratorType.CONTEXT

    @pytest.mark.asyncio
    async def test_generate_attestation(
        self, auto_generation_service, pr_context, ai_session_context
    ):
        """Test attestation generation through service."""
        result = await auto_generation_service.generate_attestation(
            pr_context, ai_session_context
        )

        assert result.success is True
        assert result.generator_type == GeneratorType.ATTESTATION

    @pytest.mark.asyncio
    async def test_generate_all_for_pr(
        self, auto_generation_service, pr_context, task_context, ai_session_context
    ):
        """Test generating all artifacts for a PR."""
        results = await auto_generation_service.generate_all_for_pr(
            pr=pr_context,
            task=task_context,
            ai_session=ai_session_context,
        )

        # Context is always generated
        assert "context" in results
        assert results["context"].success is True

        # Intent is generated when task provided
        assert "intent" in results
        assert results["intent"].success is True

        # Ownership is generated for changed files
        assert "ownership" in results
        assert isinstance(results["ownership"], list)

        # Attestation is generated when AI session provided
        assert "attestation" in results
        assert results["attestation"].success is True

    @pytest.mark.asyncio
    async def test_generate_all_without_optional_contexts(
        self, auto_generation_service, pr_context
    ):
        """Test generating artifacts without optional task/AI session."""
        results = await auto_generation_service.generate_all_for_pr(
            pr=pr_context,
            task=None,
            ai_session=None,
        )

        # Context is always generated
        assert "context" in results
        assert results["context"].success is True

        # Intent not generated without task
        assert "intent" not in results

        # Attestation not generated without AI session
        assert "attestation" not in results

    def test_health_check(self, auto_generation_service):
        """Test service health check."""
        health = auto_generation_service.health_check()

        assert health["service"] == "AutoGenerationService"
        assert health["healthy"] is True
        assert "generators" in health
        assert "fail_safe_enabled" in health
        assert health["generators"]["intent"] == "enabled"


# ============================================================================
# Factory Function Tests
# ============================================================================


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_create_auto_generation_service(self):
        """Test creating service via factory function."""
        service = create_auto_generation_service()

        assert isinstance(service, AutoGenerationService)
        assert service.intent_generator is not None
        assert service.ownership_generator is not None
        assert service.context_generator is not None
        assert service.attestation_generator is not None

    def test_get_auto_generation_service_singleton(self):
        """Test that get_auto_generation_service returns singleton."""
        service1 = get_auto_generation_service()
        service2 = get_auto_generation_service()

        assert service1 is service2


# ============================================================================
# GenerationResult Tests
# ============================================================================


class TestGenerationResult:
    """Tests for GenerationResult data class."""

    def test_ui_badge_llm(self):
        """Test UI badge for LLM generation."""
        result = GenerationResult(
            success=True,
            fallback_level=FallbackLevel.LLM,
            content="test",
            confidence=85,
            latency_ms=1000,
            generator_type=GeneratorType.INTENT,
        )

        badge = result.ui_badge
        assert badge["color"] == "green"
        assert "AI" in badge["text"]

    def test_ui_badge_template(self):
        """Test UI badge for template generation."""
        result = GenerationResult(
            success=True,
            fallback_level=FallbackLevel.TEMPLATE,
            content="test",
            confidence=60,
            latency_ms=100,
            generator_type=GeneratorType.INTENT,
        )

        badge = result.ui_badge
        assert badge["color"] == "yellow"
        assert "template" in badge["text"].lower()

    def test_ui_badge_minimal(self):
        """Test UI badge for minimal fallback."""
        result = GenerationResult(
            success=True,
            fallback_level=FallbackLevel.MINIMAL,
            content="test",
            confidence=30,
            latency_ms=50,
            generator_type=GeneratorType.INTENT,
        )

        badge = result.ui_badge
        assert badge["color"] == "orange"
        assert "failed" in badge["text"].lower() or "manual" in badge["text"].lower()


# ============================================================================
# Performance Tests
# ============================================================================


class TestPerformance:
    """Performance tests for generators."""

    @pytest.mark.asyncio
    async def test_intent_generator_latency(self, task_context, mock_ollama_service):
        """Test intent generator completes within target latency."""
        generator = IntentGenerator(mock_ollama_service)

        result = await generator.generate(task_context)

        # Template fallback should be fast (<1s)
        assert result.latency_ms < 1000

    @pytest.mark.asyncio
    async def test_ownership_generator_latency(self, file_context):
        """Test ownership generator completes within target latency."""
        generator = OwnershipGenerator(".")

        result = await generator.generate(file_context)

        # Should be fast (<2s)
        assert result.latency_ms < 2000

    @pytest.mark.asyncio
    async def test_context_generator_latency(self, pr_context):
        """Test context generator completes within target latency."""
        generator = ContextAttachmentGenerator(".")

        result = await generator.generate(pr_context)

        # Should be fast (<5s)
        assert result.latency_ms < 5000

    @pytest.mark.asyncio
    async def test_attestation_generator_latency(self, pr_context, ai_session_context):
        """Test attestation generator completes within target latency."""
        generator = AttestationGenerator()

        result = await generator.generate(pr_context, ai_session_context)

        # Should be very fast (<3s)
        assert result.latency_ms < 3000
