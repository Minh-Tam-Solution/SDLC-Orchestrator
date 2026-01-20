/**
 * Evidence Manifest Hooks - SDLC Orchestrator
 *
 * @module frontend/src/hooks/useEvidenceManifest
 * @description TanStack Query hooks for Evidence Hash Chain (P0 Blocker)
 * @sdlc SDLC 5.1.3 Framework - Sprint 87 (Evidence Hash Chain v1)
 * @status Sprint 87 - CTO APPROVED (January 20, 2026)
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getEvidenceManifests,
  getEvidenceManifest,
  createEvidenceManifest,
  verifyEvidenceChain,
  getChainStatus,
  getVerificationHistory,
} from "@/lib/api";
import type {
  ManifestListParams,
  CreateManifestRequest,
  VerifyChainRequest,
} from "@/lib/types/evidence-manifest";

// =============================================================================
// Query Keys
// =============================================================================

export const evidenceManifestKeys = {
  all: ["evidence-manifests"] as const,
  lists: () => [...evidenceManifestKeys.all, "list"] as const,
  list: (params: ManifestListParams) =>
    [...evidenceManifestKeys.lists(), params] as const,
  details: () => [...evidenceManifestKeys.all, "detail"] as const,
  detail: (id: string) => [...evidenceManifestKeys.details(), id] as const,
  chainStatus: (projectId: string) =>
    [...evidenceManifestKeys.all, "chain-status", projectId] as const,
  verificationHistory: (projectId: string) =>
    [...evidenceManifestKeys.all, "verification-history", projectId] as const,
};

// =============================================================================
// Query Hooks
// =============================================================================

/**
 * Hook to fetch evidence manifests list
 */
export function useEvidenceManifests(params: ManifestListParams) {
  return useQuery({
    queryKey: evidenceManifestKeys.list(params),
    queryFn: () => getEvidenceManifests(params),
    enabled: !!params.project_id,
    staleTime: 30 * 1000, // 30 seconds
  });
}

/**
 * Hook to fetch single evidence manifest by ID
 */
export function useEvidenceManifest(manifestId: string | undefined) {
  return useQuery({
    queryKey: evidenceManifestKeys.detail(manifestId ?? ""),
    queryFn: () => getEvidenceManifest(manifestId!),
    enabled: !!manifestId,
    staleTime: 60 * 1000, // 1 minute (manifests are immutable)
  });
}

/**
 * Hook to fetch chain status for a project
 */
export function useChainStatus(projectId: string | undefined) {
  return useQuery({
    queryKey: evidenceManifestKeys.chainStatus(projectId ?? ""),
    queryFn: () => getChainStatus(projectId!),
    enabled: !!projectId,
    staleTime: 30 * 1000, // 30 seconds
  });
}

/**
 * Hook to fetch verification history for a project
 */
export function useVerificationHistory(
  projectId: string | undefined,
  options?: { limit?: number; offset?: number }
) {
  return useQuery({
    queryKey: evidenceManifestKeys.verificationHistory(projectId ?? ""),
    queryFn: () =>
      getVerificationHistory(projectId!, options?.limit, options?.offset),
    enabled: !!projectId,
    staleTime: 30 * 1000, // 30 seconds
  });
}

// =============================================================================
// Mutation Hooks
// =============================================================================

/**
 * Hook to create a new evidence manifest
 */
export function useCreateManifest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateManifestRequest) => createEvidenceManifest(data),
    onSuccess: (_, variables) => {
      // Invalidate manifests list for this project
      queryClient.invalidateQueries({
        queryKey: evidenceManifestKeys.list({ project_id: variables.project_id }),
      });
      // Invalidate chain status
      queryClient.invalidateQueries({
        queryKey: evidenceManifestKeys.chainStatus(variables.project_id),
      });
    },
  });
}

/**
 * Hook to verify evidence chain
 */
export function useVerifyChain() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: VerifyChainRequest) => verifyEvidenceChain(data),
    onSuccess: (_, variables) => {
      // Invalidate chain status
      queryClient.invalidateQueries({
        queryKey: evidenceManifestKeys.chainStatus(variables.project_id),
      });
      // Invalidate verification history
      queryClient.invalidateQueries({
        queryKey: evidenceManifestKeys.verificationHistory(variables.project_id),
      });
    },
  });
}

// =============================================================================
// Combined Hooks
// =============================================================================

/**
 * Hook for Evidence Manifest dashboard - combines status and history
 */
export function useEvidenceManifestDashboard(projectId: string | undefined) {
  const chainStatusQuery = useChainStatus(projectId);
  const verificationHistoryQuery = useVerificationHistory(projectId, {
    limit: 10,
  });
  const manifestsQuery = useEvidenceManifests({
    project_id: projectId ?? "",
    limit: 20,
  });

  return {
    chainStatus: chainStatusQuery.data,
    verificationHistory: verificationHistoryQuery.data,
    manifests: manifestsQuery.data,
    isLoading:
      chainStatusQuery.isLoading ||
      verificationHistoryQuery.isLoading ||
      manifestsQuery.isLoading,
    isError:
      chainStatusQuery.isError ||
      verificationHistoryQuery.isError ||
      manifestsQuery.isError,
    error:
      chainStatusQuery.error ||
      verificationHistoryQuery.error ||
      manifestsQuery.error,
    refetch: () => {
      chainStatusQuery.refetch();
      verificationHistoryQuery.refetch();
      manifestsQuery.refetch();
    },
  };
}

/**
 * Hook for Manifest detail page
 */
export function useManifestDetail(manifestId: string | undefined) {
  const manifestQuery = useEvidenceManifest(manifestId);

  // Get project ID from manifest to fetch related data
  const projectId = manifestQuery.data?.project_id;

  const chainStatusQuery = useChainStatus(projectId);

  return {
    manifest: manifestQuery.data,
    chainStatus: chainStatusQuery.data,
    isLoading: manifestQuery.isLoading,
    isError: manifestQuery.isError,
    error: manifestQuery.error,
  };
}
