# Sprint 84: Frontend - Teams & Organizations UI

**Sprint ID:** S84
**Status:** ✅ **CTO APPROVED** (January 20, 2026)
**Duration:** 10 days (January 21 - January 31, 2026)
**Goal:** Implement Teams & Organizations management UI to close Frontend-Backend gap
**Story Points:** 34 SP
**Framework Reference:** SDLC 5.1.3 P2 (Sprint Planning Governance)
**Prerequisite:** Sprint 83 ✅ Dynamic Context & Analytics Complete
**Target:** Multi-tenant UI Foundation

---

## Executive Summary

### Gap Analysis Finding (January 20, 2026)

| Category | Backend Endpoints | Frontend Pages | Coverage |
|----------|-------------------|----------------|----------|
| **Teams & Organizations** | 14 endpoints | 0 pages | **0%** 🔴 |

**Business Impact:**
- Users cannot create or manage teams
- Multi-tenant features unusable from UI
- Organization hierarchy not visible
- SASE role management (SE4H/SE4A) blocked

**Sprint 84 Target:** Achieve **100% coverage** for Teams & Organizations APIs

---

## 🎯 Sprint 84 Objectives

### Primary Goals (P0 - Launch Blocker)

1. **Teams Management UI** - Full CRUD + member management
2. **Organizations Management UI** - Organization creation and overview
3. **Sidebar Navigation Update** - Add Teams & Organizations menu items
4. **API Hooks** - `useTeams.ts` and `useOrganizations.ts`

### Secondary Goals (P1)

5. **Team Statistics Dashboard** - Member count, project stats
6. **Role Management UI** - SASE roles (owner, admin, member, ai_agent)
7. **Team Switcher** - Quick team context switching

---

## 📋 Sprint 84 Backlog

### Day 1-2: API Hooks & Types (8 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create `useTeams.ts` hook | Frontend | 4h | P0 | ⏳ |
| Create `useOrganizations.ts` hook | Frontend | 4h | P0 | ⏳ |
| Define TypeScript interfaces for Teams/Orgs | Frontend | 2h | P0 | ⏳ |
| Add API endpoints to `api.ts` | Frontend | 2h | P0 | ⏳ |
| Unit tests for hooks (8 tests) | Frontend | 3h | P0 | ⏳ |

**Files to Create:**

```
frontend/src/hooks/useTeams.ts
frontend/src/hooks/useOrganizations.ts
frontend/src/lib/types/team.ts
frontend/src/lib/types/organization.ts
```

**Hook API Reference:**

```typescript
// useTeams.ts
export function useTeams() {
  // GET /teams - List user's teams
  // Returns: { teams, isLoading, error }
}

export function useTeam(teamId: string) {
  // GET /teams/{teamId} - Get team details
  // Returns: { team, isLoading, error }
}

export function useTeamMembers(teamId: string) {
  // GET /teams/{teamId}/members - List members
  // Returns: { members, isLoading, error }
}

export function useTeamStats(teamId: string) {
  // GET /teams/{teamId}/stats - Get statistics
  // Returns: { stats, isLoading, error }
}

export function useCreateTeam() {
  // POST /teams - Create team
  // Returns: { createTeam, isLoading, error }
}

export function useUpdateTeam(teamId: string) {
  // PATCH /teams/{teamId} - Update team
  // Returns: { updateTeam, isLoading, error }
}

export function useDeleteTeam() {
  // DELETE /teams/{teamId} - Soft delete
  // Returns: { deleteTeam, isLoading, error }
}

export function useAddTeamMember(teamId: string) {
  // POST /teams/{teamId}/members - Add member
  // Returns: { addMember, isLoading, error }
}

export function useRemoveTeamMember(teamId: string) {
  // DELETE /teams/{teamId}/members/{userId}
  // Returns: { removeMember, isLoading, error }
}

export function useUpdateMemberRole(teamId: string) {
  // PATCH /teams/{teamId}/members/{userId}
  // Returns: { updateRole, isLoading, error }
}
```

---

### Day 3-5: Teams UI Pages (12 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create Teams list page | Frontend | 4h | P0 | ⏳ |
| Create Team detail page | Frontend | 4h | P0 | ⏳ |
| Create Team members panel | Frontend | 3h | P0 | ⏳ |
| Create Team modal (Create/Edit) | Frontend | 3h | P0 | ⏳ |
| Create Add Member dialog | Frontend | 2h | P0 | ⏳ |
| Create Role selector component | Frontend | 2h | P1 | ⏳ |
| Team statistics cards | Frontend | 2h | P1 | ⏳ |
| Loading states & skeletons | Frontend | 1h | P0 | ⏳ |
| Error handling & toast notifications | Frontend | 1h | P0 | ⏳ |

**Files to Create:**

```
frontend/src/app/app/teams/
├── page.tsx                     # Team list
├── [id]/
│   └── page.tsx                 # Team detail
└── components/
    ├── TeamCard.tsx             # Team card for list
    ├── TeamModal.tsx            # Create/Edit modal
    ├── TeamMembersList.tsx      # Members panel
    ├── AddMemberDialog.tsx      # Add member dialog
    ├── RoleSelector.tsx         # Role dropdown
    └── TeamStatsCards.tsx       # Statistics display
```

**UI Specifications:**

```
Teams List Page (/app/teams):
┌─────────────────────────────────────────────────────────┐
│ Teams                                    [+ Create Team] │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │
│ │ Team Alpha  │ │ Team Beta   │ │ Team Gamma  │        │
│ │ 5 members   │ │ 3 members   │ │ 8 members   │        │
│ │ 12 projects │ │ 5 projects  │ │ 20 projects │        │
│ │ [View →]    │ │ [View →]    │ │ [View →]    │        │
│ └─────────────┘ └─────────────┘ └─────────────┘        │
└─────────────────────────────────────────────────────────┘

Team Detail Page (/app/teams/[id]):
┌─────────────────────────────────────────────────────────┐
│ ← Back   Team Alpha                     [Edit] [Delete] │
├─────────────────────────────────────────────────────────┤
│ Members (5)                              [+ Add Member] │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Avatar  Name           Email            Role  [⋮]  │ │
│ │ 🧑      John Doe      john@...         Owner  ▼   │ │
│ │ 👩      Jane Smith    jane@...         Admin  ▼   │ │
│ │ 🧑      Bob Wilson    bob@...          Member ▼   │ │
│ │ 🤖      Claude AI     ai@...           AI Agent   │ │
│ └────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ Statistics                                              │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│ │ 5        │ │ 12       │ │ 45       │ │ 87%      │   │
│ │ Members  │ │ Projects │ │ Gates    │ │ Pass Rate│   │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
├─────────────────────────────────────────────────────────┤
│ Projects                                                │
│ • Project A (Gate G2 ✓)                                │
│ • Project B (Gate G1 ⏳)                               │
│ • Project C (Gate G3 ✓)                                │
└─────────────────────────────────────────────────────────┘
```

---

### Day 6-7: Organizations UI Pages (8 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create Organizations list page | Frontend | 3h | P0 | ⏳ |
| Create Organization detail page | Frontend | 3h | P0 | ⏳ |
| Create Organization modal (Create/Edit) | Frontend | 2h | P0 | ⏳ |
| Organization statistics cards | Frontend | 2h | P1 | ⏳ |
| Teams list within Organization | Frontend | 2h | P1 | ⏳ |

**Files to Create:**

```
frontend/src/app/app/organizations/
├── page.tsx                     # Organization list
├── [id]/
│   └── page.tsx                 # Organization detail
└── components/
    ├── OrgCard.tsx              # Organization card
    ├── OrgModal.tsx             # Create/Edit modal
    ├── OrgStatsCards.tsx        # Statistics display
    └── OrgTeamsList.tsx         # Teams within org
```

---

### Day 8-9: Navigation & Integration (4 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Update Sidebar.tsx with new menu items | Frontend | 2h | P0 | ⏳ |
| Create TeamSwitcher component | Frontend | 3h | P1 | ⏳ |
| Add team context to header | Frontend | 2h | P1 | ⏳ |
| Breadcrumb navigation for nested routes | Frontend | 1h | P1 | ⏳ |

**Sidebar Update:**

```tsx
// frontend/src/components/dashboard/Sidebar.tsx

const navigation = [
  { name: "Dashboard", href: "/app", icon: LayoutDashboard },
  { name: "Projects", href: "/app/projects", icon: FolderKanban },
  { name: "Gates", href: "/app/gates", icon: ShieldCheck },
  { name: "Evidence", href: "/app/evidence", icon: FileText },
  { name: "Policies", href: "/app/policies", icon: ScrollText },
  // NEW: Sprint 84
  { name: "Teams", href: "/app/teams", icon: Users },
  { name: "Organizations", href: "/app/organizations", icon: Building2 },
  // END NEW
  { name: "App Builder", href: "/app/codegen", icon: Code2 },
  { name: "SOP Generator", href: "/app/sop-generator", icon: FileCode2 },
  { name: "Settings", href: "/app/settings", icon: Settings },
];
```

---

### Day 10: Testing & QA (2 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| E2E tests for Teams flow | QA | 3h | P0 | ⏳ |
| E2E tests for Organizations flow | QA | 2h | P0 | ⏳ |
| Responsive design testing | QA | 1h | P1 | ⏳ |
| Accessibility audit (WCAG 2.1 AA) | QA | 1h | P1 | ⏳ |
| Performance testing (Lighthouse) | QA | 1h | P1 | ⏳ |

---

## 🔧 Technical Specifications

### API Endpoints Used

| Method | Endpoint | Hook Function |
|--------|----------|---------------|
| POST | `/teams` | `useCreateTeam().createTeam()` |
| GET | `/teams` | `useTeams().teams` |
| GET | `/teams/{id}` | `useTeam(id).team` |
| PATCH | `/teams/{id}` | `useUpdateTeam(id).updateTeam()` |
| DELETE | `/teams/{id}` | `useDeleteTeam().deleteTeam()` |
| GET | `/teams/{id}/stats` | `useTeamStats(id).stats` |
| POST | `/teams/{id}/members` | `useAddTeamMember(id).addMember()` |
| GET | `/teams/{id}/members` | `useTeamMembers(id).members` |
| PATCH | `/teams/{id}/members/{userId}` | `useUpdateMemberRole(id).updateRole()` |
| DELETE | `/teams/{id}/members/{userId}` | `useRemoveTeamMember(id).removeMember()` |
| POST | `/organizations` | `useCreateOrganization().create()` |
| GET | `/organizations` | `useOrganizations().organizations` |
| GET | `/organizations/{id}` | `useOrganization(id).organization` |
| PATCH | `/organizations/{id}` | `useUpdateOrganization(id).update()` |
| GET | `/organizations/{id}/stats` | `useOrgStats(id).stats` |

### TypeScript Interfaces

```typescript
// frontend/src/lib/types/team.ts

export type TeamRole = "owner" | "admin" | "member" | "ai_agent";
export type MemberType = "human" | "ai_agent";

export interface Team {
  id: string;
  name: string;
  slug: string;
  description?: string;
  organization_id: string;
  owner_id: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TeamMember {
  id: string;
  team_id: string;
  user_id: string;
  role: TeamRole;
  member_type: MemberType;
  invited_by?: string;
  joined_at?: string;
  created_at: string;
  user: {
    id: string;
    email: string;
    full_name: string;
    avatar_url?: string;
  };
}

export interface TeamStatistics {
  total_members: number;
  human_members: number;
  ai_agents: number;
  total_projects: number;
  active_projects: number;
  total_gates: number;
  passed_gates: number;
  pass_rate: number;
}

export interface CreateTeamRequest {
  name: string;
  description?: string;
  organization_id: string;
}

export interface UpdateTeamRequest {
  name?: string;
  description?: string;
  is_active?: boolean;
}

export interface AddMemberRequest {
  user_id: string;
  role: TeamRole;
  member_type?: MemberType;
}

export interface UpdateMemberRoleRequest {
  role: TeamRole;
}
```

```typescript
// frontend/src/lib/types/organization.ts

export interface Organization {
  id: string;
  name: string;
  slug: string;
  description?: string;
  owner_id: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface OrganizationStatistics {
  total_teams: number;
  total_members: number;
  total_projects: number;
  active_projects: number;
}

export interface CreateOrganizationRequest {
  name: string;
  description?: string;
}

export interface UpdateOrganizationRequest {
  name?: string;
  description?: string;
}
```

---

## 📊 Success Criteria

| Metric | Target | Verification |
|--------|--------|--------------|
| Teams CRUD working | ✅ | E2E tests pass |
| Organizations CRUD working | ✅ | E2E tests pass |
| Member management working | ✅ | E2E tests pass |
| Role assignment working | ✅ | E2E tests pass |
| API coverage | 100% | All 14 endpoints used |
| Lighthouse score | >90 | Lighthouse audit |
| WCAG 2.1 AA | Pass | Accessibility audit |
| Unit test coverage | >80% | Jest coverage report |

---

## 🚀 Deployment Plan

### Pre-deployment Checklist

- [ ] All E2E tests passing
- [ ] All unit tests passing
- [ ] Lighthouse score >90
- [ ] Accessibility audit passed
- [ ] Code review approved (2+ reviewers)
- [ ] No TypeScript errors
- [ ] No ESLint warnings

### Rollout Strategy

1. **Deploy to staging** - Day 9
2. **Internal testing** - Day 9-10
3. **Production deploy** - Day 10 (end of sprint)
4. **Feature flag** - Teams visible to all users

---

## 📝 Dependencies

### Backend Dependencies (Already Implemented ✅)

- Teams API: 10 endpoints (Sprint 71)
- Organizations API: 5 endpoints (Sprint 71)
- RBAC middleware
- Multi-tenant isolation

### Frontend Dependencies

- shadcn/ui components ✅
- TanStack Query v5 ✅
- React Hook Form ✅
- Zod validation ✅

---

## ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| API contract mismatch | High | Verify with backend team, use OpenAPI spec |
| Performance with large teams | Medium | Implement pagination, virtualization |
| Role permission edge cases | Medium | Comprehensive E2E tests |
| Mobile responsiveness | Low | Test on multiple devices |

---

## 📅 Timeline Summary

| Day | Focus | Deliverables |
|-----|-------|-------------|
| 1-2 | API Hooks | `useTeams.ts`, `useOrganizations.ts`, types |
| 3-5 | Teams UI | List page, detail page, modals, components |
| 6-7 | Organizations UI | List page, detail page, components |
| 8-9 | Navigation | Sidebar update, TeamSwitcher, integration |
| 10 | Testing | E2E tests, QA, deployment |

---

## Approval

- [ ] **CTO Approval**: Technical scope and architecture
- [ ] **CPO Approval**: UX/UI specifications
- [ ] **Backend Lead Approval**: API contract verification
- [ ] **Frontend Lead Approval**: Implementation approach

---

**Sprint Owner:** Frontend Lead
**Reviewers:** CTO, CPO, Backend Lead
**Created:** January 20, 2026
**Last Updated:** January 20, 2026
