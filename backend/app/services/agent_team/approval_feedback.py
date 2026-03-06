"""Approval Feedback Service — Sprint 220 (P4 Human-in-the-Loop).

Extends magic_link gate approval with structured feedback capture.
Stores feedback in agent_messages.metadata_["approval_feedback"] (S218 column).
Injects <human_feedback> XML into next agent turn via context_injector.

Usage:
    service = ApprovalFeedbackService(db)
    await service.approve_with_feedback(conversation_id, feedback_text, user_id)
    await service.reject_with_feedback(conversation_id, reason, user_id)

References:
- ADR-072, Sprint 220 Plan S220-03
- CoPaw magic_link pattern (ADR-064, FR-047)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_conversation import AgentConversation
from app.models.agent_message import AgentMessage

logger = logging.getLogger(__name__)


class ApprovalFeedbackService:
    """Captures structured approval/rejection feedback for agent conversations.

    Stores feedback as a system message with metadata for traceability.
    The context_injector.build_feedback_md() reads this metadata to inject
    <human_feedback> into the agent's next turn.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def approve_with_feedback(
        self,
        conversation_id: UUID,
        feedback_text: str = "",
        user_id: UUID | None = None,
    ) -> AgentMessage:
        """Record approval with optional feedback text.

        Creates a system message in the conversation with approval metadata.
        The agent will see this feedback via <human_feedback> context injection.

        Args:
            conversation_id: Conversation to approve.
            feedback_text: Optional feedback text (e.g., "Good approach, proceed").
            user_id: User performing the approval.

        Returns:
            The created system message.

        Raises:
            ValueError: If conversation not found or not active.
        """
        return await self._record_feedback(
            conversation_id=conversation_id,
            action="approved",
            feedback_text=feedback_text,
            user_id=user_id,
        )

    async def reject_with_feedback(
        self,
        conversation_id: UUID,
        reason: str = "",
        user_id: UUID | None = None,
    ) -> AgentMessage:
        """Record rejection with reason.

        Creates a system message with rejection metadata.
        Agent context will include: "Please revise your approach and try again."

        Args:
            conversation_id: Conversation to reject.
            reason: Rejection reason (e.g., "Security concern in line 42").
            user_id: User performing the rejection.

        Returns:
            The created system message.

        Raises:
            ValueError: If conversation not found or not active.
        """
        return await self._record_feedback(
            conversation_id=conversation_id,
            action="rejected",
            feedback_text=reason,
            user_id=user_id,
        )

    async def get_latest_feedback(
        self,
        conversation_id: UUID,
    ) -> dict | None:
        """Get the most recent approval feedback for a conversation.

        Args:
            conversation_id: Conversation to check.

        Returns:
            Feedback dict with action, feedback_text, user_id, timestamp;
            or None if no feedback exists.
        """
        result = await self.db.execute(
            select(AgentMessage)
            .where(
                and_(
                    AgentMessage.conversation_id == conversation_id,
                    AgentMessage.message_type == "system",
                    AgentMessage.processing_status == "completed",
                )
            )
            .order_by(desc(AgentMessage.created_at))
            .limit(10)
        )
        messages = list(result.scalars().all())

        for msg in messages:
            meta = msg.metadata_ if isinstance(msg.metadata_, dict) else {}
            feedback = meta.get("approval_feedback")
            if feedback:
                return feedback

        return None

    async def _record_feedback(
        self,
        conversation_id: UUID,
        action: str,
        feedback_text: str,
        user_id: UUID | None,
    ) -> AgentMessage:
        """Internal: create system message with approval feedback metadata.

        Args:
            conversation_id: Conversation ID.
            action: "approved" or "rejected".
            feedback_text: Human-provided feedback text.
            user_id: User performing the action.

        Returns:
            Created AgentMessage.

        Raises:
            ValueError: If conversation not found or not active.
        """
        # Verify conversation exists and is active
        conv_result = await self.db.execute(
            select(AgentConversation).where(
                AgentConversation.id == conversation_id
            )
        )
        conv = conv_result.scalar_one_or_none()
        if conv is None:
            raise ValueError(f"Conversation not found: {conversation_id}")
        if conv.status not in ("active", "paused"):
            raise ValueError(
                f"Conversation {conversation_id} is {conv.status}, "
                "cannot record feedback"
            )

        now = datetime.now(timezone.utc)
        feedback_data = {
            "action": action,
            "feedback_text": feedback_text.strip() if feedback_text else "",
            "user_id": str(user_id) if user_id else None,
            "timestamp": now.isoformat(),
        }

        # Build human-readable content
        content_parts = [f"Human {action} this work."]
        if feedback_text and feedback_text.strip():
            content_parts.append(f"Feedback: {feedback_text.strip()}")
        if action == "rejected":
            content_parts.append(
                "Please revise your approach based on this feedback and try again."
            )

        message = AgentMessage(
            id=uuid4(),
            conversation_id=conversation_id,
            sender_type="system",
            sender_id="approval_feedback",
            recipient_id=None,
            content="\n".join(content_parts),
            mentions=[],
            metadata_={"approval_feedback": feedback_data},
            message_type="system",
            queue_mode="queue",
            processing_status="completed",
            processing_lane="main",
            correlation_id=uuid4(),
        )
        self.db.add(message)
        await self.db.flush()

        logger.info(
            "TRACE_FEEDBACK: %s conv=%s user=%s text_len=%d",
            action,
            conversation_id,
            user_id,
            len(feedback_text or ""),
        )

        return message
