/**
 * GitHub Checks Hook - SDLC Orchestrator
 *
 * @module frontend/src/hooks/useGitHubChecks
 * @description TanStack Query hooks for GitHub Check Run management (P0 Blocker)
 * @sdlc SDLC 5.1.3 Framework - Sprint 86 (GitHub Check Run UI)
 * @status Sprint 86 - CTO APPROVED (January 20, 2026)
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getCheckRuns,
  getCheckRun,
  getCheckRunStats,
  createCheckRun,
  rerunCheckRun,
  getProjectCheckRunConfig,
  updateProjectCheckRunConfig,
} from "@/lib/api";
import type {
  CheckRun,
  CheckRunListItem,
  CheckRunDetail,
  CheckRunListParams,
  CheckRunsResponse,
  CreateCheckRunRequest,
  RerunCheckRunRequest,
  CheckRunStats,
  ProjectCheckRunConfig,
  UpdateCheckRunConfigRequest,
} from "@/lib/types/github-checks";

// =============================================================================
// Query Keys
// =============================================================================

export const checkRunKeys = {
  all: ["check-runs"] as const,
  lists: () => [...checkRunKeys.all, "list"] as const,
  list: (params?: CheckRunListParams) => [...checkRunKeys.lists(), params] as const,
  details: () => [...checkRunKeys.all, "detail"] as const,
  detail: (id: string) => [...checkRunKeys.details(), id] as const,
  stats: () => [...checkRunKeys.all, "stats"] as const,
  statsWithParams: (params?: { project_id?: string; period_days?: number }) =>
    [...checkRunKeys.stats(), params] as const,
  configs: () => [...checkRunKeys.all, "config"] as const,
  config: (projectId: string) => [...checkRunKeys.configs(), projectId] as const,
};

// =============================================================================
// Query Hooks
// =============================================================================

/**
 * Fetch list of Check Runs
 */
export function useCheckRuns(params?: CheckRunListParams) {
  return useQuery({
    queryKey: checkRunKeys.list(params),
    queryFn: () => getCheckRuns(params),
    staleTime: 30 * 1000, // 30 seconds
  });
}

/**
 * Fetch single Check Run detail
 */
export function useCheckRun(checkRunId: string) {
  return useQuery({
    queryKey: checkRunKeys.detail(checkRunId),
    queryFn: () => getCheckRun(checkRunId),
    enabled: !!checkRunId,
  });
}

/**
 * Fetch Check Run statistics
 */
export function useCheckRunStats(options?: {
  project_id?: string;
  period_days?: number;
}) {
  return useQuery({
    queryKey: checkRunKeys.statsWithParams(options),
    queryFn: () => getCheckRunStats(options),
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Fetch project Check Run configuration
 */
export function useProjectCheckRunConfig(projectId: string) {
  return useQuery({
    queryKey: checkRunKeys.config(projectId),
    queryFn: () => getProjectCheckRunConfig(projectId),
    enabled: !!projectId,
  });
}

// =============================================================================
// Mutation Hooks
// =============================================================================

/**
 * Create a new Check Run
 */
export function useCreateCheckRun() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateCheckRunRequest) => createCheckRun(data),
    onSuccess: () => {
      // Invalidate check run list and stats
      queryClient.invalidateQueries({ queryKey: checkRunKeys.lists() });
      queryClient.invalidateQueries({ queryKey: checkRunKeys.stats() });
    },
  });
}

/**
 * Re-run a Check Run
 */
export function useRerunCheckRun() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: RerunCheckRunRequest) => rerunCheckRun(data),
    onSuccess: (_, variables) => {
      // Invalidate specific check run and lists
      queryClient.invalidateQueries({
        queryKey: checkRunKeys.detail(variables.check_run_id),
      });
      queryClient.invalidateQueries({ queryKey: checkRunKeys.lists() });
      queryClient.invalidateQueries({ queryKey: checkRunKeys.stats() });
    },
  });
}

/**
 * Update project Check Run configuration
 */
export function useUpdateProjectCheckRunConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      projectId,
      data,
    }: {
      projectId: string;
      data: UpdateCheckRunConfigRequest;
    }) => updateProjectCheckRunConfig(projectId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: checkRunKeys.config(variables.projectId),
      });
    },
  });
}

// =============================================================================
// Combined Hooks
// =============================================================================

/**
 * Combined hook for Check Runs dashboard
 * Returns check runs, stats, and actions in a single hook
 */
export function useCheckRunsDashboard(params?: CheckRunListParams) {
  const checkRunsQuery = useCheckRuns(params);
  const statsQuery = useCheckRunStats({
    project_id: params?.project_id,
  });

  return {
    // Check Runs
    checkRuns: checkRunsQuery.data?.items ?? [],
    totalCheckRuns: checkRunsQuery.data?.total ?? 0,
    hasMore: checkRunsQuery.data?.has_more ?? false,

    // Stats
    stats: statsQuery.data,

    // Loading states
    isLoading: checkRunsQuery.isLoading || statsQuery.isLoading,
    isLoadingCheckRuns: checkRunsQuery.isLoading,
    isLoadingStats: statsQuery.isLoading,

    // Error states
    error: checkRunsQuery.error || statsQuery.error,

    // Refetch functions
    refetchCheckRuns: checkRunsQuery.refetch,
    refetchStats: statsQuery.refetch,
    refetchAll: () => {
      checkRunsQuery.refetch();
      statsQuery.refetch();
    },
  };
}

/**
 * Hook for Check Run detail page
 */
export function useCheckRunDetail(checkRunId: string) {
  const checkRunQuery = useCheckRun(checkRunId);
  const rerunMutation = useRerunCheckRun();

  return {
    checkRun: checkRunQuery.data,
    isLoading: checkRunQuery.isLoading,
    error: checkRunQuery.error,
    refetch: checkRunQuery.refetch,

    // Actions
    rerun: (force?: boolean) =>
      rerunMutation.mutateAsync({ check_run_id: checkRunId, force }),

    // Action states
    isRerunning: rerunMutation.isPending,
  };
}

/**
 * Hook for project Check Run settings
 */
export function useProjectCheckRunSettings(projectId: string) {
  const configQuery = useProjectCheckRunConfig(projectId);
  const updateConfigMutation = useUpdateProjectCheckRunConfig();

  return {
    config: configQuery.data,
    isLoading: configQuery.isLoading,
    error: configQuery.error,
    refetch: configQuery.refetch,

    // Actions
    updateConfig: (data: UpdateCheckRunConfigRequest) =>
      updateConfigMutation.mutateAsync({ projectId, data }),

    // Action states
    isUpdating: updateConfigMutation.isPending,
  };
}

// =============================================================================
// Utility Hooks
// =============================================================================

/**
 * Hook to get recent Check Runs count
 */
export function useRecentCheckRunsCount(periodDays: number = 7) {
  const { data: stats } = useCheckRunStats({ period_days: periodDays });
  return stats?.total_runs ?? 0;
}

/**
 * Hook to check if Check Runs feature is enabled for a project
 */
export function useCheckRunsEnabled(projectId: string) {
  const { data: config, isLoading } = useProjectCheckRunConfig(projectId);
  return {
    enabled: config?.auto_create_on_pr ?? false,
    mode: config?.mode ?? "advisory",
    isLoading,
  };
}

// =============================================================================
// Prefetch Functions
// =============================================================================

/**
 * Prefetch Check Runs for page navigation
 */
export function usePrefetchCheckRuns() {
  const queryClient = useQueryClient();

  return (params?: CheckRunListParams) => {
    queryClient.prefetchQuery({
      queryKey: checkRunKeys.list(params),
      queryFn: () => getCheckRuns(params),
      staleTime: 30 * 1000,
    });
  };
}

/**
 * Prefetch Check Run detail
 */
export function usePrefetchCheckRun() {
  const queryClient = useQueryClient();

  return (checkRunId: string) => {
    queryClient.prefetchQuery({
      queryKey: checkRunKeys.detail(checkRunId),
      queryFn: () => getCheckRun(checkRunId),
      staleTime: 30 * 1000,
    });
  };
}

// =============================================================================
// Type Exports
// =============================================================================

export type {
  CheckRun,
  CheckRunListItem,
  CheckRunDetail,
  CheckRunListParams,
  CheckRunsResponse,
  CreateCheckRunRequest,
  RerunCheckRunRequest,
  CheckRunStats,
  ProjectCheckRunConfig,
  UpdateCheckRunConfigRequest,
};
