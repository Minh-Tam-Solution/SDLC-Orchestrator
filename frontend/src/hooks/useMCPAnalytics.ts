/**
 * MCP Analytics TanStack Query Hooks - SDLC Orchestrator Dashboard
 *
 * @module frontend/src/hooks/useMCPAnalytics
 * @description React Query hooks for MCP Analytics API
 * @sdlc SDLC 6.0.3 Universal Framework
 * @status Sprint 150 - MCP Analytics Dashboard
 */

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";
import {
  getMCPProviderHealth,
  getMCPCostTracking,
  getMCPLatencyMetrics,
  getMCPContextUsage,
  getMCPDashboardSummary,
} from "@/lib/mcp";

// Query keys for cache management
export const mcpKeys = {
  all: ["mcp"] as const,
  health: () => [...mcpKeys.all, "health"] as const,
  cost: () => [...mcpKeys.all, "cost"] as const,
  costRange: (start?: string, end?: string) =>
    [...mcpKeys.cost(), { start, end }] as const,
  latency: () => [...mcpKeys.all, "latency"] as const,
  latencyRange: (start?: string, end?: string, granularity?: string) =>
    [...mcpKeys.latency(), { start, end, granularity }] as const,
  context: () => [...mcpKeys.all, "context"] as const,
  contextRange: (start?: string, end?: string) =>
    [...mcpKeys.context(), { start, end }] as const,
  dashboard: () => [...mcpKeys.all, "dashboard"] as const,
};

/**
 * Hook to fetch MCP provider health metrics.
 *
 * Returns health status, uptime, and error rates for all AI providers.
 * Sprint 150: MCP Analytics Dashboard MVP.
 */
export function useMCPProviderHealth() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: mcpKeys.health(),
    queryFn: getMCPProviderHealth,
    enabled: isAuthenticated && !authLoading,
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 60 * 1000, // Auto-refresh every minute for real-time health
  });
}

/**
 * Hook to fetch MCP cost tracking metrics.
 *
 * Returns cost estimates per provider and category breakdown.
 *
 * @param options - Optional date range
 */
export function useMCPCostTracking(options?: {
  startDate?: string;
  endDate?: string;
}) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: mcpKeys.costRange(options?.startDate, options?.endDate),
    queryFn: () => getMCPCostTracking(options?.startDate, options?.endDate),
    enabled: isAuthenticated && !authLoading,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to fetch MCP latency metrics and trends.
 *
 * Returns latency trends and SLA compliance per provider.
 *
 * @param options - Optional date range and granularity
 */
export function useMCPLatencyMetrics(options?: {
  startDate?: string;
  endDate?: string;
  granularity?: "hour" | "day" | "week";
}) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: mcpKeys.latencyRange(
      options?.startDate,
      options?.endDate,
      options?.granularity
    ),
    queryFn: () =>
      getMCPLatencyMetrics(
        options?.startDate,
        options?.endDate,
        options?.granularity
      ),
    enabled: isAuthenticated && !authLoading,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to fetch MCP context provider usage metrics.
 *
 * Returns usage statistics for each context provider.
 *
 * @param options - Optional date range
 */
export function useMCPContextUsage(options?: {
  startDate?: string;
  endDate?: string;
}) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: mcpKeys.contextRange(options?.startDate, options?.endDate),
    queryFn: () => getMCPContextUsage(options?.startDate, options?.endDate),
    enabled: isAuthenticated && !authLoading,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to fetch complete MCP dashboard summary.
 *
 * Aggregates all metrics for dashboard rendering in a single request.
 * Use this for the main dashboard view to minimize API calls.
 */
export function useMCPDashboard() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: mcpKeys.dashboard(),
    queryFn: getMCPDashboardSummary,
    enabled: isAuthenticated && !authLoading,
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 60 * 1000, // Auto-refresh every minute
  });
}

/**
 * Hook to fetch all MCP analytics data at once.
 *
 * Useful for comprehensive dashboard views that need all data.
 */
export function useAllMCPAnalytics(options?: {
  startDate?: string;
  endDate?: string;
}) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const healthQuery = useQuery({
    queryKey: mcpKeys.health(),
    queryFn: getMCPProviderHealth,
    enabled: isAuthenticated && !authLoading,
    staleTime: 60 * 1000,
  });

  const costQuery = useQuery({
    queryKey: mcpKeys.costRange(options?.startDate, options?.endDate),
    queryFn: () => getMCPCostTracking(options?.startDate, options?.endDate),
    enabled: isAuthenticated && !authLoading,
    staleTime: 5 * 60 * 1000,
  });

  const latencyQuery = useQuery({
    queryKey: mcpKeys.latencyRange(options?.startDate, options?.endDate, "day"),
    queryFn: () =>
      getMCPLatencyMetrics(options?.startDate, options?.endDate, "day"),
    enabled: isAuthenticated && !authLoading,
    staleTime: 5 * 60 * 1000,
  });

  const contextQuery = useQuery({
    queryKey: mcpKeys.contextRange(options?.startDate, options?.endDate),
    queryFn: () => getMCPContextUsage(options?.startDate, options?.endDate),
    enabled: isAuthenticated && !authLoading,
    staleTime: 5 * 60 * 1000,
  });

  return {
    health: healthQuery,
    cost: costQuery,
    latency: latencyQuery,
    context: contextQuery,
    isLoading:
      healthQuery.isLoading ||
      costQuery.isLoading ||
      latencyQuery.isLoading ||
      contextQuery.isLoading,
    isError:
      healthQuery.isError ||
      costQuery.isError ||
      latencyQuery.isError ||
      contextQuery.isError,
  };
}
