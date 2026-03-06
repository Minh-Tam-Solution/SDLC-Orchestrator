"""
Sprint 222 — OTT @mention → EP-07 Agent Direct Routing
Tests: 21 across 10 groups

Groups:
  G1: handle_mention_request — happy path (name match)       3 tests
  G2: handle_mention_request — role match (sdlc_role)        2 tests
  G3: handle_mention_request — unknown agent → error msg     2 tests
  G4: handle_mention_request — no project configured         2 tests
  G5: _find_agent_by_name_or_role — lookup priority          3 tests
  G6: False-positive guard (email@domain.com not routed)     2 tests
  G7: Multi-mention (first wins)                             2 tests
  G8: Zalo channel parity                                    2 tests
  G9: Routing precedence (/command > @mention > kw > AI)     2 tests
  G10: Regression — definition_override=None backward compat 1 test
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_agent(
    agent_name: str = "pjm",
    sdlc_role: str = "pm",
    project_id: uuid.UUID | None = None,
) -> MagicMock:
    agent = MagicMock()
    agent.id = uuid.uuid4()
    agent.agent_name = agent_name
    agent.sdlc_role = sdlc_role
    agent.project_id = project_id or uuid.uuid4()
    agent.is_active = True
    return agent


def _mock_db() -> MagicMock:
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.add = AsyncMock()
    return db


def _scalar_result(value: Any) -> MagicMock:
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=value)
    return result


# ---------------------------------------------------------------------------
# G1: handle_mention_request — happy path (agent_name match)
# ---------------------------------------------------------------------------


class TestHandleMentionHappyPath:
    """G1 — @pjm found by name → pipeline runs."""

    @pytest.mark.asyncio
    async def test_mention_routes_to_agent(self):
        agent = _make_agent("pjm", "pm")
        with (
            patch(
                "app.services.agent_bridge.ott_team_bridge._resolve_project_id",
                new=AsyncMock(return_value=uuid.uuid4()),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._find_agent_by_name_or_role",
                new=AsyncMock(return_value=agent),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._process_agent_request",
                new=AsyncMock(return_value=True),
            ) as mock_process,
            patch(
                "app.services.agent_bridge.ott_team_bridge._ott_send_progress",
                new=AsyncMock(),
            ),
            patch("app.db.session.AsyncSessionLocal") as mock_session_cls,
        ):
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=_mock_db())
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_session

            from app.services.agent_bridge.ott_team_bridge import handle_mention_request

            result = await handle_mention_request(
                chat_id="-100123",
                text="@pjm báo cáo hiện trạng dự án",
                bot_token="bot_token",
                sender_id="user_1",
                channel="telegram",
            )

        assert result is True
        mock_process.assert_called_once()
        call_kwargs = mock_process.call_args.kwargs
        assert call_kwargs["definition_override"] is agent

    @pytest.mark.asyncio
    async def test_mention_returns_true_on_pipeline_success(self):
        agent = _make_agent("architect")
        with (
            patch(
                "app.services.agent_bridge.ott_team_bridge._resolve_project_id",
                new=AsyncMock(return_value=uuid.uuid4()),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._find_agent_by_name_or_role",
                new=AsyncMock(return_value=agent),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._process_agent_request",
                new=AsyncMock(return_value=True),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._ott_send_progress",
                new=AsyncMock(),
            ),
            patch("app.db.session.AsyncSessionLocal") as mock_session_cls,
        ):
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=_mock_db())
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_session

            from app.services.agent_bridge.ott_team_bridge import handle_mention_request

            result = await handle_mention_request(
                chat_id="chat_1",
                text="@architect review auth flow",
                bot_token="tok",
                sender_id="u1",
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_routing_ack_message_sent(self):
        """Progress message sent before pipeline (routing acknowledgment)."""
        agent = _make_agent("coder", "developer")
        send_progress = AsyncMock()
        with (
            patch(
                "app.services.agent_bridge.ott_team_bridge._resolve_project_id",
                new=AsyncMock(return_value=uuid.uuid4()),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._find_agent_by_name_or_role",
                new=AsyncMock(return_value=agent),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._process_agent_request",
                new=AsyncMock(return_value=True),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._ott_send_progress",
                new=send_progress,
            ),
            patch("app.db.session.AsyncSessionLocal") as mock_session_cls,
        ):
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=_mock_db())
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_session

            from app.services.agent_bridge.ott_team_bridge import handle_mention_request

            await handle_mention_request(
                chat_id="chat_x", text="@coder generate tests",
                bot_token="tok", sender_id="u1",
            )

        # Ack message should reference agent name
        assert send_progress.called
        ack_text = send_progress.call_args_list[0][0][3]  # 4th positional arg is text
        assert "coder" in ack_text.lower() or "Routing" in ack_text


# ---------------------------------------------------------------------------
# G2: handle_mention_request — sdlc_role fallback
# ---------------------------------------------------------------------------


class TestHandleMentionRoleFallback:
    """G2 — @coder matches by sdlc_role when no agent_name='coder' exists."""

    @pytest.mark.asyncio
    async def test_role_mention_resolves_correctly(self):
        agent = _make_agent("coder-alpha", "developer")
        with (
            patch(
                "app.services.agent_bridge.ott_team_bridge._resolve_project_id",
                new=AsyncMock(return_value=uuid.uuid4()),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._find_agent_by_name_or_role",
                new=AsyncMock(return_value=agent),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._process_agent_request",
                new=AsyncMock(return_value=True),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._ott_send_progress",
                new=AsyncMock(),
            ),
            patch("app.db.session.AsyncSessionLocal") as mock_session_cls,
        ):
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=_mock_db())
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_session

            from app.services.agent_bridge.ott_team_bridge import handle_mention_request

            result = await handle_mention_request(
                chat_id="c1", text="@developer review this PR",
                bot_token="tok", sender_id="u1",
            )
        assert result is True

    @pytest.mark.asyncio
    async def test_definition_override_uses_role_result(self):
        """_process_agent_request receives the role-matched definition."""
        agent = _make_agent("review-bot", "reviewer")
        with (
            patch(
                "app.services.agent_bridge.ott_team_bridge._resolve_project_id",
                new=AsyncMock(return_value=uuid.uuid4()),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._find_agent_by_name_or_role",
                new=AsyncMock(return_value=agent),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._process_agent_request",
                new=AsyncMock(return_value=True),
            ) as mock_proc,
            patch(
                "app.services.agent_bridge.ott_team_bridge._ott_send_progress",
                new=AsyncMock(),
            ),
            patch("app.db.session.AsyncSessionLocal") as mock_session_cls,
        ):
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=_mock_db())
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_session

            from app.services.agent_bridge.ott_team_bridge import handle_mention_request

            await handle_mention_request(
                chat_id="c1", text="@reviewer check security",
                bot_token="tok", sender_id="u1",
            )

        assert mock_proc.call_args.kwargs["definition_override"] is agent


# ---------------------------------------------------------------------------
# G3: handle_mention_request — unknown agent → error message, returns True
# ---------------------------------------------------------------------------


class TestHandleMentionUnknownAgent:
    """G3 — @unknownbot sends error, does NOT fall through to generic AI."""

    @pytest.mark.asyncio
    async def test_unknown_agent_sends_error_message(self):
        send_progress = AsyncMock()
        with (
            patch(
                "app.services.agent_bridge.ott_team_bridge._resolve_project_id",
                new=AsyncMock(return_value=uuid.uuid4()),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._find_agent_by_name_or_role",
                new=AsyncMock(return_value=None),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._ott_send_progress",
                new=send_progress,
            ),
            patch("app.db.session.AsyncSessionLocal") as mock_session_cls,
        ):
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=_mock_db())
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_session

            from app.services.agent_bridge.ott_team_bridge import handle_mention_request

            result = await handle_mention_request(
                chat_id="c1", text="@unknownbot do something",
                bot_token="tok", sender_id="u1",
            )

        assert result is True  # handled (error sent)
        assert send_progress.called

    @pytest.mark.asyncio
    async def test_unknown_agent_does_not_call_process(self):
        with (
            patch(
                "app.services.agent_bridge.ott_team_bridge._resolve_project_id",
                new=AsyncMock(return_value=uuid.uuid4()),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._find_agent_by_name_or_role",
                new=AsyncMock(return_value=None),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._process_agent_request",
                new=AsyncMock(return_value=True),
            ) as mock_proc,
            patch(
                "app.services.agent_bridge.ott_team_bridge._ott_send_progress",
                new=AsyncMock(),
            ),
            patch("app.db.session.AsyncSessionLocal") as mock_session_cls,
        ):
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=_mock_db())
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_session

            from app.services.agent_bridge.ott_team_bridge import handle_mention_request

            await handle_mention_request(
                chat_id="c1", text="@ghost help me",
                bot_token="tok", sender_id="u1",
            )

        mock_proc.assert_not_called()


# ---------------------------------------------------------------------------
# G4: handle_mention_request — no project configured
# ---------------------------------------------------------------------------


class TestHandleMentionNoProject:
    """G4 — No project → error sent, returns True (do not fall to generic AI)."""

    @pytest.mark.asyncio
    async def test_no_project_sends_error(self):
        send_progress = AsyncMock()
        with (
            patch(
                "app.services.agent_bridge.ott_team_bridge._resolve_project_id",
                new=AsyncMock(return_value=None),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._ott_send_progress",
                new=send_progress,
            ),
        ):
            from app.services.agent_bridge.ott_team_bridge import handle_mention_request

            result = await handle_mention_request(
                chat_id="c1", text="@pjm status update",
                bot_token="tok", sender_id="u1",
            )

        assert result is True
        assert send_progress.called

    @pytest.mark.asyncio
    async def test_no_mention_returns_false(self):
        """No @mention in text → returns False → caller tries next branch."""
        from app.services.agent_bridge.ott_team_bridge import handle_mention_request

        result = await handle_mention_request(
            chat_id="c1", text="generate code for me",
            bot_token="tok", sender_id="u1",
        )
        assert result is False


# ---------------------------------------------------------------------------
# G5: _find_agent_by_name_or_role — lookup priority
# ---------------------------------------------------------------------------


class TestFindAgentByNameOrRole:
    """G5 — name match takes precedence over role match."""

    @pytest.mark.asyncio
    async def test_name_match_returns_first(self):
        agent = _make_agent("pjm-alpha", "pm")
        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(agent))

        from app.services.agent_bridge.ott_team_bridge import _find_agent_by_name_or_role

        result = await _find_agent_by_name_or_role(db, uuid.uuid4(), "pjm-alpha")
        assert result is agent
        assert db.execute.call_count == 1  # name match → no role fallback needed

    @pytest.mark.asyncio
    async def test_role_fallback_when_name_not_found(self):
        agent = _make_agent("pm-bot", "pm")
        db = _mock_db()
        # First call (name) → None; second call (role) → agent
        db.execute = AsyncMock(side_effect=[
            _scalar_result(None),
            _scalar_result(agent),
        ])

        from app.services.agent_bridge.ott_team_bridge import _find_agent_by_name_or_role

        result = await _find_agent_by_name_or_role(db, uuid.uuid4(), "pm")
        assert result is agent
        assert db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_returns_none_when_neither_found(self):
        db = _mock_db()
        db.execute = AsyncMock(return_value=_scalar_result(None))

        from app.services.agent_bridge.ott_team_bridge import _find_agent_by_name_or_role

        result = await _find_agent_by_name_or_role(db, uuid.uuid4(), "nobody")
        assert result is None


# ---------------------------------------------------------------------------
# G6: False-positive guard — email addresses NOT treated as @mention
# ---------------------------------------------------------------------------


class TestFalsePositiveGuard:
    """G6 — email@domain.com is not extracted as @mention by MentionParser."""

    def test_email_address_not_extracted(self):
        from app.services.agent_team.mention_parser import MentionParser

        mentions = MentionParser.extract_mentions(
            "contact me at admin@sdlc.test for help"
        )
        # MentionParser uses (?<!\S)@(\w+) which excludes email patterns
        assert not any(m.name == "sdlc" for m in mentions)

    @pytest.mark.asyncio
    async def test_email_does_not_trigger_routing(self):
        from app.services.agent_bridge.ott_team_bridge import handle_mention_request

        # Email in text — no valid @mention → should return False
        result = await handle_mention_request(
            chat_id="c1",
            text="send report to user@example.com please",
            bot_token="tok",
            sender_id="u1",
        )
        assert result is False


# ---------------------------------------------------------------------------
# G7: Multi-mention (first wins, rest handled by agent delegation internally)
# ---------------------------------------------------------------------------


class TestMultiMention:
    """G7 — First @mention is target; subsequent ones handled by agent chain."""

    @pytest.mark.asyncio
    async def test_first_mention_used_as_target(self):
        pm_agent = _make_agent("pjm", "pm")
        architect_agent = _make_agent("arch", "architect")
        # _find_agent_by_name_or_role called with first mention name only
        find_mock = AsyncMock(return_value=pm_agent)
        with (
            patch(
                "app.services.agent_bridge.ott_team_bridge._resolve_project_id",
                new=AsyncMock(return_value=uuid.uuid4()),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._find_agent_by_name_or_role",
                new=find_mock,
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._process_agent_request",
                new=AsyncMock(return_value=True),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._ott_send_progress",
                new=AsyncMock(),
            ),
            patch("app.db.session.AsyncSessionLocal") as mock_session_cls,
        ):
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=_mock_db())
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_session

            from app.services.agent_bridge.ott_team_bridge import handle_mention_request

            await handle_mention_request(
                chat_id="c1",
                text="@pjm and @architect review the design",
                bot_token="tok", sender_id="u1",
            )

        # Called once with 'pjm' (first mention)
        assert find_mock.call_count == 1
        _, _, name_arg = find_mock.call_args[0]
        assert name_arg == "pjm"

    @pytest.mark.asyncio
    async def test_single_mention_in_multi_text_extracts_correctly(self):
        from app.services.agent_team.mention_parser import MentionParser

        mentions = MentionParser.extract_mentions("@coder please fix @reviewer issue")
        assert len(mentions) == 2
        assert mentions[0].name == "coder"
        assert mentions[1].name == "reviewer"


# ---------------------------------------------------------------------------
# G8: Zalo channel parity
# ---------------------------------------------------------------------------


class TestZaloChannelParity:
    """G8 — handle_mention_request works with channel='zalo'."""

    @pytest.mark.asyncio
    async def test_zalo_mention_routes_to_agent(self):
        agent = _make_agent("pjm", "pm")
        with (
            patch(
                "app.services.agent_bridge.ott_team_bridge._resolve_project_id",
                new=AsyncMock(return_value=uuid.uuid4()),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._find_agent_by_name_or_role",
                new=AsyncMock(return_value=agent),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._process_agent_request",
                new=AsyncMock(return_value=True),
            ) as mock_proc,
            patch(
                "app.services.agent_bridge.ott_team_bridge._ott_send_progress",
                new=AsyncMock(),
            ),
            patch("app.db.session.AsyncSessionLocal") as mock_session_cls,
        ):
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=_mock_db())
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_session

            from app.services.agent_bridge.ott_team_bridge import handle_mention_request

            result = await handle_mention_request(
                chat_id="zalo_user_123",
                text="@pjm báo cáo",
                bot_token="",
                sender_id="zalo_user_123",
                channel="zalo",
            )

        assert result is True
        assert mock_proc.call_args.kwargs["channel"] == "zalo"

    @pytest.mark.asyncio
    async def test_zalo_channel_passed_to_process(self):
        """channel='zalo' propagates all the way to _process_agent_request."""
        agent = _make_agent("qa-bot", "qa")
        with (
            patch(
                "app.services.agent_bridge.ott_team_bridge._resolve_project_id",
                new=AsyncMock(return_value=uuid.uuid4()),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._find_agent_by_name_or_role",
                new=AsyncMock(return_value=agent),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._process_agent_request",
                new=AsyncMock(return_value=True),
            ) as mock_proc,
            patch(
                "app.services.agent_bridge.ott_team_bridge._ott_send_progress",
                new=AsyncMock(),
            ),
            patch("app.db.session.AsyncSessionLocal") as mock_session_cls,
        ):
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=_mock_db())
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_session

            from app.services.agent_bridge.ott_team_bridge import handle_mention_request

            await handle_mention_request(
                chat_id="z1", text="@qa run tests",
                bot_token="", sender_id="z1", channel="zalo",
            )

        assert mock_proc.call_args.kwargs["channel"] == "zalo"
        assert mock_proc.call_args.kwargs["bot_token"] == ""


# ---------------------------------------------------------------------------
# G9: Routing precedence (/command > @mention > multi-agent kw > free text)
# ---------------------------------------------------------------------------


class TestRoutingPrecedence:
    """G9 — @mention branch sits between /command and multi-agent keyword."""

    def test_mention_parser_detects_at_mention(self):
        from app.services.agent_team.mention_parser import MentionParser

        # Plain @mention
        mentions = MentionParser.extract_mentions("@pjm give me a status update")
        assert len(mentions) == 1
        assert mentions[0].name == "pjm"

    def test_mention_parser_returns_empty_for_no_mention(self):
        from app.services.agent_team.mention_parser import MentionParser

        mentions = MentionParser.extract_mentions("generate code for the auth module")
        assert mentions == []


# ---------------------------------------------------------------------------
# G10: Regression — definition_override=None preserves original behavior
# ---------------------------------------------------------------------------


class TestDefinitionOverrideBackwardCompat:
    """G10 — _process_agent_request with definition_override=None still calls _find_entry_agent."""

    @pytest.mark.asyncio
    async def test_none_override_calls_find_entry_agent(self):
        agent = _make_agent("coder", "developer")
        find_entry = AsyncMock(return_value=agent)
        db = _mock_db()

        with (
            patch(
                "app.services.agent_bridge.ott_team_bridge._find_entry_agent",
                new=find_entry,
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge.get_redis_client",
                new=AsyncMock(return_value=AsyncMock()),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge.ConversationTracker",
            ) as mock_tracker_cls,
            patch(
                "app.services.agent_bridge.ott_team_bridge.MessageQueue",
            ) as mock_queue_cls,
            patch(
                "app.services.agent_bridge.ott_team_bridge.TeamOrchestrator",
            ) as mock_orch_cls,
            patch(
                "app.services.agent_bridge.ott_team_bridge._get_or_create_active_conversation",
                new=AsyncMock(return_value=None),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._store_active_conversation",
                new=AsyncMock(),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._ott_send_progress",
                new=AsyncMock(),
            ),
            patch(
                "app.services.agent_bridge.ott_team_bridge._ott_send_result",
                new=AsyncMock(),
            ),
        ):
            mock_tracker = AsyncMock()
            conv = MagicMock()
            conv.id = uuid.uuid4()
            conv.queue_mode = "queue"
            mock_tracker.create = AsyncMock(return_value=conv)
            mock_tracker.record_token_usage = AsyncMock(return_value=MagicMock(
                status=MagicMock(value="ok"), cost_cents=0
            ))
            mock_tracker_cls.return_value = mock_tracker

            mock_queue = AsyncMock()
            msg = MagicMock()
            msg.id = uuid.uuid4()
            mock_queue.enqueue = AsyncMock(return_value=msg)
            mock_queue_cls.return_value = mock_queue

            mock_orch = AsyncMock()
            proc_result = MagicMock()
            proc_result.success = True
            proc_result.response_message_id = None
            proc_result.tokens_used = 0
            proc_result.cost_cents = 0
            proc_result.provider_used = "ollama"
            proc_result.model_used = "qwen3:14b"
            proc_result.mentions_routed = []
            proc_result.error = None
            proc_result.skipped_reason = None
            mock_orch.process_next = AsyncMock(return_value=proc_result)
            mock_orch_cls.return_value = mock_orch

            from app.services.agent_bridge.ott_team_bridge import _process_agent_request

            await _process_agent_request(
                db=db,
                project_id=uuid.uuid4(),
                chat_id="c1",
                text="generate code",
                bot_token="tok",
                sender_id="u1",
                preset_name="startup-2",
                channel="telegram",
                definition_override=None,  # explicit None — backward compat
            )

        find_entry.assert_called_once()
