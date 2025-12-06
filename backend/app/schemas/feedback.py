"""
File: backend/app/schemas/feedback.py
Version: 1.0.0
Status: ACTIVE - STAGE 03 (BUILD)
Date: 2025-12-03
Authority: Backend Lead + CTO Approved

Description:
Pydantic schemas for pilot feedback API.

Sprint 24 Day 2: Pilot Onboarding Guide
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.models.feedback import FeedbackType, FeedbackPriority, FeedbackStatus


class FeedbackBase(BaseModel):
    """Base schema for feedback."""
    title: str = Field(..., min_length=5, max_length=255, description="Short summary of the feedback")
    description: str = Field(..., min_length=10, description="Detailed description")
    type: FeedbackType = Field(default=FeedbackType.OTHER, description="Type of feedback")


class FeedbackCreate(FeedbackBase):
    """Schema for creating new feedback."""
    steps_to_reproduce: Optional[str] = Field(None, description="Steps to reproduce (for bugs)")
    expected_behavior: Optional[str] = Field(None, description="Expected behavior (for bugs)")
    actual_behavior: Optional[str] = Field(None, description="Actual behavior (for bugs)")
    browser: Optional[str] = Field(None, max_length=100, description="Browser information")
    os: Optional[str] = Field(None, max_length=100, description="Operating system")
    screenshot_url: Optional[str] = Field(None, max_length=512, description="Screenshot URL")
    page_url: Optional[str] = Field(None, max_length=512, description="Page URL where issue occurred")


class FeedbackUpdate(BaseModel):
    """Schema for updating feedback."""
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    type: Optional[FeedbackType] = None
    priority: Optional[FeedbackPriority] = None
    status: Optional[FeedbackStatus] = None
    resolution_notes: Optional[str] = None


class FeedbackResponse(FeedbackBase):
    """Schema for feedback response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: Optional[UUID] = None
    priority: Optional[FeedbackPriority] = None
    status: FeedbackStatus
    steps_to_reproduce: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    screenshot_url: Optional[str] = None
    page_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[UUID] = None
    resolution_notes: Optional[str] = None


class FeedbackListResponse(BaseModel):
    """Schema for paginated feedback list."""
    items: list[FeedbackResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class FeedbackCommentCreate(BaseModel):
    """Schema for creating feedback comment."""
    content: str = Field(..., min_length=1, description="Comment content")


class FeedbackCommentResponse(BaseModel):
    """Schema for feedback comment response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    feedback_id: UUID
    user_id: Optional[UUID] = None
    content: str
    created_at: datetime
    updated_at: datetime


class FeedbackStats(BaseModel):
    """Schema for feedback statistics."""
    total: int
    by_type: dict[str, int]
    by_status: dict[str, int]
    by_priority: dict[str, int]
    avg_resolution_time_hours: Optional[float] = None
