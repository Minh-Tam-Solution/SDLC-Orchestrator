/**
 * Override React Query Hooks - VCR (Version Controlled Resolution) Flow
 *
 * SDLC Stage: 04 - BUILD
 * Sprint: 43 - Policy Guards & Evidence UI
 * Framework: SDLC 5.1.1
 * Epic: EP-02 AI Safety Layer v1
 *
 * Purpose:
 * React Query hooks for VCR Override API endpoints.
 * Provides data fetching, caching, and mutations for override workflow.
 *
 * Features:
 * - Override request creation
 * - Admin queue management
 * - Approve/reject mutations
 * - Statistics and reporting
 * - Real-time invalidation
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/api/client'
import type {
  OverrideApprovalRequest,
  OverrideCancellationRequest,
  OverrideListFilters,
  OverrideListResponse,
  OverrideRejectionRequest,
  OverrideRequestCreate,
  OverrideResponse,
  OverrideStatsResponse,
  VCRQueueResponse,
} from '@/types/override'
import { evidenceTimelineKeys } from './useEvidenceTimeline'

// =============================================================================
// Query Keys
// =============================================================================

export const overrideKeys = {
  all: ['overrides'] as const,
  lists: () => [...overrideKeys.all, 'list'] as const,
  list: (projectId: string, filters?: OverrideListFilters) =>
    [...overrideKeys.lists(), projectId, filters] as const,
  details: () => [...overrideKeys.all, 'detail'] as const,
  detail: (overrideId: string) => [...overrideKeys.details(), overrideId] as const,
  byEvent: (eventId: string) => [...overrideKeys.all, 'event', eventId] as const,
  adminQueue: (projectId?: string) => [...overrideKeys.all, 'admin-queue', projectId] as const,
  stats: (projectId?: string, days?: number) =>
    [...overrideKeys.all, 'stats', projectId, days] as const,
}

// =============================================================================
// Get Override by ID
// =============================================================================

interface UseOverrideDetailOptions {
  overrideId: string
  enabled?: boolean
}

export function useOverrideDetail({
  overrideId,
  enabled = true,
}: UseOverrideDetailOptions) {
  return useQuery<OverrideResponse, Error>({
    queryKey: overrideKeys.detail(overrideId),
    queryFn: async () => {
      const response = await apiClient.get<OverrideResponse>(
        `/overrides/${overrideId}`
      )
      return response.data
    },
    enabled: enabled && !!overrideId,
    staleTime: 30 * 1000, // 30 seconds
  })
}

// =============================================================================
// Get Override by Event ID
// =============================================================================

interface UseOverrideByEventOptions {
  eventId: string
  enabled?: boolean
}

export function useOverrideByEvent({
  eventId,
  enabled = true,
}: UseOverrideByEventOptions) {
  return useQuery<OverrideResponse | null, Error>({
    queryKey: overrideKeys.byEvent(eventId),
    queryFn: async () => {
      try {
        const response = await apiClient.get<OverrideResponse>(
          `/overrides/event/${eventId}`
        )
        return response.data
      } catch (error: unknown) {
        // 404 means no override exists for this event
        if ((error as { response?: { status: number } }).response?.status === 404) {
          return null
        }
        throw error
      }
    },
    enabled: enabled && !!eventId,
    staleTime: 30 * 1000, // 30 seconds
  })
}

// =============================================================================
// Create Override Request
// =============================================================================

export function useCreateOverrideRequest() {
  const queryClient = useQueryClient()

  return useMutation<OverrideResponse, Error, OverrideRequestCreate>({
    mutationFn: async (request) => {
      const response = await apiClient.post<OverrideResponse>(
        '/overrides/request',
        request
      )
      return response.data
    },
    onSuccess: (data) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: overrideKeys.all })
      queryClient.invalidateQueries({ queryKey: evidenceTimelineKeys.all })
    },
  })
}

// =============================================================================
// Approve Override
// =============================================================================

interface ApproveOverrideParams {
  overrideId: string
  request: OverrideApprovalRequest
}

export function useApproveOverride() {
  const queryClient = useQueryClient()

  return useMutation<OverrideResponse, Error, ApproveOverrideParams>({
    mutationFn: async ({ overrideId, request }) => {
      const response = await apiClient.post<OverrideResponse>(
        `/overrides/${overrideId}/approve`,
        request
      )
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: overrideKeys.all })
      queryClient.invalidateQueries({ queryKey: evidenceTimelineKeys.all })
    },
  })
}

// =============================================================================
// Reject Override
// =============================================================================

interface RejectOverrideParams {
  overrideId: string
  request: OverrideRejectionRequest
}

export function useRejectOverride() {
  const queryClient = useQueryClient()

  return useMutation<OverrideResponse, Error, RejectOverrideParams>({
    mutationFn: async ({ overrideId, request }) => {
      const response = await apiClient.post<OverrideResponse>(
        `/overrides/${overrideId}/reject`,
        request
      )
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: overrideKeys.all })
      queryClient.invalidateQueries({ queryKey: evidenceTimelineKeys.all })
    },
  })
}

// =============================================================================
// Cancel Override
// =============================================================================

interface CancelOverrideParams {
  overrideId: string
  request?: OverrideCancellationRequest
}

export function useCancelOverride() {
  const queryClient = useQueryClient()

  return useMutation<OverrideResponse, Error, CancelOverrideParams>({
    mutationFn: async ({ overrideId, request }) => {
      const response = await apiClient.post<OverrideResponse>(
        `/overrides/${overrideId}/cancel`,
        request ?? {}
      )
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: overrideKeys.all })
      queryClient.invalidateQueries({ queryKey: evidenceTimelineKeys.all })
    },
  })
}

// =============================================================================
// Admin Override Queue
// =============================================================================

interface UseAdminOverrideQueueOptions {
  projectId?: string
  limit?: number
  enabled?: boolean
}

export function useAdminOverrideQueue({
  projectId,
  limit = 20,
  enabled = true,
}: UseAdminOverrideQueueOptions = {}) {
  return useQuery<VCRQueueResponse, Error>({
    queryKey: overrideKeys.adminQueue(projectId),
    queryFn: async () => {
      const params = new URLSearchParams()
      params.set('limit', String(limit))
      if (projectId) params.set('project_id', projectId)

      const response = await apiClient.get<VCRQueueResponse>(
        `/admin/override-queue?${params.toString()}`
      )
      return response.data
    },
    enabled,
    staleTime: 15 * 1000, // 15 seconds - queue should be fresh
    refetchInterval: 60 * 1000, // Refetch every minute
  })
}

// =============================================================================
// Override Statistics
// =============================================================================

interface UseOverrideStatsOptions {
  projectId?: string
  days?: number
  enabled?: boolean
}

export function useOverrideStats({
  projectId,
  days = 30,
  enabled = true,
}: UseOverrideStatsOptions = {}) {
  return useQuery<OverrideStatsResponse, Error>({
    queryKey: overrideKeys.stats(projectId, days),
    queryFn: async () => {
      const params = new URLSearchParams()
      params.set('days', String(days))
      if (projectId) params.set('project_id', projectId)

      const response = await apiClient.get<OverrideStatsResponse>(
        `/admin/override-stats?${params.toString()}`
      )
      return response.data
    },
    enabled,
    staleTime: 60 * 1000, // 1 minute
  })
}

// =============================================================================
// Project Overrides List
// =============================================================================

interface UseProjectOverridesOptions {
  projectId: string
  filters?: OverrideListFilters
  page?: number
  limit?: number
  enabled?: boolean
}

export function useProjectOverrides({
  projectId,
  filters = {},
  page = 1,
  limit = 20,
  enabled = true,
}: UseProjectOverridesOptions) {
  return useQuery<OverrideListResponse, Error>({
    queryKey: overrideKeys.list(projectId, filters),
    queryFn: async () => {
      const params = new URLSearchParams()
      params.set('page', String(page))
      params.set('limit', String(limit))

      // Add filters
      if (filters.status) params.set('status', filters.status)
      if (filters.override_type) params.set('override_type', filters.override_type)
      if (filters.requested_by_id) params.set('requested_by_id', filters.requested_by_id)
      if (filters.date_start) params.set('date_start', filters.date_start)
      if (filters.date_end) params.set('date_end', filters.date_end)
      if (filters.pr_number) params.set('pr_number', filters.pr_number)

      const response = await apiClient.get<OverrideListResponse>(
        `/projects/${projectId}/overrides?${params.toString()}`
      )
      return response.data
    },
    enabled: enabled && !!projectId,
    staleTime: 30 * 1000, // 30 seconds
  })
}

// =============================================================================
// Invalidation Helpers
// =============================================================================

export function useInvalidateOverrides() {
  const queryClient = useQueryClient()

  return {
    invalidateAll: () => {
      queryClient.invalidateQueries({ queryKey: overrideKeys.all })
      queryClient.invalidateQueries({ queryKey: evidenceTimelineKeys.all })
    },
    invalidateQueue: () => {
      queryClient.invalidateQueries({ queryKey: overrideKeys.adminQueue() })
    },
    invalidateStats: () => {
      queryClient.invalidateQueries({ queryKey: overrideKeys.stats() })
    },
    invalidateByProject: (projectId: string) => {
      queryClient.invalidateQueries({ queryKey: overrideKeys.list(projectId) })
      queryClient.invalidateQueries({ queryKey: overrideKeys.stats(projectId) })
    },
  }
}

// =============================================================================
// Prefetch Helpers
// =============================================================================

export function usePrefetchOverride() {
  const queryClient = useQueryClient()

  return async (overrideId: string) => {
    await queryClient.prefetchQuery({
      queryKey: overrideKeys.detail(overrideId),
      queryFn: async () => {
        const response = await apiClient.get<OverrideResponse>(
          `/overrides/${overrideId}`
        )
        return response.data
      },
      staleTime: 30 * 1000,
    })
  }
}
