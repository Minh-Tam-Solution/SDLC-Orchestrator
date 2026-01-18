# Sprint Policies Tests
#
# SDLC Stage: 04 - BUILD
# Sprint: 76 - SASE Workflow Integration
# Framework: SDLC 5.1.3 P5 (SASE Integration)
#
# Purpose:
# Test sprint-aware SASE policies for deployment and code review authorization.
# These tests verify GAP 3 resolution - SASE workflows with sprint team context.
#
# Test Coverage (8 tests):
# 1. test_deploy_staging_g_sprint_passed - Staging deploy with passed gate
# 2. test_deploy_staging_g_sprint_pending - Staging deploy blocked by pending gate
# 3. test_deploy_staging_non_member - Non-member cannot deploy
# 4. test_deploy_production_both_gates_passed - Production with both gates
# 5. test_deploy_production_missing_close_gate - Production blocked by close gate
# 6. test_deploy_production_non_admin - Non-admin cannot deploy production
# 7. test_code_review_team_member - Team member can review code
# 8. test_gate_approval_coach_only - Only SE4H Coach can approve gates
#
# Run tests: opa test . -v

package sdlc.sprint

import future.keywords.if

# ==================== Test Data ====================

# Team member context
test_team_member := {
    "user_id": "member-uuid-123",
    "role": "member",
    "can_approve_gates": false,
}

# Team owner context (SE4H Coach)
test_team_owner := {
    "user_id": "owner-uuid-456",
    "role": "owner",
    "can_approve_gates": true,
}

# Team admin context (SE4H Coach)
test_team_admin := {
    "user_id": "admin-uuid-789",
    "role": "admin",
    "can_approve_gates": true,
}

# AI agent context (SE4A - cannot approve gates)
test_ai_agent := {
    "user_id": "ai-agent-uuid-000",
    "role": "member",
    "can_approve_gates": false,
}

# Sprint context with pending gates
test_sprint_pending := {
    "sprint_id": "sprint-uuid-001",
    "team_members": [test_team_member, test_team_owner, test_team_admin],
    "gates": {
        "g_sprint": "pending",
        "g_sprint_close": "pending",
    },
    "status": "planning",
}

# Sprint context with G-Sprint passed (active sprint)
test_sprint_active := {
    "sprint_id": "sprint-uuid-002",
    "team_members": [test_team_member, test_team_owner, test_team_admin],
    "gates": {
        "g_sprint": "passed",
        "g_sprint_close": "pending",
    },
    "status": "active",
}

# Sprint context with both gates passed (completed sprint)
test_sprint_completed := {
    "sprint_id": "sprint-uuid-003",
    "team_members": [test_team_member, test_team_owner, test_team_admin],
    "gates": {
        "g_sprint": "passed",
        "g_sprint_close": "passed",
    },
    "status": "completed",
}

# ==================== Deploy to Staging Tests ====================

# Test 1: Staging deploy allowed when G-Sprint passed and requester is team member
test_deploy_staging_g_sprint_passed if {
    deploy_allowed with input as {
        "action": "deploy_staging",
        "sprint_context": test_sprint_active,
        "requester_id": "member-uuid-123",
    }
}

# Test 2: Staging deploy blocked when G-Sprint pending
test_deploy_staging_g_sprint_pending if {
    not deploy_allowed with input as {
        "action": "deploy_staging",
        "sprint_context": test_sprint_pending,
        "requester_id": "member-uuid-123",
    }
}

# Test 3: Non-member cannot deploy to staging
test_deploy_staging_non_member if {
    not deploy_allowed with input as {
        "action": "deploy_staging",
        "sprint_context": test_sprint_active,
        "requester_id": "non-member-uuid-999",
    }
}

# Test 3b: Staging deploy with environment parameter
test_deploy_staging_with_environment if {
    deploy_allowed with input as {
        "environment": "staging",
        "sprint_context": test_sprint_active,
        "requester_id": "member-uuid-123",
    }
}

# ==================== Deploy to Production Tests ====================

# Test 4: Production deploy allowed when both gates passed and requester is admin
test_deploy_production_both_gates_passed if {
    deploy_allowed with input as {
        "action": "deploy_production",
        "sprint_context": test_sprint_completed,
        "requester_id": "owner-uuid-456",
    }
}

# Test 5: Production deploy blocked when G-Sprint-Close pending
test_deploy_production_missing_close_gate if {
    not deploy_allowed with input as {
        "action": "deploy_production",
        "sprint_context": test_sprint_active,
        "requester_id": "owner-uuid-456",
    }
}

# Test 6: Non-admin member cannot deploy to production (even with all gates passed)
test_deploy_production_non_admin if {
    not deploy_allowed with input as {
        "action": "deploy_production",
        "sprint_context": test_sprint_completed,
        "requester_id": "member-uuid-123",
    }
}

# Test 6b: Admin can deploy to production
test_deploy_production_admin if {
    deploy_allowed with input as {
        "action": "deploy_production",
        "sprint_context": test_sprint_completed,
        "requester_id": "admin-uuid-789",
    }
}

# Test 6c: Production deploy with environment parameter
test_deploy_production_with_environment if {
    deploy_allowed with input as {
        "environment": "production",
        "sprint_context": test_sprint_completed,
        "requester_id": "owner-uuid-456",
    }
}

# ==================== Code Review Tests ====================

# Test 7: Team member can review code
test_code_review_team_member if {
    code_review_allowed with input as {
        "action": "code_review",
        "sprint_context": test_sprint_active,
        "requester_id": "member-uuid-123",
    }
}

# Test 7b: Non-member cannot review code
test_code_review_non_member if {
    not code_review_allowed with input as {
        "action": "code_review",
        "sprint_context": test_sprint_active,
        "requester_id": "non-member-uuid-999",
    }
}

# ==================== Gate Approval Tests ====================

# Test 8: SE4H Coach (owner) can approve gates
test_gate_approval_coach_only if {
    gate_approval_allowed with input as {
        "action": "approve_gate",
        "sprint_context": test_sprint_pending,
        "requester_id": "owner-uuid-456",
    }
}

# Test 8b: Regular member cannot approve gates
test_gate_approval_member_denied if {
    not gate_approval_allowed with input as {
        "action": "approve_gate",
        "sprint_context": test_sprint_pending,
        "requester_id": "member-uuid-123",
    }
}

# Test 8c: Admin (also SE4H Coach) can approve gates
test_gate_approval_admin_allowed if {
    gate_approval_allowed with input as {
        "action": "approve_gate",
        "sprint_context": test_sprint_pending,
        "requester_id": "admin-uuid-789",
    }
}

# ==================== No Sprint Context Tests ====================

# Test: No sprint context blocks all actions
test_no_sprint_context_blocks_deploy if {
    not deploy_allowed with input as {
        "action": "deploy_staging",
        "sprint_context": null,
        "requester_id": "member-uuid-123",
    }
}

test_no_sprint_context_blocks_review if {
    not code_review_allowed with input as {
        "action": "code_review",
        "sprint_context": null,
        "requester_id": "member-uuid-123",
    }
}

# ==================== Denial Reason Tests ====================

# Test: Denial reason for missing G-Sprint gate
test_denial_reason_g_sprint_pending if {
    reason := denial_reason with input as {
        "action": "deploy_staging",
        "sprint_context": test_sprint_pending,
        "requester_id": "member-uuid-123",
    }
    contains(reason, "G-Sprint")
}

# Test: Denial reason for non-team-member
test_denial_reason_non_member if {
    reason := denial_reason with input as {
        "action": "deploy_staging",
        "sprint_context": test_sprint_active,
        "requester_id": "non-member-uuid-999",
    }
    contains(reason, "not a member")
}

# Test: Denial reason for non-coach gate approval
test_denial_reason_non_coach if {
    reason := denial_reason with input as {
        "action": "approve_gate",
        "sprint_context": test_sprint_pending,
        "requester_id": "member-uuid-123",
    }
    contains(reason, "SE4H Coach")
}

# ==================== Response Structure Tests ====================

# Test: Response includes all required fields for allowed action
test_response_allowed if {
    resp := response with input as {
        "action": "deploy_staging",
        "sprint_context": test_sprint_active,
        "requester_id": "member-uuid-123",
    }
    resp.allowed == true
    resp.policy == "sdlc.sprint"
    resp.is_team_member == true
}

# Test: Response includes denial reason for blocked action
test_response_denied if {
    resp := response with input as {
        "action": "deploy_staging",
        "sprint_context": test_sprint_pending,
        "requester_id": "member-uuid-123",
    }
    resp.allowed == false
    contains(resp.reason, "G-Sprint")
}
