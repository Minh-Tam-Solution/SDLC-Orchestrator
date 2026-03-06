"""
Context Injector — Sprint 216-220 (P1 Context Injection → P5 Memory Enhancement).

Dynamically generates virtual markdown sections before every LLM call.
Port of MTClaw resolver.go: buildDelegateAgentsMD + buildTeamMD + buildAvailabilityMD.

7 Builders:
- build_delegation_md(agent_id) → DELEGATION section (<=2000 tokens)
- build_team_md(agent_id, team_id) → TEAM section (<=1500 tokens)
- build_availability_md(agent_id) → AVAILABILITY section (<=200 tokens)
- build_skills_md(agent_id, project_id) → SKILLS section (<=1500 tokens) [Sprint 217]
- build_workspace_md(conversation_id) → WORKSPACE section (<=500 tokens) [Sprint 220]
- build_feedback_md(conversation_id) → HUMAN_FEEDBACK section [Sprint 220]
- build_consensus_md(conversation_id) → ACTIVE_VOTES section [Sprint 221, via ConsensusService]

Entrypoint:
- inject_context(agent_id, team_id, system_prompt, project_id, conversation_id)

CTO F1 (Sprint 220): conversation_id param added ONCE — shared by workspace,
feedback, and future consensus builders.

References:
- ADR-069 D-069-01, FR-051 sections 2.2-2.3
- ADR-072, Sprint 219 Track B (workspace), Sprint 220 (memory enhancement)
- CoPaw ReMe shared memory pattern
"""

from __future__ import annotations

import logging
from html import escape as xml_escape
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_definition import AgentDefinition
from app.models.delegation_link import DelegationLink
from app.models.team import Team
from app.models.team_member import TeamMember
from app.services.agent_team.delegation_service import DelegationService
from app.services.agent_team.skill_summary import SkillSummaryBuilder

logger = logging.getLogger(__name__)

# Token budget constants (FR-051 NFR)
MAX_DELEGATION_TARGETS_FULL = 15
MAX_DELEGATION_TOKENS = 2000
MAX_TEAM_TOKENS = 1500
MAX_AVAILABILITY_TOKENS = 200
MAX_SKILLS_TOKENS = 1500  # Sprint 217
MAX_WORKSPACE_TOKENS = 500  # Sprint 220
MAX_WORKSPACE_CHARS = 1500  # ~500 tokens


class ContextInjector:
    """
    Builds dynamic context sections for agent system prompts.

    Each builder returns a markdown string wrapped in XML tags.
    The inject_context() entrypoint calls all builders and appends
    the combined result to the base system prompt.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._delegation_service = DelegationService(db)
        self._skill_summary = SkillSummaryBuilder(db)

    async def build_delegation_md(self, agent_id: UUID) -> str:
        """
        Build DELEGATION.md section listing available delegation targets.

        If <=15 targets: full list with agent name, role, and description.
        If >15 targets: first 15 + search instruction for overflow.
        If 0 targets: returns empty string (AVAILABILITY.md handles this).

        Token budget: <= 2000 tokens.

        Args:
            agent_id: Source agent definition ID.

        Returns:
            Markdown string wrapped in <delegation> tags, or empty string.
        """
        links = await self._delegation_service.get_targets(agent_id)

        if not links:
            return ""

        lines = [
            "## Available Delegation Targets\n",
            "You can delegate work to these agents using @mention:\n",
        ]

        # Show up to MAX_DELEGATION_TARGETS_FULL targets
        display_links = links[:MAX_DELEGATION_TARGETS_FULL]
        for link in display_links:
            target = link.target_agent
            if target is not None:
                name = xml_escape(target.agent_name)
                role = xml_escape(target.sdlc_role)
                desc = ""
                if target.system_prompt:
                    # Use first 80 chars of system_prompt as capability summary
                    desc_raw = target.system_prompt[:80].replace("\n", " ").strip()
                    desc = f" — {xml_escape(desc_raw)}"
                lines.append(f"- **@{name}** (role: {role}){desc}")

        # Overflow notice
        remaining = len(links) - MAX_DELEGATION_TARGETS_FULL
        if remaining > 0:
            lines.append(
                f"\n> You have {remaining} more targets not shown. "
                "Use `@search <query>` to find specific agents."
            )

        content = "\n".join(lines)
        return f"<delegation>\n{content}\n</delegation>"

    async def build_team_md(
        self,
        agent_id: UUID,
        team_id: UUID | None,
    ) -> str:
        """
        Build TEAM.md section with team context.

        Two variants:
        - Lead variant: full team roster, delegation overview, coordination role.
        - Member variant: lead reference, own role, escalation instructions.

        If agent is not in a team (team_id is None): returns empty string.

        Token budget: <= 1500 tokens.

        Args:
            agent_id: Agent definition ID.
            team_id: Team ID (None if agent has no team).

        Returns:
            Markdown string wrapped in <team> tags, or empty string.
        """
        if team_id is None:
            return ""

        # Fetch team
        team_result = await self.db.execute(
            select(Team).where(Team.id == team_id)
        )
        team = team_result.scalar_one_or_none()
        if team is None:
            return ""

        # Fetch current agent definition
        agent_result = await self.db.execute(
            select(AgentDefinition).where(AgentDefinition.id == agent_id)
        )
        agent = agent_result.scalar_one_or_none()
        if agent is None:
            return ""

        # Fetch team members (agent definitions in this team)
        members_result = await self.db.execute(
            select(AgentDefinition).where(
                and_(
                    AgentDefinition.team_id == team_id,
                    AgentDefinition.is_active.is_(True),
                )
            )
        )
        team_agents = list(members_result.scalars().all())

        team_name = xml_escape(team.name)
        is_lead = (
            team.lead_agent_definition_id is not None
            and team.lead_agent_definition_id == agent_id
        )

        if is_lead:
            return self._build_team_lead_md(team_name, agent, team_agents)
        return await self._build_team_member_md(team_name, agent, team)

    def _build_team_lead_md(
        self,
        team_name: str,
        agent: AgentDefinition,
        team_agents: list[AgentDefinition],
    ) -> str:
        """Build TEAM.md lead variant."""
        lines = [
            "## Team Context (Lead)\n",
            f"You are the **lead** of team '{team_name}'.",
            "You coordinate work across team members and can delegate tasks.\n",
            "### Team Members",
        ]

        for member in team_agents:
            if member.id == agent.id:
                continue  # Skip self
            name = xml_escape(member.agent_name)
            role = xml_escape(member.sdlc_role)
            lines.append(f"- **@{name}** (role: {role})")

        content = "\n".join(lines)
        return f"<team>\n{content}\n</team>"

    async def _build_team_member_md(
        self,
        team_name: str,
        agent: AgentDefinition,
        team: Team,
    ) -> str:
        """Build TEAM.md member variant."""
        lines = [
            "## Team Context (Member)\n",
            f"You are a member of team '{team_name}'.",
        ]

        # Reference lead if set — async fetch from DB
        if team.lead_agent_definition_id is not None:
            lead_result = await self.db.execute(
                select(AgentDefinition).where(
                    AgentDefinition.id == team.lead_agent_definition_id
                )
            )
            lead_agent = lead_result.scalar_one_or_none()
            if lead_agent:
                lines.append(
                    f"Your team lead is **@{xml_escape(lead_agent.agent_name)}**. "
                    "Escalate blockers to them.\n"
                )

        lines.append("### Your Role")
        lines.append(
            "Focus on your assigned tasks. "
            "Report completion to your team lead."
        )

        content = "\n".join(lines)
        return f"<team>\n{content}\n</team>"

    async def build_availability_md(self, agent_id: UUID) -> str:
        """
        Build AVAILABILITY.md section with negative context.

        Only emitted when agent has 0 delegation targets.
        Prevents hallucinated @mentions and spawn tool calls.

        Token budget: <= 200 tokens.

        Args:
            agent_id: Agent definition ID.

        Returns:
            Markdown string wrapped in <availability> tags, or empty string.
        """
        target_count = await self._delegation_service.get_target_count(agent_id)

        if target_count > 0:
            # Agent has targets — no negative context needed
            return ""

        content = (
            "## Availability Notice\n\n"
            "You have **no delegation targets** configured.\n"
            "Do NOT attempt to use @mention or spawn tools — they will fail.\n"
            "Complete your task independently using your own tools."
        )
        return f"<availability>\n{content}\n</availability>"

    async def build_skills_md(
        self,
        agent_id: UUID,
        project_id: UUID | None = None,
    ) -> str:
        """
        Build SKILLS section listing accessible skills for this agent.

        Delegates to SkillSummaryBuilder for the actual rendering.
        Token budget: <= 1500 tokens.

        Args:
            agent_id: Agent definition ID.
            project_id: Project ID for workspace-scoped skills.

        Returns:
            XML string wrapped in <available_skills> tags, or empty string.
        """
        return await self._skill_summary.build_summary(agent_id, project_id)

    async def build_workspace_md(self, conversation_id: UUID | None) -> str:
        """
        Build WORKSPACE section listing active shared workspace items.

        Shows key names, types, and 50-char content preview.
        Token budget: <= 500 tokens (~1,500 chars).
        Returns empty string if no active items or conversation_id is None.

        Args:
            conversation_id: Conversation ID to scope workspace.

        Returns:
            Markdown string wrapped in <workspace> tags, or empty string.
        """
        if conversation_id is None:
            return ""

        from app.services.agent_team.shared_workspace import SharedWorkspace
        ws = SharedWorkspace(self.db, conversation_id)
        items = await ws.list_keys()

        if not items:
            return ""

        lines = [
            "## Shared Workspace\n",
            "Active workspace items shared across agents in this conversation:\n",
        ]

        total_chars = 0
        for item in items:
            key = xml_escape(item["item_key"])
            itype = xml_escape(item["item_type"])
            version = item["version"]
            preview = xml_escape(item["preview"]) if item.get("preview") else ""
            line = f"- **{key}** (type: {itype}, v{version})"
            if preview:
                line += f" — {preview}"
            lines.append(line)
            total_chars += len(line)
            if total_chars > MAX_WORKSPACE_CHARS:
                remaining = len(items) - len(lines) + 2  # +2 for header lines
                if remaining > 0:
                    lines.append(f"\n> {remaining} more items not shown.")
                break

        content = "\n".join(lines)
        return f"<workspace>\n{content}\n</workspace>"

    async def build_feedback_md(self, conversation_id: UUID | None) -> str:
        """
        Build HUMAN_FEEDBACK section from most recent approval feedback.

        Injects latest human feedback into agent context so the agent
        can act on approval/rejection feedback in its next turn.
        Returns empty string if no feedback or conversation_id is None.

        Args:
            conversation_id: Conversation ID to check for feedback.

        Returns:
            Markdown string wrapped in <human_feedback> tags, or empty string.
        """
        if conversation_id is None:
            return ""

        from app.models.agent_message import AgentMessage
        from sqlalchemy import desc

        # Find latest message with approval_feedback in metadata
        result = await self.db.execute(
            select(AgentMessage)
            .where(AgentMessage.conversation_id == conversation_id)
            .where(AgentMessage.message_type == "system")
            .where(AgentMessage.processing_status == "completed")
            .order_by(desc(AgentMessage.created_at))
            .limit(5)
        )
        recent_msgs = list(result.scalars().all())

        for msg in recent_msgs:
            meta = msg.metadata_ if isinstance(msg.metadata_, dict) else {}
            feedback = meta.get("approval_feedback")
            if feedback:
                action = xml_escape(str(feedback.get("action", "unknown")))
                text = xml_escape(str(feedback.get("feedback_text", "")))
                lines = [
                    "## Human Feedback\n",
                    f"**Decision**: {action}",
                ]
                if text:
                    lines.append(f"**Feedback**: {text}")
                if action == "rejected":
                    lines.append(
                        "\nPlease revise your approach based on this feedback and try again."
                    )
                content = "\n".join(lines)
                return f"<human_feedback>\n{content}\n</human_feedback>"

        return ""

    async def inject_context(
        self,
        agent_id: UUID,
        team_id: UUID | None,
        system_prompt: str,
        project_id: UUID | None = None,
        conversation_id: UUID | None = None,
    ) -> str:
        """
        Entrypoint: build all context sections and append to system prompt.

        Order: delegation → team → availability → skills → workspace → feedback → consensus
        All content wrapped in <system_context> outer tag.

        CTO F1 (Sprint 220): conversation_id added ONCE — all conversation-scoped
        builders (workspace, feedback, future consensus) share it.

        Args:
            agent_id: Agent definition ID.
            team_id: Team ID (None if no team).
            system_prompt: Base system prompt to append to.
            project_id: Project ID for workspace-scoped skills (Sprint 217).
            conversation_id: Conversation ID for workspace/feedback (Sprint 220).

        Returns:
            System prompt with context sections appended.
        """
        sections: list[str] = []

        delegation_md = await self.build_delegation_md(agent_id)
        if delegation_md:
            sections.append(delegation_md)

        team_md = await self.build_team_md(agent_id, team_id)
        if team_md:
            sections.append(team_md)

        availability_md = await self.build_availability_md(agent_id)
        if availability_md:
            sections.append(availability_md)

        skills_md = await self.build_skills_md(agent_id, project_id)
        if skills_md:
            sections.append(skills_md)

        # Sprint 220 — conversation-scoped builders
        workspace_md = await self.build_workspace_md(conversation_id)
        if workspace_md:
            sections.append(workspace_md)

        feedback_md = await self.build_feedback_md(conversation_id)
        if feedback_md:
            sections.append(feedback_md)

        # Sprint 221 — consensus builder (lives in consensus_service to avoid circular import)
        try:
            from app.services.agent_team.consensus_service import ConsensusService
            consensus_svc = ConsensusService(self.db)
            consensus_md = await consensus_svc.build_consensus_md(conversation_id)
            if consensus_md:
                sections.append(consensus_md)
        except ImportError:
            pass  # Consensus module not installed — skip
        except Exception as e:
            logger.warning("TRACE_CONSENSUS: build_consensus_md failed: %s", e)

        if not sections:
            return system_prompt

        context_block = "\n".join(sections)
        injected = f"\n\n<system_context>\n{context_block}\n</system_context>"

        logger.debug(
            "Injected context for agent %s (team %s): %d sections, %d chars",
            agent_id, team_id, len(sections), len(injected),
        )

        return system_prompt + injected
