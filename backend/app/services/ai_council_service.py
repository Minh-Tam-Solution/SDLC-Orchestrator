# =========================================================================
# STATUS: FROZEN (Sprint 173, Feb 2026)
# TIER: Enterprise
# REASON: Non-core for current phase. Working code preserved.
# REACTIVATION: CPO approval required.
# DO NOT: Delete, refactor, or add features without CTO approval.
# =========================================================================
"""
=========================================================================
AI Council Service - Multi-LLM Deliberation Pattern
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: December 6, 2025
Status: ACTIVE - Sprint 26 (AI Governance Phase 01)
Authority: Backend Lead + CTO Approved
Foundation: ADR-007 (AI Context Engine), Sprint 26 Plan
Framework: SDLC 4.9.1 Complete Lifecycle

Purpose:
- 3-stage LLM Council for high-confidence recommendations
- Stage 1: Parallel queries to multiple LLMs
- Stage 2: Anonymized peer review and ranking
- Stage 3: Chairman synthesis (final answer)

Modes:
- Single: Use existing AIRecommendationService (default, fast)
- Council: 3-stage deliberation for CRITICAL/HIGH violations (accurate)
- Auto: Auto-select based on violation severity

Performance Targets:
- Single Mode (p95): <3s
- Council Mode (p95): <8s
- Fallback: Auto-fallback to single if council >8s

Zero Mock Policy: 100% real AI implementation
=========================================================================
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.compliance_scan import ComplianceViolation
from app.schemas.council import (
    AIProviderResponse,
    BacklogSummary,
    CouncilConfig,
    CouncilDecision,
    CouncilDecisionRequest,
    CouncilDecisionType,
    CouncilDeliberation,
    CouncilMode,
    CouncilProvider,
    CouncilRequest,
    CouncilResponse,
    CouncilSprintContext,
    DeliberationStage,
    FinalSynthesis,
    PeerReview,
    ResponseRanking,
    SprintHealthContext,
    Stage1Result,
    Stage2Result,
    Stage3Result,
    TeamMemberContext,
    VelocityContext,
)
from app.middleware.business_metrics import AICouncilMetrics
from app.services.ai_recommendation_service import (
    AIProviderType,
    AIRecommendationService,
    create_ai_recommendation_service,
)
from app.services.audit_service import AuditAction, AuditService

logger = logging.getLogger(__name__)


# ============================================================================
# Council State Tracking
# ============================================================================


@dataclass
class CouncilState:
    """Track state of a council deliberation."""

    request_id: UUID = field(default_factory=uuid4)
    violation_id: Optional[UUID] = None
    mode: CouncilMode = CouncilMode.AUTO
    stage: DeliberationStage = DeliberationStage.STAGE_1_QUERIES
    start_time: float = field(default_factory=time.time)
    stage1_result: Optional[Stage1Result] = None
    stage2_result: Optional[Stage2Result] = None
    stage3_result: Optional[Stage3Result] = None
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    error: Optional[str] = None

    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        return (time.time() - self.start_time) * 1000

    @property
    def total_cost(self) -> float:
        """Calculate total cost across all stages."""
        cost = 0.0
        if self.stage1_result:
            cost += self.stage1_result.total_cost_usd
        if self.stage2_result:
            cost += self.stage2_result.total_cost_usd
        if self.stage3_result:
            cost += self.stage3_result.cost_usd
        return cost


# ============================================================================
# AI Council Service
# ============================================================================


class AICouncilService:
    """
    3-Stage LLM Council for high-confidence recommendations.

    Deliberation Pattern:
    1. Stage 1 (Parallel Queries): Query 3 LLMs simultaneously
    2. Stage 2 (Peer Review): Each LLM ranks others' responses (anonymized)
    3. Stage 3 (Synthesis): Chairman LLM produces final answer

    Usage:
        council = AICouncilService(db)

        # Auto mode (council for critical/high, single for others)
        result = await council.generate_recommendation(
            violation_id=violation.id,
            council_mode=CouncilMode.AUTO
        )

        # Force council mode
        result = await council.generate_recommendation(
            violation_id=violation.id,
            council_mode=CouncilMode.COUNCIL
        )

    Performance:
        - Single mode: <3s (p95)
        - Council mode: <8s (p95)
        - Auto-fallback if council exceeds timeout
    """

    def __init__(
        self,
        db: AsyncSession,
        ai_service: Optional[AIRecommendationService] = None,
        audit_service: Optional[AuditService] = None,
        config: Optional[CouncilConfig] = None,
    ):
        """
        Initialize AI Council Service.

        Args:
            db: Database session
            ai_service: Optional pre-configured AI recommendation service
            audit_service: Optional pre-configured audit service
            config: Optional council configuration
        """
        self.db = db
        self.ai_service = ai_service or create_ai_recommendation_service(db)
        self.audit_service = audit_service or AuditService(db)
        self.config = config or CouncilConfig()

        # Provider configuration
        self.available_providers: list[CouncilProvider] = []
        self._init_available_providers()

        logger.info(
            f"AI Council Service initialized with {len(self.available_providers)} providers: "
            f"{[p.value for p in self.available_providers]}"
        )

    def _init_available_providers(self) -> None:
        """Initialize list of available providers."""
        # Ollama is always available (self-hosted)
        if self.ai_service.ollama.is_available:
            self.available_providers.append(CouncilProvider.OLLAMA)

        # Claude requires API key
        if settings.ANTHROPIC_API_KEY:
            self.available_providers.append(CouncilProvider.CLAUDE)

        # GPT-4 requires API key
        if settings.OPENAI_API_KEY:
            self.available_providers.append(CouncilProvider.GPT4)

    # ============================================================================
    # Main Entry Point
    # ============================================================================

    async def generate_recommendation(
        self,
        violation_id: UUID,
        council_mode: CouncilMode = CouncilMode.AUTO,
        user_id: Optional[UUID] = None,
        providers: Optional[list[CouncilProvider]] = None,
    ) -> CouncilResponse:
        """
        Generate AI recommendation for a compliance violation.

        Args:
            violation_id: UUID of the violation to analyze
            council_mode: Execution mode (single, council, auto)
            user_id: Requesting user (for audit logging)
            providers: Specific providers to use (default: all available)

        Returns:
            CouncilResponse with recommendation and deliberation details

        Raises:
            ValueError: If violation not found
            RuntimeError: If all providers fail

        Example:
            result = await council.generate_recommendation(
                violation_id=violation.id,
                council_mode=CouncilMode.AUTO,
                user_id=current_user.id
            )
            print(f"Recommendation: {result.recommendation}")
            print(f"Confidence: {result.confidence_score}%")
            print(f"Mode used: {result.mode_used}")
        """
        state = CouncilState(violation_id=violation_id, mode=council_mode)

        # Get violation from database
        violation = await self._get_violation(violation_id)
        if not violation:
            raise ValueError(f"Violation not found: {violation_id}")

        # Determine actual mode to use
        actual_mode = self._determine_mode(council_mode, violation.severity)
        state.mode = actual_mode

        # Log request
        await self.audit_service.log_ai_council_action(
            action=AuditAction.AI_COUNCIL_REQUESTED,
            user_id=user_id,
            violation_id=violation_id,
            details={
                "requested_mode": council_mode.value,
                "actual_mode": actual_mode.value,
                "severity": violation.severity,
                "providers_available": [p.value for p in self.available_providers],
            },
        )

        try:
            if actual_mode == CouncilMode.SINGLE:
                return await self._generate_single_mode(violation, state, user_id)
            else:
                return await self._generate_council_mode(
                    violation, state, user_id, providers
                )
        except Exception as e:
            logger.error(f"Council recommendation failed: {e}")

            # Log failure
            await self.audit_service.log_ai_council_action(
                action=AuditAction.AI_COUNCIL_FAILED,
                user_id=user_id,
                violation_id=violation_id,
                details={
                    "error": str(e),
                    "mode": actual_mode.value,
                    "stage": state.stage.value,
                    "elapsed_ms": state.elapsed_ms,
                },
            )
            raise

    def _determine_mode(self, requested_mode: CouncilMode, severity: str) -> CouncilMode:
        """Determine actual mode based on request and severity."""
        if requested_mode == CouncilMode.AUTO:
            # Use council mode for critical/high severity
            if severity.lower() in self.config.auto_council_severities:
                # But only if we have enough providers
                if len(self.available_providers) >= self.config.min_providers_for_council:
                    return CouncilMode.COUNCIL
            return CouncilMode.SINGLE

        # Council mode requires enough providers
        if requested_mode == CouncilMode.COUNCIL:
            if len(self.available_providers) < self.config.min_providers_for_council:
                logger.warning(
                    f"Not enough providers for council mode "
                    f"({len(self.available_providers)} < {self.config.min_providers_for_council}), "
                    f"falling back to single mode"
                )
                return CouncilMode.SINGLE

        return requested_mode

    # ============================================================================
    # Single Mode
    # ============================================================================

    async def _generate_single_mode(
        self,
        violation: ComplianceViolation,
        state: CouncilState,
        user_id: Optional[UUID],
    ) -> CouncilResponse:
        """Generate recommendation using single provider (fast path)."""
        result = await self.ai_service.generate_recommendation(
            violation_type=violation.violation_type,
            severity=violation.severity,
            location=violation.location or "unknown",
            description=violation.description,
            user_id=user_id,
        )

        # Log completion
        await self.audit_service.log_ai_council_action(
            action=AuditAction.AI_COUNCIL_COMPLETE,
            user_id=user_id,
            violation_id=violation.id,
            details={
                "mode": "single",
                "provider": result.provider,
                "confidence": result.confidence,
                "duration_ms": result.duration_ms,
                "cost_usd": result.cost_usd,
                "fallback_used": result.fallback_used,
            },
        )

        # Record Prometheus metrics
        AICouncilMetrics.record_deliberation_complete(
            mode="single",
            status="fallback" if result.fallback_used else "success",
            total_duration_seconds=state.elapsed_ms / 1000,
            stage1_duration_seconds=result.duration_ms / 1000,
            stage2_duration_seconds=0,
            stage3_duration_seconds=0,
            confidence_score=result.confidence,
            providers_used=[result.provider],
            total_cost_usd=result.cost_usd,
        )

        return CouncilResponse(
            request_id=state.request_id,
            violation_id=violation.id,
            mode_used=CouncilMode.SINGLE,
            recommendation=result.recommendation,
            confidence_score=result.confidence,
            providers_used=[result.provider],
            deliberation=None,  # No deliberation in single mode
            total_duration_ms=state.elapsed_ms,
            total_cost_usd=result.cost_usd,
            fallback_used=result.fallback_used,
            fallback_reason=result.fallback_reason,
        )

    # ============================================================================
    # Council Mode - Stage 1: Parallel Queries
    # ============================================================================

    async def _generate_council_mode(
        self,
        violation: ComplianceViolation,
        state: CouncilState,
        user_id: Optional[UUID],
        providers: Optional[list[CouncilProvider]] = None,
    ) -> CouncilResponse:
        """Generate recommendation using 3-stage council deliberation."""
        # Use specified providers or all available
        providers_to_use = providers or self.available_providers

        try:
            # Stage 1: Parallel Queries
            state.stage = DeliberationStage.STAGE_1_QUERIES
            stage1_result = await asyncio.wait_for(
                self._stage1_parallel_queries(violation, providers_to_use),
                timeout=self.config.stage_1_timeout_ms / 1000,
            )
            state.stage1_result = stage1_result

            # Log Stage 1 completion
            await self.audit_service.log_ai_council_action(
                action=AuditAction.AI_COUNCIL_STAGE1_COMPLETE,
                user_id=user_id,
                violation_id=violation.id,
                details={
                    "successful_count": stage1_result.successful_count,
                    "failed_count": stage1_result.failed_count,
                    "duration_ms": stage1_result.total_duration_ms,
                    "cost_usd": stage1_result.total_cost_usd,
                    "has_quorum": stage1_result.has_quorum,
                },
            )

            # Check if we have quorum for deliberation
            if not stage1_result.has_quorum:
                logger.warning("Not enough responses for peer review, using best single response")
                return await self._fallback_to_best_single(violation, state, stage1_result, user_id)

            # Stage 2: Peer Review
            state.stage = DeliberationStage.STAGE_2_REVIEW
            stage2_result = await asyncio.wait_for(
                self._stage2_peer_review(stage1_result),
                timeout=self.config.stage_2_timeout_ms / 1000,
            )
            state.stage2_result = stage2_result

            # Log Stage 2 completion
            await self.audit_service.log_ai_council_action(
                action=AuditAction.AI_COUNCIL_STAGE2_COMPLETE,
                user_id=user_id,
                violation_id=violation.id,
                details={
                    "reviews_count": len(stage2_result.reviews),
                    "best_response_id": stage2_result.best_response_id,
                    "aggregated_scores": stage2_result.aggregated_scores,
                    "duration_ms": stage2_result.total_duration_ms,
                    "cost_usd": stage2_result.total_cost_usd,
                },
            )

            # Stage 3: Synthesis
            state.stage = DeliberationStage.STAGE_3_SYNTHESIS
            stage3_result = await asyncio.wait_for(
                self._stage3_synthesis(stage1_result, stage2_result),
                timeout=self.config.stage_3_timeout_ms / 1000,
            )
            state.stage3_result = stage3_result

            # Log Stage 3 completion
            await self.audit_service.log_ai_council_action(
                action=AuditAction.AI_COUNCIL_STAGE3_COMPLETE,
                user_id=user_id,
                violation_id=violation.id,
                details={
                    "chairman": stage3_result.chairman,
                    "confidence": stage3_result.synthesis.confidence,
                    "duration_ms": stage3_result.duration_ms,
                    "cost_usd": stage3_result.cost_usd,
                },
            )

            state.stage = DeliberationStage.COMPLETE

            # Build full response
            deliberation = CouncilDeliberation(
                stage_1=stage1_result,
                stage_2=stage2_result,
                stage_3=stage3_result,
            )

            providers_used = [r.provider for r in stage1_result.responses if r.is_success]

            # Log final completion
            await self.audit_service.log_ai_council_action(
                action=AuditAction.AI_COUNCIL_COMPLETE,
                user_id=user_id,
                violation_id=violation.id,
                details={
                    "mode": "council",
                    "providers_used": providers_used,
                    "confidence": stage3_result.synthesis.confidence,
                    "total_duration_ms": state.elapsed_ms,
                    "total_cost_usd": state.total_cost,
                },
            )

            # Record Prometheus metrics
            AICouncilMetrics.record_deliberation_complete(
                mode="council",
                status="success",
                total_duration_seconds=state.elapsed_ms / 1000,
                stage1_duration_seconds=stage1_result.total_duration_ms / 1000,
                stage2_duration_seconds=stage2_result.total_duration_ms / 1000,
                stage3_duration_seconds=stage3_result.duration_ms / 1000,
                confidence_score=stage3_result.synthesis.confidence,
                providers_used=providers_used,
                total_cost_usd=state.total_cost,
            )

            return CouncilResponse(
                request_id=state.request_id,
                violation_id=violation.id,
                mode_used=CouncilMode.COUNCIL,
                recommendation=stage3_result.synthesis.answer,
                confidence_score=stage3_result.synthesis.confidence,
                providers_used=providers_used,
                deliberation=deliberation,
                total_duration_ms=state.elapsed_ms,
                total_cost_usd=state.total_cost,
                fallback_used=False,
            )

        except asyncio.TimeoutError as e:
            logger.warning(f"Council mode timed out at stage {state.stage}: {e}")
            state.fallback_used = True
            state.fallback_reason = f"Timeout at {state.stage.value}"

            # Log fallback
            await self.audit_service.log_ai_council_action(
                action=AuditAction.AI_COUNCIL_FALLBACK,
                user_id=user_id,
                violation_id=violation.id,
                details={
                    "reason": "timeout",
                    "stage": state.stage.value,
                    "elapsed_ms": state.elapsed_ms,
                },
            )

            # Record fallback metrics
            AICouncilMetrics.record_fallback(reason="timeout")

            # Fall back to single mode if configured
            if self.config.fallback_to_single_on_timeout:
                return await self._generate_single_mode(violation, state, user_id)
            raise

    async def _stage1_parallel_queries(
        self,
        violation: ComplianceViolation,
        providers: list[CouncilProvider],
    ) -> Stage1Result:
        """
        Stage 1: Query all providers in parallel.

        Each provider receives the same prompt and generates a recommendation
        independently. Responses are collected for peer review in Stage 2.

        Args:
            violation: The compliance violation to analyze
            providers: List of providers to query

        Returns:
            Stage1Result with all responses
        """
        start_time = time.time()

        # Build query tasks for each provider
        tasks = []
        for provider in providers:
            task = self._query_single_provider(violation, provider)
            tasks.append(task)

        # Execute all queries in parallel
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        provider_responses: list[AIProviderResponse] = []
        for i, response in enumerate(responses):
            provider = providers[i]

            if isinstance(response, Exception):
                provider_responses.append(
                    AIProviderResponse(
                        provider=provider.value,
                        model="unknown",
                        response="",
                        confidence=0,
                        duration_ms=0,
                        tokens_used=0,
                        cost_usd=0,
                        error=str(response),
                    )
                )
            else:
                provider_responses.append(response)

        # Calculate totals
        successful_responses = [r for r in provider_responses if r.is_success]
        total_duration = (time.time() - start_time) * 1000
        total_cost = sum(r.cost_usd for r in provider_responses)

        return Stage1Result(
            responses=provider_responses,
            successful_count=len(successful_responses),
            failed_count=len(provider_responses) - len(successful_responses),
            total_duration_ms=total_duration,
            total_cost_usd=total_cost,
        )

    async def _query_single_provider(
        self,
        violation: ComplianceViolation,
        provider: CouncilProvider,
    ) -> AIProviderResponse:
        """Query a single provider for recommendation."""
        start_time = time.time()

        try:
            # Map CouncilProvider to AIProviderType
            provider_type = AIProviderType(provider.value)

            # Generate recommendation using the AI service
            result = await self.ai_service._generate_with_provider(
                provider=provider_type,
                violation_type=violation.violation_type,
                severity=violation.severity,
                location=violation.location or "unknown",
                description=violation.description,
            )

            return AIProviderResponse(
                provider=provider.value,
                model=result.model,
                response=result.recommendation,
                confidence=result.confidence,
                duration_ms=result.duration_ms,
                tokens_used=result.tokens_used,
                cost_usd=result.cost_usd,
            )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"Provider {provider.value} failed: {e}")
            return AIProviderResponse(
                provider=provider.value,
                model="unknown",
                response="",
                confidence=0,
                duration_ms=duration,
                tokens_used=0,
                cost_usd=0,
                error=str(e),
            )

    async def _fallback_to_best_single(
        self,
        violation: ComplianceViolation,
        state: CouncilState,
        stage1_result: Stage1Result,
        user_id: Optional[UUID],
    ) -> CouncilResponse:
        """Fall back to best single response when quorum not met."""
        state.fallback_used = True
        state.fallback_reason = "Insufficient responses for peer review"

        # Log fallback
        await self.audit_service.log_ai_council_action(
            action=AuditAction.AI_COUNCIL_FALLBACK,
            user_id=user_id,
            violation_id=violation.id,
            details={
                "reason": "no_quorum",
                "successful_count": stage1_result.successful_count,
                "required": self.config.min_providers_for_council,
            },
        )

        # Record fallback metrics
        AICouncilMetrics.record_fallback(reason="no_quorum")

        # Find best response by confidence
        successful_responses = [r for r in stage1_result.responses if r.is_success]
        if not successful_responses:
            raise RuntimeError("No successful responses in Stage 1")

        best_response = max(successful_responses, key=lambda r: r.confidence)

        # Build partial deliberation
        deliberation = CouncilDeliberation(
            stage_1=stage1_result,
            stage_2=None,
            stage_3=None,
        )

        return CouncilResponse(
            request_id=state.request_id,
            violation_id=violation.id,
            mode_used=CouncilMode.COUNCIL,
            recommendation=best_response.response,
            confidence_score=best_response.confidence,
            providers_used=[best_response.provider],
            deliberation=deliberation,
            total_duration_ms=state.elapsed_ms,
            total_cost_usd=state.total_cost,
            fallback_used=True,
            fallback_reason=state.fallback_reason,
        )

    # ============================================================================
    # Stage 2: Peer Review
    # ============================================================================

    async def _stage2_peer_review(
        self,
        stage1_result: Stage1Result,
    ) -> Stage2Result:
        """
        Stage 2: Anonymized peer review.

        Each provider ranks the other providers' responses without knowing
        which provider generated each response. Rankings are aggregated
        to determine the best response.

        Process:
        1. Anonymize responses (provider → "Response A", "Response B", etc.)
        2. Each provider reviews and ranks all other responses
        3. Aggregate scores using weighted average
        4. Determine best response based on aggregated rankings

        Args:
            stage1_result: Results from Stage 1 parallel queries

        Returns:
            Stage2Result with peer reviews and aggregated scores
        """
        start_time = time.time()

        # Get successful responses only
        successful_responses = [r for r in stage1_result.responses if r.is_success]
        if len(successful_responses) < 2:
            # Not enough responses for meaningful peer review
            logger.warning("Only one successful response, skipping peer review")
            return self._create_fallback_stage2_result(successful_responses, start_time)

        # Create anonymized mapping: provider → Response A/B/C
        anonymized_mapping = self._create_anonymized_mapping(successful_responses)

        # Each provider reviews other responses
        review_tasks = []
        for reviewer in successful_responses:
            # Get responses to review (exclude reviewer's own response)
            responses_to_review = [
                (anonymized_mapping[r.provider], r.response)
                for r in successful_responses
                if r.provider != reviewer.provider
            ]
            task = self._conduct_peer_review(
                reviewer=reviewer,
                responses_to_review=responses_to_review,
                anonymized_mapping=anonymized_mapping,
            )
            review_tasks.append(task)

        # Execute all reviews in parallel
        review_results = await asyncio.gather(*review_tasks, return_exceptions=True)

        # Process review results
        peer_reviews: list[PeerReview] = []
        for i, result in enumerate(review_results):
            if isinstance(result, Exception):
                logger.error(f"Peer review failed: {result}")
                continue
            if result:
                peer_reviews.append(result)

        # Aggregate scores
        aggregated_scores = self._aggregate_scores(
            peer_reviews, anonymized_mapping, successful_responses
        )

        # Determine best response
        best_response_id = max(aggregated_scores, key=aggregated_scores.get) if aggregated_scores else ""

        total_duration = (time.time() - start_time) * 1000
        total_cost = sum(r.cost_usd for r in peer_reviews)

        return Stage2Result(
            reviews=peer_reviews,
            aggregated_scores=aggregated_scores,
            best_response_id=best_response_id,
            total_duration_ms=total_duration,
            total_cost_usd=total_cost,
        )

    def _create_anonymized_mapping(
        self,
        responses: list[AIProviderResponse],
    ) -> dict[str, str]:
        """
        Create anonymized mapping for peer review.

        Maps provider names to neutral identifiers (Response A, B, C...)
        to prevent bias during peer review.

        Args:
            responses: List of successful provider responses

        Returns:
            Dict mapping provider name to anonymized identifier
        """
        labels = ["Response A", "Response B", "Response C", "Response D", "Response E"]
        return {
            response.provider: labels[i]
            for i, response in enumerate(responses)
            if i < len(labels)
        }

    async def _conduct_peer_review(
        self,
        reviewer: AIProviderResponse,
        responses_to_review: list[tuple[str, str]],
        anonymized_mapping: dict[str, str],
    ) -> Optional[PeerReview]:
        """
        Have a provider review and rank other responses.

        Uses the same provider that generated the response to evaluate
        other responses. The reviewer is unaware of which provider
        generated each response due to anonymization.

        Args:
            reviewer: The provider doing the review
            responses_to_review: List of (anonymized_id, response_text) tuples
            anonymized_mapping: Full mapping for reference

        Returns:
            PeerReview with rankings, or None if review failed
        """
        start_time = time.time()

        # Build review prompt
        prompt = self._build_peer_review_prompt(responses_to_review)

        try:
            # Map reviewer to provider type
            provider_type = AIProviderType(reviewer.provider)

            # Generate review using the provider's API
            review_response = await self._call_provider_for_review(
                provider=provider_type,
                prompt=prompt,
            )

            # Parse rankings from response
            rankings = self._parse_review_response(
                review_response=review_response,
                responses_to_review=responses_to_review,
            )

            duration = (time.time() - start_time) * 1000

            return PeerReview(
                reviewer=reviewer.provider,
                rankings=rankings,
                duration_ms=duration,
                cost_usd=self._estimate_review_cost(provider_type),
            )

        except Exception as e:
            logger.error(f"Peer review by {reviewer.provider} failed: {e}")
            return None

    def _build_peer_review_prompt(
        self,
        responses_to_review: list[tuple[str, str]],
    ) -> str:
        """
        Build prompt for peer review.

        Creates a structured prompt asking the reviewer to rank
        responses based on quality criteria.

        Args:
            responses_to_review: List of (anonymized_id, response_text)

        Returns:
            Formatted prompt string
        """
        responses_text = "\n\n".join([
            f"### {resp_id}\n{resp_text}"
            for resp_id, resp_text in responses_to_review
        ])

        return f"""You are reviewing AI-generated compliance recommendations.
Evaluate each response based on:
1. Accuracy: Is the recommendation technically correct?
2. Completeness: Does it address all aspects of the violation?
3. Actionability: Are the steps clear and executable?
4. Compliance: Does it align with best practices and standards?

{responses_text}

For each response, provide:
1. A rank (1 = best, higher = worse)
2. A score from 0-100
3. A brief explanation (1-2 sentences)

Format your response as JSON:
{{
    "rankings": [
        {{"response_id": "Response A", "rank": 1, "score": 85, "reasoning": "Clear and actionable..."}},
        {{"response_id": "Response B", "rank": 2, "score": 72, "reasoning": "Good but missing..."}}
    ]
}}
"""

    async def _call_provider_for_review(
        self,
        provider: AIProviderType,
        prompt: str,
    ) -> str:
        """
        Call provider API for peer review.

        Args:
            provider: Provider to use for review
            prompt: Review prompt

        Returns:
            Provider's review response text
        """
        if provider == AIProviderType.OLLAMA:
            return await self._call_ollama_for_review(prompt)
        elif provider == AIProviderType.CLAUDE:
            return await self._call_claude_for_review(prompt)
        elif provider == AIProviderType.GPT4:
            return await self._call_gpt4_for_review(prompt)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _call_ollama_for_review(self, prompt: str) -> str:
        """Call Ollama for peer review."""
        result = await self.ai_service.ollama.generate(
            prompt=prompt,
            model=settings.OLLAMA_MODEL or "mistral",
            stream=False,
        )
        return result.get("response", "")

    async def _call_claude_for_review(self, prompt: str) -> str:
        """Call Claude for peer review."""
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text if response.content else ""

    async def _call_gpt4_for_review(self, prompt: str) -> str:
        """Call GPT-4 for peer review."""
        import openai

        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        return response.choices[0].message.content or "" if response.choices else ""

    def _parse_review_response(
        self,
        review_response: str,
        responses_to_review: list[tuple[str, str]],
    ) -> list[ResponseRanking]:
        """
        Parse rankings from review response.

        Attempts to parse JSON response, with fallback to text analysis.

        Args:
            review_response: Raw response from reviewer
            responses_to_review: Original responses being reviewed

        Returns:
            List of ResponseRanking objects
        """
        import json
        import re

        rankings: list[ResponseRanking] = []

        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', review_response)
            if json_match:
                parsed = json.loads(json_match.group())
                if "rankings" in parsed:
                    for item in parsed["rankings"]:
                        rankings.append(
                            ResponseRanking(
                                response_id=item.get("response_id", ""),
                                rank=item.get("rank", 1),
                                score=item.get("score", 50),
                                reasoning=item.get("reasoning", ""),
                            )
                        )
                    return rankings
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse JSON review response: {e}")

        # Fallback: create default rankings based on order mentioned
        for i, (resp_id, _) in enumerate(responses_to_review):
            rankings.append(
                ResponseRanking(
                    response_id=resp_id,
                    rank=i + 1,
                    score=max(100 - (i * 15), 50),  # Decreasing scores
                    reasoning="Unable to parse structured ranking",
                )
            )

        return rankings

    def _aggregate_scores(
        self,
        peer_reviews: list[PeerReview],
        anonymized_mapping: dict[str, str],
        responses: list[AIProviderResponse],
    ) -> dict[str, float]:
        """
        Aggregate scores from all peer reviews.

        Combines rankings from all reviewers into final scores.
        Uses weighted average where:
        - Higher-confidence reviewers have more weight
        - Rank position converted to score (1st = 100, 2nd = 80, etc.)

        Args:
            peer_reviews: All peer reviews
            anonymized_mapping: Provider → anonymized ID mapping
            responses: Original responses for confidence weights

        Returns:
            Dict mapping provider name to aggregated score
        """
        # Reverse mapping: anonymized ID → provider name
        reverse_mapping = {v: k for k, v in anonymized_mapping.items()}

        # Collect all scores for each provider
        provider_scores: dict[str, list[tuple[float, float]]] = {
            provider: [] for provider in anonymized_mapping.keys()
        }

        # Get reviewer confidence weights
        reviewer_weights = {r.provider: r.confidence / 100.0 for r in responses}

        for review in peer_reviews:
            reviewer_weight = reviewer_weights.get(review.reviewer, 0.5)

            for ranking in review.rankings:
                provider = reverse_mapping.get(ranking.response_id, "")
                if provider:
                    # Weight the score by reviewer's confidence
                    weighted_score = ranking.score * reviewer_weight
                    provider_scores[provider].append((weighted_score, reviewer_weight))

        # Calculate weighted average for each provider
        aggregated: dict[str, float] = {}
        for provider, scores_and_weights in provider_scores.items():
            if scores_and_weights:
                total_weighted_score = sum(s for s, _ in scores_and_weights)
                total_weight = sum(w for _, w in scores_and_weights)
                if total_weight > 0:
                    aggregated[provider] = total_weighted_score / total_weight
                else:
                    aggregated[provider] = 0.0
            else:
                # If no reviews (only 2 providers, each reviews only the other)
                # Use original confidence
                original = next((r for r in responses if r.provider == provider), None)
                aggregated[provider] = float(original.confidence) if original else 0.0

        return aggregated

    def _estimate_review_cost(self, provider: AIProviderType) -> float:
        """Estimate cost for a peer review call."""
        cost_map = {
            AIProviderType.OLLAMA: 0.0,  # Self-hosted
            AIProviderType.CLAUDE: 0.003,  # ~1K tokens
            AIProviderType.GPT4: 0.006,  # ~1K tokens
        }
        return cost_map.get(provider, 0.0)

    def _create_fallback_stage2_result(
        self,
        responses: list[AIProviderResponse],
        start_time: float,
    ) -> Stage2Result:
        """Create Stage2 result when peer review is not possible."""
        if not responses:
            return Stage2Result(
                reviews=[],
                aggregated_scores={},
                best_response_id="",
                total_duration_ms=(time.time() - start_time) * 1000,
                total_cost_usd=0.0,
            )

        # Use confidence scores directly
        aggregated_scores = {r.provider: float(r.confidence) for r in responses}
        best_provider = max(aggregated_scores, key=aggregated_scores.get)

        return Stage2Result(
            reviews=[],
            aggregated_scores=aggregated_scores,
            best_response_id=best_provider,
            total_duration_ms=(time.time() - start_time) * 1000,
            total_cost_usd=0.0,
        )

    # ============================================================================
    # Stage 3: Chairman Synthesis
    # ============================================================================

    async def _stage3_synthesis(
        self,
        stage1_result: Stage1Result,
        stage2_result: Stage2Result,
    ) -> Stage3Result:
        """
        Stage 3: Chairman synthesis.

        The chairman (highest-ranked provider from Stage 2) synthesizes
        all responses into a final comprehensive answer.

        Process:
        1. Select chairman (highest aggregated score from peer review)
        2. Provide chairman with all responses and rankings
        3. Chairman synthesizes best elements into final recommendation
        4. Extract key points and note dissenting views

        Args:
            stage1_result: Results from Stage 1 parallel queries
            stage2_result: Results from Stage 2 peer review

        Returns:
            Stage3Result with final synthesis
        """
        start_time = time.time()

        # Determine chairman (provider with highest aggregated score)
        chairman_provider = stage2_result.best_response_id
        if not chairman_provider:
            # Fallback: use provider with highest confidence
            successful = [r for r in stage1_result.responses if r.is_success]
            if not successful:
                raise RuntimeError("No successful responses for synthesis")
            chairman_provider = max(successful, key=lambda r: r.confidence).provider

        # Get all successful responses
        successful_responses = [r for r in stage1_result.responses if r.is_success]

        # Build synthesis prompt
        prompt = self._build_synthesis_prompt(
            responses=successful_responses,
            stage2_result=stage2_result,
        )

        try:
            # Call chairman for synthesis
            provider_type = AIProviderType(chairman_provider)
            synthesis_response = await self._call_provider_for_synthesis(
                provider=provider_type,
                prompt=prompt,
            )

            # Parse synthesis into structured format
            synthesis = self._parse_synthesis_response(
                synthesis_response=synthesis_response,
                responses=successful_responses,
                stage2_result=stage2_result,
            )

            duration = (time.time() - start_time) * 1000
            cost = self._estimate_synthesis_cost(provider_type)

            return Stage3Result(
                chairman=chairman_provider,
                synthesis=synthesis,
                duration_ms=duration,
                cost_usd=cost,
            )

        except Exception as e:
            logger.error(f"Synthesis by {chairman_provider} failed: {e}")
            # Fallback to best response directly
            return self._create_fallback_stage3_result(
                stage1_result, stage2_result, chairman_provider, start_time
            )

    def _build_synthesis_prompt(
        self,
        responses: list[AIProviderResponse],
        stage2_result: Stage2Result,
    ) -> str:
        """
        Build prompt for chairman synthesis.

        Provides chairman with all responses, their scores, and
        instructions to synthesize the best recommendation.

        Args:
            responses: All successful responses from Stage 1
            stage2_result: Peer review results including scores

        Returns:
            Formatted synthesis prompt
        """
        # Build responses section with scores
        responses_text = ""
        for i, response in enumerate(responses):
            score = stage2_result.aggregated_scores.get(response.provider, 0)
            responses_text += f"""
### Response {i + 1} (Score: {score:.1f}/100)
{response.response}
"""

        # Include peer review insights if available
        review_insights = ""
        if stage2_result.reviews:
            insights = []
            for review in stage2_result.reviews:
                for ranking in review.rankings:
                    if ranking.reasoning:
                        insights.append(f"- {ranking.reasoning}")
            if insights:
                review_insights = "\n**Peer Review Insights:**\n" + "\n".join(insights[:5])

        return f"""You are the Chairman of an AI Council tasked with synthesizing the best compliance recommendation.

You have received the following responses from other AI providers, along with their peer review scores:

{responses_text}
{review_insights}

Your task is to:
1. Analyze all responses and their strengths/weaknesses
2. Synthesize the BEST elements from each into a comprehensive final recommendation
3. Ensure the final answer is actionable and complete
4. Identify any dissenting views or areas of disagreement
5. Extract 3-5 key action points

Format your response as JSON:
{{
    "final_recommendation": "Your synthesized comprehensive recommendation...",
    "confidence": 85,
    "reasoning": "Explanation of how you synthesized the responses...",
    "key_points": [
        "Action point 1",
        "Action point 2",
        "Action point 3"
    ],
    "dissenting_views": "Notable disagreements between responses (or null if consensus)"
}}
"""

    async def _call_provider_for_synthesis(
        self,
        provider: AIProviderType,
        prompt: str,
    ) -> str:
        """
        Call chairman provider for synthesis.

        Args:
            provider: Chairman provider
            prompt: Synthesis prompt

        Returns:
            Chairman's synthesized response
        """
        if provider == AIProviderType.OLLAMA:
            return await self._call_ollama_for_synthesis(prompt)
        elif provider == AIProviderType.CLAUDE:
            return await self._call_claude_for_synthesis(prompt)
        elif provider == AIProviderType.GPT4:
            return await self._call_gpt4_for_synthesis(prompt)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _call_ollama_for_synthesis(self, prompt: str) -> str:
        """Call Ollama for synthesis."""
        result = await self.ai_service.ollama.generate(
            prompt=prompt,
            model=settings.OLLAMA_MODEL or "mistral",
            stream=False,
        )
        return result.get("response", "")

    async def _call_claude_for_synthesis(self, prompt: str) -> str:
        """Call Claude for synthesis."""
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text if response.content else ""

    async def _call_gpt4_for_synthesis(self, prompt: str) -> str:
        """Call GPT-4 for synthesis."""
        import openai

        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
        )
        return response.choices[0].message.content or "" if response.choices else ""

    def _parse_synthesis_response(
        self,
        synthesis_response: str,
        responses: list[AIProviderResponse],
        stage2_result: Stage2Result,
    ) -> FinalSynthesis:
        """
        Parse synthesis response into structured format.

        Args:
            synthesis_response: Raw response from chairman
            responses: Original responses for fallback
            stage2_result: Peer review results

        Returns:
            FinalSynthesis with parsed data
        """
        import json
        import re

        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', synthesis_response)
            if json_match:
                parsed = json.loads(json_match.group())

                return FinalSynthesis(
                    answer=parsed.get("final_recommendation", synthesis_response),
                    confidence=min(max(int(parsed.get("confidence", 75)), 0), 100),
                    reasoning=parsed.get("reasoning", "Synthesized from multiple AI responses"),
                    key_points=parsed.get("key_points", [])[:5],  # Max 5 points
                    dissenting_views=parsed.get("dissenting_views"),
                )
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.warning(f"Failed to parse JSON synthesis response: {e}")

        # Fallback: use response as-is
        return FinalSynthesis(
            answer=synthesis_response.strip() if synthesis_response else self._get_best_response_text(responses, stage2_result),
            confidence=self._calculate_synthesis_confidence(responses, stage2_result),
            reasoning="Synthesized recommendation from council deliberation",
            key_points=self._extract_key_points(synthesis_response),
            dissenting_views=None,
        )

    def _get_best_response_text(
        self,
        responses: list[AIProviderResponse],
        stage2_result: Stage2Result,
    ) -> str:
        """Get text of best response based on peer review scores."""
        best_provider = stage2_result.best_response_id
        best_response = next(
            (r for r in responses if r.provider == best_provider),
            responses[0] if responses else None,
        )
        return best_response.response if best_response else ""

    def _calculate_synthesis_confidence(
        self,
        responses: list[AIProviderResponse],
        stage2_result: Stage2Result,
    ) -> int:
        """
        Calculate confidence for synthesized answer.

        Factors:
        - Average peer review score
        - Consensus among responses (lower variance = higher confidence)
        - Original confidence scores
        """
        if not stage2_result.aggregated_scores:
            # Fallback to average original confidence
            if responses:
                return int(sum(r.confidence for r in responses) / len(responses))
            return 50

        # Use weighted combination of:
        # 1. Best peer review score (60% weight)
        # 2. Average peer review score (40% weight)
        scores = list(stage2_result.aggregated_scores.values())
        best_score = max(scores) if scores else 50
        avg_score = sum(scores) / len(scores) if scores else 50

        confidence = int(best_score * 0.6 + avg_score * 0.4)
        return min(max(confidence, 0), 100)

    def _extract_key_points(self, text: str) -> list[str]:
        """
        Extract key points from synthesis text.

        Looks for numbered lists, bullet points, or action items.
        """
        import re

        key_points = []

        # Look for numbered points (1. xxx, 2. xxx)
        numbered = re.findall(r'\d+\.\s*([^\n]+)', text)
        key_points.extend(numbered[:5])

        # Look for bullet points (- xxx, * xxx)
        if len(key_points) < 3:
            bullets = re.findall(r'[-*]\s*([^\n]+)', text)
            for bullet in bullets:
                if bullet not in key_points:
                    key_points.append(bullet)
                if len(key_points) >= 5:
                    break

        return key_points[:5]

    def _estimate_synthesis_cost(self, provider: AIProviderType) -> float:
        """Estimate cost for synthesis call (larger output)."""
        cost_map = {
            AIProviderType.OLLAMA: 0.0,  # Self-hosted
            AIProviderType.CLAUDE: 0.01,  # ~2K tokens
            AIProviderType.GPT4: 0.02,  # ~2K tokens
        }
        return cost_map.get(provider, 0.0)

    def _create_fallback_stage3_result(
        self,
        stage1_result: Stage1Result,
        stage2_result: Stage2Result,
        chairman: str,
        start_time: float,
    ) -> Stage3Result:
        """Create Stage3 result when synthesis fails."""
        # Use best response directly
        successful = [r for r in stage1_result.responses if r.is_success]
        best_provider = stage2_result.best_response_id or chairman
        best_response = next(
            (r for r in successful if r.provider == best_provider),
            successful[0] if successful else None,
        )

        if not best_response:
            raise RuntimeError("No responses available for synthesis fallback")

        synthesis = FinalSynthesis(
            answer=best_response.response,
            confidence=best_response.confidence,
            reasoning="Fallback to best-ranked response due to synthesis error",
            key_points=self._extract_key_points(best_response.response),
            dissenting_views=None,
        )

        return Stage3Result(
            chairman=chairman,
            synthesis=synthesis,
            duration_ms=(time.time() - start_time) * 1000,
            cost_usd=0.0,  # No cost since synthesis failed
        )

    # ============================================================================
    # Helper Methods
    # ============================================================================

    async def _get_violation(self, violation_id: UUID) -> Optional[ComplianceViolation]:
        """Get violation from database."""
        result = await self.db.execute(
            select(ComplianceViolation).where(ComplianceViolation.id == violation_id)
        )
        return result.scalar_one_or_none()

    async def get_providers_status(self) -> dict[str, Any]:
        """Get status of all council providers."""
        return {
            "available_providers": [p.value for p in self.available_providers],
            "provider_count": len(self.available_providers),
            "council_enabled": len(self.available_providers) >= self.config.min_providers_for_council,
            "config": {
                "default_mode": self.config.default_mode.value,
                "auto_council_severities": self.config.auto_council_severities,
                "min_providers_for_council": self.config.min_providers_for_council,
                "council_timeout_ms": self.config.council_timeout_ms,
            },
        }

    # ============================================================================
    # Sprint 77: Sprint-Aware Council Decisions
    # ============================================================================

    async def make_decision(
        self,
        request: CouncilDecisionRequest,
    ) -> CouncilDecision:
        """
        Make council decision with sprint context.

        Sprint 77 Day 1: AI Council Sprint Context Integration

        Sprint context influences:
        - Review urgency based on sprint health
        - Reviewer assignment based on team availability
        - Architecture decisions based on sprint scope

        Args:
            request: CouncilDecisionRequest with decision_type and sprint_context

        Returns:
            CouncilDecision with recommendation and sprint-aware adjustments

        Example:
            decision = await council.make_decision(
                CouncilDecisionRequest(
                    decision_type=CouncilDecisionType.CODE_REVIEW,
                    resource_id=backlog_item.id,
                    resource_type="backlog_item",
                    requester_id=current_user.id,
                    description="Review refactored authentication module",
                    sprint_context=sprint_context,
                )
            )
        """
        start_time = time.time()

        # Build context from sprint data
        context = self._build_decision_context(request)

        # Determine urgency (adjust based on sprint health)
        urgency = self._adjust_urgency(request)

        # Build AI prompt with sprint awareness
        prompt = self._build_decision_prompt(request, context)

        # Generate recommendation via LLM
        try:
            result = await self.ai_service.generate_recommendation_from_prompt(
                prompt=prompt,
                user_id=request.requester_id,
            )

            # Extract action items from response
            action_items = self._extract_action_items(result.recommendation)

            # Find suggested assignee based on expertise
            suggested_assignee = self._find_best_assignee(
                request.sprint_context,
                request.decision_type,
            )

            # Calculate sprint impact
            sprint_impact = self._assess_sprint_impact(request, result.recommendation)

            elapsed_ms = (time.time() - start_time) * 1000

            decision = CouncilDecision(
                decision_id=uuid4(),
                request_id=uuid4(),
                decision_type=request.decision_type,
                recommendation=result.recommendation,
                confidence=result.confidence,
                reasoning=f"Based on {request.decision_type.value} analysis",
                suggested_assignee=suggested_assignee,
                urgency_adjusted=urgency,
                sprint_impact=sprint_impact,
                action_items=action_items,
                providers_used=[result.provider],
                total_duration_ms=elapsed_ms,
                sprint_id=request.sprint_context.sprint_id if request.sprint_context else None,
            )

            # Log decision with sprint reference
            await self._log_decision(
                decision=decision,
                request=request,
            )

            return decision

        except Exception as e:
            logger.error(f"Council decision failed: {e}")
            raise

    def _build_decision_context(self, request: CouncilDecisionRequest) -> dict[str, Any]:
        """Build context dictionary from sprint context."""
        context: dict[str, Any] = {
            "decision_type": request.decision_type.value,
            "resource_type": request.resource_type,
            "description": request.description,
        }

        if request.sprint_context:
            ctx = request.sprint_context
            context["sprint"] = {
                "id": str(ctx.sprint_id),
                "number": ctx.sprint_number,
                "name": ctx.sprint_name,
                "goal": ctx.sprint_goal,
                "status": ctx.sprint_status,
                "velocity_avg": ctx.velocity.average,
                "velocity_trend": ctx.velocity.trend,
                "health_risk": ctx.health.risk_level,
                "completion_rate": ctx.health.completion_rate,
                "days_remaining": ctx.health.days_remaining,
                "team_size": len(ctx.team_members),
                "blocked_items": ctx.backlog_summary.blocked_items,
                "p0_incomplete": ctx.backlog_summary.p0_count - ctx.backlog_summary.p0_completed,
                "g_sprint_passed": ctx.g_sprint_passed,
                "documentation_overdue": ctx.documentation_overdue,
            }

        return context

    def _adjust_urgency(self, request: CouncilDecisionRequest) -> str:
        """Adjust urgency based on sprint health and context."""
        base_urgency = request.urgency

        if not request.sprint_context:
            return base_urgency

        ctx = request.sprint_context

        # Escalate urgency for sprints at risk
        if ctx.health.risk_level in ("high", "critical"):
            if base_urgency == "low":
                return "normal"
            elif base_urgency == "normal":
                return "high"

        # Escalate for documentation deadline
        if ctx.documentation_overdue:
            if base_urgency in ("low", "normal"):
                return "high"

        # Escalate for P0 blockers
        p0_blocked = ctx.backlog_summary.p0_count > ctx.backlog_summary.p0_completed
        if p0_blocked and ctx.health.days_remaining <= 2:
            return "critical"

        return base_urgency

    def _build_decision_prompt(
        self,
        request: CouncilDecisionRequest,
        context: dict[str, Any],
    ) -> str:
        """Build LLM prompt with sprint context awareness."""
        base_prompt = f"""You are an AI Council making a {request.decision_type.value} decision.

## Request
{request.description}

## Decision Type
{request.decision_type.value}

## Resource
- Type: {request.resource_type}
- ID: {request.resource_id}
"""

        if request.sprint_context:
            sprint = context.get("sprint", {})
            base_prompt += f"""
## Sprint Context
- Sprint: {sprint.get('name')} (#{sprint.get('number')})
- Goal: {sprint.get('goal')}
- Status: {sprint.get('status')}
- Days Remaining: {sprint.get('days_remaining')}
- Completion Rate: {sprint.get('completion_rate'):.1f}%
- Risk Level: {sprint.get('health_risk')}
- Blocked Items: {sprint.get('blocked_items')}
- P0 Incomplete: {sprint.get('p0_incomplete')}
- Team Size: {sprint.get('team_size')}
- Velocity: {sprint.get('velocity_avg'):.1f} SP/sprint ({sprint.get('velocity_trend')})
"""

        base_prompt += """
## Instructions
Provide a clear, actionable recommendation considering:
1. The sprint context and timeline
2. Team availability and expertise
3. Risk level and blockers
4. Impact on sprint goal

Format your response as:
- **Recommendation**: Your recommendation
- **Reasoning**: Why this is the best approach
- **Action Items**: Numbered list of concrete steps
- **Sprint Impact**: How this affects the sprint goal
"""

        return base_prompt

    def _extract_action_items(self, recommendation: str) -> list[str]:
        """Extract action items from recommendation."""
        import re

        items: list[str] = []

        # Look for numbered items after "Action Items" header
        action_section = re.search(
            r'Action Items[:\s]*(.*?)(?:\n\n|$)',
            recommendation,
            re.IGNORECASE | re.DOTALL
        )

        if action_section:
            text = action_section.group(1)
            # Extract numbered items
            numbered = re.findall(r'\d+[.)]\s*([^\n]+)', text)
            items.extend(numbered[:5])

        # Fallback: look for any numbered list
        if not items:
            numbered = re.findall(r'\d+[.)]\s*([^\n]+)', recommendation)
            items.extend(numbered[:5])

        return items

    def _find_best_assignee(
        self,
        sprint_context: Optional[CouncilSprintContext],
        decision_type: CouncilDecisionType,
    ) -> Optional[UUID]:
        """Find best team member for the task based on expertise and availability."""
        if not sprint_context or not sprint_context.team_members:
            return None

        # Map decision type to expertise areas
        expertise_map = {
            CouncilDecisionType.CODE_REVIEW: ["backend", "frontend", "code_review"],
            CouncilDecisionType.ARCHITECTURE: ["architecture", "tech_lead", "system_design"],
            CouncilDecisionType.SECURITY: ["security", "devsecops", "owasp"],
            CouncilDecisionType.PRIORITIZATION: ["pm", "product", "backlog"],
            CouncilDecisionType.ESTIMATION: ["estimation", "planning", "developer"],
            CouncilDecisionType.BLOCKER: ["tech_lead", "senior", "troubleshooting"],
        }

        required_expertise = expertise_map.get(decision_type, [])

        # Score each team member
        best_score = -1
        best_member: Optional[UUID] = None

        for member in sprint_context.team_members:
            score = 0

            # Expertise match
            for exp in member.expertise:
                if exp.lower() in required_expertise:
                    score += 10

            # Availability factor
            score *= member.availability

            # Penalize overloaded members
            if member.workload_items > 5:
                score *= 0.7
            elif member.workload_items > 3:
                score *= 0.85

            if score > best_score:
                best_score = score
                best_member = member.user_id

        return best_member

    def _assess_sprint_impact(
        self,
        request: CouncilDecisionRequest,
        recommendation: str,
    ) -> Optional[str]:
        """Assess impact of decision on sprint goal."""
        if not request.sprint_context:
            return None

        ctx = request.sprint_context

        # Simple heuristic based on sprint state
        if ctx.health.risk_level == "critical":
            return "Critical - immediate action required to meet sprint goal"
        elif ctx.health.risk_level == "high":
            return "High - decision affects sprint goal achievement"
        elif ctx.backlog_summary.blocked_items > 0:
            return f"Medium - {ctx.backlog_summary.blocked_items} blocked items may be affected"
        elif ctx.health.days_remaining <= 2:
            return "Medium - limited time remaining in sprint"
        else:
            return "Low - minimal impact on current sprint"

    async def _log_decision(
        self,
        decision: CouncilDecision,
        request: CouncilDecisionRequest,
    ) -> None:
        """Log council decision with sprint reference for audit."""
        try:
            await self.audit_service.log_ai_council_action(
                action=AuditAction.AI_COUNCIL_COMPLETE,
                user_id=request.requester_id,
                violation_id=None,  # Not a violation, it's a decision
                details={
                    "decision_id": str(decision.decision_id),
                    "decision_type": decision.decision_type.value,
                    "sprint_id": str(decision.sprint_id) if decision.sprint_id else None,
                    "confidence": decision.confidence,
                    "urgency": decision.urgency_adjusted,
                    "providers_used": decision.providers_used,
                    "duration_ms": decision.total_duration_ms,
                    "resource_type": request.resource_type,
                    "resource_id": str(request.resource_id),
                },
            )
        except Exception as e:
            logger.warning(f"Failed to log council decision: {e}")

    async def deliberate(
        self,
        violation: ComplianceViolation,
        council_mode: CouncilMode = CouncilMode.AUTO,
        providers: Optional[list[CouncilProvider]] = None,
        user_id: Optional[UUID] = None,
    ) -> CouncilResponse:
        """
        Alias for generate_recommendation - matches router interface.

        This method is called by the council router to trigger AI Council
        deliberation for a compliance violation.

        Args:
            violation: ComplianceViolation object to analyze
            council_mode: Execution mode (single, council, auto)
            providers: Specific providers to use (default: all available)
            user_id: Requesting user (for audit logging)

        Returns:
            CouncilResponse with recommendation and deliberation details

        Note:
            This is an alias for generate_recommendation() that accepts
            the violation object directly instead of violation_id.
        """
        return await self.generate_recommendation(
            violation_id=violation.id,
            council_mode=council_mode,
            user_id=user_id,
            providers=providers,
        )


# ============================================================================
# Factory Function
# ============================================================================


def create_ai_council_service(
    db: AsyncSession,
    ai_service: Optional[AIRecommendationService] = None,
    audit_service: Optional[AuditService] = None,
    config: Optional[CouncilConfig] = None,
) -> AICouncilService:
    """
    Factory function to create AICouncilService.

    Args:
        db: Database session
        ai_service: Optional pre-configured AI recommendation service
        audit_service: Optional pre-configured audit service
        config: Optional council configuration

    Returns:
        AICouncilService instance

    Example:
        council = create_ai_council_service(db)
        result = await council.generate_recommendation(
            violation_id=violation.id,
            council_mode=CouncilMode.AUTO
        )
    """
    return AICouncilService(
        db=db,
        ai_service=ai_service,
        audit_service=audit_service,
        config=config,
    )
