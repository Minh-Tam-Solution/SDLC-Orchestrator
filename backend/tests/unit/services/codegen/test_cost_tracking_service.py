"""
Tests for CostTrackingService - Sprint 48.

Test coverage for codegen cost tracking:
- Request logging
- Cost calculation
- Daily/monthly summaries
- Budget monitoring
- Provider health tracking

SDLC Stage: 04 - BUILD
Sprint: 48 - Quality Gates + Ollama Optimization + MVP Hardening
Framework: SDLC 5.1.3

Author: Backend Lead
Date: December 23, 2025
"""

import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.codegen_usage import (
    CodegenUsageLog,
    CodegenDailySummary,
    CodegenMonthlyCost,
    CodegenProviderHealth,
    GenerationStatus,
    QualityGateStatus,
)
from app.services.codegen.cost_tracking_service import (
    CostTrackingService,
    PROVIDER_COSTS,
    DEFAULT_MONTHLY_BUDGET_USD,
    get_cost_tracking_service,
)
from app.services.codegen.base_provider import (
    CodegenSpec,
    CodegenResult,
    CostEstimate,
)


class TestCostTrackingService:
    """Test suite for CostTrackingService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mock db."""
        return CostTrackingService(mock_db)

    @pytest.fixture
    def sample_spec(self):
        """Create sample CodegenSpec."""
        return CodegenSpec(
            app_blueprint={
                "name": "TestApp",
                "modules": [
                    {
                        "name": "users",
                        "entities": [{"name": "User", "fields": []}],
                    }
                ],
            },
            language="python",
            framework="fastapi",
            target_module=None,
        )

    @pytest.fixture
    def sample_result(self):
        """Create sample CodegenResult."""
        return CodegenResult(
            code="# Generated code",
            files={
                "app/models/user.py": "class User: pass",
                "app/schemas/user.py": "class UserSchema: pass",
            },
            metadata={
                "prompt_tokens": 500,
                "completion_tokens": 1500,
                "model": "qwen3-coder:30b",
            },
            provider="ollama",
            tokens_used=2000,
            generation_time_ms=1500,
        )


class TestLogGenerationRequest(TestCostTrackingService):
    """Test logging generation requests."""

    def test_log_generation_request(self, service, mock_db, sample_spec):
        """Test logging a new generation request."""
        request_id = "req-12345"
        user_id = uuid.uuid4()
        project_id = uuid.uuid4()

        log = service.log_generation_request(
            request_id=request_id,
            spec=sample_spec,
            user_id=user_id,
            project_id=project_id,
        )

        # Verify db.add was called
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

        # Verify log properties
        added_log = mock_db.add.call_args[0][0]
        assert added_log.request_id == request_id
        assert added_log.user_id == user_id
        assert added_log.project_id == project_id
        assert added_log.status == GenerationStatus.PENDING.value
        assert added_log.language == "python"
        assert added_log.framework == "fastapi"
        assert added_log.blueprint_name == "TestApp"

    def test_log_request_without_user(self, service, mock_db, sample_spec):
        """Test logging request without user context."""
        log = service.log_generation_request(
            request_id="req-no-user",
            spec=sample_spec,
            user_id=None,
            project_id=None,
        )

        added_log = mock_db.add.call_args[0][0]
        assert added_log.user_id is None
        assert added_log.project_id is None


class TestUpdateGenerationStart(TestCostTrackingService):
    """Test updating generation start."""

    def test_update_generation_start(self, service, mock_db):
        """Test updating log when generation starts."""
        existing_log = CodegenUsageLog(
            request_id="req-123",
            provider="pending",
            status=GenerationStatus.PENDING.value,
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing_log

        result = service.update_generation_start(
            request_id="req-123",
            provider="ollama",
            model="qwen3-coder:30b",
        )

        assert result.provider == "ollama"
        assert result.model == "qwen3-coder:30b"
        assert result.status == GenerationStatus.IN_PROGRESS.value
        mock_db.commit.assert_called()

    def test_update_start_with_estimate(self, service, mock_db):
        """Test updating with cost estimate."""
        existing_log = CodegenUsageLog(
            request_id="req-123",
            provider="pending",
            status=GenerationStatus.PENDING.value,
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing_log

        estimate = CostEstimate(
            estimated_tokens=5000,
            estimated_cost_usd=0.05,
            provider="ollama",
            confidence=0.9,
        )

        result = service.update_generation_start(
            request_id="req-123",
            provider="ollama",
            estimated_cost=estimate,
        )

        assert result.estimated_cost_usd == Decimal("0.05")

    def test_update_start_not_found(self, service, mock_db):
        """Test updating non-existent request."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.update_generation_start(
            request_id="non-existent",
            provider="ollama",
        )

        assert result is None


class TestUpdateGenerationComplete(TestCostTrackingService):
    """Test updating generation completion."""

    def test_update_generation_complete(self, service, mock_db, sample_result):
        """Test updating log when generation completes."""
        existing_log = CodegenUsageLog(
            request_id="req-123",
            provider="ollama",
            status=GenerationStatus.IN_PROGRESS.value,
            prompt_tokens=0,
            completion_tokens=0,
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing_log

        result = service.update_generation_complete(
            request_id="req-123",
            result=sample_result,
            quality_passed=True,
            quality_errors=0,
            quality_warnings=2,
        )

        assert result.status == GenerationStatus.COMPLETED.value
        assert result.prompt_tokens == 500
        assert result.completion_tokens == 1500
        assert result.total_tokens == 2000
        assert result.files_generated == 2
        assert result.quality_gate_status == QualityGateStatus.PASSED.value
        assert result.quality_warnings == 2
        assert result.completed_at is not None

    def test_update_complete_quality_failed(self, service, mock_db, sample_result):
        """Test updating with failed quality gates."""
        existing_log = CodegenUsageLog(
            request_id="req-123",
            provider="ollama",
            status=GenerationStatus.IN_PROGRESS.value,
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing_log

        result = service.update_generation_complete(
            request_id="req-123",
            result=sample_result,
            quality_passed=False,
            quality_errors=3,
            quality_blocked=True,
        )

        assert result.status == GenerationStatus.BLOCKED.value
        assert result.quality_gate_status == QualityGateStatus.FAILED.value
        assert result.quality_blocked is True

    def test_update_complete_not_found(self, service, mock_db, sample_result):
        """Test updating non-existent request."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.update_generation_complete(
            request_id="non-existent",
            result=sample_result,
        )

        assert result is None


class TestUpdateGenerationFailed(TestCostTrackingService):
    """Test updating generation failures."""

    def test_update_generation_failed(self, service, mock_db):
        """Test updating log when generation fails."""
        existing_log = CodegenUsageLog(
            request_id="req-123",
            provider="ollama",
            status=GenerationStatus.IN_PROGRESS.value,
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing_log

        result = service.update_generation_failed(
            request_id="req-123",
            error_message="Provider timeout",
            error_type="TimeoutError",
        )

        assert result.status == GenerationStatus.FAILED.value
        assert result.error_message == "Provider timeout"
        assert result.error_type == "TimeoutError"
        assert result.completed_at is not None


class TestCostCalculation(TestCostTrackingService):
    """Test cost calculation logic."""

    def test_calculate_cost_ollama(self, service, mock_db):
        """Test cost calculation for Ollama provider."""
        cost = service._calculate_cost(
            provider="ollama",
            prompt_tokens=1000,
            completion_tokens=1000,
        )

        # Ollama: input=0.0001/1K, output=0.0002/1K
        expected = Decimal("0.0001") + Decimal("0.0002")
        assert cost == expected

    def test_calculate_cost_claude(self, service, mock_db):
        """Test cost calculation for Claude provider."""
        cost = service._calculate_cost(
            provider="claude",
            prompt_tokens=1000,
            completion_tokens=1000,
        )

        # Claude: input=0.003/1K, output=0.015/1K
        expected = Decimal("0.003") + Decimal("0.015")
        assert cost == expected

    def test_calculate_cost_unknown_provider(self, service, mock_db):
        """Test cost calculation falls back to Ollama rates."""
        cost = service._calculate_cost(
            provider="unknown_provider",
            prompt_tokens=1000,
            completion_tokens=1000,
        )

        # Should use Ollama rates as fallback
        expected = Decimal("0.0001") + Decimal("0.0002")
        assert cost == expected


class TestProviderCosts:
    """Test provider cost configuration."""

    def test_ollama_costs_defined(self):
        """Test Ollama costs are properly defined."""
        assert "ollama" in PROVIDER_COSTS
        assert "input" in PROVIDER_COSTS["ollama"]
        assert "output" in PROVIDER_COSTS["ollama"]
        # Ollama should be cheapest
        assert PROVIDER_COSTS["ollama"]["input"] < PROVIDER_COSTS["claude"]["input"]

    def test_claude_costs_defined(self):
        """Test Claude costs are properly defined."""
        assert "claude" in PROVIDER_COSTS
        assert PROVIDER_COSTS["claude"]["input"] == Decimal("0.003")
        assert PROVIDER_COSTS["claude"]["output"] == Decimal("0.015")

    def test_deepcode_costs_defined(self):
        """Test DeepCode costs are properly defined."""
        assert "deepcode" in PROVIDER_COSTS

    def test_default_budget(self):
        """Test default monthly budget is set."""
        assert DEFAULT_MONTHLY_BUDGET_USD == Decimal("50.00")


class TestProviderHealthTracking(TestCostTrackingService):
    """Test provider health tracking."""

    def test_log_provider_health(self, service, mock_db):
        """Test logging provider health check."""
        health = service.log_provider_health(
            provider="ollama",
            is_available=True,
            response_time_ms=150,
            model="qwen3-coder:30b",
            model_available=True,
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

        added_health = mock_db.add.call_args[0][0]
        assert added_health.provider == "ollama"
        assert added_health.is_available is True
        assert added_health.response_time_ms == 150

    def test_log_provider_health_unavailable(self, service, mock_db):
        """Test logging unavailable provider."""
        health = service.log_provider_health(
            provider="claude",
            is_available=False,
            error_message="API key expired",
        )

        added_health = mock_db.add.call_args[0][0]
        assert added_health.is_available is False
        assert added_health.error_message == "API key expired"

    def test_get_provider_health_history(self, service, mock_db):
        """Test getting provider health history."""
        mock_records = [
            CodegenProviderHealth(
                provider="ollama",
                is_available=True,
                response_time_ms=100,
                checked_at=datetime.utcnow(),
            ),
            CodegenProviderHealth(
                provider="ollama",
                is_available=True,
                response_time_ms=120,
                checked_at=datetime.utcnow() - timedelta(hours=1),
            ),
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_records

        history = service.get_provider_health_history(
            provider="ollama",
            hours=24,
        )

        assert len(history) == 2
        assert all(h["is_available"] is True for h in history)


class TestFactoryFunction:
    """Test factory function."""

    def test_get_cost_tracking_service(self):
        """Test factory creates service instance."""
        mock_db = MagicMock(spec=Session)
        service = get_cost_tracking_service(mock_db)

        assert isinstance(service, CostTrackingService)
        assert service.db == mock_db


class TestDailySummary(TestCostTrackingService):
    """Test daily summary generation."""

    def test_get_daily_summary_structure(self, service, mock_db):
        """Test daily summary returns correct structure."""
        # Mock query results
        mock_result = MagicMock()
        mock_result.total_requests = 10
        mock_result.total_tokens = 50000
        mock_result.total_cost = Decimal("0.05")
        mock_result.avg_time_ms = 1500
        mock_result.total_files = 25

        mock_db.query.return_value.filter.return_value.first.return_value = mock_result
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        summary = service.get_daily_summary(
            target_date=date.today(),
        )

        assert "date" in summary
        assert "total_requests" in summary
        assert "total_tokens" in summary
        assert "total_cost_usd" in summary
        assert "avg_generation_time_ms" in summary


class TestMonthlyCost(TestCostTrackingService):
    """Test monthly cost calculation."""

    def test_get_monthly_cost_structure(self, service, mock_db):
        """Test monthly cost returns correct structure."""
        # Mock query results
        mock_result = MagicMock()
        mock_result.total_requests = 100
        mock_result.total_tokens = 500000
        mock_result.total_cost = Decimal("5.00")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_result
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        cost = service.get_monthly_cost(
            year=2025,
            month=12,
        )

        assert cost["year"] == 2025
        assert cost["month"] == 12
        assert "total_cost_usd" in cost
        assert "budget_limit_usd" in cost
        assert "budget_used_percent" in cost
        assert "budget_exceeded" in cost

    def test_get_monthly_cost_budget_exceeded(self, service, mock_db):
        """Test budget exceeded flag."""
        mock_result = MagicMock()
        mock_result.total_requests = 1000
        mock_result.total_tokens = 5000000
        mock_result.total_cost = Decimal("60.00")  # Over $50 budget

        mock_db.query.return_value.filter.return_value.first.return_value = mock_result
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        cost = service.get_monthly_cost(year=2025, month=12)

        assert cost["budget_exceeded"] is True
        assert cost["budget_used_percent"] > 100


class TestCostReport(TestCostTrackingService):
    """Test comprehensive cost report."""

    def test_get_cost_report_structure(self, service, mock_db):
        """Test cost report returns all sections."""
        # Mock totals query
        mock_totals = MagicMock()
        mock_totals.total_requests = 50
        mock_totals.total_tokens = 250000
        mock_totals.total_cost = Decimal("2.50")
        mock_totals.avg_time_ms = 1200
        mock_totals.total_files = 100
        mock_totals.total_lines = 5000

        # Mock quality stats
        mock_quality = MagicMock()
        mock_quality.total = 50
        mock_quality.passed = 45
        mock_quality.errors = 10
        mock_quality.warnings = 25

        # Setup query chain returns
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.side_effect = [mock_totals, mock_quality]
        mock_filter.group_by.return_value.order_by.return_value.all.return_value = []
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        report = service.get_cost_report(days=30)

        assert "period" in report
        assert "totals" in report
        assert "daily_costs" in report
        assert "quality" in report
        assert "projections" in report

        assert report["period"]["days"] == 30
