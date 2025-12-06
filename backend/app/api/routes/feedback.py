"""
File: backend/app/api/routes/feedback.py
Version: 1.0.0
Status: ACTIVE - STAGE 03 (BUILD)
Date: 2025-12-03
Authority: Backend Lead + CTO Approved

Description:
API routes for pilot feedback collection system.

Sprint 24 Day 2: Pilot Onboarding Guide

Endpoints:
- POST /feedback - Submit new feedback
- GET /feedback - List all feedback (with filters)
- GET /feedback/{id} - Get feedback details
- PATCH /feedback/{id} - Update feedback (status, priority)
- POST /feedback/{id}/comments - Add comment
- GET /feedback/stats - Get feedback statistics
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.feedback import (
    FeedbackComment,
    FeedbackPriority,
    FeedbackStatus,
    FeedbackType,
    PilotFeedback,
)
from app.models.user import User
from app.schemas.feedback import (
    FeedbackCommentCreate,
    FeedbackCommentResponse,
    FeedbackCreate,
    FeedbackListResponse,
    FeedbackResponse,
    FeedbackStats,
    FeedbackUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    feedback_in: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeedbackResponse:
    """
    Submit new feedback.

    Anyone with an account can submit feedback about bugs,
    feature requests, or general improvements.
    """
    feedback = PilotFeedback(
        user_id=current_user.id,
        title=feedback_in.title,
        description=feedback_in.description,
        type=feedback_in.type,
        steps_to_reproduce=feedback_in.steps_to_reproduce,
        expected_behavior=feedback_in.expected_behavior,
        actual_behavior=feedback_in.actual_behavior,
        browser=feedback_in.browser,
        os=feedback_in.os,
        screenshot_url=feedback_in.screenshot_url,
        page_url=feedback_in.page_url,
        status=FeedbackStatus.NEW,
    )

    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)

    logger.info(f"Feedback submitted: {feedback.id} by user {current_user.id}")

    return FeedbackResponse.model_validate(feedback)


@router.get("", response_model=FeedbackListResponse)
async def list_feedback(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    type: Optional[FeedbackType] = Query(None, description="Filter by type"),
    status: Optional[FeedbackStatus] = Query(None, description="Filter by status"),
    priority: Optional[FeedbackPriority] = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> FeedbackListResponse:
    """
    List all feedback with optional filters.

    Supports filtering by type, status, and priority.
    Results are paginated.
    """
    query = select(PilotFeedback)

    # Apply filters
    if type:
        query = query.where(PilotFeedback.type == type)
    if status:
        query = query.where(PilotFeedback.status == status)
    if priority:
        query = query.where(PilotFeedback.priority == priority)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(PilotFeedback.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return FeedbackListResponse(
        items=[FeedbackResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/stats", response_model=FeedbackStats)
async def get_feedback_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeedbackStats:
    """
    Get feedback statistics.

    Returns counts by type, status, and priority,
    plus average resolution time.
    """
    # Total count
    total_result = await db.execute(select(func.count(PilotFeedback.id)))
    total = total_result.scalar() or 0

    # Count by type
    type_query = select(
        PilotFeedback.type,
        func.count(PilotFeedback.id)
    ).group_by(PilotFeedback.type)
    type_result = await db.execute(type_query)
    by_type = {str(row[0].value): row[1] for row in type_result.all()}

    # Count by status
    status_query = select(
        PilotFeedback.status,
        func.count(PilotFeedback.id)
    ).group_by(PilotFeedback.status)
    status_result = await db.execute(status_query)
    by_status = {str(row[0].value): row[1] for row in status_result.all()}

    # Count by priority
    priority_query = select(
        PilotFeedback.priority,
        func.count(PilotFeedback.id)
    ).where(PilotFeedback.priority.isnot(None)).group_by(PilotFeedback.priority)
    priority_result = await db.execute(priority_query)
    by_priority = {str(row[0].value): row[1] for row in priority_result.all()}

    # Average resolution time (for resolved items)
    # This would need PostgreSQL-specific date functions
    avg_resolution_time = None

    return FeedbackStats(
        total=total,
        by_type=by_type,
        by_status=by_status,
        by_priority=by_priority,
        avg_resolution_time_hours=avg_resolution_time,
    )


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeedbackResponse:
    """
    Get feedback details by ID.
    """
    result = await db.execute(
        select(PilotFeedback).where(PilotFeedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )

    return FeedbackResponse.model_validate(feedback)


@router.patch("/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
    feedback_id: UUID,
    feedback_in: FeedbackUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeedbackResponse:
    """
    Update feedback status, priority, or resolution.

    Only admins or the original submitter can update.
    """
    result = await db.execute(
        select(PilotFeedback).where(PilotFeedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )

    # Check permissions (owner or admin)
    if feedback.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this feedback",
        )

    # Update fields
    update_data = feedback_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(feedback, field, value)

    # Set resolution timestamp if status changed to resolved
    if feedback_in.status == FeedbackStatus.RESOLVED and not feedback.resolved_at:
        feedback.resolved_at = datetime.utcnow()
        feedback.resolved_by = current_user.id

    await db.commit()
    await db.refresh(feedback)

    logger.info(f"Feedback {feedback_id} updated by user {current_user.id}")

    return FeedbackResponse.model_validate(feedback)


@router.post("/{feedback_id}/comments", response_model=FeedbackCommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    feedback_id: UUID,
    comment_in: FeedbackCommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeedbackCommentResponse:
    """
    Add a comment to feedback.
    """
    # Check feedback exists
    result = await db.execute(
        select(PilotFeedback).where(PilotFeedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )

    comment = FeedbackComment(
        feedback_id=feedback_id,
        user_id=current_user.id,
        content=comment_in.content,
    )

    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    logger.info(f"Comment added to feedback {feedback_id} by user {current_user.id}")

    return FeedbackCommentResponse.model_validate(comment)


@router.get("/{feedback_id}/comments", response_model=list[FeedbackCommentResponse])
async def list_comments(
    feedback_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[FeedbackCommentResponse]:
    """
    List all comments for a feedback item.
    """
    # Check feedback exists
    result = await db.execute(
        select(PilotFeedback).where(PilotFeedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )

    comments_result = await db.execute(
        select(FeedbackComment)
        .where(FeedbackComment.feedback_id == feedback_id)
        .order_by(FeedbackComment.created_at.asc())
    )
    comments = comments_result.scalars().all()

    return [FeedbackCommentResponse.model_validate(c) for c in comments]
