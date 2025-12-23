/**
 * Evidence Timeline React Query Hooks
 *
 * SDLC Stage: 04 - BUILD
 * Sprint: 43 - Policy Guards & Evidence UI
 * Framework: SDLC 5.1.1
 * Epic: EP-02 AI Safety Layer v1
 *
 * Purpose:
 * React Query hooks for Evidence Timeline API endpoints.
 * Provides data fetching, caching, and mutations.
 *
 * Features:
 * - Timeline listing with infinite scroll
 * - Event detail fetching
 * - Statistics aggregation
 * - Override request mutations
 * - Export functionality
 */

import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/api/client'
import type {
  EvidenceEventDetail,
  EvidenceFilters,
  EvidenceTimelineResponse,
  EvidenceTimelineStats,
  ExportFormat,
  OverrideApproval,
  OverrideQueueResponse,
  OverrideRecord,
  OverrideRejection,
  OverrideRequest,
} from '@/types/evidence-timeline'

// =============================================================================
// Query Keys
// =============================================================================

export const evidenceTimelineKeys = {
  all: ['evidence-timeline'] as const,
  lists: () => [...evidenceTimelineKeys.all, 'list'] as const,
  list: (projectId: string, filters?: EvidenceFilters) =>
    [...evidenceTimelineKeys.lists(), projectId, filters] as const,
  stats: (projectId: string, days?: number) =>
    [...evidenceTimelineKeys.all, 'stats', projectId, days] as const,
  details: () => [...evidenceTimelineKeys.all, 'detail'] as const,
  detail: (projectId: string, eventId: string) =>
    [...evidenceTimelineKeys.details(), projectId, eventId] as const,
  overrideQueue: () => [...evidenceTimelineKeys.all, 'override-queue'] as const,
}

// =============================================================================
// Timeline List Hook (with Infinite Scroll)
// =============================================================================

interface UseEvidenceTimelineOptions {
  projectId: string
  filters?: EvidenceFilters
  limit?: number
  enabled?: boolean
}

export function useEvidenceTimeline({
  projectId,
  filters = {},
  limit = 20,
  enabled = true,
}: UseEvidenceTimelineOptions) {
  return useInfiniteQuery<EvidenceTimelineResponse, Error>({
    queryKey: evidenceTimelineKeys.list(projectId, filters),
    queryFn: async ({ pageParam = 1 }) => {
      const params = new URLSearchParams()
      params.set('page', String(pageParam))
      params.set('limit', String(limit))

      // Add filters
      if (filters.date_start) params.set('date_start', filters.date_start)
      if (filters.date_end) params.set('date_end', filters.date_end)
      if (filters.ai_tool) params.set('ai_tool', filters.ai_tool)
      if (filters.validation_status) params.set('validation_status', filters.validation_status)
      if (filters.search) params.set('search', filters.search)

      const response = await apiClient.get<EvidenceTimelineResponse>(
        `/projects/${projectId}/timeline?${params.toString()}`
      )
      return response.data
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      if (lastPage.has_next) {
        return lastPage.page + 1
      }
      return undefined
    },
    enabled: enabled && !!projectId,
    staleTime: 30 * 1000, // 30 seconds
  })
}

// =============================================================================
// Timeline Stats Hook
// =============================================================================

interface UseTimelineStatsOptions {
  projectId: string
  days?: number
  enabled?: boolean
}

export function useTimelineStats({
  projectId,
  days = 30,
  enabled = true,
}: UseTimelineStatsOptions) {
  return useQuery<EvidenceTimelineStats, Error>({
    queryKey: evidenceTimelineKeys.stats(projectId, days),
    queryFn: async () => {
      const response = await apiClient.get<EvidenceTimelineStats>(
        `/projects/${projectId}/timeline/stats?days=${days}`
      )
      return response.data
    },
    enabled: enabled && !!projectId,
    staleTime: 60 * 1000, // 1 minute
  })
}

// =============================================================================
// Event Detail Hook
// =============================================================================

interface UseEventDetailOptions {
  projectId: string
  eventId: string
  enabled?: boolean
}

export function useEventDetail({
  projectId,
  eventId,
  enabled = true,
}: UseEventDetailOptions) {
  return useQuery<EvidenceEventDetail, Error>({
    queryKey: evidenceTimelineKeys.detail(projectId, eventId),
    queryFn: async () => {
      const response = await apiClient.get<EvidenceEventDetail>(
        `/projects/${projectId}/timeline/${eventId}`
      )
      return response.data
    },
    enabled: enabled && !!projectId && !!eventId,
    staleTime: 30 * 1000, // 30 seconds
  })
}

// =============================================================================
// Override Request Mutation
// =============================================================================

interface RequestOverrideParams {
  eventId: string
  request: OverrideRequest
}

export function useRequestOverride() {
  const queryClient = useQueryClient()

  return useMutation<OverrideRecord, Error, RequestOverrideParams>({
    mutationFn: async ({ eventId, request }) => {
      const response = await apiClient.post<OverrideRecord>(
        `/timeline/${eventId}/override/request`,
        request
      )
      return response.data
    },
    onSuccess: (_, variables) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: evidenceTimelineKeys.all })
    },
  })
}

// =============================================================================
// Override Approve Mutation
// =============================================================================

interface ApproveOverrideParams {
  eventId: string
  approval: OverrideApproval
}

export function useApproveOverride() {
  const queryClient = useQueryClient()

  return useMutation<OverrideRecord, Error, ApproveOverrideParams>({
    mutationFn: async ({ eventId, approval }) => {
      const response = await apiClient.post<OverrideRecord>(
        `/timeline/${eventId}/override/approve`,
        approval
      )
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: evidenceTimelineKeys.all })
    },
  })
}

// =============================================================================
// Override Reject Mutation
// =============================================================================

interface RejectOverrideParams {
  eventId: string
  rejection: OverrideRejection
}

export function useRejectOverride() {
  const queryClient = useQueryClient()

  return useMutation<OverrideRecord, Error, RejectOverrideParams>({
    mutationFn: async ({ eventId, rejection }) => {
      const response = await apiClient.post<OverrideRecord>(
        `/timeline/${eventId}/override/reject`,
        rejection
      )
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: evidenceTimelineKeys.all })
    },
  })
}

// =============================================================================
// Override Queue Hook (Admin)
// =============================================================================

export function useOverrideQueue(enabled = true) {
  return useQuery<OverrideQueueResponse, Error>({
    queryKey: evidenceTimelineKeys.overrideQueue(),
    queryFn: async () => {
      const response = await apiClient.get<OverrideQueueResponse>('/admin/override-queue')
      return response.data
    },
    enabled,
    staleTime: 30 * 1000, // 30 seconds
  })
}

// =============================================================================
// Export Timeline Mutation
// =============================================================================

interface ExportTimelineParams {
  projectId: string
  format: ExportFormat
  dateStart?: string
  dateEnd?: string
  includeDetails?: boolean
}

export function useExportTimeline() {
  return useMutation<Blob, Error, ExportTimelineParams>({
    mutationFn: async ({ projectId, format, dateStart, dateEnd, includeDetails }) => {
      const params = new URLSearchParams()
      params.set('format', format)
      if (dateStart) params.set('date_start', dateStart)
      if (dateEnd) params.set('date_end', dateEnd)
      if (includeDetails) params.set('include_details', 'true')

      const response = await apiClient.get(
        `/projects/${projectId}/timeline/export?${params.toString()}`,
        {
          responseType: 'blob',
        }
      )
      return response.data
    },
    onSuccess: (blob, variables) => {
      // Create download link
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `evidence-timeline-${variables.projectId}-${new Date().toISOString().split('T')[0]}.${variables.format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    },
  })
}

// =============================================================================
// Prefetch Helpers
// =============================================================================

export function usePrefetchEventDetail() {
  const queryClient = useQueryClient()

  return async (projectId: string, eventId: string) => {
    await queryClient.prefetchQuery({
      queryKey: evidenceTimelineKeys.detail(projectId, eventId),
      queryFn: async () => {
        const response = await apiClient.get<EvidenceEventDetail>(
          `/projects/${projectId}/timeline/${eventId}`
        )
        return response.data
      },
      staleTime: 30 * 1000,
    })
  }
}
