"""Sprint 74: Planning Hierarchy Tables

Revision ID: s74_planning_hierarchy
Revises: s74_merge_heads
Create Date: 2026-01-18 14:00:00.000000

Implements ADR-013 Planning Hierarchy + SDLC 5.1.3 Sprint Governance:
- roadmaps: Strategic 12-month planning
- phases: 4-8 week themed objectives
- sprints: 5-10 day delivery cycles with G-Sprint/G-Sprint-Close gates
- sprint_gate_evaluations: Gate evaluation history with JSONB checklists
- backlog_items: User stories, tasks, bugs with P0/P1/P2 priorities
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = 's74_planning_hierarchy'
down_revision = 's74_merge_heads'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create roadmaps table
    op.create_table(
        'roadmaps',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('vision', sa.Text, nullable=True),
        sa.Column('start_date', sa.Date, nullable=True),
        sa.Column('end_date', sa.Date, nullable=True),
        sa.Column('review_cadence', sa.String(50), server_default='quarterly', nullable=False),  # monthly, quarterly, yearly
        sa.Column('status', sa.String(50), server_default='active', nullable=False),  # draft, active, archived
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()'), nullable=False),
        sa.UniqueConstraint('project_id', 'name', name='uq_roadmaps_project_name')
    )
    op.create_index('idx_roadmaps_project', 'roadmaps', ['project_id'])
    op.create_index('idx_roadmaps_status', 'roadmaps', ['status'])

    # 2. Create phases table
    op.create_table(
        'phases',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('roadmap_id', UUID(as_uuid=True), sa.ForeignKey('roadmaps.id', ondelete='CASCADE'), nullable=False),
        sa.Column('number', sa.Integer, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('theme', sa.Text, nullable=True),  # e.g., "Q1 Foundation"
        sa.Column('objective', sa.Text, nullable=True),  # Phase goal
        sa.Column('start_date', sa.Date, nullable=True),
        sa.Column('end_date', sa.Date, nullable=True),
        sa.Column('status', sa.String(50), server_default='planned', nullable=False),  # planned, active, completed
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()'), nullable=False),
        sa.UniqueConstraint('roadmap_id', 'number', name='uq_phases_roadmap_number')
    )
    op.create_index('idx_phases_roadmap', 'phases', ['roadmap_id'])
    op.create_index('idx_phases_status', 'phases', ['status'])

    # 3. Create sprints table (SDLC 5.1.3 compliant)
    op.create_table(
        'sprints',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('phase_id', UUID(as_uuid=True), sa.ForeignKey('phases.id', ondelete='SET NULL'), nullable=True),  # Optional phase
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('number', sa.Integer, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),  # e.g., "Sprint 74: Planning Hierarchy"
        sa.Column('goal', sa.Text, nullable=False),  # Single sentence sprint goal (Rule #7)
        sa.Column('status', sa.String(50), server_default='planning', nullable=False),  # planning, active, completed, cancelled
        sa.Column('start_date', sa.Date, nullable=True),
        sa.Column('end_date', sa.Date, nullable=True),
        sa.Column('capacity_points', sa.Integer, nullable=True),  # Story points capacity
        sa.Column('team_size', sa.Integer, nullable=True),
        sa.Column('velocity_target', sa.Integer, nullable=True),  # Target velocity

        # SDLC 5.1.3 Sprint Governance Gates
        sa.Column('g_sprint_status', sa.String(50), server_default='pending', nullable=False),  # pending, passed, failed
        sa.Column('g_sprint_approved_by', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('g_sprint_approved_at', sa.DateTime, nullable=True),
        sa.Column('g_sprint_close_status', sa.String(50), server_default='pending', nullable=False),  # pending, passed, failed
        sa.Column('g_sprint_close_approved_by', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('g_sprint_close_approved_at', sa.DateTime, nullable=True),
        sa.Column('documentation_deadline', sa.DateTime, nullable=True),  # 24h business hours from end_date (Rule #2)

        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()'), nullable=False),
        sa.UniqueConstraint('project_id', 'number', name='uq_sprints_project_number')  # Rule #1: Immutable sprint numbers
    )
    op.create_index('idx_sprints_project', 'sprints', ['project_id'])
    op.create_index('idx_sprints_phase', 'sprints', ['phase_id'])
    op.create_index('idx_sprints_status', 'sprints', ['status'])
    op.create_index('idx_sprints_g_sprint_status', 'sprints', ['g_sprint_status'])
    op.create_index('idx_sprints_g_sprint_close_status', 'sprints', ['g_sprint_close_status'])

    # 4. Create sprint_gate_evaluations table
    op.create_table(
        'sprint_gate_evaluations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('sprint_id', UUID(as_uuid=True), sa.ForeignKey('sprints.id', ondelete='CASCADE'), nullable=False),
        sa.Column('gate_type', sa.String(50), nullable=False),  # 'g_sprint' or 'g_sprint_close'
        sa.Column('status', sa.String(50), server_default='pending', nullable=False),  # pending, passed, failed
        sa.Column('checklist', JSONB, nullable=False),  # Checklist items with pass/fail per SDLC 5.1.3
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('evaluated_by', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('evaluated_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()'), nullable=False),
        sa.UniqueConstraint('sprint_id', 'gate_type', name='uq_gate_eval_sprint_type')
    )
    op.create_index('idx_gate_eval_sprint', 'sprint_gate_evaluations', ['sprint_id'])
    op.create_index('idx_gate_eval_type', 'sprint_gate_evaluations', ['gate_type'])
    op.create_index('idx_gate_eval_status', 'sprint_gate_evaluations', ['status'])

    # 5. Create backlog_items table
    op.create_table(
        'backlog_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('sprint_id', UUID(as_uuid=True), sa.ForeignKey('sprints.id', ondelete='SET NULL'), nullable=True),  # Nullable for product backlog
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),  # 'story', 'task', 'bug', 'spike'
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('acceptance_criteria', sa.Text, nullable=True),
        sa.Column('priority', sa.String(10), server_default='P2', nullable=False),  # P0, P1, P2 (Rule #8)
        sa.Column('story_points', sa.Integer, nullable=True),
        sa.Column('status', sa.String(50), server_default='todo', nullable=False),  # todo, in_progress, review, done, blocked
        sa.Column('assignee_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('parent_id', UUID(as_uuid=True), sa.ForeignKey('backlog_items.id', ondelete='SET NULL'), nullable=True),  # For subtasks
        sa.Column('labels', JSONB, server_default='[]', nullable=False),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()'), nullable=False)
    )
    op.create_index('idx_backlog_sprint', 'backlog_items', ['sprint_id'])
    op.create_index('idx_backlog_project', 'backlog_items', ['project_id'])
    op.create_index('idx_backlog_status', 'backlog_items', ['status'])
    op.create_index('idx_backlog_assignee', 'backlog_items', ['assignee_id'])
    op.create_index('idx_backlog_priority', 'backlog_items', ['priority'])
    op.create_index('idx_backlog_type', 'backlog_items', ['type'])
    op.create_index('idx_backlog_parent', 'backlog_items', ['parent_id'])


def downgrade():
    # Drop tables in reverse order (handle FK dependencies)
    op.drop_table('backlog_items')
    op.drop_table('sprint_gate_evaluations')
    op.drop_table('sprints')
    op.drop_table('phases')
    op.drop_table('roadmaps')
