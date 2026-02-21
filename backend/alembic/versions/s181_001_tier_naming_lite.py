"""Sprint 181: Rename SubscriptionPlan FREE → LITE (ADR-059 4-Tier unification)

Revision ID: s181_001
Revises: s178_001
Create Date: 2026-02-19 00:00:00.000000

CONTEXT:
- ADR-059 Enterprise-First Refocus defines canonical tier names:
    LITE / STANDARD / PROFESSIONAL / ENTERPRISE
- subscription_plan_enum previously had value 'free' (SDLC <6.1.0 naming)
- This migration renames the PostgreSQL enum value 'free' → 'lite'
- No data loss: ALTER TYPE ... RENAME VALUE is a non-destructive DDL operation
- All existing rows with plan='free' are automatically updated to plan='lite'
  because the enum value itself is renamed, not re-mapped.

SAFETY:
- ALTER TYPE ... RENAME VALUE requires PostgreSQL 10+ (safe for PG 15.5)
- Non-destructive: existing rows automatically reflect the rename
- Rollback: rename 'lite' → 'free' (safe if LITE rows exist, just re-labels them)
- FOUNDER plan name stays within STANDARD tier (unchanged)

RELATED:
- SubscriptionPlan.FREE → SubscriptionPlan.LITE in app/models/subscription.py
- SubscriptionPlan.LITE default in Subscription.plan column
- ADR-059 Appendix C: Tier-Billing migration steps
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "s181_001"
down_revision = "s178_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Rename subscription_plan_enum value 'free' → 'lite' (ADR-059)."""
    op.execute(
        "ALTER TYPE subscription_plan_enum RENAME VALUE 'free' TO 'lite'"
    )


def downgrade() -> None:
    """Revert subscription_plan_enum value 'lite' → 'free' (rollback)."""
    op.execute(
        "ALTER TYPE subscription_plan_enum RENAME VALUE 'lite' TO 'free'"
    )
