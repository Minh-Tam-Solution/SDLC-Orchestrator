"""
=========================================================================
History Compactor — ADR-058 Pattern B (ZeroClaw)
SDLC Orchestrator - Sprint 179 (ZeroClaw Security Hardening)

Version: 1.0.0
Date: February 2026
Status: ACTIVE - Sprint 179
Authority: CTO Approved (ADR-058 Decision 2)
Reference: ADR-058-ZeroClaw-Best-Practice-Adoption.md

Purpose:
- Auto-summarize conversation history before it hits the hard message cap.
- Trigger: total_messages >= max_messages * 0.8  (80% threshold)
- Stale-guard: Skip if already compacted at same message count (±5).
- Summarize with LLM → preserve last 20 messages + inject 2K-char summary.
- Fallback: If LLM summarize fails → deterministic truncation (no exception).
- Injection: Summary prepended to system_prompt in team_orchestrator._build_llm_context().
- Storage: conversation.metadata_["compaction_summary"] + ["last_compacted_at"]

Summarizer prompt (ZeroClaw N5 verbatim):
  "Preserve: user preferences, commitments, decisions, unresolved tasks,
   key facts. Omit: filler, repeated chit-chat, verbose tool logs."

Integration:
  team_orchestrator._process() calls HistoryCompactor.maybe_compact()
  BEFORE Step 5 (_build_llm_context) if conversation is near limit.

References:
  - FR-044 History Compaction
  - ADR-058 Decision 2 (LOCKED)
  - ZeroClaw src/agent/loop_.rs (threshold 50 → summarize → keep 20 recent)
=========================================================================
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_conversation import AgentConversation
from app.models.agent_message import AgentMessage

logger = logging.getLogger(__name__)

# ── Constants (ADR-058 §2.3) ─────────────────────────────────────────────────

# Compact when message count reaches this fraction of max_messages.
COMPACTION_THRESHOLD_RATIO: float = 0.80

# Messages to keep verbatim (most recent) after compaction.
KEEP_RECENT: int = 20

# Maximum characters for the LLM-generated summary.
MAX_SUMMARY_CHARS: int = 2_000

# Stale-guard: skip re-compaction if message count grew by less than this.
STALE_GUARD_DELTA: int = 5

# Summarizer system prompt (ZeroClaw N5 verbatim).
_SUMMARIZER_PROMPT = (
    "You are a conversation summarizer. Summarize the following conversation "
    "history in at most 2000 characters. "
    "Preserve: user preferences, commitments, decisions, unresolved tasks, "
    "key facts. "
    "Omit: filler, repeated chit-chat, verbose tool logs. "
    "Output only the summary text."
)


class HistoryCompactor:
    """
    Auto-compacts conversation history to avoid the hard message cap.

    Call ``maybe_compact()`` before building LLM context. If compaction
    fires, the updated summary is stored in ``conversation.metadata_``.

    Usage::

        compactor = HistoryCompactor(db=db)
        summary = await compactor.maybe_compact(
            conversation=conv,
            agent_invoker=invoker,   # optional; fallback used if None
        )
        # summary is None if not triggered, str if compacted
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def should_compact(self, conversation: AgentConversation) -> bool:
        """
        Return True if compaction should fire for this conversation.

        Conditions:
        1. total_messages >= max_messages * COMPACTION_THRESHOLD_RATIO
        2. Stale-guard: current count has grown by >= STALE_GUARD_DELTA
           since the last compaction (avoids re-compacting on every message
           once we're near the cap).

        Args:
            conversation: Current AgentConversation ORM object.

        Returns:
            True if compaction should run, False to skip.
        """
        threshold = int(conversation.max_messages * COMPACTION_THRESHOLD_RATIO)
        if conversation.total_messages < threshold:
            return False

        # Stale-guard check
        raw_meta = conversation.metadata_
        meta: dict = raw_meta if isinstance(raw_meta, dict) else {}
        last_compacted_count: int = meta.get("last_compacted_messages", 0)
        if not isinstance(last_compacted_count, int):
            last_compacted_count = 0
        delta = conversation.total_messages - last_compacted_count
        if delta < STALE_GUARD_DELTA:
            logger.debug(
                "TRACE_COMPACTOR stale-guard: conv=%s, delta=%d (< %d), skip",
                conversation.id,
                delta,
                STALE_GUARD_DELTA,
            )
            return False

        return True

    async def maybe_compact(
        self,
        conversation: AgentConversation,
        agent_invoker: object | None = None,
    ) -> str | None:
        """
        Compact conversation history if threshold is reached.

        If compaction fires:
        1. Fetch all completed messages for the conversation.
        2. Attempt LLM summarization of older messages.
        3. Store summary in ``conversation.metadata_["compaction_summary"]``.
        4. Store current message count in ``["last_compacted_messages"]``.
        5. Return summary string.

        If threshold is not reached, return None (no-op).

        Args:
            conversation: Current AgentConversation instance (will be mutated).
            agent_invoker: Optional AgentInvoker for LLM summarization.
                           If None, fallback deterministic truncation is used.

        Returns:
            Summary string if compaction fired, None otherwise.
        """
        if not self.should_compact(conversation):
            return None

        logger.info(
            "TRACE_COMPACTOR: Compaction triggered — conv=%s, "
            "total_messages=%d, max=%d",
            conversation.id,
            conversation.total_messages,
            conversation.max_messages,
        )

        # Fetch all completed messages, oldest-first.
        result = await self.db.execute(
            select(AgentMessage)
            .where(AgentMessage.conversation_id == conversation.id)
            .where(AgentMessage.processing_status == "completed")
            .order_by(AgentMessage.created_at.asc())
        )
        all_msgs: list[AgentMessage] = list(result.scalars().all())

        if len(all_msgs) <= KEEP_RECENT:
            # Nothing to summarize — all messages fit in recent window.
            logger.debug(
                "TRACE_COMPACTOR: Not enough history to compact (n=%d <= %d)",
                len(all_msgs),
                KEEP_RECENT,
            )
            return None

        older_msgs = all_msgs[:-KEEP_RECENT]

        # Build text representation of older messages for summarization.
        older_text = self._messages_to_text(older_msgs)

        # Attempt LLM summarization; fall back to deterministic on failure.
        summary = await self._summarize(older_text, agent_invoker)

        # Persist summary in metadata_.
        await self._persist_summary(conversation, summary)

        logger.info(
            "TRACE_COMPACTOR: Compacted conv=%s — "
            "older_msgs=%d, summary_len=%d chars",
            conversation.id,
            len(older_msgs),
            len(summary),
        )

        return summary

    async def _summarize(
        self, text: str, agent_invoker: object | None
    ) -> str:
        """
        Attempt LLM summarization. Fall back to truncation on any failure.

        Args:
            text: Plain text of older messages to summarize.
            agent_invoker: AgentInvoker instance (or None).

        Returns:
            Summary string (≤ MAX_SUMMARY_CHARS).
        """
        if agent_invoker is None:
            logger.debug(
                "TRACE_COMPACTOR: No invoker — using fallback truncation"
            )
            return self._fallback_truncate(text)

        try:
            # Dynamic import avoids circular dependency.
            invoke = getattr(agent_invoker, "invoke", None)
            if invoke is None:
                return self._fallback_truncate(text)

            result = await invoke(
                messages=[{"role": "user", "content": text}],
                system_prompt=_SUMMARIZER_PROMPT,
                max_tokens=600,   # 600 tokens ≈ 2K chars
                temperature=0.3,  # Low temperature for factual summary
            )

            summary = getattr(result, "content", "")
            if not summary:
                return self._fallback_truncate(text)

            # Enforce character limit.
            return summary[:MAX_SUMMARY_CHARS]

        except Exception as exc:
            logger.warning(
                "TRACE_COMPACTOR: LLM summarization failed (%s) — "
                "falling back to truncation",
                exc,
            )
            return self._fallback_truncate(text)

    def _fallback_truncate(self, text: str) -> str:
        """
        Deterministic fallback: truncate text to MAX_SUMMARY_CHARS.

        Appends a sentinel so context consumers can detect truncation.

        Args:
            text: Full message text to truncate.

        Returns:
            Truncated string with ``[...truncated]`` suffix if needed.
        """
        if len(text) <= MAX_SUMMARY_CHARS:
            return text
        truncated = text[:MAX_SUMMARY_CHARS - 20]
        return truncated + "\n[...truncated]"

    @staticmethod
    def _messages_to_text(messages: list[AgentMessage]) -> str:
        """
        Convert list of AgentMessage ORM objects to plain text.

        Format: ``<role>: <content>`` per message, separated by newlines.
        """
        lines: list[str] = []
        for msg in messages:
            role = "assistant" if msg.sender_type == "agent" else "user"
            content = (msg.content or "").strip()
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    async def _persist_summary(
        self, conversation: AgentConversation, summary: str
    ) -> None:
        """
        Store compaction summary and current message count in metadata_.

        Keys written:
        - ``compaction_summary``: The summary text.
        - ``last_compacted_messages``: total_messages at compaction time.
        - ``last_compacted_at``: ISO 8601 UTC timestamp.
        - ``workspace_keys``: Active workspace keys at compaction time (Sprint 220).
        - ``workspace_key_count``: Number of active workspace keys (Sprint 220).

        Args:
            conversation: Conversation to update (mutated in-place).
            summary: Summary text to persist.
        """
        raw = conversation.metadata_
        meta: dict[str, Any] = dict(raw) if isinstance(raw, dict) else {}
        meta["compaction_summary"] = summary
        meta["last_compacted_messages"] = conversation.total_messages
        meta["last_compacted_at"] = datetime.now(timezone.utc).isoformat()

        # Sprint 220: Capture active workspace keys for cross-reference
        ws_keys = await self._get_workspace_keys(conversation.id)
        meta["workspace_keys"] = ws_keys
        meta["workspace_key_count"] = len(ws_keys)

        conversation.metadata_ = meta
        await self.db.flush()

    # ── Sprint 220: Workspace-Aware Compaction ────────────────────────────────

    # Regex to extract workspace key references: agent/artifact pattern
    _WORKSPACE_KEY_PATTERN = re.compile(r"\b(\w+/[\w.\-]+)\b")

    @staticmethod
    def extract_workspace_keys_from_text(text: str) -> list[str]:
        """
        Extract workspace key references from message text.

        Matches patterns like ``coder/main.py``, ``reviewer/feedback``,
        ``tester/results.json`` — the ``{agent}/{artifact}`` pattern.

        Args:
            text: Message text to scan.

        Returns:
            De-duplicated list of extracted key references.
        """
        matches = HistoryCompactor._WORKSPACE_KEY_PATTERN.findall(text)
        # De-duplicate while preserving order
        seen: set[str] = set()
        result: list[str] = []
        for m in matches:
            if m not in seen:
                seen.add(m)
                result.append(m)
        return result

    async def _get_workspace_keys(self, conversation_id: UUID) -> list[str]:
        """
        Get active workspace keys for a conversation.

        Uses SharedWorkspace.get_active_keys() to fetch current keys.
        Returns empty list if workspace has no items.

        Args:
            conversation_id: Conversation ID.

        Returns:
            List of active workspace key names.
        """
        try:
            from app.services.agent_team.shared_workspace import SharedWorkspace
            ws = SharedWorkspace(self.db, conversation_id)
            return await ws.get_active_keys()
        except Exception as exc:
            logger.warning(
                "TRACE_COMPACTOR: Failed to fetch workspace keys: %s", exc,
            )
            return []

    async def compact_with_workspace_preservation(
        self,
        conversation: AgentConversation,
        agent_invoker: object | None = None,
    ) -> str | None:
        """
        Workspace-aware compaction: extract referenced keys before summarizing.

        Same as maybe_compact() but additionally:
        1. Extracts workspace key references from older messages.
        2. Cross-checks against active workspace keys.
        3. Includes referenced workspace keys in metadata for traceability.

        Args:
            conversation: Current AgentConversation instance.
            agent_invoker: Optional AgentInvoker for LLM summarization.

        Returns:
            Summary string if compaction fired, None otherwise.
        """
        if not self.should_compact(conversation):
            return None

        # Fetch all completed messages, oldest-first
        result = await self.db.execute(
            select(AgentMessage)
            .where(AgentMessage.conversation_id == conversation.id)
            .where(AgentMessage.processing_status == "completed")
            .order_by(AgentMessage.created_at.asc())
        )
        all_msgs: list[AgentMessage] = list(result.scalars().all())

        if len(all_msgs) <= KEEP_RECENT:
            return None

        older_msgs = all_msgs[:-KEEP_RECENT]
        older_text = self._messages_to_text(older_msgs)

        # Extract workspace keys referenced in older messages
        referenced_keys = self.extract_workspace_keys_from_text(older_text)

        # Cross-check against active workspace keys
        active_keys = await self._get_workspace_keys(conversation.id)
        preserved_keys = [k for k in referenced_keys if k in active_keys]

        logger.info(
            "TRACE_COMPACTOR: workspace-aware compaction — conv=%s, "
            "referenced=%d, active=%d, preserved=%d",
            conversation.id,
            len(referenced_keys),
            len(active_keys),
            len(preserved_keys),
        )

        # Summarize
        summary = await self._summarize(older_text, agent_invoker)

        # Persist with workspace keys
        await self._persist_summary(conversation, summary)

        return summary
