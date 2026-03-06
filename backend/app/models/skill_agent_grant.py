"""SkillAgentGrant model — per-agent skill access control.

Sprint 218: ADR-070 CoPaw Pattern Adoption (P3 Skills Engine completion).
Junction table: skill_definition_id x agent_definition_id.
Open tiers (global, builtin) don't require grants — they're accessible to all agents.
Workspace/project/personal tiers require an explicit grant row for the agent to see the skill.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class SkillAgentGrant(Base):
    __tablename__ = "skill_agent_grants"

    __table_args__ = (
        UniqueConstraint(
            "skill_definition_id",
            "agent_definition_id",
            name="uq_skill_agent_grant",
        ),
    )

    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    skill_definition_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skill_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=False,
    )

    agent_definition_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    granted_by: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    # Relationships
    skill_definition = relationship("SkillDefinition", lazy="selectin")
    agent_definition = relationship("AgentDefinition", lazy="selectin")

    def to_dict(self) -> dict:
        """JSON-serializable representation including skill slug and agent name."""
        result = {
            "id": str(self.id),
            "skill_definition_id": str(self.skill_definition_id),
            "agent_definition_id": str(self.agent_definition_id),
            "granted_by": str(self.granted_by) if self.granted_by else None,
            "granted_at": self.granted_at.isoformat() if self.granted_at else None,
        }
        if self.skill_definition:
            result["skill_slug"] = self.skill_definition.slug
            result["skill_name"] = self.skill_definition.name
        if self.agent_definition:
            result["agent_name"] = self.agent_definition.agent_name
        return result
