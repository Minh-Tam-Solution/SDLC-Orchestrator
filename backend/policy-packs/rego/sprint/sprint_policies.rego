# Sprint-aware SASE Policies
#
# SDLC Stage: 04 - BUILD
# Sprint: 76 - SASE Workflow Integration
# Framework: SDLC 5.1.3 P5 (SASE Integration)
#
# Purpose:
# Enforce sprint team membership and gate approval requirements for
# deployment and code review actions. This policy enables SASE workflows
# to verify that requesters are members of the sprint team and that
# required gates have been approved.
#
# GAP 3 Resolution:
# - SASE workflows now receive sprint context
# - Team membership is verified before authorization
# - Gate status (G-Sprint, G-Sprint-Close) checked for deployments
#
# SDLC 5.1.3 Rules Enforced:
# - Rule #2: Post-Sprint Documentation (G-Sprint-Close for production)
# - Rule #3: Sprint Planning Requires Approval (G-Sprint for staging)
# - SE4H Coach: Only human owner/admin for gate approvals
#
# Input Schema:
# {
#   "sprint_context": {
#     "sprint_id": "uuid",
#     "team_members": [{"user_id": "uuid", "role": "owner|admin|member|ai_agent", "can_approve_gates": bool}],
#     "gates": {"g_sprint": "pending|passed|failed", "g_sprint_close": "pending|passed|failed"},
#     "status": "planning|active|completed|cancelled"
#   },
#   "requester_id": "uuid",
#   "action": "deploy_staging|deploy_production|code_review|approve_gate",
#   "environment": "staging|production" (optional)
# }

package sdlc.sprint

import future.keywords.if
import future.keywords.in
import future.keywords.contains

# ==================== Default Deny ====================

default deploy_allowed := false
default code_review_allowed := false
default gate_approval_allowed := false

# ==================== Helper Sets ====================

# Get team member IDs from sprint context
sprint_team_member_ids contains member.user_id if {
    some member in input.sprint_context.team_members
}

# Get team members who can approve gates (SE4H Coach)
sprint_gate_approvers contains member.user_id if {
    some member in input.sprint_context.team_members
    member.can_approve_gates == true
}

# Get admin/owner members for production deploy
sprint_admins contains member.user_id if {
    some member in input.sprint_context.team_members
    member.role in {"owner", "admin"}
}

# ==================== Deploy to Staging ====================

# Deploy to staging requires:
# 1. G-Sprint gate passed (Rule #3)
# 2. Requester is team member
deploy_allowed if {
    input.action == "deploy_staging"
    input.sprint_context != null
    input.sprint_context.gates.g_sprint == "passed"
    input.requester_id in sprint_team_member_ids
}

# Also support environment parameter for flexibility
deploy_allowed if {
    input.environment == "staging"
    input.sprint_context != null
    input.sprint_context.gates.g_sprint == "passed"
    input.requester_id in sprint_team_member_ids
}

# ==================== Deploy to Production ====================

# Deploy to production requires:
# 1. Both G-Sprint and G-Sprint-Close passed (Rules #2 and #3)
# 2. Requester is team admin/owner (stricter control)
deploy_allowed if {
    input.action == "deploy_production"
    input.sprint_context != null
    input.sprint_context.gates.g_sprint == "passed"
    input.sprint_context.gates.g_sprint_close == "passed"
    input.requester_id in sprint_admins
}

# Also support environment parameter for production
deploy_allowed if {
    input.environment == "production"
    input.sprint_context != null
    input.sprint_context.gates.g_sprint == "passed"
    input.sprint_context.gates.g_sprint_close == "passed"
    input.requester_id in sprint_admins
}

# ==================== Code Review ====================

# Code review allowed for any team member
code_review_allowed if {
    input.action == "code_review"
    input.sprint_context != null
    input.requester_id in sprint_team_member_ids
}

# ==================== Gate Approval ====================

# Gate approval requires SE4H Coach (human owner/admin)
# AI agents cannot approve gates per SDLC 5.1.3
gate_approval_allowed if {
    input.action == "approve_gate"
    input.sprint_context != null
    input.requester_id in sprint_gate_approvers
}

# ==================== Authorization Decision ====================

# Main authorization decision
authorized if {
    deploy_allowed
}

authorized if {
    code_review_allowed
}

authorized if {
    gate_approval_allowed
}

default authorized := false

# ==================== Denial Reasons ====================

# Reason when no sprint context provided
denial_reason := "No sprint context provided" if {
    not authorized
    input.sprint_context == null
}

# Reason for staging deployment without G-Sprint
denial_reason := "G-Sprint gate must be approved for staging deployment (SDLC 5.1.3 Rule #3)" if {
    not authorized
    input.action == "deploy_staging"
    input.sprint_context != null
    input.sprint_context.gates.g_sprint != "passed"
}

denial_reason := "G-Sprint gate must be approved for staging deployment (SDLC 5.1.3 Rule #3)" if {
    not authorized
    input.environment == "staging"
    input.sprint_context != null
    input.sprint_context.gates.g_sprint != "passed"
}

# Reason for production deployment without gates
denial_reason := "Both G-Sprint and G-Sprint-Close gates must be approved for production deployment (SDLC 5.1.3 Rules #2 and #3)" if {
    not authorized
    input.action == "deploy_production"
    input.sprint_context != null
    not (input.sprint_context.gates.g_sprint == "passed")
}

denial_reason := "Both G-Sprint and G-Sprint-Close gates must be approved for production deployment (SDLC 5.1.3 Rules #2 and #3)" if {
    not authorized
    input.action == "deploy_production"
    input.sprint_context != null
    input.sprint_context.gates.g_sprint == "passed"
    not (input.sprint_context.gates.g_sprint_close == "passed")
}

denial_reason := "Both G-Sprint and G-Sprint-Close gates must be approved for production deployment (SDLC 5.1.3 Rules #2 and #3)" if {
    not authorized
    input.environment == "production"
    input.sprint_context != null
    not (input.sprint_context.gates.g_sprint == "passed")
}

denial_reason := "Both G-Sprint and G-Sprint-Close gates must be approved for production deployment (SDLC 5.1.3 Rules #2 and #3)" if {
    not authorized
    input.environment == "production"
    input.sprint_context != null
    input.sprint_context.gates.g_sprint == "passed"
    not (input.sprint_context.gates.g_sprint_close == "passed")
}

# Reason for non-admin production deployment
denial_reason := "Only team owners or admins can deploy to production" if {
    not authorized
    input.action == "deploy_production"
    input.sprint_context != null
    input.sprint_context.gates.g_sprint == "passed"
    input.sprint_context.gates.g_sprint_close == "passed"
    not (input.requester_id in sprint_admins)
}

denial_reason := "Only team owners or admins can deploy to production" if {
    not authorized
    input.environment == "production"
    input.sprint_context != null
    input.sprint_context.gates.g_sprint == "passed"
    input.sprint_context.gates.g_sprint_close == "passed"
    not (input.requester_id in sprint_admins)
}

# Reason for non-team-member
denial_reason := "Requester is not a member of the sprint team" if {
    not authorized
    input.sprint_context != null
    not (input.requester_id in sprint_team_member_ids)
}

# Reason for gate approval by non-coach
denial_reason := "Only SE4H Coach (human owner/admin) can approve sprint gates. AI agents cannot approve governance gates." if {
    not authorized
    input.action == "approve_gate"
    input.sprint_context != null
    input.requester_id in sprint_team_member_ids
    not (input.requester_id in sprint_gate_approvers)
}

# Default reason
default denial_reason := "Action not authorized"

# ==================== Response Structure ====================

# Full authorization response
response := {
    "allowed": authorized,
    "reason": reason,
    "policy": "sdlc.sprint",
    "checked_gates": checked_gates,
    "is_team_member": is_member,
    "can_approve_gates": can_approve,
} if {
    authorized
    reason := "Action authorized"
    checked_gates := {
        "g_sprint": input.sprint_context.gates.g_sprint,
        "g_sprint_close": input.sprint_context.gates.g_sprint_close,
    }
    is_member := input.requester_id in sprint_team_member_ids
    can_approve := input.requester_id in sprint_gate_approvers
}

response := {
    "allowed": false,
    "reason": denial_reason,
    "policy": "sdlc.sprint",
    "checked_gates": checked_gates,
    "is_team_member": is_member,
    "can_approve_gates": can_approve,
} if {
    not authorized
    checked_gates := {
        "g_sprint": object.get(object.get(input, "sprint_context", {}), "gates", {}).g_sprint,
        "g_sprint_close": object.get(object.get(input, "sprint_context", {}), "gates", {}).g_sprint_close,
    }
    is_member := input.requester_id in sprint_team_member_ids
    can_approve := input.requester_id in sprint_gate_approvers
}
