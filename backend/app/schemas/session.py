"""
=========================================================================
Session Checkpoint Schemas - Sprint 51B
SDLC Orchestrator - Progressive Code Generation

Version: 1.0.0
Date: December 26, 2025
Status: ACTIVE - Sprint 51B Implementation
Authority: Backend Team + CTO Approved
Foundation: Session-Checkpoint-Design.md

Purpose:
- Session state management for code generation
- Checkpoint data for recovery after failures
- Error context for retry decisions
- Redis storage serialization

References:
- docs/02-design/14-Technical-Specs/Session-Checkpoint-Design.md
- docs/02-design/15-Pattern-Adoption/Vibecode-Pattern-Adoption-Plan.md
=========================================================================
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """Session lifecycle states for code generation."""
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    CHECKPOINTED = "checkpointed"
    COMPLETED = "completed"
    FAILED = "failed"
    RESUMED = "resumed"


class GeneratedFileCheckpoint(BaseModel):
    """Checkpoint data for a generated file."""
    file_path: str
    content: str
    language: str
    lines: int
    generated_at: datetime
    checksum: str  # SHA256 for integrity

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorContext(BaseModel):
    """Error context for retry decisions."""
    error_type: str
    error_message: str
    file_path: Optional[str] = None
    retry_count: int = 0
    recoverable: bool = True
    context: Dict[str, Any] = Field(default_factory=dict)


class SessionState(BaseModel):
    """Main session state stored in Redis."""
    session_id: UUID
    project_id: UUID
    user_id: UUID
    status: SessionStatus

    # Blueprint reference
    blueprint_hash: str  # SHA256 of AppBlueprint
    blueprint_version: str

    # Progress tracking
    total_files_expected: int
    files_completed: int
    current_file: Optional[str] = None

    # Checkpoint data
    checkpoint_count: int = 0
    last_checkpoint_at: Optional[datetime] = None

    # Timing
    created_at: datetime
    updated_at: datetime
    expires_at: datetime  # TTL tracking

    # Error tracking
    errors: List[ErrorContext] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class SessionMetadata(BaseModel):
    """Additional session metadata."""
    provider: str  # ollama, claude, deepcode
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    generation_time_ms: int = 0
    resume_count: int = 0


# Request/Response Models

class SessionStateResponse(BaseModel):
    """API response for session state."""
    session_id: str
    project_id: str
    status: SessionStatus
    files_completed: int
    total_files_expected: int
    checkpoint_count: int
    last_checkpoint_at: Optional[datetime] = None
    errors: List[ErrorContext] = Field(default_factory=list)
    can_resume: bool = False
    created_at: datetime
    expires_at: datetime

    @classmethod
    def from_state(cls, state: SessionState) -> "SessionStateResponse":
        """Create response from SessionState."""
        can_resume = state.status in [
            SessionStatus.CHECKPOINTED,
            SessionStatus.IN_PROGRESS
        ] or (
            state.status == SessionStatus.FAILED
            and state.errors
            and state.errors[-1].recoverable
        )

        return cls(
            session_id=str(state.session_id),
            project_id=str(state.project_id),
            status=state.status,
            files_completed=state.files_completed,
            total_files_expected=state.total_files_expected,
            checkpoint_count=state.checkpoint_count,
            last_checkpoint_at=state.last_checkpoint_at,
            errors=state.errors,
            can_resume=can_resume,
            created_at=state.created_at,
            expires_at=state.expires_at
        )
