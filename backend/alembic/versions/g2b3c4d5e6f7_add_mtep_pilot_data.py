"""Add MTEP Platform and pilot team accounts

Revision ID: g2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2025-12-03 22:00:00.000000

Sprint 24 Day 1: Beta Pilot Preparation
Authority: Backend Lead + CTO Approved

Changes:
- Add MTEP Platform project (5th pilot project)
- Add 3 new pilot team members
- Add MTEP gates
- Configure project memberships for pilot teams

Pilot Teams (5 total):
1. BFlow Platform (CEO: existing admin)
2. NQH-Bot (CTO: cto@bflow.vn)
3. SDLC Orchestrator (CPO: cpo@bflow.vn)
4. SDLC Enterprise Framework (PM: pm@bflow.vn)
5. MTEP Platform (EM: hoang.van.em@mtc.com.vn) - NEW
"""
from typing import Sequence, Union
from datetime import datetime
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g2b3c4d5e6f7'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add MTEP Platform and pilot data."""
    conn = op.get_bind()

    # Generate UUIDs
    mtep_project_id = str(uuid.uuid4())

    now = datetime.utcnow().isoformat()

    # Get existing owner (use EM from mtc.com.vn as project owner)
    owner = conn.execute(
        sa.text("SELECT id FROM users WHERE email = 'hoang.van.em@mtc.com.vn'")
    ).fetchone()

    if not owner:
        # Use admin as fallback owner
        owner = conn.execute(
            sa.text("SELECT id FROM users WHERE email = 'admin@sdlc-orchestrator.io'")
        ).fetchone()

    if not owner:
        print("No suitable owner found, skipping MTEP project creation")
        return

    owner_id = str(owner[0])

    # 1. Add MTEP Platform project
    conn.execute(
        sa.text("""
            INSERT INTO projects (
                id, name, slug, description, owner_id, is_active,
                created_at, updated_at
            )
            VALUES (
                :id, 'MTEP Platform', 'mtep-platform',
                'Multi-Tenant Enterprise Platform - SaaS solution for enterprise resource planning with AI-powered insights and real-time analytics.',
                :owner_id, true, :now, :now
            )
            ON CONFLICT (slug) DO NOTHING
        """),
        {"id": mtep_project_id, "owner_id": owner_id, "now": now}
    )

    # Check if project was created
    project = conn.execute(
        sa.text("SELECT id FROM projects WHERE slug = 'mtep-platform'")
    ).fetchone()

    if not project:
        print("MTEP project already exists or could not be created")
        return

    project_id = str(project[0])

    # 2. Add project members
    # Get users to add as members
    users_to_add = conn.execute(
        sa.text("""
            SELECT id, email FROM users
            WHERE email IN (
                'cto@bflow.vn', 'cpo@bflow.vn', 'pm@bflow.vn',
                'dev@bflow.vn', 'qa@bflow.vn',
                'admin@sdlc-orchestrator.io'
            )
        """)
    ).fetchall()

    for user in users_to_add:
        user_id = str(user[0])
        email = user[1]

        # Determine role based on email
        if 'admin' in email:
            role = 'admin'
        elif 'cto' in email or 'cpo' in email:
            role = 'maintainer'
        else:
            role = 'member'

        conn.execute(
            sa.text("""
                INSERT INTO project_members (
                    id, project_id, user_id, role, invited_at, joined_at, created_at
                )
                VALUES (
                    :id, :project_id, :user_id, :role, :now, :now, :now
                )
                ON CONFLICT DO NOTHING
            """),
            {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "user_id": user_id,
                "role": role,
                "now": now
            }
        )

    # 3. Add MTEP gates (Stage 0-2)
    gates_data = [
        # Stage 0: Problem Definition
        ("G0.1", "Problem Validation", "00", "approved"),
        ("G0.2", "Solution Diversity", "00", "approved"),
        # Stage 1: Planning
        ("G1.1", "Requirements Complete", "01", "approved"),
        ("G1.2", "Technical Feasibility", "01", "approved"),
        # Stage 2: Design
        ("G2.1", "Architecture Review", "02", "approved"),
        ("G2.2", "Security Baseline", "02", "pending"),
    ]

    for gate_code, gate_name, stage, status in gates_data:
        gate_id = str(uuid.uuid4())

        approved_at = now if status == "approved" else None

        conn.execute(
            sa.text("""
                INSERT INTO gates (
                    id, gate_name, gate_type, stage, project_id, status,
                    exit_criteria, description, created_at, updated_at,
                    approved_at
                )
                VALUES (
                    :id, :name, 'quality_gate', :stage, :project_id, :status,
                    :criteria, :description, :now, :now, :approved_at
                )
                ON CONFLICT DO NOTHING
            """),
            {
                "id": gate_id,
                "name": f"{gate_code}: {gate_name}",
                "stage": stage,
                "project_id": project_id,
                "status": status,
                "criteria": '{"min_score": 80}',
                "description": f"{gate_name} gate for MTEP Platform",
                "now": now,
                "approved_at": approved_at
            }
        )

    print(f"MTEP Platform created successfully with ID: {project_id}")


def downgrade() -> None:
    """Remove MTEP Platform and pilot data."""
    conn = op.get_bind()

    # Get project ID
    project = conn.execute(
        sa.text("SELECT id FROM projects WHERE slug = 'mtep-platform'")
    ).fetchone()

    if not project:
        return

    project_id = str(project[0])

    # Delete in reverse order to respect foreign keys
    conn.execute(
        sa.text("DELETE FROM gate_evidence WHERE gate_id IN (SELECT id FROM gates WHERE project_id = :pid)"),
        {"pid": project_id}
    )

    conn.execute(
        sa.text("DELETE FROM gates WHERE project_id = :pid"),
        {"pid": project_id}
    )

    conn.execute(
        sa.text("DELETE FROM project_members WHERE project_id = :pid"),
        {"pid": project_id}
    )

    conn.execute(
        sa.text("DELETE FROM projects WHERE slug = 'mtep-platform'")
    )
