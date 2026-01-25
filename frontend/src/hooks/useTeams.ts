/**
 * Teams TanStack Query Hooks - SDLC Orchestrator Dashboard
 *
 * @module frontend/src/hooks/useTeams
 * @description React Query hooks for Teams API
 * @sdlc SDLC 5.1.3 Framework - Sprint 84 (Teams & Organizations UI)
 * @status Sprint 84 - CTO APPROVED (January 20, 2026)
 * @see backend/app/api/routes/teams.py (10 endpoints)
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getTeams,
  getTeam,
  createTeam,
  updateTeam,
  deleteTeam,
  getTeamStats,
  addTeamMember,
  getTeamMembers,
  updateTeamMemberRole,
  removeTeamMember,
  type Team,
  type TeamCreate,
  type TeamUpdate,
  type TeamListResponse,
  type TeamListParams,
  type TeamStatistics,
  type TeamMember,
  type TeamMemberListResponse,
  type TeamMemberListParams,
  type TeamMemberAdd,
  type TeamMemberRoleUpdate,
} from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

// =============================================================================
// Query Keys for Cache Management
// =============================================================================

export const teamKeys = {
  all: ["teams"] as const,
  lists: () => [...teamKeys.all, "list"] as const,
  list: (params?: TeamListParams) => [...teamKeys.lists(), params] as const,
  details: () => [...teamKeys.all, "detail"] as const,
  detail: (id: string) => [...teamKeys.details(), id] as const,
  stats: (id: string) => [...teamKeys.detail(id), "stats"] as const,
  members: (id: string) => [...teamKeys.detail(id), "members"] as const,
  membersList: (id: string, params?: TeamMemberListParams) =>
    [...teamKeys.members(id), params] as const,
};

// =============================================================================
// Team Query Hooks
// =============================================================================

/**
 * Hook to fetch list of teams user is member of
 * Sprint 84: GET /teams - Paginated list with optional org filter
 */
export function useTeams(params?: TeamListParams) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: teamKeys.list(params),
    queryFn: () => getTeams(params),
    enabled: isAuthenticated && !authLoading,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Hook to fetch a single team by ID
 * Sprint 84: GET /teams/{team_id}
 */
export function useTeam(teamId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: teamKeys.detail(teamId || ""),
    queryFn: () => {
      if (!teamId) {
        throw new Error("Missing team ID");
      }
      return getTeam(teamId);
    },
    enabled: isAuthenticated && !authLoading && !!teamId,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Hook to fetch team statistics
 * Sprint 84: GET /teams/{team_id}/stats
 */
export function useTeamStats(teamId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: teamKeys.stats(teamId || ""),
    queryFn: () => {
      if (!teamId) {
        throw new Error("Missing team ID");
      }
      return getTeamStats(teamId);
    },
    enabled: isAuthenticated && !authLoading && !!teamId,
    staleTime: 30 * 1000, // 30 seconds (stats change more frequently)
  });
}

/**
 * Hook to fetch team members
 * Sprint 84: GET /teams/{team_id}/members - Paginated list
 */
export function useTeamMembers(teamId: string | undefined, params?: TeamMemberListParams) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: teamKeys.membersList(teamId || "", params),
    queryFn: () => {
      if (!teamId) {
        throw new Error("Missing team ID");
      }
      return getTeamMembers(teamId, params);
    },
    enabled: isAuthenticated && !authLoading && !!teamId,
    staleTime: 60 * 1000, // 1 minute
  });
}

// =============================================================================
// Team Mutation Hooks
// =============================================================================

/**
 * Hook to create a new team
 * Sprint 84: POST /teams - Creator becomes owner (SE4H Coach)
 */
export function useCreateTeam() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TeamCreate) => createTeam(data),
    onSuccess: () => {
      // Invalidate teams list to refetch
      queryClient.invalidateQueries({ queryKey: teamKeys.all });
    },
  });
}

/**
 * Hook to update a team
 * Sprint 84: PATCH /teams/{team_id} - Admin/Owner only
 */
export function useUpdateTeam(teamId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TeamUpdate) => updateTeam(teamId, data),
    onSuccess: (updatedTeam) => {
      // Update cache with new team data
      queryClient.setQueryData(teamKeys.detail(teamId), updatedTeam);
      // Invalidate lists to reflect changes
      queryClient.invalidateQueries({ queryKey: teamKeys.lists() });
    },
  });
}

/**
 * Hook to delete a team
 * Sprint 84: DELETE /teams/{team_id} - Soft delete, Owner only
 */
export function useDeleteTeam() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (teamId: string) => deleteTeam(teamId),
    onSuccess: (_data, teamId) => {
      // Remove team from cache
      queryClient.removeQueries({ queryKey: teamKeys.detail(teamId) });
      // Invalidate lists to refetch
      queryClient.invalidateQueries({ queryKey: teamKeys.lists() });
    },
  });
}

// =============================================================================
// Team Member Mutation Hooks
// =============================================================================

/**
 * Hook to add a member to team
 * Sprint 84: POST /teams/{team_id}/members - Admin/Owner only
 */
export function useAddTeamMember(teamId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TeamMemberAdd) => addTeamMember(teamId, data),
    onSuccess: () => {
      console.log("[useAddTeamMember] onSuccess called");
      // Invalidate members list and team stats
      queryClient.invalidateQueries({ queryKey: teamKeys.members(teamId) });
      queryClient.invalidateQueries({ queryKey: teamKeys.stats(teamId) });
      // Invalidate team detail (members_count changes)
      queryClient.invalidateQueries({ queryKey: teamKeys.detail(teamId) });
    },
    onError: (error) => {
      // Sprint 105: Added onError callback for debugging
      // This ensures React Query properly handles the error state
      console.log("[useAddTeamMember] onError called:", error);
    },
  });
}

/**
 * Hook to update member role
 * Sprint 84: PATCH /teams/{team_id}/members/{user_id} - Owner only
 */
export function useUpdateMemberRole(teamId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: TeamMemberRoleUpdate }) =>
      updateTeamMemberRole(teamId, userId, data),
    onSuccess: () => {
      // Invalidate members list and team stats
      queryClient.invalidateQueries({ queryKey: teamKeys.members(teamId) });
      queryClient.invalidateQueries({ queryKey: teamKeys.stats(teamId) });
    },
  });
}

/**
 * Hook to remove member from team
 * Sprint 84: DELETE /teams/{team_id}/members/{user_id} - Admin/Owner only
 * Sprint 105: Added optimistic updates to prevent stale UI after delete
 */
export function useRemoveTeamMember(teamId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userId: string) => {
      console.log("[useRemoveTeamMember] mutationFn called for userId:", userId);
      return removeTeamMember(teamId, userId);
    },
    // Sprint 105: Optimistic update - immediately remove member from cache
    // This prevents the "ghost member" issue where user clicks delete on stale data
    onMutate: async (userId: string) => {
      console.log("[useRemoveTeamMember] onMutate called for userId:", userId);
      // Cancel any outgoing refetches to prevent overwriting optimistic update
      await queryClient.cancelQueries({ queryKey: teamKeys.members(teamId) });
      await queryClient.cancelQueries({ queryKey: teamKeys.detail(teamId) });

      // Snapshot the previous values for rollback
      const previousMembers = queryClient.getQueryData<TeamMemberListResponse>(
        teamKeys.membersList(teamId, undefined)
      );
      const previousTeam = queryClient.getQueryData<Team>(teamKeys.detail(teamId));

      // Optimistically update the members list
      if (previousMembers) {
        queryClient.setQueryData<TeamMemberListResponse>(
          teamKeys.membersList(teamId, undefined),
          {
            ...previousMembers,
            items: previousMembers.items.filter((m) => m.user_id !== userId),
            total: previousMembers.total - 1,
          }
        );
      }

      // Return context for rollback
      return { previousMembers, previousTeam };
    },
    onSuccess: () => {
      console.log("[useRemoveTeamMember] onSuccess called");
      // Invalidate to get fresh data from server (confirms our optimistic update)
      queryClient.invalidateQueries({ queryKey: teamKeys.members(teamId) });
      queryClient.invalidateQueries({ queryKey: teamKeys.stats(teamId) });
      queryClient.invalidateQueries({ queryKey: teamKeys.detail(teamId) });
    },
    onError: (error, _userId, context) => {
      // Sprint 105: Handle 404 gracefully - member already deleted
      const errorStatus = error && typeof error === "object" && "status" in error
        ? (error as { status: number }).status
        : null;

      if (errorStatus === 404) {
        // Member already deleted - treat as success
        console.log("[useRemoveTeamMember] 404 = member already deleted, treating as success");
        // Still invalidate to sync UI
        queryClient.invalidateQueries({ queryKey: teamKeys.members(teamId) });
        queryClient.invalidateQueries({ queryKey: teamKeys.stats(teamId) });
        queryClient.invalidateQueries({ queryKey: teamKeys.detail(teamId) });
        return; // Don't rollback on 404
      }

      // For real errors: Rollback optimistic update
      console.log("[useRemoveMember] onError - rolling back:", error);

      // Restore previous data
      if (context?.previousMembers) {
        queryClient.setQueryData(
          teamKeys.membersList(teamId, undefined),
          context.previousMembers
        );
      }
      if (context?.previousTeam) {
        queryClient.setQueryData(teamKeys.detail(teamId), context.previousTeam);
      }

      // Also invalidate to sync with backend state
      queryClient.invalidateQueries({ queryKey: teamKeys.members(teamId) });
      queryClient.invalidateQueries({ queryKey: teamKeys.stats(teamId) });
      queryClient.invalidateQueries({ queryKey: teamKeys.detail(teamId) });
    },
  });
}

// =============================================================================
// Cache Invalidation Utilities
// =============================================================================

/**
 * Hook to invalidate all teams cache
 */
export function useInvalidateTeams() {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: teamKeys.all });
  };
}

/**
 * Hook to invalidate specific team cache
 */
export function useInvalidateTeam(teamId: string) {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: teamKeys.detail(teamId) });
    queryClient.invalidateQueries({ queryKey: teamKeys.stats(teamId) });
    queryClient.invalidateQueries({ queryKey: teamKeys.members(teamId) });
  };
}

// =============================================================================
// Prefetch Utilities
// =============================================================================

/**
 * Prefetch team data for navigation optimization
 */
export function usePrefetchTeam() {
  const queryClient = useQueryClient();

  return (teamId: string) => {
    queryClient.prefetchQuery({
      queryKey: teamKeys.detail(teamId),
      queryFn: () => getTeam(teamId),
      staleTime: 60 * 1000,
    });
  };
}

/**
 * Prefetch team members for navigation optimization
 */
export function usePrefetchTeamMembers() {
  const queryClient = useQueryClient();

  return (teamId: string) => {
    queryClient.prefetchQuery({
      queryKey: teamKeys.membersList(teamId),
      queryFn: () => getTeamMembers(teamId),
      staleTime: 60 * 1000,
    });
  };
}

// =============================================================================
// Type Exports
// =============================================================================

export type {
  Team,
  TeamCreate,
  TeamUpdate,
  TeamListResponse,
  TeamListParams,
  TeamStatistics,
  TeamMember,
  TeamMemberListResponse,
  TeamMemberListParams,
  TeamMemberAdd,
  TeamMemberRoleUpdate,
};
