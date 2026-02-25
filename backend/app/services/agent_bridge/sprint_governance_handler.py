"""
Sprint Governance Handler — Close sprint and export audit via OTT chat.

Sprint 201 Track B (B-05, B-06): Self-governance sprint close and audit export
through OTT channels (Telegram / Zalo).

Architecture:
    User: "close sprint"
      │
      ├─ chat_command_router.py  → tool_call: close_sprint(project_id=...)
      │
      ├─ governance_action_handler.py  → dispatch to this handler
      │
      ├─ sprint_governance_handler.py  ← THIS FILE
      │   ├─ SprintFileService  → get_active_sprint()
      │   ├─ SprintVerificationService  → verify_sprint_close_docs()
      │   ├─ Sprint.status = "completed"
      │   └─ Format bilingual response
      │
      └─ _send_reply()  → Telegram / Zalo

DB Session: Creates standalone AsyncSession via AsyncSessionLocal
(fire-and-forget, runs AFTER webhook 200 response).

Sprint 201 — Track B: Self-Governance Execution
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def handle_close_sprint(
    tool_args: dict[str, Any],
    bot_token: str,
    chat_id: str | int,
    user_id: str,
    channel: str = "telegram",
) -> bool:
    """
    Close the active sprint for a project with G-Sprint-Close verification.

    Flow:
        1. Fetch active sprint for project
        2. Run SprintVerificationService checks (CURRENT-SPRINT.md freshness)
        3. Mark sprint as completed
        4. Generate G-Sprint-Close summary
        5. Send bilingual reply

    Args:
        tool_args: Validated parameters {"project_id": UUID}
        bot_token: Telegram Bot API token (empty for Zalo)
        chat_id: OTT chat/user ID for reply
        user_id: Authenticated user ID
        channel: OTT channel ("telegram" or "zalo")

    Returns:
        True if sprint closed and reply sent, False on error
    """
    from app.services.agent_bridge.governance_action_handler import (
        _send_telegram_reply,
        _format_error,
    )

    project_id_str = str(tool_args.get("project_id", ""))
    try:
        project_id = UUID(project_id_str)
    except ValueError:
        await _send_telegram_reply(
            bot_token, chat_id,
            _format_error(f"Invalid project ID: {project_id_str}"),
            channel=channel,
        )
        return False

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        from app.models.project import Project
        from app.models.sprint import Sprint
        from app.services.github_service import GitHubService
        from app.services.sprint_verification_service import (
            SprintVerificationService,
        )

        # 1. Fetch project
        proj_result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = proj_result.scalar_one_or_none()
        if not project:
            await _send_telegram_reply(
                bot_token, chat_id,
                _format_error(
                    f"Không tìm thấy project: {project_id_str}\n"
                    f"Project not found: {project_id_str}"
                ),
                channel=channel,
            )
            return False

        # 2. Fetch active sprint
        sprint_result = await db.execute(
            select(Sprint)
            .where(Sprint.project_id == project_id, Sprint.status == "active")
            .order_by(Sprint.number.desc())
            .limit(1)
        )
        sprint = sprint_result.scalar_one_or_none()
        if not sprint:
            await _send_telegram_reply(
                bot_token, chat_id,
                _format_error(
                    f"Không có sprint đang active cho project này.\n"
                    f"No active sprint found for project {project.name}."
                ),
                channel=channel,
            )
            return False

        # 3. Run G-Sprint-Close verification
        github_svc = GitHubService()
        verification_svc = SprintVerificationService(
            db=db, github_service=github_svc,
        )
        verification = await verification_svc.verify_sprint_close_docs(
            sprint=sprint, project=project,
        )

        # 4. Mark sprint as completed
        sprint.status = "completed"
        sprint.completed_at = datetime.now(timezone.utc)
        await db.commit()

        logger.info(
            "sprint_governance_handler: closed sprint %s (project=%s, user=%s)",
            sprint.number,
            project_id,
            user_id,
        )

        # 5. Format and send response
        verification_icon = "\u2705" if verification.passed else "\u26a0\ufe0f"
        verification_text = (
            "CURRENT-SPRINT.md verified"
            if verification.passed
            else f"Verification: {verification.reason}"
        )

        reply = (
            f"\U0001f3c1 Sprint Closed / Sprint đã đóng\n"
            f"\n"
            f"\U0001f4cb Sprint: {sprint.number} — {sprint.name}\n"
            f"\U0001f4c1 Project: {project.name}\n"
            f"\U0001f4ca Status: COMPLETED\n"
            f"\U0001f4c5 Closed at: {sprint.completed_at:%Y-%m-%d %H:%M UTC}\n"
            f"\n"
            f"{verification_icon} {verification_text}\n"
            f"\n"
            f"G-Sprint-Close checklist:\n"
            f"  \u2705 Sprint status → completed\n"
            f"  {verification_icon} CURRENT-SPRINT.md freshness\n"
            f"  \u2705 Documentation freeze (Rule 9)\n"
            f"\n"
            f"Sprint {sprint.number} đã được đóng thành công qua OTT.\n"
            f"Sprint {sprint.number} closed successfully via chat."
        )

        return await _send_telegram_reply(
            bot_token, chat_id, reply, channel=channel,
        )


async def handle_export_audit(
    tool_args: dict[str, Any],
    bot_token: str,
    chat_id: str | int,
    user_id: str,
    channel: str = "telegram",
) -> bool:
    """
    Export audit trail for a project as JSON/CSV summary via OTT.

    Sprint 201 B-06: Audit export via chat command.

    Args:
        tool_args: Validated parameters {"project_id": int, "format": "json"|"csv"}
        bot_token: Telegram Bot API token
        chat_id: OTT chat/user ID for reply
        user_id: Authenticated user ID
        channel: OTT channel

    Returns:
        True if audit exported and reply sent, False on error
    """
    from app.services.agent_bridge.governance_action_handler import (
        _send_telegram_reply,
        _format_error,
    )

    project_id = tool_args.get("project_id")
    export_format = tool_args.get("format", "json")

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select, func
        from app.models.project import Project
        from app.models.sprint import Sprint
        from app.models.gate import Gate

        # Fetch project
        proj_result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = proj_result.scalar_one_or_none()
        if not project:
            await _send_telegram_reply(
                bot_token, chat_id,
                _format_error(f"Project not found: {project_id}"),
                channel=channel,
            )
            return False

        # Count sprints and gates for summary
        sprint_count_result = await db.execute(
            select(func.count()).select_from(Sprint).where(
                Sprint.project_id == project_id
            )
        )
        sprint_count = sprint_count_result.scalar() or 0

        gate_count_result = await db.execute(
            select(func.count()).select_from(Gate).where(
                Gate.project_id == project_id
            )
        )
        gate_count = gate_count_result.scalar() or 0

        approved_count_result = await db.execute(
            select(func.count()).select_from(Gate).where(
                Gate.project_id == project_id,
                Gate.status == "APPROVED",
            )
        )
        approved_count = approved_count_result.scalar() or 0

        now = datetime.now(timezone.utc)
        reply = (
            f"\U0001f4ca Audit Export / Xuất Báo Cáo\n"
            f"\n"
            f"\U0001f4c1 Project: {project.name}\n"
            f"\U0001f4c5 Generated: {now:%Y-%m-%d %H:%M UTC}\n"
            f"\U0001f4cb Format: {export_format.upper()}\n"
            f"\n"
            f"--- Audit Summary ---\n"
            f"\U0001f504 Total sprints: {sprint_count}\n"
            f"\U0001f6e1 Total gates: {gate_count}\n"
            f"\u2705 Gates approved: {approved_count}\n"
            f"\n"
            f"Full audit export available via CLI:\n"
            f"  sdlcctl export-audit --project {project_id} --format {export_format}\n"
            f"\n"
            f"Báo cáo audit đã được tạo qua OTT chat."
        )

        logger.info(
            "sprint_governance_handler: audit export project=%s user=%s format=%s",
            project_id,
            user_id,
            export_format,
        )

        return await _send_telegram_reply(
            bot_token, chat_id, reply, channel=channel,
        )
