/**
 * Telemetry TanStack Query Hooks - SDLC Orchestrator Dashboard
 *
 * @module frontend/src/hooks/useTelemetry
 * @description React Query hooks for Telemetry API (Product Truth Layer)
 * @sdlc SDLC 6.0.5 Universal Framework
 * @status Sprint 147 - Product Truth Layer
 */

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";
import {
  getDashboardMetrics,
  getFunnelMetrics,
  getInterfaceBreakdown,
} from "@/lib/telemetry";

// Query keys for cache management
export const telemetryKeys = {
  all: ["telemetry"] as const,
  dashboard: () => [...telemetryKeys.all, "dashboard"] as const,
  funnels: () => [...telemetryKeys.all, "funnels"] as const,
  funnel: (name: string) => [...telemetryKeys.funnels(), name] as const,
  interfaces: () => [...telemetryKeys.all, "interfaces"] as const,
  interfacesRange: (start?: string, end?: string) =>
    [...telemetryKeys.interfaces(), { start, end }] as const,
};

/**
 * Hook to fetch activation dashboard metrics.
 *
 * Returns signups, projects, activation rate, and funnel summaries.
 * Sprint 147: Product Truth Layer - Replace "82-85% realization" with measured metrics.
 */
export function useTelemetryDashboard() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: telemetryKeys.dashboard(),
    queryFn: getDashboardMetrics,
    enabled: isAuthenticated && !authLoading,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 5 * 60 * 1000, // Auto-refresh every 5 minutes
  });
}

/**
 * Hook to fetch funnel metrics for a specific activation funnel.
 *
 * @param funnelName - "time_to_first_project" | "time_to_first_evidence" | "time_to_first_gate"
 * @param options - Optional date range
 */
export function useTelemetryFunnel(
  funnelName: "time_to_first_project" | "time_to_first_evidence" | "time_to_first_gate",
  options?: {
    startDate?: string;
    endDate?: string;
  }
) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: telemetryKeys.funnel(funnelName),
    queryFn: () => getFunnelMetrics(funnelName, options?.startDate, options?.endDate),
    enabled: isAuthenticated && !authLoading,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to fetch interface breakdown metrics.
 *
 * Shows usage distribution across web, CLI, extension, and API.
 *
 * @param options - Optional date range
 */
export function useTelemetryInterfaces(options?: {
  startDate?: string;
  endDate?: string;
}) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: telemetryKeys.interfacesRange(options?.startDate, options?.endDate),
    queryFn: () => getInterfaceBreakdown(options?.startDate, options?.endDate),
    enabled: isAuthenticated && !authLoading,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to fetch all three activation funnels at once.
 *
 * Useful for dashboard views that need all funnel data.
 */
export function useAllTelemetryFunnels(options?: {
  startDate?: string;
  endDate?: string;
}) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const projectFunnel = useQuery({
    queryKey: [...telemetryKeys.funnel("time_to_first_project"), options],
    queryFn: () =>
      getFunnelMetrics("time_to_first_project", options?.startDate, options?.endDate),
    enabled: isAuthenticated && !authLoading,
    staleTime: 5 * 60 * 1000,
  });

  const evidenceFunnel = useQuery({
    queryKey: [...telemetryKeys.funnel("time_to_first_evidence"), options],
    queryFn: () =>
      getFunnelMetrics("time_to_first_evidence", options?.startDate, options?.endDate),
    enabled: isAuthenticated && !authLoading,
    staleTime: 5 * 60 * 1000,
  });

  const gateFunnel = useQuery({
    queryKey: [...telemetryKeys.funnel("time_to_first_gate"), options],
    queryFn: () =>
      getFunnelMetrics("time_to_first_gate", options?.startDate, options?.endDate),
    enabled: isAuthenticated && !authLoading,
    staleTime: 5 * 60 * 1000,
  });

  return {
    projectFunnel,
    evidenceFunnel,
    gateFunnel,
    isLoading:
      projectFunnel.isLoading || evidenceFunnel.isLoading || gateFunnel.isLoading,
    isError: projectFunnel.isError || evidenceFunnel.isError || gateFunnel.isError,
  };
}
