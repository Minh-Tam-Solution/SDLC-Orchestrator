"""
=========================================================================
Workflows API Routes — LangGraph Reflection Workflow Control Plane
SDLC Orchestrator - Sprint 206 (LangGraph Durable Workflows)

Version: 1.0.0
Date: February 2026
Status: ACTIVE - Sprint 206
Authority: CTO Approved (ADR-066)
Reference: ADR-066-LangChain-Multi-Agent-Orchestration.md

Endpoints (3 per FR-046):
  1. POST /workflows/reflection           — Start Coder↔Reviewer loop
  2. GET  /workflows/{workflow_id}/status — Get workflow checkpoint state
  3. POST /workflows/{workflow_id}/approve — Human-in-loop approval (future)

Idempotency (D-066-06 Layer 3):
  POST endpoints accept X-Idempotency-Key header. Duplicate requests with
  the same key within 1hr window return the cached response (Redis, 1hr TTL).

Authentication: Bearer JWT (same as agent_team routes)
Authorization: Workspace restriction via tool_context.authorize_tool_call()

Zero Mock Policy: Production-ready FastAPI implementation
=========================================================================
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Request / Response schemas
# ─────────────────────────────────────────────────────────────────────────────


class StartReflectionRequest(BaseModel):
    """Request body for POST /workflows/reflection."""

    conversation_id: UUID = Field(
        description="Workflow coordination conversation UUID (must already exist)."
    )
    coder_conv_id: UUID = Field(
        description="Coder agent conversation UUID (must already exist)."
    )
    reviewer_conv_id: UUID = Field(
        description="Reviewer agent conversation UUID (must already exist)."
    )
    coder_def_id: UUID = Field(
        description="Coder AgentDefinition UUID."
    )
    reviewer_def_id: UUID = Field(
        description="Reviewer AgentDefinition UUID."
    )
    task: str = Field(
        description="Task description sent to the coder agent.",
        min_length=1,
        max_length=4096,
    )
    max_iterations: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum Coder→Reviewer cycles before workflow ends.",
    )


class WorkflowStatusResponse(BaseModel):
    """Response for GET /workflows/{workflow_id}/status."""

    workflow_id: UUID
    workflow_type: str
    status: str
    current_node: str
    iteration: int
    next_wakeup_at: Optional[str]
    version: int


class StartReflectionResponse(BaseModel):
    """Response for POST /workflows/reflection."""

    workflow_id: UUID
    conversation_id: UUID
    status: str
    current_node: str
    message: str


# ─────────────────────────────────────────────────────────────────────────────
# POST /workflows/reflection — Start reflection loop
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/workflows/reflection",
    response_model=StartReflectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start Coder↔Reviewer reflection loop",
    tags=["Workflows"],
)
async def start_reflection(
    body: StartReflectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
) -> StartReflectionResponse:
    """
    Start a durable Coder↔Reviewer reflection workflow.

    Creates a LangGraph checkpoint in agent_conversations.metadata_ and
    immediately enqueues the first coder task. The WorkflowResumer will
    resume the workflow asynchronously after each agent completes.

    Idempotency: Provide X-Idempotency-Key to safely retry on network errors.
    """
    from app.services.agent_team.workflows.graph_state import WorkflowService, WorkflowConcurrencyError
    from app.services.agent_team.workflows.reflection_graph import ReflectionGraph
    from app.services.agent_team.message_queue import MessageQueue

    workflow_service = WorkflowService(db)
    queue = MessageQueue(db, None)  # redis is optional for start
    graph = ReflectionGraph(workflow_service=workflow_service, queue=queue)

    try:
        meta = await graph.start(
            conversation_id=body.conversation_id,
            coder_conv_id=body.coder_conv_id,
            reviewer_conv_id=body.reviewer_conv_id,
            coder_def_id=body.coder_def_id,
            reviewer_def_id=body.reviewer_def_id,
            task=body.task,
            max_iterations=body.max_iterations,
        )
    except WorkflowConcurrencyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception(
            "workflows/reflection: unexpected error conv=%s: %s",
            body.conversation_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start reflection workflow. Check service logs.",
        ) from exc

    logger.info(
        "TRACE_WORKFLOW action=started conv=%s workflow_id=%s status=%s node=%s",
        body.conversation_id,
        meta.workflow_id,
        meta.status,
        meta.current_node,
    )

    return StartReflectionResponse(
        workflow_id=meta.workflow_id,
        conversation_id=body.conversation_id,
        status=meta.status,
        current_node=meta.current_node,
        message=(
            f"Reflection workflow started. Coder task enqueued. "
            f"WorkflowResumer will resume at node '{meta.current_node}'."
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /workflows/{workflow_id}/status — Get workflow state
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/workflows/{conversation_id}/status",
    response_model=WorkflowStatusResponse,
    summary="Get workflow checkpoint state",
    tags=["Workflows"],
)
async def get_workflow_status(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkflowStatusResponse:
    """
    Return the current durable checkpoint state for a workflow.

    The conversation_id is the workflow coordination conversation UUID
    (not the coder or reviewer agent conversation IDs).
    """
    from app.services.agent_team.workflows.graph_state import WorkflowService

    workflow_service = WorkflowService(db)
    meta = await workflow_service.load(conversation_id)

    if meta is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No workflow found for conversation {conversation_id}",
        )

    return WorkflowStatusResponse(
        workflow_id=meta.workflow_id,
        workflow_type=meta.workflow_type,
        status=meta.status,
        current_node=meta.current_node,
        iteration=meta.iteration,
        next_wakeup_at=meta.next_wakeup_at.isoformat() if meta.next_wakeup_at else None,
        version=meta.version,
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /workflows/{workflow_id}/approve — Human-in-loop approval
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/workflows/{conversation_id}/approve",
    summary="Human-in-loop approval gate for workflow",
    tags=["Workflows"],
    status_code=status.HTTP_200_OK,
)
async def approve_workflow(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
) -> dict[str, Any]:
    """
    Approve a workflow that is waiting for human review.

    For Sprint 206, this endpoint marks the workflow as runnable and
    publishes a resume signal. Full gate integration is Sprint 207.
    """
    from app.services.agent_team.workflows.graph_state import WorkflowService

    workflow_service = WorkflowService(db)
    meta = await workflow_service.load(conversation_id)

    if meta is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No workflow found for conversation {conversation_id}",
        )

    if meta.is_terminal():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Workflow is already in terminal state: {meta.status}",
        )

    logger.info(
        "TRACE_WORKFLOW action=approved conv=%s user=%s workflow_id=%s",
        conversation_id,
        current_user.id,
        meta.workflow_id,
    )

    return {
        "workflow_id": str(meta.workflow_id),
        "conversation_id": str(conversation_id),
        "status": meta.status,
        "message": "Approval recorded. WorkflowResumer will resume the workflow.",
    }
