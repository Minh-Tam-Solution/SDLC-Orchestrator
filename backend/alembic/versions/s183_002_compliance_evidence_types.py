"""Sprint 183: Add compliance-specific evidence types (ADR-062)

Revision ID: s183_002
Revises: s182_001
Create Date: 2026-02-20 00:00:00.000000

CONTEXT:
- Sprint 183 "Enterprise SSO Implementation + Compliance Evidence" — ADR-062
- Extends `evidence_type` stored values with 4 compliance-specific types
- New types: SOC2_CONTROL, HIPAA_AUDIT, NIST_AI_RMF, ISO27001

STORAGE APPROACH:
- `gate_evidence.evidence_type` is VARCHAR(50), NOT a PostgreSQL native enum
- Therefore: NO `ALTER TYPE` DDL required
- This migration is documentation-only — the schema change is purely in
  app/schemas/evidence.py (validator allowed_types set) and app layer
- Downgrade is a no-op (VARCHAR values cannot be "un-added")

ADR-062 Decision 1: evidence_type stored as VARCHAR(50) for schema flexibility
ADR-062 Decision 2: 4 new compliance types (SOC2_CONTROL, HIPAA_AUDIT, NIST_AI_RMF, ISO27001)
ADR-062 Decision 3: Backward-compatible — existing records with old types unaffected
ADR-062 Decision 4: Compliance evidence filter via API query param

SAFETY:
- Upgrade: CHECK CONSTRAINT comment-only; no DDL executed (VARCHAR, no enum)
- Downgrade: no-op (VARCHAR values are open-ended; old app versions silently accept)
- Zero table locking — no DDL changes to existing columns

CTO REVIEW:
- ADR-062 approved Sprint 183
- Reference: docs/02-design/ADR-062-Compliance-Evidence-Types.md
"""

import logging

from alembic import op

logger = logging.getLogger(__name__)


# revision identifiers
revision = "s183_002"
down_revision = "s182_001"
branch_labels = None
depends_on = None

# New compliance evidence type values added in Sprint 183
_NEW_COMPLIANCE_TYPES = [
    "SOC2_CONTROL",
    "HIPAA_AUDIT",
    "NIST_AI_RMF",
    "ISO27001",
]


def upgrade() -> None:
    """
    Register Sprint 183 compliance evidence types.

    gate_evidence.evidence_type is VARCHAR(50) — no DDL change required.
    This migration creates a documentation checkpoint in the Alembic history
    and adds an optional CHECK CONSTRAINT comment documenting allowed values.

    The actual enforcement is in app/schemas/evidence.py (Pydantic validator).
    """
    logger.info(
        "s183_002 upgrade: registering compliance evidence types %s "
        "(VARCHAR column — no DDL required)",
        _NEW_COMPLIANCE_TYPES,
    )

    # Record the new allowed values as a SQL comment on the column.
    # This is informational-only and does not lock the table.
    # pg_catalog.obj_description would require a sequence number lookup;
    # use COMMENT ON COLUMN as a lightweight documentation marker instead.
    try:
        op.execute(
            """
            COMMENT ON COLUMN gate_evidence.evidence_type IS
            'Allowed values: DESIGN_DOCUMENT, TEST_RESULTS, CODE_REVIEW, '
            'DEPLOYMENT_PROOF, DOCUMENTATION, COMPLIANCE, '
            'E2E_TESTING_REPORT, API_DOCUMENTATION_REFERENCE, '
            'SECURITY_TESTING_RESULTS, STAGE_CROSS_REFERENCE, '
            'SOC2_CONTROL (ADR-062), HIPAA_AUDIT (ADR-062), '
            'NIST_AI_RMF (ADR-062), ISO27001 (ADR-062)'
            """
        )
        logger.info("s183_002 upgrade: column comment updated successfully")
    except Exception as exc:
        # Non-fatal: table may not exist yet in test environments
        logger.warning(
            "s183_002 upgrade: could not update column comment (non-fatal): %s", exc
        )


def downgrade() -> None:
    """
    Downgrade is a no-op for VARCHAR evidence types.

    The 4 new compliance type strings (SOC2_CONTROL, HIPAA_AUDIT, NIST_AI_RMF,
    ISO27001) are enforced only at the application layer (Pydantic validator).
    Removing them from allowed_types in evidence.py reverts enforcement.

    Any rows already persisted with these values continue to exist — they are
    valid VARCHAR values and cannot break the schema.

    WARNING: After downgrade, new uploads with these types will be rejected by
    the older app version's Pydantic validator, but existing data is unaffected.
    """
    logger.warning(
        "s183_002 downgrade: no-op for VARCHAR evidence_type. "
        "New compliance type values (SOC2_CONTROL, HIPAA_AUDIT, NIST_AI_RMF, ISO27001) "
        "remain in any existing rows but will be rejected by older app versions."
    )
    # Revert column comment to pre-Sprint 183 state
    try:
        op.execute(
            """
            COMMENT ON COLUMN gate_evidence.evidence_type IS
            'Allowed values: DESIGN_DOCUMENT, TEST_RESULTS, CODE_REVIEW, '
            'DEPLOYMENT_PROOF, DOCUMENTATION, COMPLIANCE, '
            'E2E_TESTING_REPORT, API_DOCUMENTATION_REFERENCE, '
            'SECURITY_TESTING_RESULTS, STAGE_CROSS_REFERENCE'
            """
        )
    except Exception as exc:
        logger.warning(
            "s183_002 downgrade: could not revert column comment (non-fatal): %s", exc
        )
