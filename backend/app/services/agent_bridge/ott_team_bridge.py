"""
OTT Team Bridge — Sprint 200 (A-01/A-05/A-06).

Routes multi-agent intents from OTT channels to the Team Orchestrator.
Handles conversation creation, message enqueuing, pipeline processing,
progress streaming, and result delivery back to the OTT channel.

Architecture:
    ai_response_handler detects multi-agent intent
        → ott_team_bridge.handle_agent_team_request()
            → ConversationTracker.create() / find existing
            → MessageQueue.enqueue()
            → TeamOrchestrator.process_next()
            → telegram_responder.send_progress_message()
            → telegram_responder.send_result_message()

DB Session: Creates a standalone AsyncSession via AsyncSessionLocal (same
pattern as governance_action_handler.py — fire-and-forget context).

Sprint 200 — Track A: Agent Team OTT Integration
ADR-056: Snapshot Precedence + Lane Contract
ADR-060: Channel-agnostic OrchestratorMessage
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_definition import AgentDefinition
from app.services.agent_team.agent_seed_service import AgentSeedService
from app.services.agent_team.conversation_tracker import (
    ConversationTracker,
    LimitExceededError,
    BudgetStatus,
)
from app.services.agent_team.message_queue import MessageQueue
from app.services.agent_team.team_orchestrator import TeamOrchestrator
from app.services.agent_team.team_presets import get_preset, TEAM_PRESETS
from app.services.agent_team.output_scrubber import OutputScrubber
from app.utils.redis import get_redis_client

logger = logging.getLogger(__name__)

_scrubber = OutputScrubber()

# Default project for OTT users (configured via env var)
_DEFAULT_PROJECT_ID: str = os.getenv("OTT_DEFAULT_PROJECT_ID", "")


# ── Sprint 200 C-01: Channel-agnostic send helpers ──


async def _ott_send_progress(
    channel: str, bot_token: str, chat_id: str | int, text: str,
) -> bool:
    """Route progress message to the correct OTT channel (C-01)."""
    if channel == "zalo":
        from app.services.agent_bridge.zalo_responder import send_progress_message
        return await send_progress_message(user_id=str(chat_id), text=text)
    from app.services.agent_bridge.telegram_responder import send_progress_message
    return await send_progress_message(bot_token, chat_id, text)


async def _ott_send_result(
    channel: str,
    bot_token: str,
    chat_id: str | int,
    agent_name: str,
    content: str,
    tokens_used: int = 0,
    cost_cents: int = 0,
    elapsed_ms: int = 0,
    provider: str = "",
) -> bool:
    """Route result message to the correct OTT channel (C-01/C-04)."""
    if channel == "zalo":
        from app.services.agent_bridge.zalo_responder import send_result_message
        return await send_result_message(
            user_id=str(chat_id), agent_name=agent_name, content=content,
            tokens_used=tokens_used, cost_cents=cost_cents,
            elapsed_ms=elapsed_ms, provider=provider,
        )
    from app.services.agent_bridge.telegram_responder import send_result_message
    return await send_result_message(
        bot_token, chat_id, agent_name=agent_name, content=content,
        tokens_used=tokens_used, cost_cents=cost_cents,
        elapsed_ms=elapsed_ms, provider=provider,
    )

# Redis key patterns for OTT ↔ conversation mapping
_ACTIVE_CONV_KEY = "ott_active_conv:{chat_id}"
_USER_PROJECT_KEY = "ott_user_project:{chat_id}"

# Conversation TTL in Redis (24 hours — same as session)
_CONV_TTL_SECONDS: int = 86400

# Default preset for OTT agent team invocation
_DEFAULT_PRESET: str = "startup-2"

# Multi-agent intent keywords (bilingual: English + Vietnamese)
MULTI_AGENT_KEYWORDS: tuple[str, ...] = (
    # Code generation
    "generate code", "tạo code", "tạo mã", "viết code",
    "create code", "write code", "code generation",
    # Agent team invocation
    "use coder team", "use review team", "use full team",
    "dùng team coder", "dùng team review",
    "start agent", "khởi chạy agent",
    # Analysis + generation
    "analyze and generate", "phân tích và tạo",
    "analyze my", "phân tích",
    "generate models", "generate api", "generate tests",
    "tạo models", "tạo api", "tạo tests",
    # Sprint 200 specific
    "agent team", "nhóm agent", "multi-agent",
)

# Preset selection keywords (A-02)
_PRESET_KEYWORDS: dict[str, str] = {
    "solo": "solo-dev",
    "coder": "startup-2",
    "review": "review-pair",
    "enterprise": "enterprise-3",
    "full": "full-sprint",
    "full team": "full-sprint",
    "full sprint": "full-sprint",
    "startup": "startup-2",
}


def is_multi_agent_intent(text: str) -> bool:
    """
    Detect multi-agent intent in user message (Sprint 200 A-01).

    Returns True if the message contains keywords that should route to
    the multi-agent team pipeline instead of single-turn AI chat.
    """
    text_lower = text.lower().strip()
    return any(kw in text_lower for kw in MULTI_AGENT_KEYWORDS)


def _detect_preset(text: str) -> str:
    """
    Detect team preset from user message (Sprint 200 A-02).

    Returns preset name if detected, defaults to _DEFAULT_PRESET.
    """
    text_lower = text.lower()
    for keyword, preset_name in _PRESET_KEYWORDS.items():
        if keyword in text_lower:
            return preset_name
    return _DEFAULT_PRESET


async def _resolve_project_id(chat_id: str | int) -> UUID | None:
    """
    Resolve project_id for an OTT user.

    Priority:
    1. Redis binding (user previously selected a project via chat)
    2. Environment variable OTT_DEFAULT_PROJECT_ID
    3. None (caller handles missing project)
    """
    try:
        redis = await get_redis_client()
        cached = await redis.get(_USER_PROJECT_KEY.format(chat_id=chat_id))
        if cached:
            return UUID(cached.decode() if isinstance(cached, bytes) else cached)
    except Exception as exc:
        logger.warning(
            "ott_team_bridge: project resolution failed chat_id=%s error=%s",
            chat_id,
            str(exc),
        )

    if _DEFAULT_PROJECT_ID:
        try:
            return UUID(_DEFAULT_PROJECT_ID)
        except ValueError:
            logger.error(
                "ott_team_bridge: invalid OTT_DEFAULT_PROJECT_ID=%s",
                _DEFAULT_PROJECT_ID,
            )

    return None


async def _get_or_create_active_conversation(
    chat_id: str | int,
    redis: Any,
) -> UUID | None:
    """Check Redis for an active agent conversation for this chat."""
    try:
        cached = await redis.get(_ACTIVE_CONV_KEY.format(chat_id=chat_id))
        if cached:
            return UUID(cached.decode() if isinstance(cached, bytes) else cached)
    except Exception:
        pass
    return None


async def _store_active_conversation(
    chat_id: str | int,
    conversation_id: UUID,
) -> None:
    """Store the active conversation mapping in Redis."""
    try:
        redis = await get_redis_client()
        await redis.set(
            _ACTIVE_CONV_KEY.format(chat_id=chat_id),
            str(conversation_id),
            ex=_CONV_TTL_SECONDS,
        )
    except Exception as exc:
        logger.warning(
            "ott_team_bridge: failed to store conv mapping chat_id=%s error=%s",
            chat_id,
            str(exc),
        )


async def _clear_active_conversation(chat_id: str | int) -> None:
    """Clear the active conversation mapping in Redis."""
    try:
        redis = await get_redis_client()
        await redis.delete(_ACTIVE_CONV_KEY.format(chat_id=chat_id))
    except Exception:
        pass


async def _find_entry_agent(
    db: AsyncSession,
    project_id: UUID,
    preset_name: str,
) -> AgentDefinition | None:
    """
    Find the entry-point agent for a preset.

    For "startup-2" → coder agent.
    For "enterprise-3" → architect agent.
    For "full-sprint" → pm agent.
    For "solo-dev" → coder agent.
    For "review-pair" → reviewer agent.
    """
    preset = get_preset(preset_name)
    if not preset:
        return None

    entry_role = preset.roles[0]  # First role in preset is the entry point

    result = await db.execute(
        select(AgentDefinition).where(
            and_(
                AgentDefinition.project_id == project_id,
                AgentDefinition.sdlc_role == entry_role,
                AgentDefinition.is_active.is_(True),
            )
        ).limit(1)
    )
    definition = result.scalar_one_or_none()

    if definition:
        return definition

    # No agent found — seed the project agents first
    logger.info(
        "ott_team_bridge: seeding agents for project=%s preset=%s",
        project_id,
        preset_name,
    )
    seed_svc = AgentSeedService(db)
    await seed_svc.seed_project_agents(project_id)
    await db.commit()

    # Re-query after seeding
    result = await db.execute(
        select(AgentDefinition).where(
            and_(
                AgentDefinition.project_id == project_id,
                AgentDefinition.sdlc_role == entry_role,
                AgentDefinition.is_active.is_(True),
            )
        ).limit(1)
    )
    return result.scalar_one_or_none()


async def handle_agent_team_request(
    chat_id: str | int,
    text: str,
    bot_token: str,
    sender_id: str,
    channel: str = "telegram",
) -> bool:
    """
    Handle a multi-agent team request from OTT chat (Sprint 200 A-01).

    This is the main entry point called by ai_response_handler when a
    multi-agent intent is detected. Runs in fire-and-forget context.

    Flow:
        1. Resolve project_id for the OTT user
        2. Detect team preset from message text
        3. Find or create agent conversation (A-06: multi-turn)
        4. Enqueue user message into agent conversation
        5. Process via TeamOrchestrator (agent pipeline)
        6. Stream progress + deliver result back to OTT channel

    Args:
        chat_id: OTT chat/user ID.
        text: User message text.
        bot_token: Bot API token (Telegram only; empty for Zalo).
        sender_id: OTT user ID.
        channel: OTT channel ("telegram" or "zalo").

    Returns:
        True if agent team pipeline ran, False on setup failure.
    """
    # Step 1: Resolve project
    project_id = await _resolve_project_id(chat_id)
    if not project_id:
        await _ott_send_progress(
            channel,
            bot_token,
            chat_id,
            "\u26a0\ufe0f No project configured for this chat.\n\n"
            "Set project: send your project UUID or ask admin to configure "
            "OTT_DEFAULT_PROJECT_ID.\n\n"
            "Chua co du an. Gui UUID du an hoac lien he admin.",
        )
        return False

    # Step 2: Detect preset
    preset_name = _detect_preset(text)

    # Step 3-6: Process in DB session
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            return await _process_agent_request(
                db=db,
                project_id=project_id,
                chat_id=chat_id,
                text=text,
                bot_token=bot_token,
                sender_id=sender_id,
                preset_name=preset_name,
                channel=channel,
            )
        except Exception as exc:
            logger.error(
                "ott_team_bridge: pipeline error chat_id=%s error=%s",
                chat_id,
                str(exc),
                exc_info=True,
            )
            await _ott_send_progress(
                channel,
                bot_token,
                chat_id,
                "\u274c Agent pipeline error. Please try again.\n"
                f"Error: {str(exc)[:200]}",
            )
            return False


async def _process_agent_request(
    db: AsyncSession,
    project_id: UUID,
    chat_id: str | int,
    text: str,
    bot_token: str,
    sender_id: str,
    preset_name: str,
    channel: str = "telegram",
) -> bool:
    """
    Core agent team processing pipeline (DB session available).

    Steps:
        1. Find entry-point agent definition
        2. Find or create conversation (multi-turn: A-06)
        3. Send initial acknowledgment to user
        4. Enqueue user message
        5. Process via TeamOrchestrator
        6. Deliver result to OTT channel
    """
    redis = await get_redis_client()
    start_time = time.monotonic()

    # Step 1: Find entry-point agent
    definition = await _find_entry_agent(db, project_id, preset_name)
    if not definition:
        await _ott_send_progress(
            channel,
            bot_token,
            chat_id,
            "\u26a0\ufe0f No agent definitions found for this project.\n"
            "Please seed agents first via API or Web Dashboard.",
        )
        return False

    # Step 2: Check for existing active conversation (A-06 multi-turn)
    tracker = ConversationTracker(db)
    existing_conv_id = await _get_or_create_active_conversation(chat_id, redis)

    conversation = None
    is_new_conversation = True

    if existing_conv_id:
        try:
            conversation = await tracker.get_active(existing_conv_id)
            is_new_conversation = False
            logger.info(
                "ott_team_bridge: resuming existing conversation=%s chat_id=%s",
                conversation.id,
                chat_id,
            )
        except Exception:
            # Conversation no longer active — create new one
            await _clear_active_conversation(chat_id)

    if conversation is None:
        conversation = await tracker.create(
            definition=definition,
            project_id=project_id,
            initiator_type="ott_channel",
            initiator_id=str(sender_id),
            channel=channel,
            metadata={
                "ott_chat_id": str(chat_id),
                "preset": preset_name,
                "source": "ott_team_bridge",
            },
        )
        await db.commit()
        await _store_active_conversation(chat_id, conversation.id)

    # Step 3: Send initial acknowledgment
    preset = get_preset(preset_name)
    preset_desc = preset.description if preset else preset_name
    roles_str = ", ".join(preset.roles) if preset else "coder"

    if is_new_conversation:
        await _ott_send_progress(
            channel,
            bot_token,
            chat_id,
            f"\U0001f680 Starting Agent Team: {preset_desc}\n"
            f"Roles: {roles_str}\n"
            f"Processing: \"{text[:80]}{'...' if len(text) > 80 else ''}\"",
        )
    else:
        await _ott_send_progress(
            channel,
            bot_token,
            chat_id,
            f"\U0001f504 Continuing conversation with {definition.agent_name}...",
        )

    # Step 4: Enqueue user message
    queue = MessageQueue(db, redis=redis)
    processing_lane = f"agent:{definition.sdlc_role}"

    message = await queue.enqueue(
        conversation_id=conversation.id,
        content=text,
        sender_type="user",
        sender_id=str(sender_id),
        processing_lane=processing_lane,
        queue_mode=conversation.queue_mode,
        message_type="user_input",
    )
    await db.commit()

    # Step 5: Process via TeamOrchestrator
    orchestrator = TeamOrchestrator(db, redis=redis)

    try:
        result = await orchestrator.process_next(processing_lane)
    except LimitExceededError as exc:
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        await _ott_send_progress(
            channel,
            bot_token,
            chat_id,
            f"\u26a0\ufe0f Budget/message limit reached.\n{str(exc)[:200]}\n"
            f"Time: {elapsed_ms}ms",
        )
        await _clear_active_conversation(chat_id)
        return False

    if result is None:
        await _ott_send_progress(
            channel,
            bot_token,
            chat_id,
            "\u26a0\ufe0f No message to process. Please try again.",
        )
        return False

    await db.commit()
    elapsed_ms = int((time.monotonic() - start_time) * 1000)

    # Sprint 200 B-01/B-03/B-04: Record cost and check budget status
    budget_result = None
    if result.cost_cents > 0:
        provider_info_budget = result.provider_used or "unknown"
        budget_result = await tracker.record_token_usage(
            conversation_id=conversation.id,
            input_tokens=result.tokens_used // 2,  # Approximate split
            output_tokens=result.tokens_used - (result.tokens_used // 2),
            cost_cents=result.cost_cents,
            provider=provider_info_budget,
        )
        await db.commit()

    # Step 6: Deliver result
    if result.success:
        # Fetch the response message content
        from app.models.agent_message import AgentMessage

        response_msg = None
        if result.response_message_id:
            resp_result = await db.execute(
                select(AgentMessage).where(
                    AgentMessage.id == result.response_message_id
                )
            )
            response_msg = resp_result.scalar_one_or_none()

        response_text = response_msg.content if response_msg else "(no response)"

        # Scrub credentials from output (ADR-058)
        clean_text, violations = _scrubber.scrub(response_text)
        if violations:
            logger.warning(
                "ott_team_bridge: scrubbed %d violations from agent response",
                len(violations),
            )

        # Format result
        provider_info = f"{result.provider_used}" if result.provider_used else "unknown"
        model_info = f" ({result.model_used})" if result.model_used else ""

        await _ott_send_result(
            channel,
            bot_token,
            chat_id,
            agent_name=definition.agent_name,
            content=clean_text,
            tokens_used=result.tokens_used,
            cost_cents=result.cost_cents,
            elapsed_ms=elapsed_ms,
            provider=f"{provider_info}{model_info}",
        )

        # Sprint 200 B-03: Send budget warning at 80%
        if budget_result and budget_result.status == BudgetStatus.WARNING:
            await _ott_send_progress(
                channel,
                bot_token,
                chat_id,
                f"\u26a0\ufe0f {budget_result.message}\n"
                f"Canh bao: Ngan sach da su dung {budget_result.percentage}%.",
            )

        # Sprint 200 B-04: Notify hard stop at 100%
        if budget_result and budget_result.status == BudgetStatus.EXCEEDED:
            await _ott_send_progress(
                channel,
                bot_token,
                chat_id,
                f"\U0001f6d1 {budget_result.message}\n"
                "Conversation paused. Contact admin to increase budget.\n"
                "Hoi thoai da tam dung. Lien he admin de tang ngan sach.",
            )
            await _clear_active_conversation(chat_id)

        # Route @mentions to next agents (delegation chain)
        if result.mentions_routed:
            await _ott_send_progress(
                channel,
                bot_token,
                chat_id,
                f"\U0001f517 Routing to: {', '.join(result.mentions_routed)}",
            )

        logger.info(
            "ott_team_bridge: pipeline complete chat_id=%s conv=%s "
            "tokens=%d cost=%dc elapsed=%dms provider=%s budget=%s",
            chat_id,
            conversation.id,
            result.tokens_used,
            result.cost_cents,
            elapsed_ms,
            provider_info,
            budget_result.status.value if budget_result else "n/a",
        )
        return True

    else:
        error_detail = result.error or result.skipped_reason or "Unknown error"
        await _ott_send_progress(
            channel,
            bot_token,
            chat_id,
            f"\u274c Agent pipeline failed.\n"
            f"Reason: {error_detail[:300]}\n"
            f"Time: {elapsed_ms}ms",
        )
        return False


async def handle_interrupt(
    chat_id: str | int,
    bot_token: str,
    channel: str = "telegram",
) -> bool:
    """
    Interrupt the active agent conversation for a chat (Sprint 200 A-04).

    Called when user sends "stop" or "cancel" during an agent pipeline.

    Returns True if conversation was paused, False if no active conversation.
    """
    redis = await get_redis_client()
    conv_id = await _get_or_create_active_conversation(chat_id, redis)

    if not conv_id:
        await _ott_send_progress(
            channel,
            bot_token,
            chat_id,
            "No active agent conversation to stop.",
        )
        return False

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            tracker = ConversationTracker(db)
            await tracker.pause(conv_id, reason="User interrupted via OTT chat")
            await db.commit()
            await _clear_active_conversation(chat_id)

            await _ott_send_progress(
                channel,
                bot_token,
                chat_id,
                "\u23f9\ufe0f Agent conversation stopped.\n"
                "Send a new message to start a fresh conversation.",
            )
            logger.info(
                "ott_team_bridge: conversation interrupted chat_id=%s conv=%s",
                chat_id,
                conv_id,
            )
            return True
        except Exception as exc:
            logger.warning(
                "ott_team_bridge: interrupt failed chat_id=%s conv=%s error=%s",
                chat_id,
                conv_id,
                str(exc),
            )
            await _ott_send_progress(
                channel,
                bot_token,
                chat_id,
                f"\u26a0\ufe0f Failed to stop conversation: {str(exc)[:200]}",
            )
            return False
