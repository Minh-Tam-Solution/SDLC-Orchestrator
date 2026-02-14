"""Sprint 172: Sync SDLC-Orchestrator project metadata

Revision ID: s172_001_sync_metadata
Revises: s171_001
Create Date: 2026-02-10 18:30:00.000000

CONTEXT:
- Phase 1 of Project Metadata Auto-Sync feature
- Fixes outdated project information in database
- Aligns with AGENTS.md (Sprint 171) + CLAUDE.md (SDLC 6.0.5)

CHANGES:
- Update SDLC-Orchestrator project description
- Update framework version (4.9.1 → 6.0.5)
- Update status (MVP Development → G3 Ship Ready)
- Update tech stack (add Stripe, i18n, pilot features)

RELATED:
- ADR-029: AGENTS.md Integration Strategy
- AGENTS.md lines 20-23: Sprint 171 status
- CLAUDE.md lines 3-5: Framework 6.0.5
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone


# revision identifiers, used by Alembic.
revision = 's172_001'
down_revision = 's168_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Update SDLC-Orchestrator project metadata to match repo reality.

    Sources:
    - .sdlc-config.json: Project name, tier
    - AGENTS.md (Sprint 171): Current sprint, completion status
    - CLAUDE.md (v3.3.0): Framework version, gate status
    - README.md: Tech stack description
    """

    # New description reflecting Sprint 171 + SDLC 6.0.5 + G3 Ship Ready
    updated_description = """Operating System for Software 3.0 | Governance-first platform on SDLC 6.0.5 (7-Pillar + Section 7 Quality Assurance + AI Governance Principles). Features: Quality Gates, Evidence Vault, AI Context Engine, GitHub Bridge, IR-Based Codegen (EP-06), Multi-Provider AI (Ollama→Claude→DeepCode), i18n Infrastructure (Vietnamese/English), VND Pricing (Stripe Integration), Pilot Landing Page. Tech Stack: Python/FastAPI, React/TypeScript (Next.js), PostgreSQL, Redis, OPA, MinIO, Grafana, Prometheus. Status: G3 Ship Ready (98.2% readiness - Dec 12, 2025). Sprint 171: Market Expansion Foundation (90% complete - Vietnamese SME pilot). Target: Vietnam SME Pilot (5 founding customers Q1 2026)."""

    # Update using raw SQL with escaped quotes
    op.execute(
        f"""
        UPDATE projects
        SET
            description = $${updated_description}$$,
            updated_at = NOW()
        WHERE id = 'c0000000-0000-0000-0000-000000000003'
        """
    )

    print(f"✅ Updated SDLC-Orchestrator project metadata")
    print(f"   - Framework: SDLC 4.9.1 → SDLC 6.0.5")
    print(f"   - Status: MVP Development → G3 Ship Ready (98.2%)")
    print(f"   - Sprint: → Sprint 171 (Market Expansion - 90%)")
    print(f"   - Tech Stack: Added Stripe, i18n, Vietnamese/VND support")


def downgrade() -> None:
    """
    Revert to old metadata (for rollback safety).
    """

    old_description = """Governance-first platform built on SDLC 4.9.1 Complete Lifecycle methodology. Features: Quality Gates, Evidence Vault, AI Context Engine, GitHub Bridge. Tech Stack: Python/FastAPI, React/TypeScript, PostgreSQL, OPA, MinIO. Status: MVP Development. Target: G6 Internal Validation by Week 17."""

    op.execute(
        f"""
        UPDATE projects
        SET
            description = $${old_description}$$,
            updated_at = NOW()
        WHERE id = 'c0000000-0000-0000-0000-000000000003'
        """
    )

    print(f"⏪ Reverted SDLC-Orchestrator project metadata to old version")
