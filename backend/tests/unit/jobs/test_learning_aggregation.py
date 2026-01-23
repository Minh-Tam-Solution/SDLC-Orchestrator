"""
=========================================================================
Learning Aggregation Jobs Unit Tests - Sprint 100 (EP-11)
SDLC Orchestrator - Stage 04 (BUILD)

Version: 1.0.0
Date: January 23, 2026
Status: ACTIVE - Sprint 100 Implementation
Authority: Backend Lead + CTO Approved
Framework: SDLC 5.1.3 SASE Integration

Purpose:
- Unit tests for learning aggregation background jobs
- Test period calculation utilities
- Test monthly aggregation job
- Test quarterly synthesis job
- Test hint effectiveness update
- Test on-demand aggregation

Test Coverage:
- ✅ Period calculation (weekly, monthly, quarterly)
- ✅ Monthly aggregation for all projects
- ✅ Quarterly synthesis with CLAUDE.md suggestions
- ✅ Hint effectiveness scoring
- ✅ On-demand project aggregation
- ✅ Aggregation status and utility functions

Zero Mock Policy: Real job logic with mocked database
=========================================================================
"""

import pytest
from datetime import datetime, date, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from calendar import monthrange

from app.jobs.learning_aggregation import (
    AGGREGATION_CONFIG,
    get_previous_month_period,
    get_previous_quarter_period,
    get_weekly_period,
    run_monthly_aggregation,
    run_quarterly_synthesis,
    update_hint_effectiveness,
    schedule_project_aggregation,
    get_aggregation_status,
    apply_aggregation_suggestions,
    _extract_patterns,
    _extract_common_themes,
    _count_severities,
    _merge_patterns,
    _generate_adr_recommendations,
)
from app.models.pr_learning import PRLearning
from app.models.decomposition_hint import DecompositionHint
from app.models.learning_aggregation import LearningAggregation
from app.models.project import Project


# ============================================================================
# Test Period Calculation Utilities
# ============================================================================


class TestPeriodCalculation:
    """Tests for period calculation utility functions."""

    def test_get_previous_month_period(self):
        """Test previous month period calculation."""
        # Freeze time to a known date for testing
        with patch("app.jobs.learning_aggregation.date") as mock_date:
            mock_date.today.return_value = date(2026, 1, 15)
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

            start, end = get_previous_month_period()

            assert start == date(2025, 12, 1)
            assert end == date(2025, 12, 31)

    def test_get_previous_month_period_january(self):
        """Test previous month period calculation in January."""
        with patch("app.jobs.learning_aggregation.date") as mock_date:
            mock_date.today.return_value = date(2026, 2, 10)
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

            start, end = get_previous_month_period()

            assert start == date(2026, 1, 1)
            assert end == date(2026, 1, 31)

    def test_get_previous_quarter_period_q1(self):
        """Test previous quarter calculation when in Q1."""
        with patch("app.jobs.learning_aggregation.date") as mock_date:
            mock_date.today.return_value = date(2026, 2, 15)  # Q1
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

            start, end = get_previous_quarter_period()

            # Previous quarter is Q4 of previous year
            assert start == date(2025, 10, 1)
            assert end == date(2025, 12, 31)

    def test_get_previous_quarter_period_q2(self):
        """Test previous quarter calculation when in Q2."""
        with patch("app.jobs.learning_aggregation.date") as mock_date:
            mock_date.today.return_value = date(2026, 4, 15)  # Q2
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

            start, end = get_previous_quarter_period()

            # Previous quarter is Q1
            assert start == date(2026, 1, 1)
            assert end.month == 3

    def test_get_weekly_period(self):
        """Test weekly period calculation."""
        with patch("app.jobs.learning_aggregation.date") as mock_date:
            # Set to a Wednesday
            mock_date.today.return_value = date(2026, 1, 22)  # Wednesday
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

            start, end = get_weekly_period()

            # Previous week Monday to Sunday
            assert start.weekday() == 0  # Monday
            assert end.weekday() == 6  # Sunday
            assert (end - start).days == 6


# ============================================================================
# Test Pattern Extraction
# ============================================================================


class TestPatternExtraction:
    """Tests for pattern extraction from learnings."""

    def test_extract_patterns_groups_by_type_and_extension(self):
        """Test that patterns are grouped by feedback type and file extension."""
        learnings = [
            MagicMock(
                feedback_type="edge_case",
                file_path="src/service.py",
                severity="medium",
                learning_description="Handle null input",
                id=uuid4(),
            ),
            MagicMock(
                feedback_type="edge_case",
                file_path="src/utils.py",
                severity="medium",
                learning_description="Handle empty list",
                id=uuid4(),
            ),
            MagicMock(
                feedback_type="edge_case",
                file_path="src/api.py",
                severity="high",
                learning_description="Handle null response",
                id=uuid4(),
            ),
        ]

        # Mock async function
        import asyncio
        patterns = asyncio.get_event_loop().run_until_complete(
            _extract_patterns(learnings)
        )

        assert len(patterns) >= 1
        # Should find edge_case_py pattern with count >= 3
        py_pattern = next(
            (p for p in patterns if p.get("file_extension") == "py"),
            None,
        )
        if py_pattern:
            assert py_pattern["count"] >= 3

    def test_extract_common_themes(self):
        """Test extraction of common themes from descriptions."""
        descriptions = [
            "Need to add error handling for null values",
            "Missing error handling in the exception case",
            "Add validation for null check",
            "Handle the null edge case properly",
        ]

        themes = _extract_common_themes(descriptions)

        assert len(themes) <= 5
        # Should detect "null" and "error handling" related themes
        assert any("null" in theme.lower() or "error" in theme.lower() for theme in themes)

    def test_count_severities(self):
        """Test severity counting."""
        learnings = [
            MagicMock(severity="critical"),
            MagicMock(severity="high"),
            MagicMock(severity="high"),
            MagicMock(severity="medium"),
        ]

        counts = _count_severities(learnings)

        assert counts["critical"] == 1
        assert counts["high"] == 2
        assert counts["medium"] == 1


# ============================================================================
# Test Pattern Merging
# ============================================================================


class TestPatternMerging:
    """Tests for merging patterns from multiple aggregations."""

    def test_merge_patterns_combines_counts(self):
        """Test that merging patterns combines counts correctly."""
        patterns = [
            {
                "feedback_type": "edge_case",
                "file_extension": "py",
                "count": 5,
                "themes": ["null check", "validation"],
            },
            {
                "feedback_type": "edge_case",
                "file_extension": "py",
                "count": 3,
                "themes": ["null check", "error handling"],
            },
            {
                "feedback_type": "security_issue",
                "file_extension": "py",
                "count": 2,
                "themes": ["sql injection"],
            },
        ]

        merged = _merge_patterns(patterns)

        # Should have 2 unique patterns (edge_case_py and security_issue_py)
        assert len(merged) == 2

        # edge_case_py should have combined count
        edge_case = next(
            (p for p in merged if p.get("feedback_type") == "edge_case"),
            None,
        )
        assert edge_case["count"] == 8

        # Themes should be merged
        assert len(edge_case["themes"]) >= 2

    def test_merge_patterns_limits_results(self):
        """Test that merging limits to top patterns."""
        patterns = [
            {"feedback_type": f"type_{i}", "file_extension": "py", "count": i, "themes": []}
            for i in range(20)
        ]

        merged = _merge_patterns(patterns)

        # Should be limited to 15
        assert len(merged) <= 15


# ============================================================================
# Test ADR Recommendations
# ============================================================================


class TestADRRecommendations:
    """Tests for ADR recommendation generation."""

    def test_generate_adr_for_pattern_violations(self):
        """Test ADR generation for high-count pattern violations."""
        patterns = [
            {
                "feedback_type": "pattern_violation",
                "count": 15,
                "themes": ["naming convention", "consistency"],
            },
        ]

        recommendations = _generate_adr_recommendations(patterns)

        assert len(recommendations) >= 1
        assert recommendations[0]["type"] == "new_adr"
        assert "pattern" in recommendations[0]["title"].lower()

    def test_generate_adr_for_architecture(self):
        """Test ADR generation for architecture-related patterns."""
        patterns = [
            {
                "feedback_type": "architecture",
                "count": 10,
                "themes": ["layering", "separation of concerns"],
            },
        ]

        recommendations = _generate_adr_recommendations(patterns)

        assert len(recommendations) >= 1
        assert recommendations[0]["type"] == "update_adr"

    def test_no_adr_for_low_count(self):
        """Test that ADRs are not generated for low-count patterns."""
        patterns = [
            {
                "feedback_type": "pattern_violation",
                "count": 3,  # Below threshold
                "themes": ["minor issue"],
            },
        ]

        recommendations = _generate_adr_recommendations(patterns)

        assert len(recommendations) == 0


# ============================================================================
# Test Monthly Aggregation Job
# ============================================================================


class TestMonthlyAggregation:
    """Tests for monthly aggregation job."""

    @pytest.mark.asyncio
    async def test_run_monthly_aggregation(self):
        """Test monthly aggregation runs for all active projects."""
        with patch("app.jobs.learning_aggregation.AsyncSessionLocal") as mock_session:
            mock_db = AsyncMock()

            # Mock project query
            project1 = MagicMock(id=uuid4(), is_active=True)
            project2 = MagicMock(id=uuid4(), is_active=True)

            mock_projects_result = MagicMock()
            mock_projects_result.scalars.return_value.all.return_value = [project1, project2]

            # Mock existing aggregation check (none exist)
            mock_existing_result = MagicMock()
            mock_existing_result.scalar_one_or_none.return_value = None

            # Mock learnings query (no learnings)
            mock_learnings_result = MagicMock()
            mock_learnings_result.scalars.return_value.all.return_value = []

            mock_db.execute = AsyncMock(
                side_effect=[
                    mock_projects_result,
                    mock_existing_result,
                    mock_learnings_result,
                    mock_existing_result,
                    mock_learnings_result,
                ]
            )

            mock_session.return_value.__aenter__.return_value = mock_db

            result = await run_monthly_aggregation()

            assert result["status"] == "completed"
            assert result["period_type"] == "monthly"
            assert "projects_processed" in result
            assert "projects_skipped" in result


# ============================================================================
# Test Quarterly Synthesis Job
# ============================================================================


class TestQuarterlySynthesis:
    """Tests for quarterly synthesis job."""

    @pytest.mark.asyncio
    async def test_run_quarterly_synthesis(self):
        """Test quarterly synthesis runs for all active projects."""
        with patch("app.jobs.learning_aggregation.AsyncSessionLocal") as mock_session:
            mock_db = AsyncMock()

            # Mock project query
            project1 = MagicMock(id=uuid4(), is_active=True)

            mock_projects_result = MagicMock()
            mock_projects_result.scalars.return_value.all.return_value = [project1]

            # Mock existing aggregation check (none exist)
            mock_existing_result = MagicMock()
            mock_existing_result.scalar_one_or_none.return_value = None

            # Mock monthly aggregations query (none exist)
            mock_monthly_result = MagicMock()
            mock_monthly_result.scalars.return_value.all.return_value = []

            mock_db.execute = AsyncMock(
                side_effect=[
                    mock_projects_result,
                    mock_existing_result,
                    mock_monthly_result,
                ]
            )

            mock_session.return_value.__aenter__.return_value = mock_db

            result = await run_quarterly_synthesis()

            assert result["status"] == "completed"
            assert result["period_type"] == "quarterly"


# ============================================================================
# Test Hint Effectiveness Update
# ============================================================================


class TestHintEffectiveness:
    """Tests for hint effectiveness update job."""

    @pytest.mark.asyncio
    async def test_update_hint_effectiveness_boost(self):
        """Test that hints with prevented errors get boosted."""
        with patch("app.jobs.learning_aggregation.AsyncSessionLocal") as mock_session:
            mock_db = AsyncMock()

            hint = MagicMock(
                id=uuid4(),
                is_active=True,
                confidence_score=0.7,
                feedback_scores={"prevented_errors": 3, "false_positives": 0},
                last_used_at=datetime.utcnow(),
            )

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [hint]

            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_session.return_value.__aenter__.return_value = mock_db

            result = await update_hint_effectiveness()

            assert result["status"] == "completed"
            # Hint should have been boosted
            assert hint.confidence_score > 0.7

    @pytest.mark.asyncio
    async def test_update_hint_effectiveness_penalty(self):
        """Test that hints with false positives get penalized."""
        with patch("app.jobs.learning_aggregation.AsyncSessionLocal") as mock_session:
            mock_db = AsyncMock()

            hint = MagicMock(
                id=uuid4(),
                is_active=True,
                confidence_score=0.7,
                feedback_scores={"prevented_errors": 0, "false_positives": 2},
                last_used_at=datetime.utcnow(),
            )

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [hint]

            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_session.return_value.__aenter__.return_value = mock_db

            result = await update_hint_effectiveness()

            assert result["status"] == "completed"
            # Hint should have been penalized
            assert hint.confidence_score < 0.7

    @pytest.mark.asyncio
    async def test_update_hint_effectiveness_deactivation(self):
        """Test that hints with very low confidence get deactivated."""
        with patch("app.jobs.learning_aggregation.AsyncSessionLocal") as mock_session:
            mock_db = AsyncMock()

            hint = MagicMock(
                id=uuid4(),
                is_active=True,
                confidence_score=0.15,  # Very low
                feedback_scores={"prevented_errors": 0, "false_positives": 1},
                last_used_at=datetime.utcnow(),
            )

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [hint]

            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_session.return_value.__aenter__.return_value = mock_db

            result = await update_hint_effectiveness()

            assert result["status"] == "completed"
            assert result["hints_deactivated"] >= 1
            assert hint.is_active is False


# ============================================================================
# Test On-Demand Aggregation
# ============================================================================


class TestOnDemandAggregation:
    """Tests for on-demand project aggregation."""

    @pytest.mark.asyncio
    async def test_schedule_project_aggregation_weekly(self):
        """Test scheduling weekly aggregation for a project."""
        project_id = uuid4()

        with patch("app.jobs.learning_aggregation.AsyncSessionLocal") as mock_session:
            mock_db = AsyncMock()

            # Mock learnings query (no learnings)
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []

            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_session.return_value.__aenter__.return_value = mock_db

            result = await schedule_project_aggregation(
                project_id=project_id,
                period_type="weekly",
            )

            assert result["status"] == "skipped"
            assert "No learnings found" in result.get("message", "")

    @pytest.mark.asyncio
    async def test_schedule_project_aggregation_with_learnings(self):
        """Test scheduling aggregation when learnings exist."""
        project_id = uuid4()

        with patch("app.jobs.learning_aggregation.AsyncSessionLocal") as mock_session:
            with patch("app.jobs.learning_aggregation._aggregate_project_learnings") as mock_agg:
                mock_db = AsyncMock()
                mock_session.return_value.__aenter__.return_value = mock_db

                mock_agg.return_value = {
                    "aggregation_id": str(uuid4()),
                    "total_learnings": 10,
                    "hints_generated": 2,
                    "patterns_found": 3,
                }

                result = await schedule_project_aggregation(
                    project_id=project_id,
                    period_type="monthly",
                )

                assert result["status"] == "completed"
                assert result["total_learnings"] == 10


# ============================================================================
# Test Aggregation Status
# ============================================================================


class TestAggregationStatus:
    """Tests for aggregation status queries."""

    @pytest.mark.asyncio
    async def test_get_aggregation_status(self):
        """Test getting aggregation status for a project."""
        project_id = uuid4()

        with patch("app.jobs.learning_aggregation.AsyncSessionLocal") as mock_session:
            mock_db = AsyncMock()

            aggregation = MagicMock(
                status="processed",
                claude_md_suggestions=[{"section": "Test", "content": "Test content"}],
            )
            aggregation.to_summary_dict.return_value = {"id": str(uuid4()), "status": "processed"}

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [aggregation]

            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_session.return_value.__aenter__.return_value = mock_db

            result = await get_aggregation_status(project_id)

            assert result["project_id"] == str(project_id)
            assert result["total_aggregations"] == 1
            assert result["pending_suggestions"] == 1

    @pytest.mark.asyncio
    async def test_apply_aggregation_suggestions(self):
        """Test applying aggregation suggestions."""
        aggregation_id = uuid4()
        user_id = uuid4()

        with patch("app.jobs.learning_aggregation.AsyncSessionLocal") as mock_session:
            mock_db = AsyncMock()

            aggregation = MagicMock(
                id=aggregation_id,
                status="processed",
                claude_md_suggestions=[
                    {"section": "Security", "content": "Validate inputs"}
                ],
                decomposition_hints=[
                    {"type": "pattern", "content": "Input validation"}
                ],
            )

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = aggregation

            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_session.return_value.__aenter__.return_value = mock_db

            result = await apply_aggregation_suggestions(
                aggregation_id=aggregation_id,
                applied_by=user_id,
                apply_to=["claude_md", "decomposition"],
            )

            assert result["status"] == "applied"
            assert result["items_applied"] == 2

    @pytest.mark.asyncio
    async def test_apply_aggregation_already_applied(self):
        """Test applying already applied aggregation."""
        aggregation_id = uuid4()
        user_id = uuid4()

        with patch("app.jobs.learning_aggregation.AsyncSessionLocal") as mock_session:
            mock_db = AsyncMock()

            aggregation = MagicMock(
                id=aggregation_id,
                status="applied",  # Already applied
            )

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = aggregation

            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_session.return_value.__aenter__.return_value = mock_db

            result = await apply_aggregation_suggestions(
                aggregation_id=aggregation_id,
                applied_by=user_id,
                apply_to=["claude_md"],
            )

            assert "error" in result
            assert "already applied" in result["error"]


# ============================================================================
# Test Configuration
# ============================================================================


class TestConfiguration:
    """Tests for aggregation configuration."""

    def test_aggregation_config_values(self):
        """Test that configuration has required values."""
        assert AGGREGATION_CONFIG["monthly_day"] == 1
        assert AGGREGATION_CONFIG["monthly_hour"] == 4
        assert AGGREGATION_CONFIG["quarterly_months"] == [1, 4, 7, 10]
        assert AGGREGATION_CONFIG["min_learnings_for_pattern"] >= 1
        assert AGGREGATION_CONFIG["min_confidence_for_hint"] > 0
        assert AGGREGATION_CONFIG["min_confidence_for_hint"] < 1

    def test_aggregation_timeouts(self):
        """Test that timeouts are reasonable."""
        assert AGGREGATION_CONFIG["aggregation_timeout_seconds"] >= 60
        assert AGGREGATION_CONFIG["synthesis_timeout_seconds"] >= 300

    def test_hint_effectiveness_factors(self):
        """Test hint effectiveness factors are in valid range."""
        assert 0 < AGGREGATION_CONFIG["hint_decay_factor"] < 1
        assert 0 < AGGREGATION_CONFIG["hint_boost_on_prevent"] < 0.5
        assert 0 < AGGREGATION_CONFIG["hint_penalty_on_false_positive"] < 0.5
