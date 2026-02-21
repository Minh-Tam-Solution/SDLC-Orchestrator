# Sprint 72: Teams Frontend

**Sprint ID:** S72  
**Status:** ⏳ QUEUED  
**Duration:** 5 days (Feb 03-07, 2026)  
**Goal:** Create Teams UI pages, hooks, and components for full team management

**Dependency:** Sprint 71 (Backend API) must be complete

---

## 🎯 Orchestrator Philosophy: Dual Workbench Support

Per SDLC 6.1.0 Principle #6 "Dual Workbenches", the UI must support both:

### Agent Coaching Environment (ACE) - For SE4H

```
┌─────────────────────────────────────────────────────────────┐
│  ACE Dashboard (Team Owner/Admin View)                     │
├─────────────────────────────────────────────────────────────┤
│  📋 BriefingScript Editor    │  📊 Team Performance        │
│  ├─ Task Queue               │  ├─ Sprint Burndown         │
│  ├─ Agent Assignment         │  ├─ MRP Approval Rate       │
│  └─ Priority Matrix          │  └─ CRP Statistics          │
│─────────────────────────────────────────────────────────────│
│  📝 MentorScript Manager     │  ✅ VCR Approval Queue      │
│  ├─ Standards Library        │  ├─ Pending MRPs            │
│  └─ Prompt Templates         │  └─ Review History          │
└─────────────────────────────────────────────────────────────┘
```

### Agent Execution Environment (AEE) - For SE4A

```
┌─────────────────────────────────────────────────────────────┐
│  AEE Dashboard (Agent/Member View)                         │
├─────────────────────────────────────────────────────────────┤
│  📖 Current BriefingScript   │  📤 MRP Submission          │
│  ├─ Assigned Tasks           │  ├─ Evidence Upload         │
│  ├─ Acceptance Criteria      │  ├─ Test Results            │
│  └─ MentorScript Reference   │  └─ Self-Assessment         │
│─────────────────────────────────────────────────────────────│
│  🤔 CRP Console              │  📊 My Progress             │
│  ├─ Request Guidance         │  ├─ Tasks Completed         │
│  └─ Consultation History     │  └─ MRP Approval Rate       │
└─────────────────────────────────────────────────────────────┘
```

### UI Component Mapping

| Component | ACE (SE4H) | AEE (SE4A) |
|-----------|------------|------------|
| Team Dashboard | Full stats + settings | Limited to assigned tasks |
| Member List | Edit/remove members | View only |
| Settings Page | Full access | Read-only |
| Activity Feed | All team activity | Personal activity only |

---

## 📋 Sprint Overview

| Attribute | Value |
|-----------|-------|
| Sprint Number | 72 |
| Start Date | February 03, 2026 (Monday) |
| End Date | February 07, 2026 (Friday) |
| Working Days | 5 |
| Story Points | 24 |
| Team Capacity | Frontend Dev (5d), Tech Lead (1d) |

---

## 🎯 Sprint Goal

> Implement complete Teams frontend with list/detail pages, member management, team settings, and integration with existing project workflows.

---

## 📊 Sprint Backlog

### Epic: ADR-028 Teams Feature Implementation

#### Story 1: useTeams Hook (5 SP)
**As a** frontend developer  
**I want** TanStack Query hooks for teams  
**So that** I can fetch and mutate team data

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S72-T01 | `useTeams()` - list teams query | Frontend Dev | 2h | ⏳ |
| S72-T02 | `useTeam(id)` - single team query | Frontend Dev | 1h | ⏳ |
| S72-T03 | `useTeamStatistics(id)` - stats query | Frontend Dev | 1h | ⏳ |
| S72-T04 | `createTeam` mutation | Frontend Dev | 1.5h | ⏳ |
| S72-T05 | `updateTeam` mutation | Frontend Dev | 1h | ⏳ |
| S72-T06 | `deleteTeam` mutation | Frontend Dev | 1h | ⏳ |
| S72-T07 | `addMember` mutation | Frontend Dev | 1.5h | ⏳ |
| S72-T08 | `removeMember` mutation | Frontend Dev | 1h | ⏳ |
| S72-T09 | `updateMemberRole` mutation | Frontend Dev | 1h | ⏳ |

**Acceptance Criteria:**
- [ ] All queries properly typed with TypeScript
- [ ] Optimistic updates for mutations
- [ ] Cache invalidation on mutations
- [ ] Error handling with toast notifications
- [ ] Loading states exposed

---

#### Story 2: Teams List Page (5 SP)
**As a** user  
**I want** to see all my teams  
**So that** I can navigate to team workspaces

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S72-T10 | Create `/app/teams/page.tsx` | Frontend Dev | 3h | ⏳ |
| S72-T11 | Create `TeamCard` component | Frontend Dev | 2h | ⏳ |
| S72-T12 | Create `CreateTeamModal` | Frontend Dev | 2h | ⏳ |
| S72-T13 | Empty state for no teams | Frontend Dev | 1h | ⏳ |
| S72-T14 | Search/filter teams | Frontend Dev | 1.5h | ⏳ |

**Acceptance Criteria:**
- [ ] Teams displayed in responsive grid
- [ ] Team card shows name, member count, project count
- [ ] Create team modal with form validation
- [ ] Empty state prompts user to create first team
- [ ] Search filters teams by name

---

#### Story 3: Team Dashboard Page (6 SP)
**As a** team member  
**I want** to see team overview  
**So that** I can understand team activity

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S72-T15 | Create `/app/teams/[id]/page.tsx` | Frontend Dev | 4h | ⏳ |
| S72-T16 | Team header with stats | Frontend Dev | 2h | ⏳ |
| S72-T17 | Members list component | Frontend Dev | 2h | ⏳ |
| S72-T18 | Recent projects section | Frontend Dev | 2h | ⏳ |
| S72-T19 | Activity feed (optional) | Frontend Dev | 2h | ⏳ |

**Acceptance Criteria:**
- [ ] Dashboard shows team name, description
- [ ] Statistics cards: members, projects, compliance
- [ ] Quick links to projects and members
- [ ] Responsive layout (mobile-friendly)

---

#### Story 4: Team Members Management (4 SP)
**As a** team admin  
**I want** to manage team members  
**So that** I can control team access

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S72-T20 | Create `/app/teams/[id]/members/page.tsx` | Frontend Dev | 3h | ⏳ |
| S72-T21 | `InviteMemberModal` component | Frontend Dev | 2h | ⏳ |
| S72-T22 | Role dropdown selector | Frontend Dev | 1h | ⏳ |
| S72-T23 | Remove member confirmation | Frontend Dev | 1h | ⏳ |
| S72-T24 | Member role badges | Frontend Dev | 0.5h | ⏳ |

**Acceptance Criteria:**
- [ ] Members displayed in table with avatar, name, role
- [ ] Admins see invite button
- [ ] Role can be changed via dropdown (owners only)
- [ ] Confirmation dialog for member removal
- [ ] Shows "Owner", "Admin", "Member" badges

---

#### Story 5: Team Settings Page (2 SP)
**As a** team owner  
**I want** to configure team settings  
**So that** I can customize team behavior

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S72-T25 | Create `/app/teams/[id]/settings/page.tsx` | Frontend Dev | 2h | ⏳ |
| S72-T26 | Team info edit form | Frontend Dev | 1.5h | ⏳ |
| S72-T27 | Delete team danger zone | Frontend Dev | 1h | ⏳ |

**Acceptance Criteria:**
- [ ] Edit team name and description
- [ ] Delete team with confirmation (type team name)
- [ ] Only visible to owners/admins

---

#### Story 6: Navigation & Integration (2 SP)
**As a** user  
**I want** teams integrated into the app  
**So that** navigation is seamless

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S72-T28 | Add Teams to sidebar navigation | Frontend Dev | 1h | ⏳ |
| S72-T29 | Team selector in header (optional) | Frontend Dev | 2h | ⏳ |
| S72-T30 | Team filter on projects list | Frontend Dev | 1.5h | ⏳ |
| S72-T31 | Team selector on project creation | Frontend Dev | 1.5h | ⏳ |
| S72-T32 | i18n translations (EN/VN) | Frontend Dev | 2h | ⏳ |

**Acceptance Criteria:**
- [ ] "Teams" link in sidebar with icon
- [ ] Project creation shows team dropdown
- [ ] Projects page can filter by team
- [ ] All text translated EN/VN

---

## 📁 Files to Create/Modify

### New Files
```
frontend/landing/src/
├── hooks/
│   └── useTeams.ts                          # ~200 lines
├── app/(app)/teams/
│   ├── page.tsx                             # Teams list
│   ├── loading.tsx                          # Loading skeleton
│   ├── new/
│   │   └── page.tsx                         # Create team (optional)
│   └── [id]/
│       ├── page.tsx                         # Team dashboard
│       ├── loading.tsx                      # Loading skeleton
│       ├── members/
│       │   └── page.tsx                     # Manage members
│       └── settings/
│           └── page.tsx                     # Team settings
├── components/teams/
│   ├── TeamCard.tsx                         # Team card
│   ├── TeamMemberList.tsx                   # Members table
│   ├── CreateTeamModal.tsx                  # Create modal
│   ├── InviteMemberModal.tsx                # Invite modal
│   └── TeamStatistics.tsx                   # Stats cards
└── locales/
    ├── en/teams.json                        # EN translations
    └── vi/teams.json                        # VN translations
```

### Modified Files
```
frontend/landing/src/
├── components/layout/Sidebar.tsx            # Add Teams link
├── app/(app)/projects/new/page.tsx          # Team selector
├── app/(app)/projects/page.tsx              # Team filter
└── lib/api.ts                               # Add team types
```

---

## 📝 Component Specifications

### useTeams Hook
```typescript
// frontend/landing/src/hooks/useTeams.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

// Types
export interface Team {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  description?: string;
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface TeamWithMembers extends Team {
  members: TeamMember[];
  projects: Project[];
}

export interface TeamMember {
  id: string;
  team_id: string;
  user_id: string;
  role: 'owner' | 'admin' | 'member';
  joined_at: string;
  user: {
    id: string;
    email: string;
    full_name: string;
    avatar_url?: string;
  };
}

export interface TeamStatistics {
  member_count: number;
  project_count: number;
  active_gates: number;
  compliance_score: number;
  created_at: string;
}

// Queries
export function useTeams(organizationId?: string) {
  return useQuery({
    queryKey: ['teams', { organizationId }],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (organizationId) params.set('organization_id', organizationId);
      const response = await api.get(`/teams?${params}`);
      return response.data as Team[];
    },
  });
}

export function useTeam(teamId: string) {
  return useQuery({
    queryKey: ['teams', teamId],
    queryFn: async () => {
      const response = await api.get(`/teams/${teamId}`);
      return response.data as TeamWithMembers;
    },
    enabled: !!teamId,
  });
}

export function useTeamStatistics(teamId: string) {
  return useQuery({
    queryKey: ['teams', teamId, 'statistics'],
    queryFn: async () => {
      const response = await api.get(`/teams/${teamId}/statistics`);
      return response.data as TeamStatistics;
    },
    enabled: !!teamId,
  });
}

// Mutations
export function useCreateTeam() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: {
      name: string;
      slug: string;
      organization_id: string;
      description?: string;
    }) => {
      const response = await api.post('/teams', data);
      return response.data as Team;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] });
    },
  });
}

export function useUpdateTeam(teamId: string) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: { name?: string; description?: string }) => {
      const response = await api.patch(`/teams/${teamId}`, data);
      return response.data as Team;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams', teamId] });
    },
  });
}

export function useDeleteTeam() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (teamId: string) => {
      await api.delete(`/teams/${teamId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] });
    },
  });
}

export function useAddTeamMember(teamId: string) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: { user_id: string; role?: string }) => {
      const response = await api.post(`/teams/${teamId}/members`, data);
      return response.data as TeamMember;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams', teamId] });
    },
  });
}

export function useRemoveTeamMember(teamId: string) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (userId: string) => {
      await api.delete(`/teams/${teamId}/members/${userId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams', teamId] });
    },
  });
}

export function useUpdateTeamMemberRole(teamId: string) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ userId, role }: { userId: string; role: string }) => {
      const response = await api.patch(`/teams/${teamId}/members/${userId}`, { role });
      return response.data as TeamMember;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams', teamId] });
    },
  });
}
```

### Teams List Page
```tsx
// frontend/landing/src/app/(app)/teams/page.tsx
'use client';

import { useState } from 'react';
import { useTranslation } from 'next-i18next';
import { Plus, Search, Users } from 'lucide-react';
import { useTeams } from '@/hooks/useTeams';
import { TeamCard } from '@/components/teams/TeamCard';
import { CreateTeamModal } from '@/components/teams/CreateTeamModal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';

export default function TeamsPage() {
  const { t } = useTranslation('teams');
  const { data: teams, isLoading } = useTeams();
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  const filteredTeams = teams?.filter(team =>
    team.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="container mx-auto py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">{t('title')}</h1>
          <p className="text-muted-foreground">{t('subtitle')}</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="w-4 h-4 mr-2" />
          {t('createTeam')}
        </Button>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          placeholder={t('searchPlaceholder')}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Teams Grid */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-40" />
          ))}
        </div>
      ) : filteredTeams?.length === 0 ? (
        <EmptyState onCreateClick={() => setShowCreateModal(true)} />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredTeams?.map((team) => (
            <TeamCard key={team.id} team={team} />
          ))}
        </div>
      )}

      {/* Create Modal */}
      <CreateTeamModal
        open={showCreateModal}
        onOpenChange={setShowCreateModal}
      />
    </div>
  );
}

function EmptyState({ onCreateClick }: { onCreateClick: () => void }) {
  const { t } = useTranslation('teams');
  
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <Users className="w-12 h-12 text-muted-foreground mb-4" />
      <h3 className="text-lg font-medium mb-2">{t('emptyState.title')}</h3>
      <p className="text-muted-foreground mb-4">{t('emptyState.description')}</p>
      <Button onClick={onCreateClick}>
        <Plus className="w-4 h-4 mr-2" />
        {t('createFirstTeam')}
      </Button>
    </div>
  );
}
```

### i18n Translations
```json
// frontend/landing/src/locales/en/teams.json
{
  "title": "Teams",
  "subtitle": "Manage your teams and collaborate with your organization",
  "createTeam": "Create Team",
  "searchPlaceholder": "Search teams...",
  "emptyState": {
    "title": "No teams yet",
    "description": "Create your first team to start collaborating with your organization."
  },
  "createFirstTeam": "Create your first team",
  "teamCard": {
    "members": "{{count}} members",
    "projects": "{{count}} projects"
  },
  "createModal": {
    "title": "Create Team",
    "nameLabel": "Team Name",
    "namePlaceholder": "Engineering",
    "slugLabel": "Team Slug",
    "slugPlaceholder": "engineering",
    "slugHint": "Used in URLs. Lowercase letters, numbers, and hyphens only.",
    "descriptionLabel": "Description",
    "descriptionPlaceholder": "Optional team description...",
    "cancel": "Cancel",
    "create": "Create Team"
  },
  "dashboard": {
    "members": "Members",
    "projects": "Projects",
    "compliance": "Compliance Score",
    "recentProjects": "Recent Projects",
    "viewAllProjects": "View All Projects"
  },
  "members": {
    "title": "Team Members",
    "invite": "Invite Member",
    "role": "Role",
    "joinedAt": "Joined",
    "actions": "Actions",
    "remove": "Remove",
    "changeRole": "Change Role",
    "roles": {
      "owner": "Owner",
      "admin": "Admin",
      "member": "Member"
    }
  },
  "settings": {
    "title": "Team Settings",
    "general": "General",
    "dangerZone": "Danger Zone",
    "deleteTeam": "Delete Team",
    "deleteWarning": "This action cannot be undone. All projects will be unassigned.",
    "confirmDelete": "Type team name to confirm"
  }
}
```

```json
// frontend/landing/src/locales/vi/teams.json
{
  "title": "Nhóm",
  "subtitle": "Quản lý nhóm và cộng tác với tổ chức của bạn",
  "createTeam": "Tạo Nhóm",
  "searchPlaceholder": "Tìm kiếm nhóm...",
  "emptyState": {
    "title": "Chưa có nhóm nào",
    "description": "Tạo nhóm đầu tiên để bắt đầu cộng tác với tổ chức của bạn."
  },
  "createFirstTeam": "Tạo nhóm đầu tiên",
  "teamCard": {
    "members": "{{count}} thành viên",
    "projects": "{{count}} dự án"
  },
  "createModal": {
    "title": "Tạo Nhóm",
    "nameLabel": "Tên Nhóm",
    "namePlaceholder": "Kỹ thuật",
    "slugLabel": "Slug Nhóm",
    "slugPlaceholder": "ky-thuat",
    "slugHint": "Dùng trong URL. Chỉ chữ thường, số và dấu gạch ngang.",
    "descriptionLabel": "Mô tả",
    "descriptionPlaceholder": "Mô tả nhóm (tùy chọn)...",
    "cancel": "Hủy",
    "create": "Tạo Nhóm"
  },
  "dashboard": {
    "members": "Thành viên",
    "projects": "Dự án",
    "compliance": "Điểm Tuân thủ",
    "recentProjects": "Dự án Gần đây",
    "viewAllProjects": "Xem Tất cả Dự án"
  },
  "members": {
    "title": "Thành viên Nhóm",
    "invite": "Mời Thành viên",
    "role": "Vai trò",
    "joinedAt": "Ngày tham gia",
    "actions": "Thao tác",
    "remove": "Xóa",
    "changeRole": "Đổi Vai trò",
    "roles": {
      "owner": "Chủ sở hữu",
      "admin": "Quản trị viên",
      "member": "Thành viên"
    }
  },
  "settings": {
    "title": "Cài đặt Nhóm",
    "general": "Chung",
    "dangerZone": "Vùng Nguy hiểm",
    "deleteTeam": "Xóa Nhóm",
    "deleteWarning": "Hành động này không thể hoàn tác. Tất cả dự án sẽ bị hủy gán.",
    "confirmDelete": "Nhập tên nhóm để xác nhận"
  }
}
```

---

## ✅ Definition of Done

### Code Complete
- [ ] useTeams hook with all queries/mutations
- [ ] Teams list page with search
- [ ] Team dashboard page
- [ ] Members management page
- [ ] Team settings page
- [ ] All components created

### Tests
- [ ] Hook unit tests (optional)
- [ ] Component render tests (optional)
- [ ] Manual QA of all flows

### Design
- [ ] Responsive on mobile/tablet/desktop
- [ ] Matches existing design system
- [ ] Loading states implemented
- [ ] Error states handled

### i18n
- [ ] English translations complete
- [ ] Vietnamese translations complete
- [ ] All text externalized

### Review
- [ ] Code review approved
- [ ] PR merged to main
- [ ] Staging deployment verified

---

## 📅 Daily Schedule

### Day 1 (Mon, Feb 03)
- [ ] Morning: Create useTeams hook (S72-T01 to T09)
- [ ] Afternoon: Add types to lib/api.ts
- [ ] EOD: Hook complete and tested

### Day 2 (Tue, Feb 04)
- [ ] Morning: Teams list page (S72-T10 to T14)
- [ ] Afternoon: TeamCard component
- [ ] EOD: Teams list functional

### Day 3 (Wed, Feb 05)
- [ ] Morning: Team dashboard (S72-T15 to T19)
- [ ] Afternoon: Statistics cards
- [ ] EOD: Dashboard complete

### Day 4 (Thu, Feb 06)
- [ ] Morning: Members page (S72-T20 to T24)
- [ ] Afternoon: Settings page (S72-T25 to T27)
- [ ] EOD: All pages complete

### Day 5 (Fri, Feb 07)
- [ ] Morning: Navigation integration (S72-T28 to T31)
- [ ] Afternoon: i18n translations (S72-T32)
- [ ] EOD: Code review, PR merged

---

## 🔗 References

- [Sprint 71: Teams Backend API](./SPRINT-71-TEAMS-BACKEND-API.md)
- [Existing hooks pattern](../../../frontend/landing/src/hooks/)
- [shadcn/ui components](https://ui.shadcn.com)
- [TanStack Query docs](https://tanstack.com/query/latest)
