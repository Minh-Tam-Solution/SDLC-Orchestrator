# Teams Frontend Specification
## React Components, Hooks, and Pages for Team Orchestration

**Version**: 1.1.0
**Date**: January 25, 2026
**Status**: APPROVED (Updated Sprint 105)
**Author**: Frontend Lead
**Reference**: ADR-028-Teams-Feature-Architecture
**Sprint**: Sprint 72 (Feb 3 - Feb 17, 2026)
**Framework**: SDLC 5.1.2 (Stage 08: COLLABORATE)

**Changelog v1.1.0** (Jan 25, 2026):
- Added `member_type` field to AddMemberInput interface
- Added `ai_agent` to role type definition
- Added SASE-compliant UX behavior: auto-select ai_agent role for AI agent member types

---

## 1. Overview

This specification defines the frontend implementation for Teams feature in SDLC Orchestrator. The Teams feature enables **orchestration of AI+Human teams** following SDLC 5.1.2 SASE principles.

### SDLC Orchestrator = "Nhạc Trưởng" (Conductor)

The Teams feature embodies the core platform philosophy:
- **Orchestrate** both AI Agents (SE4A) and Human Developers (SE4H)
- **Govern** team work through SDLC Quality Gates
- **Collaborate** across 10 SDLC stages (Stage 08: COLLABORATE)
- **Track Evidence** for every team decision and deliverable

### Component Summary

| Category | Components | Priority |
|----------|------------|----------|
| Hooks | 3 | P0 |
| Pages | 6 | P0 |
| Components | 10 | P1 |
| **Total** | **19** | |

---

## 2. Architecture Overview

### Component Tree

```
app/(app)/teams/
├── page.tsx                    # Teams list
├── new/
│   └── page.tsx                # Create team wizard
└── [id]/
    ├── page.tsx                # Team dashboard (orchestration view)
    ├── members/
    │   └── page.tsx            # Member management
    ├── projects/
    │   └── page.tsx            # Team projects
    └── settings/
        └── page.tsx            # Team settings

components/teams/
├── TeamCard.tsx                # Team card in grid
├── TeamSelector.tsx            # Header team switcher
├── TeamMemberList.tsx          # Member list with roles
├── TeamMemberRow.tsx           # Individual member row
├── TeamStatsDashboard.tsx      # Statistics overview
├── TeamActivityFeed.tsx        # Recent activity stream
├── CreateTeamDialog.tsx        # Create team modal
├── AddMemberDialog.tsx         # Add member modal
├── TeamRoleBadge.tsx           # Role badge (owner/admin/member)
└── TeamOrchestrationView.tsx   # SDLC stage progress view

hooks/
├── useTeams.ts                 # Teams queries & mutations
├── useTeamMembers.ts           # Member management
└── useTeamStatistics.ts        # Statistics & analytics
```

---

## 3. React Query Hooks

### 3.1 useTeams Hook

Main hook for team management operations.

```typescript
// frontend/landing/src/hooks/useTeams.ts
import {
  useQuery,
  useMutation,
  useQueryClient,
  UseQueryResult,
  UseMutationResult,
} from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";

// ==================== Types ====================

export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: "free" | "pro" | "enterprise";
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Team {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  description: string | null;
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  members_count?: number;
  projects_count?: number;
}

export interface TeamDetail extends Team {
  members?: TeamMember[];
  projects?: TeamProject[];
}

export interface TeamMember {
  id: string;
  team_id: string;
  user_id: string;
  role: "owner" | "admin" | "member";
  joined_at: string;
  user?: {
    id: string;
    email: string;
    full_name: string;
    avatar_url?: string;
  };
}

export interface TeamProject {
  id: string;
  name: string;
  status: string;
  stage?: string;
}

export interface TeamStatistics {
  team_id: string;
  members_count: number;
  projects_count: number;
  gates_total: number;
  gates_passed: number;
  gates_failed: number;
  gates_pending: number;
  compliance_rate: number;
  evidence_count: number;
  last_activity: string | null;
}

export interface CreateTeamInput {
  organization_id: string;
  name: string;
  slug: string;
  description?: string;
}

export interface UpdateTeamInput {
  name?: string;
  description?: string;
  settings?: Record<string, unknown>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

// ==================== Query Keys ====================

export const teamKeys = {
  all: ["teams"] as const,
  lists: () => [...teamKeys.all, "list"] as const,
  list: (filters?: { organization_id?: string }) =>
    [...teamKeys.lists(), filters] as const,
  details: () => [...teamKeys.all, "detail"] as const,
  detail: (id: string) => [...teamKeys.details(), id] as const,
  statistics: (id: string) => [...teamKeys.all, id, "statistics"] as const,
  members: (id: string) => [...teamKeys.all, id, "members"] as const,
};

// ==================== API Functions ====================

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// ==================== Hooks ====================

/**
 * Hook to list teams user has access to
 * Sprint 72: Teams orchestration dashboard
 */
export function useTeams(filters?: { organization_id?: string }) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: teamKeys.list(filters),
    queryFn: async (): Promise<PaginatedResponse<Team>> => {
      const params = new URLSearchParams();
      if (filters?.organization_id) {
        params.set("organization_id", filters.organization_id);
      }
      return fetchWithAuth(`/teams?${params.toString()}`);
    },
    enabled: isAuthenticated && !authLoading,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Hook to get team details with members and projects
 */
export function useTeam(teamId: string | undefined, options?: {
  includeMembers?: boolean;
  includeProjects?: boolean;
}) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: teamKeys.detail(teamId || ""),
    queryFn: async (): Promise<TeamDetail> => {
      const params = new URLSearchParams();
      if (options?.includeMembers) params.set("include_members", "true");
      if (options?.includeProjects) params.set("include_projects", "true");
      return fetchWithAuth(`/teams/${teamId}?${params.toString()}`);
    },
    enabled: isAuthenticated && !authLoading && !!teamId,
    staleTime: 60 * 1000,
  });
}

/**
 * Hook to get team statistics (orchestration metrics)
 */
export function useTeamStatistics(teamId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: teamKeys.statistics(teamId || ""),
    queryFn: async (): Promise<TeamStatistics> => {
      return fetchWithAuth(`/teams/${teamId}/statistics`);
    },
    enabled: isAuthenticated && !authLoading && !!teamId,
    staleTime: 30 * 1000, // 30 seconds for live stats
  });
}

/**
 * Hook to create a new team
 */
export function useCreateTeam() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateTeamInput): Promise<Team> => {
      return fetchWithAuth("/teams", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: teamKeys.lists() });
    },
  });
}

/**
 * Hook to update team details
 */
export function useUpdateTeam(teamId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: UpdateTeamInput): Promise<Team> => {
      return fetchWithAuth(`/teams/${teamId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
    },
    onSuccess: (updatedTeam) => {
      queryClient.invalidateQueries({ queryKey: teamKeys.lists() });
      queryClient.setQueryData(teamKeys.detail(teamId), updatedTeam);
    },
  });
}

/**
 * Hook to delete a team
 */
export function useDeleteTeam() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (teamId: string): Promise<void> => {
      await fetchWithAuth(`/teams/${teamId}`, { method: "DELETE" });
    },
    onSuccess: (_, teamId) => {
      queryClient.invalidateQueries({ queryKey: teamKeys.lists() });
      queryClient.removeQueries({ queryKey: teamKeys.detail(teamId) });
    },
  });
}

/**
 * Hook to invalidate all team caches
 */
export function useInvalidateTeams() {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: teamKeys.all });
  };
}
```

### 3.2 useTeamMembers Hook

```typescript
// frontend/landing/src/hooks/useTeamMembers.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";
import { teamKeys, TeamMember, PaginatedResponse } from "./useTeams";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export interface AddMemberInput {
  user_id?: string;           // Optional if using user_email
  user_email?: string;        // Find user by email (Sprint 105)
  role?: "owner" | "admin" | "member" | "ai_agent";
  member_type?: "human" | "ai_agent";  // SASE member type
}

export interface UpdateMemberRoleInput {
  role: "owner" | "admin" | "member" | "ai_agent";
}

/**
 * SASE Role Constraint (Sprint 105 UX Improvement):
 *
 * When member_type = "ai_agent":
 *   - Role MUST be "ai_agent" (auto-selected by frontend)
 *   - Frontend shows fixed display instead of dropdown
 *   - This prevents user confusion between Member/AI Agent roles
 *
 * When member_type = "human":
 *   - Role can be "owner", "admin", or "member"
 *   - Frontend shows dropdown with 3 options
 *
 * Backend enforces: AI agents cannot have owner/admin roles (SASE compliance)
 */

/**
 * Hook to list team members
 */
export function useTeamMembers(
  teamId: string | undefined,
  options?: { role?: string }
) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: teamKeys.members(teamId || ""),
    queryFn: async (): Promise<PaginatedResponse<TeamMember>> => {
      const params = new URLSearchParams();
      if (options?.role) params.set("role", options.role);
      return fetchWithAuth(`/teams/${teamId}/members?${params.toString()}`);
    },
    enabled: isAuthenticated && !authLoading && !!teamId,
    staleTime: 60 * 1000,
  });
}

/**
 * Hook to add a member to team
 */
export function useAddTeamMember(teamId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: AddMemberInput): Promise<TeamMember> => {
      return fetchWithAuth(`/teams/${teamId}/members`, {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: teamKeys.members(teamId) });
      queryClient.invalidateQueries({ queryKey: teamKeys.detail(teamId) });
      queryClient.invalidateQueries({ queryKey: teamKeys.statistics(teamId) });
    },
  });
}

/**
 * Hook to update member role
 */
export function useUpdateMemberRole(teamId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      userId,
      role,
    }: {
      userId: string;
      role: "owner" | "admin" | "member";
    }): Promise<TeamMember> => {
      return fetchWithAuth(`/teams/${teamId}/members/${userId}`, {
        method: "PATCH",
        body: JSON.stringify({ role }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: teamKeys.members(teamId) });
    },
  });
}

/**
 * Hook to remove a member from team
 */
export function useRemoveTeamMember(teamId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (userId: string): Promise<void> => {
      await fetchWithAuth(`/teams/${teamId}/members/${userId}`, {
        method: "DELETE",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: teamKeys.members(teamId) });
      queryClient.invalidateQueries({ queryKey: teamKeys.detail(teamId) });
      queryClient.invalidateQueries({ queryKey: teamKeys.statistics(teamId) });
    },
  });
}
```

---

## 4. Page Components

### 4.1 Teams List Page

```typescript
// frontend/landing/src/app/(app)/teams/page.tsx
"use client";

import { useState } from "react";
import Link from "next/link";
import { Plus, Users, FolderOpen, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useTeams, Team } from "@/hooks/useTeams";
import { TeamRoleBadge } from "@/components/teams/TeamRoleBadge";

export default function TeamsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const { data, isLoading, error } = useTeams();

  const teams = data?.items || [];

  // Filter teams by search query
  const filteredTeams = teams.filter(
    (team) =>
      team.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      team.slug.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (error) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center text-destructive">
          <p>Failed to load teams: {error.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Teams</h1>
          <p className="text-muted-foreground mt-1">
            Orchestrate your AI+Human teams across SDLC stages
          </p>
        </div>
        <Link href="/app/teams/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Team
          </Button>
        </Link>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search teams..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Teams Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-3/4" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-4 w-full mb-4" />
                <div className="flex gap-4">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-20" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : filteredTeams.length === 0 ? (
        <div className="text-center py-12">
          <Users className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium">No teams found</h3>
          <p className="text-muted-foreground mb-4">
            {searchQuery
              ? "No teams match your search"
              : "Get started by creating your first team"}
          </p>
          {!searchQuery && (
            <Link href="/app/teams/new">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Create Team
              </Button>
            </Link>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTeams.map((team) => (
            <TeamCard key={team.id} team={team} />
          ))}
        </div>
      )}
    </div>
  );
}

function TeamCard({ team }: { team: Team }) {
  return (
    <Link href={`/app/teams/${team.id}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer">
        <CardHeader>
          <div className="flex items-start justify-between">
            <CardTitle className="text-xl">{team.name}</CardTitle>
          </div>
          <p className="text-sm text-muted-foreground">@{team.slug}</p>
        </CardHeader>
        <CardContent>
          {team.description && (
            <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
              {team.description}
            </p>
          )}
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-1">
              <Users className="h-4 w-4" />
              <span>{team.members_count || 0} members</span>
            </div>
            <div className="flex items-center gap-1">
              <FolderOpen className="h-4 w-4" />
              <span>{team.projects_count || 0} projects</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
```

### 4.2 Team Dashboard Page (Orchestration View)

```typescript
// frontend/landing/src/app/(app)/teams/[id]/page.tsx
"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import {
  Users,
  FolderOpen,
  Settings,
  BarChart3,
  CheckCircle,
  XCircle,
  Clock,
  Activity,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { useTeam, useTeamStatistics } from "@/hooks/useTeams";
import { TeamOrchestrationView } from "@/components/teams/TeamOrchestrationView";
import { TeamActivityFeed } from "@/components/teams/TeamActivityFeed";

export default function TeamDashboardPage() {
  const params = useParams();
  const teamId = params.id as string;

  const { data: team, isLoading: teamLoading } = useTeam(teamId, {
    includeMembers: true,
    includeProjects: true,
  });
  const { data: statistics, isLoading: statsLoading } = useTeamStatistics(teamId);

  if (teamLoading || statsLoading) {
    return <TeamDashboardSkeleton />;
  }

  if (!team) {
    return (
      <div className="container mx-auto py-8 text-center">
        <h2 className="text-2xl font-bold">Team not found</h2>
        <p className="text-muted-foreground mt-2">
          The team you're looking for doesn't exist or you don't have access.
        </p>
        <Link href="/app/teams">
          <Button className="mt-4">Back to Teams</Button>
        </Link>
      </div>
    );
  }

  const compliancePercent = statistics
    ? Math.round(statistics.compliance_rate * 100)
    : 0;

  return (
    <div className="container mx-auto py-8">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">{team.name}</h1>
          <p className="text-muted-foreground mt-1">
            @{team.slug} · {team.description || "No description"}
          </p>
        </div>
        <div className="flex gap-2">
          <Link href={`/app/teams/${teamId}/members`}>
            <Button variant="outline">
              <Users className="mr-2 h-4 w-4" />
              Members
            </Button>
          </Link>
          <Link href={`/app/teams/${teamId}/settings`}>
            <Button variant="outline">
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </Button>
          </Link>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Members"
          value={statistics?.members_count || 0}
          icon={Users}
          description="Team members"
        />
        <StatCard
          title="Projects"
          value={statistics?.projects_count || 0}
          icon={FolderOpen}
          description="Active projects"
        />
        <StatCard
          title="Gates Passed"
          value={statistics?.gates_passed || 0}
          icon={CheckCircle}
          description={`of ${statistics?.gates_total || 0} total`}
          iconColor="text-green-500"
        />
        <StatCard
          title="Compliance"
          value={`${compliancePercent}%`}
          icon={BarChart3}
          description="Quality score"
          iconColor={compliancePercent >= 80 ? "text-green-500" : "text-yellow-500"}
        />
      </div>

      {/* Main Content */}
      <Tabs defaultValue="orchestration" className="space-y-6">
        <TabsList>
          <TabsTrigger value="orchestration">Orchestration</TabsTrigger>
          <TabsTrigger value="projects">Projects</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
        </TabsList>

        <TabsContent value="orchestration">
          <Card>
            <CardHeader>
              <CardTitle>SDLC Stage Progress</CardTitle>
              <CardDescription>
                Track your team's progress across all 10 SDLC stages
              </CardDescription>
            </CardHeader>
            <CardContent>
              <TeamOrchestrationView
                teamId={teamId}
                projects={team.projects || []}
              />
            </CardContent>
          </Card>

          {/* Gate Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  Passed
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {statistics?.gates_passed || 0}
                </div>
                <p className="text-xs text-muted-foreground">gates</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <XCircle className="h-4 w-4 text-red-500" />
                  Failed
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {statistics?.gates_failed || 0}
                </div>
                <p className="text-xs text-muted-foreground">gates</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Clock className="h-4 w-4 text-yellow-500" />
                  Pending
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-yellow-600">
                  {statistics?.gates_pending || 0}
                </div>
                <p className="text-xs text-muted-foreground">gates</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="projects">
          <Card>
            <CardHeader>
              <CardTitle>Team Projects</CardTitle>
              <CardDescription>
                All projects managed by this team
              </CardDescription>
            </CardHeader>
            <CardContent>
              {team.projects && team.projects.length > 0 ? (
                <div className="space-y-4">
                  {team.projects.map((project) => (
                    <Link
                      key={project.id}
                      href={`/app/projects/${project.id}`}
                      className="block"
                    >
                      <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                        <div>
                          <h3 className="font-medium">{project.name}</h3>
                          <p className="text-sm text-muted-foreground">
                            Stage: {project.stage || "Not started"}
                          </p>
                        </div>
                        <Badge>{project.status}</Badge>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <FolderOpen className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">No projects yet</p>
                  <Link href="/app/projects/new">
                    <Button className="mt-4">Create Project</Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="activity">
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>
                Latest actions from team members
              </CardDescription>
            </CardHeader>
            <CardContent>
              <TeamActivityFeed teamId={teamId} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon: Icon,
  description,
  iconColor = "text-primary",
}: {
  title: string;
  value: string | number;
  icon: React.ElementType;
  description: string;
  iconColor?: string;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className={`h-4 w-4 ${iconColor}`} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}

function TeamDashboardSkeleton() {
  return (
    <div className="container mx-auto py-8">
      <div className="flex items-start justify-between mb-8">
        <div>
          <Skeleton className="h-10 w-64 mb-2" />
          <Skeleton className="h-4 w-96" />
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-10 w-32" />
          <Skeleton className="h-10 w-32" />
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
```

### 4.3 TeamOrchestrationView Component

```typescript
// frontend/landing/src/components/teams/TeamOrchestrationView.tsx
"use client";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

// SDLC 5.1.2 Stage definitions
const SDLC_STAGES = [
  { id: "00", name: "Foundation", question: "WHY?" },
  { id: "01", name: "Planning", question: "WHAT?" },
  { id: "02", name: "Design", question: "HOW?" },
  { id: "03", name: "Integrate", question: "Connect?" },
  { id: "04", name: "Build", question: "Building?" },
  { id: "05", name: "Test", question: "Works?" },
  { id: "06", name: "Deploy", question: "Ship?" },
  { id: "07", name: "Operate", question: "Running?" },
  { id: "08", name: "Collaborate", question: "Effective?" },
  { id: "09", name: "Govern", question: "Compliant?" },
];

interface TeamOrchestrationViewProps {
  teamId: string;
  projects: Array<{
    id: string;
    name: string;
    status: string;
    stage?: string;
  }>;
}

export function TeamOrchestrationView({
  teamId,
  projects,
}: TeamOrchestrationViewProps) {
  // Calculate projects per stage
  const stageProjectCounts = SDLC_STAGES.reduce(
    (acc, stage) => {
      acc[stage.id] = projects.filter((p) => p.stage === stage.id).length;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Stage Pipeline */}
        <div className="flex items-center gap-2 overflow-x-auto pb-4">
          {SDLC_STAGES.map((stage, index) => (
            <div key={stage.id} className="flex items-center">
              <StageNode
                stage={stage}
                projectCount={stageProjectCounts[stage.id] || 0}
                isActive={stageProjectCounts[stage.id] > 0}
              />
              {index < SDLC_STAGES.length - 1 && (
                <div className="w-8 h-0.5 bg-border mx-1" />
              )}
            </div>
          ))}
        </div>

        {/* Stage Details Table */}
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-muted">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">Stage</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Question</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Projects</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {SDLC_STAGES.map((stage) => (
                <tr key={stage.id} className="border-t">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs bg-muted px-2 py-1 rounded">
                        {stage.id}
                      </span>
                      <span className="font-medium">{stage.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {stage.question}
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant="secondary">
                      {stageProjectCounts[stage.id] || 0}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <StageStatusBadge count={stageProjectCounts[stage.id] || 0} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </TooltipProvider>
  );
}

function StageNode({
  stage,
  projectCount,
  isActive,
}: {
  stage: { id: string; name: string; question: string };
  projectCount: number;
  isActive: boolean;
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div
          className={cn(
            "flex flex-col items-center min-w-[80px] p-3 rounded-lg border-2 transition-colors",
            isActive
              ? "border-primary bg-primary/10"
              : "border-border bg-background hover:bg-muted"
          )}
        >
          <span className="font-mono text-xs text-muted-foreground">
            {stage.id}
          </span>
          <span className="text-sm font-medium mt-1">{stage.name}</span>
          {projectCount > 0 && (
            <Badge variant="default" className="mt-2">
              {projectCount}
            </Badge>
          )}
        </div>
      </TooltipTrigger>
      <TooltipContent>
        <p className="font-medium">{stage.name}</p>
        <p className="text-xs text-muted-foreground">{stage.question}</p>
        <p className="text-xs mt-1">{projectCount} project(s) in this stage</p>
      </TooltipContent>
    </Tooltip>
  );
}

function StageStatusBadge({ count }: { count: number }) {
  if (count === 0) {
    return <Badge variant="outline">Idle</Badge>;
  }
  if (count > 0) {
    return <Badge variant="default">Active</Badge>;
  }
  return null;
}
```

---

## 5. Internationalization (i18n)

### Vietnamese Translations

```json
// frontend/landing/src/locales/vi/teams.json
{
  "teams": {
    "title": "Đội nhóm",
    "subtitle": "Điều phối đội ngũ AI+Human của bạn qua các giai đoạn SDLC",
    "create": "Tạo đội mới",
    "search": "Tìm kiếm đội...",
    "empty": {
      "title": "Không tìm thấy đội nào",
      "noSearch": "Bắt đầu bằng cách tạo đội đầu tiên của bạn",
      "withSearch": "Không có đội nào khớp với tìm kiếm"
    },
    "card": {
      "members": "thành viên",
      "projects": "dự án"
    },
    "dashboard": {
      "orchestration": "Điều phối",
      "projects": "Dự án",
      "activity": "Hoạt động",
      "stageProgress": "Tiến độ theo giai đoạn SDLC",
      "stageDescription": "Theo dõi tiến độ đội qua 10 giai đoạn SDLC"
    },
    "stats": {
      "members": "Thành viên",
      "projects": "Dự án",
      "gatesPassed": "Gates Đạt",
      "compliance": "Tuân thủ",
      "qualityScore": "Điểm chất lượng"
    },
    "roles": {
      "owner": "Chủ sở hữu",
      "admin": "Quản trị viên",
      "member": "Thành viên"
    },
    "stages": {
      "00": { "name": "Nền tảng", "question": "TẠI SAO?" },
      "01": { "name": "Lập kế hoạch", "question": "CÁI GÌ?" },
      "02": { "name": "Thiết kế", "question": "LÀM SAO?" },
      "03": { "name": "Tích hợp", "question": "Kết nối?" },
      "04": { "name": "Xây dựng", "question": "Đang xây?" },
      "05": { "name": "Kiểm thử", "question": "Hoạt động?" },
      "06": { "name": "Triển khai", "question": "Ship?" },
      "07": { "name": "Vận hành", "question": "Đang chạy?" },
      "08": { "name": "Cộng tác", "question": "Hiệu quả?" },
      "09": { "name": "Quản trị", "question": "Tuân thủ?" }
    }
  }
}
```

---

## 6. Success Criteria

### Sprint 72 Definition of Done

- [ ] `useTeams` hook implemented with all queries/mutations
- [ ] `useTeamMembers` hook implemented
- [ ] Teams list page renders with search
- [ ] Team dashboard page shows orchestration view
- [ ] Member management page allows add/remove/role change
- [ ] Team settings page allows update team details
- [ ] i18n support for EN/VN
- [ ] Mobile responsive (768px breakpoint)
- [ ] Loading states with skeletons
- [ ] Error handling with user-friendly messages
- [ ] 90%+ accessibility (WCAG 2.1 AA)

### Performance Targets

| Metric | Target |
|--------|--------|
| Teams list load | <500ms |
| Team dashboard load | <800ms |
| Component render | <100ms |
| Lighthouse score | >90 |

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Date** | January 17, 2026 |
| **Author** | Frontend Lead |
| **Reviewer** | CTO |
| **Status** | APPROVED |
