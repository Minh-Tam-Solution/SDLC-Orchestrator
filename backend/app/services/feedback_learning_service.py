# =========================================================================
# STATUS: FROZEN (Sprint 173, Feb 2026)
# TIER: Post-Launch
# REASON: Non-core for current phase. Working code preserved.
# REACTIVATION: CPO approval required.
# DO NOT: Delete, refactor, or add features without CTO approval.
# =========================================================================
"""
=========================================================================
Feedback Learning Service - EP-11 Feedback Loop Closure
SDLC Orchestrator - Sprint 100 (Feedback Learning Service)

Version: 1.0.0
Date: January 23, 2026
Status: ACTIVE - Sprint 100 Implementation
Authority: Backend Lead + CTO Approved
Reference: docs/02-design/14-Technical-Specs/Feedback-Learning-Service-Design.md

Purpose:
- Extract learnings from PR review comments (AI-powered)
- Generate decomposition hints from aggregated learnings
- Synthesize CLAUDE.md update suggestions (quarterly)
- Track hint effectiveness for continuous improvement

Feedback Loop:
1. PR merged → Extract learnings from review comments
2. Monthly → Aggregate learnings → Generate hints
3. Quarterly → Synthesize → CLAUDE.md suggestions
4. Track effectiveness → Close feedback loop

AI Integration:
- Primary: Ollama qwen3:32b (Vietnamese + analysis)
- Fallback: Claude claude-sonnet-4-5-20250929 (if Ollama fails)

Zero Mock Policy: Real HTTP/database implementations
=========================================================================
"""

import json
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.pr_learning import PRLearning, FEEDBACK_TYPES, SEVERITY_LEVELS
from app.models.decomposition_hint import DecompositionHint, HintUsageLog
from app.models.learning_aggregation import LearningAggregation
from app.schemas.feedback_learning import (
    FeedbackType,
    Severity,
    LearningStatus,
    HintType,
    HintCategory,
    HintStatus,
    AggregationPeriod,
    AggregationStatus,
    PRLearningCreate,
    PRLearningExtract,
    PRLearningUpdate,
    PRLearningStats,
    DecompositionHintCreate,
    DecompositionHintUpdate,
    DecompositionHintStats,
    HintUsageCreate,
    HintUsageFeedback,
    LearningAggregationCreate,
    AggregationApplyRequest,
    LearningFilterParams,
    HintFilterParams,
    CLAUDEMdSuggestion,
)
from app.services.ollama_service import OllamaService, OllamaModel

logger = logging.getLogger(__name__)


# ============================================================================
# Feedback Type Detection Patterns
# ============================================================================

FEEDBACK_TYPE_PATTERNS = {
    FeedbackType.PATTERN_VIOLATION: [
        r"pattern",
        r"convention",
        r"style",
        r"follow the",
        r"should use",
        r"inconsistent",
        r"doesn't match",
        r"ADR",
    ],
    FeedbackType.MISSING_REQUIREMENT: [
        r"missing",
        r"requirement",
        r"acceptance criteria",
        r"doesn't handle",
        r"need to",
        r"forgot to",
        r"should also",
    ],
    FeedbackType.EDGE_CASE: [
        r"edge case",
        r"what if",
        r"corner case",
        r"null",
        r"empty",
        r"undefined",
        r"when there are no",
        r"when the list is empty",
    ],
    FeedbackType.PERFORMANCE: [
        r"performance",
        r"slow",
        r"optimize",
        r"O\(n\)",
        r"expensive",
        r"cache",
        r"memory",
        r"latency",
    ],
    FeedbackType.SECURITY_ISSUE: [
        r"security",
        r"vulnerability",
        r"injection",
        r"XSS",
        r"CSRF",
        r"sanitize",
        r"escape",
        r"validate input",
        r"auth",
    ],
    FeedbackType.TEST_COVERAGE: [
        r"test",
        r"coverage",
        r"unit test",
        r"integration test",
        r"mock",
        r"assert",
        r"verify",
    ],
    FeedbackType.DOCUMENTATION: [
        r"document",
        r"comment",
        r"docstring",
        r"README",
        r"explain",
        r"unclear",
        r"describe",
    ],
    FeedbackType.REFACTORING: [
        r"refactor",
        r"extract",
        r"simplify",
        r"DRY",
        r"duplication",
        r"clean up",
        r"restructure",
    ],
}

SEVERITY_KEYWORDS = {
    Severity.CRITICAL: ["critical", "blocker", "must fix", "security vulnerability", "data loss"],
    Severity.HIGH: ["high priority", "important", "should fix before merge", "significant"],
    Severity.MEDIUM: ["consider", "should", "would be better", "suggestion"],
    Severity.LOW: ["nit", "minor", "optional", "nice to have", "could"],
}


@dataclass
class ExtractionResult:
    """Result of extracting learning from PR comment."""

    feedback_type: FeedbackType
    severity: Severity
    pattern_extracted: Optional[str]
    corrected_approach: Optional[str]
    confidence: float
    ai_model: str


class FeedbackLearningService:
    """
    Service for managing feedback learning loop (EP-11).

    Responsibilities:
    - Extract learnings from PR review comments
    - Generate decomposition hints from learnings
    - Aggregate learnings monthly/quarterly
    - Generate CLAUDE.md update suggestions
    - Track hint effectiveness

    Usage:
        service = FeedbackLearningService(db, ollama_service)
        learnings = await service.extract_learnings_from_pr(project_id, pr_data)
        hints = await service.update_decomposition_hints(project_id)
    """

    def __init__(
        self,
        db: AsyncSession,
        ollama_service: Optional[OllamaService] = None,
    ):
        """
        Initialize FeedbackLearningService.

        Args:
            db: Async database session
            ollama_service: Optional Ollama service for AI extraction
        """
        self.db = db
        self.ollama = ollama_service or OllamaService()

    # ========================================================================
    # PR Learning Methods
    # ========================================================================

    async def extract_learning_from_comment(
        self,
        project_id: UUID,
        comment_data: PRLearningExtract,
        use_ai: bool = True,
    ) -> PRLearning:
        """
        Extract a learning from a PR review comment.

        Args:
            project_id: Project UUID
            comment_data: PR comment data
            use_ai: Whether to use AI for extraction

        Returns:
            Created PRLearning object
        """
        logger.info(
            f"Extracting learning from PR #{comment_data.pr_number} comment"
        )

        # Step 1: Classify feedback type and severity
        if use_ai:
            extraction = await self._extract_with_ai(comment_data)
        else:
            extraction = self._extract_with_rules(comment_data.comment_body)

        # Step 2: Create learning record
        learning = PRLearning(
            id=uuid4(),
            project_id=project_id,
            pr_number=comment_data.pr_number,
            pr_title=comment_data.pr_title,
            pr_url=comment_data.pr_url,
            feedback_type=extraction.feedback_type.value,
            severity=extraction.severity.value,
            review_comment=comment_data.comment_body,
            corrected_approach=extraction.corrected_approach,
            pattern_extracted=extraction.pattern_extracted,
            file_path=comment_data.file_path,
            original_code=comment_data.diff_hunk,
            reviewer_github_login=comment_data.reviewer_github_login,
            status="extracted",
            ai_extracted=use_ai,
            ai_confidence=extraction.confidence if use_ai else None,
            ai_model=extraction.ai_model if use_ai else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(learning)
        await self.db.commit()
        await self.db.refresh(learning)

        logger.info(
            f"Created learning {learning.id} for PR #{comment_data.pr_number}: "
            f"{extraction.feedback_type.value} ({extraction.severity.value})"
        )

        return learning

    async def create_learning_manual(
        self,
        project_id: UUID,
        data: PRLearningCreate,
        user_id: Optional[UUID] = None,
    ) -> PRLearning:
        """
        Create a learning manually (not from AI extraction).

        Args:
            project_id: Project UUID
            data: Learning data
            user_id: User who created the learning

        Returns:
            Created PRLearning object
        """
        learning = PRLearning(
            id=uuid4(),
            project_id=project_id,
            pr_number=data.pr_number,
            pr_title=data.pr_title,
            pr_url=data.pr_url,
            feedback_type=data.feedback_type.value,
            severity=data.severity.value,
            review_comment=data.review_comment,
            corrected_approach=data.corrected_approach,
            pattern_extracted=data.pattern_extracted,
            file_path=data.file_path,
            line_start=data.line_start,
            line_end=data.line_end,
            related_adr=data.related_adr,
            original_code=data.original_code,
            original_spec_section=data.original_spec_section,
            reviewer_github_login=data.reviewer_github_login,
            tags=data.tags,
            status="extracted",
            ai_extracted=False,
            reviewer_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(learning)
        await self.db.commit()
        await self.db.refresh(learning)

        logger.info(f"Created manual learning {learning.id}")
        return learning

    async def get_learning(self, learning_id: UUID) -> Optional[PRLearning]:
        """Get a learning by ID."""
        result = await self.db.execute(
            select(PRLearning).where(PRLearning.id == learning_id)
        )
        return result.scalar_one_or_none()

    async def list_learnings(
        self,
        project_id: UUID,
        filters: Optional[LearningFilterParams] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PRLearning], int]:
        """
        List learnings with filtering and pagination.

        Args:
            project_id: Project UUID
            filters: Optional filter parameters
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (learnings list, total count)
        """
        query = select(PRLearning).where(PRLearning.project_id == project_id)

        if filters:
            if filters.feedback_type:
                query = query.where(
                    PRLearning.feedback_type == filters.feedback_type.value
                )
            if filters.severity:
                query = query.where(PRLearning.severity == filters.severity.value)
            if filters.status:
                query = query.where(PRLearning.status == filters.status.value)
            if filters.ai_extracted is not None:
                query = query.where(PRLearning.ai_extracted == filters.ai_extracted)
            if filters.applied_to_claude_md is not None:
                query = query.where(
                    PRLearning.applied_to_claude_md == filters.applied_to_claude_md
                )
            if filters.applied_to_decomposition is not None:
                query = query.where(
                    PRLearning.applied_to_decomposition
                    == filters.applied_to_decomposition
                )
            if filters.pr_number:
                query = query.where(PRLearning.pr_number == filters.pr_number)
            if filters.from_date:
                query = query.where(
                    func.date(PRLearning.created_at) >= filters.from_date
                )
            if filters.to_date:
                query = query.where(
                    func.date(PRLearning.created_at) <= filters.to_date
                )
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.where(
                    or_(
                        PRLearning.review_comment.ilike(search_term),
                        PRLearning.pattern_extracted.ilike(search_term),
                        PRLearning.corrected_approach.ilike(search_term),
                    )
                )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination
        query = (
            query.order_by(desc(PRLearning.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        learnings = result.scalars().all()

        return list(learnings), total

    async def update_learning(
        self,
        learning_id: UUID,
        data: PRLearningUpdate,
    ) -> Optional[PRLearning]:
        """Update a learning."""
        learning = await self.get_learning(learning_id)
        if not learning:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(learning, key):
                setattr(learning, key, value)

        learning.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(learning)

        return learning

    async def get_learning_stats(
        self,
        project_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> PRLearningStats:
        """Get learning statistics for a project."""
        query = select(PRLearning).where(PRLearning.project_id == project_id)

        if from_date:
            query = query.where(func.date(PRLearning.created_at) >= from_date)
        if to_date:
            query = query.where(func.date(PRLearning.created_at) <= to_date)

        result = await self.db.execute(query)
        learnings = result.scalars().all()

        by_feedback_type: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        by_status: dict[str, int] = {}
        applied_count = 0
        pending_count = 0

        for learning in learnings:
            by_feedback_type[learning.feedback_type] = (
                by_feedback_type.get(learning.feedback_type, 0) + 1
            )
            by_severity[learning.severity] = (
                by_severity.get(learning.severity, 0) + 1
            )
            by_status[learning.status] = by_status.get(learning.status, 0) + 1

            if learning.applied_to_claude_md or learning.applied_to_decomposition:
                applied_count += 1
            if learning.status == "extracted":
                pending_count += 1

        return PRLearningStats(
            total_learnings=len(learnings),
            by_feedback_type=by_feedback_type,
            by_severity=by_severity,
            by_status=by_status,
            applied_count=applied_count,
            pending_count=pending_count,
            period_start=from_date,
            period_end=to_date,
        )

    # ========================================================================
    # Decomposition Hint Methods
    # ========================================================================

    async def create_hint(
        self,
        project_id: UUID,
        data: DecompositionHintCreate,
        user_id: Optional[UUID] = None,
    ) -> DecompositionHint:
        """Create a decomposition hint manually."""
        hint = DecompositionHint(
            id=uuid4(),
            project_id=project_id,
            hint_type=data.hint_type.value,
            category=data.category.value,
            subcategory=data.subcategory,
            title=data.title,
            description=data.description,
            example_good=data.example_good,
            example_bad=data.example_bad,
            rationale=data.rationale,
            applies_to=data.applies_to,
            languages=data.languages,
            frameworks=data.frameworks,
            confidence=data.confidence,
            source_learning_id=data.source_learning_id,
            tags=data.tags,
            related_adrs=data.related_adrs,
            status="active",
            ai_generated=False,
            created_by=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(hint)
        await self.db.commit()
        await self.db.refresh(hint)

        logger.info(f"Created decomposition hint {hint.id}: {hint.title}")
        return hint

    async def get_hint(self, hint_id: UUID) -> Optional[DecompositionHint]:
        """Get a hint by ID."""
        result = await self.db.execute(
            select(DecompositionHint).where(DecompositionHint.id == hint_id)
        )
        return result.scalar_one_or_none()

    async def list_hints(
        self,
        project_id: UUID,
        filters: Optional[HintFilterParams] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DecompositionHint], int]:
        """List hints with filtering and pagination."""
        query = select(DecompositionHint).where(
            DecompositionHint.project_id == project_id
        )

        if filters:
            if filters.hint_type:
                query = query.where(
                    DecompositionHint.hint_type == filters.hint_type.value
                )
            if filters.category:
                query = query.where(
                    DecompositionHint.category == filters.category.value
                )
            if filters.status:
                query = query.where(
                    DecompositionHint.status == filters.status.value
                )
            if filters.ai_generated is not None:
                query = query.where(
                    DecompositionHint.ai_generated == filters.ai_generated
                )
            if filters.human_verified is not None:
                query = query.where(
                    DecompositionHint.human_verified == filters.human_verified
                )
            if filters.min_confidence is not None:
                query = query.where(
                    DecompositionHint.confidence >= filters.min_confidence
                )
            if filters.min_effectiveness is not None:
                query = query.where(
                    DecompositionHint.effectiveness_score >= filters.min_effectiveness
                )
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.where(
                    or_(
                        DecompositionHint.title.ilike(search_term),
                        DecompositionHint.description.ilike(search_term),
                    )
                )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination
        query = (
            query.order_by(desc(DecompositionHint.usage_count))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        hints = result.scalars().all()

        return list(hints), total

    async def get_active_hints_for_decomposition(
        self,
        project_id: UUID,
        applies_to: Optional[str] = None,
        language: Optional[str] = None,
        framework: Optional[str] = None,
    ) -> list[DecompositionHint]:
        """
        Get active hints relevant for task decomposition.

        Args:
            project_id: Project UUID
            applies_to: Filter by area (frontend, backend, etc.)
            language: Filter by language
            framework: Filter by framework

        Returns:
            List of relevant active hints
        """
        query = select(DecompositionHint).where(
            and_(
                DecompositionHint.project_id == project_id,
                DecompositionHint.status == "active",
                DecompositionHint.confidence >= 0.5,  # Only confident hints
            )
        )

        result = await self.db.execute(query)
        hints = result.scalars().all()

        # Filter by applicability
        filtered_hints = []
        for hint in hints:
            # Check applies_to
            if applies_to and "all" not in hint.applies_to:
                if applies_to not in hint.applies_to:
                    continue

            # Check language
            if language and "all" not in hint.languages:
                if language not in hint.languages:
                    continue

            # Check framework
            if framework and "all" not in hint.frameworks:
                if framework not in hint.frameworks:
                    continue

            filtered_hints.append(hint)

        # Sort by effectiveness score (best first)
        filtered_hints.sort(
            key=lambda h: (h.effectiveness_score or 0, h.usage_count),
            reverse=True,
        )

        return filtered_hints

    async def update_hint(
        self,
        hint_id: UUID,
        data: DecompositionHintUpdate,
    ) -> Optional[DecompositionHint]:
        """Update a decomposition hint."""
        hint = await self.get_hint(hint_id)
        if not hint:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(hint, key):
                setattr(hint, key, value)

        hint.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(hint)

        return hint

    async def verify_hint(
        self,
        hint_id: UUID,
        user_id: UUID,
    ) -> Optional[DecompositionHint]:
        """Mark a hint as human verified."""
        hint = await self.get_hint(hint_id)
        if not hint:
            return None

        hint.human_verified = True
        hint.verified_by = user_id
        hint.verified_at = datetime.utcnow()
        hint.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(hint)

        logger.info(f"Hint {hint_id} verified by user {user_id}")
        return hint

    async def record_hint_usage(
        self,
        project_id: UUID,
        data: HintUsageCreate,
        user_id: Optional[UUID] = None,
    ) -> HintUsageLog:
        """Record usage of a hint during decomposition."""
        # Update hint usage count
        hint = await self.get_hint(data.hint_id)
        if hint:
            hint.usage_count += 1
            hint.last_used_at = datetime.utcnow()

        # Create usage log
        usage_log = HintUsageLog(
            id=uuid4(),
            hint_id=data.hint_id,
            project_id=project_id,
            used_by=user_id,
            decomposition_session_id=data.decomposition_session_id,
            task_description=data.task_description,
            plan_generated=data.plan_generated,
            used_at=datetime.utcnow(),
        )

        self.db.add(usage_log)
        await self.db.commit()
        await self.db.refresh(usage_log)

        return usage_log

    async def provide_hint_feedback(
        self,
        usage_log_id: UUID,
        feedback: HintUsageFeedback,
    ) -> Optional[HintUsageLog]:
        """Provide feedback on hint usage outcome."""
        result = await self.db.execute(
            select(HintUsageLog).where(HintUsageLog.id == usage_log_id)
        )
        usage_log = result.scalar_one_or_none()

        if not usage_log:
            return None

        usage_log.outcome = feedback.outcome.value
        usage_log.pr_id = feedback.pr_id
        usage_log.feedback = feedback.feedback
        usage_log.error_prevented = feedback.outcome == "prevented_error"

        # Update hint effectiveness
        hint = await self.get_hint(usage_log.hint_id)
        if hint and feedback.outcome == "prevented_error":
            hint.prevented_errors += 1
            if hint.usage_count > 0:
                hint.effectiveness_score = hint.prevented_errors / hint.usage_count

        await self.db.commit()
        await self.db.refresh(usage_log)

        return usage_log

    async def get_hint_stats(self, project_id: UUID) -> DecompositionHintStats:
        """Get hint statistics for a project."""
        query = select(DecompositionHint).where(
            DecompositionHint.project_id == project_id
        )

        result = await self.db.execute(query)
        hints = result.scalars().all()

        by_type: dict[str, int] = {}
        by_category: dict[str, int] = {}
        total_usage = 0
        total_prevented = 0
        effectiveness_scores = []
        human_verified_count = 0
        active_count = 0

        for hint in hints:
            by_type[hint.hint_type] = by_type.get(hint.hint_type, 0) + 1
            by_category[hint.category] = by_category.get(hint.category, 0) + 1
            total_usage += hint.usage_count
            total_prevented += hint.prevented_errors

            if hint.effectiveness_score is not None:
                effectiveness_scores.append(hint.effectiveness_score)

            if hint.human_verified:
                human_verified_count += 1

            if hint.status == "active":
                active_count += 1

        avg_effectiveness = (
            sum(effectiveness_scores) / len(effectiveness_scores)
            if effectiveness_scores
            else None
        )

        return DecompositionHintStats(
            total_hints=len(hints),
            active_hints=active_count,
            by_type=by_type,
            by_category=by_category,
            total_usage=total_usage,
            total_prevented_errors=total_prevented,
            average_effectiveness=avg_effectiveness,
            human_verified_count=human_verified_count,
        )

    # ========================================================================
    # Aggregation Methods
    # ========================================================================

    async def create_aggregation(
        self,
        project_id: UUID,
        data: LearningAggregationCreate,
    ) -> LearningAggregation:
        """
        Create and process a learning aggregation.

        This method:
        1. Collects learnings from the period
        2. Calculates statistics
        3. Uses AI to generate suggestions
        4. Stores the aggregation

        Args:
            project_id: Project UUID
            data: Aggregation period configuration

        Returns:
            Created LearningAggregation object
        """
        logger.info(
            f"Creating {data.period_type.value} aggregation for project {project_id}"
        )

        # Get learnings from period
        learnings_query = select(PRLearning).where(
            and_(
                PRLearning.project_id == project_id,
                func.date(PRLearning.created_at) >= data.period_start,
                func.date(PRLearning.created_at) <= data.period_end,
            )
        )
        result = await self.db.execute(learnings_query)
        learnings = result.scalars().all()

        # Calculate statistics
        by_feedback_type: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        file_counts: dict[str, int] = {}
        patterns: list[str] = []

        for learning in learnings:
            by_feedback_type[learning.feedback_type] = (
                by_feedback_type.get(learning.feedback_type, 0) + 1
            )
            by_severity[learning.severity] = (
                by_severity.get(learning.severity, 0) + 1
            )

            if learning.file_path:
                file_counts[learning.file_path] = (
                    file_counts.get(learning.file_path, 0) + 1
                )

            if learning.pattern_extracted:
                patterns.append(learning.pattern_extracted)

        # Sort and get top items
        top_files = sorted(
            [{"file": k, "count": v} for k, v in file_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:10]

        top_patterns = [{"pattern": p, "occurrences": patterns.count(p)} for p in set(patterns)]
        top_patterns.sort(key=lambda x: x["occurrences"], reverse=True)
        top_patterns = top_patterns[:10]

        # Generate AI suggestions if enough learnings
        claude_md_suggestions = None
        decomposition_hints = None
        adr_recommendations = None
        ai_model = None
        ai_time = None

        if len(learnings) >= 3:
            start_time = datetime.utcnow()
            try:
                suggestions = await self._generate_aggregation_suggestions(
                    learnings, top_patterns
                )
                claude_md_suggestions = suggestions.get("claude_md")
                decomposition_hints = suggestions.get("hints")
                adr_recommendations = suggestions.get("adrs")
                ai_model = suggestions.get("model")
            except Exception as e:
                logger.warning(f"Failed to generate AI suggestions: {e}")

            ai_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Create aggregation record
        aggregation = LearningAggregation(
            id=uuid4(),
            project_id=project_id,
            period_type=data.period_type.value,
            period_start=data.period_start,
            period_end=data.period_end,
            total_learnings=len(learnings),
            by_feedback_type=by_feedback_type,
            by_severity=by_severity,
            top_patterns=top_patterns,
            top_files=top_files,
            claude_md_suggestions=claude_md_suggestions,
            decomposition_hints=decomposition_hints,
            adr_recommendations=adr_recommendations,
            status="processed" if len(learnings) >= 3 else "pending",
            processed_at=datetime.utcnow() if len(learnings) >= 3 else None,
            ai_model=ai_model,
            ai_processing_time_ms=ai_time,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(aggregation)
        await self.db.commit()
        await self.db.refresh(aggregation)

        logger.info(
            f"Created aggregation {aggregation.id} with {len(learnings)} learnings"
        )
        return aggregation

    async def get_aggregation(self, aggregation_id: UUID) -> Optional[LearningAggregation]:
        """Get an aggregation by ID."""
        result = await self.db.execute(
            select(LearningAggregation).where(LearningAggregation.id == aggregation_id)
        )
        return result.scalar_one_or_none()

    async def list_aggregations(
        self,
        project_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[LearningAggregation], int]:
        """List aggregations with pagination."""
        query = select(LearningAggregation).where(
            LearningAggregation.project_id == project_id
        )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination
        query = (
            query.order_by(desc(LearningAggregation.period_start))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        aggregations = result.scalars().all()

        return list(aggregations), total

    async def apply_aggregation(
        self,
        aggregation_id: UUID,
        request: AggregationApplyRequest,
        user_id: UUID,
    ) -> Optional[LearningAggregation]:
        """
        Apply aggregation suggestions.

        This creates decomposition hints from the suggestions
        and marks learnings as applied.

        Args:
            aggregation_id: Aggregation UUID
            request: Apply configuration
            user_id: User applying the suggestions

        Returns:
            Updated aggregation
        """
        aggregation = await self.get_aggregation(aggregation_id)
        if not aggregation:
            return None

        hints_created = 0

        # Create hints from suggestions
        if request.apply_hints and aggregation.decomposition_hints:
            for hint_data in aggregation.decomposition_hints:
                hint = DecompositionHint(
                    id=uuid4(),
                    project_id=aggregation.project_id,
                    hint_type=hint_data.get("type", "pattern"),
                    category=hint_data.get("category", "other"),
                    title=hint_data.get("title", "Untitled"),
                    description=hint_data.get("description", ""),
                    example_good=hint_data.get("example_good"),
                    example_bad=hint_data.get("example_bad"),
                    rationale=hint_data.get("rationale"),
                    confidence=hint_data.get("confidence", 0.7),
                    aggregation_id=aggregation_id,
                    status="active",
                    ai_generated=True,
                    ai_model=aggregation.ai_model,
                    created_by=user_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                self.db.add(hint)
                hints_created += 1

        # Update aggregation status
        aggregation.status = "applied"
        aggregation.applied_at = datetime.utcnow()
        aggregation.processed_by = user_id

        await self.db.commit()
        await self.db.refresh(aggregation)

        logger.info(
            f"Applied aggregation {aggregation_id}: created {hints_created} hints"
        )
        return aggregation

    async def reject_aggregation(
        self,
        aggregation_id: UUID,
        reason: str,
        user_id: UUID,
    ) -> Optional[LearningAggregation]:
        """Reject aggregation suggestions."""
        aggregation = await self.get_aggregation(aggregation_id)
        if not aggregation:
            return None

        aggregation.status = "rejected"
        aggregation.rejection_reason = reason
        aggregation.processed_by = user_id
        aggregation.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(aggregation)

        return aggregation

    # ========================================================================
    # Private AI Methods
    # ========================================================================

    async def _extract_with_ai(
        self,
        comment_data: PRLearningExtract,
    ) -> ExtractionResult:
        """
        Extract learning details using AI.

        Uses Ollama for analysis and classification.
        """
        prompt = f"""Analyze this code review comment and extract learning insights.

PR: #{comment_data.pr_number} - {comment_data.pr_title}
File: {comment_data.file_path or 'Unknown'}
Reviewer: {comment_data.reviewer_github_login}

Comment:
{comment_data.comment_body}

Code Context:
{comment_data.diff_hunk or 'Not available'}

Respond in JSON format:
{{
    "feedback_type": "pattern_violation|missing_requirement|edge_case|performance|security_issue|test_coverage|documentation|refactoring|other",
    "severity": "low|medium|high|critical",
    "pattern_extracted": "Reusable pattern or lesson learned (1-2 sentences)",
    "corrected_approach": "Brief description of the correct approach",
    "confidence": 0.0-1.0
}}

Be concise and focus on extractable patterns that could prevent similar issues in future."""

        try:
            response = await self.ollama.generate_async(
                prompt=prompt,
                model=OllamaModel.QWEN3_32B,
                temperature=0.3,
                max_tokens=500,
            )

            # Parse JSON from response
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                data = json.loads(json_match.group())

                return ExtractionResult(
                    feedback_type=FeedbackType(data.get("feedback_type", "other")),
                    severity=Severity(data.get("severity", "medium")),
                    pattern_extracted=data.get("pattern_extracted"),
                    corrected_approach=data.get("corrected_approach"),
                    confidence=float(data.get("confidence", 0.7)),
                    ai_model="qwen3:32b",
                )

        except Exception as e:
            logger.warning(f"AI extraction failed, using rules: {e}")

        # Fallback to rule-based extraction
        return self._extract_with_rules(comment_data.comment_body)

    def _extract_with_rules(self, comment: str) -> ExtractionResult:
        """
        Extract learning details using rule-based patterns.

        Fallback when AI is unavailable.
        """
        comment_lower = comment.lower()

        # Detect feedback type
        detected_type = FeedbackType.OTHER
        max_matches = 0

        for feedback_type, patterns in FEEDBACK_TYPE_PATTERNS.items():
            matches = sum(
                1 for pattern in patterns
                if re.search(pattern, comment_lower)
            )
            if matches > max_matches:
                max_matches = matches
                detected_type = feedback_type

        # Detect severity
        detected_severity = Severity.MEDIUM

        for severity, keywords in SEVERITY_KEYWORDS.items():
            if any(keyword in comment_lower for keyword in keywords):
                detected_severity = severity
                break

        return ExtractionResult(
            feedback_type=detected_type,
            severity=detected_severity,
            pattern_extracted=None,
            corrected_approach=None,
            confidence=0.5,
            ai_model="rules",
        )

    async def _generate_aggregation_suggestions(
        self,
        learnings: list[PRLearning],
        top_patterns: list[dict],
    ) -> dict[str, Any]:
        """Generate suggestions from aggregated learnings using AI."""
        # Prepare context
        learnings_summary = []
        for learning in learnings[:20]:  # Limit for context
            learnings_summary.append(
                f"- [{learning.feedback_type}] {learning.review_comment[:200]}"
            )

        prompt = f"""Analyze these PR review learnings and generate improvement suggestions.

LEARNINGS ({len(learnings)} total, showing first 20):
{chr(10).join(learnings_summary)}

TOP PATTERNS:
{json.dumps(top_patterns, indent=2)}

Generate suggestions in JSON format:
{{
    "claude_md": [
        {{
            "section": "Section name (e.g., 'Security', 'Testing')",
            "content": "Suggested addition to CLAUDE.md",
            "reason": "Why this should be added",
            "priority": "high|medium|low"
        }}
    ],
    "hints": [
        {{
            "type": "pattern|antipattern|convention|checklist",
            "category": "security|testing|architecture|naming|error_handling|performance|other",
            "title": "Short title",
            "description": "Full description",
            "example_good": "Good example (optional)",
            "example_bad": "Bad example (optional)",
            "rationale": "Why this matters",
            "confidence": 0.0-1.0
        }}
    ],
    "adrs": [
        {{
            "title": "Suggested ADR title",
            "problem": "Problem statement",
            "decision": "Recommended decision",
            "priority": "high|medium|low"
        }}
    ]
}}

Focus on actionable, reusable patterns. Limit to 3-5 suggestions per category."""

        try:
            response = await self.ollama.generate_async(
                prompt=prompt,
                model=OllamaModel.QWEN3_32B,
                temperature=0.4,
                max_tokens=2000,
            )

            # Parse JSON from response
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                data = json.loads(json_match.group())
                data["model"] = "qwen3:32b"
                return data

        except Exception as e:
            logger.warning(f"Failed to generate suggestions: {e}")

        return {"model": None}

    # ========================================================================
    # Utility Methods
    # ========================================================================

    async def generate_hints_from_learnings(
        self,
        project_id: UUID,
        since: Optional[date] = None,
    ) -> int:
        """
        Generate decomposition hints from unapplied learnings.

        This is the monthly aggregation job that closes the feedback loop.

        Args:
            project_id: Project UUID
            since: Only process learnings after this date

        Returns:
            Number of hints created
        """
        # Get unapplied learnings with extracted patterns
        query = select(PRLearning).where(
            and_(
                PRLearning.project_id == project_id,
                PRLearning.applied_to_decomposition == False,
                PRLearning.pattern_extracted.isnot(None),
                PRLearning.status != "archived",
            )
        )

        if since:
            query = query.where(func.date(PRLearning.created_at) >= since)

        result = await self.db.execute(query)
        learnings = result.scalars().all()

        hints_created = 0

        for learning in learnings:
            # Determine hint type based on feedback type
            hint_type = "pattern"
            if learning.feedback_type in ["pattern_violation", "refactoring"]:
                hint_type = "antipattern"
            elif learning.feedback_type == "security_issue":
                hint_type = "checklist"

            # Map feedback type to category
            category_map = {
                "security_issue": "security",
                "test_coverage": "testing",
                "performance": "performance",
                "documentation": "documentation",
                "pattern_violation": "architecture",
                "refactoring": "architecture",
            }
            category = category_map.get(learning.feedback_type, "other")

            # Create hint
            hint = DecompositionHint(
                id=uuid4(),
                project_id=project_id,
                hint_type=hint_type,
                category=category,
                title=f"From PR #{learning.pr_number}",
                description=learning.pattern_extracted,
                rationale=learning.corrected_approach,
                confidence=learning.ai_confidence or 0.6,
                source_learning_id=learning.id,
                status="active",
                ai_generated=learning.ai_extracted,
                ai_model=learning.ai_model,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self.db.add(hint)

            # Mark learning as applied
            learning.applied_to_decomposition = True
            learning.applied_at = datetime.utcnow()

            hints_created += 1

        await self.db.commit()

        logger.info(
            f"Generated {hints_created} hints from learnings for project {project_id}"
        )
        return hints_created

    async def generate_hint_from_pattern(
        self,
        project_id: UUID,
        pattern: dict[str, Any],
        source_aggregation_id: Optional[UUID] = None,
    ) -> Optional[DecompositionHint]:
        """
        Generate a decomposition hint from an aggregated pattern.

        This is called by the monthly aggregation job to create hints
        from identified patterns.

        Args:
            project_id: Project UUID
            pattern: Pattern dict with feedback_type, themes, count, etc.
            source_aggregation_id: UUID of source aggregation

        Returns:
            Created DecompositionHint or None if generation fails
        """
        feedback_type = pattern.get("feedback_type", "unknown")
        themes = pattern.get("themes", [])
        count = pattern.get("count", 0)
        file_extension = pattern.get("file_extension")

        # Skip if insufficient data
        if not themes or count < 3:
            return None

        # Determine hint type based on feedback type
        hint_type_map = {
            "pattern_violation": HintType.ANTIPATTERN,
            "missing_requirement": HintType.CHECKLIST,
            "edge_case": HintType.PATTERN,
            "performance": HintType.PATTERN,
            "security_issue": HintType.CHECKLIST,
            "test_coverage": HintType.CHECKLIST,
            "documentation": HintType.CONVENTION,
            "refactoring": HintType.ANTIPATTERN,
        }
        hint_type = hint_type_map.get(feedback_type, HintType.PATTERN)

        # Map feedback type to category
        category_map = {
            "security_issue": HintCategory.SECURITY,
            "test_coverage": HintCategory.TESTING,
            "performance": HintCategory.PERFORMANCE,
            "documentation": HintCategory.DOCUMENTATION,
            "pattern_violation": HintCategory.ARCHITECTURE,
            "refactoring": HintCategory.ARCHITECTURE,
            "edge_case": HintCategory.ERROR_HANDLING,
            "missing_requirement": HintCategory.OTHER,
        }
        category = category_map.get(feedback_type, HintCategory.OTHER)

        # Generate title from themes
        primary_theme = themes[0] if themes else feedback_type
        title = f"{feedback_type.replace('_', ' ').title()}: {primary_theme.title()}"

        # Generate description using AI if available
        description = None
        ai_model = None

        try:
            prompt = f"""Generate a concise decomposition hint based on this pattern.

PATTERN:
- Type: {feedback_type}
- Themes: {', '.join(themes)}
- Occurrences: {count}
- File type: {file_extension or 'various'}

Generate a 2-3 sentence description that:
1. Describes the issue pattern
2. Explains why it matters
3. Suggests how to prevent it

Be concise and actionable. Output only the description text, no formatting."""

            description = await self.ollama.generate_async(
                prompt=prompt,
                model=OllamaModel.QWEN3_32B,
                temperature=0.3,
                max_tokens=200,
            )
            ai_model = "qwen3:32b"

        except Exception as e:
            logger.warning(f"AI description generation failed: {e}")
            # Fallback description
            description = (
                f"Based on {count} occurrences in code reviews, "
                f"watch for {feedback_type.replace('_', ' ')} issues "
                f"related to: {', '.join(themes[:3])}."
            )

        # Calculate confidence based on pattern count and consistency
        base_confidence = min(0.5 + (count * 0.05), 0.9)

        # Create the hint
        hint = DecompositionHint(
            id=uuid4(),
            project_id=project_id,
            hint_type=hint_type.value,
            category=category.value,
            title=title,
            description=description,
            applies_to=["all"],
            languages=[file_extension] if file_extension else ["all"],
            frameworks=["all"],
            confidence=base_confidence,
            aggregation_id=source_aggregation_id,
            status="active",
            ai_generated=True,
            ai_model=ai_model,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(hint)
        await self.db.flush()

        logger.info(
            f"Generated hint {hint.id} from pattern: {title} "
            f"(confidence={base_confidence:.2f})"
        )

        return hint

    async def generate_claude_md_suggestions(
        self,
        project_id: UUID,
        patterns: list[dict],
        by_feedback_type: dict[str, int],
        by_severity: dict[str, int],
        total_learnings: int,
    ) -> list[dict]:
        """
        Generate CLAUDE.md update suggestions from quarterly patterns.

        This is called by the quarterly synthesis job to create
        suggestions for CLAUDE.md improvements.

        Args:
            project_id: Project UUID
            patterns: Merged patterns from quarterly aggregations
            by_feedback_type: Count by feedback type
            by_severity: Count by severity
            total_learnings: Total learnings in quarter

        Returns:
            List of CLAUDE.md suggestion dicts
        """
        # Prepare context for AI
        patterns_summary = []
        for p in patterns[:10]:
            patterns_summary.append(
                f"- {p.get('feedback_type', 'unknown')}: "
                f"{', '.join(p.get('themes', [])[:3])} "
                f"({p.get('count', 0)} occurrences)"
            )

        prompt = f"""Analyze these quarterly code review patterns and suggest CLAUDE.md updates.

QUARTERLY SUMMARY ({total_learnings} total learnings):

By Feedback Type:
{json.dumps(by_feedback_type, indent=2)}

By Severity:
{json.dumps(by_severity, indent=2)}

Top Patterns:
{chr(10).join(patterns_summary)}

Generate 3-5 CLAUDE.md suggestions in JSON format:
[
    {{
        "section": "Section name (e.g., 'Security Guidelines', 'Testing Requirements')",
        "content": "Concise text to add to CLAUDE.md (2-4 sentences)",
        "reason": "Why this should be added based on the patterns",
        "priority": "high|medium|low"
    }}
]

Focus on:
1. High-severity patterns that need enforcement
2. Recurring issues that could be prevented with clear guidelines
3. Best practices derived from the learnings

Output only valid JSON array."""

        try:
            response = await self.ollama.generate_async(
                prompt=prompt,
                model=OllamaModel.QWEN3_32B,
                temperature=0.4,
                max_tokens=1500,
            )

            # Parse JSON from response
            json_match = re.search(r"\[[\s\S]*\]", response)
            if json_match:
                suggestions = json.loads(json_match.group())

                # Validate and clean suggestions
                valid_suggestions = []
                for s in suggestions:
                    if all(k in s for k in ["section", "content", "reason"]):
                        valid_suggestions.append({
                            "section": s.get("section", "General"),
                            "content": s.get("content", "")[:500],
                            "reason": s.get("reason", "")[:300],
                            "priority": s.get("priority", "medium"),
                        })

                logger.info(
                    f"Generated {len(valid_suggestions)} CLAUDE.md suggestions "
                    f"for project {project_id}"
                )
                return valid_suggestions

        except Exception as e:
            logger.warning(f"Failed to generate CLAUDE.md suggestions: {e}")

        # Fallback: Generate basic suggestions from high-count patterns
        fallback_suggestions = []

        # Find highest severity patterns
        critical_high = by_severity.get("critical", 0) + by_severity.get("high", 0)
        if critical_high > 5:
            fallback_suggestions.append({
                "section": "Code Review Focus",
                "content": (
                    f"Pay special attention to critical and high severity issues. "
                    f"This quarter saw {critical_high} such issues. "
                    f"Common areas: {', '.join(list(by_feedback_type.keys())[:3])}."
                ),
                "reason": f"High number of critical/high severity issues ({critical_high}) this quarter",
                "priority": "high",
            })

        # Add pattern-based suggestions
        for pattern in patterns[:2]:
            if pattern.get("count", 0) >= 5:
                feedback_type = pattern.get("feedback_type", "issue")
                themes = pattern.get("themes", [])

                fallback_suggestions.append({
                    "section": feedback_type.replace("_", " ").title(),
                    "content": (
                        f"Ensure code addresses common {feedback_type.replace('_', ' ')} issues. "
                        f"Key areas: {', '.join(themes[:3])}."
                    ),
                    "reason": f"Recurring pattern with {pattern.get('count', 0)} occurrences",
                    "priority": "medium",
                })

        return fallback_suggestions
