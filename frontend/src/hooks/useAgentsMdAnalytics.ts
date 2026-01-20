/**
 * AGENTS.md Analytics TanStack Query Hooks - SDLC Orchestrator Dashboard
 *
 * @module frontend/src/hooks/useAgentsMdAnalytics
 * @description React Query hooks for AGENTS.md Analytics API
 * @sdlc SDLC 5.1.3 Framework - Sprint 85 (AGENTS.md UI)
 * @status Sprint 85 - CTO APPROVED (January 20, 2026)
 * @see backend/app/api/routes/analytics.py
 */

import { useQuery, useMutation } from "@tanstack/react-query";
import {
  getOverlayMetrics,
  getEngagementMetrics,
  getAnalyticsSummary,
  getAnalyticsTimeSeries,
  exportAnalytics,
  getProjectAnalytics,
  type TimeSeriesResponse,
} from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

// =============================================================================
// Query Keys for Cache Management
// =============================================================================

export const analyticsKeys = {
  all: ["analytics"] as const,
  overlay: (params?: { period_start?: string; period_end?: string }) =>
    [...analyticsKeys.all, "overlay", params] as const,
  engagement: (params?: { period_start?: string; period_end?: string }) =>
    [...analyticsKeys.all, "engagement", params] as const,
  summary: (params?: { period_start?: string; period_end?: string }) =>
    [...analyticsKeys.all, "summary", params] as const,
  timeSeries: (
    metric: string,
    params?: { period_start?: string; period_end?: string; granularity?: string }
  ) => [...analyticsKeys.all, "time-series", metric, params] as const,
  project: (projectId: string) => [...analyticsKeys.all, "project", projectId] as const,
};

// =============================================================================
// Analytics Query Hooks
// =============================================================================

/**
 * Hook to fetch overlay metrics
 * Sprint 85: GET /analytics/overlay
 */
export function useOverlayMetrics(params?: { period_start?: string; period_end?: string }) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: analyticsKeys.overlay(params),
    queryFn: () => getOverlayMetrics(params),
    enabled: isAuthenticated && !authLoading,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to fetch engagement metrics
 * Sprint 85: GET /analytics/engagement
 */
export function useEngagementMetrics(params?: { period_start?: string; period_end?: string }) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: analyticsKeys.engagement(params),
    queryFn: () => getEngagementMetrics(params),
    enabled: isAuthenticated && !authLoading,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to fetch complete analytics summary
 * Sprint 85: GET /analytics/summary
 */
export function useAnalyticsSummary(params?: { period_start?: string; period_end?: string }) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: analyticsKeys.summary(params),
    queryFn: () => getAnalyticsSummary(params),
    enabled: isAuthenticated && !authLoading,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to fetch time series data for a metric
 * Sprint 85: GET /analytics/time-series/{metric}
 */
export function useAnalyticsTimeSeries(
  metric: string,
  params?: {
    period_start?: string;
    period_end?: string;
    granularity?: "hour" | "day" | "week" | "month";
  }
) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: analyticsKeys.timeSeries(metric, params),
    queryFn: () => getAnalyticsTimeSeries(metric, params),
    enabled: isAuthenticated && !authLoading && !!metric,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to fetch project-specific analytics
 * Sprint 85: GET /analytics/projects/{project_id}
 */
export function useProjectAnalytics(projectId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: analyticsKeys.project(projectId || ""),
    queryFn: () => getProjectAnalytics(projectId!),
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

// =============================================================================
// Export Analytics Mutation
// =============================================================================

/**
 * Hook to export analytics data
 * Sprint 85: GET /analytics/export
 */
export function useExportAnalytics() {
  return useMutation({
    mutationFn: ({
      format,
      options,
    }: {
      format: "json" | "csv";
      options?: {
        metrics?: string[];
        period_start?: string;
        period_end?: string;
      };
    }) => exportAnalytics(format, options),
    onSuccess: (blob, variables) => {
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `analytics-export-${new Date().toISOString().split("T")[0]}.${variables.format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    },
  });
}

// =============================================================================
// Combined Analytics Hooks
// =============================================================================

/**
 * Hook to get all analytics metrics in one call
 */
export function useAllAnalytics(params?: { period_start?: string; period_end?: string }) {
  const summaryQuery = useAnalyticsSummary(params);

  return {
    summary: summaryQuery.data,
    overlay: summaryQuery.data?.overlay,
    engagement: summaryQuery.data?.engagement,
    gates: summaryQuery.data?.gates,
    security: summaryQuery.data?.security,
    agentsMd: summaryQuery.data?.agents_md,
    isLoading: summaryQuery.isLoading,
    isError: summaryQuery.isError,
    error: summaryQuery.error,
    refetch: summaryQuery.refetch,
  };
}

/**
 * Hook to get time series data for dashboard charts
 */
export function useDashboardTimeSeries(
  granularity: "hour" | "day" | "week" | "month" = "day"
) {
  const overlayQuery = useAnalyticsTimeSeries("overlays", { granularity });
  const regenerationsQuery = useAnalyticsTimeSeries("regenerations", { granularity });
  const gatesQuery = useAnalyticsTimeSeries("gates_passed", { granularity });

  return {
    overlays: overlayQuery.data,
    regenerations: regenerationsQuery.data,
    gates: gatesQuery.data,
    isLoading:
      overlayQuery.isLoading || regenerationsQuery.isLoading || gatesQuery.isLoading,
    isError: overlayQuery.isError || regenerationsQuery.isError || gatesQuery.isError,
  };
}

// =============================================================================
// Analytics Calculation Utilities
// =============================================================================

/**
 * Calculate trend from time series data
 */
export function calculateTrend(data: TimeSeriesResponse | undefined): {
  direction: "up" | "down" | "stable";
  percentage: number;
} {
  if (!data || data.data.length < 2) {
    return { direction: "stable", percentage: 0 };
  }

  const recent = data.data.slice(-7); // Last 7 data points
  if (recent.length < 2) {
    return { direction: "stable", percentage: 0 };
  }

  const firstHalf = recent.slice(0, Math.floor(recent.length / 2));
  const secondHalf = recent.slice(Math.floor(recent.length / 2));

  const firstAvg =
    firstHalf.reduce((sum, d) => sum + d.value, 0) / firstHalf.length;
  const secondAvg =
    secondHalf.reduce((sum, d) => sum + d.value, 0) / secondHalf.length;

  if (firstAvg === 0) {
    return { direction: secondAvg > 0 ? "up" : "stable", percentage: 0 };
  }

  const percentage = ((secondAvg - firstAvg) / firstAvg) * 100;

  if (percentage > 5) return { direction: "up", percentage };
  if (percentage < -5) return { direction: "down", percentage: Math.abs(percentage) };
  return { direction: "stable", percentage: 0 };
}

/**
 * Format analytics value for display
 */
export function formatAnalyticsValue(value: number, type: "count" | "rate" | "time"): string {
  switch (type) {
    case "count":
      if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
      if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
      return value.toString();
    case "rate":
      return `${value.toFixed(1)}%`;
    case "time":
      if (value >= 3600) return `${(value / 3600).toFixed(1)}h`;
      if (value >= 60) return `${(value / 60).toFixed(0)}m`;
      return `${value.toFixed(0)}s`;
    default:
      return value.toString();
  }
}

/**
 * Get color for rate value
 */
export function getRateColor(rate: number): string {
  if (rate >= 90) return "green";
  if (rate >= 70) return "yellow";
  if (rate >= 50) return "orange";
  return "red";
}
