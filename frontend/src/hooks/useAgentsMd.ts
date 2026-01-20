/**
 * AGENTS.md TanStack Query Hooks - SDLC Orchestrator Dashboard
 *
 * @module frontend/src/hooks/useAgentsMd
 * @description React Query hooks for AGENTS.md API (TRUE MOAT)
 * @sdlc SDLC 5.1.3 Framework - Sprint 85 (AGENTS.md UI)
 * @status Sprint 85 - CTO APPROVED (January 20, 2026)
 * @see backend/app/api/routes/agents_md.py (13 endpoints)
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getAgentsMdRepos,
  getAgentsMdRepo,
  regenerateAgentsMd,
  bulkRegenerateAgentsMd,
  getAgentsMdDiff,
  validateAgentsMd,
  getAgentsMdContext,
  type AgentsMdListParams,
  type AgentsMdRepoDetail,
  type RegenerateRequest,
  type BulkRegenerateRequest,
  type ValidateRequest,
} from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

// =============================================================================
// Query Keys for Cache Management
// =============================================================================

export const agentsMdKeys = {
  all: ["agents-md"] as const,
  lists: () => [...agentsMdKeys.all, "list"] as const,
  list: (params?: AgentsMdListParams) => [...agentsMdKeys.lists(), params] as const,
  details: () => [...agentsMdKeys.all, "detail"] as const,
  detail: (repoId: string) => [...agentsMdKeys.details(), repoId] as const,
  context: (repoId: string) => [...agentsMdKeys.detail(repoId), "context"] as const,
  diff: (repoId: string, from?: string, to?: string) =>
    [...agentsMdKeys.detail(repoId), "diff", from, to] as const,
  validation: () => [...agentsMdKeys.all, "validation"] as const,
};

// =============================================================================
// AGENTS.md Repository Query Hooks
// =============================================================================

/**
 * Hook to fetch list of repositories with AGENTS.md status
 * Sprint 85: GET /agents-md/repos - Paginated list with optional filters
 */
export function useAgentsMdRepos(params?: AgentsMdListParams) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: agentsMdKeys.list(params),
    queryFn: () => getAgentsMdRepos(params),
    enabled: isAuthenticated && !authLoading,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Hook to fetch a single AGENTS.md repository detail
 * Sprint 85: GET /agents-md/{repo_id}
 */
export function useAgentsMdRepo(repoId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: agentsMdKeys.detail(repoId || ""),
    queryFn: () => getAgentsMdRepo(repoId!),
    enabled: isAuthenticated && !authLoading && !!repoId,
    staleTime: 30 * 1000, // 30 seconds (content may change frequently)
  });
}

/**
 * Hook to fetch dynamic context overlay for a repository
 * Sprint 85: GET /agents-md/{repo_id}/context
 */
export function useAgentsMdContext(repoId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: agentsMdKeys.context(repoId || ""),
    queryFn: () => getAgentsMdContext(repoId!),
    enabled: isAuthenticated && !authLoading && !!repoId,
    staleTime: 30 * 1000, // 30 seconds (context updates frequently)
    refetchInterval: 60 * 1000, // Auto-refresh every minute
  });
}

/**
 * Hook to fetch diff between AGENTS.md versions
 * Sprint 85: GET /agents-md/{repo_id}/diff
 */
export function useAgentsMdDiff(
  repoId: string | undefined,
  options?: { from_version?: string; to_version?: string }
) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: agentsMdKeys.diff(repoId || "", options?.from_version, options?.to_version),
    queryFn: () => getAgentsMdDiff(repoId!, options),
    enabled: isAuthenticated && !authLoading && !!repoId,
    staleTime: 5 * 60 * 1000, // 5 minutes (diff is relatively static)
  });
}

// =============================================================================
// AGENTS.md Mutation Hooks
// =============================================================================

/**
 * Hook to regenerate AGENTS.md file for a repository
 * Sprint 85: POST /agents-md/{repo_id}/regenerate
 */
export function useRegenerateAgentsMd() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      repoId,
      data,
    }: {
      repoId: string;
      data?: RegenerateRequest;
    }) => regenerateAgentsMd(repoId, data),
    onSuccess: (_, variables) => {
      // Invalidate repo detail
      queryClient.invalidateQueries({
        queryKey: agentsMdKeys.detail(variables.repoId),
      });
      // Invalidate list to refresh status
      queryClient.invalidateQueries({
        queryKey: agentsMdKeys.lists(),
      });
    },
  });
}

/**
 * Hook to bulk regenerate AGENTS.md files for multiple repositories
 * Sprint 85: POST /agents-md/bulk/regenerate
 */
export function useBulkRegenerateAgentsMd() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BulkRegenerateRequest) => bulkRegenerateAgentsMd(data),
    onSuccess: (result, variables) => {
      // Invalidate all affected repos
      variables.repo_ids.forEach((repoId) => {
        queryClient.invalidateQueries({
          queryKey: agentsMdKeys.detail(repoId),
        });
      });
      // Invalidate list to refresh statuses
      queryClient.invalidateQueries({
        queryKey: agentsMdKeys.lists(),
      });
    },
  });
}

/**
 * Hook to validate AGENTS.md content
 * Sprint 85: POST /agents-md/validate
 */
export function useValidateAgentsMd() {
  return useMutation({
    mutationFn: (data: ValidateRequest) => validateAgentsMd(data),
  });
}

// =============================================================================
// Prefetch Utilities
// =============================================================================

/**
 * Prefetch AGENTS.md repo detail for faster navigation
 */
export function usePrefetchAgentsMdRepo() {
  const queryClient = useQueryClient();

  return (repoId: string) => {
    queryClient.prefetchQuery({
      queryKey: agentsMdKeys.detail(repoId),
      queryFn: () => getAgentsMdRepo(repoId),
      staleTime: 30 * 1000,
    });
  };
}

/**
 * Prefetch context overlay for a repo
 */
export function usePrefetchAgentsMdContext() {
  const queryClient = useQueryClient();

  return (repoId: string) => {
    queryClient.prefetchQuery({
      queryKey: agentsMdKeys.context(repoId),
      queryFn: () => getAgentsMdContext(repoId),
      staleTime: 30 * 1000,
    });
  };
}

// =============================================================================
// Combined Hooks for Common Patterns
// =============================================================================

/**
 * Hook to get repo detail with context in a single call
 * Useful for the detail page
 */
export function useAgentsMdRepoWithContext(repoId: string | undefined) {
  const repoQuery = useAgentsMdRepo(repoId);
  const contextQuery = useAgentsMdContext(repoId);

  return {
    repo: repoQuery.data,
    context: contextQuery.data,
    isLoading: repoQuery.isLoading || contextQuery.isLoading,
    isError: repoQuery.isError || contextQuery.isError,
    error: repoQuery.error || contextQuery.error,
    refetch: async () => {
      await Promise.all([repoQuery.refetch(), contextQuery.refetch()]);
    },
  };
}

/**
 * Hook to get repos filtered by status
 */
export function useAgentsMdReposByStatus(status: "valid" | "invalid" | "outdated" | "missing") {
  return useAgentsMdRepos({ status });
}

/**
 * Hook to get only outdated repos (for bulk regenerate suggestion)
 */
export function useOutdatedAgentsMdRepos() {
  const { data, ...rest } = useAgentsMdRepos();

  const outdatedRepos = data?.repos.filter((repo) => repo.is_outdated) || [];

  return {
    ...rest,
    data: outdatedRepos,
    outdatedCount: outdatedRepos.length,
  };
}

// =============================================================================
// Optimistic Update Utilities
// =============================================================================

/**
 * Hook for optimistic regeneration with rollback support
 */
export function useOptimisticRegenerate() {
  const queryClient = useQueryClient();
  const mutation = useRegenerateAgentsMd();

  return {
    ...mutation,
    regenerateWithOptimisticUpdate: async (repoId: string, data?: RegenerateRequest) => {
      // Get current data for rollback
      const previousData = queryClient.getQueryData<AgentsMdRepoDetail>(
        agentsMdKeys.detail(repoId)
      );

      // Optimistically update the repo status
      if (previousData) {
        queryClient.setQueryData<AgentsMdRepoDetail>(agentsMdKeys.detail(repoId), {
          ...previousData,
          repo: {
            ...previousData.repo,
            is_outdated: false,
            validation_status: "pending",
          },
        });
      }

      try {
        const result = await mutation.mutateAsync({ repoId, data });
        return result;
      } catch (error) {
        // Rollback on error
        if (previousData) {
          queryClient.setQueryData(agentsMdKeys.detail(repoId), previousData);
        }
        throw error;
      }
    },
  };
}

// =============================================================================
// Dashboard Stats Hook
// =============================================================================

/**
 * Hook to calculate dashboard stats from repos list
 */
export function useAgentsMdDashboardStats() {
  const { data, isLoading, error } = useAgentsMdRepos();

  const stats = {
    totalRepos: data?.total || 0,
    upToDate: 0,
    outdated: 0,
    missing: 0,
    invalid: 0,
    validRate: 0,
  };

  if (data?.repos) {
    stats.upToDate = data.repos.filter(
      (r) => r.has_agents_md && !r.is_outdated && r.validation_status === "valid"
    ).length;
    stats.outdated = data.repos.filter((r) => r.has_agents_md && r.is_outdated).length;
    stats.missing = data.repos.filter((r) => !r.has_agents_md).length;
    stats.invalid = data.repos.filter((r) => r.validation_status === "invalid").length;
    stats.validRate = stats.totalRepos > 0
      ? (stats.upToDate / stats.totalRepos) * 100
      : 0;
  }

  return {
    stats,
    isLoading,
    error,
    repos: data?.repos || [],
  };
}
