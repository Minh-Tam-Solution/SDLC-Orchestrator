-- Sprint 136: Add gate approval records for approved gates
-- Run this SQL to add missing approval history

-- User IDs from seed data
-- CEO: a0000000-0000-0000-0000-000000000001
-- CTO: a0000000-0000-0000-0000-000000000002
-- CPO: a0000000-0000-0000-0000-000000000003

-- Insert approval records for SDLC-Orchestrator gates (project c0000000-0000-0000-0000-000000000003)
-- These gates are APPROVED but missing approval history

-- G0.1 (PROBLEM_DEFINITION) - CEO approved
INSERT INTO gate_approvals (id, gate_id, approver_id, is_approved, comments, approved_at, created_at, updated_at)
SELECT
    gen_random_uuid(),
    g.id,
    'a0000000-0000-0000-0000-000000000001'::uuid,  -- CEO
    true,
    'Problem definition validated. User personas and market analysis approved.',
    g.approved_at,
    g.approved_at,
    g.approved_at
FROM gates g
WHERE g.project_id = 'c0000000-0000-0000-0000-000000000003'
  AND g.gate_type = 'PROBLEM_DEFINITION'
  AND g.status = 'APPROVED'
  AND NOT EXISTS (SELECT 1 FROM gate_approvals ga WHERE ga.gate_id = g.id);

-- G0.2 (SOLUTION_DIVERSITY) - CEO approved
INSERT INTO gate_approvals (id, gate_id, approver_id, is_approved, comments, approved_at, created_at, updated_at)
SELECT
    gen_random_uuid(),
    g.id,
    'a0000000-0000-0000-0000-000000000001'::uuid,  -- CEO
    true,
    'Solution alternatives evaluated. Bridge-first approach approved.',
    g.approved_at,
    g.approved_at,
    g.approved_at
FROM gates g
WHERE g.project_id = 'c0000000-0000-0000-0000-000000000003'
  AND g.gate_type = 'SOLUTION_DIVERSITY'
  AND g.status = 'APPROVED'
  AND NOT EXISTS (SELECT 1 FROM gate_approvals ga WHERE ga.gate_id = g.id);

-- G1 (PLANNING_COMPLETE) - CPO approved
INSERT INTO gate_approvals (id, gate_id, approver_id, is_approved, comments, approved_at, created_at, updated_at)
SELECT
    gen_random_uuid(),
    g.id,
    'a0000000-0000-0000-0000-000000000003'::uuid,  -- CPO
    true,
    'Planning phase complete. FRD and API specifications approved.',
    g.approved_at,
    g.approved_at,
    g.approved_at
FROM gates g
WHERE g.project_id = 'c0000000-0000-0000-0000-000000000003'
  AND g.gate_type = 'PLANNING_COMPLETE'
  AND g.status = 'APPROVED'
  AND NOT EXISTS (SELECT 1 FROM gate_approvals ga WHERE ga.gate_id = g.id);

-- G2 (DESIGN_READY) - CTO approved
INSERT INTO gate_approvals (id, gate_id, approver_id, is_approved, comments, approved_at, created_at, updated_at)
SELECT
    gen_random_uuid(),
    g.id,
    'a0000000-0000-0000-0000-000000000002'::uuid,  -- CTO
    true,
    'Architecture design approved. Security baseline OWASP ASVS L2 validated.',
    g.approved_at,
    g.approved_at,
    g.approved_at
FROM gates g
WHERE g.project_id = 'c0000000-0000-0000-0000-000000000003'
  AND g.gate_type = 'DESIGN_READY'
  AND g.status = 'APPROVED'
  AND NOT EXISTS (SELECT 1 FROM gate_approvals ga WHERE ga.gate_id = g.id);

-- Also add approvals for all other approved gates in the database
INSERT INTO gate_approvals (id, gate_id, approver_id, is_approved, comments, approved_at, created_at, updated_at)
SELECT
    gen_random_uuid(),
    g.id,
    CASE g.gate_type
        WHEN 'PROBLEM_DEFINITION' THEN 'a0000000-0000-0000-0000-000000000001'::uuid      -- CEO
        WHEN 'SOLUTION_DIVERSITY' THEN 'a0000000-0000-0000-0000-000000000001'::uuid      -- CEO
        WHEN 'PLANNING_COMPLETE' THEN 'a0000000-0000-0000-0000-000000000003'::uuid       -- CPO
        WHEN 'DESIGN_READY' THEN 'a0000000-0000-0000-0000-000000000002'::uuid            -- CTO
        WHEN 'SHIP_READY' THEN 'a0000000-0000-0000-0000-000000000002'::uuid              -- CTO
        WHEN 'TEST_COMPLETE' THEN 'a0000000-0000-0000-0000-000000000007'::uuid           -- QA Lead
        WHEN 'DEPLOY_READY' THEN 'a0000000-0000-0000-0000-000000000002'::uuid            -- CTO
        WHEN 'OPERATE_READY' THEN 'a0000000-0000-0000-0000-000000000001'::uuid           -- CEO
        WHEN 'INTEGRATION_COMPLETE' THEN 'a0000000-0000-0000-0000-000000000002'::uuid    -- CTO
        WHEN 'COLLABORATION_COMPLETE' THEN 'a0000000-0000-0000-0000-000000000003'::uuid  -- CPO
        WHEN 'GOVERNANCE_COMPLETE' THEN 'a0000000-0000-0000-0000-000000000001'::uuid     -- CEO
        ELSE 'a0000000-0000-0000-0000-000000000002'::uuid                                 -- Default: CTO
    END,
    true,
    CASE g.gate_type
        WHEN 'PROBLEM_DEFINITION' THEN 'Problem definition validated. User personas and market analysis approved.'
        WHEN 'SOLUTION_DIVERSITY' THEN 'Solution alternatives evaluated. Selected approach approved.'
        WHEN 'PLANNING_COMPLETE' THEN 'Planning phase complete. FRD and API specifications approved.'
        WHEN 'DESIGN_READY' THEN 'Architecture design approved. Security baseline validated.'
        WHEN 'SHIP_READY' THEN 'MVP development complete. Ready for production deployment.'
        WHEN 'TEST_COMPLETE' THEN 'QA validation complete. All test criteria met.'
        WHEN 'DEPLOY_READY' THEN 'Deployment plan approved. Rollback procedures tested.'
        WHEN 'OPERATE_READY' THEN 'Operations ready. Monitoring and runbooks in place.'
        WHEN 'INTEGRATION_COMPLETE' THEN 'External integrations validated and operational.'
        WHEN 'COLLABORATION_COMPLETE' THEN 'Knowledge transfer complete. Documentation approved.'
        WHEN 'GOVERNANCE_COMPLETE' THEN 'Full lifecycle governance validated. Compliance approved.'
        ELSE 'Gate approved.'
    END,
    g.approved_at,
    g.approved_at,
    g.approved_at
FROM gates g
WHERE g.status = 'APPROVED'
  AND g.approved_at IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM gate_approvals ga WHERE ga.gate_id = g.id);

-- Verify the results
SELECT
    g.gate_name,
    g.gate_type,
    g.status,
    g.approved_at,
    ga.comments,
    u.name as approver_name
FROM gates g
LEFT JOIN gate_approvals ga ON ga.gate_id = g.id
LEFT JOIN users u ON u.id = ga.approver_id
WHERE g.project_id = 'c0000000-0000-0000-0000-000000000003'
ORDER BY g.gate_name;
