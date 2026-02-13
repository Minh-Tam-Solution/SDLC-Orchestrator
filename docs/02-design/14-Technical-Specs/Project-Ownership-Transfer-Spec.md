# Project Ownership & Transfer Technical Specification

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Date** | February 12, 2026 |
| **Sprint** | Sprint 172 |
| **Status** | CTO APPROVED |
| **Author** | Backend Lead |
| **Reviewer** | CTO |
| **Reference** | Teams-Data-Model-Specification.md, ADR-036-4-Tier-Policy-Enforcement.md |

---

## 1. Overview

This specification defines the project ownership model with tier-dependent team assignment rules. It covers three operations:

1. **Team Reassignment**: Move a project between teams within the same organization
2. **Ownership Transfer**: Transfer project ownership to another project member
3. **Tier Change**: Upgrade/downgrade policy pack tier with validation

All operations are performed via `PATCH /projects/{project_id}` and logged to `governance_audit_log`.

---

## 2. Ownership Hierarchy

```
Organization (billing/compliance root)
    ├── Team A
    │   ├── Project 1 (owner: User X, tier: PROFESSIONAL)
    │   └── Project 2 (owner: User Y, tier: STANDARD)
    ├── Team B
    │   └── Project 3 (owner: User Z, tier: LITE)
    └── Unassigned
        └── Project 4 (owner: User W, tier: LITE, team_id: null)
```

**Key Rules**:
- A project has exactly one `owner_id` (the user who owns it)
- A project has zero or one `team_id` (nullable for LITE/STANDARD tiers)
- PROFESSIONAL and ENTERPRISE tiers require a non-null `team_id`
- Team reassignment is restricted to teams within the same organization

---

## 3. Authorization Matrix

### 3.1 Who Can Perform Each Action

| Action | LITE | STANDARD | PROFESSIONAL | ENTERPRISE |
|--------|------|----------|--------------|------------|
| Update name/description | Owner/Admin | Owner/Admin | Owner/Admin | Owner/Admin |
| Change team | Owner | Owner/Admin | Owner/Admin | Owner/Admin |
| Transfer ownership | Owner only | Owner only | Owner only | Owner only |
| Unassign team (set null) | Owner | Owner/Admin | **Blocked** | **Blocked** |
| Change tier | Owner/Admin | Owner/Admin | Owner/Admin | Owner/Admin |

### 3.2 Additional Requirements for Team Reassignment

- User must be a **member of the target team** (TeamMember record exists)
- Target team must be in the **same organization** as the project
- If project has PROFESSIONAL/ENTERPRISE tier, team_id cannot be set to null

### 3.3 Ownership Transfer Requirements

- New owner must be an **existing ProjectMember** with active status
- Only the **current owner** can initiate a transfer
- Transfer is immediate (no approval workflow required)
- Old owner retains ProjectMember access (role downgraded to "admin" if needed)

---

## 4. Tier-Dependent Validation Rules

### 4.1 Team Assignment by Tier

| Tier | team_id Nullable | Enforcement Mode | On Create | On Update |
|------|-----------------|------------------|-----------|-----------|
| **LITE** | Yes | Advisory | Optional team selector | Can set null |
| **STANDARD** | Yes | Soft | Optional (shows recommendation) | Can set null (warning) |
| **PROFESSIONAL** | No | Hard | Required field | Cannot set null (400 error) |
| **ENTERPRISE** | No | Hard | Required field | Cannot set null (400 error) |

### 4.2 Tier Change Validation

**Upgrade scenarios**:
| From | To | Validation |
|------|----|-----------|
| LITE → STANDARD | Allowed | No additional checks |
| LITE → PROFESSIONAL | Requires team_id | If team_id is null, return 400: "PROFESSIONAL tier requires team assignment" |
| STANDARD → PROFESSIONAL | Requires team_id | If team_id is null, return 400 |
| Any → ENTERPRISE | Requires team_id | If team_id is null, return 400 |

**Downgrade scenarios** (CTO Decision: keep team_id, warn only):
| From | To | Behavior |
|------|----|----------|
| PROFESSIONAL → STANDARD | Allowed | Keep team_id, return warning message |
| PROFESSIONAL → LITE | Allowed | Keep team_id, return warning message |
| ENTERPRISE → Any | Allowed | Keep team_id, return warning message |

**Warning message format**:
```json
{
  "id": "project-uuid",
  "name": "My Project",
  "policy_pack_tier": "LITE",
  "team_id": "team-uuid",
  "warning": "Tier downgraded to LITE. Team assignment is no longer required but has been preserved."
}
```

---

## 5. API Contract

### 5.1 Endpoint

```
PATCH /projects/{project_id}
Authorization: Bearer <token>
Content-Type: application/json
```

### 5.2 Request Body

All fields are optional (PATCH semantics):

```json
{
  "name": "Updated Project Name",
  "description": "Updated description",
  "team_id": "target-team-uuid",
  "owner_id": "new-owner-uuid",
  "policy_pack_tier": "PROFESSIONAL"
}
```

Special values:
- `"team_id": null` - Unassign from team (LITE/STANDARD only)
- Omitting a field means "no change"

### 5.3 Response (200 OK)

```json
{
  "id": "project-uuid",
  "name": "Updated Project Name",
  "description": "Updated description",
  "team_id": "target-team-uuid",
  "team_name": "Team Alpha",
  "owner_id": "new-owner-uuid",
  "owner_name": "John Doe",
  "policy_pack_tier": "PROFESSIONAL",
  "status": "active",
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-02-12T14:30:00Z",
  "warning": null
}
```

### 5.4 Error Responses

| Status | Condition | Body |
|--------|-----------|------|
| 400 | Cross-org team assignment | `{"detail": "Target team must be in same organization as project"}` |
| 400 | PROFESSIONAL+ null team_id | `{"detail": "Cannot unassign team for PROFESSIONAL tier"}` |
| 400 | Tier upgrade without team | `{"detail": "PROFESSIONAL tier requires team assignment"}` |
| 403 | Not owner/admin | `{"detail": "Permission denied"}` |
| 403 | Non-owner attempts transfer | `{"detail": "Only the project owner can transfer ownership"}` |
| 403 | Not member of target team | `{"detail": "You must be a member of target team to reassign"}` |
| 404 | Project not found | `{"detail": "Project not found"}` |
| 404 | Target team not found | `{"detail": "Target team not found"}` |
| 404 | New owner not found | `{"detail": "New owner must be an existing project member"}` |

---

## 6. Backend Implementation

### 6.1 Schema Changes

**File**: `backend/app/schemas/project.py`

Add to `ProjectUpdate`:
```python
class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    team_id: Optional[str] = None        # UUID string or null
    owner_id: Optional[str] = None       # UUID string
    policy_pack_tier: Optional[str] = None  # LITE|STANDARD|PROFESSIONAL|ENTERPRISE
```

### 6.2 Service Layer

**File**: `backend/app/services/teams_service.py`

New method: `validate_project_team_reassignment()`
- Validates target team exists and is not deleted
- Validates same organization constraint
- Validates requesting user is member of target team
- Validates tier-based team_id requirements
- Returns ValidationResult or raises HTTPException

### 6.3 Endpoint Logic

**File**: `backend/app/api/routes/projects.py`

Extended `update_project()` handler:
1. Existing auth check (owner/admin of project)
2. If `team_id` provided: call validation service
3. If `owner_id` provided: validate is ProjectMember + only owner can transfer
4. If `policy_pack_tier` provided: validate tier requirements
5. Apply changes to project model
6. Log to `governance_audit_log`
7. Return updated project with `selectinload` (avoid lazy-load hang)

---

## 7. Frontend Implementation

### 7.1 Type Updates

**File**: `frontend/src/lib/api.ts`

```typescript
export interface ProjectUpdate {
  name?: string;
  description?: string;
  team_id?: string | null;
  owner_id?: string;
  policy_pack_tier?: "LITE" | "STANDARD" | "PROFESSIONAL" | "ENTERPRISE";
}
```

### 7.2 Hook

**File**: `frontend/src/hooks/useProjects.ts`

New hook: `useUpdateProject(projectId: string)`
- Pattern: follows `useUpdateTeam` from `useTeams.ts`
- On success: invalidate project detail + project lists

### 7.3 Edit Project Modal

**File**: `frontend/src/app/app/projects/[id]/page.tsx`

- "Edit Project" button visible to owner/admin only
- Dialog fields:
  - Name (text input, pre-filled)
  - Description (textarea, pre-filled)
  - Team selector (dropdown from `useTeams()`, pre-filled)
  - Owner transfer (dropdown from project members, current owner selected)
  - Tier badge (display current tier)
- Loading/error states following existing modal patterns

---

## 8. Audit Trail

All project ownership changes are logged to `governance_audit_log` table:

| Action Type | Fields Logged |
|-------------|--------------|
| `PROJECT_TEAM_REASSIGNED` | `old_team_id`, `new_team_id`, `tier`, `user_id`, `timestamp` |
| `PROJECT_OWNERSHIP_TRANSFERRED` | `old_owner_id`, `new_owner_id`, `user_id`, `timestamp` |
| `PROJECT_TIER_CHANGED` | `old_tier`, `new_tier`, `warning_issued`, `user_id`, `timestamp` |

---

## 9. Testing Requirements

### 9.1 Unit Tests

| Test | Expected |
|------|----------|
| Update name/description | 200, fields updated |
| Reassign team (same org) | 200, team_id changed |
| Reassign team (cross-org) | 400, blocked |
| Transfer ownership (valid member) | 200, owner_id changed |
| Transfer ownership (non-member) | 404, blocked |
| Transfer by non-owner | 403, blocked |
| Unassign team (LITE) | 200, team_id null |
| Unassign team (PROFESSIONAL) | 400, blocked |
| Upgrade LITE → PROFESSIONAL (with team) | 200, tier changed |
| Upgrade LITE → PROFESSIONAL (no team) | 400, blocked |
| Downgrade PROFESSIONAL → LITE | 200, keep team_id, warning returned |
| Unauthorized user | 403, blocked |
| Non-existent project | 404 |

### 9.2 Integration Tests

- Full workflow: create project → assign team → reassign team → transfer ownership
- Tier change workflow: LITE → STANDARD → PROFESSIONAL → LITE (with warnings)
- Audit log verification: all actions logged correctly

### 9.3 E2E Tests

- Edit modal opens for owner/admin
- Edit modal hidden for viewers
- Team selector shows user's teams only
- Owner transfer dropdown shows project members
- Success toast after update
- Error toast for validation failures

---

## 10. Success Criteria

- [ ] PATCH /projects/{id} accepts team_id, owner_id, policy_pack_tier
- [ ] Cross-org team reassignment blocked (400)
- [ ] PROFESSIONAL/ENTERPRISE null team_id blocked (400)
- [ ] Ownership transfer validates ProjectMember existence
- [ ] Tier downgrade keeps team_id and returns warning
- [ ] All changes logged to governance_audit_log
- [ ] Frontend Edit modal works for owner/admin
- [ ] 13 unit tests passing
- [ ] Integration + E2E tests passing
- [ ] No lazy-load hang (selectinload used)

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Date** | February 12, 2026 |
| **Sprint** | Sprint 172 |
| **Author** | Backend Lead |
| **Reviewer** | CTO |
| **Status** | APPROVED |
