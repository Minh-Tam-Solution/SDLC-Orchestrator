/**
 * CRP (Consultation Request Protocol) TanStack Query Hooks
 * SDLC Orchestrator Dashboard
 *
 * @module frontend/src/hooks/useCrp
 * @description React Query hooks for CRP API - Sprint 151 SASE Artifacts Enhancement
 * @sdlc SDLC 6.0.5 Universal Framework
 * @status Sprint 151 - SASE Artifacts Enhancement (Backend from Sprint 101)
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getCrps,
  getCrp,
  createCrp,
  assignCrpReviewer,
  resolveCrp,
  addCrpComment,
  getMyPendingReviews,
  autoGenerateCrp,
  type CRP,
  type CRPCreate,
  type CRPAssignRequest,
  type CRPResolveRequest,
  type CRPAddCommentRequest,
  type CRPListResponse,
  type CRPListOptions,
  type CRPComment,
  type CRPStatus,
  type CRPPriority,
  type ReviewerExpertise,
  type CRPAutoGenerateRequest,
  type CRPAutoGenerateResponse,
} from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

// Query keys for cache management
export const crpKeys = {
  all: ["crps"] as const,
  lists: () => [...crpKeys.all, "list"] as const,
  list: (options?: CRPListOptions) => [...crpKeys.lists(), options] as const,
  details: () => [...crpKeys.all, "detail"] as const,
  detail: (id: string) => [...crpKeys.details(), id] as const,
  myReviews: () => [...crpKeys.all, "my-reviews"] as const,
};

/**
 * Hook to fetch list of CRPs with pagination and filters
 * Sprint 151: CRP workflow management
 */
export function useCrps(options?: CRPListOptions) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: crpKeys.list(options),
    queryFn: () => getCrps(options),
    enabled: isAuthenticated && !authLoading,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Hook to fetch CRPs by project ID
 */
export function useProjectCrps(projectId: string | undefined) {
  return useCrps(projectId ? { project_id: projectId } : undefined);
}

/**
 * Hook to fetch CRPs by status
 */
export function useCrpsByStatus(status: CRPStatus | undefined) {
  return useCrps(status ? { status } : undefined);
}

/**
 * Hook to fetch CRPs by priority
 */
export function useCrpsByPriority(priority: CRPPriority | undefined) {
  return useCrps(priority ? { priority } : undefined);
}

/**
 * Hook to fetch a single CRP by ID
 * Sprint 151: CRP detail view
 */
export function useCrp(crpId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: crpKeys.detail(crpId || ""),
    queryFn: () => {
      if (!crpId) {
        throw new Error("Missing CRP ID");
      }
      return getCrp(crpId);
    },
    enabled: isAuthenticated && !authLoading && !!crpId,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Hook to fetch pending reviews for current user
 * Sprint 151: Reviewer dashboard
 */
export function useMyPendingReviews() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: crpKeys.myReviews(),
    queryFn: () => getMyPendingReviews(),
    enabled: isAuthenticated && !authLoading,
    staleTime: 30 * 1000, // 30 seconds (more frequent updates for reviewers)
  });
}

/**
 * Hook to invalidate CRP cache
 */
export function useInvalidateCrps() {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: crpKeys.all });
  };
}

/**
 * Hook to create a new CRP
 * Sprint 151: CRP workflow - create consultation
 */
export function useCreateCrp() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CRPCreate) => createCrp(data),
    onSuccess: () => {
      // Invalidate lists to show the new CRP
      queryClient.invalidateQueries({ queryKey: crpKeys.lists() });
    },
  });
}

/**
 * Hook to assign a reviewer to a CRP
 * Sprint 151: CRP workflow - assign reviewer
 */
export function useAssignCrpReviewer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ crpId, data }: { crpId: string; data: CRPAssignRequest }) =>
      assignCrpReviewer(crpId, data),
    onSuccess: (updatedCrp) => {
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: crpKeys.lists() });
      // Update the specific CRP in cache
      queryClient.setQueryData(crpKeys.detail(updatedCrp.id), updatedCrp);
      // Invalidate my-reviews as assignment affects it
      queryClient.invalidateQueries({ queryKey: crpKeys.myReviews() });
    },
  });
}

/**
 * Hook to resolve a CRP (approve/reject/cancel)
 * Sprint 151: CRP workflow - resolution
 */
export function useResolveCrp() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ crpId, data }: { crpId: string; data: CRPResolveRequest }) =>
      resolveCrp(crpId, data),
    onSuccess: (updatedCrp) => {
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: crpKeys.lists() });
      // Update the specific CRP in cache
      queryClient.setQueryData(crpKeys.detail(updatedCrp.id), updatedCrp);
      // Invalidate my-reviews as resolution affects it
      queryClient.invalidateQueries({ queryKey: crpKeys.myReviews() });
    },
  });
}

/**
 * Hook to add a comment to a CRP
 * Sprint 151: CRP discussion
 */
export function useAddCrpComment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ crpId, data }: { crpId: string; data: CRPAddCommentRequest }) =>
      addCrpComment(crpId, data),
    onSuccess: (_, variables) => {
      // Invalidate the specific CRP to refresh comments
      queryClient.invalidateQueries({ queryKey: crpKeys.detail(variables.crpId) });
    },
  });
}

/**
 * Hook to auto-generate CRP content using AI
 * Sprint 151 Day 4: AI-assisted CRP creation
 */
export function useAutoGenerateCrp() {
  return useMutation({
    mutationFn: (request: CRPAutoGenerateRequest) => autoGenerateCrp(request),
  });
}

// Export types for use in components
export type {
  CRP,
  CRPCreate,
  CRPAssignRequest,
  CRPResolveRequest,
  CRPAddCommentRequest,
  CRPListResponse,
  CRPListOptions,
  CRPComment,
  CRPStatus,
  CRPPriority,
  ReviewerExpertise,
  CRPAutoGenerateRequest,
  CRPAutoGenerateResponse,
};
