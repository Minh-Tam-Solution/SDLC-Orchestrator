"""Sprint 58 - Subscription and Payment tables

Revision ID: s58_sub_pay
Revises: t5o6p7q8r9s0
Create Date: 2025-12-27

Sprint 58: Registration + VNPay
- subscriptions table: User subscription management
- payment_history table: VNPay payment records with idempotency
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 's58_sub_pay'
down_revision = 't5o6p7q8r9s0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types (create_type=False to avoid auto-creation, then explicit create with checkfirst)
    conn = op.get_bind()

    subscription_plan_enum = postgresql.ENUM(
        'free', 'founder', 'standard', 'enterprise',
        name='subscription_plan_enum',
        create_type=False
    )
    subscription_plan_enum.create(conn, checkfirst=True)

    subscription_status_enum = postgresql.ENUM(
        'active', 'canceled', 'past_due',
        name='subscription_status_enum',
        create_type=False
    )
    subscription_status_enum.create(conn, checkfirst=True)

    payment_status_enum = postgresql.ENUM(
        'pending', 'completed', 'failed',
        name='payment_status_enum',
        create_type=False
    )
    payment_status_enum.create(conn, checkfirst=True)

    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('plan', subscription_plan_enum, nullable=False, server_default='free'),
        sa.Column('status', subscription_status_enum, nullable=False, server_default='active'),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('vnpay_subscription_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        comment='User subscriptions - one per user (Sprint 58)'
    )

    # Create indexes for subscriptions
    op.create_index('ix_subscriptions_user_id', 'subscriptions', ['user_id'])
    op.create_index('ix_subscriptions_user_plan', 'subscriptions', ['user_id', 'plan'])

    # Create payment_history table
    op.create_table(
        'payment_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('vnp_txn_ref', sa.String(100), nullable=False, unique=True),
        sa.Column('vnp_transaction_no', sa.String(100), nullable=True),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='VND'),
        sa.Column('plan', sa.String(20), nullable=False),
        sa.Column('status', payment_status_enum, nullable=False, server_default='pending'),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('vnpay_response_code', sa.String(10), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'completed', 'failed')", name='valid_payment_status'),
        comment='VNPay payment history with idempotency support (Sprint 58)'
    )

    # Create indexes for payment_history
    op.create_index('ix_payment_history_user_id', 'payment_history', ['user_id'])
    op.create_index('ix_payment_history_user_status', 'payment_history', ['user_id', 'status'])
    op.create_index('ix_payment_history_vnp_txn_ref', 'payment_history', ['vnp_txn_ref'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_payment_history_vnp_txn_ref', table_name='payment_history')
    op.drop_index('ix_payment_history_user_status', table_name='payment_history')
    op.drop_index('ix_payment_history_user_id', table_name='payment_history')
    op.drop_index('ix_subscriptions_user_plan', table_name='subscriptions')
    op.drop_index('ix_subscriptions_user_id', table_name='subscriptions')

    # Drop tables
    op.drop_table('payment_history')
    op.drop_table('subscriptions')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS payment_status_enum')
    op.execute('DROP TYPE IF EXISTS subscription_status_enum')
    op.execute('DROP TYPE IF EXISTS subscription_plan_enum')
