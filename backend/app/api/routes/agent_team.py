"""
=========================================================================
Multi-Agent Team Engine API Routes (ADR-056/EP-07)
SDLC Orchestrator - Sprint 176 (Multi-Agent Foundation)

Version: 1.0.0
Date: 2026-02-18
Status: ACTIVE - Sprint 176
Authority: CTO Approved (ADR-056, EP-07)
Reference: ADR-056-Multi-Agent-Team-Engine.md
Reference: API-Specification.md v3.6.0

Purpose:
- 5 P0 endpoints for Multi-Agent Team Engine CRUD + messaging
- Agent definition lifecycle (create, list, get, update)
- Conversation management (start, list, get, interrupt)
- Message handling (send, list) with lane-based processing

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

Zero Mock Policy: Production-ready FastAPI endpoint implementation
=========================================================================
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.agent_definition import AgentDefinition
from app.models.agent_conversation import AgentConversation
from app.models.agent_message import AgentMessage
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
    "Snapshot Precedence: these values become defaults for new conversations.",
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

    # Check for duplicate agent name within project
    existing = await db.execute(
        select(AgentDefinition).where(
            and_(
                AgentDefinition.project_id == payload.project_id,
                AgentDefinition.agent_name == payload.agent_name,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agent '{payload.agent_name}' already exists in this project",
        )

    definition = AgentDefinition(
        id=uuid4(),
        project_id=payload.project_id,
        team_id=payload.team_id,
        agent_name=payload.agent_name,
        sdlc_role=payload.sdlc_role.value,
        provider=payload.provider,
        model=payload.model,
        system_prompt=payload.system_prompt,
        working_directory=payload.working_directory,
        max_tokens=payload.max_tokens,
        temperature=payload.temperature,
        queue_mode=payload.queue_mode.value,
        session_scope=payload.session_scope.value,
        max_delegation_depth=payload.max_delegation_depth,
        allowed_tools=payload.allowed_tools,
        denied_tools=payload.denied_tools,
        can_spawn_subagent=payload.can_spawn_subagent,
        allowed_paths=payload.allowed_paths,
        reflect_frequency=payload.reflect_frequency,
        is_active=True,
        config=payload.config,
    )

    db.add(definition)
    await db.commit()
    await db.refresh(definition)

    logger.info("Created agent definition: id=%s, name=%s", definition.id, definition.agent_name)
    return AgentDefinitionResponse.model_validate(definition)


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
    conditions = [AgentDefinition.project_id == project_id]

    if sdlc_role:
        conditions.append(AgentDefinition.sdlc_role == sdlc_role)
    if is_active is not None:
        conditions.append(AgentDefinition.is_active == is_active)

    # Count total
    count_query = select(func.count()).select_from(AgentDefinition).where(and_(*conditions))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch page
    query = (
        select(AgentDefinition)
        .where(and_(*conditions))
        .order_by(AgentDefinition.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    definitions = result.scalars().all()

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
    result = await db.execute(
        select(AgentDefinition).where(AgentDefinition.id == definition_id)
    )
    definition = result.scalar_one_or_none()

    if not definition:
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
    "NOTE: Changes do NOT affect running conversations (Snapshot Precedence).",
)
async def update_agent_definition(
    definition_id: UUID,
    payload: AgentDefinitionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentDefinitionResponse:
    """Update agent definition fields. Running conversations are unaffected."""
    result = await db.execute(
        select(AgentDefinition).where(AgentDefinition.id == definition_id)
    )
    definition = result.scalar_one_or_none()

    if not definition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent definition {definition_id} not found",
        )

    # Apply partial update
    update_data = payload.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        if field_name == "sdlc_role" and value is not None:
            setattr(definition, field_name, value.value)
        elif field_name == "queue_mode" and value is not None:
            setattr(definition, field_name, value.value)
        elif field_name == "session_scope" and value is not None:
            setattr(definition, field_name, value.value)
        else:
            setattr(definition, field_name, value)

    await db.commit()
    await db.refresh(definition)

    logger.info("Updated agent definition: id=%s", definition.id)
    return AgentDefinitionResponse.model_validate(definition)


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
    # Fetch agent definition for snapshotting
    result = await db.execute(
        select(AgentDefinition).where(AgentDefinition.id == payload.agent_definition_id)
    )
    definition = result.scalar_one_or_none()

    if not definition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent definition {payload.agent_definition_id} not found",
        )

    # Validate project_id matches definition's project_id
    if definition.project_id != payload.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="project_id does not match agent definition's project",
        )

    if not definition.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent definition {payload.agent_definition_id} is inactive",
        )

    # Validate delegation depth for subagent conversations (Nanobot N2)
    delegation_depth = 0
    if payload.parent_conversation_id:
        parent_result = await db.execute(
            select(AgentConversation).where(
                AgentConversation.id == payload.parent_conversation_id
            )
        )
        parent = parent_result.scalar_one_or_none()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent conversation {payload.parent_conversation_id} not found",
            )
        delegation_depth = parent.delegation_depth + 1

        if delegation_depth > definition.max_delegation_depth:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Delegation depth {delegation_depth} exceeds max "
                    f"{definition.max_delegation_depth} for agent '{definition.agent_name}'"
                ),
            )

    # Create conversation with Snapshot Precedence (ADR-056 Decision 1)
    conversation = AgentConversation(
        id=uuid4(),
        project_id=payload.project_id,
        agent_definition_id=definition.id,
        parent_conversation_id=payload.parent_conversation_id,
        delegation_depth=delegation_depth,
        initiator_type=payload.initiator_type.value,
        initiator_id=payload.initiator_id,
        channel=payload.channel.value,
        # Snapshotted from definition (ADR-056 Decision 1)
        session_scope=definition.session_scope,
        queue_mode=definition.queue_mode,
        max_messages=definition.config.get("max_messages", 50),  # Non-Negotiable #9
        max_budget_cents=definition.config.get("max_budget_cents", 1000),
        # Defaults
        status="active",
        metadata_=payload.metadata,
    )

    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    logger.info(
        "Started conversation: id=%s, agent=%s, depth=%d",
        conversation.id,
        definition.agent_name,
        delegation_depth,
    )
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
    conditions = [AgentConversation.project_id == project_id]

    if status_filter:
        conditions.append(AgentConversation.status == status_filter)

    count_query = select(func.count()).select_from(AgentConversation).where(and_(*conditions))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = (
        select(AgentConversation)
        .where(and_(*conditions))
        .order_by(AgentConversation.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    conversations = result.scalars().all()

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
    result = await db.execute(
        select(AgentConversation).where(AgentConversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
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
    # Validate conversation exists and is active
    conv_result = await db.execute(
        select(AgentConversation).where(AgentConversation.id == conversation_id)
    )
    conversation = conv_result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    if conversation.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Conversation is '{conversation.status}', cannot send messages",
        )

    # Loop guard: check max_messages (Non-Negotiable #9)
    if conversation.total_messages >= conversation.max_messages:
        conversation.status = "max_reached"
        conversation.completed_at = datetime.utcnow()
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Conversation reached max messages ({conversation.max_messages})",
        )

    # Budget circuit breaker (Non-Negotiable #13)
    if conversation.current_cost_cents >= conversation.max_budget_cents:
        conversation.status = "max_reached"
        conversation.completed_at = datetime.utcnow()
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Conversation budget exceeded (${conversation.max_budget_cents / 100:.2f})",
        )

    # Idempotency check (dedupe_key)
    if payload.dedupe_key:
        existing = await db.execute(
            select(AgentMessage).where(AgentMessage.dedupe_key == payload.dedupe_key)
        )
        existing_msg = existing.scalar_one_or_none()
        if existing_msg:
            return MessageResponse.model_validate(existing_msg)

    # Determine processing lane (agent-specific for serialization)
    # Fetch the agent definition to build the lane name
    def_result = await db.execute(
        select(AgentDefinition).where(
            AgentDefinition.id == conversation.agent_definition_id
        )
    )
    agent_def = def_result.scalar_one_or_none()
    processing_lane = f"agent:{agent_def.agent_name}" if agent_def else "main"

    # Create message with Lane Contract fields
    correlation_id = uuid4()
    message = AgentMessage(
        id=uuid4(),
        conversation_id=conversation_id,
        sender_type=payload.sender_type.value,
        sender_id=payload.sender_id,
        recipient_id=payload.recipient_id,
        content=payload.content,
        mentions=payload.mentions,
        message_type=payload.message_type.value,
        queue_mode=conversation.queue_mode,
        processing_status="pending",
        processing_lane=processing_lane,
        dedupe_key=payload.dedupe_key,
        correlation_id=correlation_id,
    )

    db.add(message)

    # Increment conversation message count
    conversation.total_messages += 1

    await db.commit()
    await db.refresh(message)

    logger.info(
        "Message sent: id=%s, conv=%s, lane=%s, correlation=%s",
        message.id,
        conversation_id,
        processing_lane,
        correlation_id,
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
    conv_result = await db.execute(
        select(AgentConversation).where(AgentConversation.id == conversation_id)
    )
    if not conv_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    conditions = [AgentMessage.conversation_id == conversation_id]

    count_query = select(func.count()).select_from(AgentMessage).where(and_(*conditions))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = (
        select(AgentMessage)
        .where(and_(*conditions))
        .order_by(AgentMessage.created_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    messages = result.scalars().all()

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
    result = await db.execute(
        select(AgentConversation).where(AgentConversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    if conversation.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot interrupt conversation in '{conversation.status}' status",
        )

    # Update conversation status
    conversation.status = "paused_by_human"

    # Create interrupt system message
    interrupt_message = AgentMessage(
        id=uuid4(),
        conversation_id=conversation_id,
        sender_type="system",
        sender_id=payload.interrupted_by,
        content=f"[INTERRUPT] {payload.reason}",
        mentions=[],
        message_type="interrupt",
        queue_mode="interrupt",
        processing_status="completed",
        processing_lane="system",
        correlation_id=uuid4(),
    )

    db.add(interrupt_message)
    conversation.total_messages += 1

    await db.commit()
    await db.refresh(conversation)

    logger.info(
        "Conversation interrupted: id=%s, by=%s, reason=%s",
        conversation_id,
        payload.interrupted_by,
        payload.reason,
    )
    return ConversationResponse.model_validate(conversation)
