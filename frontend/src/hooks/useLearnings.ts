/**
 * Feedback Learning TanStack Query Hooks - SDLC Orchestrator Dashboard
 *
 * @module frontend/src/hooks/useLearnings
 * @description React Query hooks for EP-11 Feedback Learning API
 * @sdlc SDLC 5.1.3 Framework - Sprint 100 (Feedback Learning Service)
 * @status Sprint 100 - EP-11 Implementation
 * @see backend/app/api/routes/learnings.py
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getLearnings,
  getLearning,
  createLearning,
  updateLearning,
  deleteLearning,
  getLearningStats,
  applyLearning,
  getHints,
  getHint,
  createHint,
  updateHint,
  verifyHint,
  recordHintUsage,
  provideHintFeedback,
  getActiveHints,
  getAggregations,
  getAggregation,
  createAggregation,
  applyAggregation,
  rejectAggregation,
  type LearningFilterParams,
  type HintFilterParams,
  type CreateLearningRequest,
  type UpdateLearningRequest,
  type CreateHintRequest,
  type UpdateHintRequest,
  type CreateAggregationRequest,
  type AggregationPeriod,
  type PRLearning,
  type DecompositionHint,
  type LearningAggregation,
} from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

// =============================================================================
// Query Keys for Cache Management
// =============================================================================

export const learningsKeys = {
  all: ["learnings"] as const,

  // Learnings
  lists: () => [...learningsKeys.all, "list"] as const,
  list: (projectId: string, params?: LearningFilterParams) =>
    [...learningsKeys.lists(), projectId, params] as const,
  details: () => [...learningsKeys.all, "detail"] as const,
  detail: (projectId: string, learningId: string) =>
    [...learningsKeys.details(), projectId, learningId] as const,
  stats: (projectId: string) => [...learningsKeys.all, "stats", projectId] as const,

  // Hints
  hints: () => [...learningsKeys.all, "hints"] as const,
  hintLists: () => [...learningsKeys.hints(), "list"] as const,
  hintList: (projectId: string, params?: HintFilterParams) =>
    [...learningsKeys.hintLists(), projectId, params] as const,
  hintDetails: () => [...learningsKeys.hints(), "detail"] as const,
  hintDetail: (projectId: string, hintId: string) =>
    [...learningsKeys.hintDetails(), projectId, hintId] as const,
  activeHints: (projectId: string, context?: Record<string, unknown>) =>
    [...learningsKeys.hints(), "active", projectId, context] as const,

  // Aggregations
  aggregations: () => [...learningsKeys.all, "aggregations"] as const,
  aggregationLists: () => [...learningsKeys.aggregations(), "list"] as const,
  aggregationList: (projectId: string, params?: Record<string, unknown>) =>
    [...learningsKeys.aggregationLists(), projectId, params] as const,
  aggregationDetails: () => [...learningsKeys.aggregations(), "detail"] as const,
  aggregationDetail: (projectId: string, aggregationId: string) =>
    [...learningsKeys.aggregationDetails(), projectId, aggregationId] as const,
};

// =============================================================================
// Learnings Query Hooks
// =============================================================================

/**
 * Hook to fetch learnings for a project with filtering
 * Sprint 100: GET /projects/{project_id}/learnings
 */
export function useLearnings(
  projectId: string | undefined,
  params?: LearningFilterParams
) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: learningsKeys.list(projectId || "", params),
    queryFn: () => getLearnings(projectId!, params),
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Hook to fetch a single learning by ID
 * Sprint 100: GET /projects/{project_id}/learnings/{learning_id}
 */
export function useLearning(
  projectId: string | undefined,
  learningId: string | undefined
) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: learningsKeys.detail(projectId || "", learningId || ""),
    queryFn: () => getLearning(projectId!, learningId!),
    enabled: isAuthenticated && !authLoading && !!projectId && !!learningId,
    staleTime: 30 * 1000, // 30 seconds
  });
}

/**
 * Hook to fetch learning statistics for a project
 * Sprint 100: GET /projects/{project_id}/learnings/stats
 */
export function useLearningStats(projectId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: learningsKeys.stats(projectId || ""),
    queryFn: () => getLearningStats(projectId!),
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 5 * 60 * 1000, // 5 minutes (stats don't change often)
  });
}

// =============================================================================
// Learnings Mutation Hooks
// =============================================================================

/**
 * Hook to create a manual learning
 * Sprint 100: POST /projects/{project_id}/learnings
 */
export function useCreateLearning(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateLearningRequest) => createLearning(projectId, data),
    onSuccess: () => {
      // Invalidate learnings list and stats
      queryClient.invalidateQueries({ queryKey: learningsKeys.lists() });
      queryClient.invalidateQueries({ queryKey: learningsKeys.stats(projectId) });
    },
  });
}

/**
 * Hook to update a learning
 * Sprint 100: PATCH /projects/{project_id}/learnings/{learning_id}
 */
export function useUpdateLearning(projectId: string, learningId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UpdateLearningRequest) =>
      updateLearning(projectId, learningId, data),
    onSuccess: (updatedLearning) => {
      // Update cache with new data
      queryClient.setQueryData(
        learningsKeys.detail(projectId, learningId),
        updatedLearning
      );
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: learningsKeys.lists() });
    },
  });
}

/**
 * Hook to delete a learning
 * Sprint 100: DELETE /projects/{project_id}/learnings/{learning_id}
 */
export function useDeleteLearning(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (learningId: string) => deleteLearning(projectId, learningId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: learningsKeys.lists() });
      queryClient.invalidateQueries({ queryKey: learningsKeys.stats(projectId) });
    },
  });
}

/**
 * Hook to apply a learning to CLAUDE.md or decomposition
 * Sprint 100: POST /projects/{project_id}/learnings/{learning_id}/apply
 */
export function useApplyLearning(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      learningId,
      target,
    }: {
      learningId: string;
      target: "claude_md" | "decomposition" | "both";
    }) => applyLearning(projectId, learningId, target),
    onSuccess: (updatedLearning, { learningId }) => {
      queryClient.setQueryData(
        learningsKeys.detail(projectId, learningId),
        updatedLearning
      );
      queryClient.invalidateQueries({ queryKey: learningsKeys.lists() });
      queryClient.invalidateQueries({ queryKey: learningsKeys.stats(projectId) });
    },
  });
}

// =============================================================================
// Hints Query Hooks
// =============================================================================

/**
 * Hook to fetch decomposition hints for a project
 * Sprint 100: GET /projects/{project_id}/hints
 */
export function useHints(projectId: string | undefined, params?: HintFilterParams) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: learningsKeys.hintList(projectId || "", params),
    queryFn: () => getHints(projectId!, params),
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Hook to fetch a single hint by ID
 * Sprint 100: GET /projects/{project_id}/hints/{hint_id}
 */
export function useHint(projectId: string | undefined, hintId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: learningsKeys.hintDetail(projectId || "", hintId || ""),
    queryFn: () => getHint(projectId!, hintId!),
    enabled: isAuthenticated && !authLoading && !!projectId && !!hintId,
    staleTime: 30 * 1000, // 30 seconds
  });
}

/**
 * Hook to fetch active hints for decomposition
 * Sprint 100: GET /projects/{project_id}/hints/active
 */
export function useActiveHints(
  projectId: string | undefined,
  context?: {
    applies_to?: string[];
    languages?: string[];
    frameworks?: string[];
    min_confidence?: number;
  }
) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: learningsKeys.activeHints(projectId || "", context),
    queryFn: () => getActiveHints(projectId!, context),
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes (hints may be updated)
  });
}

// =============================================================================
// Hints Mutation Hooks
// =============================================================================

/**
 * Hook to create a new hint
 * Sprint 100: POST /projects/{project_id}/hints
 */
export function useCreateHint(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateHintRequest) => createHint(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: learningsKeys.hintLists() });
      queryClient.invalidateQueries({
        queryKey: learningsKeys.activeHints(projectId, undefined),
      });
    },
  });
}

/**
 * Hook to update a hint
 * Sprint 100: PATCH /projects/{project_id}/hints/{hint_id}
 */
export function useUpdateHint(projectId: string, hintId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UpdateHintRequest) => updateHint(projectId, hintId, data),
    onSuccess: (updatedHint) => {
      queryClient.setQueryData(
        learningsKeys.hintDetail(projectId, hintId),
        updatedHint
      );
      queryClient.invalidateQueries({ queryKey: learningsKeys.hintLists() });
    },
  });
}

/**
 * Hook to verify a hint (human review)
 * Sprint 100: POST /projects/{project_id}/hints/{hint_id}/verify
 */
export function useVerifyHint(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (hintId: string) => verifyHint(projectId, hintId),
    onSuccess: (updatedHint, hintId) => {
      queryClient.setQueryData(
        learningsKeys.hintDetail(projectId, hintId),
        updatedHint
      );
      queryClient.invalidateQueries({ queryKey: learningsKeys.hintLists() });
    },
  });
}

/**
 * Hook to record hint usage during decomposition
 * Sprint 100: POST /projects/{project_id}/hints/{hint_id}/usage
 */
export function useRecordHintUsage(projectId: string) {
  return useMutation({
    mutationFn: ({
      hintId,
      data,
    }: {
      hintId: string;
      data: {
        decomposition_session_id?: string;
        task_description?: string;
        plan_generated?: string;
      };
    }) => recordHintUsage(projectId, hintId, data),
  });
}

/**
 * Hook to provide feedback on hint usage
 * Sprint 100: POST /projects/{project_id}/hints/{hint_id}/feedback
 */
export function useProvideHintFeedback(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      hintId,
      data,
    }: {
      hintId: string;
      data: {
        usage_id: string;
        outcome: "prevented_error" | "no_effect" | "false_positive";
        feedback?: string;
        pr_id?: number;
      };
    }) => provideHintFeedback(projectId, hintId, data),
    onSuccess: (updatedHint, { hintId }) => {
      queryClient.setQueryData(
        learningsKeys.hintDetail(projectId, hintId),
        updatedHint
      );
      queryClient.invalidateQueries({ queryKey: learningsKeys.hintLists() });
    },
  });
}

// =============================================================================
// Aggregations Query Hooks
// =============================================================================

/**
 * Hook to fetch learning aggregations for a project
 * Sprint 100: GET /projects/{project_id}/aggregations
 */
export function useAggregations(
  projectId: string | undefined,
  params?: {
    period_type?: AggregationPeriod;
    status?: string;
    page?: number;
    per_page?: number;
  }
) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: learningsKeys.aggregationList(projectId || "", params),
    queryFn: () => getAggregations(projectId!, params),
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 5 * 60 * 1000, // 5 minutes (aggregations don't change often)
  });
}

/**
 * Hook to fetch a single aggregation by ID
 * Sprint 100: GET /projects/{project_id}/aggregations/{aggregation_id}
 */
export function useAggregation(
  projectId: string | undefined,
  aggregationId: string | undefined
) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: learningsKeys.aggregationDetail(projectId || "", aggregationId || ""),
    queryFn: () => getAggregation(projectId!, aggregationId!),
    enabled: isAuthenticated && !authLoading && !!projectId && !!aggregationId,
    staleTime: 60 * 1000, // 1 minute
  });
}

// =============================================================================
// Aggregations Mutation Hooks
// =============================================================================

/**
 * Hook to create a new aggregation
 * Sprint 100: POST /projects/{project_id}/aggregations
 */
export function useCreateAggregation(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateAggregationRequest) =>
      createAggregation(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: learningsKeys.aggregationLists() });
    },
  });
}

/**
 * Hook to apply an aggregation (implement suggestions)
 * Sprint 100: POST /projects/{project_id}/aggregations/{aggregation_id}/apply
 */
export function useApplyAggregation(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (aggregationId: string) => applyAggregation(projectId, aggregationId),
    onSuccess: (updatedAggregation, aggregationId) => {
      queryClient.setQueryData(
        learningsKeys.aggregationDetail(projectId, aggregationId),
        updatedAggregation
      );
      queryClient.invalidateQueries({ queryKey: learningsKeys.aggregationLists() });
      // Also invalidate hints as new hints may have been created
      queryClient.invalidateQueries({ queryKey: learningsKeys.hintLists() });
    },
  });
}

/**
 * Hook to reject an aggregation
 * Sprint 100: POST /projects/{project_id}/aggregations/{aggregation_id}/reject
 */
export function useRejectAggregation(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      aggregationId,
      reason,
    }: {
      aggregationId: string;
      reason: string;
    }) => rejectAggregation(projectId, aggregationId, reason),
    onSuccess: (updatedAggregation, { aggregationId }) => {
      queryClient.setQueryData(
        learningsKeys.aggregationDetail(projectId, aggregationId),
        updatedAggregation
      );
      queryClient.invalidateQueries({ queryKey: learningsKeys.aggregationLists() });
    },
  });
}

// =============================================================================
// Re-export types for convenience
// =============================================================================

export type {
  PRLearning,
  DecompositionHint,
  LearningAggregation,
  LearningFilterParams,
  HintFilterParams,
  CreateLearningRequest,
  UpdateLearningRequest,
  CreateHintRequest,
  UpdateHintRequest,
  CreateAggregationRequest,
};
