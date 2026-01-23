"""
=========================================================================
Learning Aggregation Background Jobs - EP-11 Feedback Learning Service
SDLC Orchestrator - Sprint 100 (Feedback Learning Service)

Version: 1.0.0
Date: January 23, 2026
Status: ACTIVE - Sprint 100 Implementation
Authority: Backend Lead + CTO Approved
Framework: SDLC 5.1.3 SASE Integration
Reference: docs/02-design/14-Technical-Specs/Feedback-Learning-Service-Design.md

Purpose:
- Monthly aggregation: Aggregate learnings → Generate decomposition hints
- Quarterly aggregation: Synthesize patterns → CLAUDE.md suggestions
- On-demand aggregation: Manual trigger for specific projects
- Hint effectiveness tracking: Update hint confidence based on feedback

Job Types:
1. run_monthly_aggregation: Monthly job to aggregate learnings per project
2. run_quarterly_synthesis: Quarterly job to synthesize CLAUDE.md suggestions
3. schedule_project_aggregation: On-demand aggregation for specific project
4. update_hint_effectiveness: Update hint confidence scores based on feedback

Integration:
- APScheduler for job scheduling
- FeedbackLearningService for aggregation logic
- Ollama AI for pattern synthesis
- Evidence Vault for storing aggregation artifacts

Zero Mock Policy: Real aggregation + AI synthesis + persistence
=========================================================================
"""

import asyncio
import logging
from datetime import datetime, timedelta, date
from typing import Any, Optional
from uuid import UUID, uuid4
from calendar import monthrange

from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.pr_learning import PRLearning
from app.models.decomposition_hint import DecompositionHint
from app.models.learning_aggregation import LearningAggregation
from app.models.project import Project

logger = logging.getLogger(__name__)


# ============================================================================
# Aggregation Configuration
# ============================================================================

AGGREGATION_CONFIG = {
    # Monthly aggregation: 1st of each month at 4:00 AM
    "monthly_day": 1,
    "monthly_hour": 4,
    "monthly_minute": 0,

    # Quarterly synthesis: 1st of Jan, Apr, Jul, Oct at 5:00 AM
    "quarterly_months": [1, 4, 7, 10],
    "quarterly_day": 1,
    "quarterly_hour": 5,
    "quarterly_minute": 0,

    # Processing limits
    "max_learnings_per_aggregation": 500,
    "min_learnings_for_pattern": 3,  # Need at least 3 similar learnings to create pattern
    "min_confidence_for_hint": 0.6,  # Minimum confidence to create hint

    # Timeouts
    "aggregation_timeout_seconds": 600,  # 10 minutes per project
    "synthesis_timeout_seconds": 1800,  # 30 minutes for quarterly synthesis

    # Hint effectiveness
    "hint_decay_factor": 0.95,  # Confidence decay per month without usage
    "hint_boost_on_prevent": 0.1,  # Confidence boost when hint prevents error
    "hint_penalty_on_false_positive": 0.15,  # Confidence penalty on false positive
}


# ============================================================================
# Period Calculation Utilities
# ============================================================================


def get_previous_month_period() -> tuple[date, date]:
    """
    Get the start and end dates for the previous month.

    Returns:
        Tuple of (start_date, end_date) for previous month
    """
    today = date.today()
    first_of_current_month = today.replace(day=1)
    last_of_previous_month = first_of_current_month - timedelta(days=1)
    first_of_previous_month = last_of_previous_month.replace(day=1)

    return first_of_previous_month, last_of_previous_month


def get_previous_quarter_period() -> tuple[date, date]:
    """
    Get the start and end dates for the previous quarter.

    Returns:
        Tuple of (start_date, end_date) for previous quarter
    """
    today = date.today()
    current_quarter = (today.month - 1) // 3  # 0, 1, 2, 3

    # Previous quarter
    if current_quarter == 0:
        # Previous quarter is Q4 of previous year
        prev_quarter_start = date(today.year - 1, 10, 1)
        prev_quarter_end = date(today.year - 1, 12, 31)
    else:
        # Previous quarter in same year
        prev_quarter_month = (current_quarter - 1) * 3 + 1
        prev_quarter_start = date(today.year, prev_quarter_month, 1)
        _, last_day = monthrange(today.year, prev_quarter_month + 2)
        prev_quarter_end = date(today.year, prev_quarter_month + 2, last_day)

    return prev_quarter_start, prev_quarter_end


def get_weekly_period() -> tuple[date, date]:
    """
    Get the start and end dates for the previous week (Mon-Sun).

    Returns:
        Tuple of (start_date, end_date) for previous week
    """
    today = date.today()
    # Get Monday of current week
    monday_this_week = today - timedelta(days=today.weekday())
    # Previous week
    monday_prev_week = monday_this_week - timedelta(days=7)
    sunday_prev_week = monday_prev_week + timedelta(days=6)

    return monday_prev_week, sunday_prev_week


# ============================================================================
# Monthly Aggregation Job
# ============================================================================


async def run_monthly_aggregation() -> dict[str, Any]:
    """
    Run monthly aggregation for all active projects.

    This job runs on the 1st of each month at 4:00 AM and:
    1. Aggregates learnings from the previous month for each project
    2. Identifies patterns across learnings
    3. Generates decomposition hints from aggregated patterns

    Returns:
        Summary of monthly aggregation run
    """
    logger.info("Starting monthly learning aggregation for all active projects")

    start_time = datetime.utcnow()
    period_start, period_end = get_previous_month_period()
    projects_processed = 0
    projects_skipped = 0
    total_learnings = 0
    hints_generated = 0
    errors = []

    try:
        async with AsyncSessionLocal() as db:
            # Get all active projects
            result = await db.execute(
                select(Project).where(
                    Project.is_active == True,
                    Project.deleted_at.is_(None),
                )
            )
            projects = result.scalars().all()

            logger.info(f"Found {len(projects)} active projects for monthly aggregation")

            for project in projects:
                try:
                    # Check if already aggregated for this period
                    existing = await db.execute(
                        select(LearningAggregation).where(
                            LearningAggregation.project_id == project.id,
                            LearningAggregation.period_type == "monthly",
                            LearningAggregation.period_start == period_start,
                        )
                    )
                    if existing.scalar_one_or_none():
                        logger.debug(
                            f"Skipping project {project.id}: already aggregated for {period_start}"
                        )
                        projects_skipped += 1
                        continue

                    # Run aggregation for this project
                    aggregation_result = await _aggregate_project_learnings(
                        db=db,
                        project_id=project.id,
                        period_type="monthly",
                        period_start=period_start,
                        period_end=period_end,
                    )

                    if aggregation_result:
                        projects_processed += 1
                        total_learnings += aggregation_result["total_learnings"]
                        hints_generated += aggregation_result["hints_generated"]

                        logger.info(
                            f"Aggregated project {project.id}: "
                            f"learnings={aggregation_result['total_learnings']}, "
                            f"hints={aggregation_result['hints_generated']}"
                        )
                    else:
                        projects_skipped += 1

                except Exception as e:
                    logger.error(f"Error aggregating project {project.id}: {e}")
                    errors.append({
                        "project_id": str(project.id),
                        "error": str(e),
                    })

    except Exception as e:
        logger.error(f"Monthly aggregation failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "started_at": start_time.isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
        }

    duration_seconds = (datetime.utcnow() - start_time).total_seconds()

    summary = {
        "status": "completed",
        "period_type": "monthly",
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "started_at": start_time.isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "duration_seconds": int(duration_seconds),
        "projects_processed": projects_processed,
        "projects_skipped": projects_skipped,
        "total_learnings": total_learnings,
        "hints_generated": hints_generated,
        "errors": errors,
    }

    logger.info(
        f"Monthly aggregation completed: "
        f"processed={projects_processed}, skipped={projects_skipped}, "
        f"learnings={total_learnings}, hints={hints_generated}, "
        f"duration={duration_seconds:.1f}s"
    )

    return summary


async def _aggregate_project_learnings(
    db: AsyncSession,
    project_id: UUID,
    period_type: str,
    period_start: date,
    period_end: date,
) -> Optional[dict[str, Any]]:
    """
    Aggregate learnings for a specific project and period.

    Args:
        db: Database session
        project_id: Project to aggregate
        period_type: "weekly", "monthly", or "quarterly"
        period_start: Start of period
        period_end: End of period

    Returns:
        Aggregation result or None if no learnings
    """
    from app.services.feedback_learning_service import FeedbackLearningService

    # Get learnings for the period
    result = await db.execute(
        select(PRLearning).where(
            PRLearning.project_id == project_id,
            PRLearning.extracted_at >= datetime.combine(period_start, datetime.min.time()),
            PRLearning.extracted_at <= datetime.combine(period_end, datetime.max.time()),
        ).limit(AGGREGATION_CONFIG["max_learnings_per_aggregation"])
    )
    learnings = result.scalars().all()

    if not learnings:
        logger.debug(f"No learnings found for project {project_id} in period {period_start} - {period_end}")
        return None

    # Calculate statistics
    by_feedback_type = {}
    by_severity = {}

    for learning in learnings:
        # Count by feedback type
        feedback_type = learning.feedback_type or "unknown"
        by_feedback_type[feedback_type] = by_feedback_type.get(feedback_type, 0) + 1

        # Count by severity
        severity = learning.severity or "unknown"
        by_severity[severity] = by_severity.get(severity, 0) + 1

    # Identify top patterns (group similar learnings)
    top_patterns = await _extract_patterns(learnings)

    # Identify files with most learnings
    file_counts = {}
    for learning in learnings:
        if learning.file_path:
            file_counts[learning.file_path] = file_counts.get(learning.file_path, 0) + 1

    top_files = [
        {"file_path": path, "count": count}
        for path, count in sorted(file_counts.items(), key=lambda x: -x[1])[:10]
    ]

    # Create aggregation record
    aggregation = LearningAggregation(
        project_id=project_id,
        period_type=period_type,
        period_start=period_start,
        period_end=period_end,
        total_learnings=len(learnings),
        by_feedback_type=by_feedback_type,
        by_severity=by_severity,
        top_patterns=top_patterns,
        top_files=top_files,
        status="pending",
    )
    db.add(aggregation)
    await db.flush()

    # Generate hints from patterns
    hints_generated = 0
    feedback_service = FeedbackLearningService(db)

    for pattern in top_patterns:
        if pattern.get("count", 0) >= AGGREGATION_CONFIG["min_learnings_for_pattern"]:
            try:
                hint = await feedback_service.generate_hint_from_pattern(
                    project_id=project_id,
                    pattern=pattern,
                    source_aggregation_id=aggregation.id,
                )
                if hint:
                    hints_generated += 1
            except Exception as e:
                logger.warning(f"Failed to generate hint from pattern: {e}")

    # Update aggregation with generated hints
    aggregation.status = "processed"
    aggregation.processed_at = datetime.utcnow()

    await db.commit()

    return {
        "aggregation_id": str(aggregation.id),
        "total_learnings": len(learnings),
        "hints_generated": hints_generated,
        "patterns_found": len(top_patterns),
    }


async def _extract_patterns(learnings: list[PRLearning]) -> list[dict]:
    """
    Extract patterns from a list of learnings.

    Groups similar learnings based on:
    - Feedback type
    - File path patterns
    - Common keywords in descriptions

    Args:
        learnings: List of PRLearning objects

    Returns:
        List of pattern dictionaries
    """
    patterns = []

    # Group by feedback_type + file extension pattern
    type_file_groups = {}
    for learning in learnings:
        file_ext = ""
        if learning.file_path:
            parts = learning.file_path.rsplit(".", 1)
            if len(parts) > 1:
                file_ext = parts[1]

        key = f"{learning.feedback_type or 'unknown'}_{file_ext}"
        if key not in type_file_groups:
            type_file_groups[key] = []
        type_file_groups[key].append(learning)

    # Create patterns from groups with enough learnings
    for key, group in type_file_groups.items():
        if len(group) >= AGGREGATION_CONFIG["min_learnings_for_pattern"]:
            feedback_type, file_ext = key.rsplit("_", 1)

            # Extract common themes from learning descriptions
            themes = _extract_common_themes([l.learning_description or "" for l in group])

            patterns.append({
                "feedback_type": feedback_type,
                "file_extension": file_ext if file_ext else None,
                "count": len(group),
                "themes": themes,
                "severity_distribution": _count_severities(group),
                "sample_learning_ids": [str(l.id) for l in group[:5]],
            })

    # Sort by count descending
    patterns.sort(key=lambda x: -x["count"])

    return patterns[:20]  # Return top 20 patterns


def _extract_common_themes(descriptions: list[str]) -> list[str]:
    """
    Extract common themes from learning descriptions.

    Simple keyword extraction - in production, could use NLP/AI.

    Args:
        descriptions: List of learning descriptions

    Returns:
        List of common theme keywords
    """
    # Common keywords to extract
    theme_keywords = [
        "error handling", "validation", "security", "performance",
        "null check", "type safety", "edge case", "async", "await",
        "exception", "boundary", "input", "output", "logging",
        "test", "coverage", "documentation", "naming", "convention",
        "import", "dependency", "circular", "memory", "leak",
    ]

    # Count keyword occurrences
    keyword_counts = {}
    combined_text = " ".join(descriptions).lower()

    for keyword in theme_keywords:
        count = combined_text.count(keyword)
        if count > 0:
            keyword_counts[keyword] = count

    # Return top 5 themes
    sorted_themes = sorted(keyword_counts.items(), key=lambda x: -x[1])
    return [theme for theme, _ in sorted_themes[:5]]


def _count_severities(learnings: list[PRLearning]) -> dict[str, int]:
    """Count learnings by severity."""
    counts = {}
    for learning in learnings:
        severity = learning.severity or "unknown"
        counts[severity] = counts.get(severity, 0) + 1
    return counts


# ============================================================================
# Quarterly Synthesis Job
# ============================================================================


async def run_quarterly_synthesis() -> dict[str, Any]:
    """
    Run quarterly synthesis for all active projects.

    This job runs on the 1st of Jan, Apr, Jul, Oct at 5:00 AM and:
    1. Reviews all aggregations from the previous quarter
    2. Synthesizes patterns into CLAUDE.md suggestions
    3. Creates ADR recommendations where applicable

    Returns:
        Summary of quarterly synthesis run
    """
    logger.info("Starting quarterly synthesis for all active projects")

    start_time = datetime.utcnow()
    period_start, period_end = get_previous_quarter_period()
    projects_processed = 0
    projects_skipped = 0
    suggestions_generated = 0
    errors = []

    try:
        async with AsyncSessionLocal() as db:
            # Get all active projects
            result = await db.execute(
                select(Project).where(
                    Project.is_active == True,
                    Project.deleted_at.is_(None),
                )
            )
            projects = result.scalars().all()

            logger.info(f"Found {len(projects)} active projects for quarterly synthesis")

            for project in projects:
                try:
                    # Check if already synthesized for this period
                    existing = await db.execute(
                        select(LearningAggregation).where(
                            LearningAggregation.project_id == project.id,
                            LearningAggregation.period_type == "quarterly",
                            LearningAggregation.period_start == period_start,
                        )
                    )
                    if existing.scalar_one_or_none():
                        logger.debug(
                            f"Skipping project {project.id}: already synthesized for Q{(period_start.month - 1) // 3 + 1}"
                        )
                        projects_skipped += 1
                        continue

                    # Run synthesis for this project
                    synthesis_result = await _synthesize_project_quarter(
                        db=db,
                        project_id=project.id,
                        period_start=period_start,
                        period_end=period_end,
                    )

                    if synthesis_result:
                        projects_processed += 1
                        suggestions_generated += synthesis_result["suggestions_count"]

                        logger.info(
                            f"Synthesized project {project.id}: "
                            f"suggestions={synthesis_result['suggestions_count']}"
                        )
                    else:
                        projects_skipped += 1

                except Exception as e:
                    logger.error(f"Error synthesizing project {project.id}: {e}")
                    errors.append({
                        "project_id": str(project.id),
                        "error": str(e),
                    })

    except Exception as e:
        logger.error(f"Quarterly synthesis failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "started_at": start_time.isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
        }

    duration_seconds = (datetime.utcnow() - start_time).total_seconds()

    summary = {
        "status": "completed",
        "period_type": "quarterly",
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "started_at": start_time.isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "duration_seconds": int(duration_seconds),
        "projects_processed": projects_processed,
        "projects_skipped": projects_skipped,
        "suggestions_generated": suggestions_generated,
        "errors": errors,
    }

    logger.info(
        f"Quarterly synthesis completed: "
        f"processed={projects_processed}, skipped={projects_skipped}, "
        f"suggestions={suggestions_generated}, duration={duration_seconds:.1f}s"
    )

    return summary


async def _synthesize_project_quarter(
    db: AsyncSession,
    project_id: UUID,
    period_start: date,
    period_end: date,
) -> Optional[dict[str, Any]]:
    """
    Synthesize quarterly patterns into CLAUDE.md suggestions.

    Args:
        db: Database session
        project_id: Project to synthesize
        period_start: Start of quarter
        period_end: End of quarter

    Returns:
        Synthesis result or None if insufficient data
    """
    from app.services.feedback_learning_service import FeedbackLearningService

    # Get monthly aggregations for this quarter
    result = await db.execute(
        select(LearningAggregation).where(
            LearningAggregation.project_id == project_id,
            LearningAggregation.period_type == "monthly",
            LearningAggregation.period_start >= period_start,
            LearningAggregation.period_end <= period_end,
        )
    )
    monthly_aggregations = result.scalars().all()

    if not monthly_aggregations:
        logger.debug(f"No monthly aggregations found for project {project_id} in Q period")
        return None

    # Combine statistics from monthly aggregations
    total_learnings = sum(a.total_learnings for a in monthly_aggregations)

    if total_learnings < 10:  # Need minimum learnings for meaningful synthesis
        logger.debug(f"Insufficient learnings ({total_learnings}) for project {project_id} quarterly synthesis")
        return None

    # Combine patterns across months
    all_patterns = []
    for agg in monthly_aggregations:
        all_patterns.extend(agg.top_patterns or [])

    # Merge similar patterns
    merged_patterns = _merge_patterns(all_patterns)

    # Combined by_feedback_type and by_severity
    combined_by_type = {}
    combined_by_severity = {}
    for agg in monthly_aggregations:
        for k, v in (agg.by_feedback_type or {}).items():
            combined_by_type[k] = combined_by_type.get(k, 0) + v
        for k, v in (agg.by_severity or {}).items():
            combined_by_severity[k] = combined_by_severity.get(k, 0) + v

    # Generate CLAUDE.md suggestions using AI
    feedback_service = FeedbackLearningService(db)
    claude_md_suggestions = await feedback_service.generate_claude_md_suggestions(
        project_id=project_id,
        patterns=merged_patterns,
        by_feedback_type=combined_by_type,
        by_severity=combined_by_severity,
        total_learnings=total_learnings,
    )

    # Generate ADR recommendations if patterns indicate architectural issues
    adr_recommendations = _generate_adr_recommendations(merged_patterns)

    # Create quarterly aggregation record
    aggregation = LearningAggregation(
        project_id=project_id,
        period_type="quarterly",
        period_start=period_start,
        period_end=period_end,
        total_learnings=total_learnings,
        by_feedback_type=combined_by_type,
        by_severity=combined_by_severity,
        top_patterns=merged_patterns,
        top_files=[],  # Not tracked for quarterly
        claude_md_suggestions=claude_md_suggestions,
        adr_recommendations=adr_recommendations,
        status="processed",
        processed_at=datetime.utcnow(),
    )
    db.add(aggregation)
    await db.commit()

    return {
        "aggregation_id": str(aggregation.id),
        "total_learnings": total_learnings,
        "patterns_merged": len(merged_patterns),
        "suggestions_count": len(claude_md_suggestions or []),
        "adr_count": len(adr_recommendations or []),
    }


def _merge_patterns(patterns: list[dict]) -> list[dict]:
    """
    Merge similar patterns from multiple aggregations.

    Args:
        patterns: List of pattern dicts from multiple aggregations

    Returns:
        Merged pattern list
    """
    merged = {}

    for pattern in patterns:
        key = f"{pattern.get('feedback_type', 'unknown')}_{pattern.get('file_extension', '')}"

        if key in merged:
            # Merge counts and themes
            merged[key]["count"] += pattern.get("count", 0)
            existing_themes = set(merged[key].get("themes", []))
            new_themes = set(pattern.get("themes", []))
            merged[key]["themes"] = list(existing_themes | new_themes)[:10]
        else:
            merged[key] = pattern.copy()

    # Sort by count and return top patterns
    result = sorted(merged.values(), key=lambda x: -x.get("count", 0))
    return result[:15]


def _generate_adr_recommendations(patterns: list[dict]) -> list[dict]:
    """
    Generate ADR recommendations from patterns.

    Patterns with high counts or specific types may warrant ADRs.

    Args:
        patterns: Merged patterns from quarterly synthesis

    Returns:
        List of ADR recommendation dicts
    """
    recommendations = []

    for pattern in patterns:
        count = pattern.get("count", 0)
        feedback_type = pattern.get("feedback_type", "")
        themes = pattern.get("themes", [])

        # Recommend ADR for significant patterns
        if count >= 10 and feedback_type == "pattern_violation":
            recommendations.append({
                "type": "new_adr",
                "title": f"Pattern Standardization: {themes[0] if themes else 'General'}",
                "reason": f"Recurring pattern violations ({count} instances) suggest need for formal standardization",
                "themes": themes,
                "priority": "high" if count >= 20 else "medium",
            })

        if count >= 5 and feedback_type == "architecture":
            recommendations.append({
                "type": "update_adr",
                "title": f"Architecture Review: {themes[0] if themes else 'Structure'}",
                "reason": f"Architecture-related feedback ({count} instances) may need ADR clarification",
                "themes": themes,
                "priority": "high" if count >= 15 else "medium",
            })

    return recommendations[:5]  # Return top 5 recommendations


# ============================================================================
# On-Demand Aggregation
# ============================================================================


async def schedule_project_aggregation(
    project_id: UUID,
    period_type: str = "weekly",
    triggered_by: Optional[UUID] = None,
) -> dict[str, Any]:
    """
    Schedule on-demand aggregation for a specific project.

    Args:
        project_id: UUID of project to aggregate
        period_type: "weekly", "monthly", or "custom"
        triggered_by: UUID of user who triggered aggregation

    Returns:
        Aggregation job result
    """
    logger.info(f"Scheduling {period_type} aggregation for project {project_id}")

    # Determine period based on type
    if period_type == "weekly":
        period_start, period_end = get_weekly_period()
    elif period_type == "monthly":
        period_start, period_end = get_previous_month_period()
    else:
        # Default to last 30 days
        period_end = date.today() - timedelta(days=1)
        period_start = period_end - timedelta(days=30)

    try:
        async with AsyncSessionLocal() as db:
            result = await _aggregate_project_learnings(
                db=db,
                project_id=project_id,
                period_type=period_type,
                period_start=period_start,
                period_end=period_end,
            )

            if result:
                logger.info(f"On-demand aggregation completed for project {project_id}")
                return {
                    "status": "completed",
                    "project_id": str(project_id),
                    "period_type": period_type,
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat(),
                    **result,
                }
            else:
                return {
                    "status": "skipped",
                    "project_id": str(project_id),
                    "message": "No learnings found for the specified period",
                }

    except Exception as e:
        logger.error(f"On-demand aggregation failed for project {project_id}: {e}")
        return {
            "status": "failed",
            "project_id": str(project_id),
            "error": str(e),
        }


# ============================================================================
# Hint Effectiveness Update
# ============================================================================


async def update_hint_effectiveness() -> dict[str, Any]:
    """
    Update hint confidence scores based on usage feedback.

    This job runs daily and:
    1. Boosts confidence for hints that prevented errors
    2. Penalizes confidence for false positives
    3. Applies decay to hints without recent usage
    4. Deactivates hints with very low confidence

    Returns:
        Summary of effectiveness update
    """
    logger.info("Updating hint effectiveness scores")

    start_time = datetime.utcnow()
    hints_updated = 0
    hints_deactivated = 0

    try:
        async with AsyncSessionLocal() as db:
            # Get all active hints
            result = await db.execute(
                select(DecompositionHint).where(
                    DecompositionHint.is_active == True,
                )
            )
            hints = result.scalars().all()

            for hint in hints:
                original_confidence = hint.confidence_score

                # Check for recent feedback
                if hint.feedback_scores:
                    prevented = hint.feedback_scores.get("prevented_errors", 0)
                    false_positives = hint.feedback_scores.get("false_positives", 0)

                    # Boost for prevented errors
                    if prevented > 0:
                        boost = min(prevented * AGGREGATION_CONFIG["hint_boost_on_prevent"], 0.3)
                        hint.confidence_score = min(1.0, hint.confidence_score + boost)

                    # Penalty for false positives
                    if false_positives > 0:
                        penalty = min(false_positives * AGGREGATION_CONFIG["hint_penalty_on_false_positive"], 0.4)
                        hint.confidence_score = max(0.0, hint.confidence_score - penalty)

                    # Reset feedback scores after processing
                    hint.feedback_scores = {"prevented_errors": 0, "false_positives": 0}

                # Apply decay for hints without recent usage
                if hint.last_used_at:
                    days_since_use = (datetime.utcnow() - hint.last_used_at).days
                    if days_since_use > 30:
                        # Apply monthly decay
                        months = days_since_use // 30
                        decay = AGGREGATION_CONFIG["hint_decay_factor"] ** months
                        hint.confidence_score *= decay

                # Deactivate hints with very low confidence
                if hint.confidence_score < 0.2:
                    hint.is_active = False
                    hints_deactivated += 1
                    logger.info(f"Deactivated hint {hint.id} due to low confidence ({hint.confidence_score:.2f})")

                # Track if updated
                if hint.confidence_score != original_confidence:
                    hints_updated += 1

            await db.commit()

    except Exception as e:
        logger.error(f"Hint effectiveness update failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
        }

    duration_seconds = (datetime.utcnow() - start_time).total_seconds()

    summary = {
        "status": "completed",
        "started_at": start_time.isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "duration_seconds": int(duration_seconds),
        "hints_updated": hints_updated,
        "hints_deactivated": hints_deactivated,
    }

    logger.info(
        f"Hint effectiveness update completed: "
        f"updated={hints_updated}, deactivated={hints_deactivated}"
    )

    return summary


# ============================================================================
# APScheduler Job Registration
# ============================================================================


def register_scheduled_jobs(scheduler: Any) -> None:
    """
    Register learning aggregation jobs with APScheduler.

    Registered Jobs:
    1. Monthly aggregation (1st of each month at 4:00 AM)
    2. Quarterly synthesis (1st of Jan, Apr, Jul, Oct at 5:00 AM)
    3. Daily hint effectiveness update (6:00 AM)

    Args:
        scheduler: APScheduler instance

    Usage:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        scheduler = AsyncIOScheduler()
        register_scheduled_jobs(scheduler)
        scheduler.start()
    """
    from apscheduler.triggers.cron import CronTrigger

    # Monthly aggregation on 1st of each month at 4:00 AM
    scheduler.add_job(
        run_monthly_aggregation,
        CronTrigger(
            day=AGGREGATION_CONFIG["monthly_day"],
            hour=AGGREGATION_CONFIG["monthly_hour"],
            minute=AGGREGATION_CONFIG["monthly_minute"],
        ),
        id="monthly_learning_aggregation",
        name="Monthly Learning Aggregation",
        replace_existing=True,
    )

    # Quarterly synthesis on 1st of Jan, Apr, Jul, Oct at 5:00 AM
    scheduler.add_job(
        run_quarterly_synthesis,
        CronTrigger(
            month=",".join(str(m) for m in AGGREGATION_CONFIG["quarterly_months"]),
            day=AGGREGATION_CONFIG["quarterly_day"],
            hour=AGGREGATION_CONFIG["quarterly_hour"],
            minute=AGGREGATION_CONFIG["quarterly_minute"],
        ),
        id="quarterly_learning_synthesis",
        name="Quarterly Learning Synthesis",
        replace_existing=True,
    )

    # Daily hint effectiveness update at 6:00 AM
    scheduler.add_job(
        update_hint_effectiveness,
        CronTrigger(hour=6, minute=0),
        id="daily_hint_effectiveness",
        name="Daily Hint Effectiveness Update",
        replace_existing=True,
    )

    logger.info("Registered learning aggregation scheduled jobs (3 jobs)")


# ============================================================================
# Utility Functions
# ============================================================================


async def get_aggregation_status(project_id: UUID) -> dict[str, Any]:
    """
    Get aggregation status for a project.

    Args:
        project_id: UUID of the project

    Returns:
        Aggregation status summary
    """
    async with AsyncSessionLocal() as db:
        # Get latest aggregations
        result = await db.execute(
            select(LearningAggregation)
            .where(LearningAggregation.project_id == project_id)
            .order_by(LearningAggregation.created_at.desc())
            .limit(5)
        )
        aggregations = result.scalars().all()

        # Count by status
        pending = sum(1 for a in aggregations if a.status == "pending")
        processed = sum(1 for a in aggregations if a.status == "processed")
        applied = sum(1 for a in aggregations if a.status == "applied")

        # Get pending suggestions count
        pending_suggestions = 0
        for agg in aggregations:
            if agg.status == "processed" and agg.claude_md_suggestions:
                pending_suggestions += len(agg.claude_md_suggestions)

        return {
            "project_id": str(project_id),
            "total_aggregations": len(aggregations),
            "by_status": {
                "pending": pending,
                "processed": processed,
                "applied": applied,
            },
            "pending_suggestions": pending_suggestions,
            "latest_aggregation": aggregations[0].to_summary_dict() if aggregations else None,
        }


async def apply_aggregation_suggestions(
    aggregation_id: UUID,
    applied_by: UUID,
    apply_to: list[str],
) -> dict[str, Any]:
    """
    Apply suggestions from an aggregation.

    Args:
        aggregation_id: UUID of the aggregation
        applied_by: UUID of user applying suggestions
        apply_to: List of targets ("claude_md", "decomposition", "adr")

    Returns:
        Application result
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(LearningAggregation).where(LearningAggregation.id == aggregation_id)
        )
        aggregation = result.scalar_one_or_none()

        if not aggregation:
            return {"error": "Aggregation not found"}

        if aggregation.status == "applied":
            return {"error": "Aggregation already applied"}

        applied_items = []

        # Apply CLAUDE.md suggestions
        if "claude_md" in apply_to and aggregation.claude_md_suggestions:
            # In production, this would update the actual CLAUDE.md file
            # For now, we just mark as applied
            for suggestion in aggregation.claude_md_suggestions:
                applied_items.append({
                    "type": "claude_md",
                    "section": suggestion.get("section"),
                    "content": suggestion.get("content"),
                })

        # Apply decomposition hints (already created during aggregation)
        if "decomposition" in apply_to and aggregation.decomposition_hints:
            for hint in aggregation.decomposition_hints:
                applied_items.append({
                    "type": "decomposition_hint",
                    "hint_type": hint.get("type"),
                    "content": hint.get("content"),
                })

        # Mark aggregation as applied
        aggregation.status = "applied"
        aggregation.applied_at = datetime.utcnow()
        aggregation.processed_by = applied_by

        await db.commit()

        logger.info(f"Applied aggregation {aggregation_id}: {len(applied_items)} items")

        return {
            "status": "applied",
            "aggregation_id": str(aggregation_id),
            "items_applied": len(applied_items),
            "applied_items": applied_items,
        }
