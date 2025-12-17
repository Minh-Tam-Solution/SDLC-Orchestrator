"""
Admin Panel - System Settings and Audit Log enhancements.

Revision ID: m8h9i0j1k2l3
Revises: l7g8h9i0j1k2
Create Date: 2025-12-16

SDLC 5.1.1 Compliance:
- ADR-017: Admin Panel Architecture (APPROVED Dec 16, 2025)
- CTO Condition: Version field for rollback capability
- SOC 2 Type II: Append-only audit logs (CC7.1)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'm8h9i0j1k2l3'
down_revision = 'l7g8h9i0j1k2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create system_settings table and enhance audit_logs."""

    # 1. Create system_settings table (per ADR-017 and CTO condition)
    op.create_table(
        'system_settings',
        sa.Column('key', sa.String(100), primary_key=True),
        sa.Column('value', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('previous_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('category', sa.String(50), nullable=False, server_default='general'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_by', sa.UUID(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
    )

    # Create indexes for system_settings
    op.create_index('ix_system_settings_category', 'system_settings', ['category'])
    op.create_index('ix_system_settings_updated_at', 'system_settings', ['updated_at'])

    # 2. Add target_name column to audit_logs for display purposes
    op.add_column('audit_logs', sa.Column('target_name', sa.String(255), nullable=True))

    # 3. Create append-only rules for audit_logs (SOC 2 compliance)
    # These rules prevent UPDATE and DELETE operations on audit_logs
    op.execute("""
        CREATE OR REPLACE RULE audit_logs_no_update AS
        ON UPDATE TO audit_logs
        DO INSTEAD NOTHING;
    """)

    op.execute("""
        CREATE OR REPLACE RULE audit_logs_no_delete AS
        ON DELETE TO audit_logs
        DO INSTEAD NOTHING;
    """)

    # 4. Insert default system settings
    op.execute("""
        INSERT INTO system_settings (key, value, category, description, version) VALUES
        ('session_timeout_minutes', '30', 'security', 'Session timeout in minutes', 1),
        ('max_login_attempts', '5', 'security', 'Maximum failed login attempts before lockout', 1),
        ('max_projects_per_user', '50', 'limits', 'Maximum projects per user', 1),
        ('max_file_size_mb', '100', 'limits', 'Maximum file size in MB', 1),
        ('ai_council_enabled', 'true', 'features', 'Enable AI Council feature', 1),
        ('mfa_required', 'false', 'security', 'Require MFA for all users', 1),
        ('password_min_length', '12', 'security', 'Minimum password length', 1),
        ('evidence_retention_days', '365', 'limits', 'Evidence retention period in days', 1)
        ON CONFLICT (key) DO NOTHING;
    """)


def downgrade() -> None:
    """Remove system_settings table and audit_logs enhancements."""

    # Remove append-only rules from audit_logs
    op.execute("DROP RULE IF EXISTS audit_logs_no_update ON audit_logs;")
    op.execute("DROP RULE IF EXISTS audit_logs_no_delete ON audit_logs;")

    # Remove target_name column from audit_logs
    op.drop_column('audit_logs', 'target_name')

    # Drop system_settings table
    op.drop_index('ix_system_settings_updated_at')
    op.drop_index('ix_system_settings_category')
    op.drop_table('system_settings')
