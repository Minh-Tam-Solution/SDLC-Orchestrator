"""Sprint 156: Compliance Framework Tables (5 tables)

Creates shared compliance framework tables supporting NIST AI RMF,
EU AI Act, and ISO 42001. Seeds NIST AI RMF framework with 5 GOVERN
controls.

Sprint: 156 - Phase 3 COMPLIANCE (NIST AI RMF GOVERN)
Priority: P0
Reference: ADR-051

Tables:
- compliance_frameworks: Framework registry
- compliance_controls: Per-framework controls
- compliance_assessments: Per-project evaluations
- compliance_risk_register: Risk entries
- compliance_raci: RACI accountability matrix

Revision ID: s156_001
Revises: s151_001
Create Date: 2026-04-07
"""

from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "s156_001"
down_revision: Union[str, None] = "s151_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create 5 compliance framework tables and seed NIST GOVERN data."""

    # =========================================================================
    # Table 1: compliance_frameworks
    # =========================================================================

    op.create_table(
        "compliance_frameworks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("total_controls", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_index("ix_compliance_frameworks_code", "compliance_frameworks", ["code"])

    # =========================================================================
    # Table 2: compliance_controls
    # =========================================================================

    op.create_table(
        "compliance_controls",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "framework_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("compliance_frameworks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("control_code", sa.String(50), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("severity", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("gate_mapping", sa.String(20), nullable=True),
        sa.Column(
            "evidence_required",
            postgresql.JSONB,
            nullable=False,
            server_default="[]",
        ),
        sa.Column("opa_policy_code", sa.String(100), nullable=True),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("framework_id", "control_code", name="uq_control_framework_code"),
        comment="Compliance controls per framework",
    )

    op.create_index("ix_compliance_controls_framework", "compliance_controls", ["framework_id"])

    # =========================================================================
    # Table 3: compliance_assessments
    # =========================================================================

    op.create_table(
        "compliance_assessments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "control_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("compliance_controls.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(30),
            nullable=False,
            server_default="not_started",
        ),
        sa.Column(
            "evidence_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=True,
        ),
        sa.Column(
            "assessor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("auto_evaluated", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("opa_result", postgresql.JSONB, nullable=True),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("project_id", "control_id", name="uq_assessment_project_control"),
        comment="Per-project compliance control assessments",
    )

    op.create_index("ix_assessments_project", "compliance_assessments", ["project_id"])
    op.create_index("ix_assessments_status", "compliance_assessments", ["status"])

    # =========================================================================
    # Table 4: compliance_risk_register
    # =========================================================================

    op.create_table(
        "compliance_risk_register",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "framework_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("compliance_frameworks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("risk_code", sa.String(50), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("likelihood", sa.String(20), nullable=False, server_default="possible"),
        sa.Column("impact", sa.String(20), nullable=False, server_default="moderate"),
        sa.Column("risk_score", sa.Integer, nullable=False, server_default="9"),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("mitigation_strategy", sa.Text, nullable=True),
        sa.Column(
            "responsible_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="identified"),
        sa.Column("target_date", sa.Date, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_index("ix_risk_project", "compliance_risk_register", ["project_id"])
    op.create_index("ix_risk_score", "compliance_risk_register", ["risk_score"])
    op.create_index("ix_risk_status", "compliance_risk_register", ["status"])

    # =========================================================================
    # Table 5: compliance_raci
    # =========================================================================

    op.create_table(
        "compliance_raci",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "control_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("compliance_controls.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "responsible_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "accountable_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "consulted_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=True,
        ),
        sa.Column(
            "informed_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("project_id", "control_id", name="uq_raci_project_control"),
        comment="RACI accountability matrix per project per control",
    )

    op.create_index("ix_raci_project", "compliance_raci", ["project_id"])

    # =========================================================================
    # Seed Data: NIST AI RMF Framework + 5 GOVERN Controls
    # =========================================================================

    nist_framework_id = str(uuid4())

    op.execute(
        f"""
        INSERT INTO compliance_frameworks (id, code, name, version, description, total_controls, is_active)
        VALUES (
            '{nist_framework_id}',
            'NIST_AI_RMF',
            'NIST AI Risk Management Framework',
            '1.0',
            'The NIST AI RMF provides organizations with a framework for managing risks '
            'associated with AI systems throughout their lifecycle. It includes four core functions: '
            'GOVERN, MAP, MEASURE, and MANAGE.',
            5,
            true
        )
        """
    )

    # EU AI Act framework (controls to be added in Sprint 158)
    eu_framework_id = str(uuid4())
    op.execute(
        f"""
        INSERT INTO compliance_frameworks (id, code, name, version, description, total_controls, is_active)
        VALUES (
            '{eu_framework_id}',
            'EU_AI_ACT',
            'EU Artificial Intelligence Act',
            '2024/1689',
            'The EU AI Act establishes a comprehensive legal framework for AI systems in the European Union. '
            'It classifies AI systems into risk categories: Unacceptable, High-Risk, Limited-Risk, and Minimal-Risk.',
            0,
            false
        )
        """
    )

    # ISO 42001 framework (controls to be added in Sprint 159)
    iso_framework_id = str(uuid4())
    op.execute(
        f"""
        INSERT INTO compliance_frameworks (id, code, name, version, description, total_controls, is_active)
        VALUES (
            '{iso_framework_id}',
            'ISO_42001',
            'ISO/IEC 42001:2023 AI Management Systems',
            '2023',
            'ISO/IEC 42001 specifies requirements for establishing, implementing, maintaining, and '
            'continually improving an AI management system (AIMS) within organizations.',
            0,
            false
        )
        """
    )

    # Seed 5 NIST GOVERN controls
    govern_controls = [
        {
            "code": "GOVERN-1.1",
            "category": "GOVERN",
            "title": "AI System Accountability Structure",
            "description": (
                "All AI systems must have designated owners with clear accountability. "
                "Each AI system in the project must be assigned to a specific team member "
                "who is responsible for its governance, monitoring, and risk management."
            ),
            "severity": "critical",
            "gate_mapping": "G1",
            "opa_policy": "compliance.nist.govern.accountability",
            "sort_order": 1,
            "evidence": (
                '[{"type": "document", "description": "AI system inventory with designated owners", '
                '"required": true, "accepted_formats": ["pdf", "md", "csv"]}, '
                '{"type": "attestation", "description": "Owner acknowledgment of AI governance responsibilities", '
                '"required": true, "accepted_formats": ["pdf", "signed_form"]}]'
            ),
        },
        {
            "code": "GOVERN-1.2",
            "category": "GOVERN",
            "title": "AI Risk Awareness Culture",
            "description": (
                "Team members must complete AI risk awareness training. "
                "At least 80%% of team members should have completed training on AI risks, "
                "responsible AI practices, and the organization''s AI governance policies."
            ),
            "severity": "high",
            "gate_mapping": "G1",
            "opa_policy": "compliance.nist.govern.risk_culture",
            "sort_order": 2,
            "evidence": (
                '[{"type": "report", "description": "Training completion report showing >=80%% completion", '
                '"required": true, "accepted_formats": ["pdf", "csv"]}, '
                '{"type": "document", "description": "AI risk training curriculum", '
                '"required": false, "accepted_formats": ["pdf", "md"]}]'
            ),
        },
        {
            "code": "GOVERN-1.3",
            "category": "GOVERN",
            "title": "Legal and Regulatory Compliance",
            "description": (
                "AI usage must have legal review and approval. "
                "Before deploying AI systems, a legal review must confirm compliance "
                "with applicable laws, regulations, and organizational policies."
            ),
            "severity": "critical",
            "gate_mapping": "G1",
            "opa_policy": "compliance.nist.govern.legal_compliance",
            "sort_order": 3,
            "evidence": (
                '[{"type": "attestation", "description": "Legal review approval for AI usage", '
                '"required": true, "accepted_formats": ["pdf", "signed_form"]}, '
                '{"type": "document", "description": "Legal compliance assessment document", '
                '"required": true, "accepted_formats": ["pdf", "docx"]}]'
            ),
        },
        {
            "code": "GOVERN-1.4",
            "category": "GOVERN",
            "title": "Third-Party AI Oversight",
            "description": (
                "Third-party AI APIs and services must have documented SLAs and privacy agreements. "
                "All external AI providers used in the project must have formal service level "
                "agreements and data privacy/processing agreements in place."
            ),
            "severity": "high",
            "gate_mapping": "G2",
            "opa_policy": "compliance.nist.govern.third_party_oversight",
            "sort_order": 4,
            "evidence": (
                '[{"type": "document", "description": "SLA documentation for each third-party AI provider", '
                '"required": true, "accepted_formats": ["pdf", "docx"]}, '
                '{"type": "document", "description": "Data processing agreement (DPA) for each provider", '
                '"required": true, "accepted_formats": ["pdf", "docx"]}]'
            ),
        },
        {
            "code": "GOVERN-1.5",
            "category": "GOVERN",
            "title": "Continuous Improvement from Incidents",
            "description": (
                "AI-related incidents must have postmortems completed within 48 hours "
                "with documented process improvements. Each incident should result in "
                "actionable changes to prevent recurrence."
            ),
            "severity": "medium",
            "gate_mapping": "G3",
            "opa_policy": "compliance.nist.govern.continuous_improvement",
            "sort_order": 5,
            "evidence": (
                '[{"type": "report", "description": "Incident postmortem report completed within 48h", '
                '"required": true, "accepted_formats": ["pdf", "md"]}, '
                '{"type": "document", "description": "Process improvement documentation", '
                '"required": false, "accepted_formats": ["pdf", "md"]}]'
            ),
        },
    ]

    for ctrl in govern_controls:
        ctrl_id = str(uuid4())
        op.execute(
            f"""
            INSERT INTO compliance_controls
                (id, framework_id, control_code, category, title, description,
                 severity, gate_mapping, evidence_required, opa_policy_code, sort_order)
            VALUES (
                '{ctrl_id}',
                '{nist_framework_id}',
                '{ctrl["code"]}',
                '{ctrl["category"]}',
                '{ctrl["title"]}',
                '{ctrl["description"]}',
                '{ctrl["severity"]}',
                '{ctrl["gate_mapping"]}',
                '{ctrl["evidence"]}'::jsonb,
                '{ctrl["opa_policy"]}',
                {ctrl["sort_order"]}
            )
            """
        )


def downgrade() -> None:
    """Drop all 5 compliance framework tables."""
    op.drop_table("compliance_raci")
    op.drop_table("compliance_risk_register")
    op.drop_table("compliance_assessments")
    op.drop_table("compliance_controls")
    op.drop_table("compliance_frameworks")
