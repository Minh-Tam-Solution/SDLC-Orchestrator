"""Sprint 176: Multi-Agent Team Engine Foundation (ADR-056/EP-07)

Revision ID: s176_001
Revises: s173_001
Create Date: 2026-02-18 10:00:00.000000

CONTEXT:
- Sprint 176 "Multi-Agent Foundation" — ADR-056 Phase 1
- 3 P0 tables: agent_definitions, agent_conversations, agent_messages
- OpenClaw patterns: lane-based queue, failover classification, session inheritance
- TinyClaw patterns: @mention routing, 50-msg loop prevention, branch counting
- Nanobot patterns: delegation depth, tool permissions, workspace restriction

TABLES CREATED:
1. agent_definitions (22 columns) — agent configuration templates
2. agent_conversations (19 columns) — conversation sessions with snapshotted config
3. agent_messages (22 columns) — messages with lane-based processing + dead-letter

4 LOCKED DECISIONS (ADR-056):
  1. Snapshot Precedence — definition → conversation snapshot on creation
  2. Lane Contract — SKIP LOCKED + processing_lane + dead-letter
  3. Provider Profile Key — {provider}:{account}:{region}:{model_family}
  4. Canonical Protocol Owner — Orchestrator owns all schemas

14 NON-NEGOTIABLES ENFORCED:
  Security: least-privilege (#1), tool restriction (#6), shell guard (#5)
  Architecture: lane queue (#7), loop guards (#9), dead-letter (#10), snapshot (#11)
  Observability: correlation_id (#12), budget breaker (#13), interrupt (#14)

RELATED:
- ADR-056-Multi-Agent-Team-Engine.md
- EP-07-Multi-Agent-Team-Engine.md
- Data-Model-ERD.md v3.4.0
- API-Specification.md v3.6.0
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = "s176_001"
down_revision = "s173_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ================================================================
    # Table 1: agent_definitions — agent configuration templates
    # ================================================================
    op.create_table(
        "agent_definitions",
        # Primary Key
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        # Foreign Keys
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("team_id", UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="SET NULL"), nullable=True),
        # Identity
        sa.Column("agent_name", sa.String(50), nullable=False),
        sa.Column("sdlc_role", sa.String(20), nullable=False),
        # Provider Configuration
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("system_prompt", sa.Text, nullable=True),
        sa.Column("working_directory", sa.String(500), nullable=True),
        sa.Column("max_tokens", sa.Integer, nullable=False, server_default="4096"),
        sa.Column("temperature", sa.Float, nullable=False, server_default="0.7"),
        # Queue Configuration (CTO: P0 = 3 of 7 modes, 2 scopes)
        sa.Column("queue_mode", sa.String(20), nullable=False, server_default="queue"),
        sa.Column("session_scope", sa.String(20), nullable=False, server_default="per-sender"),
        # Safety Controls (Nanobot N2)
        sa.Column("max_delegation_depth", sa.Integer, nullable=False, server_default="1"),
        sa.Column("allowed_tools", JSONB, nullable=False, server_default='["*"]'),
        sa.Column("denied_tools", JSONB, nullable=False, server_default="[]"),
        sa.Column("can_spawn_subagent", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("allowed_paths", JSONB, nullable=False, server_default="[]"),
        # Reflect Step (Nanobot)
        sa.Column("reflect_frequency", sa.Integer, nullable=False, server_default="1"),
        # Status
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        # Extensible Config
        sa.Column("config", JSONB, nullable=False, server_default="{}"),
        # Timestamps
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    # Indexes for agent_definitions
    op.create_index("ix_agent_definitions_project_id", "agent_definitions", ["project_id"])
    op.create_index("ix_agent_definitions_team_id", "agent_definitions", ["team_id"])
    op.create_index("ix_agent_definitions_sdlc_role", "agent_definitions", ["sdlc_role"])
    op.create_index("ix_agent_definitions_is_active", "agent_definitions", ["is_active"])
    op.create_index(
        "ix_agent_definitions_project_name",
        "agent_definitions",
        ["project_id", "agent_name"],
        unique=True,
    )

    # Check constraints for agent_definitions
    op.create_check_constraint(
        "ck_agent_definitions_sdlc_role",
        "agent_definitions",
        "sdlc_role IN ('pm', 'architect', 'coder', 'reviewer', 'tester', 'devops')",
    )
    op.create_check_constraint(
        "ck_agent_definitions_queue_mode",
        "agent_definitions",
        "queue_mode IN ('queue', 'steer', 'interrupt', 'followup', 'collect', 'steer-backlog', 'steer+backlog')",
    )
    op.create_check_constraint(
        "ck_agent_definitions_session_scope",
        "agent_definitions",
        "session_scope IN ('per-sender', 'global')",
    )
    op.create_check_constraint(
        "ck_agent_definitions_max_delegation",
        "agent_definitions",
        "max_delegation_depth >= 0 AND max_delegation_depth <= 10",
    )

    # ================================================================
    # Table 2: agent_conversations — conversation sessions
    # ================================================================
    op.create_table(
        "agent_conversations",
        # Primary Key
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        # Foreign Keys
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_definition_id", UUID(as_uuid=True), sa.ForeignKey("agent_definitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_conversation_id", UUID(as_uuid=True), sa.ForeignKey("agent_conversations.id", ondelete="SET NULL"), nullable=True),
        # Delegation Depth (Nanobot N2)
        sa.Column("delegation_depth", sa.Integer, nullable=False, server_default="0"),
        # Initiator
        sa.Column("initiator_type", sa.String(20), nullable=False),
        sa.Column("initiator_id", sa.String(100), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        # Snapshotted Fields (ADR-056 Decision 1)
        sa.Column("session_scope", sa.String(20), nullable=False),
        sa.Column("queue_mode", sa.String(20), nullable=False),
        # Status
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        # Loop Prevention (TinyClaw)
        sa.Column("total_messages", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_messages", sa.Integer, nullable=False, server_default="50"),
        sa.Column("branch_count", sa.Integer, nullable=False, server_default="0"),
        # Token Budget (OpenClaw + Non-Negotiable #13)
        sa.Column("input_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("current_cost_cents", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_budget_cents", sa.Integer, nullable=False, server_default="1000"),
        # Metadata
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        # Timestamps
        sa.Column("started_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )

    # Indexes for agent_conversations
    op.create_index("ix_agent_conversations_project_id", "agent_conversations", ["project_id"])
    op.create_index("ix_agent_conversations_agent_def_id", "agent_conversations", ["agent_definition_id"])
    op.create_index("ix_agent_conversations_parent_id", "agent_conversations", ["parent_conversation_id"])
    op.create_index("ix_agent_conversations_status", "agent_conversations", ["status"])
    op.create_index("ix_agent_conversations_started_at", "agent_conversations", ["started_at"])
    op.create_index(
        "ix_agent_conversations_initiator",
        "agent_conversations",
        ["initiator_type", "initiator_id"],
    )

    # Check constraints for agent_conversations
    op.create_check_constraint(
        "ck_agent_conversations_status",
        "agent_conversations",
        "status IN ('active', 'completed', 'max_reached', 'paused_by_human', 'error')",
    )
    op.create_check_constraint(
        "ck_agent_conversations_initiator_type",
        "agent_conversations",
        "initiator_type IN ('user', 'agent', 'gate_event', 'ott_channel')",
    )
    op.create_check_constraint(
        "ck_agent_conversations_channel",
        "agent_conversations",
        "channel IN ('web', 'cli', 'extension', 'telegram', 'discord', 'whatsapp', 'zalo')",
    )
    op.create_check_constraint(
        "ck_agent_conversations_budget",
        "agent_conversations",
        "current_cost_cents >= 0 AND max_budget_cents > 0",
    )

    # ================================================================
    # Table 3: agent_messages — messages with lane-based processing
    # ================================================================
    op.create_table(
        "agent_messages",
        # Primary Key
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        # Foreign Keys
        sa.Column("conversation_id", UUID(as_uuid=True), sa.ForeignKey("agent_conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_message_id", UUID(as_uuid=True), sa.ForeignKey("agent_messages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("evidence_id", UUID(as_uuid=True), sa.ForeignKey("gate_evidence.id", ondelete="SET NULL"), nullable=True),
        # Sender / Recipient
        sa.Column("sender_type", sa.String(20), nullable=False),
        sa.Column("sender_id", sa.String(100), nullable=False),
        sa.Column("recipient_id", sa.String(100), nullable=True),
        # Content
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("mentions", JSONB, nullable=False, server_default="[]"),
        sa.Column("message_type", sa.String(20), nullable=False),
        # Queue / Lane (ADR-056 Decision 2)
        sa.Column("queue_mode", sa.String(20), nullable=False, server_default="queue"),
        sa.Column("processing_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("processing_lane", sa.String(50), nullable=False, server_default="main"),
        # Idempotency
        sa.Column("dedupe_key", sa.String(100), nullable=True, unique=True),
        # Tracing (Non-Negotiable #12)
        sa.Column("correlation_id", UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        # Provider Metrics
        sa.Column("token_count", sa.Integer, nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("provider_used", sa.String(20), nullable=True),
        sa.Column("failover_reason", sa.String(20), nullable=True),
        # Dead-Letter Queue (Non-Negotiable #10)
        sa.Column("failed_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("next_retry_at", sa.DateTime, nullable=True),
        # Timestamp
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    # Indexes for agent_messages
    op.create_index("ix_agent_messages_conversation_id", "agent_messages", ["conversation_id"])
    op.create_index("ix_agent_messages_parent_msg_id", "agent_messages", ["parent_message_id"])
    op.create_index("ix_agent_messages_processing_status", "agent_messages", ["processing_status"])
    op.create_index("ix_agent_messages_processing_lane", "agent_messages", ["processing_lane"])
    op.create_index("ix_agent_messages_correlation_id", "agent_messages", ["correlation_id"])
    op.create_index("ix_agent_messages_created_at", "agent_messages", ["created_at"])
    # Composite index for Lane Contract: SKIP LOCKED query pattern
    op.create_index(
        "ix_agent_messages_lane_pending",
        "agent_messages",
        ["processing_lane", "processing_status", "created_at"],
        postgresql_where=sa.text("processing_status = 'pending'"),
    )
    # Composite index for dead-letter inspection
    op.create_index(
        "ix_agent_messages_dead_letter",
        "agent_messages",
        ["processing_status", "failed_count"],
        postgresql_where=sa.text("processing_status = 'dead_letter'"),
    )

    # Check constraints for agent_messages
    op.create_check_constraint(
        "ck_agent_messages_sender_type",
        "agent_messages",
        "sender_type IN ('user', 'agent', 'system')",
    )
    op.create_check_constraint(
        "ck_agent_messages_message_type",
        "agent_messages",
        "message_type IN ('request', 'response', 'mention', 'system', 'interrupt')",
    )
    op.create_check_constraint(
        "ck_agent_messages_processing_status",
        "agent_messages",
        "processing_status IN ('pending', 'processing', 'completed', 'failed', 'dead_letter')",
    )
    op.create_check_constraint(
        "ck_agent_messages_failover_reason",
        "agent_messages",
        "failover_reason IS NULL OR failover_reason IN ('auth', 'format', 'rate_limit', 'billing', 'timeout', 'unknown')",
    )
    op.create_check_constraint(
        "ck_agent_messages_failed_count",
        "agent_messages",
        "failed_count >= 0",
    )

    # ================================================================
    # Trigger: auto-update updated_at on agent_definitions
    # ================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION update_agent_definitions_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trigger_agent_definitions_updated_at
            BEFORE UPDATE ON agent_definitions
            FOR EACH ROW
            EXECUTE FUNCTION update_agent_definitions_updated_at();
    """)


def downgrade() -> None:
    # Drop trigger first
    op.execute("DROP TRIGGER IF EXISTS trigger_agent_definitions_updated_at ON agent_definitions;")
    op.execute("DROP FUNCTION IF EXISTS update_agent_definitions_updated_at();")

    # Drop tables in reverse dependency order
    op.drop_table("agent_messages")
    op.drop_table("agent_conversations")
    op.drop_table("agent_definitions")
