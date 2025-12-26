"""
=========================================================================
Session Manager - Redis-Backed Checkpoint Management
SDLC Orchestrator - Sprint 51B

Version: 1.0.0
Date: December 26, 2025
Status: ACTIVE - Sprint 51B Implementation
Authority: Backend Team + CTO Approved
Foundation: Session-Checkpoint-Design.md

Purpose:
- Manage code generation sessions with Redis checkpoints
- Enable resume from last successful checkpoint
- Track session lifecycle and errors
- Support 24h TTL with automatic cleanup

Key Patterns:
- checkpoint:{session_id}:state    → SessionState JSON
- checkpoint:{session_id}:files    → List[GeneratedFileCheckpoint] JSON
- checkpoint:{session_id}:metadata → SessionMetadata JSON
- checkpoint:user:{user_id}:sessions → Set of session_ids

References:
- docs/02-design/14-Technical-Specs/Session-Checkpoint-Design.md
- docs/02-design/15-Pattern-Adoption/Vibecode-Pattern-Adoption-Plan.md
=========================================================================
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4

from redis.asyncio import Redis

from app.core.config import settings
from app.schemas.session import (
    ErrorContext,
    GeneratedFileCheckpoint,
    SessionMetadata,
    SessionState,
    SessionStatus,
)

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages code generation sessions with Redis-backed checkpoints.

    Key patterns:
        checkpoint:{session_id}:state    → SessionState JSON
        checkpoint:{session_id}:files    → List of GeneratedFileCheckpoint JSON
        checkpoint:{session_id}:metadata → SessionMetadata JSON
        checkpoint:user:{user_id}:sessions → Set of session_ids

    Example usage:
        manager = SessionManager(redis)
        session = await manager.create_session(
            project_id=uuid4(),
            user_id=uuid4(),
            blueprint={"app_name": "test"},
            total_files_expected=10
        )

        # During generation
        await manager.update_session(
            session.session_id,
            files_completed=3,
            current_file="app/models.py"
        )

        # Save checkpoint every 3 files
        if await manager.should_checkpoint(files_completed=3):
            await manager.save_checkpoint(session.session_id, completed_files)

        # Resume after failure
        completed_files = await manager.get_completed_files(session.session_id)
    """

    CHECKPOINT_PREFIX = "checkpoint"
    DEFAULT_TTL = 86400  # 24 hours
    DEFAULT_CHECKPOINT_INTERVAL = 3  # Save checkpoint every N files
    COMPLETED_TTL = 604800  # 7 days for completed sessions

    def __init__(self, redis: Redis):
        """
        Initialize SessionManager with Redis connection.

        Args:
            redis: Async Redis connection
        """
        self.redis = redis
        self.ttl = getattr(settings, 'REDIS_CHECKPOINT_TTL', self.DEFAULT_TTL)
        self.checkpoint_interval = getattr(
            settings, 'CHECKPOINT_INTERVAL', self.DEFAULT_CHECKPOINT_INTERVAL
        )

    def _state_key(self, session_id: UUID) -> str:
        """Redis key for session state."""
        return f"{self.CHECKPOINT_PREFIX}:{session_id}:state"

    def _files_key(self, session_id: UUID) -> str:
        """Redis key for completed files list."""
        return f"{self.CHECKPOINT_PREFIX}:{session_id}:files"

    def _metadata_key(self, session_id: UUID) -> str:
        """Redis key for session metadata."""
        return f"{self.CHECKPOINT_PREFIX}:{session_id}:metadata"

    def _user_sessions_key(self, user_id: UUID) -> str:
        """Redis key for user's session set."""
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

        # Calculate blueprint hash for integrity verification
        blueprint_json = json.dumps(blueprint, sort_keys=True, default=str)
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

        # Store in Redis with TTL using pipeline for atomicity
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

        logger.info(
            f"Created session {session_id} for user {user_id}, "
            f"expecting {total_files_expected} files"
        )

        return session_state

    async def get_session(self, session_id: UUID) -> Optional[SessionState]:
        """
        Get session state from Redis.

        Args:
            session_id: Session UUID

        Returns:
            SessionState if found, None otherwise
        """
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

        Raises:
            ValueError: If session not found
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

        # Preserve existing TTL
        ttl = await self.redis.ttl(self._state_key(session_id))
        if ttl > 0:
            await self.redis.setex(
                self._state_key(session_id),
                ttl,
                session.model_dump_json()
            )
        else:
            # Session expired, use default TTL
            await self.redis.setex(
                self._state_key(session_id),
                self.ttl,
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

        Args:
            session_id: Session UUID
            completed_files: List of completed file checkpoints

        Returns:
            Updated SessionState with new checkpoint count
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.checkpoint_count += 1
        session.last_checkpoint_at = datetime.utcnow()
        session.files_completed = len(completed_files)
        session.status = SessionStatus.CHECKPOINTED
        session.updated_at = datetime.utcnow()

        # Serialize files list
        files_json = json.dumps(
            [f.model_dump() for f in completed_files],
            default=str
        )

        ttl = await self.redis.ttl(self._state_key(session_id))
        if ttl <= 0:
            ttl = self.ttl

        # Atomic update using pipeline
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

        logger.info(
            f"Saved checkpoint {session.checkpoint_count} for session {session_id}, "
            f"{len(completed_files)} files"
        )

        return session

    async def get_completed_files(
        self,
        session_id: UUID
    ) -> List[GeneratedFileCheckpoint]:
        """
        Get list of completed files from checkpoint.

        Args:
            session_id: Session UUID

        Returns:
            List of GeneratedFileCheckpoint objects
        """
        data = await self.redis.get(self._files_key(session_id))
        if not data:
            return []

        files_data = json.loads(data)
        return [GeneratedFileCheckpoint.model_validate(f) for f in files_data]

    async def should_checkpoint(self, files_completed: int) -> bool:
        """
        Check if we should save a checkpoint based on interval.

        Args:
            files_completed: Number of files completed

        Returns:
            True if checkpoint should be saved
        """
        return files_completed > 0 and files_completed % self.checkpoint_interval == 0

    async def complete_session(
        self,
        session_id: UUID,
        final_files: List[GeneratedFileCheckpoint],
        metadata_updates: Optional[dict] = None
    ) -> SessionState:
        """
        Mark session as completed.

        Completed sessions are kept for 7 days.

        Args:
            session_id: Session UUID
            final_files: Final list of generated files
            metadata_updates: Optional metadata to update (e.g., tokens, time)

        Returns:
            Updated SessionState with COMPLETED status
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.status = SessionStatus.COMPLETED
        session.files_completed = len(final_files)
        session.current_file = None
        session.updated_at = datetime.utcnow()

        # Completed sessions get longer TTL
        completed_ttl = self.COMPLETED_TTL

        files_json = json.dumps(
            [f.model_dump() for f in final_files],
            default=str
        )

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

        # Update metadata if provided
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

        logger.info(
            f"Completed session {session_id} with {len(final_files)} files"
        )

        return session

    async def fail_session(
        self,
        session_id: UUID,
        error: ErrorContext
    ) -> SessionState:
        """
        Mark session as failed with error context.

        Failed sessions can still be resumed if error is recoverable.

        Args:
            session_id: Session UUID
            error: Error context with recovery info

        Returns:
            Updated SessionState with FAILED status
        """
        logger.warning(
            f"Session {session_id} failed: {error.error_type} - {error.error_message}"
        )
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
        """
        List all sessions for a user, optionally filtered by status.

        Args:
            user_id: User UUID
            status_filter: Optional list of statuses to include

        Returns:
            List of SessionState objects, sorted by updated_at descending
        """
        session_ids = await self.redis.smembers(self._user_sessions_key(user_id))

        sessions = []
        for sid in session_ids:
            sid_str = sid.decode() if isinstance(sid, bytes) else sid
            try:
                session = await self.get_session(UUID(sid_str))
                if session:
                    if status_filter is None or session.status in status_filter:
                        sessions.append(session)
            except (ValueError, Exception) as e:
                # Invalid UUID or parsing error - skip
                logger.debug(f"Skipping invalid session {sid_str}: {e}")
                continue

        # Sort by updated_at descending (most recent first)
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions

    async def cleanup_expired_sessions(self, user_id: UUID) -> int:
        """
        Remove expired session references from user's session set.

        Called periodically to clean up stale references.

        Args:
            user_id: User UUID

        Returns:
            Number of sessions removed
        """
        session_ids = await self.redis.smembers(self._user_sessions_key(user_id))
        removed = 0

        for sid in session_ids:
            sid_str = sid.decode() if isinstance(sid, bytes) else sid
            try:
                exists = await self.redis.exists(self._state_key(UUID(sid_str)))
                if not exists:
                    await self.redis.srem(self._user_sessions_key(user_id), sid)
                    removed += 1
            except (ValueError, Exception):
                # Invalid UUID - remove it
                await self.redis.srem(self._user_sessions_key(user_id), sid)
                removed += 1

        if removed > 0:
            logger.info(f"Cleaned up {removed} expired sessions for user {user_id}")

        return removed

    async def get_metadata(self, session_id: UUID) -> Optional[SessionMetadata]:
        """
        Get session metadata.

        Args:
            session_id: Session UUID

        Returns:
            SessionMetadata if found, None otherwise
        """
        data = await self.redis.get(self._metadata_key(session_id))
        if not data:
            return None
        return SessionMetadata.model_validate_json(data)

    async def increment_resume_count(self, session_id: UUID) -> int:
        """
        Increment resume count and return new value.

        Args:
            session_id: Session UUID

        Returns:
            New resume count
        """
        metadata = await self.get_metadata(session_id)
        if not metadata:
            return 0

        metadata.resume_count += 1

        ttl = await self.redis.ttl(self._metadata_key(session_id))
        if ttl > 0:
            await self.redis.setex(
                self._metadata_key(session_id),
                ttl,
                metadata.model_dump_json()
            )

        return metadata.resume_count


# Singleton instance for dependency injection
_session_manager: Optional[SessionManager] = None


async def get_session_manager(redis: Redis) -> SessionManager:
    """
    Get SessionManager instance.

    Args:
        redis: Redis connection

    Returns:
        SessionManager instance
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(redis)
    return _session_manager
