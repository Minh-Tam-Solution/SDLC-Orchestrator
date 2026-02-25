"""
Governance Action Handler — executes chat governance commands end-to-end.

Bridges ChatCommandResult (from chat_command_router.py) → real service calls
(GateService, ProjectService, MagicLinkService) → formatted Telegram reply.

Architecture (Sprint 199 Track A):
    User: "approve gate 5"
      │
      ├─ ai_response_handler.py  → detect governance intent
      ├─ chat_command_router.py  → Ollama function calling
      │   └─ tool_call: request_approval(gate_id=5, action="approve")
      │
      ├─ governance_action_handler.py  ← THIS FILE
      │   ├─ gate_service.get_gate_by_id()  → fetch gate
      │   ├─ compute_gate_actions()  → check permissions
      │   ├─ magic_link_service.generate_token()  → OOB auth (G3/G4)
      │   └─ format response  → Vietnamese/English
      │
      └─ _send_telegram_reply()  → reply to user

DB Session handling: Creates a standalone AsyncSession via AsyncSessionLocal
since this runs fire-and-forget AFTER the webhook 200 response.

Sprint 199 — Track A: Gate Actions via Chat
ADR-064 D-064-03: ALWAYS call compute_gate_actions() before mutations.
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import UUID

import httpx

from app.db.session import AsyncSessionLocal
from app.services.agent_team.chat_command_router import ChatCommandResult
from app.services.agent_team.command_registry import ToolName
from app.services.agent_team.magic_link_service import MagicLinkService

logger = logging.getLogger(__name__)

# Telegram API message length limit
_MAX_RESPONSE_LENGTH = 4000


# ──────────────────────────────────────────────────────────────────────────────
# Response formatting — Vietnamese/English bilingual (A-06)
# ──────────────────────────────────────────────────────────────────────────────


def _format_gate_status(gate: Any) -> str:
    """Format gate status for Telegram reply (A-01 response)."""
    gate_type = getattr(gate, "gate_type", None) or getattr(gate, "gate_code", "?")
    gate_name = getattr(gate, "gate_name", "") or gate_type
    status = getattr(gate, "status", "UNKNOWN")
    project_id = getattr(gate, "project_id", "?")
    evaluated_at = getattr(gate, "evaluated_at", None)
    created_at = getattr(gate, "created_at", None)

    lines = [
        f"\U0001f6e1 Gate Status / Trạng thái Gate",
        f"",
        f"\U0001f4cb Gate: {gate_name} ({gate_type})",
        f"\U0001f4ca Status: {status}",
        f"\U0001f4c1 Project ID: {project_id}",
    ]

    if evaluated_at:
        lines.append(f"\U0001f4c5 Last evaluated: {evaluated_at}")
    if created_at:
        lines.append(f"\U0001f4c5 Created: {created_at}")

    # Exit criteria summary
    exit_criteria = getattr(gate, "exit_criteria", None)
    if exit_criteria and isinstance(exit_criteria, list):
        total = len(exit_criteria)
        passed = sum(
            1 for c in exit_criteria
            if isinstance(c, dict) and c.get("passed") is True
        )
        lines.append(f"\U00002705 Exit criteria: {passed}/{total} passed")

    lines.append("")
    lines.append("Gửi 'approve gate <id>' để duyệt. / Send 'approve gate <id>' to approve.")
    return "\n".join(lines)


def _format_gate_approval_link(gate: Any, token_url: str, ttl: int) -> str:
    """Format Magic Link approval message (A-02 response)."""
    gate_type = getattr(gate, "gate_type", None) or getattr(gate, "gate_code", "?")
    gate_name = getattr(gate, "gate_name", "") or gate_type
    status = getattr(gate, "status", "UNKNOWN")

    return (
        f"\U0001f512 Gate Approval / Duyệt Gate\n"
        f"\n"
        f"\U0001f4cb Gate: {gate_name} ({gate_type})\n"
        f"\U0001f4ca Current status: {status}\n"
        f"\n"
        f"\u26a0\ufe0f Gate này yêu cầu xác thực OOB (Out-of-Band).\n"
        f"Click link bên dưới để xác nhận duyệt gate:\n"
        f"\n"
        f"\U0001f517 {token_url}\n"
        f"\n"
        f"\u23f0 Link hết hạn sau {ttl // 60} phút. / Link expires in {ttl // 60} min.\n"
        f"\U0001f6ab Single-use — chỉ dùng được 1 lần."
    )


def _format_gate_approved_direct(gate: Any) -> str:
    """Format direct gate approval confirmation (no Magic Link needed)."""
    gate_type = getattr(gate, "gate_type", None) or getattr(gate, "gate_code", "?")
    gate_name = getattr(gate, "gate_name", "") or gate_type

    return (
        f"\u2705 Gate Approved / Gate đã được duyệt\n"
        f"\n"
        f"\U0001f4cb Gate: {gate_name} ({gate_type})\n"
        f"\U0001f4ca Status: APPROVED\n"
        f"\n"
        f"Gate đã được duyệt thành công qua OTT chat."
    )


def _format_gate_rejected(gate: Any) -> str:
    """Format gate rejection confirmation."""
    gate_type = getattr(gate, "gate_type", None) or getattr(gate, "gate_code", "?")
    gate_name = getattr(gate, "gate_name", "") or gate_type

    return (
        f"\u274c Gate Rejected / Gate bị từ chối\n"
        f"\n"
        f"\U0001f4cb Gate: {gate_name} ({gate_type})\n"
        f"\U0001f4ca Status: REJECTED\n"
        f"\n"
        f"Gate đã bị từ chối qua OTT chat."
    )


def _format_error(message: str) -> str:
    """Format error message."""
    return f"\u26a0\ufe0f Lỗi / Error\n\n{message}"


# ──────────────────────────────────────────────────────────────────────────────
# Telegram reply helper
# ──────────────────────────────────────────────────────────────────────────────


async def _send_telegram_reply(
    bot_token: str,
    chat_id: str | int,
    text: str,
    channel: str = "telegram",
) -> bool:
    """
    Send reply message to OTT channel (Sprint 200 C-01).

    Routes to Telegram Bot API or Zalo OA based on channel parameter.
    """
    # Sprint 200 C-01: Zalo channel routing
    if channel == "zalo":
        from app.services.agent_bridge.zalo_responder import send_progress_message
        return await send_progress_message(
            user_id=str(chat_id), text=text[:_MAX_RESPONSE_LENGTH],
        )

    if not bot_token:
        return False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text[:_MAX_RESPONSE_LENGTH],
                },
            )
            if resp.status_code == 200:
                logger.info(
                    "governance_handler: reply sent chat_id=%s len=%d",
                    chat_id,
                    len(text),
                )
                return True
            logger.warning(
                "governance_handler: sendMessage failed status=%s",
                resp.status_code,
            )
            return False
    except Exception as exc:
        logger.warning(
            "governance_handler: sendMessage error chat_id=%s error=%s",
            chat_id,
            str(exc),
        )
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Command Execution — Gate Status (A-01)
# ──────────────────────────────────────────────────────────────────────────────


async def _execute_gate_status(
    tool_args: dict[str, Any],
    bot_token: str,
    chat_id: str | int,
    user_id: str,
    channel: str = "telegram",
) -> bool:
    """
    Execute get_gate_status command — fetch gate info and reply.

    Supports lookup by gate_id (UUID) or project_id (int).
    """
    from app.services.gate_service import GateService

    gate_id_str: Optional[str] = tool_args.get("gate_id")
    project_id: Optional[int] = tool_args.get("project_id")

    async with AsyncSessionLocal() as db:
        gate_svc = GateService(db)

        if gate_id_str:
            try:
                gid = UUID(str(gate_id_str))
            except ValueError:
                await _send_telegram_reply(
                    bot_token, chat_id,
                    _format_error(f"Invalid gate ID: {gate_id_str}"),
                    channel=channel,
                )
                return False

            gate = await gate_svc.get_gate_by_id(gid)
            if not gate:
                await _send_telegram_reply(
                    bot_token, chat_id,
                    _format_error(f"Gate not found: {gate_id_str}"),
                    channel=channel,
                )
                return False

            reply = _format_gate_status(gate)
            return await _send_telegram_reply(bot_token, chat_id, reply, channel=channel)

        elif project_id:
            gates = await gate_svc.list_gates_by_project(UUID(int=project_id) if isinstance(project_id, int) and project_id < 1000 else UUID(str(project_id)))
            if not gates:
                await _send_telegram_reply(
                    bot_token, chat_id,
                    _format_error(f"No gates found for project {project_id}."),
                    channel=channel,
                )
                return False

            # Format summary of all gates for the project
            lines = [
                f"\U0001f6e1 Gate Summary / Tổng quan Gates — Project {project_id}",
                "",
            ]
            for g in gates:
                gtype = getattr(g, "gate_type", None) or getattr(g, "gate_code", "?")
                gstatus = getattr(g, "status", "?")
                gid = getattr(g, "id", "?")
                icon = "\u2705" if gstatus == "APPROVED" else "\u274c" if gstatus == "REJECTED" else "\U0001f7e1"
                lines.append(f"  {icon} {gtype}: {gstatus} (ID: {gid})")
            lines.append("")
            lines.append("Gửi 'gate status <gate_id>' để xem chi tiết.")

            return await _send_telegram_reply(bot_token, chat_id, "\n".join(lines), channel=channel)

        else:
            await _send_telegram_reply(
                bot_token, chat_id,
                _format_error(
                    "Vui lòng cung cấp gate_id hoặc project_id.\n"
                    "Please provide gate_id or project_id.\n\n"
                    "Ví dụ / Example: 'gate status 5' or 'trạng thái gate <uuid>'"
                ),
                channel=channel,
            )
            return False


# ──────────────────────────────────────────────────────────────────────────────
# Command Execution — Gate Approval/Rejection (A-02)
# ──────────────────────────────────────────────────────────────────────────────


async def _execute_request_approval(
    tool_args: dict[str, Any],
    bot_token: str,
    chat_id: str | int,
    user_id: str,
    channel: str = "telegram",
) -> bool:
    """
    Execute request_approval command — approve/reject gate with OOB auth.

    Flow (ADR-064 D-064-03):
        1. Fetch gate from DB
        2. Call compute_gate_actions() to check permissions
        3. If requires_oob_auth (G3/G4) → generate Magic Link
        4. Else → approve/reject directly
        5. Send formatted reply
    """
    from app.models.user import User as UserModel
    from app.services.gate_service import GateService, compute_gate_actions

    gate_id_str: str = str(tool_args.get("gate_id", ""))
    action: str = tool_args.get("action", "approve")

    try:
        gate_id = UUID(gate_id_str)
    except ValueError:
        await _send_telegram_reply(
            bot_token, chat_id,
            _format_error(f"Invalid gate ID: {gate_id_str}"),
            channel=channel,
        )
        return False

    async with AsyncSessionLocal() as db:
        gate_svc = GateService(db)

        # 1. Fetch gate
        gate = await gate_svc.get_gate_by_id(gate_id)
        if not gate:
            await _send_telegram_reply(
                bot_token, chat_id,
                _format_error(f"Gate not found: {gate_id_str}"),
                channel=channel,
            )
            return False

        # 2. Check permissions via compute_gate_actions (D-064-03)
        from sqlalchemy import select
        user_result = await db.execute(
            select(UserModel).where(UserModel.id == UUID(user_id))
        )
        user = user_result.scalar_one_or_none()
        if not user:
            await _send_telegram_reply(
                bot_token, chat_id,
                _format_error(
                    "Không tìm thấy tài khoản của bạn. Vui lòng đăng ký trước.\n"
                    "User account not found. Please register first."
                ),
                channel=channel,
            )
            return False

        actions = await compute_gate_actions(gate, user, db)

        # 3. Check if the requested action is allowed
        action_key = f"can_{action}"
        if not actions.get("actions", {}).get(action_key, False):
            reason = actions.get("reasons", {}).get(action_key, "Action not permitted")
            await _send_telegram_reply(
                bot_token, chat_id,
                _format_error(
                    f"Không thể {action} gate này.\n"
                    f"Cannot {action} this gate.\n\n"
                    f"Lý do / Reason: {reason}"
                ),
                channel=channel,
            )
            return False

        # 4. Check if OOB auth required (G3/G4 gates)
        requires_oob = actions.get("requires_oob_auth", False)

        if requires_oob:
            ml_service = MagicLinkService()
            token = await ml_service.generate_token(
                gate_id=str(gate_id),
                action=action,
                user_id=user_id,
            )
            reply = _format_gate_approval_link(gate, token.url, token.ttl_seconds)
            return await _send_telegram_reply(bot_token, chat_id, reply, channel=channel)

        # 5. Direct approve/reject (G0.1, G0.2, G1, G2)
        if action == "approve":
            updated_gate = await gate_svc.approve_gate(
                gate_id=gate_id,
                approver_id=UUID(user_id),
            )
            await db.commit()
            reply = _format_gate_approved_direct(updated_gate)
        else:
            updated_gate = await gate_svc.reject_gate(
                gate_id=gate_id,
                approver_id=UUID(user_id),
                rejection_reason="Rejected via OTT chat",
            )
            await db.commit()
            reply = _format_gate_rejected(updated_gate)

        return await _send_telegram_reply(bot_token, chat_id, reply, channel=channel)


# ──────────────────────────────────────────────────────────────────────────────
# Main Dispatch — route ChatCommandResult to handler
# ──────────────────────────────────────────────────────────────────────────────


async def execute_governance_action(
    result: ChatCommandResult,
    bot_token: str,
    chat_id: str | int,
    user_id: str,
    channel: str = "telegram",
) -> bool:
    """
    Execute a validated governance command from ChatCommandResult.

    This is the main entry point called from ott_gateway.py (or
    ai_response_handler.py) after chat_command_router returns a
    validated tool call.

    Args:
        result: Validated ChatCommandResult from route_chat_command()
        bot_token: Bot API token (Telegram only; empty for Zalo).
        chat_id: OTT chat/user ID for reply target.
        user_id: Authenticated user ID (from OTT identity mapping).
        channel: OTT channel ("telegram" or "zalo").

    Returns:
        True if action executed and reply sent, False on error.
    """
    if not result.is_tool_call:
        if result.response_text:
            return await _send_telegram_reply(bot_token, chat_id, result.response_text, channel=channel)
        if result.error:
            return await _send_telegram_reply(
                bot_token, chat_id, _format_error(result.error), channel=channel,
            )
        return False

    tool_name = result.tool_name
    tool_args = result.tool_args or {}

    logger.info(
        "governance_handler: executing tool=%s args=%s user=%s chat_id=%s channel=%s",
        tool_name, tool_args, user_id, chat_id, channel,
    )

    try:
        if tool_name == ToolName.GET_GATE_STATUS.value:
            return await _execute_gate_status(tool_args, bot_token, chat_id, user_id, channel=channel)

        elif tool_name == ToolName.REQUEST_APPROVAL.value:
            return await _execute_request_approval(tool_args, bot_token, chat_id, user_id, channel=channel)

        elif tool_name == ToolName.CREATE_PROJECT.value:
            name = tool_args.get("name", "?")
            await _send_telegram_reply(
                bot_token, chat_id,
                f"\U0001f4e6 Create Project / Tạo dự án\n\n"
                f"Project name: {name}\n\n"
                f"\u26a0\ufe0f Tính năng tạo project qua chat đang phát triển.\n"
                f"Feature coming in Sprint 199 A-03.\n"
                f"Vui lòng sử dụng Web Dashboard: https://sdlc.nhatquangholding.com",
                channel=channel,
            )
            return True

        elif tool_name == ToolName.SUBMIT_EVIDENCE.value:
            await _send_telegram_reply(
                bot_token, chat_id,
                f"\U0001f4ce Submit Evidence / Nộp bằng chứng\n\n"
                f"\u26a0\ufe0f Gửi file đính kèm (PDF, image) để upload evidence.\n"
                f"Attach a file (PDF, image) to upload evidence.\n"
                f"Feature coming in Sprint 199 Track B.",
                channel=channel,
            )
            return True

        elif tool_name == ToolName.EXPORT_AUDIT.value:
            from app.services.agent_bridge.sprint_governance_handler import (
                handle_export_audit,
            )
            return await handle_export_audit(
                tool_args, bot_token, chat_id, user_id, channel=channel,
            )

        elif tool_name == ToolName.UPDATE_SPRINT.value:
            project_id = tool_args.get("project_id")
            await _send_telegram_reply(
                bot_token, chat_id,
                f"\U0001f504 Update Sprint / Cập nhật Sprint\n\n"
                f"Project: {project_id}\n\n"
                f"\u26a0\ufe0f Sprint update qua chat đang phát triển.\n"
                f"Vui lòng sử dụng CLI: sdlcctl update-sprint --project {project_id}",
                channel=channel,
            )
            return True

        elif tool_name == ToolName.CLOSE_SPRINT.value:
            from app.services.agent_bridge.sprint_governance_handler import (
                handle_close_sprint,
            )
            return await handle_close_sprint(
                tool_args, bot_token, chat_id, user_id, channel=channel,
            )

        elif tool_name == ToolName.INVITE_MEMBER.value:
            from app.services.agent_bridge.team_invite_handler import (
                handle_invite_member,
            )
            return await handle_invite_member(
                tool_args, bot_token, chat_id, user_id, channel=channel,
            )

        else:
            await _send_telegram_reply(
                bot_token, chat_id,
                _format_error(f"Unknown command: {tool_name}"),
                channel=channel,
            )
            return False

    except Exception as exc:
        logger.error(
            "governance_handler: execution failed tool=%s error=%s",
            tool_name, str(exc),
        )
        await _send_telegram_reply(
            bot_token, chat_id,
            _format_error(
                f"Lỗi khi thực hiện lệnh: {tool_name}\n"
                f"Error executing command: {str(exc)[:200]}\n\n"
                f"Vui lòng thử lại hoặc gửi /help."
            ),
            channel=channel,
        )
        return False
