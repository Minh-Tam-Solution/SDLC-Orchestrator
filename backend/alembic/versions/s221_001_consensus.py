"""consensus migration

Revision ID: s221_001
Revises: s219_001
Create Date: 2026-05-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 's221_001'
down_revision = 's219_001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Step 1: Create consensus_sessions WITHOUT decided_by_vote_id foreign key constraint initially
    op.create_table(
        'consensus_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('topic', sa.String(length=200), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quorum_type', sa.String(length=20), server_default='majority', nullable=False),
        sa.Column('required_voters', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('threshold_pct', sa.Numeric(precision=3, scale=2), server_default='0.67', nullable=True),
        sa.Column('timeout_seconds', sa.Integer(), server_default='300', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='open', nullable=False),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('decided_by_vote_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("quorum_type IN ('majority', 'unanimous', 'threshold')", name='consensus_sessions_quorum_type_check'),
        sa.CheckConstraint("status IN ('open', 'voting', 'decided', 'timeout', 'cancelled')", name='consensus_sessions_status_check'),
        sa.ForeignKeyConstraint(['conversation_id'], ['agent_conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['agent_definitions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consensus_sessions_conversation_id'), 'consensus_sessions', ['conversation_id'], unique=False)

    # Step 2: Create consensus_votes
    op.create_table(
        'consensus_votes',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('voter_agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vote', sa.String(length=10), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("vote IN ('approve', 'reject', 'abstain')", name='consensus_votes_vote_check'),
        sa.ForeignKeyConstraint(['session_id'], ['consensus_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['voter_agent_id'], ['agent_definitions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'voter_agent_id', name='uq_consensus_vote_session_agent')
    )
    op.create_index(op.f('ix_consensus_votes_session_id'), 'consensus_votes', ['session_id'], unique=False)

    # Step 3: Add foreign key for decided_by_vote_id with deferrable constraint
    op.create_foreign_key(
        'fk_decided_vote',
        'consensus_sessions',
        'consensus_votes',
        ['decided_by_vote_id'],
        ['id'],
        ondelete='SET NULL',
        deferrable=True,
        initially='DEFERRED'
    )

def downgrade() -> None:
    # Remove FK first
    op.drop_constraint('fk_decided_vote', 'consensus_sessions', type_='foreignkey')
    
    # Drop votes
    op.drop_index(op.f('ix_consensus_votes_session_id'), table_name='consensus_votes')
    op.drop_table('consensus_votes')
    
    # Drop sessions
    op.drop_index(op.f('ix_consensus_sessions_conversation_id'), table_name='consensus_sessions')
    op.drop_table('consensus_sessions')

