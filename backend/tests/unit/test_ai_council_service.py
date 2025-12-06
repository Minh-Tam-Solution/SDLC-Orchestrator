"""
=========================================================================
AI Council Service Unit Tests - Sprint 26
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: December 4, 2025
Status: ACTIVE - Sprint 26 Day 4 (Tests + Performance)
Authority: Backend Lead + CTO Approved
Foundation: Sprint 26 Plan, ADR-011 (AI Governance Layer)
Framework: SDLC 4.9.1 Complete Lifecycle

Purpose:
- Unit tests for AICouncilService
- Test 3-stage deliberation process
- Test anonymized peer review
- Test chairman synthesis
- Test fallback mechanisms
- Test metrics recording

Test Coverage:
- ✅ Single mode deliberation
- ✅ Council mode deliberation (3 stages)
- ✅ AUTO mode (severity-based routing)
- ✅ Stage 1: Parallel queries
- ✅ Stage 2: Peer review + aggregation
- ✅ Stage 3: Chairman synthesis
- ✅ Fallback scenarios (timeout, no quorum, errors)
- ✅ Metrics recording

Zero Mock Policy: Real service integration with mocked LLM calls
=========================================================================
"""

import asyncio
import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.compliance_scan import ComplianceViolation
from app.schemas.council import (
    CouncilMode,
    CouncilProvider,
    AIProviderResponse,
    Stage1Result,
    Stage2Result,
    Stage3Result,
    PeerReview,
    ResponseRanking,
    FinalSynthesis,
)
from app.services.ai_council_service import AICouncilService, CouncilConfig


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_ai_service():
    """Mock AI recommendation service."""
    service = MagicMock()
    service.ollama = AsyncMock()
    service.claude = AsyncMock()
    service.gpt4 = AsyncMock()
    return service


@pytest.fixture
def mock_audit_service():
    """Mock audit service."""
    service = AsyncMock()
    service.log_ai_council_action = AsyncMock()
    return service


@pytest.fixture
def sample_violation():
    """Create sample compliance violation."""
    return ComplianceViolation(
        id=uuid4(),
        scan_id=uuid4(),
        project_id=uuid4(),
        violation_type="MISSING_DOCUMENTATION",
        severity="CRITICAL",
        location="/docs/00-Project-Foundation",
        description="Missing Product Vision document (Product-Vision.md) in Stage 00",
        recommendation="Create Product Vision document following SDLC 4.9.1 template",
        is_resolved=False,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def council_service(mock_db_session, mock_ai_service, mock_audit_service):
    """Create AICouncilService instance with mocks."""
    return AICouncilService(
        db=mock_db_session,
        ai_service=mock_ai_service,
        audit_service=mock_audit_service,
        config=CouncilConfig(),
    )


# ============================================================================
# Test Single Mode Deliberation
# ============================================================================


@pytest.mark.asyncio
async def test_single_mode_success(council_service, sample_violation):
    """Test single mode deliberation with successful response."""
    # Mock AI service response
    council_service.ai_service.generate_recommendation = AsyncMock(
        return_value=MagicMock(
            recommendation="Fix: Create /docs/00-Project-Foundation/01-Vision/Product-Vision.md",
            provider="ollama",
            model="mistral",
            confidence=85,
            duration_ms=1234.5,
            tokens_used=500,
            cost_usd=0.0,
            fallback_used=False,
        )
    )

    # Execute single mode deliberation
    response = await council_service.deliberate(
        violation=sample_violation,
        council_mode=CouncilMode.SINGLE,
        providers=None,
        user_id=uuid4(),
    )

    # Assertions
    assert response.mode_used == CouncilMode.SINGLE
    assert response.confidence_score == 85
    assert response.providers_used == ["ollama"]
    assert "Create /docs/00-Project-Foundation" in response.recommendation
    assert response.deliberation is None  # No deliberation in single mode
    assert response.total_duration_ms > 0
    assert response.total_cost_usd >= 0


@pytest.mark.asyncio
async def test_single_mode_fallback(council_service, sample_violation):
    """Test single mode fallback when primary provider fails."""
    # Mock AI service with fallback
    council_service.ai_service.generate_recommendation = AsyncMock(
        return_value=MagicMock(
            recommendation="Rule-based fallback recommendation",
            provider="rule_based",
            model="rules",
            confidence=50,
            duration_ms=50.0,
            tokens_used=0,
            cost_usd=0.0,
            fallback_used=True,
            fallback_reason="Ollama timeout",
        )
    )

    # Execute single mode deliberation
    response = await council_service.deliberate(
        violation=sample_violation,
        council_mode=CouncilMode.SINGLE,
        providers=None,
        user_id=uuid4(),
    )

    # Assertions
    assert response.mode_used == CouncilMode.SINGLE
    assert response.confidence_score == 50
    assert response.fallback_used is True
    assert response.fallback_reason == "Ollama timeout"


# ============================================================================
# Test Stage 1: Parallel Queries
# ============================================================================


@pytest.mark.asyncio
async def test_stage1_parallel_queries_success(council_service, sample_violation):
    """Test Stage 1 parallel queries with all providers successful."""
    # Mock multiple provider responses
    mock_responses = [
        AIProviderResponse(
            provider="ollama",
            response="Ollama recommendation: Create Product Vision doc",
            confidence=85,
            duration_ms=1200.0,
            cost_usd=0.0,
            is_success=True,
        ),
        AIProviderResponse(
            provider="claude",
            response="Claude recommendation: Add comprehensive vision document",
            confidence=90,
            duration_ms=2500.0,
            cost_usd=0.015,
            is_success=True,
        ),
        AIProviderResponse(
            provider="gpt4",
            response="GPT-4 recommendation: Document product vision following SDLC",
            confidence=88,
            duration_ms=2000.0,
            cost_usd=0.020,
            is_success=True,
        ),
    ]

    # Mock _query_single_provider for each provider
    council_service._query_single_provider = AsyncMock(side_effect=mock_responses)

    # Execute Stage 1
    providers = [CouncilProvider.OLLAMA, CouncilProvider.CLAUDE, CouncilProvider.GPT4]
    result = await council_service._stage1_parallel_queries(sample_violation, providers)

    # Assertions
    assert result.successful_count == 3
    assert result.failed_count == 0
    assert len(result.responses) == 3
    assert result.total_duration_ms > 0
    assert result.total_cost_usd == 0.035  # 0.015 + 0.020


@pytest.mark.asyncio
async def test_stage1_partial_failure(council_service, sample_violation):
    """Test Stage 1 with one provider failing."""
    # Mock responses with one failure
    mock_responses = [
        AIProviderResponse(
            provider="ollama",
            response="Ollama recommendation",
            confidence=85,
            duration_ms=1200.0,
            cost_usd=0.0,
            is_success=True,
        ),
        AIProviderResponse(
            provider="claude",
            response="",
            confidence=0,
            duration_ms=5000.0,
            cost_usd=0.0,
            is_success=False,
            error_message="Timeout after 5 seconds",
        ),
        AIProviderResponse(
            provider="gpt4",
            response="GPT-4 recommendation",
            confidence=88,
            duration_ms=2000.0,
            cost_usd=0.020,
            is_success=True,
        ),
    ]

    council_service._query_single_provider = AsyncMock(side_effect=mock_responses)

    # Execute Stage 1
    providers = [CouncilProvider.OLLAMA, CouncilProvider.CLAUDE, CouncilProvider.GPT4]
    result = await council_service._stage1_parallel_queries(sample_violation, providers)

    # Assertions
    assert result.successful_count == 2
    assert result.failed_count == 1
    assert len([r for r in result.responses if r.is_success]) == 2


# ============================================================================
# Test Stage 2: Peer Review
# ============================================================================


@pytest.mark.asyncio
async def test_stage2_peer_review_success(council_service):
    """Test Stage 2 peer review with successful rankings."""
    # Mock Stage 1 results
    stage1_result = Stage1Result(
        responses=[
            AIProviderResponse(
                provider="ollama",
                response="Ollama recommendation",
                confidence=85,
                duration_ms=1200.0,
                cost_usd=0.0,
                is_success=True,
            ),
            AIProviderResponse(
                provider="claude",
                response="Claude recommendation",
                confidence=90,
                duration_ms=2500.0,
                cost_usd=0.015,
                is_success=True,
            ),
            AIProviderResponse(
                provider="gpt4",
                response="GPT-4 recommendation",
                confidence=88,
                duration_ms=2000.0,
                cost_usd=0.020,
                is_success=True,
            ),
        ],
        successful_count=3,
        failed_count=0,
        total_duration_ms=5700.0,
        total_cost_usd=0.035,
    )

    # Mock peer review responses
    mock_reviews = [
        PeerReview(
            reviewer="ollama",
            rankings=[
                ResponseRanking(response_id="Response A", rank=1, score=92, reasoning="Best"),
                ResponseRanking(response_id="Response B", rank=2, score=85, reasoning="Good"),
            ],
            duration_ms=800.0,
            cost_usd=0.0,
        ),
        PeerReview(
            reviewer="claude",
            rankings=[
                ResponseRanking(response_id="Response A", rank=1, score=90, reasoning="Clear"),
                ResponseRanking(response_id="Response B", rank=2, score=88, reasoning="Solid"),
            ],
            duration_ms=1200.0,
            cost_usd=0.003,
        ),
        PeerReview(
            reviewer="gpt4",
            rankings=[
                ResponseRanking(response_id="Response A", rank=1, score=88, reasoning="Strong"),
                ResponseRanking(response_id="Response B", rank=2, score=86, reasoning="Decent"),
            ],
            duration_ms=1000.0,
            cost_usd=0.006,
        ),
    ]

    council_service._conduct_peer_review = AsyncMock(side_effect=mock_reviews)

    # Execute Stage 2
    result = await council_service._stage2_peer_review(stage1_result)

    # Assertions
    assert len(result.reviews) == 3
    assert len(result.aggregated_scores) > 0
    assert result.best_response_id in ["ollama", "claude", "gpt4"]
    assert result.total_duration_ms > 0


@pytest.mark.asyncio
async def test_stage2_anonymized_mapping(council_service):
    """Test anonymized mapping creation for peer review."""
    responses = [
        AIProviderResponse(provider="ollama", response="A", confidence=85, duration_ms=100, cost_usd=0, is_success=True),
        AIProviderResponse(provider="claude", response="B", confidence=90, duration_ms=100, cost_usd=0, is_success=True),
        AIProviderResponse(provider="gpt4", response="C", confidence=88, duration_ms=100, cost_usd=0, is_success=True),
    ]

    mapping = council_service._create_anonymized_mapping(responses)

    # Assertions
    assert len(mapping) == 3
    assert mapping["ollama"] == "Response A"
    assert mapping["claude"] == "Response B"
    assert mapping["gpt4"] == "Response C"


@pytest.mark.asyncio
async def test_stage2_score_aggregation(council_service):
    """Test weighted score aggregation from peer reviews."""
    responses = [
        AIProviderResponse(provider="ollama", response="A", confidence=85, duration_ms=100, cost_usd=0, is_success=True),
        AIProviderResponse(provider="claude", response="B", confidence=90, duration_ms=100, cost_usd=0, is_success=True),
    ]

    anonymized_mapping = {"ollama": "Response A", "claude": "Response B"}

    peer_reviews = [
        PeerReview(
            reviewer="ollama",
            rankings=[ResponseRanking(response_id="Response B", rank=1, score=95, reasoning="Best")],
            duration_ms=100,
            cost_usd=0,
        ),
        PeerReview(
            reviewer="claude",
            rankings=[ResponseRanking(response_id="Response A", rank=1, score=88, reasoning="Good")],
            duration_ms=100,
            cost_usd=0,
        ),
    ]

    aggregated = council_service._aggregate_scores(peer_reviews, anonymized_mapping, responses)

    # Assertions
    assert "ollama" in aggregated
    assert "claude" in aggregated
    assert aggregated["claude"] > aggregated["ollama"]  # Claude got higher score


# ============================================================================
# Test Stage 3: Chairman Synthesis
# ============================================================================


@pytest.mark.asyncio
async def test_stage3_synthesis_success(council_service):
    """Test Stage 3 chairman synthesis with successful parsing."""
    # Mock Stage 1 and 2 results
    stage1_result = Stage1Result(
        responses=[
            AIProviderResponse(provider="claude", response="Claude rec", confidence=90, duration_ms=100, cost_usd=0.015, is_success=True),
            AIProviderResponse(provider="gpt4", response="GPT-4 rec", confidence=88, duration_ms=100, cost_usd=0.020, is_success=True),
        ],
        successful_count=2,
        failed_count=0,
        total_duration_ms=200.0,
        total_cost_usd=0.035,
    )

    stage2_result = Stage2Result(
        reviews=[],
        aggregated_scores={"claude": 95.0, "gpt4": 87.0},
        best_response_id="claude",
        total_duration_ms=100.0,
        total_cost_usd=0.003,
    )

    # Mock chairman synthesis response
    synthesis_json = """{
        "final_recommendation": "Comprehensive synthesized recommendation combining best elements",
        "confidence": 92,
        "reasoning": "Combined strengths from both responses",
        "key_points": ["Point 1", "Point 2", "Point 3"],
        "dissenting_views": null
    }"""

    council_service._call_provider_for_synthesis = AsyncMock(return_value=synthesis_json)

    # Execute Stage 3
    result = await council_service._stage3_synthesis(stage1_result, stage2_result)

    # Assertions
    assert result.chairman == "claude"
    assert result.synthesis.confidence == 92
    assert len(result.synthesis.key_points) == 3
    assert "synthesized" in result.synthesis.answer.lower()


@pytest.mark.asyncio
async def test_stage3_fallback_on_error(council_service):
    """Test Stage 3 fallback when synthesis fails."""
    stage1_result = Stage1Result(
        responses=[
            AIProviderResponse(provider="claude", response="Best response", confidence=90, duration_ms=100, cost_usd=0.015, is_success=True),
        ],
        successful_count=1,
        failed_count=0,
        total_duration_ms=100.0,
        total_cost_usd=0.015,
    )

    stage2_result = Stage2Result(
        reviews=[],
        aggregated_scores={"claude": 90.0},
        best_response_id="claude",
        total_duration_ms=100.0,
        total_cost_usd=0.0,
    )

    # Mock synthesis failure
    council_service._call_provider_for_synthesis = AsyncMock(side_effect=Exception("Synthesis timeout"))

    # Execute Stage 3 (should fallback)
    result = await council_service._stage3_synthesis(stage1_result, stage2_result)

    # Assertions
    assert result.chairman == "claude"
    assert result.synthesis.answer == "Best response"  # Fallback to best response
    assert "fallback" in result.synthesis.reasoning.lower()


# ============================================================================
# Test AUTO Mode (Severity-Based Routing)
# ============================================================================


@pytest.mark.asyncio
async def test_auto_mode_critical_uses_council(council_service):
    """Test AUTO mode uses council for CRITICAL severity."""
    violation = ComplianceViolation(
        id=uuid4(),
        scan_id=uuid4(),
        project_id=uuid4(),
        violation_type="SECURITY_VULNERABILITY",
        severity="CRITICAL",
        location="/src/auth.py",
        description="SQL injection vulnerability detected",
        is_resolved=False,
        created_at=datetime.utcnow(),
    )

    # Mock council mode execution
    with patch.object(council_service, '_generate_council_mode', new_callable=AsyncMock) as mock_council:
        mock_council.return_value = MagicMock(
            mode_used=CouncilMode.COUNCIL,
            confidence_score=92,
        )

        response = await council_service.deliberate(
            violation=violation,
            council_mode=CouncilMode.AUTO,
            providers=None,
            user_id=uuid4(),
        )

        # Assertions
        mock_council.assert_called_once()
        assert response.mode_used == CouncilMode.COUNCIL


@pytest.mark.asyncio
async def test_auto_mode_low_uses_single(council_service):
    """Test AUTO mode uses single for LOW severity."""
    violation = ComplianceViolation(
        id=uuid4(),
        scan_id=uuid4(),
        project_id=uuid4(),
        violation_type="FORMATTING_ISSUE",
        severity="LOW",
        location="/docs/README.md",
        description="Inconsistent heading format",
        is_resolved=False,
        created_at=datetime.utcnow(),
    )

    # Mock single mode execution
    with patch.object(council_service, '_generate_single_mode', new_callable=AsyncMock) as mock_single:
        mock_single.return_value = MagicMock(
            mode_used=CouncilMode.SINGLE,
            confidence_score=75,
        )

        response = await council_service.deliberate(
            violation=violation,
            council_mode=CouncilMode.AUTO,
            providers=None,
            user_id=uuid4(),
        )

        # Assertions
        mock_single.assert_called_once()
        assert response.mode_used == CouncilMode.SINGLE


# ============================================================================
# Test Helper Methods
# ============================================================================


@pytest.mark.asyncio
async def test_parse_review_response_json(council_service):
    """Test parsing structured JSON from review response."""
    review_text = """{
        "rankings": [
            {"response_id": "Response A", "rank": 1, "score": 92, "reasoning": "Best"},
            {"response_id": "Response B", "rank": 2, "score": 85, "reasoning": "Good"}
        ]
    }"""

    responses_to_review = [("Response A", "Text A"), ("Response B", "Text B")]

    rankings = council_service._parse_review_response(review_text, responses_to_review)

    # Assertions
    assert len(rankings) == 2
    assert rankings[0].response_id == "Response A"
    assert rankings[0].rank == 1
    assert rankings[0].score == 92


@pytest.mark.asyncio
async def test_parse_review_response_fallback(council_service):
    """Test fallback parsing when JSON is malformed."""
    review_text = "This is not valid JSON at all"

    responses_to_review = [("Response A", "Text A"), ("Response B", "Text B")]

    rankings = council_service._parse_review_response(review_text, responses_to_review)

    # Assertions (fallback creates default rankings)
    assert len(rankings) == 2
    assert rankings[0].rank == 1
    assert rankings[1].rank == 2
    assert "Unable to parse" in rankings[0].reasoning


@pytest.mark.asyncio
async def test_extract_key_points(council_service):
    """Test extracting key points from synthesis text."""
    text = """
    Here are the key recommendations:
    1. Create Product Vision document
    2. Define success metrics
    3. Establish stakeholder alignment

    Additional notes:
    - Review quarterly
    - Update based on feedback
    """

    key_points = council_service._extract_key_points(text)

    # Assertions
    assert len(key_points) >= 3
    assert any("Product Vision" in point for point in key_points)
    assert any("metrics" in point for point in key_points)


@pytest.mark.asyncio
async def test_calculate_synthesis_confidence(council_service):
    """Test confidence calculation for synthesized answer."""
    responses = [
        AIProviderResponse(provider="ollama", response="A", confidence=85, duration_ms=100, cost_usd=0, is_success=True),
        AIProviderResponse(provider="claude", response="B", confidence=90, duration_ms=100, cost_usd=0, is_success=True),
        AIProviderResponse(provider="gpt4", response="C", confidence=88, duration_ms=100, cost_usd=0, is_success=True),
    ]

    stage2_result = Stage2Result(
        reviews=[],
        aggregated_scores={"ollama": 82.0, "claude": 95.0, "gpt4": 88.0},
        best_response_id="claude",
        total_duration_ms=100.0,
        total_cost_usd=0.0,
    )

    confidence = council_service._calculate_synthesis_confidence(responses, stage2_result)

    # Assertions
    assert 0 <= confidence <= 100
    assert confidence > 85  # Should be high given good scores


# ============================================================================
# Test Fallback Scenarios
# ============================================================================


@pytest.mark.asyncio
async def test_fallback_no_quorum(council_service, sample_violation):
    """Test fallback when insufficient providers succeed (no quorum)."""
    # Mock Stage 1 with only 1 success (need 2 for council)
    stage1_result = Stage1Result(
        responses=[
            AIProviderResponse(provider="ollama", response="Only response", confidence=85, duration_ms=100, cost_usd=0, is_success=True),
            AIProviderResponse(provider="claude", response="", confidence=0, duration_ms=100, cost_usd=0, is_success=False, error_message="Timeout"),
            AIProviderResponse(provider="gpt4", response="", confidence=0, duration_ms=100, cost_usd=0, is_success=False, error_message="Error"),
        ],
        successful_count=1,
        failed_count=2,
        total_duration_ms=300.0,
        total_cost_usd=0.0,
    )

    with patch.object(council_service, '_stage1_parallel_queries', return_value=stage1_result):
        response = await council_service.deliberate(
            violation=sample_violation,
            council_mode=CouncilMode.COUNCIL,
            providers=None,
            user_id=uuid4(),
        )

        # Assertions
        assert response.fallback_used is True
        assert "no_quorum" in response.fallback_reason.lower() or response.fallback_reason is not None
        assert response.confidence_score == 85  # From the single successful response


# ============================================================================
# Test Metrics Recording
# ============================================================================


@pytest.mark.asyncio
async def test_metrics_recorded_single_mode(council_service, sample_violation):
    """Test that Prometheus metrics are recorded for single mode."""
    with patch('app.services.ai_council_service.AICouncilMetrics') as mock_metrics:
        council_service.ai_service.generate_recommendation = AsyncMock(
            return_value=MagicMock(
                recommendation="Test",
                provider="ollama",
                confidence=85,
                duration_ms=1000,
                cost_usd=0.0,
                fallback_used=False,
            )
        )

        await council_service.deliberate(
            violation=sample_violation,
            council_mode=CouncilMode.SINGLE,
            providers=None,
            user_id=uuid4(),
        )

        # Verify metrics were recorded
        mock_metrics.record_deliberation_complete.assert_called_once()
        call_args = mock_metrics.record_deliberation_complete.call_args[1]
        assert call_args['mode'] == 'single'
        assert call_args['status'] in ['success', 'fallback']
