"""
Unit Tests for Planning Orchestrator Service

SDLC Stage: 04 - BUILD
Sprint: 98 - Planning Sub-agent Implementation Part 1
Framework: SDLC 5.2.0
Epic: EP-10 Planning Mode with Sub-agent Orchestration

Purpose:
Comprehensive unit tests for PlanningOrchestratorService.
Tests sub-agent orchestration, pattern synthesis, and plan generation.

Coverage Target: 80%+
Reference: ADR-034-Planning-Subagent-Orchestration
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.schemas.planning_subagent import (
    ConformanceLevel,
    ExploreAgentType,
    ExploreResult,
    ExtractedPattern,
    PatternCategory,
    PlanningRequest,
    PlanningStatus,
)
from app.services.planning_orchestrator_service import (
    PlanningOrchestratorService,
    create_planning_orchestrator_service,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_pattern_service():
    """Create a mock PatternExtractionService."""
    service = MagicMock()
    service.search_similar_implementations = AsyncMock(
        return_value=ExploreResult(
            agent_type=ExploreAgentType.SIMILAR_IMPLEMENTATIONS,
            status="completed",
            patterns=[
                ExtractedPattern(
                    id="pattern_1",
                    category=PatternCategory.CODE_STYLE,
                    name="snake_case_functions",
                    description="Functions use snake_case naming",
                    source_file="app/services/user_service.py",
                    source_line=10,
                    code_snippet="def get_user_by_id(user_id: UUID):",
                    confidence=0.9,
                    occurrences=15,
                ),
                ExtractedPattern(
                    id="pattern_2",
                    category=PatternCategory.ERROR_HANDLING,
                    name="try_except_logging",
                    description="Errors are caught and logged with context",
                    source_file="app/services/auth_service.py",
                    source_line=25,
                    code_snippet="try:\\n    ...",
                    confidence=0.85,
                    occurrences=12,
                ),
            ],
            files_searched=50,
            files_relevant=10,
            execution_time_ms=1500,
            search_queries=["Similar implementation search"],
        )
    )
    return service


@pytest.fixture
def mock_adr_service():
    """Create a mock ADRScannerService."""
    service = MagicMock()
    service.find_related_adrs = AsyncMock(
        return_value=ExploreResult(
            agent_type=ExploreAgentType.ADR_PATTERNS,
            status="completed",
            patterns=[
                ExtractedPattern(
                    id="adr_1",
                    category=PatternCategory.ARCHITECTURE,
                    name="ADR-007",
                    description="Multi-provider AI fallback chain",
                    source_file="docs/02-design/03-ADRs/ADR-007.md",
                    confidence=0.8,
                    occurrences=1,
                ),
            ],
            files_searched=20,
            files_relevant=5,
            execution_time_ms=500,
            search_queries=["ADR scan"],
        )
    )
    return service


@pytest.fixture
def mock_test_service():
    """Create a mock TestPatternService."""
    service = MagicMock()
    service.find_test_patterns = AsyncMock(
        return_value=ExploreResult(
            agent_type=ExploreAgentType.TEST_PATTERNS,
            status="completed",
            patterns=[
                ExtractedPattern(
                    id="test_1",
                    category=PatternCategory.TESTING,
                    name="pytest_fixture",
                    description="Pytest fixture for test setup",
                    source_file="tests/unit/test_user.py",
                    code_snippet="@pytest.fixture\\ndef user():",
                    confidence=0.95,
                    occurrences=30,
                ),
            ],
            files_searched=100,
            files_relevant=25,
            execution_time_ms=800,
            search_queries=["Test pattern scan"],
        )
    )
    return service


@pytest.fixture
def orchestrator_service(mock_pattern_service, mock_adr_service, mock_test_service):
    """Create PlanningOrchestratorService with mocked dependencies."""
    return PlanningOrchestratorService(
        pattern_service=mock_pattern_service,
        adr_service=mock_adr_service,
        test_service=mock_test_service,
    )


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        # Create basic project structure
        (project_path / "app").mkdir()
        (project_path / "app" / "services").mkdir(parents=True)
        (project_path / "tests").mkdir()
        (project_path / "docs").mkdir()
        # Create a sample Python file
        (project_path / "app" / "services" / "user_service.py").write_text(
            "def get_user_by_id(user_id: str):\n    return None\n"
        )
        yield project_path


# =============================================================================
# Test: Basic Planning Execution
# =============================================================================


@pytest.mark.asyncio
async def test_plan_basic_execution(orchestrator_service, temp_project_dir):
    """Test basic planning execution completes successfully."""
    request = PlanningRequest(
        task="Add user authentication with JWT tokens",
        project_path=str(temp_project_dir),
        depth=3,
        include_tests=True,
        include_adrs=True,
    )

    result = await orchestrator_service.plan(request)

    assert result is not None
    assert result.status == PlanningStatus.AWAITING_APPROVAL
    assert result.task == request.task
    assert isinstance(result.id, UUID)
    assert result.execution_time_ms > 0


@pytest.mark.asyncio
async def test_plan_extracts_patterns(orchestrator_service, temp_project_dir):
    """Test that planning extracts patterns from codebase."""
    request = PlanningRequest(
        task="Refactor user service to use repository pattern",
        project_path=str(temp_project_dir),
    )

    result = await orchestrator_service.plan(request)

    assert result.patterns is not None
    assert result.patterns.total_patterns_found >= 1
    assert result.patterns.total_files_scanned > 0
    assert len(result.patterns.patterns) > 0


@pytest.mark.asyncio
async def test_plan_generates_implementation_plan(orchestrator_service, temp_project_dir):
    """Test that planning generates an implementation plan."""
    request = PlanningRequest(
        task="Add OAuth2 authentication with Google provider",
        project_path=str(temp_project_dir),
    )

    result = await orchestrator_service.plan(request)

    assert result.plan is not None
    assert len(result.plan.steps) >= 1
    assert result.plan.total_estimated_loc >= 0
    assert result.plan.total_estimated_hours >= 0
    assert result.plan.summary is not None


@pytest.mark.asyncio
async def test_plan_calculates_conformance(orchestrator_service, temp_project_dir):
    """Test that planning calculates conformance score."""
    request = PlanningRequest(
        task="Add unit tests for payment service",
        project_path=str(temp_project_dir),
    )

    result = await orchestrator_service.plan(request)

    assert result.conformance is not None
    assert 0 <= result.conformance.score <= 100
    assert result.conformance.level in [
        ConformanceLevel.EXCELLENT,
        ConformanceLevel.GOOD,
        ConformanceLevel.FAIR,
        ConformanceLevel.POOR,
    ]


# =============================================================================
# Test: Sub-agent Spawning
# =============================================================================


@pytest.mark.asyncio
async def test_plan_spawns_all_subagents(orchestrator_service, temp_project_dir):
    """Test that planning spawns pattern, ADR, and test sub-agents."""
    request = PlanningRequest(
        task="Implement caching layer",
        project_path=str(temp_project_dir),
        include_tests=True,
        include_adrs=True,
    )

    result = await orchestrator_service.plan(request)

    # Check all services were called
    orchestrator_service.pattern_service.search_similar_implementations.assert_called_once()
    orchestrator_service.adr_service.find_related_adrs.assert_called_once()
    orchestrator_service.test_service.find_test_patterns.assert_called_once()


@pytest.mark.asyncio
async def test_plan_without_adrs(orchestrator_service, temp_project_dir):
    """Test planning without ADR analysis."""
    request = PlanningRequest(
        task="Add logging middleware",
        project_path=str(temp_project_dir),
        include_adrs=False,
    )

    result = await orchestrator_service.plan(request)

    orchestrator_service.adr_service.find_related_adrs.assert_not_called()
    assert result.status == PlanningStatus.AWAITING_APPROVAL


@pytest.mark.asyncio
async def test_plan_without_tests(orchestrator_service, temp_project_dir):
    """Test planning without test pattern analysis."""
    request = PlanningRequest(
        task="Add rate limiting",
        project_path=str(temp_project_dir),
        include_tests=False,
    )

    result = await orchestrator_service.plan(request)

    orchestrator_service.test_service.find_test_patterns.assert_not_called()
    assert result.status == PlanningStatus.AWAITING_APPROVAL


# =============================================================================
# Test: Pattern Synthesis
# =============================================================================


@pytest.mark.asyncio
async def test_pattern_deduplication(orchestrator_service, temp_project_dir):
    """Test that duplicate patterns are merged."""
    # Configure mock to return duplicate pattern names
    orchestrator_service.pattern_service.search_similar_implementations = AsyncMock(
        return_value=ExploreResult(
            agent_type=ExploreAgentType.SIMILAR_IMPLEMENTATIONS,
            status="completed",
            patterns=[
                ExtractedPattern(
                    id="p1",
                    category=PatternCategory.CODE_STYLE,
                    name="snake_case",
                    description="Snake case naming",
                    source_file="file1.py",
                    confidence=0.9,
                    occurrences=5,
                ),
                ExtractedPattern(
                    id="p2",
                    category=PatternCategory.CODE_STYLE,
                    name="snake_case",  # Duplicate name
                    description="Snake case in other file",
                    source_file="file2.py",
                    confidence=0.85,
                    occurrences=3,
                ),
            ],
            files_searched=10,
            files_relevant=2,
        )
    )

    request = PlanningRequest(
        task="Test pattern deduplication",
        project_path=str(temp_project_dir),
        include_adrs=False,
        include_tests=False,
    )

    result = await orchestrator_service.plan(request)

    # Should have only one "snake_case" pattern with increased occurrences
    snake_case_patterns = [
        p for p in result.patterns.patterns if p.name == "snake_case"
    ]
    assert len(snake_case_patterns) == 1
    assert snake_case_patterns[0].occurrences >= 6  # 5 + 1 (increment)


# =============================================================================
# Test: Plan Approval
# =============================================================================


@pytest.mark.asyncio
async def test_approve_plan(orchestrator_service, temp_project_dir):
    """Test approving a planning session."""
    request = PlanningRequest(
        task="Add feature flag system",
        project_path=str(temp_project_dir),
    )

    result = await orchestrator_service.plan(request)
    planning_id = result.id

    # Approve the plan
    approved_result = await orchestrator_service.approve_plan(
        planning_id=planning_id,
        approved=True,
        notes="Looks good",
        approved_by=uuid4(),
    )

    assert approved_result.status == PlanningStatus.APPROVED
    assert approved_result.approved_at is not None


@pytest.mark.asyncio
async def test_reject_plan(orchestrator_service, temp_project_dir):
    """Test rejecting a planning session."""
    request = PlanningRequest(
        task="Implement notification system",
        project_path=str(temp_project_dir),
    )

    result = await orchestrator_service.plan(request)
    planning_id = result.id

    # Reject the plan
    rejected_result = await orchestrator_service.approve_plan(
        planning_id=planning_id,
        approved=False,
        notes="Need more detail on step 2",
    )

    assert rejected_result.status == PlanningStatus.REJECTED
    assert rejected_result.rejection_reason == "Need more detail on step 2"


@pytest.mark.asyncio
async def test_approve_nonexistent_plan(orchestrator_service):
    """Test approving a non-existent planning session raises error."""
    fake_id = uuid4()

    with pytest.raises(ValueError) as exc_info:
        await orchestrator_service.approve_plan(
            planning_id=fake_id,
            approved=True,
        )

    assert "not found" in str(exc_info.value).lower()


# =============================================================================
# Test: Session Management
# =============================================================================


@pytest.mark.asyncio
async def test_get_session(orchestrator_service, temp_project_dir):
    """Test retrieving a planning session by ID."""
    request = PlanningRequest(
        task="Add email service",
        project_path=str(temp_project_dir),
    )

    result = await orchestrator_service.plan(request)

    retrieved = orchestrator_service.get_session(result.id)

    assert retrieved is not None
    assert retrieved.id == result.id
    assert retrieved.task == result.task


@pytest.mark.asyncio
async def test_list_sessions(orchestrator_service, temp_project_dir):
    """Test listing all active sessions."""
    # Create multiple sessions
    for task in ["Task 1", "Task 2", "Task 3"]:
        request = PlanningRequest(
            task=task * 5,  # Min 10 chars
            project_path=str(temp_project_dir),
        )
        await orchestrator_service.plan(request)

    sessions = orchestrator_service.list_sessions()

    assert len(sessions) >= 3


# =============================================================================
# Test: Error Handling
# =============================================================================


@pytest.mark.asyncio
async def test_plan_invalid_path():
    """Test planning with non-existent path."""
    orchestrator = PlanningOrchestratorService()
    request = PlanningRequest(
        task="Test with invalid path",
        project_path="/nonexistent/path/that/does/not/exist",
    )

    with pytest.raises(ValueError) as exc_info:
        await orchestrator.plan(request)

    assert "does not exist" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_plan_handles_subagent_failure(temp_project_dir):
    """Test that planning handles sub-agent failures gracefully."""
    # Create orchestrator with failing pattern service
    pattern_service = MagicMock()
    pattern_service.search_similar_implementations = AsyncMock(
        side_effect=Exception("Pattern extraction failed")
    )

    adr_service = MagicMock()
    adr_service.find_related_adrs = AsyncMock(
        return_value=ExploreResult(
            agent_type=ExploreAgentType.ADR_PATTERNS,
            status="completed",
            patterns=[],
            files_searched=0,
            files_relevant=0,
        )
    )

    test_service = MagicMock()
    test_service.find_test_patterns = AsyncMock(
        return_value=ExploreResult(
            agent_type=ExploreAgentType.TEST_PATTERNS,
            status="completed",
            patterns=[],
            files_searched=0,
            files_relevant=0,
        )
    )

    orchestrator = PlanningOrchestratorService(
        pattern_service=pattern_service,
        adr_service=adr_service,
        test_service=test_service,
    )

    request = PlanningRequest(
        task="Test sub-agent failure handling",
        project_path=str(temp_project_dir),
    )

    # Should still complete but with error results
    result = await orchestrator.plan(request)
    assert result is not None
    # One of the explore results should have error status
    error_results = [r for r in result.explore_results if r.status == "error"]
    assert len(error_results) >= 1


# =============================================================================
# Test: Conformance Scoring
# =============================================================================


@pytest.mark.asyncio
async def test_conformance_excellent_score(orchestrator_service, temp_project_dir):
    """Test conformance scoring for well-aligned plans."""
    # Configure high pattern coverage
    orchestrator_service.pattern_service.search_similar_implementations = AsyncMock(
        return_value=ExploreResult(
            agent_type=ExploreAgentType.SIMILAR_IMPLEMENTATIONS,
            status="completed",
            patterns=[
                ExtractedPattern(
                    id=f"p{i}",
                    category=PatternCategory.CODE_STYLE,
                    name=f"pattern_{i}",
                    description=f"Pattern {i}",
                    source_file=f"file{i}.py",
                    confidence=0.9,
                    occurrences=10,
                )
                for i in range(10)
            ],
            files_searched=100,
            files_relevant=50,
        )
    )

    request = PlanningRequest(
        task="Add small utility function",
        project_path=str(temp_project_dir),
    )

    result = await orchestrator_service.plan(request)

    # Should have good conformance
    assert result.conformance.score >= 50


# =============================================================================
# Test: Factory Function
# =============================================================================


def test_create_planning_orchestrator_service():
    """Test factory function creates service with default dependencies."""
    service = create_planning_orchestrator_service()

    assert service is not None
    assert service.pattern_service is not None
    assert service.adr_service is not None
    assert service.test_service is not None


# =============================================================================
# Test: Risk Identification
# =============================================================================


@pytest.mark.asyncio
async def test_identifies_security_risks(orchestrator_service, temp_project_dir):
    """Test that security-related tasks are flagged."""
    request = PlanningRequest(
        task="Add authentication and password hashing",
        project_path=str(temp_project_dir),
    )

    result = await orchestrator_service.plan(request)

    # Should identify security risk
    security_risks = [r for r in result.plan.risks if "security" in r.lower()]
    assert len(security_risks) >= 1


@pytest.mark.asyncio
async def test_identifies_database_risks(orchestrator_service, temp_project_dir):
    """Test that database-related tasks are flagged."""
    request = PlanningRequest(
        task="Add database migration for user schema",
        project_path=str(temp_project_dir),
    )

    result = await orchestrator_service.plan(request)

    # Should identify database risk
    db_risks = [r for r in result.plan.risks if "database" in r.lower()]
    assert len(db_risks) >= 1


# =============================================================================
# Test: Auto-Approve Mode
# =============================================================================


@pytest.mark.asyncio
async def test_auto_approve_mode(orchestrator_service, temp_project_dir):
    """Test auto-approve mode doesn't require manual approval."""
    request = PlanningRequest(
        task="Add simple utility function",
        project_path=str(temp_project_dir),
        auto_approve=True,
    )

    result = await orchestrator_service.plan(request)

    assert result.requires_approval is False
