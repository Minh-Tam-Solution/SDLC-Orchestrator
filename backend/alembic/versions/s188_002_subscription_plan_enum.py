"""s188_002_subscription_plan_enum — Add 'starter' and 'pro' to subscription_plan_enum

Sprint 188 — GA Launch (F-01 fix: SubscriptionPlan missing STARTER and PRO)

Problem (F-01, P1 BLOCKING):
  TIER_LIMITS in usage_limits.py defines 6 tiers including "starter" and "pro".
  UsageLimitsMiddleware looks up Subscription.plan to resolve the effective tier.
  But the PostgreSQL enum 'subscription_plan_enum' only had 4 values:
    lite, founder, standard, enterprise
  → "starter" and "pro" were never stored → _resolve_effective_tier fell back to "lite"
  → PRO customers ($499/mo) were enforced at LITE limits (1 project, 100MB).

Fix:
  Add 'starter' ($99/mo, STANDARD_STARTER tier) and 'pro' ($499/mo, PROFESSIONAL tier)
  to the subscription_plan_enum PostgreSQL ENUM type.

  Python model update:  app/models/subscription.py  (SubscriptionPlan enum, Sprint 188)
  PostgreSQL DDL:       ALTER TYPE subscription_plan_enum ADD VALUE IF NOT EXISTS ...

TECHNICAL NOTE — ADD VALUE outside transaction:
  PostgreSQL requires ALTER TYPE ... ADD VALUE to run outside any open transaction
  block. Alembic wraps all migrations in context.begin_transaction(), so we must
  obtain the raw connection and set isolation_level="AUTOCOMMIT" before executing.
  The IF NOT EXISTS guard makes this idempotent (safe to re-run).

DOWNGRADE NOTE — PostgreSQL ≤ 15 has no DROP VALUE:
  ALTER TYPE ... DROP VALUE was added in PostgreSQL 16. This project targets PG 15.5.
  Downgrade therefore recreates the enum from scratch without 'starter'/'pro', then
  re-types the subscriptions.plan column via an explicit USING cast.
  A guard ensures no live rows use the removed values before proceeding.

Revision ID: s188002
Revises:     s187001
Create Date: 2026-02-20 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "s188002"
down_revision = "s187001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add 'starter' and 'pro' enum values to subscription_plan_enum (F-01 fix)."""
    # ALTER TYPE ADD VALUE cannot run inside a transaction block (PostgreSQL requirement).
    # Switching to AUTOCOMMIT commits any Alembic-managed transaction implicitly.
    connection = op.get_bind()
    autocommit_conn = connection.execution_options(isolation_level="AUTOCOMMIT")

    autocommit_conn.execute(
        sa.text(
            "ALTER TYPE subscription_plan_enum ADD VALUE IF NOT EXISTS 'starter'"
        )
    )
    autocommit_conn.execute(
        sa.text(
            "ALTER TYPE subscription_plan_enum ADD VALUE IF NOT EXISTS 'pro'"
        )
    )


def downgrade() -> None:
    """Remove 'starter' and 'pro' from subscription_plan_enum (enum recreation).

    PostgreSQL 15.5 does not support ALTER TYPE DROP VALUE.  We recreate the enum
    type without the two new values.

    Guard: if any subscription row currently uses 'starter' or 'pro', raise an
    error — the operator must re-assign those rows before downgrading.
    """
    connection = op.get_bind()

    # Guard: abort if any live data uses the values being removed.
    result = connection.execute(
        sa.text(
            "SELECT COUNT(*) FROM subscriptions WHERE plan IN ('starter', 'pro')"
        )
    )
    count = result.scalar()
    if count and count > 0:
        raise RuntimeError(
            f"Cannot downgrade: {count} subscription row(s) use plan='starter' or "
            "'pro'. Manually re-assign those rows to another plan value before "
            "running this downgrade."
        )

    # Recreate the enum without 'starter' and 'pro' using AUTOCOMMIT (DDL outside tx).
    autocommit_conn = connection.execution_options(isolation_level="AUTOCOMMIT")

    # Step 1: Create the reduced enum under a temporary name.
    # DROP IF EXISTS first — makes downgrade idempotent if it failed mid-sequence.
    autocommit_conn.execute(
        sa.text("DROP TYPE IF EXISTS subscription_plan_enum_s188_downgrade")
    )
    autocommit_conn.execute(
        sa.text(
            "CREATE TYPE subscription_plan_enum_s188_downgrade AS ENUM "
            "('lite', 'founder', 'standard', 'enterprise')"
        )
    )

    # Step 2: Migrate the subscriptions.plan column to the new type.
    #         USING cast: plan::text casts the old enum to text, then to the new enum.
    autocommit_conn.execute(
        sa.text(
            "ALTER TABLE subscriptions "
            "ALTER COLUMN plan TYPE subscription_plan_enum_s188_downgrade "
            "USING plan::text::subscription_plan_enum_s188_downgrade"
        )
    )

    # Step 3: Drop the original enum (now no columns reference it).
    autocommit_conn.execute(
        sa.text("DROP TYPE subscription_plan_enum")
    )

    # Step 4: Rename the reduced enum back to the canonical name.
    autocommit_conn.execute(
        sa.text(
            "ALTER TYPE subscription_plan_enum_s188_downgrade "
            "RENAME TO subscription_plan_enum"
        )
    )
