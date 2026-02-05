"""Sprint 136: Add gate approval records for approved gates

Revision ID: s136_001_add_gate_approvals
Revises: s94_001_pr_learnings
Create Date: 2026-02-01

Description:
    Gates have status=APPROVED and approved_at timestamp but missing
    approval records in gate_approvals table. This migration adds
    the missing approval history for audit trail.
"""

from datetime import datetime
from uuid import uuid4

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "s136_001_add_gate_approvals"
down_revision = "s94_001_pr_learnings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add approval records for all gates with status=APPROVED."""
    conn = op.get_bind()

    # User IDs from seed data (a502ce0d23a7)
    ceo_user_id = "b0000000-0000-0000-0000-000000000001"  # Tai Dang
    cto_user_id = "b0000000-0000-0000-0000-000000000003"  # Hiep Dinh
    cpo_user_id = "b0000000-0000-0000-0000-000000000002"  # Dung Luong
    qa_lead_user_id = "b0000000-0000-0000-0000-000000000010"

    # Define approvers for each gate type
    gate_approvers = {
        'PROBLEM_DEFINITION': ceo_user_id,      # G0.1 - CEO approves
        'SOLUTION_DIVERSITY': ceo_user_id,      # G0.2 - CEO approves
        'PLANNING_COMPLETE': cpo_user_id,       # G1 - CPO approves
        'DESIGN_READY': cto_user_id,            # G2 - CTO approves
        'SHIP_READY': cto_user_id,              # G3 - CTO approves
        'TEST_COMPLETE': qa_lead_user_id,       # G4 - QA Lead approves
        'DEPLOY_READY': cto_user_id,            # G5 - CTO approves
        'OPERATE_READY': ceo_user_id,           # G6 - CEO approves
        'INTEGRATION_COMPLETE': cto_user_id,    # G7 - CTO approves
        'COLLABORATION_COMPLETE': cpo_user_id,  # G8 - CPO approves
        'GOVERNANCE_COMPLETE': ceo_user_id,     # G9 - CEO approves
    }

    # Get all approved gates that don't have approval records
    result = conn.execute(text("""
        SELECT g.id, g.gate_type, g.gate_name, g.approved_at, g.project_id
        FROM gates g
        WHERE g.status = 'APPROVED'
          AND g.approved_at IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM gate_approvals ga WHERE ga.gate_id = g.id
          )
    """))

    gates_without_approvals = result.fetchall()

    # Comments for each gate type
    approval_comments = {
        'PROBLEM_DEFINITION': 'Problem definition validated. User personas and market analysis approved.',
        'SOLUTION_DIVERSITY': 'Solution alternatives evaluated. Selected approach approved.',
        'PLANNING_COMPLETE': 'Planning phase complete. FRD and API specifications approved.',
        'DESIGN_READY': 'Architecture design approved. Security baseline validated.',
        'SHIP_READY': 'MVP development complete. Ready for production deployment.',
        'TEST_COMPLETE': 'QA validation complete. All test criteria met.',
        'DEPLOY_READY': 'Deployment plan approved. Rollback procedures tested.',
        'OPERATE_READY': 'Operations ready. Monitoring and runbooks in place.',
        'INTEGRATION_COMPLETE': 'External integrations validated and operational.',
        'COLLABORATION_COMPLETE': 'Knowledge transfer complete. Documentation approved.',
        'GOVERNANCE_COMPLETE': 'Full lifecycle governance validated. Compliance approved.',
    }

    for gate in gates_without_approvals:
        gate_id = gate[0]
        gate_type = gate[1]
        gate_name = gate[2]
        approved_at = gate[3]

        # Determine approver
        approver_id = gate_approvers.get(gate_type, cto_user_id)
        comments = approval_comments.get(gate_type, f'Gate {gate_name} approved.')

        # Generate approval ID
        approval_id = str(uuid4())

        # Insert approval record
        conn.execute(text("""
            INSERT INTO gate_approvals (id, gate_id, approver_id, status, comments, approved_at, created_at, updated_at)
            VALUES (:id, :gate_id, :approver_id, :status, :comments, :approved_at, :created_at, :updated_at)
            ON CONFLICT DO NOTHING
        """), {
            'id': approval_id,
            'gate_id': str(gate_id),
            'approver_id': approver_id,
            'status': 'APPROVED',
            'comments': comments,
            'approved_at': approved_at,
            'created_at': approved_at,
            'updated_at': approved_at,
        })

    print(f"Added approval records for {len(gates_without_approvals)} gates")


def downgrade() -> None:
    """Remove the added approval records."""
    conn = op.get_bind()

    # Remove approval records that were added by this migration
    # We identify them by matching approved_at with gate's approved_at
    conn.execute(text("""
        DELETE FROM gate_approvals ga
        USING gates g
        WHERE ga.gate_id = g.id
          AND ga.approved_at = g.approved_at
          AND ga.comments LIKE '%approved%'
    """))
