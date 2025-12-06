/**
 * File: frontend/web/src/hooks/useCouncil.ts
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-04
 * Authority: Frontend Lead + CTO Approved
 * Sprint: 28 - Web Dashboard AI Assistant
 *
 * Description:
 * React Query hooks for AI Council API endpoints.
 * Provides caching, optimistic updates, and error handling.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import type {
  CouncilRecommendRequest,
  CouncilRecommendResponse,
  GateStatusResponse,
  EvidenceChecklistResponse,
  GateType,
} from '@/types/council'

// =========================================================================
// QUERY KEYS
// =========================================================================

export const councilKeys = {
  all: ['council'] as const,
  recommendations: () => [...councilKeys.all, 'recommendations'] as const,
  recommendation: (id: string) => [...councilKeys.recommendations(), id] as const,
  gateStatus: (projectId: string) => [...councilKeys.all, 'gateStatus', projectId] as const,
  evidenceChecklist: (gateType: GateType, projectId: string) =>
    [...councilKeys.all, 'evidenceChecklist', gateType, projectId] as const,
}

// =========================================================================
// API FUNCTIONS
// =========================================================================

async function getCouncilRecommendation(
  request: CouncilRecommendRequest
): Promise<CouncilRecommendResponse> {
  const { data } = await apiClient.post<CouncilRecommendResponse>(
    '/council/recommend',
    request
  )
  return data
}

async function getGateStatus(projectId: string): Promise<GateStatusResponse> {
  const { data } = await apiClient.get<GateStatusResponse>(
    `/projects/${projectId}/gates/status`
  )
  return data
}

async function getEvidenceChecklist(
  gateType: GateType,
  projectId: string
): Promise<EvidenceChecklistResponse> {
  const { data } = await apiClient.get<EvidenceChecklistResponse>(
    `/gates/${gateType}/evidence/checklist`,
    { params: { project_id: projectId } }
  )
  return data
}

// =========================================================================
// HOOKS
// =========================================================================

/**
 * Hook for getting AI Council recommendations
 *
 * @example
 * ```tsx
 * const { mutate: getRecommendation, isLoading, data } = useCouncilRecommend()
 *
 * const handleAsk = (question: string) => {
 *   getRecommendation({
 *     project_id: projectId,
 *     question,
 *     council_mode: true,
 *   })
 * }
 * ```
 */
export function useCouncilRecommend() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: getCouncilRecommendation,
    onSuccess: () => {
      // Invalidate related queries on success
      queryClient.invalidateQueries({ queryKey: councilKeys.recommendations() })

      // Could also invalidate violations if recommendation affects them
      queryClient.invalidateQueries({ queryKey: ['violations'] })
    },
    onError: (error) => {
      console.error('Council recommendation failed:', error)
    },
  })
}

/**
 * Hook for getting gate status for a project
 *
 * @param projectId - Project ID to get gate status for
 * @param options - Query options (enabled, etc)
 *
 * @example
 * ```tsx
 * const { data: gateStatus, isLoading } = useGateStatus(projectId)
 *
 * if (gateStatus) {
 *   console.log('Current gate:', gateStatus.current_gate)
 * }
 * ```
 */
export function useGateStatus(
  projectId: string,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: councilKeys.gateStatus(projectId),
    queryFn: () => getGateStatus(projectId),
    enabled: options?.enabled !== false && !!projectId,
    staleTime: 30_000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes (formerly cacheTime)
  })
}

/**
 * Hook for getting evidence checklist for a gate
 *
 * @param gateType - Gate type (G0.1, G1, etc)
 * @param projectId - Project ID
 * @param options - Query options
 *
 * @example
 * ```tsx
 * const { data: checklist } = useEvidenceChecklist('G2', projectId)
 *
 * if (checklist) {
 *   console.log(`${checklist.uploaded}/${checklist.total} evidence uploaded`)
 * }
 * ```
 */
export function useEvidenceChecklist(
  gateType: GateType,
  projectId: string,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: councilKeys.evidenceChecklist(gateType, projectId),
    queryFn: () => getEvidenceChecklist(gateType, projectId),
    enabled: options?.enabled !== false && !!gateType && !!projectId,
    staleTime: 60_000, // 1 minute
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}

/**
 * Hook for prefetching gate status
 * Use this to warm the cache before navigation
 *
 * @example
 * ```tsx
 * const prefetchGateStatus = usePrefetchGateStatus()
 *
 * const handleProjectHover = (projectId: string) => {
 *   prefetchGateStatus(projectId)
 * }
 * ```
 */
export function usePrefetchGateStatus() {
  const queryClient = useQueryClient()

  return (projectId: string) => {
    queryClient.prefetchQuery({
      queryKey: councilKeys.gateStatus(projectId),
      queryFn: () => getGateStatus(projectId),
      staleTime: 30_000,
    })
  }
}

// =========================================================================
// UTILITY HOOKS
// =========================================================================

/**
 * Hook for invalidating all council-related queries
 * Use after major state changes
 */
export function useInvalidateCouncilQueries() {
  const queryClient = useQueryClient()

  return () => {
    queryClient.invalidateQueries({ queryKey: councilKeys.all })
  }
}
