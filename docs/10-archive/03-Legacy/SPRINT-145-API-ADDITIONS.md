# Sprint 145+ API Additions

**Version**: 1.0.0
**Date**: February 3, 2026
**Status**: ✅ ACTIVE - Production Ready
**Authority**: Backend Lead + CTO Approved
**Framework**: SDLC 6.0.3 (Framework-First)

---

## Overview

This document covers new API endpoints added in Sprint 145 and subsequent sprints, including:

1. **E2E Testing API** (`/api/v1/e2e/`) - Automated end-to-end test execution
2. **Cross-Reference API** (`/api/v1/cross-reference/`) - Evidence-to-test validation
3. **Organization Invitations API** - Multi-tenant team management
4. **Gate Approval Workflow** - Enhanced approval with async notifications

---

## 1. E2E Testing API

**Base Path**: `/api/v1/e2e`
**Purpose**: Execute and manage end-to-end tests with Evidence Vault integration
**Sprint**: 139-141

### Endpoints

#### POST `/api/v1/e2e/execute`

Execute E2E test suite against a project.

**Request Body**:
```json
{
  "project_id": "uuid",
  "test_suite": "full|smoke|regression",
  "environment": "staging|production",
  "tags": ["authentication", "gates"]
}
```

**Response** (200 OK):
```json
{
  "execution_id": "uuid",
  "status": "RUNNING",
  "started_at": "2026-02-03T10:00:00Z",
  "estimated_duration_seconds": 120
}
```

---

#### GET `/api/v1/e2e/results/{execution_id}`

Get detailed test results for an execution.

**Response** (200 OK):
```json
{
  "execution_id": "uuid",
  "status": "COMPLETED|FAILED|RUNNING",
  "total_tests": 50,
  "passed": 48,
  "failed": 2,
  "skipped": 0,
  "duration_seconds": 95.3,
  "test_results": [
    {
      "test_name": "test_gate_approval_flow",
      "status": "PASSED",
      "duration_ms": 1523,
      "evidence_id": "uuid"
    }
  ],
  "completed_at": "2026-02-03T10:01:35Z"
}
```

---

#### GET `/api/v1/e2e/status/{execution_id}`

Check execution status without full results.

**Response** (200 OK):
```json
{
  "execution_id": "uuid",
  "status": "RUNNING|COMPLETED|FAILED|CANCELLED",
  "progress_percent": 75,
  "current_test": "test_evidence_upload",
  "started_at": "2026-02-03T10:00:00Z"
}
```

---

#### POST `/api/v1/e2e/cancel/{execution_id}`

Cancel a running test execution.

**Response** (200 OK):
```json
{
  "execution_id": "uuid",
  "status": "CANCELLED",
  "cancelled_at": "2026-02-03T10:00:45Z",
  "tests_completed": 25
}
```

---

#### GET `/api/v1/e2e/history`

Get test execution history.

**Query Parameters**:
- `project_id` (optional): Filter by project
- `status` (optional): Filter by status
- `limit` (default: 20): Number of results
- `offset` (default: 0): Pagination offset

**Response** (200 OK):
```json
{
  "items": [
    {
      "execution_id": "uuid",
      "project_id": "uuid",
      "status": "COMPLETED",
      "total_tests": 50,
      "passed": 50,
      "created_at": "2026-02-03T10:00:00Z"
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

---

## 2. Cross-Reference API

**Base Path**: `/api/v1/cross-reference`
**Purpose**: Validate evidence coverage and test traceability
**Sprint**: 139-141

### Endpoints

#### POST `/api/v1/cross-reference/validate`

Validate cross-references between specs, evidence, and tests.

**Request Body**:
```json
{
  "project_id": "uuid",
  "spec_ids": ["SPEC-0001", "SPEC-0002"],
  "include_evidence": true,
  "include_tests": true
}
```

**Response** (200 OK):
```json
{
  "validation_id": "uuid",
  "status": "VALID|INVALID|PARTIAL",
  "coverage_percent": 85.5,
  "missing_evidence": ["SPEC-0003"],
  "missing_tests": ["SPEC-0002"],
  "violations": [
    {
      "spec_id": "SPEC-0002",
      "type": "MISSING_TEST",
      "message": "No test coverage for acceptance criteria"
    }
  ]
}
```

---

#### GET `/api/v1/cross-reference/coverage/{project_id}`

Get overall coverage metrics for a project.

**Response** (200 OK):
```json
{
  "project_id": "uuid",
  "total_specs": 50,
  "specs_with_evidence": 45,
  "specs_with_tests": 40,
  "evidence_coverage_percent": 90.0,
  "test_coverage_percent": 80.0,
  "overall_coverage_percent": 85.0,
  "last_updated": "2026-02-03T10:00:00Z"
}
```

---

#### GET `/api/v1/cross-reference/missing-tests/{project_id}`

Get list of specs missing test coverage.

**Response** (200 OK):
```json
{
  "project_id": "uuid",
  "missing_tests": [
    {
      "spec_id": "SPEC-0023",
      "spec_title": "MCP Commands Design",
      "priority": "HIGH",
      "suggested_test_type": "integration"
    }
  ],
  "total_missing": 5
}
```

---

#### GET `/api/v1/cross-reference/ssot-check/{project_id}`

Check Single Source of Truth compliance.

**Response** (200 OK):
```json
{
  "project_id": "uuid",
  "ssot_compliant": true,
  "issues": [],
  "last_checked": "2026-02-03T10:00:00Z"
}
```

---

## 3. Organization Invitations API

**Base Path**: `/api/v1`
**Purpose**: Manage organization membership via invitations
**Sprint**: 145-146

### Endpoints

#### POST `/api/v1/organizations/{organization_id}/invitations`

Create invitation to join organization.

**Request Body**:
```json
{
  "email": "user@example.com",
  "role": "MEMBER|ADMIN|OWNER",
  "message": "Welcome to our organization!"
}
```

**Response** (201 Created):
```json
{
  "invitation_id": "uuid",
  "organization_id": "uuid",
  "email": "user@example.com",
  "role": "MEMBER",
  "status": "PENDING",
  "token": "secure-invitation-token",
  "expires_at": "2026-02-10T10:00:00Z",
  "created_at": "2026-02-03T10:00:00Z"
}
```

---

#### POST `/api/v1/org-invitations/{invitation_id}/resend`

Resend invitation email.

**Response** (200 OK):
```json
{
  "invitation_id": "uuid",
  "resent_at": "2026-02-03T10:05:00Z",
  "expires_at": "2026-02-10T10:05:00Z"
}
```

---

#### GET `/api/v1/org-invitations/{token}`

Get invitation details by token (for recipient).

**Response** (200 OK):
```json
{
  "invitation_id": "uuid",
  "organization_name": "Acme Corp",
  "organization_id": "uuid",
  "role": "MEMBER",
  "inviter_name": "John Doe",
  "message": "Welcome to our organization!",
  "expires_at": "2026-02-10T10:00:00Z"
}
```

---

#### POST `/api/v1/org-invitations/{token}/accept`

Accept invitation and join organization.

**Response** (200 OK):
```json
{
  "success": true,
  "organization_id": "uuid",
  "user_role": "MEMBER",
  "joined_at": "2026-02-03T10:10:00Z"
}
```

---

#### POST `/api/v1/org-invitations/{token}/decline`

Decline invitation.

**Response** (200 OK):
```json
{
  "success": true,
  "invitation_id": "uuid",
  "declined_at": "2026-02-03T10:10:00Z"
}
```

---

#### GET `/api/v1/organizations/{organization_id}/invitations`

List all pending invitations for organization (admin only).

**Query Parameters**:
- `status` (optional): Filter by PENDING|ACCEPTED|DECLINED|EXPIRED
- `limit` (default: 20)
- `offset` (default: 0)

**Response** (200 OK):
```json
{
  "items": [
    {
      "invitation_id": "uuid",
      "email": "user@example.com",
      "role": "MEMBER",
      "status": "PENDING",
      "created_at": "2026-02-03T10:00:00Z",
      "expires_at": "2026-02-10T10:00:00Z"
    }
  ],
  "total": 5
}
```

---

#### DELETE `/api/v1/org-invitations/{invitation_id}`

Cancel/revoke a pending invitation.

**Response** (204 No Content)

---

## 4. Gate Approval Workflow (Enhanced)

**Base Path**: `/api/v1/gates`
**Enhancement**: Async notifications, optimized queries
**Sprint**: 145

### Updated Endpoints

#### POST `/api/v1/gates/{gate_id}/approve`

Approve or reject a gate (CTO/CPO/CEO only).

**Authorization**: Requires `CTO`, `CPO`, or `CEO` role

**Request Body**:
```json
{
  "approved": true,
  "comments": "All exit criteria validated. Approved for production deployment."
}
```

**Response** (200 OK):
```json
{
  "id": "uuid",
  "gate_name": "G3",
  "status": "APPROVED",
  "approved_at": "2026-02-03T10:30:00Z",
  "approvals": [
    {
      "approver_id": "uuid",
      "status": "APPROVED",
      "comments": "All exit criteria validated.",
      "approved_at": "2026-02-03T10:30:00Z"
    }
  ],
  "evidence_count": 15,
  "policy_violations": []
}
```

**Performance Optimizations** (Sprint 145):
- Stakeholder query: Single JOIN instead of 2 sequential queries
- Notifications: Async via `asyncio.create_task()` (non-blocking)
- Response time: <1s (previously timing out at 10s)

---

## 5. MCP Integration (CLI Only)

**Note**: MCP integration is CLI-only via `sdlcctl` commands, not REST API.

### CLI Commands

```bash
# Connect to platforms
sdlcctl mcp connect --slack --bot-token "xoxb-..." --signing-secret "..." --channel "bugs"
sdlcctl mcp connect --github --app-id 123456 --private-key-path ~/.ssh/github-app.pem

# Manage connections
sdlcctl mcp disconnect slack
sdlcctl mcp disconnect --all --force
sdlcctl mcp test github
sdlcctl mcp list
```

**Architecture**:
```
┌─────────────────────────────────────────────────┐
│              MCP Service (Orchestrator)          │
├─────────────────────────────────────────────────┤
│  SlackAdapter  │  GitHubAdapter  │  EvidenceVault │
└─────────────────────────────────────────────────┘
         ↓                ↓                  ↓
    Slack API       GitHub API      Ed25519 Signing
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `E2E_001` | 400 | Invalid test suite configuration |
| `E2E_002` | 404 | Execution not found |
| `E2E_003` | 409 | Execution already running |
| `XREF_001` | 400 | Invalid spec ID format |
| `XREF_002` | 404 | Project not found |
| `INV_001` | 400 | Invalid email format |
| `INV_002` | 404 | Invitation not found |
| `INV_003` | 410 | Invitation expired |
| `INV_004` | 409 | User already member |
| `GATE_001` | 403 | Gate not in PENDING_APPROVAL status |
| `GATE_002` | 403 | User not authorized (requires CTO/CPO/CEO) |

---

## Rate Limits

| Endpoint Category | Rate Limit |
|-------------------|------------|
| E2E Execute | 10 req/min per project |
| Cross-Reference Validate | 100 req/min |
| Organization Invitations | 50 req/min per org |
| Gate Approval | 100 req/min per user |

---

## Changelog

### v1.0.0 (February 3, 2026)
- Initial documentation for Sprint 145+ API additions
- E2E Testing API (5 endpoints)
- Cross-Reference API (4 endpoints)
- Organization Invitations API (7 endpoints)
- Gate Approval enhancement documentation
- MCP CLI integration reference

---

**Document Status**: ✅ APPROVED
**Next Review**: Sprint 150 (February 2026)
