"""
=========================================================================
E2E Execution Store Service
SDLC Orchestrator - Sprint 140 (CLI Orchestration Upgrade)

Version: 1.0.0
Date: February 11, 2026
Status: ACTIVE - Sprint 140 Day 2
Authority: Backend Lead + CTO Approved
Framework: SDLC 6.0.5 (RFC-SDLC-602 E2E API Testing Enhancement)

Purpose:
- Redis-backed store for E2E test execution state
- Persistent execution tracking across server restarts
- TTL-based cleanup for completed executions
- Fallback to in-memory store when Redis unavailable

Zero Mock Policy: Production-ready Redis integration
=========================================================================
"""

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.utils.redis import get_redis_client

logger = logging.getLogger(__name__)

# Redis key prefix for E2E executions
E2E_EXECUTION_PREFIX = "e2e:execution:"
E2E_EXECUTION_INDEX = "e2e:executions"

# TTL for execution records (7 days)
EXECUTION_TTL_SECONDS = 7 * 24 * 60 * 60


class ExecutionStatus(str, Enum):
    """Test execution status."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class E2EExecutionStore:
    """Redis-backed store for E2E test execution state.

    Provides persistent storage for test execution records with:
    - Automatic TTL cleanup
    - User-based filtering
    - Project-based filtering
    - Fallback to in-memory when Redis unavailable

    Example:
        store = E2EExecutionStore()
        execution = await store.create_execution(
            project_id="123",
            user_id="456",
            runner="newman",
            test_suite_path="/tests/collection.json"
        )
        await store.update_status(execution["id"], ExecutionStatus.RUNNING)
        await store.set_results(execution["id"], results)
    """

    def __init__(self):
        """Initialize the execution store."""
        self._redis_available: Optional[bool] = None
        # In-memory fallback (used only when Redis unavailable)
        self._memory_store: Dict[str, Dict[str, Any]] = {}

    async def _get_redis(self):
        """Get Redis client with availability check."""
        if self._redis_available is False:
            return None

        try:
            redis = await get_redis_client()
            self._redis_available = True
            return redis
        except Exception as e:
            logger.warning(f"Redis unavailable, using in-memory fallback: {e}")
            self._redis_available = False
            return None

    def _execution_key(self, execution_id: str) -> str:
        """Get Redis key for execution."""
        return f"{E2E_EXECUTION_PREFIX}{execution_id}"

    def _serialize(self, data: Dict[str, Any]) -> str:
        """Serialize execution data to JSON."""

        def default_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, UUID):
                return str(obj)
            if isinstance(obj, Enum):
                return obj.value
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        return json.dumps(data, default=default_serializer)

    def _deserialize(self, data: str) -> Dict[str, Any]:
        """Deserialize JSON to execution data."""
        result = json.loads(data)

        # Parse datetime strings
        for key in ["created_at", "started_at", "completed_at"]:
            if result.get(key):
                try:
                    result[key] = datetime.fromisoformat(result[key])
                except (ValueError, TypeError):
                    pass

        # Parse status enum
        if "status" in result:
            try:
                result["status"] = ExecutionStatus(result["status"])
            except ValueError:
                pass

        return result

    async def create_execution(
        self,
        execution_id: str,
        project_id: str,
        user_id: str,
        runner: str,
        test_suite_path: str,
        environment: Optional[str] = None,
        environment_variables: Optional[Dict[str, str]] = None,
        timeout_seconds: int = 300,
    ) -> Dict[str, Any]:
        """Create a new execution record.

        Args:
            execution_id: Unique execution identifier
            project_id: Project UUID
            user_id: User UUID
            runner: Test runner type (newman, pytest, etc.)
            test_suite_path: Path to test suite
            environment: Optional environment file path
            environment_variables: Additional env vars
            timeout_seconds: Execution timeout

        Returns:
            Created execution record
        """
        execution = {
            "id": execution_id,
            "project_id": project_id,
            "user_id": user_id,
            "status": ExecutionStatus.QUEUED,
            "runner": runner,
            "test_suite_path": test_suite_path,
            "environment": environment,
            "environment_variables": environment_variables or {},
            "timeout_seconds": timeout_seconds,
            "created_at": datetime.now(timezone.utc),
            "started_at": None,
            "completed_at": None,
            "results": None,
            "error": None,
        }

        redis = await self._get_redis()
        if redis:
            try:
                key = self._execution_key(execution_id)
                await redis.set(
                    key,
                    self._serialize(execution),
                    ex=EXECUTION_TTL_SECONDS,
                )
                # Add to user's execution index
                user_index = f"e2e:user:{user_id}:executions"
                await redis.zadd(
                    user_index,
                    {execution_id: datetime.now(timezone.utc).timestamp()},
                )
                # Add to project's execution index
                project_index = f"e2e:project:{project_id}:executions"
                await redis.zadd(
                    project_index,
                    {execution_id: datetime.now(timezone.utc).timestamp()},
                )
                logger.debug(f"Execution {execution_id} created in Redis")
            except Exception as e:
                logger.error(f"Failed to store execution in Redis: {e}")
                self._memory_store[execution_id] = execution
        else:
            self._memory_store[execution_id] = execution

        return execution

    async def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution record by ID.

        Args:
            execution_id: Execution identifier

        Returns:
            Execution record or None if not found
        """
        redis = await self._get_redis()
        if redis:
            try:
                key = self._execution_key(execution_id)
                data = await redis.get(key)
                if data:
                    return self._deserialize(data)
            except Exception as e:
                logger.error(f"Failed to get execution from Redis: {e}")

        return self._memory_store.get(execution_id)

    async def update_status(
        self,
        execution_id: str,
        status: ExecutionStatus,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update execution status.

        Args:
            execution_id: Execution identifier
            status: New status
            started_at: Execution start time
            completed_at: Execution completion time
            error: Error message if failed

        Returns:
            Updated execution record or None if not found
        """
        execution = await self.get_execution(execution_id)
        if not execution:
            return None

        execution["status"] = status
        if started_at:
            execution["started_at"] = started_at
        if completed_at:
            execution["completed_at"] = completed_at
        if error:
            execution["error"] = error

        redis = await self._get_redis()
        if redis:
            try:
                key = self._execution_key(execution_id)
                await redis.set(
                    key,
                    self._serialize(execution),
                    ex=EXECUTION_TTL_SECONDS,
                )
            except Exception as e:
                logger.error(f"Failed to update execution in Redis: {e}")
                self._memory_store[execution_id] = execution
        else:
            self._memory_store[execution_id] = execution

        return execution

    async def set_results(
        self,
        execution_id: str,
        results: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Set execution results.

        Args:
            execution_id: Execution identifier
            results: Test results data

        Returns:
            Updated execution record or None if not found
        """
        execution = await self.get_execution(execution_id)
        if not execution:
            return None

        execution["results"] = results
        execution["status"] = ExecutionStatus.COMPLETED
        execution["completed_at"] = datetime.now(timezone.utc)

        redis = await self._get_redis()
        if redis:
            try:
                key = self._execution_key(execution_id)
                await redis.set(
                    key,
                    self._serialize(execution),
                    ex=EXECUTION_TTL_SECONDS,
                )
            except Exception as e:
                logger.error(f"Failed to set results in Redis: {e}")
                self._memory_store[execution_id] = execution
        else:
            self._memory_store[execution_id] = execution

        return execution

    async def list_executions(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List executions with optional filters.

        Args:
            user_id: Filter by user
            project_id: Filter by project
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of execution records
        """
        redis = await self._get_redis()
        if redis:
            try:
                # Determine which index to use
                if user_id:
                    index_key = f"e2e:user:{user_id}:executions"
                elif project_id:
                    index_key = f"e2e:project:{project_id}:executions"
                else:
                    # Return empty - need user or project filter
                    return []

                # Get execution IDs from sorted set (most recent first)
                execution_ids = await redis.zrevrange(
                    index_key,
                    offset,
                    offset + limit - 1,
                )

                # Fetch execution details
                executions = []
                for exec_id in execution_ids:
                    exec_data = await self.get_execution(exec_id)
                    if exec_data:
                        executions.append(exec_data)

                return executions

            except Exception as e:
                logger.error(f"Failed to list executions from Redis: {e}")

        # Fallback to in-memory
        executions = list(self._memory_store.values())

        # Apply filters
        if user_id:
            executions = [e for e in executions if e.get("user_id") == user_id]
        if project_id:
            executions = [e for e in executions if e.get("project_id") == project_id]

        # Sort by created_at descending
        executions.sort(
            key=lambda x: x.get("created_at", datetime.min.replace(tzinfo=timezone.utc)),
            reverse=True,
        )

        # Apply pagination
        return executions[offset : offset + limit]

    async def delete_execution(self, execution_id: str) -> bool:
        """Delete an execution record.

        Args:
            execution_id: Execution identifier

        Returns:
            True if deleted, False if not found
        """
        execution = await self.get_execution(execution_id)
        if not execution:
            return False

        redis = await self._get_redis()
        if redis:
            try:
                key = self._execution_key(execution_id)
                await redis.delete(key)

                # Remove from indexes
                user_id = execution.get("user_id")
                project_id = execution.get("project_id")

                if user_id:
                    user_index = f"e2e:user:{user_id}:executions"
                    await redis.zrem(user_index, execution_id)

                if project_id:
                    project_index = f"e2e:project:{project_id}:executions"
                    await redis.zrem(project_index, execution_id)

                return True

            except Exception as e:
                logger.error(f"Failed to delete execution from Redis: {e}")

        # Fallback to in-memory
        if execution_id in self._memory_store:
            del self._memory_store[execution_id]
            return True

        return False

    async def get_stats(self, user_id: Optional[str] = None) -> Dict[str, int]:
        """Get execution statistics.

        Args:
            user_id: Optional filter by user

        Returns:
            Dict with counts by status
        """
        executions = await self.list_executions(user_id=user_id, limit=1000)

        stats = {
            "total": len(executions),
            "queued": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
            "timeout": 0,
        }

        for execution in executions:
            status = execution.get("status")
            if isinstance(status, ExecutionStatus):
                status = status.value
            if status in stats:
                stats[status] += 1

        return stats


# Global store instance
_execution_store: Optional[E2EExecutionStore] = None


async def get_execution_store() -> E2EExecutionStore:
    """Get E2E execution store instance (singleton).

    Returns:
        E2EExecutionStore instance
    """
    global _execution_store
    if _execution_store is None:
        _execution_store = E2EExecutionStore()
    return _execution_store
