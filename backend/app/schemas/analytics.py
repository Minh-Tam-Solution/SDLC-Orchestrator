"""
Analytics Pydantic Schemas

SDLC Stage: 04 - BUILD
Sprint: 41 - AI Safety Foundation
Epic: EP-01/EP-02
Status: IMPLEMENTED
Framework: SDLC 5.1.1

Purpose:
Request/response schemas for analytics API endpoints.
Validates event properties, enforces constraints, provides examples.

API Endpoints:
- POST /api/v1/analytics/events - Track single event
- POST /api/v1/analytics/events/batch - Track multiple events
- GET /api/v1/analytics/metrics/dau - Get Daily Active Users
- GET /api/v1/analytics/metrics/ai-safety - Get AI Safety metrics
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator


class EventType(str, Enum):
    """Standard event types for product analytics."""

    # User lifecycle
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_SIGNUP = "user_signup"

    # Project lifecycle
    PROJECT_CREATED = "project_created"
    PROJECT_DELETED = "project_deleted"
    PROJECT_SETTINGS_UPDATED = "project_settings_updated"

    # Gate lifecycle
    GATE_EVALUATED = "gate_evaluated"
    GATE_PASSED = "gate_passed"
    GATE_FAILED = "gate_failed"
    GATE_OVERRIDDEN = "gate_overridden"

    # Evidence
    EVIDENCE_UPLOADED = "evidence_uploaded"
    EVIDENCE_DELETED = "evidence_deleted"
    EVIDENCE_REVIEWED = "evidence_reviewed"

    # AI Safety
    AI_SAFETY_VALIDATION = "ai_safety_validation"
    AI_CODE_DETECTED = "ai_code_detected"
    AI_PR_REVIEWED = "ai_pr_reviewed"

    # Design Partner (EP-03)
    WORKSHOP_ATTENDED = "workshop_attended"
    FEEDBACK_SUBMITTED = "feedback_submitted"
    NPS_SURVEY_COMPLETED = "nps_survey_completed"


class EventCreate(BaseModel):
    """
    Create analytics event request.

    Example:
        {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "event_name": "gate_passed",
            "properties": {
                "gate_id": "G2",
                "project_id": "proj_123",
                "duration_ms": 1250
            }
        }
    """

    user_id: UUID = Field(..., description="User UUID")
    event_name: str = Field(..., min_length=1, max_length=100, description="Event name")
    properties: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Event metadata (max 100 keys, 100KB total)"
    )

    @validator("properties")
    def validate_properties_size(cls, v):
        """Validate properties size (max 100 keys, 100KB)."""
        if v and len(v) > 100:
            raise ValueError("Event properties cannot exceed 100 keys")

        # Rough size check (JSON serialization would be more accurate)
        if v and len(str(v)) > 102400:  # 100KB
            raise ValueError("Event properties cannot exceed 100KB")

        return v

    class Config:
        schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "event_name": "gate_passed",
                "properties": {
                    "gate_id": "G2",
                    "project_id": "proj_123",
                    "evidence_count": 5,
                    "duration_ms": 1250
                }
            }
        }


class EventResponse(BaseModel):
    """Event tracking response."""

    success: bool = Field(..., description="Whether event was tracked successfully")
    event_id: Optional[UUID] = Field(None, description="Event ID (if stored locally)")
    message: Optional[str] = Field(None, description="Error message (if failed)")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "event_id": "660e8400-e29b-41d4-a716-446655440000",
                "message": None
            }
        }


class AISafetyEventProperties(BaseModel):
    """
    AI Safety Layer event properties.

    Tracked when AI-generated code is validated against SDLC policies.
    """

    pr_id: str = Field(..., description="Pull request ID")
    ai_tool: str = Field(..., description="AI tool detected (claude, cursor, copilot)")
    result: str = Field(..., description="Validation result (passed, failed, warning)")
    duration_ms: int = Field(..., ge=0, description="Validation duration in milliseconds")
    violations_found: int = Field(default=0, ge=0, description="Number of violations found")
    validated_at: str = Field(..., description="ISO 8601 timestamp")

    class Config:
        schema_extra = {
            "example": {
                "pr_id": "PR-1234",
                "ai_tool": "claude-code",
                "result": "failed",
                "duration_ms": 1250,
                "violations_found": 3,
                "validated_at": "2026-01-06T10:30:00Z"
            }
        }


class GateEventProperties(BaseModel):
    """
    SDLC gate evaluation event properties.

    Tracked when a gate is evaluated (passed, failed, pending).
    """

    project_id: str = Field(..., description="Project UUID")
    gate_id: str = Field(..., description="Gate identifier (G0, G1, G2, G3)")
    status: str = Field(..., description="Gate status (passed, failed, pending)")
    evidence_count: int = Field(default=0, ge=0, description="Number of evidence items")
    policy_violations: int = Field(default=0, ge=0, description="Number of policy violations")
    evaluated_at: str = Field(..., description="ISO 8601 timestamp")

    class Config:
        schema_extra = {
            "example": {
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "gate_id": "G2",
                "status": "passed",
                "evidence_count": 5,
                "policy_violations": 0,
                "evaluated_at": "2026-01-06T10:30:00Z"
            }
        }


class BatchEventCreate(BaseModel):
    """
    Batch event tracking request.

    Supports up to 100 events per batch for performance optimization.
    """

    events: List[EventCreate] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="List of events to track (max 100)"
    )

    class Config:
        schema_extra = {
            "example": {
                "events": [
                    {
                        "user_id": "550e8400-e29b-41d4-a716-446655440000",
                        "event_name": "gate_passed",
                        "properties": {"gate_id": "G2"}
                    },
                    {
                        "user_id": "550e8400-e29b-41d4-a716-446655440000",
                        "event_name": "evidence_uploaded",
                        "properties": {"file_size_kb": 1024}
                    }
                ]
            }
        }


class BatchEventResponse(BaseModel):
    """Batch event tracking response."""

    success_count: int = Field(..., description="Number of successfully tracked events")
    total_count: int = Field(..., description="Total number of events in batch")
    failed_events: List[int] = Field(
        default_factory=list,
        description="Indexes of failed events (0-based)"
    )

    class Config:
        schema_extra = {
            "example": {
                "success_count": 98,
                "total_count": 100,
                "failed_events": [12, 45]
            }
        }


class DAUMetrics(BaseModel):
    """
    Daily Active Users metrics.

    Aggregated by date for the last N days.
    """

    start_date: str = Field(..., description="Start date (ISO 8601)")
    end_date: str = Field(..., description="End date (ISO 8601)")
    daily_counts: Dict[str, int] = Field(..., description="Date -> DAU count mapping")
    total_unique_users: int = Field(..., description="Total unique users in period")
    avg_dau: float = Field(..., description="Average DAU across period")

    class Config:
        schema_extra = {
            "example": {
                "start_date": "2026-01-01",
                "end_date": "2026-01-30",
                "daily_counts": {
                    "2026-01-06": 45,
                    "2026-01-07": 52,
                    "2026-01-08": 48
                },
                "total_unique_users": 127,
                "avg_dau": 48.3
            }
        }


class AISafetyMetrics(BaseModel):
    """
    AI Safety Layer aggregate metrics.

    Provides pass rate, tool usage, and violation statistics.
    """

    period_days: int = Field(..., description="Number of days aggregated")
    total_validations: int = Field(..., description="Total PR validations")
    pass_rate: float = Field(..., ge=0.0, le=1.0, description="Percentage of validations passed")
    avg_duration_ms: float = Field(..., description="Average validation duration")
    top_tools: Dict[str, int] = Field(..., description="AI tools usage count (top 5)")
    violations_by_type: Dict[str, int] = Field(
        default_factory=dict,
        description="Violation counts by type"
    )

    class Config:
        schema_extra = {
            "example": {
                "period_days": 7,
                "total_validations": 1234,
                "pass_rate": 0.87,
                "avg_duration_ms": 945.2,
                "top_tools": {
                    "claude-code": 450,
                    "cursor": 380,
                    "copilot": 250,
                    "windsurf": 100,
                    "continue": 54
                },
                "violations_by_type": {
                    "naming_convention": 12,
                    "folder_structure": 8,
                    "missing_evidence": 5
                }
            }
        }
