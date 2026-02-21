# Session Checkpoint & Resume - Technical Design

**Version**: 1.0.0
**Status**: Ready for Implementation
**Sprint**: 51B
**Priority**: HIGH
**Effort**: 2 days
**Author**: CTO
**Date**: December 25, 2025

---

## 1. Overview

### 1.1 Problem Statement

Long-running code generation (30-60s for 15-20 files) can fail mid-way due to:
- Network interruptions
- Provider timeouts
- Quality gate failures
- User browser disconnection

Currently, any failure requires regenerating ALL files from scratch.

### 1.2 Solution

Implement session checkpoints that:
- Save progress every N files (default: 3)
- Store state in Redis with 24h TTL
- Enable resume from last successful checkpoint
- Preserve error context for retry decisions

### 1.3 Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Resume rate after failure | 0% | 95%+ |
| Wasted regeneration | 100% | <10% |
| User frustration (NPS) | N/A | +15 points |

---

## 2. Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     CodeGenerationPage                           │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────────┐   │
│  │   Start     │   │   Resume    │   │   Checkpoint        │   │
│  │   Button    │   │   Button    │   │   Progress Bar      │   │
│  └──────┬──────┘   └──────┬──────┘   └──────────────────────┘   │
│         │                 │                                      │
└─────────┼─────────────────┼──────────────────────────────────────┘
          │                 │
          ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend API Layer                             │
│  ┌─────────────────────┐   ┌─────────────────────────────────┐  │
│  │ POST /generate      │   │ POST /generate/resume/{id}      │  │
│  │ (SSE streaming)     │   │ (Resume from checkpoint)        │  │
│  └──────────┬──────────┘   └──────────────┬──────────────────┘  │
│             │                              │                     │
└─────────────┼──────────────────────────────┼─────────────────────┘
              │                              │
              ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SessionManager                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ create_session  │  │ save_checkpoint │  │ resume_session  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Redis                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ checkpoint:{session_id}:state    → SessionState (JSON)     │ │
│  │ checkpoint:{session_id}:files    → List[GeneratedFile]     │ │
│  │ checkpoint:{session_id}:errors   → List[ErrorContext]      │ │
│  │ checkpoint:{session_id}:metadata → SessionMetadata         │ │
│  └────────────────────────────────────────────────────────────┘ │
│  TTL: 24 hours                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Sequence Diagram - New Generation

```
User          Frontend        API         SessionManager      Redis       Provider
  │               │            │               │                │            │
  │──Start Gen──▶│            │               │                │            │
  │               │──POST /generate──────────▶│               │            │
  │               │            │──create_session──────────────▶│            │
  │               │            │               │◀──session_id──│            │
  │               │            │               │                │            │
  │               │◀─────SSE: session_created─│               │            │
  │               │            │               │                │            │
  │               │            │──────────────generate_file────────────────▶│
  │               │◀─────SSE: file_generated──│               │            │
  │               │            │               │                │            │
  │               │            │──────────────generate_file────────────────▶│
  │               │◀─────SSE: file_generated──│               │            │
  │               │            │               │                │            │
  │               │            │ (every 3 files)               │            │
  │               │            │──save_checkpoint─────────────▶│            │
  │               │◀─────SSE: checkpoint_saved│               │            │
  │               │            │               │                │            │
  │               │            │   ... continue ...            │            │
  │               │            │               │                │            │
  │               │◀─────SSE: generation_complete──────────────│            │
```

### 2.3 Sequence Diagram - Resume

```
User          Frontend        API         SessionManager      Redis       Provider
  │               │            │               │                │            │
  │──Resume Gen─▶│            │               │                │            │
  │               │──POST /generate/resume/{id}───────────────▶│            │
  │               │            │               │──get_checkpoint──────────▶│
  │               │            │               │◀──SessionState + Files────│
  │               │            │               │                │            │
  │               │◀─────SSE: session_resumed (with completed files)───────│
  │               │            │               │                │            │
  │               │            │──────────────generate_remaining───────────▶│
  │               │◀─────SSE: file_generated──│               │            │
  │               │            │               │                │            │
  │               │            │   ... continue from checkpoint ...        │
  │               │            │               │                │            │
  │               │◀─────SSE: generation_complete──────────────│            │
```

---

## 3. Data Models

### 3.1 Session State (Redis)

```python
# backend/app/schemas/session.py

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


class SessionStatus(str, Enum):
    """Session lifecycle states"""
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    CHECKPOINTED = "checkpointed"
    COMPLETED = "completed"
    FAILED = "failed"
    RESUMED = "resumed"


class GeneratedFileCheckpoint(BaseModel):
    """Checkpoint data for a generated file"""
    file_path: str
    content: str
    language: str
    lines: int
    generated_at: datetime
    checksum: str  # SHA256 for integrity


class ErrorContext(BaseModel):
    """Error context for retry decisions"""
    error_type: str
    error_message: str
    file_path: Optional[str] = None
    retry_count: int = 0
    recoverable: bool = True
    context: Dict[str, Any] = Field(default_factory=dict)


class SessionState(BaseModel):
    """Main session state stored in Redis"""
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
    """Additional session metadata"""
    provider: str  # ollama, claude, deepcode
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    generation_time_ms: int = 0
    resume_count: int = 0
```

### 3.2 SSE Events

```python
# backend/app/schemas/streaming.py (additions)

class CheckpointEvent(BaseModel):
    """SSE event for checkpoint notifications"""
    type: Literal["checkpoint"] = "checkpoint"
    session_id: str
    checkpoint_number: int
    files_completed: int
    total_files: int
    last_file: str
    can_resume: bool = True
    checkpoint_at: datetime


class SessionCreatedEvent(BaseModel):
    """SSE event when session is created"""
    type: Literal["session_created"] = "session_created"
    session_id: str
    blueprint_hash: str
    total_files_expected: int
    expires_at: datetime


class SessionResumedEvent(BaseModel):
    """SSE event when session is resumed"""
    type: Literal["session_resumed"] = "session_resumed"
    session_id: str
    resumed_from_checkpoint: int
    files_already_completed: int
    files_remaining: int
    completed_files: List[GeneratedFileCheckpoint]
```

---

## 4. API Endpoints

### 4.1 Resume Endpoint

```python
# backend/app/api/routes/codegen.py (additions)

@router.post("/generate/resume/{session_id}")
async def resume_generation(
    session_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> StreamingResponse:
    """
    Resume code generation from last checkpoint.

    Args:
        session_id: UUID of the session to resume

    Returns:
        SSE stream with remaining file generation events

    Raises:
        404: Session not found or expired
        400: Session cannot be resumed (completed or invalid)
        403: User not authorized for this session
    """
    session_manager = SessionManager(redis)

    # Validate session exists and is resumable
    session_state = await session_manager.get_session(session_id)
    if not session_state:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found or expired"
        )

    # Check authorization
    if session_state.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to resume this session"
        )

    # Check if resumable
    if session_state.status == SessionStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Session already completed"
        )

    if session_state.status == SessionStatus.FAILED:
        # Allow resume of failed sessions
        if not session_state.errors or not session_state.errors[-1].recoverable:
            raise HTTPException(
                status_code=400,
                detail="Session failed with non-recoverable error"
            )

    # Get completed files
    completed_files = await session_manager.get_completed_files(session_id)

    # Create SSE generator
    async def generate_remaining():
        # Send session resumed event
        yield SessionResumedEvent(
            session_id=str(session_id),
            resumed_from_checkpoint=session_state.checkpoint_count,
            files_already_completed=len(completed_files),
            files_remaining=session_state.total_files_expected - len(completed_files),
            completed_files=completed_files
        ).model_dump_json()

        # Resume generation from where we left off
        async for event in codegen_service.resume_generation(
            session_id=session_id,
            completed_files=completed_files,
            session_state=session_state
        ):
            yield event.model_dump_json()

    return StreamingResponse(
        generate_remaining(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Session-Id": str(session_id)
        }
    )


@router.get("/sessions/{session_id}")
async def get_session_status(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis)
) -> SessionState:
    """
    Get current session status and checkpoint info.

    Returns:
        SessionState with current progress and checkpoint data
    """
    session_manager = SessionManager(redis)
    session_state = await session_manager.get_session(session_id)

    if not session_state:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found or expired"
        )

    if session_state.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this session"
        )

    return session_state


@router.get("/sessions/active")
async def list_active_sessions(
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis)
) -> List[SessionState]:
    """
    List all active (resumable) sessions for current user.
    """
    session_manager = SessionManager(redis)
    return await session_manager.list_user_sessions(
        user_id=current_user.id,
        status_filter=[
            SessionStatus.IN_PROGRESS,
            SessionStatus.CHECKPOINTED,
            SessionStatus.FAILED
        ]
    )
```

---

## 5. SessionManager Service

```python
# backend/app/services/codegen/session_manager.py

import hashlib
import json
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4

from redis.asyncio import Redis
from pydantic import BaseModel

from app.schemas.session import (
    SessionState,
    SessionStatus,
    GeneratedFileCheckpoint,
    ErrorContext,
    SessionMetadata
)
from app.core.config import settings


class SessionManager:
    """
    Manages code generation sessions with Redis-backed checkpoints.

    Key patterns:
        checkpoint:{session_id}:state    → SessionState JSON
        checkpoint:{session_id}:files    → List of GeneratedFileCheckpoint JSON
        checkpoint:{session_id}:metadata → SessionMetadata JSON
        checkpoint:user:{user_id}:sessions → Set of session_ids
    """

    CHECKPOINT_PREFIX = "checkpoint"
    DEFAULT_TTL = 86400  # 24 hours
    CHECKPOINT_INTERVAL = 3  # Save checkpoint every N files

    def __init__(self, redis: Redis):
        self.redis = redis
        self.ttl = settings.REDIS_CHECKPOINT_TTL or self.DEFAULT_TTL
        self.checkpoint_interval = settings.CHECKPOINT_INTERVAL or self.CHECKPOINT_INTERVAL

    def _state_key(self, session_id: UUID) -> str:
        return f"{self.CHECKPOINT_PREFIX}:{session_id}:state"

    def _files_key(self, session_id: UUID) -> str:
        return f"{self.CHECKPOINT_PREFIX}:{session_id}:files"

    def _metadata_key(self, session_id: UUID) -> str:
        return f"{self.CHECKPOINT_PREFIX}:{session_id}:metadata"

    def _user_sessions_key(self, user_id: UUID) -> str:
        return f"{self.CHECKPOINT_PREFIX}:user:{user_id}:sessions"

    async def create_session(
        self,
        project_id: UUID,
        user_id: UUID,
        blueprint: dict,
        total_files_expected: int,
        provider: str = "ollama",
        model: str = "qwen3-coder:30b"
    ) -> SessionState:
        """
        Create a new code generation session.

        Args:
            project_id: Project UUID
            user_id: User UUID
            blueprint: AppBlueprint dict
            total_files_expected: Estimated number of files
            provider: AI provider name
            model: Model name

        Returns:
            SessionState with new session_id
        """
        session_id = uuid4()
        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=self.ttl)

        # Calculate blueprint hash for integrity
        blueprint_json = json.dumps(blueprint, sort_keys=True)
        blueprint_hash = hashlib.sha256(blueprint_json.encode()).hexdigest()

        session_state = SessionState(
            session_id=session_id,
            project_id=project_id,
            user_id=user_id,
            status=SessionStatus.CREATED,
            blueprint_hash=blueprint_hash,
            blueprint_version=blueprint.get("version", "1.0.0"),
            total_files_expected=total_files_expected,
            files_completed=0,
            checkpoint_count=0,
            created_at=now,
            updated_at=now,
            expires_at=expires_at
        )

        metadata = SessionMetadata(
            provider=provider,
            model=model
        )

        # Store in Redis with TTL
        pipe = self.redis.pipeline()
        pipe.setex(
            self._state_key(session_id),
            self.ttl,
            session_state.model_dump_json()
        )
        pipe.setex(
            self._metadata_key(session_id),
            self.ttl,
            metadata.model_dump_json()
        )
        pipe.sadd(self._user_sessions_key(user_id), str(session_id))
        pipe.expire(self._user_sessions_key(user_id), self.ttl)
        await pipe.execute()

        return session_state

    async def get_session(self, session_id: UUID) -> Optional[SessionState]:
        """Get session state from Redis."""
        data = await self.redis.get(self._state_key(session_id))
        if not data:
            return None
        return SessionState.model_validate_json(data)

    async def update_session(
        self,
        session_id: UUID,
        status: Optional[SessionStatus] = None,
        files_completed: Optional[int] = None,
        current_file: Optional[str] = None,
        error: Optional[ErrorContext] = None
    ) -> SessionState:
        """
        Update session state.

        Args:
            session_id: Session UUID
            status: New status (optional)
            files_completed: Updated file count (optional)
            current_file: Current file being generated (optional)
            error: Error context to append (optional)

        Returns:
            Updated SessionState
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if status:
            session.status = status
        if files_completed is not None:
            session.files_completed = files_completed
        if current_file is not None:
            session.current_file = current_file
        if error:
            session.errors.append(error)

        session.updated_at = datetime.utcnow()

        # Preserve TTL
        ttl = await self.redis.ttl(self._state_key(session_id))
        if ttl > 0:
            await self.redis.setex(
                self._state_key(session_id),
                ttl,
                session.model_dump_json()
            )

        return session

    async def save_checkpoint(
        self,
        session_id: UUID,
        completed_files: List[GeneratedFileCheckpoint]
    ) -> SessionState:
        """
        Save a checkpoint with completed files.

        Called every CHECKPOINT_INTERVAL files.
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.checkpoint_count += 1
        session.last_checkpoint_at = datetime.utcnow()
        session.files_completed = len(completed_files)
        session.status = SessionStatus.CHECKPOINTED
        session.updated_at = datetime.utcnow()

        # Store files list
        files_json = json.dumps([f.model_dump() for f in completed_files], default=str)

        ttl = await self.redis.ttl(self._state_key(session_id))
        if ttl > 0:
            pipe = self.redis.pipeline()
            pipe.setex(
                self._state_key(session_id),
                ttl,
                session.model_dump_json()
            )
            pipe.setex(
                self._files_key(session_id),
                ttl,
                files_json
            )
            await pipe.execute()

        return session

    async def get_completed_files(
        self,
        session_id: UUID
    ) -> List[GeneratedFileCheckpoint]:
        """Get list of completed files from checkpoint."""
        data = await self.redis.get(self._files_key(session_id))
        if not data:
            return []

        files_data = json.loads(data)
        return [GeneratedFileCheckpoint.model_validate(f) for f in files_data]

    async def should_checkpoint(self, files_completed: int) -> bool:
        """Check if we should save a checkpoint based on interval."""
        return files_completed > 0 and files_completed % self.checkpoint_interval == 0

    async def complete_session(
        self,
        session_id: UUID,
        final_files: List[GeneratedFileCheckpoint],
        metadata_updates: Optional[dict] = None
    ) -> SessionState:
        """Mark session as completed."""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.status = SessionStatus.COMPLETED
        session.files_completed = len(final_files)
        session.current_file = None
        session.updated_at = datetime.utcnow()

        # Store final state (keep for 7 days for completed sessions)
        completed_ttl = 7 * 24 * 3600  # 7 days

        files_json = json.dumps([f.model_dump() for f in final_files], default=str)

        pipe = self.redis.pipeline()
        pipe.setex(
            self._state_key(session_id),
            completed_ttl,
            session.model_dump_json()
        )
        pipe.setex(
            self._files_key(session_id),
            completed_ttl,
            files_json
        )

        if metadata_updates:
            metadata_data = await self.redis.get(self._metadata_key(session_id))
            if metadata_data:
                metadata = SessionMetadata.model_validate_json(metadata_data)
                for key, value in metadata_updates.items():
                    if hasattr(metadata, key):
                        setattr(metadata, key, value)
                pipe.setex(
                    self._metadata_key(session_id),
                    completed_ttl,
                    metadata.model_dump_json()
                )

        await pipe.execute()
        return session

    async def fail_session(
        self,
        session_id: UUID,
        error: ErrorContext
    ) -> SessionState:
        """Mark session as failed with error context."""
        return await self.update_session(
            session_id=session_id,
            status=SessionStatus.FAILED,
            error=error
        )

    async def list_user_sessions(
        self,
        user_id: UUID,
        status_filter: Optional[List[SessionStatus]] = None
    ) -> List[SessionState]:
        """List all sessions for a user, optionally filtered by status."""
        session_ids = await self.redis.smembers(self._user_sessions_key(user_id))

        sessions = []
        for sid in session_ids:
            session = await self.get_session(UUID(sid.decode() if isinstance(sid, bytes) else sid))
            if session:
                if status_filter is None or session.status in status_filter:
                    sessions.append(session)

        # Sort by updated_at descending
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions

    async def cleanup_expired_sessions(self, user_id: UUID) -> int:
        """Remove expired session references from user's session set."""
        session_ids = await self.redis.smembers(self._user_sessions_key(user_id))
        removed = 0

        for sid in session_ids:
            sid_str = sid.decode() if isinstance(sid, bytes) else sid
            exists = await self.redis.exists(self._state_key(UUID(sid_str)))
            if not exists:
                await self.redis.srem(self._user_sessions_key(user_id), sid)
                removed += 1

        return removed
```

---

## 6. Frontend Integration

### 6.1 React Hook

```typescript
// frontend/web/src/hooks/useSessionCheckpoint.ts

import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';

interface SessionState {
  session_id: string;
  project_id: string;
  status: 'created' | 'in_progress' | 'checkpointed' | 'completed' | 'failed' | 'resumed';
  files_completed: number;
  total_files_expected: number;
  checkpoint_count: number;
  last_checkpoint_at: string | null;
  errors: ErrorContext[];
  can_resume: boolean;
}

interface ErrorContext {
  error_type: string;
  error_message: string;
  file_path: string | null;
  recoverable: boolean;
}

interface GeneratedFile {
  file_path: string;
  content: string;
  language: string;
  lines: number;
}

interface UseSessionCheckpointReturn {
  activeSessions: SessionState[];
  isLoading: boolean;
  resumeSession: (sessionId: string) => Promise<void>;
  isResuming: boolean;
  resumedFiles: GeneratedFile[];
  resumeProgress: number;
  clearSession: (sessionId: string) => void;
}

export function useSessionCheckpoint(): UseSessionCheckpointReturn {
  const queryClient = useQueryClient();
  const [resumedFiles, setResumedFiles] = useState<GeneratedFile[]>([]);
  const [resumeProgress, setResumeProgress] = useState(0);
  const [isResuming, setIsResuming] = useState(false);

  // Fetch active sessions
  const { data: activeSessions = [], isLoading } = useQuery({
    queryKey: ['sessions', 'active'],
    queryFn: async () => {
      const response = await apiClient.get<SessionState[]>('/codegen/sessions/active');
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30s
  });

  // Resume session mutation
  const resumeSession = useCallback(async (sessionId: string) => {
    setIsResuming(true);
    setResumedFiles([]);
    setResumeProgress(0);

    try {
      const eventSource = new EventSource(
        `${import.meta.env.VITE_API_URL}/codegen/generate/resume/${sessionId}`,
        { withCredentials: true }
      );

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case 'session_resumed':
            // Set already completed files
            setResumedFiles(data.completed_files);
            setResumeProgress(
              (data.files_already_completed /
               (data.files_already_completed + data.files_remaining)) * 100
            );
            break;

          case 'file_generated':
            setResumedFiles(prev => [...prev, data.file]);
            setResumeProgress(prev =>
              Math.min(prev + (100 / data.total_files), 100)
            );
            break;

          case 'checkpoint':
            // Checkpoint saved - could show toast notification
            console.log(`Checkpoint ${data.checkpoint_number} saved`);
            break;

          case 'generation_complete':
            setIsResuming(false);
            eventSource.close();
            // Invalidate sessions query
            queryClient.invalidateQueries({ queryKey: ['sessions', 'active'] });
            break;

          case 'error':
            console.error('Resume error:', data.message);
            setIsResuming(false);
            eventSource.close();
            break;
        }
      };

      eventSource.onerror = () => {
        setIsResuming(false);
        eventSource.close();
      };
    } catch (error) {
      setIsResuming(false);
      throw error;
    }
  }, [queryClient]);

  // Clear session (remove from local state, let Redis TTL expire)
  const clearSession = useCallback((sessionId: string) => {
    queryClient.setQueryData<SessionState[]>(
      ['sessions', 'active'],
      (old) => old?.filter(s => s.session_id !== sessionId) || []
    );
  }, [queryClient]);

  return {
    activeSessions,
    isLoading,
    resumeSession,
    isResuming,
    resumedFiles,
    resumeProgress,
    clearSession,
  };
}
```

### 6.2 Resume Banner Component

```typescript
// frontend/web/src/components/codegen/SessionResumeBanner.tsx

import React from 'react';
import { AlertCircle, Play, X, Clock } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useSessionCheckpoint } from '@/hooks/useSessionCheckpoint';
import { formatDistanceToNow } from 'date-fns';

interface SessionResumeBannerProps {
  onResume?: (sessionId: string) => void;
}

export function SessionResumeBanner({ onResume }: SessionResumeBannerProps) {
  const {
    activeSessions,
    isLoading,
    resumeSession,
    isResuming,
    resumeProgress,
    clearSession,
  } = useSessionCheckpoint();

  if (isLoading || activeSessions.length === 0) {
    return null;
  }

  // Show most recent resumable session
  const resumableSession = activeSessions.find(
    s => s.status === 'checkpointed' || (s.status === 'failed' && s.errors.some(e => e.recoverable))
  );

  if (!resumableSession) {
    return null;
  }

  const handleResume = async () => {
    await resumeSession(resumableSession.session_id);
    onResume?.(resumableSession.session_id);
  };

  const handleDismiss = () => {
    clearSession(resumableSession.session_id);
  };

  return (
    <Alert className="mb-4 border-yellow-500 bg-yellow-50">
      <AlertCircle className="h-4 w-4 text-yellow-600" />
      <AlertDescription className="flex items-center justify-between">
        <div className="flex-1">
          <span className="font-medium text-yellow-800">
            Incomplete generation detected
          </span>
          <p className="text-sm text-yellow-700">
            {resumableSession.files_completed} of {resumableSession.total_files_expected} files completed
            {resumableSession.last_checkpoint_at && (
              <span className="ml-2 inline-flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {formatDistanceToNow(new Date(resumableSession.last_checkpoint_at), { addSuffix: true })}
              </span>
            )}
          </p>
          {isResuming && (
            <Progress value={resumeProgress} className="mt-2 h-2 w-48" />
          )}
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleResume}
            disabled={isResuming}
          >
            <Play className="mr-1 h-4 w-4" />
            {isResuming ? 'Resuming...' : 'Resume'}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDismiss}
            disabled={isResuming}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </AlertDescription>
    </Alert>
  );
}
```

---

## 7. Configuration

### 7.1 Environment Variables

```bash
# .env.example additions

# Session Checkpoint Configuration
REDIS_CHECKPOINT_TTL=86400          # 24 hours in seconds
CHECKPOINT_INTERVAL=3               # Save checkpoint every N files
CHECKPOINT_COMPLETED_TTL=604800     # 7 days for completed sessions
```

### 7.2 Settings

```python
# backend/app/core/config.py additions

class Settings(BaseSettings):
    # ... existing settings ...

    # Session Checkpoint
    REDIS_CHECKPOINT_TTL: int = 86400  # 24 hours
    CHECKPOINT_INTERVAL: int = 3       # Every 3 files
    CHECKPOINT_COMPLETED_TTL: int = 604800  # 7 days
```

---

## 8. Testing

### 8.1 Unit Tests

```python
# backend/tests/unit/services/test_session_manager.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from app.services.codegen.session_manager import SessionManager
from app.schemas.session import SessionState, SessionStatus, GeneratedFileCheckpoint


@pytest.fixture
def mock_redis():
    return AsyncMock()


@pytest.fixture
def session_manager(mock_redis):
    return SessionManager(mock_redis)


class TestSessionManager:

    @pytest.mark.asyncio
    async def test_create_session(self, session_manager, mock_redis):
        """Test session creation with correct Redis keys"""
        mock_redis.pipeline.return_value = AsyncMock()
        mock_redis.pipeline.return_value.execute = AsyncMock()

        session = await session_manager.create_session(
            project_id=uuid4(),
            user_id=uuid4(),
            blueprint={"app_name": "test", "version": "1.0.0"},
            total_files_expected=10
        )

        assert session.status == SessionStatus.CREATED
        assert session.files_completed == 0
        assert session.checkpoint_count == 0
        mock_redis.pipeline.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_checkpoint(self, session_manager, mock_redis):
        """Test checkpoint saving every N files"""
        # Setup mock session
        session_id = uuid4()
        mock_session = SessionState(
            session_id=session_id,
            project_id=uuid4(),
            user_id=uuid4(),
            status=SessionStatus.IN_PROGRESS,
            blueprint_hash="abc123",
            blueprint_version="1.0.0",
            total_files_expected=10,
            files_completed=0,
            checkpoint_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            expires_at=datetime.utcnow()
        )
        mock_redis.get.return_value = mock_session.model_dump_json()
        mock_redis.ttl.return_value = 3600
        mock_redis.pipeline.return_value = AsyncMock()
        mock_redis.pipeline.return_value.execute = AsyncMock()

        files = [
            GeneratedFileCheckpoint(
                file_path=f"file{i}.py",
                content=f"# file {i}",
                language="python",
                lines=10,
                generated_at=datetime.utcnow(),
                checksum="abc"
            )
            for i in range(3)
        ]

        session = await session_manager.save_checkpoint(session_id, files)

        assert session.checkpoint_count == 1
        assert session.files_completed == 3
        assert session.status == SessionStatus.CHECKPOINTED

    @pytest.mark.asyncio
    async def test_should_checkpoint_interval(self, session_manager):
        """Test checkpoint interval logic"""
        assert await session_manager.should_checkpoint(3) is True
        assert await session_manager.should_checkpoint(6) is True
        assert await session_manager.should_checkpoint(2) is False
        assert await session_manager.should_checkpoint(0) is False

    @pytest.mark.asyncio
    async def test_resume_session_gets_completed_files(self, session_manager, mock_redis):
        """Test resuming session returns completed files"""
        session_id = uuid4()
        files = [
            {"file_path": "main.py", "content": "code", "language": "python",
             "lines": 10, "generated_at": datetime.utcnow().isoformat(), "checksum": "abc"}
        ]
        mock_redis.get.return_value = json.dumps(files)

        completed = await session_manager.get_completed_files(session_id)

        assert len(completed) == 1
        assert completed[0].file_path == "main.py"
```

### 8.2 Integration Tests

```python
# backend/tests/integration/test_session_checkpoint_api.py

import pytest
from httpx import AsyncClient
from uuid import uuid4

from app.main import app


@pytest.mark.asyncio
async def test_resume_endpoint_returns_sse_stream():
    """Test resume endpoint returns SSE stream"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First create a session (mock or fixture)
        session_id = uuid4()

        response = await client.post(
            f"/api/v1/codegen/generate/resume/{session_id}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"


@pytest.mark.asyncio
async def test_list_active_sessions():
    """Test listing active sessions for user"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/codegen/sessions/active",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)
```

---

## 9. Rollout Plan

### Phase 1: Backend Implementation (Day 1)
- [ ] Implement SessionManager service
- [ ] Add Redis key patterns
- [ ] Create session schemas
- [ ] Add resume endpoint
- [ ] Unit tests

### Phase 2: Frontend Integration (Day 1.5)
- [ ] Create useSessionCheckpoint hook
- [ ] Add SessionResumeBanner component
- [ ] Integrate with CodeGenerationPage
- [ ] E2E tests

### Phase 3: Production Rollout (Day 2)
- [ ] Deploy to staging
- [ ] Test with real Ollama generation
- [ ] Monitor Redis memory usage
- [ ] Deploy to production
- [ ] Document in runbook

---

## 10. Monitoring

### 10.1 Prometheus Metrics

```python
# Metrics to add
checkpoint_saves_total = Counter(
    'codegen_checkpoint_saves_total',
    'Total checkpoint saves',
    ['status']  # success, failure
)

session_resumes_total = Counter(
    'codegen_session_resumes_total',
    'Total session resumes',
    ['status']  # success, failure
)

checkpoint_files_count = Histogram(
    'codegen_checkpoint_files_count',
    'Files per checkpoint',
    buckets=[1, 3, 5, 10, 15, 20]
)

session_duration_seconds = Histogram(
    'codegen_session_duration_seconds',
    'Total session duration including resumes',
    buckets=[30, 60, 120, 300, 600]
)
```

### 10.2 Grafana Dashboard

- Active sessions by status
- Checkpoint save rate
- Resume success rate
- Average files per checkpoint
- Redis memory usage for checkpoints

---

## 11. References

- [Vibecode Pattern Adoption Plan](../15-Pattern-Adoption/Vibecode-Pattern-Adoption-Plan.md)
- [Sprint 51 Progress](../../04-build/02-Sprint-Plans/CURRENT-SPRINT.md)
- [ADR-022: EP-06 IR-Based Codegen](../03-ADRs/ADR-022-EP-06-IR-Codegen.md)
- [Redis Best Practices](https://redis.io/docs/management/optimization/)

---

**Last Updated**: December 25, 2025
**Owner**: Backend Team
**Status**: Ready for Implementation
