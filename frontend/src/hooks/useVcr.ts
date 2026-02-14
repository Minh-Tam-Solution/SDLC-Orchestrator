/**
 * VCR (Version Controlled Resolution) TanStack Query Hooks
 * SDLC Orchestrator Dashboard
 *
 * @module frontend/src/hooks/useVcr
 * @description React Query hooks for VCR API - Sprint 151 SASE Artifacts Enhancement
 * @sdlc SDLC 6.0.5 Universal Framework
 * @status Sprint 151 - SASE Artifacts Enhancement
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getVcrs,
  getVcr,
  createVcr,
  updateVcr,
  deleteVcr,
  submitVcr,
  approveVcr,
  rejectVcr,
  reopenVcr,
  getVcrStats,
  autoGenerateVcr,
  type VCR,
  type VCRCreate,
  type VCRUpdate,
  type VCRRejectRequest,
  type VCRListResponse,
  type VCRListOptions,
  type VCRStats,
  type VCRAutoGenerateRequest,
  type VCRAutoGenerateResponse,
  type VCRStatus,
} from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

// Query keys for cache management
export const vcrKeys = {
  all: ["vcrs"] as const,
  lists: () => [...vcrKeys.all, "list"] as const,
  list: (options?: VCRListOptions) => [...vcrKeys.lists(), options] as const,
  details: () => [...vcrKeys.all, "detail"] as const,
  detail: (id: string) => [...vcrKeys.details(), id] as const,
  stats: (projectId: string) => [...vcrKeys.all, "stats", projectId] as const,
};

/**
 * Hook to fetch list of VCRs with pagination and filters
 * Sprint 151: VCR workflow management
 */
export function useVcrs(options?: VCRListOptions) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: vcrKeys.list(options),
    queryFn: () => getVcrs(options),
    enabled: isAuthenticated && !authLoading,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Hook to fetch VCRs by project ID
 */
export function useProjectVcrs(projectId: string | undefined) {
  return useVcrs(projectId ? { project_id: projectId } : undefined);
}

/**
 * Hook to fetch VCRs by status
 */
export function useVcrsByStatus(status: VCRStatus | undefined) {
  return useVcrs(status ? { status } : undefined);
}

/**
 * Hook to fetch a single VCR by ID
 * Sprint 151: VCR detail view
 */
export function useVcr(vcrId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: vcrKeys.detail(vcrId || ""),
    queryFn: () => {
      if (!vcrId) {
        throw new Error("Missing VCR ID");
      }
      return getVcr(vcrId);
    },
    enabled: isAuthenticated && !authLoading && !!vcrId,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Hook to fetch VCR statistics for a project
 * Sprint 151: VCR metrics and analytics
 */
export function useVcrStats(projectId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: vcrKeys.stats(projectId || ""),
    queryFn: () => {
      if (!projectId) {
        throw new Error("Missing project ID");
      }
      return getVcrStats(projectId);
    },
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to invalidate VCR cache
 */
export function useInvalidateVcrs() {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: vcrKeys.all });
  };
}

/**
 * Hook to create a new VCR
 * Sprint 151: VCR workflow - create DRAFT
 */
export function useCreateVcr() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: VCRCreate) => createVcr(data),
    onSuccess: (newVcr) => {
      // Invalidate lists to show the new VCR
      queryClient.invalidateQueries({ queryKey: vcrKeys.lists() });
      // Invalidate stats for the project
      queryClient.invalidateQueries({
        queryKey: vcrKeys.stats(newVcr.project_id),
      });
    },
  });
}

/**
 * Hook to update a VCR (draft only)
 * Sprint 151: VCR workflow - edit DRAFT
 */
export function useUpdateVcr() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ vcrId, data }: { vcrId: string; data: VCRUpdate }) =>
      updateVcr(vcrId, data),
    onSuccess: (updatedVcr) => {
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: vcrKeys.lists() });
      // Update the specific VCR in cache
      queryClient.setQueryData(vcrKeys.detail(updatedVcr.id), updatedVcr);
    },
  });
}

/**
 * Hook to delete a VCR (draft only)
 * Sprint 151: VCR workflow - delete DRAFT
 */
export function useDeleteVcr() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (vcrId: string) => deleteVcr(vcrId),
    onSuccess: (_, vcrId) => {
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: vcrKeys.lists() });
      // Remove from cache
      queryClient.removeQueries({ queryKey: vcrKeys.detail(vcrId) });
      // Stats will be updated on next fetch
      queryClient.invalidateQueries({
        queryKey: vcrKeys.all,
        predicate: (query) =>
          query.queryKey.includes("stats"),
      });
    },
  });
}

/**
 * Hook to submit VCR for approval
 * Sprint 151: VCR workflow - submit DRAFT → SUBMITTED
 */
export function useSubmitVcr() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (vcrId: string) => submitVcr(vcrId),
    onSuccess: (updatedVcr) => {
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: vcrKeys.lists() });
      // Update the specific VCR in cache
      queryClient.setQueryData(vcrKeys.detail(updatedVcr.id), updatedVcr);
      // Invalidate stats
      queryClient.invalidateQueries({
        queryKey: vcrKeys.stats(updatedVcr.project_id),
      });
    },
  });
}

/**
 * Hook to approve a VCR (CTO/CEO only)
 * Sprint 151: VCR workflow - approve SUBMITTED → APPROVED
 */
export function useApproveVcr() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (vcrId: string) => approveVcr(vcrId),
    onSuccess: (updatedVcr) => {
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: vcrKeys.lists() });
      // Update the specific VCR in cache
      queryClient.setQueryData(vcrKeys.detail(updatedVcr.id), updatedVcr);
      // Invalidate stats
      queryClient.invalidateQueries({
        queryKey: vcrKeys.stats(updatedVcr.project_id),
      });
    },
  });
}

/**
 * Hook to reject a VCR (CTO/CEO only)
 * Sprint 151: VCR workflow - reject SUBMITTED → REJECTED
 */
export function useRejectVcr() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      vcrId,
      request,
    }: {
      vcrId: string;
      request: VCRRejectRequest;
    }) => rejectVcr(vcrId, request),
    onSuccess: (updatedVcr) => {
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: vcrKeys.lists() });
      // Update the specific VCR in cache
      queryClient.setQueryData(vcrKeys.detail(updatedVcr.id), updatedVcr);
      // Invalidate stats
      queryClient.invalidateQueries({
        queryKey: vcrKeys.stats(updatedVcr.project_id),
      });
    },
  });
}

/**
 * Hook to reopen a rejected VCR
 * Sprint 151: VCR workflow - reopen REJECTED → DRAFT
 */
export function useReopenVcr() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (vcrId: string) => reopenVcr(vcrId),
    onSuccess: (updatedVcr) => {
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: vcrKeys.lists() });
      // Update the specific VCR in cache
      queryClient.setQueryData(vcrKeys.detail(updatedVcr.id), updatedVcr);
      // Invalidate stats
      queryClient.invalidateQueries({
        queryKey: vcrKeys.stats(updatedVcr.project_id),
      });
    },
  });
}

/**
 * Hook to auto-generate VCR content using AI
 * Sprint 151: AI-assisted VCR creation
 */
export function useAutoGenerateVcr() {
  return useMutation({
    mutationFn: (request: VCRAutoGenerateRequest) => autoGenerateVcr(request),
  });
}

// Export types for use in components
export type {
  VCR,
  VCRCreate,
  VCRUpdate,
  VCRRejectRequest,
  VCRListResponse,
  VCRListOptions,
  VCRStats,
  VCRAutoGenerateRequest,
  VCRAutoGenerateResponse,
  VCRStatus,
};
