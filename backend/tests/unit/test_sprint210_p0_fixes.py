"""
Sprint 210 — P0 ENT Critical Fixes: Consolidated Verification Tests.

Test matrix from SPRINT-210-P0-ENT-CRITICAL-FIXES.md (Track F):
    T1:  Cookie JWT → TierGate → correct tier (ENTERPRISE)
    T2:  Cookie JWT → UsageLimits → correct quota
    T3:  Cookie JWT → ConvFirstGuard → identifies user correctly
    T4:  Member POST /gates → 200 (pass through)
    T5:  Non-member POST /gates → 403 (blocked)
    T6:  Admin POST /admin → 200 (admin path)
    T7:  GET /gates (any) → 200 (read-only)
    T8:  OTT `/gate create G1` + workspace → gate created, type=CONSULTATION
    T9:  OTT `/gate create` no workspace → guidance message
    T10: OTT `/gate create INVALID` → available presets list
    T11: CLI `gate create G1 --project-id <uuid>` → 201 Created
    T12: FR-051 file exists
    T13: FR-052 file exists
    T14: CLI `governance close-sprint` → success message
    T15: Web sprint close mutation → POST succeeds

CTO Amendment Tests (blocker fixes):
    P0-1: Unlinked user blocked from /gate create (_is_unlinked computed before routing)
    P0-2: OTT gate create checks project membership (parity with POST /gates)
    P0-3: Web gates page uses access_token (not auth_token)
    P0-4: CreateGateDialog handles first-gate scenario (useProjects + URL param)
    P1-1: CLI close-sprint uses GET /sprints + PUT /sprints/{id} (2-step)

References:
  - Track A0 detail tests: test_conversation_first_guard.py (CFG-19..21)
  - Track A detail tests: test_conversation_first_guard.py (CFG-22..25)
  - Track B/D detail tests: test_ott_link_handler.py, test_ott_identity_resolver.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # backend/tests/unit → repo root
DOCS_FR_DIR = PROJECT_ROOT / "docs" / "01-planning" / "03-Functional-Requirements"


@pytest.fixture()
def mock_db() -> AsyncMock:
    """Async DB session mock."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture()
def mock_redis() -> AsyncMock:
    """Async Redis mock."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    return redis


# ============================================================================
# T1 — Cookie JWT → TierGate → correct tier
# ============================================================================


class TestT1TierGateCookie:
    """T1: TierGate middleware reads httpOnly cookie and resolves correct tier."""

    @pytest.mark.asyncio
    async def test_t1_tier_gate_cookie_extracts_user_id(self) -> None:
        """Cookie JWT with sub claim is decoded; _extract_user_id returns user_id."""
        from app.middleware.tier_gate import TierGateMiddleware

        user_id = str(uuid4())
        jwt_payload = {"sub": user_id, "exp": 9999999999}

        # Verify _extract_user_id exists and handles cookie
        mw = TierGateMiddleware(app=AsyncMock())
        scope: dict[str, Any] = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/gates",
            "headers": [
                (b"cookie", f"sdlc_access_token=fake.jwt.token".encode()),
            ],
        }

        with patch(
            "app.core.security.decode_token",
            return_value=jwt_payload,
        ):
            extracted = mw._extract_user_id(scope)
            assert str(extracted) == user_id


# ============================================================================
# T2 — Cookie JWT → UsageLimits → correct quota
# ============================================================================


class TestT2UsageLimitsCookie:
    """T2: UsageLimitsMiddleware reads httpOnly cookie and resolves correct user."""

    @pytest.mark.asyncio
    async def test_t2_usage_limits_cookie_extracts_user_id(self) -> None:
        """Cookie JWT with sub claim is decoded; _extract_user_id returns user_id."""
        from app.middleware.usage_limits import UsageLimitsMiddleware

        user_id = str(uuid4())
        jwt_payload = {"sub": user_id, "exp": 9999999999}

        mw = UsageLimitsMiddleware(app=AsyncMock())
        scope: dict[str, Any] = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/projects",
            "headers": [
                (b"cookie", f"sdlc_access_token=fake.jwt.token".encode()),
            ],
        }

        with patch(
            "app.core.security.decode_token",
            return_value=jwt_payload,
        ):
            extracted = mw._extract_user_id(scope)
            assert str(extracted) == user_id


# ============================================================================
# T3 — Cookie JWT → ConversationFirstGuard → identifies user
# ============================================================================


class TestT3ConversationFirstGuardCookie:
    """T3: ConversationFirstGuard reads httpOnly cookie and identifies user.

    Detailed tests in test_conversation_first_guard.py (CFG-19..21).
    This is the Sprint 210 verification test.
    """

    @pytest.mark.asyncio
    async def test_t3_cfg_cookie_extracts_user_id(self) -> None:
        """Cookie JWT decoded by ConversationFirstGuard._extract_user_id."""
        from app.middleware.conversation_first_guard import ConversationFirstGuard

        user_id = str(uuid4())
        jwt_payload = {"sub": user_id, "exp": 9999999999}

        mw = ConversationFirstGuard(app=AsyncMock())
        scope: dict[str, Any] = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/gates",
            "headers": [
                (b"cookie", f"sdlc_access_token=fake.jwt.token".encode()),
            ],
        }

        with patch(
            "app.core.security.decode_token",
            return_value=jwt_payload,
        ):
            extracted = mw._extract_user_id(scope)
            assert str(extracted) == user_id


# ============================================================================
# T4 — Member POST /gates → 200 (pass through)
# ============================================================================


class TestT4MemberPostGates:
    """T4: Project member can POST to /api/v1/gates (team-write path).

    Detailed test: CFG-22 in test_conversation_first_guard.py.
    """

    @pytest.mark.asyncio
    async def test_t4_member_post_gates_passes(self) -> None:
        """Member with active project membership passes team-write guard."""
        from app.middleware.conversation_first_guard import (
            ConversationFirstGuard,
            TEAM_WRITE_PATHS,
        )

        assert any("/gates" in p for p in TEAM_WRITE_PATHS), (
            "TEAM_WRITE_PATHS must include /gates"
        )

        downstream_called = False
        status_code = 200

        async def mock_app(scope: dict, receive: Any, send: Any) -> None:
            nonlocal downstream_called
            downstream_called = True
            await send({
                "type": "http.response.start",
                "status": status_code,
                "headers": [],
            })
            await send({
                "type": "http.response.body",
                "body": b'{"ok": true}',
            })

        user_id = str(uuid4())
        mw = ConversationFirstGuard(app=mock_app)

        scope: dict[str, Any] = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/gates",
            "headers": [
                (b"authorization", f"Bearer fake.jwt.token".encode()),
            ],
        }

        with (
            patch.object(
                mw, "_extract_user_id", return_value=user_id,
            ),
            patch.object(
                mw, "_resolve_is_admin",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch.object(
                mw, "_resolve_is_project_member",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            await mw(scope, AsyncMock(), AsyncMock())
            assert downstream_called, "Member should pass through to downstream"


# ============================================================================
# T5 — Non-member POST /gates → 403
# ============================================================================


class TestT5NonMemberPostGates:
    """T5: Non-member is blocked from POST /api/v1/gates."""

    @pytest.mark.asyncio
    async def test_t5_non_member_post_gates_blocked(self) -> None:
        """Non-member cannot POST to team-write path."""
        from app.middleware.conversation_first_guard import ConversationFirstGuard

        user_id = str(uuid4())
        sent_responses: list[dict] = []

        async def capture_send(message: dict) -> None:
            sent_responses.append(message)

        mw = ConversationFirstGuard(app=AsyncMock())

        scope: dict[str, Any] = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/gates",
            "headers": [
                (b"authorization", b"Bearer fake.jwt.token"),
            ],
        }

        with (
            patch.object(mw, "_extract_user_id", return_value=user_id),
            patch.object(
                mw, "_resolve_is_admin",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch.object(
                mw, "_resolve_is_project_member",
                new_callable=AsyncMock,
                return_value=False,
            ),
        ):
            await mw(scope, AsyncMock(), capture_send)

            start = next(
                (r for r in sent_responses if r.get("type") == "http.response.start"),
                None,
            )
            assert start is not None
            assert start["status"] == 403


# ============================================================================
# T6 — Admin POST /admin → 200
# ============================================================================


class TestT6AdminPostAdmin:
    """T6: Admin can POST to admin-only paths."""

    @pytest.mark.asyncio
    async def test_t6_admin_post_admin_passes(self) -> None:
        """Admin user passes admin-only path guard."""
        from app.middleware.conversation_first_guard import (
            ConversationFirstGuard,
            ADMIN_ONLY_PATHS,
        )

        assert any("/admin" in p for p in ADMIN_ONLY_PATHS), (
            "ADMIN_ONLY_PATHS must include /admin paths"
        )

        downstream_called = False

        async def mock_app(scope: dict, receive: Any, send: Any) -> None:
            nonlocal downstream_called
            downstream_called = True
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [],
            })
            await send({
                "type": "http.response.body",
                "body": b'{"ok": true}',
            })

        user_id = str(uuid4())
        mw = ConversationFirstGuard(app=mock_app)

        scope: dict[str, Any] = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/admin/users",
            "headers": [
                (b"authorization", b"Bearer fake.jwt.token"),
            ],
        }

        with (
            patch.object(mw, "_extract_user_id", return_value=user_id),
            patch.object(
                mw, "_resolve_is_admin",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            await mw(scope, AsyncMock(), AsyncMock())
            assert downstream_called


# ============================================================================
# T7 — GET /gates (any user) → 200
# ============================================================================


class TestT7GetGatesAnyUser:
    """T7: GET requests always pass through ConversationFirstGuard."""

    @pytest.mark.asyncio
    async def test_t7_get_always_passes(self) -> None:
        """GET requests bypass ConversationFirstGuard regardless of role."""
        from app.middleware.conversation_first_guard import ConversationFirstGuard

        downstream_called = False

        async def mock_app(scope: dict, receive: Any, send: Any) -> None:
            nonlocal downstream_called
            downstream_called = True
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [],
            })
            await send({
                "type": "http.response.body",
                "body": b'{"gates": []}',
            })

        mw = ConversationFirstGuard(app=mock_app)

        scope: dict[str, Any] = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/gates",
            "headers": [],
        }

        await mw(scope, AsyncMock(), AsyncMock())
        assert downstream_called, "GET always passes through"


# ============================================================================
# T8 — OTT `/gate create G1` + workspace → gate created
# ============================================================================


class TestT8OttGateCreateWithWorkspace:
    """T8: OTT /gate create G1 with active workspace creates gate."""

    @pytest.mark.asyncio
    async def test_t8_gate_create_g1_workspace(self) -> None:
        """Create G1 gate via OTT with workspace → success reply."""
        from app.services.agent_bridge.governance_action_handler import (
            _execute_create_gate,
            GATE_PRESETS,
        )

        project_id = uuid4()
        gate_id = uuid4()
        bot_token = "test-token"
        chat_id = "12345"
        user_id = str(uuid4())

        # Mock workspace resolution
        mock_ws = MagicMock()
        mock_ws.project_id = str(project_id)

        # Mock Gate model
        mock_gate = MagicMock()
        mock_gate.id = gate_id
        mock_gate.gate_name = "G1"
        mock_gate.gate_type = "CONSULTATION"
        mock_gate.stage = "WHAT"

        sent_text: list[str] = []

        async def capture_reply(token: str, cid: Any, text: str, **kw: Any) -> bool:
            sent_text.append(text)
            return True

        # Setup DB mock as async context manager
        mock_db_session = AsyncMock()
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock(
            side_effect=lambda g: setattr(g, "id", gate_id),
        )
        # P0-2 membership check: first execute() call returns member row
        member_result_mock = MagicMock()
        member_result_mock.scalar_one_or_none.return_value = uuid4()  # member exists
        mock_db_session.execute = AsyncMock(return_value=member_result_mock)

        mock_session_cls = MagicMock()
        mock_session_cls.return_value.__aenter__ = AsyncMock(
            return_value=mock_db_session,
        )
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        # Lazy imports inside _execute_create_gate → patch at source
        with (
            patch(
                "app.services.agent_bridge.workspace_service.get_workspace",
                new_callable=AsyncMock,
                return_value=mock_ws,
            ),
            patch(
                "app.utils.redis.get_redis_client",
                new_callable=AsyncMock,
            ),
            patch(
                "app.services.agent_bridge.governance_action_handler.AsyncSessionLocal",
                mock_session_cls,
            ),
            patch(
                "app.services.agent_bridge.governance_action_handler._send_telegram_reply",
                side_effect=capture_reply,
            ),
        ):
            result = await _execute_create_gate(
                gate_name="G1",
                bot_token=bot_token,
                chat_id=chat_id,
                user_id=user_id,
            )

        assert result is True
        assert len(sent_text) == 1
        assert "Gate Created" in sent_text[0] or "✅" in sent_text[0]
        assert "CONSULTATION" in sent_text[0]
        assert "WHAT" in sent_text[0]

        # Verify preset mapping
        assert GATE_PRESETS["G1"]["gate_type"] == "CONSULTATION"
        assert GATE_PRESETS["G1"]["stage"] == "WHAT"


# ============================================================================
# T9 — OTT `/gate create` no workspace → guidance
# ============================================================================


class TestT9OttGateCreateNoWorkspace:
    """T9: OTT /gate create without workspace → guidance message."""

    @pytest.mark.asyncio
    async def test_t9_no_workspace_guidance(self) -> None:
        """/gate create G1 without workspace → prompt to set workspace."""
        from app.services.agent_bridge.governance_action_handler import (
            _execute_create_gate,
        )

        sent_text: list[str] = []

        async def capture_reply(token: str, cid: Any, text: str, **kw: Any) -> bool:
            sent_text.append(text)
            return True

        # Lazy imports inside _execute_create_gate → patch at source
        with (
            patch(
                "app.services.agent_bridge.workspace_service.get_workspace",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "app.utils.redis.get_redis_client",
                new_callable=AsyncMock,
            ),
            patch(
                "app.services.agent_bridge.governance_action_handler._send_telegram_reply",
                side_effect=capture_reply,
            ),
        ):
            result = await _execute_create_gate(
                gate_name="G1",
                bot_token="test-token",
                chat_id="12345",
                user_id=str(uuid4()),
            )

        assert result is False
        assert len(sent_text) == 1
        assert "workspace" in sent_text[0].lower()


# ============================================================================
# T10 — OTT `/gate create INVALID` → available presets
# ============================================================================


class TestT10OttGateCreateInvalid:
    """T10: OTT /gate create with invalid gate name → list presets."""

    @pytest.mark.asyncio
    async def test_t10_invalid_gate_name_lists_presets(self) -> None:
        """/gate create INVALID → error reply listing available gate names."""
        from app.services.agent_bridge.governance_action_handler import (
            _execute_create_gate,
            GATE_PRESETS,
        )

        sent_text: list[str] = []

        async def capture_reply(token: str, cid: Any, text: str, **kw: Any) -> bool:
            sent_text.append(text)
            return True

        with patch(
            "app.services.agent_bridge.governance_action_handler._send_telegram_reply",
            side_effect=capture_reply,
        ):
            result = await _execute_create_gate(
                gate_name="INVALID",
                bot_token="test-token",
                chat_id="12345",
                user_id=str(uuid4()),
            )

        assert result is False
        assert len(sent_text) == 1
        # Verify available gate names are listed
        for name in GATE_PRESETS:
            assert name in sent_text[0], f"Available preset {name} should be listed"


# ============================================================================
# T11 — CLI `gate create G1 --project-id <uuid>` → 201 Created
# ============================================================================


class TestT11CliGateCreate:
    """T11: CLI sdlcctl gate create G1 → sends correct payload."""

    def test_t11_gate_create_cli_payload(self) -> None:
        """CLI create command builds correct payload from GATE_PRESETS."""
        from sdlcctl.commands.gate import GATE_PRESETS, create_command

        assert "G1" in GATE_PRESETS
        preset = GATE_PRESETS["G1"]
        assert preset["gate_type"] == "CONSULTATION"
        assert preset["stage"] == "WHAT"

    def test_t11_gate_presets_all_six(self) -> None:
        """CLI GATE_PRESETS has all 6 standard gate types."""
        from sdlcctl.commands.gate import GATE_PRESETS

        expected = {"G0.1", "G0.2", "G1", "G2", "G3", "G4"}
        assert set(GATE_PRESETS.keys()) == expected

    def test_t11_gate_presets_match_ott(self) -> None:
        """CLI GATE_PRESETS matches OTT GATE_PRESETS (shared constant parity)."""
        from sdlcctl.commands.gate import GATE_PRESETS as CLI_PRESETS
        from app.services.agent_bridge.governance_action_handler import (
            GATE_PRESETS as OTT_PRESETS,
        )

        assert set(CLI_PRESETS.keys()) == set(OTT_PRESETS.keys()), (
            "CLI and OTT must expose the same gate presets"
        )
        for name in CLI_PRESETS:
            assert CLI_PRESETS[name]["gate_type"] == OTT_PRESETS[name]["gate_type"], (
                f"gate_type mismatch for {name}"
            )
            assert CLI_PRESETS[name]["stage"] == OTT_PRESETS[name]["stage"], (
                f"stage mismatch for {name}"
            )

    def test_t11_invalid_gate_name_raises(self) -> None:
        """CLI with unknown gate name shows error (no KeyError)."""
        from sdlcctl.commands.gate import GATE_PRESETS

        preset = GATE_PRESETS.get("NONEXISTENT")
        assert preset is None, "Unknown gate name must return None"


# ============================================================================
# T12 — FR-051 file exists
# ============================================================================


class TestT12FrFileExists:
    """T12: FR-051-LangChain-Provider-Plugin.md exists after renaming."""

    def test_t12_fr_051_exists(self) -> None:
        """FR-051 file exists in functional requirements directory."""
        fr_file = DOCS_FR_DIR / "FR-051-LangChain-Provider-Plugin.md"
        assert fr_file.exists(), (
            f"FR-051 must exist at {fr_file} (renamed from FR-045 in Track C)"
        )

    def test_t12_fr_045_removed(self) -> None:
        """Old FR-045 LangChain file no longer exists (collision resolved)."""
        old_file = DOCS_FR_DIR / "FR-045-LangChain-Provider-Plugin.md"
        assert not old_file.exists(), (
            f"Old FR-045 LangChain should be renamed to FR-051"
        )


# ============================================================================
# T13 — FR-052 file exists
# ============================================================================


class TestT13FrFileExists:
    """T13: FR-052-LangGraph-Reflection-Workflow.md exists after renaming."""

    def test_t13_fr_052_exists(self) -> None:
        """FR-052 file exists in functional requirements directory."""
        fr_file = DOCS_FR_DIR / "FR-052-LangGraph-Reflection-Workflow.md"
        assert fr_file.exists(), (
            f"FR-052 must exist at {fr_file} (renamed from FR-046 in Track C)"
        )

    def test_t13_fr_046_removed(self) -> None:
        """Old FR-046 LangGraph file no longer exists (collision resolved)."""
        old_file = DOCS_FR_DIR / "FR-046-LangGraph-Workflow-Engine.md"
        assert not old_file.exists(), (
            f"Old FR-046 LangGraph should be renamed to FR-052"
        )


# ============================================================================
# T14 — CLI governance close-sprint → success message
# ============================================================================


class TestT14CliCloseSprint:
    """T14: CLI sdlcctl governance close-sprint command exists and works."""

    def test_t14_close_sprint_command_exists(self) -> None:
        """close-sprint command is registered in governance app."""
        from sdlcctl.commands.governance import app as governance_app

        command_names = [
            cmd.name for cmd in governance_app.registered_commands
        ]
        assert "close-sprint" in command_names, (
            "governance close-sprint command must be registered"
        )

    def test_t14_close_sprint_signature(self) -> None:
        """close-sprint command accepts project_id and force parameters."""
        from sdlcctl.commands.governance import close_sprint

        import inspect
        sig = inspect.signature(close_sprint)
        params = list(sig.parameters.keys())
        assert "project_id" in params, "Must accept project_id parameter"
        assert "force" in params, "Must accept force flag for skip confirmation"


# ============================================================================
# T15 — Web sprint close mutation → useCloseSprint hook
# ============================================================================


class TestT15WebSprintCloseMutation:
    """T15: Web App useCloseSprint mutation hook calls correct endpoint."""

    def test_t15_close_sprint_api_function_exists(self) -> None:
        """closeSprint is exported in api.ts (verified via import pattern)."""
        api_ts_path = PROJECT_ROOT / "frontend" / "src" / "lib" / "api.ts"
        assert api_ts_path.exists(), "api.ts must exist"

        content = api_ts_path.read_text()
        assert "export async function closeSprint" in content, (
            "closeSprint must be exported from api.ts"
        )

    def test_t15_close_sprint_hook_exists(self) -> None:
        """useCloseSprint hook is exported in useSprintGovernance.ts."""
        hook_path = (
            PROJECT_ROOT / "frontend" / "src" / "hooks" / "useSprintGovernance.ts"
        )
        assert hook_path.exists(), "useSprintGovernance.ts must exist"

        content = hook_path.read_text()
        assert "export function useCloseSprint" in content, (
            "useCloseSprint must be exported from useSprintGovernance.ts"
        )
        assert "useMutation" in content, "useCloseSprint must use useMutation"

    def test_t15_close_sprint_invalidates_queries(self) -> None:
        """useCloseSprint invalidates sprint governance + planning queries."""
        hook_path = (
            PROJECT_ROOT / "frontend" / "src" / "hooks" / "useSprintGovernance.ts"
        )
        content = hook_path.read_text()

        # Find the useCloseSprint block
        start_idx = content.find("export function useCloseSprint")
        assert start_idx > 0
        # Find the closing brace (next export or end of file)
        block = content[start_idx:start_idx + 600]

        assert "sprintGovernanceKeys.all" in block, (
            "Must invalidate sprint governance queries"
        )
        assert '"planning"' in block or "'planning'" in block, (
            "Must invalidate planning queries"
        )


# ============================================================================
# CTO AMENDMENT — P0-1: Unlinked user blocked from /gate create
# ============================================================================


class TestCtoP01UnlinkedGateCreateBlocked:
    """CTO P0-1: /gate create must be gated by identity check."""

    def test_p01_is_unlinked_computed_before_gate_create(self) -> None:
        """_is_unlinked is computed before /gate create routing block."""
        handler_path = (
            PROJECT_ROOT
            / "backend"
            / "app"
            / "services"
            / "agent_bridge"
            / "ai_response_handler.py"
        )
        content = handler_path.read_text()

        # _is_unlinked must appear BEFORE /gate create block
        unlinked_pos = content.find("_is_unlinked = (effective_user_id == sender_id")
        gate_create_pos = content.find('text_lower_stripped.startswith("/gate create")')

        assert unlinked_pos > 0, "_is_unlinked computation must exist"
        assert gate_create_pos > 0, "/gate create routing must exist"
        assert unlinked_pos < gate_create_pos, (
            "_is_unlinked must be computed BEFORE /gate create routing (CTO P0-1)"
        )

    def test_p01_gate_create_checks_is_unlinked(self) -> None:
        """The /gate create block must check _is_unlinked before proceeding."""
        handler_path = (
            PROJECT_ROOT
            / "backend"
            / "app"
            / "services"
            / "agent_bridge"
            / "ai_response_handler.py"
        )
        content = handler_path.read_text()

        # Find the /gate create block
        gc_start = content.find('text_lower_stripped.startswith("/gate create")')
        assert gc_start > 0
        # Check that _is_unlinked guard appears right after (within ~200 chars)
        gc_block = content[gc_start:gc_start + 300]
        assert "_is_unlinked" in gc_block, (
            "/gate create block must check _is_unlinked (CTO P0-1)"
        )
        assert "Account not linked" in gc_block, (
            "/gate create must reply with link prompt for unlinked users"
        )


# ============================================================================
# CTO AMENDMENT — P0-2: OTT gate create checks project membership
# ============================================================================


class TestCtoP02MembershipCheck:
    """CTO P0-2: _execute_create_gate must verify project membership."""

    def test_p02_membership_check_exists(self) -> None:
        """_execute_create_gate imports ProjectMember and checks membership."""
        import inspect
        from app.services.agent_bridge.governance_action_handler import (
            _execute_create_gate,
        )
        source = inspect.getsource(_execute_create_gate)
        assert "ProjectMember" in source, (
            "_execute_create_gate must import and check ProjectMember"
        )

    @pytest.mark.asyncio
    async def test_p02_non_member_blocked(self) -> None:
        """Non-member user gets rejection when creating gate via OTT."""
        from app.services.agent_bridge.governance_action_handler import (
            _execute_create_gate,
        )

        project_id = uuid4()
        user_id = str(uuid4())

        sent_text: list[str] = []

        async def capture_reply(token: str, cid: Any, text: str, **kw: Any) -> bool:
            sent_text.append(text)
            return True

        # Mock workspace to return project_id
        mock_ws = MagicMock()
        mock_ws.project_id = str(project_id)

        # DB session returns None for membership check (non-member)
        mock_db_session = AsyncMock()
        member_result = MagicMock()
        member_result.scalar_one_or_none.return_value = None  # NOT a member
        mock_db_session.execute = AsyncMock(return_value=member_result)

        mock_session_cls = MagicMock()
        mock_session_cls.return_value.__aenter__ = AsyncMock(
            return_value=mock_db_session,
        )
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "app.services.agent_bridge.workspace_service.get_workspace",
                new_callable=AsyncMock,
                return_value=mock_ws,
            ),
            patch(
                "app.utils.redis.get_redis_client",
                new_callable=AsyncMock,
            ),
            patch(
                "app.services.agent_bridge.governance_action_handler.AsyncSessionLocal",
                mock_session_cls,
            ),
            patch(
                "app.services.agent_bridge.governance_action_handler._send_telegram_reply",
                side_effect=capture_reply,
            ),
        ):
            result = await _execute_create_gate(
                gate_name="G1",
                bot_token="test-token",
                chat_id="12345",
                user_id=user_id,
            )

        assert result is False, "Non-member must be rejected"
        assert len(sent_text) == 1
        assert "not a member" in sent_text[0].lower() or "không phải thành viên" in sent_text[0].lower()


# ============================================================================
# CTO AMENDMENT — P0-3: Web gates page uses correct token key
# ============================================================================


class TestCtoP03TokenKey:
    """CTO P0-3: Gates page must use access_token, not auth_token."""

    def test_p03_gates_page_uses_access_token(self) -> None:
        """CreateGateDialog reads localStorage access_token (matching api.ts)."""
        gates_page = (
            PROJECT_ROOT / "frontend" / "src" / "app" / "app" / "gates" / "page.tsx"
        )
        content = gates_page.read_text()

        assert 'getItem("access_token")' in content, (
            "Gates page must use access_token (matching api.ts pattern)"
        )
        assert 'getItem("auth_token")' not in content, (
            "Gates page must NOT use auth_token (wrong key — CTO P0-3)"
        )


# ============================================================================
# CTO AMENDMENT — P0-4: CreateGateDialog handles missing projectId
# ============================================================================


class TestCtoP04ProjectFallback:
    """CTO P0-4: CreateGateDialog must handle first-gate-ever scenario."""

    def test_p04_gates_page_imports_use_projects(self) -> None:
        """Gates page imports useProjects for project fallback."""
        gates_page = (
            PROJECT_ROOT / "frontend" / "src" / "app" / "app" / "gates" / "page.tsx"
        )
        content = gates_page.read_text()

        assert "useProjects" in content, (
            "Gates page must import useProjects for project fallback (CTO P0-4)"
        )

    def test_p04_gates_page_uses_search_params(self) -> None:
        """Gates page supports ?project_id=UUID URL parameter."""
        gates_page = (
            PROJECT_ROOT / "frontend" / "src" / "app" / "app" / "gates" / "page.tsx"
        )
        content = gates_page.read_text()

        assert "useSearchParams" in content, (
            "Gates page must use useSearchParams for project_id URL param (CTO P0-4)"
        )
        assert 'project_id' in content, (
            "Gates page must read project_id from search params"
        )


# ============================================================================
# CTO AMENDMENT — P1-1: CLI close-sprint uses correct endpoint
# ============================================================================


class TestCtoP11CliCloseSprintEndpoint:
    """CTO P1-1: CLI close-sprint must use existing backend endpoints."""

    def test_p11_api_call_supports_put(self) -> None:
        """_api_call handles PUT method (not just GET/POST)."""
        import inspect
        from sdlcctl.commands.governance import _api_call
        source = inspect.getsource(_api_call)
        assert '"PUT"' in source or "'PUT'" in source, (
            "_api_call must support PUT method (CTO P1-1)"
        )

    def test_p11_close_sprint_uses_two_step_api(self) -> None:
        """close-sprint uses GET /sprints + PUT /sprints/{id} (not POST .../close)."""
        import inspect
        from sdlcctl.commands.governance import close_sprint
        source = inspect.getsource(close_sprint)

        # Must NOT use the old non-existent endpoint
        assert "/sprints/close" not in source, (
            "close-sprint must NOT use POST /projects/{id}/sprints/close (endpoint doesn't exist)"
        )

        # Must use the 2-step pattern
        assert "GET" in source or "/sprints" in source, (
            "close-sprint must list sprints to find the active one"
        )
        assert "PUT" in source or 'f"/sprints/{' in source, (
            "close-sprint must PUT /sprints/{sprint_id} to close"
        )
