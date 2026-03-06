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

# Sprint 207: Tier display emojis (FR-049)
_TIER_EMOJI = {
    "LITE": "\U0001f7e2",        # green circle
    "STANDARD": "\U0001f535",     # blue circle
    "PROFESSIONAL": "\U0001f7e3", # purple circle
    "ENTERPRISE": "\U0001f7e0",   # orange circle
}


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
# Sprint 208: Chat-native project creation, evidence submission, sprint update
# ──────────────────────────────────────────────────────────────────────────────


async def _execute_create_project(
    tool_args: dict[str, Any],
    bot_token: str,
    chat_id: str | int,
    user_id: str,
    channel: str = "telegram",
) -> bool:
    """
    Create a new project via OTT chat — direct async ORM (RF-01).

    Uses direct SQLAlchemy async ORM instead of project_service.create_project()
    which requires a sync Session. The governance handler's AsyncSessionLocal
    requires async operations throughout.

    Slug generation: lowercase, regex clean, truncate to 255 chars.
    On unique-slug collision: appends hex suffix from uuid4.

    Args:
        tool_args: {"name": str, "description"?: str}
        bot_token: Telegram Bot API token.
        chat_id: Chat ID for reply.
        user_id: Authenticated user UUID string.
        channel: OTT channel identifier.

    Returns:
        True on success, False on error.
    """
    import re
    from uuid import uuid4
    from sqlalchemy import select
    from app.models.project import Project, ProjectMember

    name = (tool_args.get("name") or "").strip()
    if not name:
        await _send_telegram_reply(
            bot_token, chat_id,
            _format_error(
                "Vui lòng cung cấp tên dự án.\n"
                "Please provide a project name.\n\n"
                "Ví dụ / Example: create project E-Commerce Platform"
            ),
            channel=channel,
        )
        return False

    description = (tool_args.get("description") or "").strip() or None

    # Generate slug: lowercase, alphanumeric + hyphens, max 255
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:245]

    try:
        async with AsyncSessionLocal() as db:
            # Check slug uniqueness, append suffix on collision
            existing = await db.execute(
                select(Project.id).where(Project.slug == slug)
            )
            if existing.scalar_one_or_none() is not None:
                slug = f"{slug}-{uuid4().hex[:6]}"

            project = Project(
                name=name,
                slug=slug,
                description=description,
                owner_id=UUID(user_id),
                is_active=True,
            )
            db.add(project)
            await db.flush()

            # Auto-add creator as owner member
            member = ProjectMember(
                project_id=project.id,
                user_id=UUID(user_id),
                role="owner",
            )
            db.add(member)
            await db.commit()

            tier = getattr(project, "policy_pack_tier", "PROFESSIONAL")
            tier_emoji = _TIER_EMOJI.get(tier, "\U0001f7e2")

            reply = (
                f"\u2705 Project Created / Dự án đã tạo\n\n"
                f"\U0001f4c1 Name: {project.name}\n"
                f"\U0001f517 Slug: {project.slug}\n"
                f"\U0001f194 ID: {project.id}\n"
                f"{tier_emoji} Tier: {tier}\n"
            )
            if description:
                reply += f"\U0001f4dd Description: {description}\n"
            reply += (
                f"\nDùng /workspace set {project.name} để chọn project này.\n"
                f"Use /workspace set {project.name} to select this project."
            )
            return await _send_telegram_reply(bot_token, chat_id, reply, channel=channel)

    except Exception as exc:
        logger.error("create_project failed: %s", exc)
        await _send_telegram_reply(
            bot_token, chat_id,
            _format_error(
                f"Lỗi tạo dự án: {str(exc)[:200]}\n"
                f"Error creating project: {str(exc)[:200]}"
            ),
            channel=channel,
        )
        return False


async def _execute_submit_evidence(
    tool_args: dict[str, Any],
    bot_token: str,
    chat_id: str | int,
    user_id: str,
    channel: str = "telegram",
) -> bool:
    """
    Submit text-only evidence via OTT chat — direct GateEvidence ORM (RF-02).

    Creates a GateEvidence record for text-based evidence submissions
    (e.g., notes, descriptions, test results pasted in chat). File-based
    evidence still requires web dashboard or CLI.

    GateEvidence NOT NULL constraints require synthetic file metadata for
    text-only submissions:
        file_name = "ott-evidence-{uuid}.txt"
        file_size = len(description.encode("utf-8"))
        file_type = "text/plain"
        s3_key = "ott-text/{gate_id}/{evidence_id}.txt" (no actual S3 upload)

    Args:
        tool_args: {"gate_id": str, "description": str, "evidence_type"?: str}
        bot_token: Telegram Bot API token.
        chat_id: Chat ID for reply.
        user_id: Authenticated user UUID string.
        channel: OTT channel identifier.

    Returns:
        True on success, False on error.
    """
    from uuid import uuid4
    from sqlalchemy import select
    from app.models.gate_evidence import GateEvidence
    from app.models.gate import Gate

    gate_id_str = (tool_args.get("gate_id") or "").strip()
    description = (tool_args.get("description") or "").strip()
    evidence_type = (tool_args.get("evidence_type") or "DOCUMENTATION").strip().upper()

    if not gate_id_str:
        await _send_telegram_reply(
            bot_token, chat_id,
            _format_error(
                "Vui lòng cung cấp gate ID.\n"
                "Please provide a gate_id.\n\n"
                "Ví dụ / Example: submit evidence gate_id=<uuid> description=\"Test results passed\""
            ),
            channel=channel,
        )
        return False

    if not description:
        await _send_telegram_reply(
            bot_token, chat_id,
            _format_error(
                "Vui lòng cung cấp mô tả evidence.\n"
                "Please provide a description for the evidence."
            ),
            channel=channel,
        )
        return False

    try:
        gate_id = UUID(gate_id_str)
    except ValueError:
        await _send_telegram_reply(
            bot_token, chat_id,
            _format_error(f"Invalid gate ID: {gate_id_str}"),
            channel=channel,
        )
        return False

    try:
        async with AsyncSessionLocal() as db:
            # Verify gate exists
            gate_result = await db.execute(
                select(Gate).where(Gate.id == gate_id)
            )
            gate = gate_result.scalar_one_or_none()
            if not gate:
                await _send_telegram_reply(
                    bot_token, chat_id,
                    _format_error(f"Gate not found: {gate_id_str}"),
                    channel=channel,
                )
                return False

            evidence_id = uuid4()
            text_bytes = description.encode("utf-8")

            evidence = GateEvidence(
                id=evidence_id,
                gate_id=gate_id,
                file_name=f"ott-evidence-{evidence_id.hex[:8]}.txt",
                file_size=len(text_bytes),
                file_type="text/plain",
                evidence_type=evidence_type,
                s3_key=f"ott-text/{gate_id}/{evidence_id}.txt",
                s3_bucket="sdlc-evidence",
                description=description,
                source="ott",
                uploaded_by=UUID(user_id),
            )
            db.add(evidence)
            await db.commit()

            gate_type = getattr(gate, "gate_type", None) or getattr(gate, "gate_code", "?")
            reply = (
                f"\u2705 Evidence Submitted / Bằng chứng đã nộp\n\n"
                f"\U0001f4cb Gate: {gate_type}\n"
                f"\U0001f4c4 Type: {evidence_type}\n"
                f"\U0001f194 Evidence ID: {evidence_id}\n"
                f"\U0001f4dd Description: {description[:200]}\n"
                f"\U0001f4e4 Source: OTT ({channel})\n\n"
                f"Đính kèm file (PDF, image) để upload evidence đầy đủ.\n"
                f"Attach a file for full evidence upload via web dashboard."
            )
            return await _send_telegram_reply(bot_token, chat_id, reply, channel=channel)

    except Exception as exc:
        logger.error("submit_evidence failed: %s", exc)
        await _send_telegram_reply(
            bot_token, chat_id,
            _format_error(
                f"Lỗi nộp evidence: {str(exc)[:200]}\n"
                f"Error submitting evidence: {str(exc)[:200]}"
            ),
            channel=channel,
        )
        return False


async def _execute_update_sprint(
    tool_args: dict[str, Any],
    bot_token: str,
    chat_id: str | int,
    user_id: str,
    channel: str = "telegram",
) -> bool:
    """
    Execute update_sprint command via OTT chat.

    Delegates to sprint_command_handler.handle_update_sprint() which:
    1. Fetches active sprint for the project
    2. Generates CURRENT-SPRINT.md via SprintFileService
    3. Pushes to GitHub (if configured)
    4. Returns confirmation summary

    Args:
        tool_args: {"project_id": str}
        bot_token: Telegram Bot API token.
        chat_id: Chat ID for reply.
        user_id: Authenticated user UUID string.
        channel: OTT channel identifier.

    Returns:
        True on success, False on error.
    """
    from app.services.agent_team.sprint_command_handler import handle_update_sprint

    project_id_str = (tool_args.get("project_id") or "").strip()
    if not project_id_str:
        await _send_telegram_reply(
            bot_token, chat_id,
            _format_error(
                "Vui lòng cung cấp project_id.\n"
                "Please provide a project_id.\n\n"
                "Ví dụ / Example: update sprint project_id=<uuid>\n"
                "Hoặc set workspace trước: /workspace set <project-name>"
            ),
            channel=channel,
        )
        return False

    try:
        project_id = UUID(project_id_str)
    except ValueError:
        await _send_telegram_reply(
            bot_token, chat_id,
            _format_error(f"Invalid project ID: {project_id_str}"),
            channel=channel,
        )
        return False

    try:
        async with AsyncSessionLocal() as db:
            result = await handle_update_sprint(db, project_id)

        status = result.get("status", "error")
        if status == "error":
            await _send_telegram_reply(
                bot_token, chat_id,
                _format_error(result.get("message", "Unknown error")),
                channel=channel,
            )
            return False

        sprint_name = result.get("sprint_name", "?")
        content_len = result.get("content_length", 0)
        commit_sha = result.get("commit_sha")
        message = result.get("message", "Sprint updated")

        lines = [
            f"\U0001f504 Sprint Updated / Sprint đã cập nhật",
            f"",
            f"\U0001f3af Sprint: {sprint_name}",
            f"\U0001f4c4 CURRENT-SPRINT.md: {content_len} chars",
        ]
        if commit_sha:
            lines.append(f"\U0001f517 GitHub commit: {commit_sha[:8]}")
        lines.append(f"\n{message}")

        return await _send_telegram_reply(
            bot_token, chat_id, "\n".join(lines), channel=channel,
        )

    except Exception as exc:
        logger.error("update_sprint failed: %s", exc)
        await _send_telegram_reply(
            bot_token, chat_id,
            _format_error(
                f"Lỗi cập nhật sprint: {str(exc)[:200]}\n"
                f"Error updating sprint: {str(exc)[:200]}"
            ),
            channel=channel,
        )
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Sprint 207: Workspace Command Execution (FR-049, ADR-067)
# ──────────────────────────────────────────────────────────────────────────────


async def execute_workspace_command(
    subcommand: str,
    args_text: str,
    bot_token: str,
    chat_id: str | int,
    user_id: str,
    channel: str = "telegram",
) -> bool:
    """
    Dispatch workspace subcommands: set, info, list, clear.

    Called from ai_response_handler.py BEFORE route_chat_command() to bypass
    the LLM router (no ToolName slot available, MAX_COMMANDS=10 reached).

    All DB-requiring workspace operations live here (NOT in ai_response_handler)
    because governance_action_handler creates AsyncSessionLocal per command.
    """
    from app.services.agent_bridge.workspace_service import (
        get_workspace,
        set_workspace,
        clear_workspace,
        touch_workspace_ttl,
        resolve_project_by_name,
        is_uuid,
        WorkspaceContext,
    )
    from app.utils.redis import get_redis_client
    from app.models.project import Project, ProjectMember
    from sqlalchemy import select

    redis = await get_redis_client()

    if subcommand == "set":
        if not args_text:
            return await _send_telegram_reply(
                bot_token, chat_id,
                _format_error(
                    "Vui lòng cung cấp tên hoặc UUID project.\n"
                    "Usage: /workspace set <project-name-or-uuid>"
                ),
                channel=channel,
            )

        async with AsyncSessionLocal() as db:
            # UUID direct path
            if is_uuid(args_text.strip()):
                project_uuid = args_text.strip()
                from sqlalchemy import select as sel
                stmt = sel(Project).where(
                    Project.id == project_uuid,
                    Project.is_active.is_(True),
                )
                result = await db.execute(stmt)
                project = result.scalar_one_or_none()
                if not project:
                    return await _send_telegram_reply(
                        bot_token, chat_id,
                        f"\u274c Project not found: {project_uuid}\n"
                        f"Use /workspace list to see your projects.",
                        channel=channel,
                    )
                # Check membership
                mem_stmt = sel(ProjectMember).where(
                    ProjectMember.project_id == project_uuid,
                    ProjectMember.user_id == user_id,
                )
                mem_result = await db.execute(mem_stmt)
                if not mem_result.scalar_one_or_none():
                    return await _send_telegram_reply(
                        bot_token, chat_id,
                        f"\u274c Access denied. You are not a member of '{project.name}'.\n"
                        f"Contact your project owner to be added.",
                        channel=channel,
                    )
                matched_project = project
            else:
                # Name-based search
                search_result = await resolve_project_by_name(
                    args_text.strip(), user_id, db,
                )
                exact = search_result["exact"]
                matches = search_result["matches"]

                if not matches:
                    return await _send_telegram_reply(
                        bot_token, chat_id,
                        f"\u274c Project '{args_text.strip()}' not found.\n"
                        f"Use /workspace list to see your projects.",
                        channel=channel,
                    )

                if not exact and len(matches) > 1:
                    # Disambiguation list (D-067-03)
                    lines = [
                        f"\U0001f50d Multiple projects match '{args_text.strip()}'. "
                        f"Use UUID to set exactly:",
                    ]
                    for i, p in enumerate(matches[:5], 1):
                        tier = getattr(p, "tier", "STANDARD") or "STANDARD"
                        emoji = _TIER_EMOJI.get(tier, "\u26aa")
                        lines.append(
                            f"  {i}. {emoji} {p.name} ({tier})\n"
                            f"     /workspace set {p.id}"
                        )
                    if len(matches) > 5:
                        lines.append(f"  ...and more. Use a more specific name.")
                    lines.append("\nUse the exact UUID above, or try a more specific name.")
                    return await _send_telegram_reply(
                        bot_token, chat_id, "\n".join(lines), channel=channel,
                    )

                matched_project = exact

            # Set workspace
            tier = getattr(matched_project, "tier", "STANDARD") or "STANDARD"
            stage = getattr(matched_project, "sdlc_stage", "") or ""
            try:
                # Read previous workspace for group override notice
                prev_ws = await get_workspace(channel, chat_id, redis)
                await set_workspace(
                    channel, chat_id,
                    str(matched_project.id),
                    matched_project.name,
                    tier, stage, user_id, redis,
                )
            except Exception:
                return await _send_telegram_reply(
                    bot_token, chat_id,
                    "\u26a0\ufe0f Workspace service temporarily unavailable. "
                    "Try again in a moment.",
                    channel=channel,
                )

            emoji = _TIER_EMOJI.get(tier, "\u26aa")
            reply = (
                f"\u2705 Workspace set to: {matched_project.name}\n"
                f"Tier: {emoji} {tier} | Stage: {stage or 'N/A'}\n"
                f"All governance commands will use this project.\n"
                f"Type /workspace to check anytime."
            )
            # Group override notice (FR-049-06 P0-4)
            if prev_ws and prev_ws.project_id != str(matched_project.id):
                reply += (
                    f"\n\u26a0\ufe0f Previous workspace ({prev_ws.project_name} "
                    f"set by {prev_ws.set_by}) was overridden."
                )
            return await _send_telegram_reply(bot_token, chat_id, reply, channel=channel)

    elif subcommand == "info":
        ws = await get_workspace(channel, chat_id, redis)
        if not ws:
            return await _send_telegram_reply(
                bot_token, chat_id,
                "\U0001f4c2 No active workspace.\n"
                "Set one with: /workspace set <project-name>\n"
                "List your projects: /workspace list",
                channel=channel,
            )
        # Touch TTL on info view (D-067-02)
        await touch_workspace_ttl(channel, chat_id, redis)
        emoji = _TIER_EMOJI.get(ws.tier, "\u26aa")
        return await _send_telegram_reply(
            bot_token, chat_id,
            f"\U0001f4c2 Active Workspace\n"
            f"\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"
            f"\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
            f"Project: {ws.project_name}\n"
            f"Tier: {emoji} {ws.tier}\n"
            f"Stage: {ws.sdlc_stage or 'N/A'}\n"
            f"Set by: {ws.set_by}\n\n"
            f"Commands: /gates /approve /evidence /sprint_status",
            channel=channel,
        )

    elif subcommand == "list":
        # Touch TTL on list view (D-067-02)
        await touch_workspace_ttl(channel, chat_id, redis)
        ws = await get_workspace(channel, chat_id, redis)
        active_id = ws.project_id if ws else None

        async with AsyncSessionLocal() as db:
            stmt = (
                select(Project)
                .join(ProjectMember, ProjectMember.project_id == Project.id)
                .where(
                    ProjectMember.user_id == user_id,
                    Project.is_active.is_(True),
                )
                .order_by(Project.name)
                .limit(10)
            )
            result = await db.execute(stmt)
            projects = list(result.scalars().all())

        if not projects:
            return await _send_telegram_reply(
                bot_token, chat_id,
                "\U0001f4cb No projects found.\n"
                "Create one via the web dashboard or ask your admin.",
                channel=channel,
            )

        lines = [
            "\U0001f4cb Your Projects",
            "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"
            "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500",
        ]
        for p in projects:
            tier = getattr(p, "tier", "STANDARD") or "STANDARD"
            emoji = _TIER_EMOJI.get(tier, "\u26aa")
            stage = getattr(p, "sdlc_stage", "") or ""
            marker = "\u25b6" if str(p.id) == active_id else "\u25cb"
            active_tag = " [ACTIVE]" if str(p.id) == active_id else ""
            lines.append(f"{marker} {emoji} {p.name}{active_tag}")
            if stage:
                lines.append(f"   Stage: {stage}")
        lines.append("")
        lines.append("Switch with: /workspace set <name>")

        return await _send_telegram_reply(
            bot_token, chat_id, "\n".join(lines), channel=channel,
        )

    elif subcommand == "clear":
        ws = await get_workspace(channel, chat_id, redis)
        if not ws:
            return await _send_telegram_reply(
                bot_token, chat_id,
                "\U0001f4c2 No active workspace to clear.",
                channel=channel,
            )
        prev_name = ws.project_name
        try:
            await clear_workspace(channel, chat_id, redis)
        except Exception:
            return await _send_telegram_reply(
                bot_token, chat_id,
                "\u26a0\ufe0f Workspace service temporarily unavailable. "
                "Try again in a moment.",
                channel=channel,
            )
        return await _send_telegram_reply(
            bot_token, chat_id,
            f"\U0001f5d1 Workspace cleared (was: {prev_name}). No active project.\n"
            f"Use /workspace set <name> to set a new one.",
            channel=channel,
        )

    else:
        return await _send_telegram_reply(
            bot_token, chat_id,
            _format_error(
                f"Unknown workspace subcommand: {subcommand}\n"
                f"Available: /workspace set, /workspace, /workspace list, /workspace clear"
            ),
            channel=channel,
        )


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

    # ── Sprint 207: Workspace project_id injection (D-067-04) ──
    # If tool_args lacks project_id, resolve from workspace (4-level priority).
    # Track whether workspace was used so we can touch TTL after success.
    workspace_used = False
    _COMMANDS_NEEDING_PROJECT = {
        ToolName.GET_GATE_STATUS.value,
        ToolName.SUBMIT_EVIDENCE.value,
        ToolName.EXPORT_AUDIT.value,
        ToolName.UPDATE_SPRINT.value,
        ToolName.CLOSE_SPRINT.value,
    }
    if tool_name in _COMMANDS_NEEDING_PROJECT and not tool_args.get("project_id"):
        try:
            from app.services.agent_bridge.workspace_service import resolve_project_id
            from app.utils.redis import get_redis_client
            redis = await get_redis_client()
            resolved_id, ws_used = await resolve_project_id(
                explicit_id=None,
                channel=channel,
                chat_id=chat_id,
                redis=redis,
            )
            if resolved_id:
                tool_args["project_id"] = resolved_id
                workspace_used = ws_used
                logger.info(
                    "governance_handler: workspace injected project_id=%s ws_used=%s",
                    resolved_id, ws_used,
                )
        except Exception as exc:
            logger.warning(
                "governance_handler: workspace resolution failed error=%s",
                str(exc),
            )

    logger.info(
        "governance_handler: executing tool=%s args=%s user=%s chat_id=%s channel=%s",
        tool_name, tool_args, user_id, chat_id, channel,
    )

    try:
        handled = False

        if tool_name == ToolName.GET_GATE_STATUS.value:
            handled = await _execute_gate_status(tool_args, bot_token, chat_id, user_id, channel=channel)

        elif tool_name == ToolName.REQUEST_APPROVAL.value:
            handled = await _execute_request_approval(tool_args, bot_token, chat_id, user_id, channel=channel)

        elif tool_name == ToolName.CREATE_PROJECT.value:
            handled = await _execute_create_project(
                tool_args, bot_token, chat_id, user_id, channel=channel,
            )

        elif tool_name == ToolName.SUBMIT_EVIDENCE.value:
            handled = await _execute_submit_evidence(
                tool_args, bot_token, chat_id, user_id, channel=channel,
            )

        elif tool_name == ToolName.EXPORT_AUDIT.value:
            from app.services.agent_bridge.sprint_governance_handler import (
                handle_export_audit,
            )
            handled = await handle_export_audit(
                tool_args, bot_token, chat_id, user_id, channel=channel,
            )

        elif tool_name == ToolName.UPDATE_SPRINT.value:
            handled = await _execute_update_sprint(
                tool_args, bot_token, chat_id, user_id, channel=channel,
            )

        elif tool_name == ToolName.CLOSE_SPRINT.value:
            from app.services.agent_bridge.sprint_governance_handler import (
                handle_close_sprint,
            )
            handled = await handle_close_sprint(
                tool_args, bot_token, chat_id, user_id, channel=channel,
            )

        elif tool_name == ToolName.INVITE_MEMBER.value:
            from app.services.agent_bridge.team_invite_handler import (
                handle_invite_member,
            )
            handled = await handle_invite_member(
                tool_args, bot_token, chat_id, user_id, channel=channel,
            )

        # Sprint 223: Wire RUN_EVALS + LIST_NOTES (dispatch-only, no registry change)
        elif tool_name == ToolName.RUN_EVALS.value:
            handled = await _execute_run_evals(
                tool_args, bot_token, chat_id, user_id, channel=channel,
            )

        elif tool_name == ToolName.LIST_NOTES.value:
            handled = await _execute_list_notes(
                tool_args, bot_token, chat_id, user_id, channel=channel,
            )

        else:
            await _send_telegram_reply(
                bot_token, chat_id,
                _format_error(f"Unknown command: {tool_name}"),
                channel=channel,
            )
            return False

        # ── Sprint 207: Touch workspace TTL after successful execution ──
        # Only when workspace-injected project_id was used (D-067-02).
        if handled and workspace_used:
            try:
                from app.services.agent_bridge.workspace_service import (
                    touch_workspace_ttl,
                )
                from app.utils.redis import get_redis_client
                redis = await get_redis_client()
                await touch_workspace_ttl(channel, chat_id, redis)
            except Exception:
                pass  # TTL touch is non-critical

        return handled

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


# ============================================================================
# Sprint 223: RUN_EVALS + LIST_NOTES Handlers (dispatch-only, CTO R2)
# ============================================================================


async def _execute_run_evals(
    tool_args: dict,
    bot_token: str,
    chat_id: str | int,
    user_id: str,
    *,
    channel: str = "telegram",
) -> bool:
    """Execute RUN_EVALS command via OTT chat."""
    project_id = tool_args.get("project_id")

    async with AsyncSessionLocal() as db:
        try:
            from app.services.agent_team.eval_scorer import EvalScorer

            scorer = EvalScorer()
            # Run a lightweight status check (no full suite without test cases)
            reply = (
                "\U0001f9ea Eval Scorer Status\n\n"
                f"\u2705 Service: Online\n"
                f"\U0001f4ca Evaluator model: {scorer.evaluator_model}\n"
            )
            if project_id:
                reply += f"\U0001f4cc Project: {project_id}\n"
            reply += (
                "\n\U0001f4a1 To run a full evaluation suite, use the API:\n"
                "POST /api/v1/agent-team/evals/run\n\n"
                "Or use the CLI: sdlcctl eval run <project_id>"
            )
            await _send_telegram_reply(bot_token, chat_id, reply, channel=channel)
            return True
        except Exception as exc:
            logger.warning("run_evals handler error: %s", exc)
            await _send_telegram_reply(
                bot_token, chat_id,
                _format_error(f"Eval scorer unavailable: {str(exc)[:200]}"),
                channel=channel,
            )
            return False


async def _execute_list_notes(
    tool_args: dict,
    bot_token: str,
    chat_id: str | int,
    user_id: str,
    *,
    channel: str = "telegram",
) -> bool:
    """Execute LIST_NOTES command via OTT chat."""
    agent_name = tool_args.get("agent_name", "")

    async with AsyncSessionLocal() as db:
        try:
            from app.services.agent_team.note_service import NoteService
            from app.services.agent_team.agent_registry import AgentRegistryService
            from uuid import UUID as _UUID

            # Find agent by name
            registry = AgentRegistryService(db)
            agents = await registry.list_definitions()
            target = None
            for agent in agents:
                if agent.name.lower() == agent_name.lower():
                    target = agent
                    break

            if not target:
                await _send_telegram_reply(
                    bot_token, chat_id,
                    _format_error(
                        f"Agent '{agent_name}' not found.\n"
                        f"Available agents: {', '.join(a.name for a in agents[:10])}"
                    ),
                    channel=channel,
                )
                return True

            note_svc = NoteService(db)
            notes = await note_svc.list_notes(target.id, limit=5)

            if not notes:
                reply = f"\U0001f4dd Notes for @{target.name}: (empty)"
            else:
                lines = [f"\U0001f4dd Notes for @{target.name}:\n"]
                for note in notes:
                    snippet = (note.content or "")[:80]
                    lines.append(
                        f"\u2022 [{note.note_type}] {snippet}"
                    )
                reply = "\n".join(lines)

            await _send_telegram_reply(bot_token, chat_id, reply, channel=channel)
            return True
        except Exception as exc:
            logger.warning("list_notes handler error: %s", exc)
            await _send_telegram_reply(
                bot_token, chat_id,
                _format_error(f"Note service unavailable: {str(exc)[:200]}"),
                channel=channel,
            )
            return False
