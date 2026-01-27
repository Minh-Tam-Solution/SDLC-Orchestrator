/**
 * Planning Review Hooks - SDLC Orchestrator
 *
 * @module frontend/src/hooks/usePlanningReview
 * @description TanStack Query hooks for Planning Sub-agent (ADR-034)
 * @sdlc SDLC 5.2.0 Framework - Sprint 99 (Planning Sub-agent Part 2)
 * @status Sprint 99 - Core Feature Implementation
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createPlanningSession,
  getPlanningSession,
  approvePlanningSession,
  checkConformance,
  listPlanningSessions,
  getPlanningSubagentHealth,
} from "@/lib/api";
import type {
  PlanningRequest,
  ConformanceCheckRequest,
  PlanningResult,
  PlanningStatus,
} from "@/lib/types/planning-subagent";

// =============================================================================
// QUERY KEYS
// =============================================================================

export const planningSubagentKeys = {
  all: ["planning-subagent"] as const,
  // Sessions
  sessions: () => [...planningSubagentKeys.all, "sessions"] as const,
  sessionsList: (params?: { status?: PlanningStatus; limit?: number }) =>
    [...planningSubagentKeys.sessions(), "list", params] as const,
  sessionDetail: (id: string) =>
    [...planningSubagentKeys.sessions(), "detail", id] as const,
  // Conformance
  conformance: () => [...planningSubagentKeys.all, "conformance"] as const,
  // Health
  health: () => [...planningSubagentKeys.all, "health"] as const,
};

// =============================================================================
// SESSION HOOKS
// =============================================================================

/**
 * Fetch a single planning session by ID
 */
export function usePlanningSession(sessionId: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: planningSubagentKeys.sessionDetail(sessionId),
    queryFn: () => getPlanningSession(sessionId),
    enabled: options?.enabled !== false && !!sessionId,
    staleTime: 1 * 60 * 1000, // 1 minute
  });
}

/**
 * List planning sessions with optional filters
 */
export function usePlanningSessions(params?: {
  status?: PlanningStatus;
  limit?: number;
}) {
  return useQuery({
    queryKey: planningSubagentKeys.sessionsList(params),
    queryFn: () => listPlanningSessions(params),
    staleTime: 30 * 1000, // 30 seconds - sessions can change quickly
  });
}

/**
 * Create a new planning session
 */
export function useCreatePlanningSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: PlanningRequest) => createPlanningSession(request),
    onSuccess: (result) => {
      // Add to cache
      queryClient.setQueryData(
        planningSubagentKeys.sessionDetail(result.id),
        result
      );
      // Invalidate sessions list
      queryClient.invalidateQueries({
        queryKey: planningSubagentKeys.sessions(),
      });
    },
  });
}

/**
 * Approve a planning session
 */
export function useApprovePlanningSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      sessionId,
      notes,
    }: {
      sessionId: string;
      notes?: string;
    }) =>
      approvePlanningSession(sessionId, {
        approved: true,
        notes,
      }),
    onSuccess: (result, { sessionId }) => {
      // Update cache
      queryClient.setQueryData(
        planningSubagentKeys.sessionDetail(sessionId),
        result
      );
      // Invalidate sessions list
      queryClient.invalidateQueries({
        queryKey: planningSubagentKeys.sessions(),
      });
    },
  });
}

/**
 * Reject a planning session
 */
export function useRejectPlanningSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      sessionId,
      notes,
    }: {
      sessionId: string;
      notes: string;
    }) =>
      approvePlanningSession(sessionId, {
        approved: false,
        notes,
      }),
    onSuccess: (result, { sessionId }) => {
      // Update cache
      queryClient.setQueryData(
        planningSubagentKeys.sessionDetail(sessionId),
        result
      );
      // Invalidate sessions list
      queryClient.invalidateQueries({
        queryKey: planningSubagentKeys.sessions(),
      });
    },
  });
}

// =============================================================================
// CONFORMANCE HOOKS
// =============================================================================

/**
 * Check conformance of a diff against established patterns
 */
export function useCheckConformance() {
  return useMutation({
    mutationFn: (request: ConformanceCheckRequest) => checkConformance(request),
  });
}

// =============================================================================
// HEALTH HOOKS
// =============================================================================

/**
 * Check planning sub-agent service health
 */
export function usePlanningSubagentHealth() {
  return useQuery({
    queryKey: planningSubagentKeys.health(),
    queryFn: getPlanningSubagentHealth,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Auto-refresh every minute
  });
}

// =============================================================================
// COMBINED HOOKS
// =============================================================================

/**
 * Combined hook for plan review workflow
 */
export function usePlanReview(sessionId: string) {
  const session = usePlanningSession(sessionId);
  const approveMutation = useApprovePlanningSession();
  const rejectMutation = useRejectPlanningSession();

  return {
    // Data
    plan: session.data,
    patterns: session.data?.patterns,
    implementationPlan: session.data?.plan,
    conformance: session.data?.conformance,

    // Status
    status: session.data?.status,
    requiresApproval: session.data?.requires_approval ?? false,
    isApproved: session.data?.status === "approved",
    isRejected: session.data?.status === "rejected",
    isPending: session.data?.status === "pending_approval",

    // Loading states
    isLoading: session.isLoading,
    isApproving: approveMutation.isPending,
    isRejecting: rejectMutation.isPending,

    // Errors
    error: session.error || approveMutation.error || rejectMutation.error,

    // Actions
    approve: (notes?: string) =>
      approveMutation.mutateAsync({ sessionId, notes }),
    reject: (notes: string) =>
      rejectMutation.mutateAsync({ sessionId, notes }),
    refetch: session.refetch,
  };
}

/**
 * Combined hook for conformance checking workflow
 */
export function useConformanceCheck() {
  const checkMutation = useCheckConformance();

  return {
    // Data
    result: checkMutation.data,
    score: checkMutation.data?.score ?? 0,
    level: checkMutation.data?.level,
    deviations: checkMutation.data?.deviations ?? [],
    recommendations: checkMutation.data?.recommendations ?? [],

    // Status
    isLoading: checkMutation.isPending,
    isSuccess: checkMutation.isSuccess,
    isError: checkMutation.isError,

    // Computed
    passed: (checkMutation.data?.score ?? 0) >= 70,
    hasDeviations: (checkMutation.data?.deviations?.length ?? 0) > 0,
    requiresADR: checkMutation.data?.requires_adr ?? false,

    // Errors
    error: checkMutation.error,

    // Actions
    check: checkMutation.mutateAsync,
    reset: checkMutation.reset,
  };
}

/**
 * Combined hook for planning session management
 */
export function usePlanningSessionManagement(params?: {
  status?: PlanningStatus;
  limit?: number;
}) {
  const sessions = usePlanningSessions(params);
  const createMutation = useCreatePlanningSession();
  const health = usePlanningSubagentHealth();

  return {
    // Data
    sessions: sessions.data?.sessions ?? [],
    total: sessions.data?.total ?? 0,

    // Service health
    isHealthy: health.data?.status === "healthy",
    serviceVersion: health.data?.version,

    // Loading states
    isLoading: sessions.isLoading,
    isCreating: createMutation.isPending,

    // Errors
    error: sessions.error || createMutation.error,

    // Actions
    create: createMutation.mutateAsync,
    refetch: sessions.refetch,

    // Filters
    filterByStatus: (status: PlanningStatus) =>
      sessions.data?.sessions.filter((s) => s.status === status) ?? [],
    getPendingApproval: () =>
      sessions.data?.sessions.filter((s) => s.status === "pending_approval") ??
      [],
  };
}

/**
 * Hook for polling a planning session until it reaches a terminal state
 */
export function usePlanningSessionPolling(
  sessionId: string,
  options?: {
    enabled?: boolean;
    intervalMs?: number;
    onComplete?: (result: PlanningResult) => void;
  }
) {
  const { enabled = true, intervalMs = 2000, onComplete } = options ?? {};

  return useQuery({
    queryKey: [...planningSubagentKeys.sessionDetail(sessionId), "polling"],
    queryFn: async () => {
      const result = await getPlanningSession(sessionId);

      // Call onComplete when session reaches a terminal state
      if (
        onComplete &&
        ["pending_approval", "approved", "rejected", "expired"].includes(
          result.status
        )
      ) {
        onComplete(result);
      }

      return result;
    },
    enabled: enabled && !!sessionId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      // Stop polling when session is complete
      if (
        status &&
        ["pending_approval", "approved", "rejected", "expired"].includes(status)
      ) {
        return false;
      }
      return intervalMs;
    },
    staleTime: 0, // Always fetch fresh data during polling
  });
}
