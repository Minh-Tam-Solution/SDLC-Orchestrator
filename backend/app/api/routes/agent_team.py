"""
=========================================================================
Multi-Agent Team Engine API Routes (ADR-056/EP-07)
SDLC Orchestrator - Sprint 177 (Multi-Agent Core Services)

Version: 2.0.0
Date: 2026-02-18
Status: ACTIVE - Sprint 177
Authority: CTO Approved (ADR-056, EP-07)
Reference: ADR-056-Multi-Agent-Team-Engine.md
Reference: API-Specification.md v3.6.0

Purpose:
- 5 P0 endpoints for Multi-Agent Team Engine CRUD + messaging
- Agent definition lifecycle (create, list, get, update)
- Conversation management (start, list, get, interrupt)
- Message handling (send, list) with lane-based processing
- Delegates all business logic to Sprint 177 service layer

Endpoints (11 total per API Spec v3.6.0):
P0 (Sprint 176-177):
  1. POST   /agent-team/definitions           — Create agent definition
  2. GET    /agent-team/definitions           — List agent definitions
  3. GET    /agent-team/definitions/{id}      — Get agent definition
  4. PUT    /agent-team/definitions/{id}      — Update agent definition
  5. POST   /agent-team/conversations         — Start conversation
  6. GET    /agent-team/conversations         — List conversations
  7. GET    /agent-team/conversations/{id}    — Get conversation
  8. POST   /agent-team/conversations/{id}/messages — Send message
  9. GET    /agent-team/conversations/{id}/messages — Get messages

P1 (Sprint 178):
  10. POST  /agent-team/conversations/{id}/interrupt — Human-in-the-loop
  11. DELETE /agent-team/definitions/{id}      — Deactivate agent

4 Locked Decisions Applied:
  1. Snapshot Precedence — conversation creation snapshots definition fields
  2. Lane Contract — messages assigned to processing lanes
  3. Provider Profile Key — tracked per message
  4. Canonical Protocol Owner — this file IS the canonical endpoint definition

Sprint 177 Refactoring:
  All inline DB queries replaced with service layer delegation:
  - AgentRegistry: definition CRUD + SE4H enforcement
  - ConversationTracker: lifecycle + loop guards + budget
  - MessageQueue: lane-based enqueue + dedupe
  - MentionParser: @mention routing

Zero Mock Policy: Production-ready FastAPI endpoint implementation
=========================================================================
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.agent_team import (
    AgentDefinitionCreate,
    AgentDefinitionUpdate,
    AgentDefinitionResponse,
    AgentDefinitionListResponse,
    ConversationCreate,
    ConversationResponse,
    ConversationListResponse,
    MessageSend,
    MessageResponse,
    MessageListResponse,
    ConversationInterrupt,
)
from app.services.agent_team import (
    AgentRegistry,
    AgentNotFoundError,
    AgentDuplicateError,
    AgentInactiveError,
    ConversationTracker,
    ConversationNotFoundError,
    ConversationInactiveError,
    LimitExceededError,
    DelegationDepthError,
    MessageQueue,
    MentionParser,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-team", tags=["Multi-Agent Team Engine"])


# =========================================================================
# Agent Definition Endpoints
# =========================================================================


@router.post(
    "/definitions",
    response_model=AgentDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create agent definition",
    description="Create a new agent definition (template/defaults). "
    "Snapshot Precedence: these values become defaults for new conversations. "
    "SE4H roles (ceo, cpo, cto) automatically receive restricted permissions.",
)
async def create_agent_definition(
    payload: AgentDefinitionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentDefinitionResponse:
    """Create an agent definition with SDLC role, provider config, and safety controls."""
    logger.info(
        "Creating agent definition: name=%s, role=%s, project=%s, user=%s",
        payload.agent_name,
        payload.sdlc_role.value,
        payload.project_id,
        current_user.id,
    )

    registry = AgentRegistry(db)
    try:
        definition = await registry.create(payload)
    except AgentDuplicateError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agent '{payload.agent_name}' already exists in this project",
        )

    await db.commit()
    await db.refresh(definition)

    logger.info("Created agent definition: id=%s, name=%s", definition.id, definition.agent_name)
    return AgentDefinitionResponse.model_validate(definition)


@router.post(
    "/definitions/seed",
    response_model=list[AgentDefinitionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Seed default agent definitions",
    description="Create 12 default SDLC role agent definitions for a project. "
    "Skips roles that already have an active definition.",
)
async def seed_agent_definitions(
    project_id: UUID,
    team_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AgentDefinitionResponse]:
    """Seed 12 default agent definitions (Sprint 194 GAP-01)."""
    from app.services.agent_team.agent_seed_service import AgentSeedService

    logger.info("Seeding agent definitions for project=%s, user=%s", project_id, current_user.id)
    svc = AgentSeedService(db)
    created = await svc.seed_project_agents(project_id, team_id=team_id)
    await db.commit()
    for d in created:
        await db.refresh(d)
    logger.info("Seeded %d agent definitions for project=%s", len(created), project_id)
    return [AgentDefinitionResponse.model_validate(d) for d in created]


@router.get(
    "/presets",
    summary="List team presets",
    description="Return all 5 named team presets (solo-dev, startup-2, enterprise-3, "
    "review-pair, full-sprint). Presets are code-defined constants.",
)
async def list_team_presets(
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """List available team presets (Sprint 194 GAP-02)."""
    from app.services.agent_team.team_presets import list_presets

    return list_presets()


@router.post(
    "/presets/{preset_name}/apply",
    status_code=status.HTTP_201_CREATED,
    summary="Apply team preset",
    description="Seed agent definitions for a named team preset. "
    "Only seeds roles defined in the preset, skipping roles that already exist.",
)
async def apply_team_preset(
    preset_name: str,
    project_id: UUID = Query(..., description="Project UUID"),
    team_id: Optional[UUID] = Query(None, description="Optional team UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Apply a team preset to seed agent definitions (Sprint 194 GAP-02)."""
    from app.services.agent_team.team_presets import TeamPresetService

    logger.info(
        "Applying preset '%s' to project=%s, user=%s",
        preset_name, project_id, current_user.id,
    )
    try:
        svc = TeamPresetService(db)
        result = await svc.apply_preset(preset_name, project_id, team_id=team_id)
        await db.commit()
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/definitions",
    response_model=AgentDefinitionListResponse,
    summary="List agent definitions",
    description="List agent definitions for a project with pagination and optional role filter.",
)
async def list_agent_definitions(
    project_id: UUID = Query(..., description="Project UUID"),
    sdlc_role: Optional[str] = Query(None, description="Filter by SDLC role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentDefinitionListResponse:
    """List agent definitions with filters and pagination."""
    registry = AgentRegistry(db)
    definitions, total = await registry.list_definitions(
        project_id=project_id,
        sdlc_role=sdlc_role,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )

    return AgentDefinitionListResponse(
        items=[AgentDefinitionResponse.model_validate(d) for d in definitions],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get(
    "/definitions/{definition_id}",
    response_model=AgentDefinitionResponse,
    summary="Get agent definition",
    description="Get a single agent definition by ID.",
)
async def get_agent_definition(
    definition_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentDefinitionResponse:
    """Get agent definition by ID."""
    registry = AgentRegistry(db)
    try:
        definition = await registry.get(definition_id)
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent definition {definition_id} not found",
        )

    return AgentDefinitionResponse.model_validate(definition)


@router.put(
    "/definitions/{definition_id}",
    response_model=AgentDefinitionResponse,
    summary="Update agent definition",
    description="Partially update an agent definition. "
    "NOTE: Changes do NOT affect running conversations (Snapshot Precedence). "
    "SE4H constraints are re-enforced if role changes to ceo/cpo/cto.",
)
async def update_agent_definition(
    definition_id: UUID,
    payload: AgentDefinitionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentDefinitionResponse:
    """Update agent definition fields. Running conversations are unaffected."""
    registry = AgentRegistry(db)
    try:
        definition = await registry.update(definition_id, payload)
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent definition {definition_id} not found",
        )
    except AgentDuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    await db.commit()
    await db.refresh(definition)

    logger.info("Updated agent definition: id=%s", definition.id)
    return AgentDefinitionResponse.model_validate(definition)


@router.delete(
    "/definitions/{definition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate agent definition",
    description="Soft-deactivate an agent definition. "
    "Fails if the agent has active conversations (complete them first). "
    "Running conversations are NOT affected — only new conversations are prevented.",
)
async def deactivate_agent_definition(
    definition_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Soft-deactivate an agent definition (set is_active=False)."""
    registry = AgentRegistry(db)

    try:
        definition = await registry.get(definition_id)
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent definition {definition_id} not found",
        )

    # Check for active conversations before deactivating
    active_count = await registry.has_active_conversations(definition_id)
    if active_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot deactivate: {active_count} active conversation(s) exist. "
            "Complete or interrupt them first.",
        )

    await registry.deactivate(definition_id)
    await db.commit()

    logger.info(
        "Deactivated agent definition: id=%s, name=%s, user=%s",
        definition_id,
        definition.agent_name,
        current_user.id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# =========================================================================
# Conversation Endpoints
# =========================================================================


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start conversation",
    description="Start a new agent conversation. "
    "Snapshot Precedence: max_messages, max_budget_cents, queue_mode, session_scope "
    "are copied from the agent definition and become immutable for this conversation.",
)
async def start_conversation(
    payload: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationResponse:
    """Start a conversation with snapshot precedence from agent definition."""
    registry = AgentRegistry(db)
    tracker = ConversationTracker(db)

    # Fetch and validate agent definition
    try:
        definition = await registry.get_active(payload.agent_definition_id)
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent definition {payload.agent_definition_id} not found",
        )
    except AgentInactiveError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent definition {payload.agent_definition_id} is inactive",
        )

    # Validate project_id matches definition's project_id
    if definition.project_id != payload.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="project_id does not match agent definition's project",
        )

    # Create conversation with snapshot precedence + delegation depth validation
    try:
        conversation = await tracker.create(
            definition=definition,
            project_id=payload.project_id,
            initiator_type=payload.initiator_type.value,
            initiator_id=payload.initiator_id,
            channel=payload.channel.value,
            parent_conversation_id=payload.parent_conversation_id,
            metadata=payload.metadata,
        )
    except DelegationDepthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    await db.commit()
    await db.refresh(conversation)

    return ConversationResponse.model_validate(conversation)


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    summary="List conversations",
    description="List agent conversations for a project with optional status filter.",
)
async def list_conversations(
    project_id: UUID = Query(..., description="Project UUID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationListResponse:
    """List conversations with pagination."""
    tracker = ConversationTracker(db)
    conversations, total = await tracker.list_conversations(
        project_id=project_id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )

    return ConversationListResponse(
        items=[ConversationResponse.model_validate(c) for c in conversations],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get conversation",
    description="Get a single conversation by ID with snapshotted configuration.",
)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationResponse:
    """Get conversation by ID."""
    tracker = ConversationTracker(db)
    try:
        conversation = await tracker.get(conversation_id)
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    return ConversationResponse.model_validate(conversation)


# =========================================================================
# Message Endpoints
# =========================================================================


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send message",
    description="Send a message to an agent conversation. "
    "The message is assigned to a processing lane and queued for processing. "
    "Idempotent: duplicate dedupe_key is silently ignored.",
)
async def send_message(
    conversation_id: UUID,
    payload: MessageSend,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """Send a message to a conversation with lane-based queue processing."""
    tracker = ConversationTracker(db)
    queue = MessageQueue(db)
    registry = AgentRegistry(db)

    # Validate conversation exists and is active
    try:
        conversation = await tracker.get_active(conversation_id)
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    except ConversationInactiveError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Check loop guards (message count + budget circuit breaker)
    try:
        await tracker.check_limits(conversation)
    except LimitExceededError as e:
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Determine processing lane from agent definition
    definition = await registry.get(conversation.agent_definition_id)
    processing_lane = f"agent:{definition.agent_name}"

    # Enqueue message (handles dedupe internally)
    message = await queue.enqueue(
        conversation_id=conversation_id,
        content=payload.content,
        sender_type=payload.sender_type.value,
        sender_id=payload.sender_id,
        processing_lane=processing_lane,
        queue_mode=conversation.queue_mode,
        message_type=payload.message_type.value,
        recipient_id=payload.recipient_id,
        mentions=payload.mentions,
        dedupe_key=payload.dedupe_key,
    )

    # Increment conversation message count
    await tracker.increment_message_count(conversation_id)

    await db.commit()
    await db.refresh(message)

    logger.info(
        "Message sent: id=%s, conv=%s, lane=%s",
        message.id,
        conversation_id,
        processing_lane,
    )
    return MessageResponse.model_validate(message)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=MessageListResponse,
    summary="Get messages",
    description="Get messages for a conversation with pagination.",
)
async def get_messages(
    conversation_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageListResponse:
    """Get messages for a conversation ordered by creation time."""
    # Verify conversation exists
    tracker = ConversationTracker(db)
    try:
        await tracker.get(conversation_id)
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    queue = MessageQueue(db)
    messages, total = await queue.list_messages(
        conversation_id=conversation_id,
        page=page,
        page_size=page_size,
    )

    return MessageListResponse(
        items=[MessageResponse.model_validate(m) for m in messages],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


# =========================================================================
# Interrupt Endpoint (Non-Negotiable #14)
# =========================================================================


@router.post(
    "/conversations/{conversation_id}/interrupt",
    response_model=ConversationResponse,
    summary="Interrupt conversation",
    description="Human-in-the-loop interrupt. Pauses the conversation and sends "
    "an interrupt message. Non-Negotiable #14.",
)
async def interrupt_conversation(
    conversation_id: UUID,
    payload: ConversationInterrupt,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationResponse:
    """Pause a conversation via human-in-the-loop interrupt."""
    tracker = ConversationTracker(db)
    queue = MessageQueue(db)

    # Validate conversation exists and is active
    try:
        conversation = await tracker.get_active(conversation_id)
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    except ConversationInactiveError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Pause conversation
    conversation = await tracker.pause(conversation_id, reason=payload.reason)

    # Create interrupt system message via queue
    await queue.enqueue(
        conversation_id=conversation_id,
        content=f"[INTERRUPT] {payload.reason}",
        sender_type="system",
        sender_id=payload.interrupted_by,
        processing_lane="system",
        queue_mode="interrupt",
        message_type="interrupt",
    )

    # Increment message count for the interrupt message
    await tracker.increment_message_count(conversation_id)

    await db.commit()
    await db.refresh(conversation)

    logger.info(
        "Conversation interrupted: id=%s, by=%s, reason=%s",
        conversation_id,
        payload.interrupted_by,
        payload.reason,
    )
    return ConversationResponse.model_validate(conversation)
