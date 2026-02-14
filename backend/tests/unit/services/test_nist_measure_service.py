"""
=========================================================================
NIST MEASURE Service Unit Tests
SDLC Orchestrator - Sprint 157 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: February 5, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5

Test Categories:
- Evaluate MEASURE Tests (all pass, some fail, empty metrics, OPA fallback, error)
- Dashboard Tests (with assessments, empty project, with metrics)
- Metrics CRUD Tests (list empty/data/filters/pagination, create, batch)
- Metric Trend Tests (with data, empty, different days, specific type)
- Bias Summary Tests (with data, empty, compliant, non-compliant, mixed)
- In-Process Evaluation Tests (perf pass/fail, bias pass/fail, disparity, trending)

Test Approach: Unit tests mocking database layer via AsyncMock
Zero Mock Policy: Mocks for database layer only
=========================================================================
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from app.models.nist_map_measure import AISystem, MetricType, PerformanceMetric
from app.schemas.compliance_framework import PolicyEvaluationResult
from app.services.nist_measure_service import (
    DISPARITY_THRESHOLD,
    KEY_METRIC_TYPES,
    MEASURE_POLICIES,
    MetricNotFoundError,
    NISTMeasureEvaluationError,
    NISTMeasureService,
)


# =============================================================================
# Test Constants
# =============================================================================

PROJECT_ID = UUID("00000000-0000-0000-0000-000000000001")
FRAMEWORK_ID = UUID("00000000-0000-0000-0000-000000000002")
SYSTEM_ID = UUID("00000000-0000-0000-0000-000000000003")
METRIC_ID = UUID("00000000-0000-0000-0000-000000000004")
USER_ID = UUID("00000000-0000-0000-0000-000000000005")
SYSTEM_ID_2 = UUID("00000000-0000-0000-0000-000000000006")
NOW = datetime(2026, 4, 14, 12, 0, 0, tzinfo=timezone.utc)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_db():
    """Create a mock async database session with proper async returns."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    db.get = AsyncMock(return_value=None)
    return db


@pytest.fixture
def service():
    """Create NISTMeasureService instance."""
    return NISTMeasureService()


@pytest.fixture
def sample_metric():
    """Create a mock PerformanceMetric model instance."""
    m = MagicMock(spec=PerformanceMetric)
    m.id = METRIC_ID
    m.project_id = PROJECT_ID
    m.ai_system_id = SYSTEM_ID
    m.metric_type = "accuracy"
    m.metric_name = "Model Accuracy"
    m.metric_value = 0.95
    m.threshold_min = 0.90
    m.threshold_max = 1.0
    m.is_within_threshold = True
    m.unit = "%"
    m.demographic_group = None
    m.tags = ["performance"]
    m.measured_at = NOW
    m.measured_by_id = USER_ID
    m.notes = "Quarterly evaluation"
    m.created_at = NOW
    return m


@pytest.fixture
def sample_ai_system():
    """Create a mock AISystem model instance."""
    s = MagicMock(spec=AISystem)
    s.id = SYSTEM_ID
    s.project_id = PROJECT_ID
    s.name = "Hiring Recommender"
    s.system_type = "recommendation"
    s.risk_level = "high"
    s.is_active = True
    s.created_at = NOW
    s.updated_at = NOW
    return s


def _mock_scalars_all(items):
    """Create a mock result with scalars().all() returning items."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = items
    return mock_result


def _mock_scalar_one_or_none(value):
    """Create a mock result with scalar_one_or_none() returning value."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = value
    return mock_result


def _mock_scalar(value):
    """Create a mock result with scalar() returning value."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = value
    return mock_result


def _mock_all(rows):
    """Create a mock result with all() returning rows (for grouped queries)."""
    mock_result = MagicMock()
    mock_result.all.return_value = rows
    return mock_result


# =============================================================================
# Evaluate MEASURE Tests
# =============================================================================


class TestEvaluateMeasure:
    """Tests for NISTMeasureService.evaluate_measure."""

    @pytest.mark.asyncio
    async def test_evaluate_measure_all_pass(self, service, mock_db):
        """Test evaluation where all 4 MEASURE policies pass."""
        with patch.object(
            service, "_fetch_ai_systems", new_callable=AsyncMock
        ) as mock_systems, patch.object(
            service, "_fetch_all_metrics", new_callable=AsyncMock
        ) as mock_metrics, patch.object(
            service, "_evaluate_single_policy", new_callable=AsyncMock
        ) as mock_eval, patch.object(
            service, "_evaluate_metric_trending", new_callable=AsyncMock
        ) as mock_trending, patch.object(
            service, "_persist_assessment_results", new_callable=AsyncMock
        ):
            mock_systems.return_value = []
            mock_metrics.return_value = []

            mock_eval.side_effect = [
                PolicyEvaluationResult(
                    control_code="MEASURE-1.1",
                    title="Performance Thresholds",
                    allowed=True,
                    reason="All metrics within bounds",
                    severity="high",
                ),
                PolicyEvaluationResult(
                    control_code="MEASURE-2.1",
                    title="Bias Detection",
                    allowed=True,
                    reason="All systems covered",
                    severity="critical",
                ),
                PolicyEvaluationResult(
                    control_code="MEASURE-2.2",
                    title="Disparity Analysis",
                    allowed=True,
                    reason="All within threshold",
                    severity="critical",
                ),
            ]
            mock_trending.return_value = PolicyEvaluationResult(
                control_code="MEASURE-3.1",
                title="Metric Trending",
                allowed=True,
                reason="Sufficient data points",
                severity="medium",
            )

            result = await service.evaluate_measure(PROJECT_ID, mock_db)

            assert result["overall_compliant"] is True
            assert result["policies_passed"] == 4
            assert result["policies_total"] == 4
            assert result["compliance_percentage"] == 100.0
            assert result["framework_code"] == "NIST_AI_RMF"
            assert result["function"] == "MEASURE"

    @pytest.mark.asyncio
    async def test_evaluate_measure_some_fail(self, service, mock_db):
        """Test evaluation where some MEASURE policies fail."""
        with patch.object(
            service, "_fetch_ai_systems", new_callable=AsyncMock
        ) as mock_systems, patch.object(
            service, "_fetch_all_metrics", new_callable=AsyncMock
        ) as mock_metrics, patch.object(
            service, "_evaluate_single_policy", new_callable=AsyncMock
        ) as mock_eval, patch.object(
            service, "_evaluate_metric_trending", new_callable=AsyncMock
        ) as mock_trending, patch.object(
            service, "_persist_assessment_results", new_callable=AsyncMock
        ):
            mock_systems.return_value = []
            mock_metrics.return_value = []

            mock_eval.side_effect = [
                PolicyEvaluationResult(
                    control_code="MEASURE-1.1",
                    title="Performance Thresholds",
                    allowed=False,
                    reason="Metric violations found",
                    severity="high",
                ),
                PolicyEvaluationResult(
                    control_code="MEASURE-2.1",
                    title="Bias Detection",
                    allowed=True,
                    reason="All systems covered",
                    severity="critical",
                ),
                PolicyEvaluationResult(
                    control_code="MEASURE-2.2",
                    title="Disparity Analysis",
                    allowed=False,
                    reason="Systems exceeding disparity threshold",
                    severity="critical",
                ),
            ]
            mock_trending.return_value = PolicyEvaluationResult(
                control_code="MEASURE-3.1",
                title="Metric Trending",
                allowed=True,
                reason="Sufficient data points",
                severity="medium",
            )

            result = await service.evaluate_measure(PROJECT_ID, mock_db)

            assert result["overall_compliant"] is False
            assert result["policies_passed"] == 2
            assert result["policies_total"] == 4
            assert result["compliance_percentage"] == 50.0

    @pytest.mark.asyncio
    async def test_evaluate_measure_empty_metrics(self, service, mock_db):
        """Test evaluation with no metrics or AI systems returns all fail."""
        with patch.object(
            service, "_fetch_ai_systems", new_callable=AsyncMock
        ) as mock_systems, patch.object(
            service, "_fetch_all_metrics", new_callable=AsyncMock
        ) as mock_metrics, patch.object(
            service, "_evaluate_single_policy", new_callable=AsyncMock
        ) as mock_eval, patch.object(
            service, "_evaluate_metric_trending", new_callable=AsyncMock
        ) as mock_trending, patch.object(
            service, "_persist_assessment_results", new_callable=AsyncMock
        ):
            mock_systems.return_value = []
            mock_metrics.return_value = []

            mock_eval.side_effect = [
                PolicyEvaluationResult(
                    control_code="MEASURE-1.1",
                    title="Performance Thresholds",
                    allowed=False,
                    reason="No performance metrics recorded",
                    severity="high",
                ),
                PolicyEvaluationResult(
                    control_code="MEASURE-2.1",
                    title="Bias Detection",
                    allowed=False,
                    reason="No bias metrics recorded",
                    severity="critical",
                ),
                PolicyEvaluationResult(
                    control_code="MEASURE-2.2",
                    title="Disparity Analysis",
                    allowed=False,
                    reason="No disparity metrics recorded",
                    severity="critical",
                ),
            ]
            mock_trending.return_value = PolicyEvaluationResult(
                control_code="MEASURE-3.1",
                title="Metric Trending",
                allowed=False,
                reason="No key metrics recorded",
                severity="medium",
            )

            result = await service.evaluate_measure(PROJECT_ID, mock_db)

            assert result["overall_compliant"] is False
            assert result["policies_passed"] == 0
            assert result["compliance_percentage"] == 0.0

    @pytest.mark.asyncio
    async def test_evaluate_measure_opa_fallback(self, service, mock_db):
        """Test evaluation falls back to in-process when OPA unavailable."""
        with patch.object(
            service, "_fetch_ai_systems", new_callable=AsyncMock
        ) as mock_systems, patch.object(
            service, "_fetch_all_metrics", new_callable=AsyncMock
        ) as mock_metrics, patch.object(
            service, "_evaluate_metric_trending", new_callable=AsyncMock
        ) as mock_trending, patch.object(
            service, "_persist_assessment_results", new_callable=AsyncMock
        ), patch("httpx.AsyncClient") as mock_httpx:
            # Make OPA unavailable
            mock_httpx_instance = AsyncMock()
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_httpx_instance)
            mock_httpx.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_httpx_instance.post.side_effect = ConnectionError("OPA unavailable")

            mock_systems.return_value = []
            mock_metrics.return_value = []

            mock_trending.return_value = PolicyEvaluationResult(
                control_code="MEASURE-3.1",
                title="Metric Trending",
                allowed=False,
                reason="No key metrics recorded",
                severity="medium",
            )

            result = await service.evaluate_measure(PROJECT_ID, mock_db)

            assert result["policies_total"] == 4
            assert "results" in result

    @pytest.mark.asyncio
    async def test_evaluate_measure_evaluation_error(self, service, mock_db):
        """Test evaluation raises NISTMeasureEvaluationError on fatal error."""
        with patch.object(
            service, "_fetch_ai_systems", new_callable=AsyncMock
        ) as mock_systems, patch.object(
            service, "_fetch_all_metrics", new_callable=AsyncMock
        ) as mock_metrics, patch.object(
            service, "_evaluate_single_policy", new_callable=AsyncMock
        ) as mock_eval:
            mock_systems.return_value = []
            mock_metrics.return_value = []
            mock_eval.side_effect = RuntimeError("Unexpected failure")

            with pytest.raises(NISTMeasureEvaluationError, match="Failed to evaluate"):
                await service.evaluate_measure(PROJECT_ID, mock_db)


# =============================================================================
# Dashboard Tests
# =============================================================================


class TestGetDashboard:
    """Tests for NISTMeasureService.get_dashboard."""

    @pytest.mark.asyncio
    async def test_get_dashboard_with_assessments(self, service, mock_db):
        """Test dashboard returns correctly aggregated data with assessments."""
        with patch.object(
            service, "_fetch_latest_assessments", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = [
                PolicyEvaluationResult(
                    control_code="MEASURE-1.1",
                    title="Performance Thresholds",
                    allowed=True,
                    reason="Passed",
                    severity="high",
                ),
                PolicyEvaluationResult(
                    control_code="MEASURE-2.1",
                    title="Bias Detection",
                    allowed=False,
                    reason="Insufficient coverage",
                    severity="critical",
                ),
                PolicyEvaluationResult(
                    control_code="MEASURE-2.2",
                    title="Disparity Analysis",
                    allowed=True,
                    reason="Within threshold",
                    severity="critical",
                ),
                PolicyEvaluationResult(
                    control_code="MEASURE-3.1",
                    title="Metric Trending",
                    allowed=True,
                    reason="Sufficient data",
                    severity="medium",
                ),
            ]

            # Mock metric count queries
            mock_db.execute = AsyncMock(
                side_effect=[
                    _mock_scalar(25),   # total_metrics
                    _mock_scalar(20),   # within_threshold
                    _mock_scalar(3),    # bias_groups_count
                ]
            )

            result = await service.get_dashboard(PROJECT_ID, mock_db)

            assert result["project_id"] == str(PROJECT_ID)
            assert result["compliance_percentage"] == 75.0
            assert result["policies_passed"] == 3
            assert result["policies_total"] == 4
            assert result["total_metrics"] == 25
            assert result["within_threshold"] == 20
            assert result["bias_groups_count"] == 3

    @pytest.mark.asyncio
    async def test_get_dashboard_empty_project(self, service, mock_db):
        """Test dashboard with no data returns defaults."""
        with patch.object(
            service, "_fetch_latest_assessments", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = []

            mock_db.execute = AsyncMock(
                side_effect=[
                    _mock_scalar(0),   # total_metrics
                    _mock_scalar(0),   # within_threshold
                    _mock_scalar(0),   # bias_groups_count
                ]
            )

            result = await service.get_dashboard(PROJECT_ID, mock_db)

            assert result["compliance_percentage"] == 0.0
            assert result["policies_passed"] == 0
            assert result["policies_total"] == 4
            assert result["total_metrics"] == 0
            assert result["within_threshold"] == 0

    @pytest.mark.asyncio
    async def test_get_dashboard_with_metrics(self, service, mock_db):
        """Test dashboard correctly counts metrics and thresholds."""
        with patch.object(
            service, "_fetch_latest_assessments", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = [
                PolicyEvaluationResult(
                    control_code="MEASURE-1.1",
                    title="Performance Thresholds",
                    allowed=True,
                    reason="Passed",
                    severity="high",
                ),
            ]

            mock_db.execute = AsyncMock(
                side_effect=[
                    _mock_scalar(100),  # total_metrics
                    _mock_scalar(85),   # within_threshold
                    _mock_scalar(5),    # bias_groups_count
                ]
            )

            result = await service.get_dashboard(PROJECT_ID, mock_db)

            assert result["total_metrics"] == 100
            assert result["within_threshold"] == 85
            assert result["bias_groups_count"] == 5


# =============================================================================
# Metrics CRUD Tests
# =============================================================================


class TestListMetrics:
    """Tests for NISTMeasureService.list_metrics."""

    @pytest.mark.asyncio
    async def test_list_metrics_empty(self, service, mock_db):
        """Test listing metrics when none exist returns empty list."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar(0),
                _mock_scalars_all([]),
            ]
        )

        items, total = await service.list_metrics(
            project_id=PROJECT_ID,
            ai_system_id=None,
            metric_type=None,
            limit=50,
            offset=0,
            db=mock_db,
        )

        assert total == 0
        assert len(items) == 0

    @pytest.mark.asyncio
    async def test_list_metrics_with_data(
        self, service, mock_db, sample_metric
    ):
        """Test listing metrics returns correct results."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar(1),
                _mock_scalars_all([sample_metric]),
            ]
        )

        items, total = await service.list_metrics(
            project_id=PROJECT_ID,
            ai_system_id=None,
            metric_type=None,
            limit=50,
            offset=0,
            db=mock_db,
        )

        assert total == 1
        assert len(items) == 1
        assert items[0].metric_name == "Model Accuracy"

    @pytest.mark.asyncio
    async def test_list_metrics_with_filters(
        self, service, mock_db, sample_metric
    ):
        """Test listing metrics with ai_system_id and metric_type filters."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar(1),
                _mock_scalars_all([sample_metric]),
            ]
        )

        items, total = await service.list_metrics(
            project_id=PROJECT_ID,
            ai_system_id=SYSTEM_ID,
            metric_type="accuracy",
            limit=50,
            offset=0,
            db=mock_db,
        )

        assert total == 1
        assert len(items) == 1

    @pytest.mark.asyncio
    async def test_list_metrics_pagination(self, service, mock_db, sample_metric):
        """Test listing metrics respects limit and offset."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar(5),
                _mock_scalars_all([sample_metric]),
            ]
        )

        items, total = await service.list_metrics(
            project_id=PROJECT_ID,
            ai_system_id=None,
            metric_type=None,
            limit=1,
            offset=2,
            db=mock_db,
        )

        assert total == 5
        assert len(items) == 1


class TestCreateMetric:
    """Tests for NISTMeasureService.create_metric."""

    @pytest.mark.asyncio
    async def test_create_metric_success(self, service, mock_db, sample_ai_system):
        """Test creating a metric succeeds with valid data."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(sample_ai_system)
        )

        data = {
            "project_id": PROJECT_ID,
            "ai_system_id": SYSTEM_ID,
            "metric_type": "accuracy",
            "metric_name": "Model Accuracy",
            "metric_value": 0.95,
            "threshold_min": 0.90,
            "threshold_max": 1.0,
            "unit": "%",
            "measured_at": NOW,
        }

        result = await service.create_metric(data, USER_ID, mock_db)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_metric_invalid_system(self, service, mock_db):
        """Test creating a metric with non-existent AI system raises error."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(None)
        )

        data = {
            "project_id": PROJECT_ID,
            "ai_system_id": UUID("00000000-0000-0000-0000-000000000999"),
            "metric_type": "accuracy",
            "metric_name": "Model Accuracy",
            "metric_value": 0.95,
            "measured_at": NOW,
        }

        with pytest.raises(MetricNotFoundError, match="not found or inactive"):
            await service.create_metric(data, USER_ID, mock_db)


class TestCreateMetricsBatch:
    """Tests for NISTMeasureService.create_metrics_batch."""

    @pytest.mark.asyncio
    async def test_batch_create_success(self, service, mock_db, sample_ai_system):
        """Test batch creating multiple metrics succeeds."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(sample_ai_system)
        )

        metrics_data = [
            {
                "ai_system_id": SYSTEM_ID,
                "metric_type": "accuracy",
                "metric_name": "Model Accuracy",
                "metric_value": 0.95,
                "threshold_min": 0.90,
                "threshold_max": 1.0,
                "measured_at": NOW,
            },
            {
                "ai_system_id": SYSTEM_ID,
                "metric_type": "f1_score",
                "metric_name": "F1 Score",
                "metric_value": 0.92,
                "threshold_min": 0.85,
                "threshold_max": 1.0,
                "measured_at": NOW,
            },
        ]

        created = await service.create_metrics_batch(
            PROJECT_ID, metrics_data, USER_ID, mock_db
        )

        assert len(created) == 2
        assert mock_db.add.call_count == 2
        assert mock_db.commit.await_count == 2

    @pytest.mark.asyncio
    async def test_batch_create_partial_failure(self, service, mock_db, sample_ai_system):
        """Test batch create stops on first invalid system."""
        # First call finds system, second call does not
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar_one_or_none(sample_ai_system),
                _mock_scalar_one_or_none(None),
            ]
        )

        metrics_data = [
            {
                "ai_system_id": SYSTEM_ID,
                "metric_type": "accuracy",
                "metric_name": "Valid Metric",
                "metric_value": 0.95,
                "measured_at": NOW,
            },
            {
                "ai_system_id": UUID("00000000-0000-0000-0000-000000000999"),
                "metric_type": "accuracy",
                "metric_name": "Invalid System Metric",
                "metric_value": 0.80,
                "measured_at": NOW,
            },
        ]

        with pytest.raises(MetricNotFoundError, match="not found or inactive"):
            await service.create_metrics_batch(
                PROJECT_ID, metrics_data, USER_ID, mock_db
            )


# =============================================================================
# Metric Trend Tests
# =============================================================================


class TestGetMetricTrend:
    """Tests for NISTMeasureService.get_metric_trend."""

    @pytest.mark.asyncio
    async def test_get_metric_trend_with_data(self, service, mock_db):
        """Test metric trend returns data points sorted by measured_at."""
        m1 = MagicMock(spec=PerformanceMetric)
        m1.measured_at = NOW - timedelta(days=2)
        m1.metric_value = 0.90
        m1.is_within_threshold = True

        m2 = MagicMock(spec=PerformanceMetric)
        m2.measured_at = NOW - timedelta(days=1)
        m2.metric_value = 0.92
        m2.is_within_threshold = True

        m3 = MagicMock(spec=PerformanceMetric)
        m3.measured_at = NOW
        m3.metric_value = 0.95
        m3.is_within_threshold = True

        mock_db.execute = AsyncMock(
            return_value=_mock_scalars_all([m1, m2, m3])
        )

        result = await service.get_metric_trend(
            ai_system_id=SYSTEM_ID,
            metric_type="accuracy",
            days=30,
            db=mock_db,
        )

        assert len(result) == 3
        assert result[0]["metric_value"] == 0.90
        assert result[2]["metric_value"] == 0.95

    @pytest.mark.asyncio
    async def test_get_metric_trend_empty(self, service, mock_db):
        """Test metric trend with no data returns empty list."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalars_all([])
        )

        result = await service.get_metric_trend(
            ai_system_id=SYSTEM_ID,
            metric_type="accuracy",
            days=30,
            db=mock_db,
        )

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_metric_trend_different_days(self, service, mock_db):
        """Test metric trend respects the days window parameter."""
        m1 = MagicMock(spec=PerformanceMetric)
        m1.measured_at = NOW - timedelta(days=5)
        m1.metric_value = 0.88
        m1.is_within_threshold = True

        mock_db.execute = AsyncMock(
            return_value=_mock_scalars_all([m1])
        )

        result = await service.get_metric_trend(
            ai_system_id=SYSTEM_ID,
            metric_type="accuracy",
            days=7,
            db=mock_db,
        )

        assert len(result) == 1
        assert result[0]["metric_value"] == 0.88

    @pytest.mark.asyncio
    async def test_get_metric_trend_specific_type(self, service, mock_db):
        """Test metric trend filters by specific metric type."""
        m1 = MagicMock(spec=PerformanceMetric)
        m1.measured_at = NOW
        m1.metric_value = 0.12
        m1.is_within_threshold = False

        mock_db.execute = AsyncMock(
            return_value=_mock_scalars_all([m1])
        )

        result = await service.get_metric_trend(
            ai_system_id=SYSTEM_ID,
            metric_type="bias_score",
            days=30,
            db=mock_db,
        )

        assert len(result) == 1
        assert result[0]["metric_value"] == 0.12
        assert result[0]["is_within_threshold"] is False


# =============================================================================
# Bias Summary Tests
# =============================================================================


class TestGetBiasSummary:
    """Tests for NISTMeasureService.get_bias_summary."""

    @pytest.mark.asyncio
    async def test_get_bias_summary_with_data(self, service, mock_db):
        """Test bias summary aggregates groups and computes disparity."""
        system = MagicMock(spec=AISystem)
        system.id = SYSTEM_ID
        system.name = "Hiring Model"
        system.is_active = True

        bias_m1 = MagicMock(spec=PerformanceMetric)
        bias_m1.ai_system_id = SYSTEM_ID
        bias_m1.metric_type = "bias_score"
        bias_m1.demographic_group = "gender:male"
        bias_m1.metric_value = 0.90

        bias_m2 = MagicMock(spec=PerformanceMetric)
        bias_m2.ai_system_id = SYSTEM_ID
        bias_m2.metric_type = "bias_score"
        bias_m2.demographic_group = "gender:female"
        bias_m2.metric_value = 0.85

        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalars_all([system]),     # AI systems
                _mock_scalars_all([bias_m1, bias_m2]),  # bias metrics
            ]
        )

        result = await service.get_bias_summary(PROJECT_ID, mock_db)

        assert result["project_id"] == str(PROJECT_ID)
        assert result["total_bias_metrics"] == 2
        assert len(result["systems"]) == 1
        assert len(result["systems"][0]["groups"]) == 2

    @pytest.mark.asyncio
    async def test_get_bias_summary_empty(self, service, mock_db):
        """Test bias summary with no data returns empty results."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalars_all([]),   # No AI systems
                _mock_scalars_all([]),   # No bias metrics
            ]
        )

        result = await service.get_bias_summary(PROJECT_ID, mock_db)

        assert result["total_bias_metrics"] == 0
        assert len(result["systems"]) == 0
        assert result["compliant_systems"] == 0
        assert result["non_compliant_systems"] == 0

    @pytest.mark.asyncio
    async def test_get_bias_summary_compliant_systems(self, service, mock_db):
        """Test bias summary with compliant systems (disparity <= 1.25)."""
        system = MagicMock(spec=AISystem)
        system.id = SYSTEM_ID
        system.name = "Fair Model"
        system.is_active = True

        # Close values -> ratio close to 1.0 -> compliant
        m1 = MagicMock(spec=PerformanceMetric)
        m1.ai_system_id = SYSTEM_ID
        m1.metric_type = "accuracy"
        m1.demographic_group = "group_a"
        m1.metric_value = 0.90

        m2 = MagicMock(spec=PerformanceMetric)
        m2.ai_system_id = SYSTEM_ID
        m2.metric_type = "accuracy"
        m2.demographic_group = "group_b"
        m2.metric_value = 0.88

        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalars_all([system]),
                _mock_scalars_all([m1, m2]),
            ]
        )

        result = await service.get_bias_summary(PROJECT_ID, mock_db)

        assert result["compliant_systems"] == 1
        assert result["non_compliant_systems"] == 0
        assert result["systems"][0]["is_compliant"] is True

    @pytest.mark.asyncio
    async def test_get_bias_summary_non_compliant(self, service, mock_db):
        """Test bias summary with non-compliant system (disparity > 1.25)."""
        system = MagicMock(spec=AISystem)
        system.id = SYSTEM_ID
        system.name = "Biased Model"
        system.is_active = True

        # Large disparity -> ratio > 1.25 -> non-compliant
        m1 = MagicMock(spec=PerformanceMetric)
        m1.ai_system_id = SYSTEM_ID
        m1.metric_type = "accuracy"
        m1.demographic_group = "group_a"
        m1.metric_value = 0.95

        m2 = MagicMock(spec=PerformanceMetric)
        m2.ai_system_id = SYSTEM_ID
        m2.metric_type = "accuracy"
        m2.demographic_group = "group_b"
        m2.metric_value = 0.60

        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalars_all([system]),
                _mock_scalars_all([m1, m2]),
            ]
        )

        result = await service.get_bias_summary(PROJECT_ID, mock_db)

        assert result["non_compliant_systems"] == 1
        assert result["systems"][0]["is_compliant"] is False
        assert result["systems"][0]["disparity_ratio"] is not None
        assert result["systems"][0]["disparity_ratio"] > DISPARITY_THRESHOLD

    @pytest.mark.asyncio
    async def test_get_bias_summary_mixed(self, service, mock_db):
        """Test bias summary with both compliant and non-compliant systems."""
        system1 = MagicMock(spec=AISystem)
        system1.id = SYSTEM_ID
        system1.name = "Fair Model"
        system1.is_active = True

        system2 = MagicMock(spec=AISystem)
        system2.id = SYSTEM_ID_2
        system2.name = "Biased Model"
        system2.is_active = True

        # System 1: compliant (close values)
        m1 = MagicMock(spec=PerformanceMetric)
        m1.ai_system_id = SYSTEM_ID
        m1.metric_type = "accuracy"
        m1.demographic_group = "group_a"
        m1.metric_value = 0.90

        m2 = MagicMock(spec=PerformanceMetric)
        m2.ai_system_id = SYSTEM_ID
        m2.metric_type = "accuracy"
        m2.demographic_group = "group_b"
        m2.metric_value = 0.88

        # System 2: non-compliant (large disparity)
        m3 = MagicMock(spec=PerformanceMetric)
        m3.ai_system_id = SYSTEM_ID_2
        m3.metric_type = "accuracy"
        m3.demographic_group = "group_a"
        m3.metric_value = 0.95

        m4 = MagicMock(spec=PerformanceMetric)
        m4.ai_system_id = SYSTEM_ID_2
        m4.metric_type = "accuracy"
        m4.demographic_group = "group_b"
        m4.metric_value = 0.55

        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalars_all([system1, system2]),
                _mock_scalars_all([m1, m2, m3, m4]),
            ]
        )

        result = await service.get_bias_summary(PROJECT_ID, mock_db)

        assert result["compliant_systems"] == 1
        assert result["non_compliant_systems"] == 1
        assert result["total_bias_metrics"] == 4


# =============================================================================
# In-Process Evaluation Tests
# =============================================================================


class TestInProcessEvaluators:
    """Tests for the in-process policy evaluation fallback methods."""

    def test_performance_thresholds_all_pass(self):
        """Test MEASURE-1.1 passes when all metrics within thresholds."""
        svc = NISTMeasureService()
        metrics = [
            {
                "metric_name": "accuracy",
                "metric_value": 0.95,
                "threshold_min": 0.90,
                "threshold_max": 1.0,
            },
            {
                "metric_name": "latency",
                "metric_value": 80,
                "threshold_min": 0,
                "threshold_max": 100,
            },
        ]

        result = svc._evaluate_performance_thresholds(metrics)

        assert result.allowed is True
        assert result.control_code == "MEASURE-1.1"
        assert result.details["within_threshold"] == 2
        assert result.details["out_of_threshold"] == 0

    def test_performance_thresholds_violations(self):
        """Test MEASURE-1.1 fails when metrics exceed thresholds."""
        svc = NISTMeasureService()
        metrics = [
            {
                "metric_name": "accuracy",
                "metric_value": 0.70,
                "threshold_min": 0.90,
                "threshold_max": 1.0,
            },
            {
                "metric_name": "latency",
                "metric_value": 150,
                "threshold_min": 0,
                "threshold_max": 100,
            },
        ]

        result = svc._evaluate_performance_thresholds(metrics)

        assert result.allowed is False
        assert result.details["out_of_threshold"] == 2
        assert "accuracy" in result.details["violations"]
        assert "latency" in result.details["violations"]

    def test_bias_detection_pass(self):
        """Test MEASURE-2.1 passes with adequate demographic coverage."""
        svc = NISTMeasureService()
        metrics = [
            {
                "ai_system_id": str(SYSTEM_ID),
                "metric_type": "bias_score",
                "metric_name": "bias_male",
                "metric_value": 0.05,
                "demographic_group": "gender:male",
                "threshold_max": 0.10,
            },
            {
                "ai_system_id": str(SYSTEM_ID),
                "metric_type": "bias_score",
                "metric_name": "bias_female",
                "metric_value": 0.04,
                "demographic_group": "gender:female",
                "threshold_max": 0.10,
            },
        ]
        ai_systems = [{"id": str(SYSTEM_ID), "name": "Model A"}]

        result = svc._evaluate_bias_detection(metrics, ai_systems)

        assert result.allowed is True
        assert result.control_code == "MEASURE-2.1"
        assert result.details["systems_with_coverage"] == 1

    def test_bias_detection_fail_insufficient_groups(self):
        """Test MEASURE-2.1 fails when system has < 2 demographic groups."""
        svc = NISTMeasureService()
        metrics = [
            {
                "ai_system_id": str(SYSTEM_ID),
                "metric_type": "bias_score",
                "metric_name": "bias_male",
                "metric_value": 0.05,
                "demographic_group": "gender:male",
                "threshold_max": 0.10,
            },
        ]
        ai_systems = [{"id": str(SYSTEM_ID), "name": "Model A"}]

        result = svc._evaluate_bias_detection(metrics, ai_systems)

        assert result.allowed is False
        assert "Model A" in result.details["systems_lacking_coverage"]

    def test_disparity_analysis_pass(self):
        """Test MEASURE-2.2 passes when disparity within 4/5ths rule."""
        svc = NISTMeasureService()
        metrics = [
            {
                "ai_system_id": str(SYSTEM_ID),
                "metric_type": "accuracy",
                "metric_value": 0.90,
                "demographic_group": "group_a",
            },
            {
                "ai_system_id": str(SYSTEM_ID),
                "metric_type": "accuracy",
                "metric_value": 0.88,
                "demographic_group": "group_b",
            },
        ]
        ai_systems = [{"id": str(SYSTEM_ID), "name": "Model A"}]

        result = svc._evaluate_disparity_analysis(metrics, ai_systems)

        assert result.allowed is True
        assert result.control_code == "MEASURE-2.2"
        assert result.details["compliant_systems"] == 1

    @pytest.mark.asyncio
    async def test_metric_trending_sufficient(self, service, mock_db):
        """Test MEASURE-3.1 passes with >= 3 data points per key metric."""
        rows = [
            (SYSTEM_ID, "accuracy", 5),
            (SYSTEM_ID, "bias_score", 3),
        ]

        mock_db.execute = AsyncMock(return_value=_mock_all(rows))

        result = await service._evaluate_metric_trending(PROJECT_ID, mock_db)

        assert result.allowed is True
        assert result.control_code == "MEASURE-3.1"
        assert result.details["sufficient_trending"] == 2
        assert len(result.details["insufficient_trending"]) == 0

    @pytest.mark.asyncio
    async def test_metric_trending_insufficient(self, service, mock_db):
        """Test MEASURE-3.1 fails with < 3 data points for some key metrics."""
        rows = [
            (SYSTEM_ID, "accuracy", 5),
            (SYSTEM_ID, "bias_score", 1),
        ]

        mock_db.execute = AsyncMock(return_value=_mock_all(rows))

        result = await service._evaluate_metric_trending(PROJECT_ID, mock_db)

        assert result.allowed is False
        assert result.details["sufficient_trending"] == 1
        assert len(result.details["insufficient_trending"]) == 1
        assert "bias_score" in result.details["insufficient_trending"][0]
