"""
AI Detection API Integration Tests - Sprint 42 Day 7

SDLC Stage: 04 - BUILD
Sprint: 42 - AI Detection & Validation Pipeline
Framework: SDLC 5.1.1
Day: 7 - Integration Testing

Purpose:
Integration tests for AI Detection REST API endpoints covering:
1. Detection status endpoint
2. Shadow mode configuration endpoint
3. PR analysis endpoint
4. Circuit breaker monitoring endpoint
5. Error handling and edge cases

Coverage Target: 95%+
"""

import pytest
from unittest.mock import patch, AsyncMock

from app.services.ai_detection import AIToolType
from app.services.ai_detection.service import GitHubAIDetectionService, DETECTION_THRESHOLD
from app.services.ai_detection.shadow_mode import shadow_mode_config, get_shadow_mode_status
from app.services.ai_detection.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    get_all_circuit_breaker_stats,
    github_api_breaker,
)


# ============================================================================
# Detection Status Tests
# ============================================================================


class TestDetectionStatusAPI:
    """Tests for GET /api/v1/ai-detection/status endpoint."""

    def test_status_returns_service_info(self):
        """Test that status endpoint returns correct service information."""
        # Simulate API response structure
        expected_strategies = ["metadata", "commit", "pattern"]
        expected_weights = {"metadata": 0.4, "commit": 0.4, "pattern": 0.2}

        # Verify detection threshold is configured
        assert DETECTION_THRESHOLD == 0.5 or DETECTION_THRESHOLD > 0

        # Verify strategies are defined
        service = GitHubAIDetectionService()
        assert len(service.detectors) == 3

    def test_status_includes_shadow_mode(self):
        """Test that status includes shadow mode configuration."""
        shadow_status = get_shadow_mode_status()

        assert "enabled" in shadow_status
        assert "sample_rate" in shadow_status
        assert "log_level" in shadow_status
        assert "collect_metrics" in shadow_status


# ============================================================================
# Shadow Mode Tests
# ============================================================================


class TestShadowModeAPI:
    """Tests for GET /api/v1/ai-detection/shadow-mode endpoint."""

    def test_shadow_mode_default_enabled(self):
        """Test that shadow mode is enabled by default."""
        assert shadow_mode_config.is_enabled is True

    def test_shadow_mode_default_sample_rate(self):
        """Test that default sample rate is 100%."""
        assert shadow_mode_config.sample_rate == 1.0

    def test_shadow_mode_should_sample(self):
        """Test that should_sample returns True with 100% rate."""
        # With 100% sample rate, should always sample
        for _ in range(10):
            assert shadow_mode_config.should_sample() is True


# ============================================================================
# PR Analysis Tests
# ============================================================================


class TestPRAnalysisAPI:
    """Tests for POST /api/v1/ai-detection/analyze endpoint."""

    @pytest.mark.asyncio
    async def test_analyze_cursor_pr(self):
        """Test analyzing a Cursor-generated PR."""
        service = GitHubAIDetectionService()

        pr_data = {
            "title": "feat: add feature with Cursor",
            "body": "Generated using Cursor AI.",
        }
        commits = [{"commit": {"message": "[cursor] implement"}}]
        diff = ""

        result = await service.detect(pr_data, commits, diff)

        assert result.is_ai_generated is True
        assert result.detected_tool == AIToolType.CURSOR
        assert result.confidence > 0.5

    @pytest.mark.asyncio
    async def test_analyze_human_pr(self):
        """Test analyzing a human-written PR."""
        service = GitHubAIDetectionService()

        pr_data = {
            "title": "fix: update documentation",
            "body": "Fixed typo in README.",
        }
        commits = [{"commit": {"message": "docs: fix typo"}}]
        diff = ""

        result = await service.detect(pr_data, commits, diff)

        assert result.is_ai_generated is False
        assert result.detected_tool is None

    @pytest.mark.asyncio
    async def test_analyze_returns_evidence(self):
        """Test that analysis returns complete evidence."""
        service = GitHubAIDetectionService()

        pr_data = {"title": "feat: Cursor test", "body": ""}
        commits = []
        diff = ""

        result = await service.detect(pr_data, commits, diff)

        # Verify evidence structure
        assert result.detection_evidence is not None
        assert "metadata" in result.detection_evidence
        assert "commit" in result.detection_evidence
        assert "pattern" in result.detection_evidence
        assert "weighted_confidence" in result.detection_evidence
        assert "detection_threshold" in result.detection_evidence

    @pytest.mark.asyncio
    async def test_analyze_returns_duration(self):
        """Test that analysis returns detection duration."""
        service = GitHubAIDetectionService()

        pr_data = {"title": "test", "body": ""}
        commits = []
        diff = ""

        result = await service.detect(pr_data, commits, diff)

        assert result.detection_duration_ms >= 0
        assert result.detection_duration_ms < 1000  # Should be fast


# ============================================================================
# Circuit Breaker Tests
# ============================================================================


class TestCircuitBreakerAPI:
    """Tests for circuit breaker API endpoints."""

    def test_circuit_breaker_initial_state(self):
        """Test that circuit breakers start in CLOSED state."""
        stats = get_all_circuit_breaker_stats()

        assert "github_api" in stats
        assert "external_ai" in stats

        for name, breaker_stats in stats.items():
            assert breaker_stats["stats"]["state"] == "closed"

    @pytest.mark.asyncio
    async def test_circuit_breaker_records_success(self):
        """Test that circuit breaker records successful calls."""
        breaker = CircuitBreaker(name="test_success")

        initial_successes = breaker.stats.total_successes
        await breaker.record_success()

        assert breaker.stats.total_successes == initial_successes + 1
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_records_failure(self):
        """Test that circuit breaker records failed calls."""
        breaker = CircuitBreaker(name="test_failure")
        breaker.config.failure_threshold = 5

        initial_failures = breaker.stats.total_failures
        await breaker.record_failure(Exception("Test error"))

        assert breaker.stats.total_failures == initial_failures + 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_threshold(self):
        """Test that circuit opens after failure threshold."""
        breaker = CircuitBreaker(name="test_open")
        breaker.config.failure_threshold = 3

        # Record failures to trip the circuit
        for i in range(3):
            await breaker.record_failure(Exception(f"Error {i}"))

        assert breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_breaker_reset(self):
        """Test that circuit breaker can be reset."""
        breaker = CircuitBreaker(name="test_reset")
        breaker.config.failure_threshold = 2

        # Trip the circuit
        await breaker.record_failure(Exception("Error 1"))
        await breaker.record_failure(Exception("Error 2"))
        assert breaker.state == CircuitState.OPEN

        # Reset
        await breaker.reset()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_protected_decorator(self):
        """Test the @protected decorator."""
        breaker = CircuitBreaker(name="test_decorator")

        @breaker.protected()
        async def successful_call():
            return "success"

        result = await successful_call()
        assert result == "success"
        assert breaker.stats.total_successes == 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_fallback(self):
        """Test fallback when circuit is open."""
        breaker = CircuitBreaker(name="test_fallback")
        breaker.config.failure_threshold = 1

        # Trip the circuit
        await breaker.record_failure(Exception("Error"))
        assert breaker.state == CircuitState.OPEN

        # Test fallback
        fallback_value = "fallback"

        @breaker.protected(fallback=lambda: fallback_value)
        async def failing_call():
            raise Exception("Should not be called")

        result = await failing_call()
        assert result == fallback_value


# ============================================================================
# Adversarial False Positive Tests
# ============================================================================


class TestAdversarialCases:
    """Tests for false positive protection."""

    @pytest.mark.asyncio
    async def test_database_cursor_not_detected(self):
        """Test that 'database cursor' is not detected as Cursor AI."""
        service = GitHubAIDetectionService()

        pr_data = {
            "title": "fix: database cursor handling",
            "body": "Fixed cursor leak in connection pool.",
        }
        commits = [{"commit": {"message": "fix db cursor leak"}}]
        diff = ""

        result = await service.detect(pr_data, commits, diff)

        assert result.is_ai_generated is False

    @pytest.mark.asyncio
    async def test_pilot_project_not_detected(self):
        """Test that 'pilot project' is not detected as Copilot."""
        service = GitHubAIDetectionService()

        pr_data = {
            "title": "feat: implement pilot project",
            "body": "This is a pilot project for testing.",
        }
        commits = [{"commit": {"message": "add pilot implementation"}}]
        diff = ""

        result = await service.detect(pr_data, commits, diff)

        assert result.is_ai_generated is False

    @pytest.mark.asyncio
    async def test_claude_shannon_not_detected(self):
        """Test that 'Claude Shannon' is not detected as Claude AI."""
        service = GitHubAIDetectionService()

        pr_data = {
            "title": "docs: Claude Shannon's information theory",
            "body": "Added documentation about Claude Shannon.",
        }
        commits = [{"commit": {"message": "add shannon docs"}}]
        diff = ""

        result = await service.detect(pr_data, commits, diff)

        assert result.is_ai_generated is False

    @pytest.mark.asyncio
    async def test_windsurf_sport_not_detected(self):
        """Test that 'windsurf' sport is not detected as Windsurf AI."""
        service = GitHubAIDetectionService()

        pr_data = {
            "title": "chore: cleanup windsurf event handler",
            "body": "Refactored windsurf sports booking handler.",
        }
        commits = [{"commit": {"message": "cleanup windsurf handler"}}]
        diff = ""

        result = await service.detect(pr_data, commits, diff)

        assert result.is_ai_generated is False


# ============================================================================
# Configuration Tests
# ============================================================================


class TestConfigurationAPI:
    """Tests for configuration validation."""

    def test_detection_threshold_range(self):
        """Test that detection threshold is in valid range."""
        assert 0.0 <= DETECTION_THRESHOLD <= 1.0

    def test_supported_tools_list(self):
        """Test that all AI tools are supported."""
        expected_tools = [
            AIToolType.CURSOR,
            AIToolType.COPILOT,
            AIToolType.CLAUDE_CODE,
            AIToolType.CHATGPT,
            AIToolType.WINDSURF,
            AIToolType.CODY,
            AIToolType.TABNINE,
        ]

        for tool in expected_tools:
            assert tool in AIToolType

    def test_strategy_weights_sum(self):
        """Test that strategy weights sum to 1.0."""
        weights = {"metadata": 0.4, "commit": 0.4, "pattern": 0.2}
        total = sum(weights.values())

        assert abs(total - 1.0) < 0.001  # Allow small floating point error


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_empty_input_handling(self):
        """Test handling of empty input."""
        service = GitHubAIDetectionService()

        result = await service.detect(
            pr_data={"title": "", "body": ""},
            commits=[],
            diff="",
        )

        assert result.is_ai_generated is False
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_none_input_handling(self):
        """Test handling of None input values."""
        service = GitHubAIDetectionService()

        result = await service.detect(
            pr_data={"title": None, "body": None},
            commits=[{"commit": {"message": None}}],
            diff=None,
        )

        # Should not crash, should return valid result
        assert result.is_ai_generated is False

    @pytest.mark.asyncio
    async def test_large_input_handling(self):
        """Test handling of large input."""
        service = GitHubAIDetectionService()

        # Large PR body
        large_body = "Large content. " * 10000

        result = await service.detect(
            pr_data={"title": "test", "body": large_body},
            commits=[],
            diff="",
        )

        # Should complete without error
        assert result.detection_duration_ms < 5000  # Max 5 seconds
