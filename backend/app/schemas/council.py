"""
=========================================================================
AI Council Schemas - Multi-LLM Deliberation Types
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: December 6, 2025
Status: ACTIVE - Sprint 26 Day 1 (AI Council Service)
Authority: Backend Lead + CTO Approved
Foundation: ADR-007 (AI Context Engine), Sprint 26 Plan
Framework: SDLC 4.9.1 Complete Lifecycle

Purpose:
- Pydantic schemas for AI Council requests/responses
- Type definitions for 3-stage deliberation process
- Validation for council mode configuration

Deliberation Stages:
1. Parallel Queries: Query multiple LLMs simultaneously
2. Peer Review: Anonymized ranking of responses
3. Synthesis: Chairman produces final answer

Zero Mock Policy: 100% real implementation
=========================================================================
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enums
# ============================================================================


class CouncilMode(str, Enum):
    """Council execution mode."""

    SINGLE = "single"  # Use single provider (fast, cheap)
    COUNCIL = "council"  # Use 3-stage deliberation (accurate, expensive)
    AUTO = "auto"  # Auto-select based on severity


class DeliberationStage(str, Enum):
    """Stages in council deliberation."""

    STAGE_1_QUERIES = "stage_1_queries"
    STAGE_2_REVIEW = "stage_2_review"
    STAGE_3_SYNTHESIS = "stage_3_synthesis"
    COMPLETE = "complete"
    FAILED = "failed"


class CouncilProvider(str, Enum):
    """AI providers available for council."""

    OLLAMA = "ollama"
    CLAUDE = "claude"
    GPT4 = "gpt4"


# ============================================================================
# Request Schemas
# ============================================================================


class CouncilRequest(BaseModel):
    """Request to generate council recommendation."""

    violation_id: UUID = Field(
        ...,
        description="UUID of the compliance violation to analyze",
    )
    council_mode: CouncilMode = Field(
        default=CouncilMode.AUTO,
        description="Council execution mode",
    )
    providers: Optional[list[CouncilProvider]] = Field(
        default=None,
        description="Specific providers to use (default: all available)",
    )
    timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Maximum time for council deliberation",
    )

    @field_validator("providers")
    @classmethod
    def validate_providers(cls, v: Optional[list[CouncilProvider]]) -> Optional[list[CouncilProvider]]:
        """Ensure at least 2 providers for council mode."""
        if v is not None and len(v) < 2:
            raise ValueError("Council mode requires at least 2 providers")
        return v


class CouncilBatchRequest(BaseModel):
    """Request to generate council recommendations for multiple violations."""

    violation_ids: list[UUID] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of violation IDs to process",
    )
    council_mode: CouncilMode = Field(
        default=CouncilMode.AUTO,
        description="Council execution mode",
    )
    parallel_limit: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Max violations to process in parallel",
    )


# ============================================================================
# Response Schemas - Stage 1: Parallel Queries
# ============================================================================


class AIProviderResponse(BaseModel):
    """Response from a single AI provider."""

    provider: str = Field(..., description="Provider name (ollama, claude, gpt4)")
    model: str = Field(..., description="Model used for generation")
    response: str = Field(..., description="AI-generated recommendation")
    confidence: int = Field(
        ...,
        ge=0,
        le=100,
        description="Provider's confidence score (0-100)",
    )
    duration_ms: float = Field(..., description="Response time in milliseconds")
    tokens_used: int = Field(default=0, description="Total tokens consumed")
    cost_usd: float = Field(default=0.0, description="Cost in USD")
    error: Optional[str] = Field(default=None, description="Error message if failed")

    @property
    def is_success(self) -> bool:
        """Check if response was successful."""
        return self.error is None and len(self.response) > 0


class Stage1Result(BaseModel):
    """Result of Stage 1: Parallel Queries."""

    responses: list[AIProviderResponse] = Field(
        ...,
        description="Responses from all queried providers",
    )
    successful_count: int = Field(..., description="Number of successful responses")
    failed_count: int = Field(..., description="Number of failed responses")
    total_duration_ms: float = Field(..., description="Total stage duration")
    total_cost_usd: float = Field(..., description="Total cost for stage")

    @property
    def has_quorum(self) -> bool:
        """Check if we have enough responses for deliberation (2+)."""
        return self.successful_count >= 2


# ============================================================================
# Response Schemas - Stage 2: Peer Review
# ============================================================================


class ResponseRanking(BaseModel):
    """Ranking of a single response by a reviewer."""

    response_id: str = Field(
        ...,
        description="Anonymized response ID (Response A, B, C)",
    )
    rank: int = Field(
        ...,
        ge=1,
        le=5,
        description="Rank position (1 = best)",
    )
    score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Quality score (0-100)",
    )
    reasoning: str = Field(
        ...,
        description="Brief explanation for ranking",
    )


class PeerReview(BaseModel):
    """Peer review from one AI provider."""

    reviewer: str = Field(..., description="Reviewing provider name")
    rankings: list[ResponseRanking] = Field(
        ...,
        description="Rankings of all other responses",
    )
    duration_ms: float = Field(..., description="Review duration")
    cost_usd: float = Field(default=0.0, description="Cost in USD")


class Stage2Result(BaseModel):
    """Result of Stage 2: Peer Review."""

    reviews: list[PeerReview] = Field(
        ...,
        description="All peer reviews",
    )
    aggregated_scores: dict[str, float] = Field(
        ...,
        description="Aggregated scores per response (provider -> avg_score)",
    )
    best_response_id: str = Field(
        ...,
        description="ID of highest-scored response",
    )
    total_duration_ms: float = Field(..., description="Total stage duration")
    total_cost_usd: float = Field(..., description="Total cost for stage")


# ============================================================================
# Response Schemas - Stage 3: Synthesis
# ============================================================================


class FinalSynthesis(BaseModel):
    """Final synthesized answer from chairman."""

    answer: str = Field(..., description="Final synthesized recommendation")
    confidence: int = Field(
        ...,
        ge=0,
        le=100,
        description="Final confidence score (0-100)",
    )
    reasoning: str = Field(
        ...,
        description="Chairman's reasoning for synthesis",
    )
    key_points: list[str] = Field(
        default_factory=list,
        description="Key action points extracted",
    )
    dissenting_views: Optional[str] = Field(
        default=None,
        description="Notable disagreements between providers",
    )


class Stage3Result(BaseModel):
    """Result of Stage 3: Synthesis."""

    chairman: str = Field(..., description="Provider acting as chairman")
    synthesis: FinalSynthesis = Field(..., description="Final synthesis")
    duration_ms: float = Field(..., description="Synthesis duration")
    cost_usd: float = Field(default=0.0, description="Cost in USD")


# ============================================================================
# Full Council Response
# ============================================================================


class CouncilDeliberation(BaseModel):
    """Full deliberation record for transparency."""

    stage_1: Stage1Result = Field(..., description="Parallel query results")
    stage_2: Optional[Stage2Result] = Field(
        default=None,
        description="Peer review results (None if skipped)",
    )
    stage_3: Optional[Stage3Result] = Field(
        default=None,
        description="Synthesis results (None if skipped)",
    )


class CouncilResponse(BaseModel):
    """Full response from AI Council."""

    request_id: UUID = Field(..., description="Unique request identifier")
    violation_id: UUID = Field(..., description="Violation that was analyzed")
    mode_used: CouncilMode = Field(
        ...,
        description="Actual mode used (may differ from requested if auto)",
    )
    recommendation: str = Field(..., description="Final recommendation")
    confidence_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Final confidence score (0-100)",
    )
    providers_used: list[str] = Field(
        ...,
        description="List of providers that contributed",
    )
    deliberation: Optional[CouncilDeliberation] = Field(
        default=None,
        description="Full deliberation details (if council mode)",
    )
    total_duration_ms: float = Field(..., description="Total request duration")
    total_cost_usd: float = Field(..., description="Total cost in USD")
    fallback_used: bool = Field(
        default=False,
        description="Whether fallback was triggered",
    )
    fallback_reason: Optional[str] = Field(
        default=None,
        description="Reason for fallback (if applicable)",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Request timestamp",
    )


class CouncilBatchResponse(BaseModel):
    """Response for batch council request."""

    request_id: UUID = Field(..., description="Batch request identifier")
    results: list[CouncilResponse] = Field(
        ...,
        description="Individual results per violation",
    )
    total_violations: int = Field(..., description="Total violations processed")
    successful_count: int = Field(..., description="Successful recommendations")
    failed_count: int = Field(..., description="Failed recommendations")
    total_duration_ms: float = Field(..., description="Total batch duration")
    total_cost_usd: float = Field(..., description="Total batch cost")


# ============================================================================
# Deliberation History
# ============================================================================


class CouncilDeliberationSummary(BaseModel):
    """Summary of a past council deliberation for listing."""

    request_id: UUID = Field(..., description="Request identifier")
    violation_id: UUID = Field(..., description="Violation analyzed")
    mode_used: CouncilMode = Field(..., description="Mode used")
    confidence_score: int = Field(..., description="Final confidence")
    providers_used: list[str] = Field(..., description="Providers used")
    total_duration_ms: float = Field(..., description="Total duration")
    total_cost_usd: float = Field(..., description="Total cost")
    created_at: datetime = Field(..., description="Timestamp")


class CouncilStats(BaseModel):
    """Statistics for council usage."""

    total_requests: int = Field(..., description="Total council requests")
    single_mode_count: int = Field(..., description="Requests using single mode")
    council_mode_count: int = Field(..., description="Requests using council mode")
    average_confidence: float = Field(..., description="Average confidence score")
    average_duration_ms: float = Field(..., description="Average duration")
    total_cost_usd: float = Field(..., description="Total cost")
    by_provider: dict[str, int] = Field(
        ...,
        description="Request count per provider",
    )
    fallback_rate: float = Field(
        ...,
        description="Percentage of requests requiring fallback",
    )


# ============================================================================
# Configuration Schemas
# ============================================================================


class CouncilConfig(BaseModel):
    """Configuration for council behavior."""

    default_mode: CouncilMode = Field(
        default=CouncilMode.AUTO,
        description="Default execution mode",
    )
    auto_council_severities: list[str] = Field(
        default=["critical", "high"],
        description="Severities that trigger council mode in AUTO",
    )
    stage_1_timeout_ms: int = Field(
        default=10000,
        description="Timeout for Stage 1 (parallel queries)",
    )
    stage_2_timeout_ms: int = Field(
        default=8000,
        description="Timeout for Stage 2 (peer review)",
    )
    stage_3_timeout_ms: int = Field(
        default=10000,
        description="Timeout for Stage 3 (synthesis)",
    )
    council_timeout_ms: int = Field(
        default=30000,
        description="Total timeout for council mode",
    )
    min_providers_for_council: int = Field(
        default=2,
        ge=2,
        le=4,
        description="Minimum providers needed for council",
    )
    fallback_to_single_on_timeout: bool = Field(
        default=True,
        description="Fall back to single mode if council times out",
    )
