/**
 * =========================================================================
 * Vibecoding Index React Query Hooks
 * SDLC Orchestrator - Sprint 118 (SPEC-0001 Anti-Vibecoding System)
 *
 * Version: 1.0.0
 * Date: January 29, 2026
 * Framework: SDLC 5.3.0 Quality Assurance System
 * Spec Reference: SPEC-0001
 *
 * Purpose: React Query hooks for Vibecoding Index operations
 * Formula: Intent (30%) + Ownership (25%) + Context (20%) + AI Attestation (15%) + Rejection (10%)
 * =========================================================================
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "./useAuth";
import { apiClient } from "@/lib/apiClient";

// =============================================================================
// Types
// =============================================================================

export interface CalculateIndexRequest {
  submission_id: string;
  submission_type?: string;
  project_id: string;
  intent_present: boolean;
  intent_linked_to_task: boolean;
  ownership_declared: boolean;
  ownership_in_codeowners: boolean;
  context_adr_linked: boolean;
  context_design_doc_exists: boolean;
  context_agents_md_fresh: boolean;
  ai_attestation_provided: boolean;
  ai_attestation_review_time_adequate: boolean;
  rejection_history_count: number;
}

export interface VibecodingIndexResult {
  submission_id: string;
  index_score: number;
  zone: "GREEN" | "YELLOW" | "ORANGE" | "RED";
  signals: {
    intent: number;
    ownership: number;
    context: number;
    ai_attestation: number;
    rejection_history: number;
  };
  routing: {
    decision: "AUTO_MERGE" | "HUMAN_REVIEW" | "SENIOR_REVIEW" | "BLOCK";
    approver_required: string | null;
    reason: string;
  };
  calculated_at: string;
}

export interface IndexHistoryItem {
  id: string;
  submission_id: string;
  index_score: number;
  zone: string;
  calculated_at: string;
  signals: Record<string, number>;
}

export interface IndexHistoryResponse {
  submission_id: string;
  history: IndexHistoryItem[];
  latest_score: number;
  trend: "improving" | "stable" | "degrading";
}

export interface RouteRequest {
  submission_id: string;
  project_id: string;
  index_score: number;
}

export interface RouteResponse {
  submission_id: string;
  decision: "AUTO_MERGE" | "HUMAN_REVIEW" | "SENIOR_REVIEW" | "BLOCK";
  zone: string;
  approver_required: string | null;
  reason: string;
  escalation_path: string[];
}

export interface SignalsResponse {
  submission_id: string;
  index_score: number;
  signals: {
    intent: { score: number; weight: number; contribution: number; details: string };
    ownership: { score: number; weight: number; contribution: number; details: string };
    context: { score: number; weight: number; contribution: number; details: string };
    ai_attestation: { score: number; weight: number; contribution: number; details: string };
    rejection_history: { score: number; weight: number; contribution: number; details: string };
  };
  top_contributors: Array<{
    signal: string;
    contribution_percent: number;
    improvement_suggestion: string;
  }>;
}

export interface ProjectStatsResponse {
  project_id: string;
  total_submissions: number;
  average_index: number;
  zone_distribution: {
    GREEN: number;
    YELLOW: number;
    ORANGE: number;
    RED: number;
  };
  trend_7d: "improving" | "stable" | "degrading";
  auto_merge_rate: number;
}

export interface KillSwitchCheckRequest {
  project_id: string;
}

export interface KillSwitchCheckResponse {
  should_trigger: boolean;
  triggered_criteria: string[];
  current_metrics: {
    rejection_rate: number;
    rejection_rate_threshold: number;
    rejection_rate_triggered: boolean;
    latency_p95_ms: number;
    latency_p95_threshold_ms: number;
    latency_triggered: boolean;
    critical_cves: number;
    critical_cves_threshold: number;
    cves_triggered: boolean;
  };
  recommended_action: string;
  last_check: string;
}

// =============================================================================
// API Functions
// =============================================================================

async function calculateVibecodingIndex(
  request: CalculateIndexRequest
): Promise<VibecodingIndexResult> {
  const response = await apiClient.post<VibecodingIndexResult>(
    "/governance/vibecoding/calculate",
    request
  );
  return response.data;
}

async function getIndexHistory(
  submissionId: string
): Promise<IndexHistoryResponse> {
  const response = await apiClient.get<IndexHistoryResponse>(
    `/governance/vibecoding/${submissionId}`
  );
  return response.data;
}

async function getRoutingDecision(
  request: RouteRequest
): Promise<RouteResponse> {
  const response = await apiClient.post<RouteResponse>(
    "/governance/vibecoding/route",
    request
  );
  return response.data;
}

async function getSignalBreakdown(
  submissionId: string
): Promise<SignalsResponse> {
  const response = await apiClient.get<SignalsResponse>(
    `/governance/vibecoding/signals/${submissionId}`
  );
  return response.data;
}

async function checkVibecodingKillSwitch(
  request: KillSwitchCheckRequest
): Promise<KillSwitchCheckResponse> {
  const response = await apiClient.post<KillSwitchCheckResponse>(
    "/governance/vibecoding/kill-switch/check",
    request
  );
  return response.data;
}

async function getProjectStats(
  projectId: string
): Promise<ProjectStatsResponse> {
  const response = await apiClient.get<ProjectStatsResponse>(
    `/governance/vibecoding/stats?project_id=${projectId}`
  );
  return response.data;
}

// =============================================================================
// Query Key Factory
// =============================================================================

export const vibecodingKeys = {
  all: ["vibecoding"] as const,
  history: (submissionId: string) =>
    [...vibecodingKeys.all, "history", submissionId] as const,
  signals: (submissionId: string) =>
    [...vibecodingKeys.all, "signals", submissionId] as const,
  stats: (projectId: string) =>
    [...vibecodingKeys.all, "stats", projectId] as const,
  killSwitch: (projectId: string) =>
    [...vibecodingKeys.all, "kill-switch", projectId] as const,
};

// =============================================================================
// Query Hooks
// =============================================================================

/**
 * Hook to get vibecoding index history for a submission
 */
export function useVibecodingHistory(submissionId: string) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: vibecodingKeys.history(submissionId),
    queryFn: () => getIndexHistory(submissionId),
    enabled: isAuthenticated && !authLoading && !!submissionId,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Hook to get signal breakdown for a submission
 */
export function useVibecodingSignals(submissionId: string) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: vibecodingKeys.signals(submissionId),
    queryFn: () => getSignalBreakdown(submissionId),
    enabled: isAuthenticated && !authLoading && !!submissionId,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Hook to get project statistics
 */
export function useVibecodingStats(projectId: string) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: vibecodingKeys.stats(projectId),
    queryFn: () => getProjectStats(projectId),
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 60 * 1000, // Auto-refresh every minute
  });
}

/**
 * Hook to check kill switch status for a project
 */
export function useVibecodingKillSwitch(projectId: string) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: vibecodingKeys.killSwitch(projectId),
    queryFn: () => checkVibecodingKillSwitch({ project_id: projectId }),
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Auto-refresh every minute
  });
}

// =============================================================================
// Mutation Hooks
// =============================================================================

/**
 * Hook to calculate vibecoding index for a submission
 */
export function useCalculateVibecodingIndex() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: calculateVibecodingIndex,
    onSuccess: (data) => {
      // Invalidate related queries
      queryClient.invalidateQueries({
        queryKey: vibecodingKeys.history(data.submission_id),
      });
      queryClient.invalidateQueries({
        queryKey: vibecodingKeys.signals(data.submission_id),
      });
    },
  });
}

/**
 * Hook to get routing decision for a submission
 */
export function useGetRoutingDecision() {
  return useMutation({
    mutationFn: getRoutingDecision,
  });
}

// =============================================================================
// Utility Hooks
// =============================================================================

/**
 * Hook to get zone color and styling
 */
export function useZoneColor(zone: string): {
  bgColor: string;
  textColor: string;
  borderColor: string;
  label: string;
} {
  switch (zone) {
    case "GREEN":
      return {
        bgColor: "bg-green-100",
        textColor: "text-green-700",
        borderColor: "border-green-200",
        label: "Auto-Merge",
      };
    case "YELLOW":
      return {
        bgColor: "bg-yellow-100",
        textColor: "text-yellow-700",
        borderColor: "border-yellow-200",
        label: "Human Review",
      };
    case "ORANGE":
      return {
        bgColor: "bg-orange-100",
        textColor: "text-orange-700",
        borderColor: "border-orange-200",
        label: "Senior Review",
      };
    case "RED":
      return {
        bgColor: "bg-red-100",
        textColor: "text-red-700",
        borderColor: "border-red-200",
        label: "Blocked",
      };
    default:
      return {
        bgColor: "bg-gray-100",
        textColor: "text-gray-700",
        borderColor: "border-gray-200",
        label: "Unknown",
      };
  }
}

/**
 * Hook to get combined vibecoding state for a submission
 */
export function useVibecodingState(submissionId: string) {
  const history = useVibecodingHistory(submissionId);
  const signals = useVibecodingSignals(submissionId);

  return {
    isLoading: history.isLoading || signals.isLoading,
    isError: history.isError || signals.isError,
    history: history.data,
    signals: signals.data,
    latestScore: history.data?.latest_score ?? 0,
    trend: history.data?.trend ?? "stable",
    refetch: () => {
      history.refetch();
      signals.refetch();
    },
  };
}
