"""Sprint 220 Tests — P5 Memory Enhancement + P4 Approval Feedback.

30 tests across 8 groups:
- S1: build_workspace_md (4 tests)
- S2: build_feedback_md (4 tests)
- S3: inject_context with conversation_id (3 tests)
- S4: extract_workspace_keys_from_text (4 tests)
- S5: compact_with_workspace_preservation (3 tests)
- S6: ApprovalFeedbackService (5 tests)
- S7: ApprovalAnalyticsService (4 tests)
- S8: Integration: feedback → context injection (3 tests)

References: ADR-072, Sprint 220 Plan S220-01 to S220-04, CTO F1 condition.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

# ── S1: build_workspace_md ────────────────────────────────────────────────────


class TestBuildWorkspaceMd:
    """S1: Context injector — build_workspace_md builder."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_conversation_id(self):
        """build_workspace_md returns '' when conversation_id is None."""
        from app.services.agent_team.context_injector import ContextInjector

        db = AsyncMock()
        injector = ContextInjector(db)
        result = await injector.build_workspace_md(None)
        assert result == ""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_items(self):
        """build_workspace_md returns '' when workspace has no active items."""
        from app.services.agent_team.context_injector import ContextInjector

        db = AsyncMock()
        injector = ContextInjector(db)
        conv_id = uuid4()

        with patch(
            "app.services.agent_team.shared_workspace.SharedWorkspace"
        ) as MockWS:
            mock_ws = AsyncMock()
            mock_ws.list_keys.return_value = []
            MockWS.return_value = mock_ws

            result = await injector.build_workspace_md(conv_id)
            assert result == ""

    @pytest.mark.asyncio
    async def test_renders_workspace_items(self):
        """build_workspace_md renders items with key, type, version, preview."""
        from app.services.agent_team.context_injector import ContextInjector

        db = AsyncMock()
        injector = ContextInjector(db)
        conv_id = uuid4()

        items = [
            {
                "item_key": "coder/main.py",
                "item_type": "code",
                "version": 2,
                "preview": "def main(): pass",
            },
            {
                "item_key": "reviewer/feedback",
                "item_type": "text",
                "version": 1,
                "preview": None,
            },
        ]

        with patch(
            "app.services.agent_team.shared_workspace.SharedWorkspace"
        ) as MockWS:
            mock_ws = AsyncMock()
            mock_ws.list_keys.return_value = items
            MockWS.return_value = mock_ws

            result = await injector.build_workspace_md(conv_id)
            assert "<workspace>" in result
            assert "</workspace>" in result
            assert "coder/main.py" in result
            assert "code" in result
            assert "v2" in result
            assert "def main(): pass" in result
            assert "reviewer/feedback" in result

    @pytest.mark.asyncio
    async def test_truncates_at_max_chars(self):
        """build_workspace_md truncates when items exceed MAX_WORKSPACE_CHARS."""
        from app.services.agent_team.context_injector import (
            MAX_WORKSPACE_CHARS,
            ContextInjector,
        )

        db = AsyncMock()
        injector = ContextInjector(db)
        conv_id = uuid4()

        # Generate many items to exceed 1500 chars
        items = [
            {
                "item_key": f"agent_{i}/artifact_{i}_long_name",
                "item_type": "text",
                "version": i,
                "preview": "x" * 50,
            }
            for i in range(50)
        ]

        with patch(
            "app.services.agent_team.shared_workspace.SharedWorkspace"
        ) as MockWS:
            mock_ws = AsyncMock()
            mock_ws.list_keys.return_value = items
            MockWS.return_value = mock_ws

            result = await injector.build_workspace_md(conv_id)
            assert "<workspace>" in result
            assert "more items not shown" in result


# ── S2: build_feedback_md ─────────────────────────────────────────────────────


class TestBuildFeedbackMd:
    """S2: Context injector — build_feedback_md builder."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_conversation_id(self):
        """build_feedback_md returns '' when conversation_id is None."""
        from app.services.agent_team.context_injector import ContextInjector

        db = AsyncMock()
        injector = ContextInjector(db)
        result = await injector.build_feedback_md(None)
        assert result == ""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_feedback(self):
        """build_feedback_md returns '' when no feedback messages exist."""
        from app.services.agent_team.context_injector import ContextInjector

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        injector = ContextInjector(db)
        result = await injector.build_feedback_md(uuid4())
        assert result == ""

    @pytest.mark.asyncio
    async def test_renders_approved_feedback(self):
        """build_feedback_md renders approved feedback with decision and text."""
        from app.services.agent_team.context_injector import ContextInjector

        db = AsyncMock()
        mock_msg = MagicMock()
        mock_msg.metadata_ = {
            "approval_feedback": {
                "action": "approved",
                "feedback_text": "Good approach, proceed",
            }
        }
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_msg]
        db.execute.return_value = mock_result

        injector = ContextInjector(db)
        result = await injector.build_feedback_md(uuid4())
        assert "<human_feedback>" in result
        assert "</human_feedback>" in result
        assert "approved" in result
        assert "Good approach, proceed" in result
        assert "revise" not in result.lower()

    @pytest.mark.asyncio
    async def test_renders_rejected_feedback_with_revise_instruction(self):
        """build_feedback_md adds revision instruction for rejections."""
        from app.services.agent_team.context_injector import ContextInjector

        db = AsyncMock()
        mock_msg = MagicMock()
        mock_msg.metadata_ = {
            "approval_feedback": {
                "action": "rejected",
                "feedback_text": "Security concern",
            }
        }
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_msg]
        db.execute.return_value = mock_result

        injector = ContextInjector(db)
        result = await injector.build_feedback_md(uuid4())
        assert "<human_feedback>" in result
        assert "rejected" in result
        assert "Security concern" in result
        assert "revise" in result.lower()


# ── S3: inject_context with conversation_id ───────────────────────────────────


class TestInjectContextConversationId:
    """S3: CTO F1 condition — conversation_id added to inject_context."""

    @pytest.mark.asyncio
    async def test_inject_context_accepts_conversation_id(self):
        """inject_context signature accepts conversation_id parameter."""
        from app.services.agent_team.context_injector import ContextInjector

        db = AsyncMock()
        injector = ContextInjector(db)

        # Patch all builders to return empty (isolate signature test)
        with patch.object(injector, "build_delegation_md", return_value=""), \
             patch.object(injector, "build_team_md", return_value=""), \
             patch.object(injector, "build_availability_md", return_value=""), \
             patch.object(injector, "build_skills_md", return_value=""), \
             patch.object(injector, "build_workspace_md", return_value=""), \
             patch.object(injector, "build_feedback_md", return_value=""):
            result = await injector.inject_context(
                agent_id=uuid4(),
                team_id=None,
                system_prompt="Base prompt",
                project_id=uuid4(),
                conversation_id=uuid4(),
            )
            assert result == "Base prompt"

    @pytest.mark.asyncio
    async def test_conversation_id_passed_to_workspace_builder(self):
        """inject_context passes conversation_id to build_workspace_md."""
        from app.services.agent_team.context_injector import ContextInjector

        db = AsyncMock()
        injector = ContextInjector(db)
        conv_id = uuid4()

        with patch.object(injector, "build_delegation_md", return_value=""), \
             patch.object(injector, "build_team_md", return_value=""), \
             patch.object(injector, "build_availability_md", return_value=""), \
             patch.object(injector, "build_skills_md", return_value=""), \
             patch.object(injector, "build_workspace_md", return_value="") as mock_ws, \
             patch.object(injector, "build_feedback_md", return_value="") as mock_fb:
            await injector.inject_context(
                agent_id=uuid4(),
                team_id=None,
                system_prompt="Base",
                conversation_id=conv_id,
            )
            mock_ws.assert_called_once_with(conv_id)
            mock_fb.assert_called_once_with(conv_id)

    @pytest.mark.asyncio
    async def test_workspace_and_feedback_appended_to_prompt(self):
        """inject_context appends workspace + feedback sections to prompt."""
        from app.services.agent_team.context_injector import ContextInjector

        db = AsyncMock()
        injector = ContextInjector(db)

        with patch.object(injector, "build_delegation_md", return_value=""), \
             patch.object(injector, "build_team_md", return_value=""), \
             patch.object(injector, "build_availability_md", return_value=""), \
             patch.object(injector, "build_skills_md", return_value=""), \
             patch.object(
                 injector, "build_workspace_md",
                 return_value="<workspace>\n## Shared Workspace\n</workspace>",
             ), \
             patch.object(
                 injector, "build_feedback_md",
                 return_value="<human_feedback>\n## Human Feedback\n</human_feedback>",
             ):
            result = await injector.inject_context(
                agent_id=uuid4(),
                team_id=None,
                system_prompt="Base",
                conversation_id=uuid4(),
            )
            assert "<system_context>" in result
            assert "<workspace>" in result
            assert "<human_feedback>" in result


# ── S4: extract_workspace_keys_from_text ──────────────────────────────────────


class TestExtractWorkspaceKeys:
    """S4: History compactor — workspace key extraction."""

    def test_extracts_agent_artifact_pattern(self):
        """extract_workspace_keys_from_text finds agent/artifact patterns."""
        from app.services.agent_team.history_compactor import HistoryCompactor

        text = "The coder/main.py was reviewed by reviewer/feedback"
        keys = HistoryCompactor.extract_workspace_keys_from_text(text)
        assert "coder/main.py" in keys
        assert "reviewer/feedback" in keys

    def test_deduplicates_keys(self):
        """extract_workspace_keys_from_text returns unique keys."""
        from app.services.agent_team.history_compactor import HistoryCompactor

        text = "See coder/main.py and also coder/main.py again"
        keys = HistoryCompactor.extract_workspace_keys_from_text(text)
        assert keys.count("coder/main.py") == 1

    def test_handles_empty_text(self):
        """extract_workspace_keys_from_text returns [] for empty input."""
        from app.services.agent_team.history_compactor import HistoryCompactor

        keys = HistoryCompactor.extract_workspace_keys_from_text("")
        assert keys == []

    def test_multiple_artifact_types(self):
        """extract_workspace_keys_from_text handles various artifact names."""
        from app.services.agent_team.history_compactor import HistoryCompactor

        text = (
            "Files: tester/results.json, coder/diff, "
            "reviewer/code-review.md, architect/design-v2"
        )
        keys = HistoryCompactor.extract_workspace_keys_from_text(text)
        assert "tester/results.json" in keys
        assert "coder/diff" in keys
        assert len(keys) >= 3


# ── S5: compact_with_workspace_preservation ───────────────────────────────────


class TestCompactWithWorkspacePreservation:
    """S5: History compactor — workspace-aware compaction."""

    @pytest.mark.asyncio
    async def test_skips_when_threshold_not_reached(self):
        """compact_with_workspace_preservation returns None below threshold."""
        from app.services.agent_team.history_compactor import HistoryCompactor

        db = AsyncMock()
        compactor = HistoryCompactor(db)

        conv = MagicMock()
        conv.total_messages = 10
        conv.max_messages = 100
        conv.metadata_ = {}

        result = await compactor.compact_with_workspace_preservation(conv)
        assert result is None

    @pytest.mark.asyncio
    async def test_persists_workspace_keys_in_metadata(self):
        """_persist_summary stores workspace_keys and workspace_key_count."""
        from app.services.agent_team.history_compactor import HistoryCompactor

        db = AsyncMock()
        compactor = HistoryCompactor(db)

        conv = MagicMock()
        conv.id = uuid4()
        conv.total_messages = 50
        conv.metadata_ = {}

        with patch.object(
            compactor, "_get_workspace_keys", return_value=["coder/main.py"]
        ):
            await compactor._persist_summary(conv, "Test summary")

        meta = conv.metadata_
        assert "compaction_summary" in meta
        assert meta["compaction_summary"] == "Test summary"
        assert "workspace_keys" in meta
        assert meta["workspace_keys"] == ["coder/main.py"]
        assert meta["workspace_key_count"] == 1
        assert "last_compacted_at" in meta

    @pytest.mark.asyncio
    async def test_workspace_keys_empty_when_no_workspace(self):
        """_persist_summary handles empty workspace keys gracefully."""
        from app.services.agent_team.history_compactor import HistoryCompactor

        db = AsyncMock()
        compactor = HistoryCompactor(db)

        conv = MagicMock()
        conv.id = uuid4()
        conv.total_messages = 50
        conv.metadata_ = {}

        with patch.object(compactor, "_get_workspace_keys", return_value=[]):
            await compactor._persist_summary(conv, "Summary text")

        meta = conv.metadata_
        assert meta["workspace_keys"] == []
        assert meta["workspace_key_count"] == 0


# ── S6: ApprovalFeedbackService ───────────────────────────────────────────────


class TestApprovalFeedbackService:
    """S6: Approval feedback — approve/reject with feedback."""

    @pytest.mark.asyncio
    async def test_approve_with_feedback_creates_message(self):
        """approve_with_feedback creates system message with metadata."""
        from app.services.agent_team.approval_feedback import (
            ApprovalFeedbackService,
        )

        db = AsyncMock()
        conv_id = uuid4()
        user_id = uuid4()

        # Mock conversation lookup
        mock_conv = MagicMock()
        mock_conv.status = "active"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conv
        db.execute.return_value = mock_result

        service = ApprovalFeedbackService(db)
        msg = await service.approve_with_feedback(
            conversation_id=conv_id,
            feedback_text="Good work, proceed",
            user_id=user_id,
        )

        assert msg.message_type == "system"
        assert msg.sender_id == "approval_feedback"
        assert msg.metadata_["approval_feedback"]["action"] == "approved"
        assert msg.metadata_["approval_feedback"]["feedback_text"] == "Good work, proceed"
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_reject_with_feedback_includes_revise_text(self):
        """reject_with_feedback includes revision instruction in content."""
        from app.services.agent_team.approval_feedback import (
            ApprovalFeedbackService,
        )

        db = AsyncMock()
        mock_conv = MagicMock()
        mock_conv.status = "active"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conv
        db.execute.return_value = mock_result

        service = ApprovalFeedbackService(db)
        msg = await service.reject_with_feedback(
            conversation_id=uuid4(),
            reason="Security concern in line 42",
        )

        assert msg.metadata_["approval_feedback"]["action"] == "rejected"
        assert "revise" in msg.content.lower()
        assert "Security concern in line 42" in msg.content

    @pytest.mark.asyncio
    async def test_raises_for_missing_conversation(self):
        """_record_feedback raises ValueError for non-existent conversation."""
        from app.services.agent_team.approval_feedback import (
            ApprovalFeedbackService,
        )

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        service = ApprovalFeedbackService(db)
        with pytest.raises(ValueError, match="not found"):
            await service.approve_with_feedback(uuid4())

    @pytest.mark.asyncio
    async def test_raises_for_completed_conversation(self):
        """_record_feedback raises ValueError for completed conversation."""
        from app.services.agent_team.approval_feedback import (
            ApprovalFeedbackService,
        )

        db = AsyncMock()
        mock_conv = MagicMock()
        mock_conv.status = "completed"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conv
        db.execute.return_value = mock_result

        service = ApprovalFeedbackService(db)
        with pytest.raises(ValueError, match="completed"):
            await service.approve_with_feedback(uuid4())

    @pytest.mark.asyncio
    async def test_get_latest_feedback_returns_none_when_empty(self):
        """get_latest_feedback returns None when no feedback exists."""
        from app.services.agent_team.approval_feedback import (
            ApprovalFeedbackService,
        )

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        service = ApprovalFeedbackService(db)
        result = await service.get_latest_feedback(uuid4())
        assert result is None


# ── S7: ApprovalAnalyticsService ──────────────────────────────────────────────


class TestApprovalAnalyticsService:
    """S7: Approval analytics — rate and response time calculations."""

    @pytest.mark.asyncio
    async def test_approval_rate_zero_when_no_data(self):
        """get_approval_rate returns 0.0 rate when no feedback exists."""
        from app.services.agent_team.approval_analytics import (
            ApprovalAnalyticsService,
        )

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        db.execute.return_value = mock_result

        service = ApprovalAnalyticsService(db)
        stats = await service.get_approval_rate(uuid4(), days=30)
        assert stats.total == 0
        assert stats.approved == 0
        assert stats.rejected == 0
        assert stats.rate == 0.0

    @pytest.mark.asyncio
    async def test_approval_rate_calculates_correctly(self):
        """get_approval_rate computes correct rate from metadata."""
        from app.services.agent_team.approval_analytics import (
            ApprovalAnalyticsService,
        )

        db = AsyncMock()
        mock_result = MagicMock()
        # 18 approved, 2 rejected → rate = 0.9
        rows = []
        for _ in range(18):
            rows.append(({"approval_feedback": {"action": "approved"}},))
        for _ in range(2):
            rows.append(({"approval_feedback": {"action": "rejected"}},))
        mock_result.all.return_value = rows
        db.execute.return_value = mock_result

        service = ApprovalAnalyticsService(db)
        stats = await service.get_approval_rate(uuid4(), days=30)
        assert stats.total == 20
        assert stats.approved == 18
        assert stats.rejected == 2
        assert stats.rate == 0.9

    @pytest.mark.asyncio
    async def test_approval_rate_ignores_invalid_metadata(self):
        """get_approval_rate skips rows with non-dict metadata."""
        from app.services.agent_team.approval_analytics import (
            ApprovalAnalyticsService,
        )

        db = AsyncMock()
        mock_result = MagicMock()
        rows = [
            ({"approval_feedback": {"action": "approved"}},),
            (None,),  # Non-dict metadata
            ("string_metadata",),  # Non-dict metadata
            ({"approval_feedback": {"action": "rejected"}},),
        ]
        mock_result.all.return_value = rows
        db.execute.return_value = mock_result

        service = ApprovalAnalyticsService(db)
        stats = await service.get_approval_rate(uuid4(), days=30)
        assert stats.total == 2
        assert stats.approved == 1
        assert stats.rejected == 1
        assert stats.rate == 0.5

    @pytest.mark.asyncio
    async def test_response_time_stats_dataclass(self):
        """ResponseTimeStats holds p50, p95, count correctly."""
        from app.services.agent_team.approval_analytics import ResponseTimeStats

        stats = ResponseTimeStats(p50=12.5, p95=45.8, count=100)
        assert stats.p50 == 12.5
        assert stats.p95 == 45.8
        assert stats.count == 100

        # Frozen dataclass
        with pytest.raises(AttributeError):
            stats.p50 = 99.9  # type: ignore[misc]


# ── S8: Integration — feedback → context injection ────────────────────────────


class TestFeedbackContextIntegration:
    """S8: Integration — feedback stored → injected into context."""

    @pytest.mark.asyncio
    async def test_feedback_metadata_matches_context_reader(self):
        """Metadata format from approval_feedback matches build_feedback_md reader."""
        # Verify the metadata schema used by ApprovalFeedbackService._record_feedback
        # matches what ContextInjector.build_feedback_md expects to read
        from app.services.agent_team.approval_feedback import (
            ApprovalFeedbackService,
        )

        db = AsyncMock()
        mock_conv = MagicMock()
        mock_conv.status = "active"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conv
        db.execute.return_value = mock_result

        service = ApprovalFeedbackService(db)
        msg = await service.approve_with_feedback(
            uuid4(), "Test feedback", uuid4()
        )

        # Verify metadata structure matches what build_feedback_md reads
        meta = msg.metadata_
        assert "approval_feedback" in meta
        feedback = meta["approval_feedback"]
        assert "action" in feedback
        assert "feedback_text" in feedback
        assert "user_id" in feedback
        assert "timestamp" in feedback

    @pytest.mark.asyncio
    async def test_approval_stats_dataclass_is_frozen(self):
        """ApprovalStats is immutable (frozen dataclass)."""
        from app.services.agent_team.approval_analytics import ApprovalStats

        stats = ApprovalStats(total=10, approved=8, rejected=2, rate=0.8)
        assert stats.total == 10
        assert stats.rate == 0.8

        with pytest.raises(AttributeError):
            stats.total = 99  # type: ignore[misc]

    @pytest.mark.asyncio
    async def test_get_latest_feedback_finds_feedback_in_metadata(self):
        """get_latest_feedback scans recent messages for approval_feedback key."""
        from app.services.agent_team.approval_feedback import (
            ApprovalFeedbackService,
        )

        db = AsyncMock()

        # First message has no feedback, second has it
        msg_no_feedback = MagicMock()
        msg_no_feedback.metadata_ = {"some_other_key": True}

        msg_with_feedback = MagicMock()
        msg_with_feedback.metadata_ = {
            "approval_feedback": {
                "action": "approved",
                "feedback_text": "Looks good",
                "user_id": str(uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            msg_no_feedback,
            msg_with_feedback,
        ]
        db.execute.return_value = mock_result

        service = ApprovalFeedbackService(db)
        feedback = await service.get_latest_feedback(uuid4())
        assert feedback is not None
        assert feedback["action"] == "approved"
        assert feedback["feedback_text"] == "Looks good"
