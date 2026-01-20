/**
 * Context Overlay TanStack Query Hooks - SDLC Orchestrator Dashboard
 *
 * @module frontend/src/hooks/useContextOverlay
 * @description React Query hooks for Dynamic Context Overlay API (TRUE MOAT)
 * @sdlc SDLC 5.1.3 Framework - Sprint 85 (AGENTS.md UI)
 * @status Sprint 85 - CTO APPROVED (January 20, 2026)
 * @see backend/app/api/routes/context_overlay.py
 */

import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getContextHistory,
  getContextOverlay,
  type ContextOverlay,
} from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

// =============================================================================
// Query Keys for Cache Management
// =============================================================================

export const contextOverlayKeys = {
  all: ["context-overlays"] as const,
  details: () => [...contextOverlayKeys.all, "detail"] as const,
  detail: (overlayId: string) => [...contextOverlayKeys.details(), overlayId] as const,
  history: () => [...contextOverlayKeys.all, "history"] as const,
  projectHistory: (projectId: string, params?: { page?: number; page_size?: number }) =>
    [...contextOverlayKeys.history(), projectId, params] as const,
};

// =============================================================================
// Context Overlay Query Hooks
// =============================================================================

/**
 * Hook to fetch context overlay detail by ID
 * Sprint 85: GET /context-overlays/{overlay_id}
 */
export function useContextOverlay(overlayId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: contextOverlayKeys.detail(overlayId || ""),
    queryFn: () => getContextOverlay(overlayId!),
    enabled: isAuthenticated && !authLoading && !!overlayId,
    staleTime: 30 * 1000, // 30 seconds
  });
}

/**
 * Hook to fetch context overlay history for a project
 * Sprint 85: GET /context-overlays/project/{project_id}/history
 */
export function useContextHistory(
  projectId: string | undefined,
  params?: { page?: number; page_size?: number }
) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: contextOverlayKeys.projectHistory(projectId || "", params),
    queryFn: () => getContextHistory(projectId!, params),
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 60 * 1000, // 1 minute
  });
}

// =============================================================================
// Prefetch Utilities
// =============================================================================

/**
 * Prefetch context overlay detail for faster navigation
 */
export function usePrefetchContextOverlay() {
  const queryClient = useQueryClient();

  return (overlayId: string) => {
    queryClient.prefetchQuery({
      queryKey: contextOverlayKeys.detail(overlayId),
      queryFn: () => getContextOverlay(overlayId),
      staleTime: 30 * 1000,
    });
  };
}

/**
 * Prefetch context history for a project
 */
export function usePrefetchContextHistory() {
  const queryClient = useQueryClient();

  return (projectId: string, params?: { page?: number; page_size?: number }) => {
    queryClient.prefetchQuery({
      queryKey: contextOverlayKeys.projectHistory(projectId, params),
      queryFn: () => getContextHistory(projectId, params),
      staleTime: 60 * 1000,
    });
  };
}

// =============================================================================
// Combined Hooks
// =============================================================================

/**
 * Hook to get context history with pagination
 */
export function useContextHistoryPaginated(
  projectId: string | undefined,
  initialPage: number = 1,
  pageSize: number = 10
) {
  const historyQuery = useContextHistory(projectId, {
    page: initialPage,
    page_size: pageSize,
  });

  return {
    history: historyQuery.data?.history || [],
    total: historyQuery.data?.total || 0,
    isLoading: historyQuery.isLoading,
    isError: historyQuery.isError,
    error: historyQuery.error,
    refetch: historyQuery.refetch,
    hasMore: (historyQuery.data?.history.length || 0) >= pageSize,
  };
}

/**
 * Hook to get latest context overlay from history
 */
export function useLatestContextOverlay(projectId: string | undefined) {
  const { history, isLoading, error } = useContextHistoryPaginated(projectId, 1, 1);

  return {
    latestOverlay: history[0],
    isLoading,
    error,
  };
}

// =============================================================================
// Context Analysis Utilities
// =============================================================================

/**
 * Hook to analyze context overlay for UI display
 */
export function useContextAnalysis(context: ContextOverlay | undefined) {
  if (!context) {
    return {
      hasConstraints: false,
      criticalConstraints: [],
      highConstraints: [],
      mediumConstraints: [],
      lowConstraints: [],
      isStrictMode: false,
      hasKnownIssues: false,
      hasPendingTasks: false,
      sprintInfo: null,
      gateInfo: null,
    };
  }

  const criticalConstraints = context.constraints.filter((c) => c.severity === "critical");
  const highConstraints = context.constraints.filter((c) => c.severity === "high");
  const mediumConstraints = context.constraints.filter((c) => c.severity === "medium");
  const lowConstraints = context.constraints.filter((c) => c.severity === "low");

  return {
    hasConstraints: context.constraints.length > 0,
    criticalConstraints,
    highConstraints,
    mediumConstraints,
    lowConstraints,
    isStrictMode: context.strict_mode,
    hasKnownIssues: (context.known_issues?.length || 0) > 0,
    hasPendingTasks: (context.pending_tasks?.length || 0) > 0,
    sprintInfo: context.sprint || null,
    gateInfo: context.gate_name && context.gate_status
      ? { name: context.gate_name, status: context.gate_status }
      : null,
  };
}

/**
 * Get context severity level for styling (non-hook utility function)
 */
export function getContextSeverityLevel(context: ContextOverlay | undefined): string {
  if (!context) return "none";

  const criticalConstraints = context.constraints.filter((c) => c.severity === "critical");
  const highConstraints = context.constraints.filter((c) => c.severity === "high");

  if (criticalConstraints.length > 0) return "critical";
  if (highConstraints.length > 0) return "high";
  if (context.strict_mode) return "strict";
  return "normal";
}
