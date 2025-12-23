/**
 * Evidence Timeline Main Component
 *
 * SDLC Stage: 04 - BUILD
 * Sprint: 43 - Policy Guards & Evidence UI
 * Framework: SDLC 5.1.1
 * Epic: EP-02 AI Safety Layer v1
 *
 * Purpose:
 * Main container component for the Evidence Timeline feature.
 * Orchestrates all sub-components and handles state management.
 *
 * Features:
 * - Timeline listing with infinite scroll
 * - Filter panel with search, date range, AI tool, status
 * - Stats bar with key metrics
 * - Event detail modal
 * - Override request modal
 * - Export functionality
 */

import { useState, useCallback, useEffect, useRef } from 'react'
import { useInView } from 'react-intersection-observer'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import TimelineStatsBar from './TimelineStatsBar'
import TimelineFilterPanel from './TimelineFilterPanel'
import TimelineEventCard from './TimelineEventCard'
import EventDetailModal from './EventDetailModal'
import OverrideRequestModal from './OverrideRequestModal'
import {
  useEvidenceTimeline,
  useTimelineStats,
  useEventDetail,
  useRequestOverride,
  useExportTimeline,
  usePrefetchEventDetail,
} from '@/hooks/useEvidenceTimeline'
import {
  ExportFormat,
  type EvidenceFilters,
  type EvidenceEventSummary,
} from '@/types/evidence-timeline'

interface EvidenceTimelineProps {
  projectId: string
}

export default function EvidenceTimeline({ projectId }: EvidenceTimelineProps) {
  // Filter state
  const [filters, setFilters] = useState<EvidenceFilters>({})

  // Modal state
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null)
  const [overrideEventId, setOverrideEventId] = useState<string | null>(null)
  const [overridePrNumber, setOverridePrNumber] = useState<string>('')

  // Infinite scroll ref
  const { ref: loadMoreRef, inView } = useInView()

  // Queries
  const {
    data: timelineData,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading: isLoadingTimeline,
    error: timelineError,
  } = useEvidenceTimeline({ projectId, filters })

  const { data: stats, isLoading: isLoadingStats } = useTimelineStats({
    projectId,
    days: 30,
  })

  const { data: eventDetail, isLoading: isLoadingDetail } = useEventDetail({
    projectId,
    eventId: selectedEventId || '',
    enabled: !!selectedEventId,
  })

  // Mutations
  const requestOverrideMutation = useRequestOverride()
  const exportMutation = useExportTimeline()

  // Prefetch
  const prefetchEventDetail = usePrefetchEventDetail()

  // Load more when scrolling to bottom
  useEffect(() => {
    if (inView && hasNextPage && !isFetchingNextPage) {
      fetchNextPage()
    }
  }, [inView, hasNextPage, isFetchingNextPage, fetchNextPage])

  // Flatten paginated data
  const events: EvidenceEventSummary[] = timelineData?.pages.flatMap((page) => page.events) || []

  // Handlers
  const handleFiltersChange = useCallback((newFilters: EvidenceFilters) => {
    setFilters(newFilters)
  }, [])

  const handleClearFilters = useCallback(() => {
    setFilters({})
  }, [])

  const handleViewDetail = useCallback((eventId: string) => {
    setSelectedEventId(eventId)
  }, [])

  const handleRequestOverride = useCallback((eventId: string) => {
    const event = events.find((e) => e.id === eventId)
    if (event) {
      setOverrideEventId(eventId)
      setOverridePrNumber(event.pr_number)
    }
  }, [events])

  const handlePrefetch = useCallback((eventId: string) => {
    prefetchEventDetail(projectId, eventId)
  }, [projectId, prefetchEventDetail])

  const handleOverrideSubmit = useCallback((eventId: string, request: { override_type: string; reason: string }) => {
    requestOverrideMutation.mutate(
      { eventId, request: request as any },
      {
        onSuccess: () => {
          setOverrideEventId(null)
          setOverridePrNumber('')
        },
      }
    )
  }, [requestOverrideMutation])

  const handleExport = useCallback((format: ExportFormat) => {
    exportMutation.mutate({
      projectId,
      format,
      dateStart: filters.date_start,
      dateEnd: filters.date_end,
    })
  }, [projectId, filters, exportMutation])

  // Error state
  if (timelineError) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <svg className="h-12 w-12 text-red-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to load timeline</h3>
        <p className="text-sm text-muted-foreground mb-4">{timelineError.message}</p>
        <Button onClick={() => window.location.reload()}>Retry</Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Evidence Timeline</h1>
          <p className="text-muted-foreground">
            AI code detection events and validation results
          </p>
        </div>

        {/* Export Button */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => handleExport(ExportFormat.CSV)}
            disabled={exportMutation.isPending}
          >
            <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Export CSV
          </Button>
          <Button
            variant="outline"
            onClick={() => handleExport(ExportFormat.JSON)}
            disabled={exportMutation.isPending}
          >
            <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Export JSON
          </Button>
        </div>
      </div>

      {/* Stats Bar */}
      <TimelineStatsBar stats={stats} isLoading={isLoadingStats} />

      {/* Filter Panel */}
      <TimelineFilterPanel
        filters={filters}
        onFiltersChange={handleFiltersChange}
        onClear={handleClearFilters}
      />

      {/* Timeline Events */}
      <div className="space-y-4">
        {isLoadingTimeline ? (
          // Loading skeletons
          Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="p-4 border rounded-lg">
              <div className="flex items-start justify-between">
                <div className="space-y-2">
                  <Skeleton className="h-5 w-32" />
                  <Skeleton className="h-4 w-64" />
                  <Skeleton className="h-3 w-48" />
                </div>
                <Skeleton className="h-6 w-20" />
              </div>
            </div>
          ))
        ) : events.length === 0 ? (
          // Empty state
          <div className="flex flex-col items-center justify-center py-12 border rounded-lg">
            <svg className="h-12 w-12 text-muted-foreground mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <h3 className="text-lg font-medium mb-2">No events found</h3>
            <p className="text-sm text-muted-foreground text-center max-w-sm">
              {Object.keys(filters).length > 0
                ? 'Try adjusting your filters to see more results.'
                : 'No AI code events have been detected for this project yet.'}
            </p>
          </div>
        ) : (
          // Event cards
          events.map((event) => (
            <TimelineEventCard
              key={event.id}
              event={event}
              onViewDetail={handleViewDetail}
              onRequestOverride={handleRequestOverride}
              onPrefetch={handlePrefetch}
            />
          ))
        )}

        {/* Load More Trigger */}
        {hasNextPage && (
          <div ref={loadMoreRef} className="flex justify-center py-4">
            {isFetchingNextPage ? (
              <div className="flex items-center gap-2 text-muted-foreground">
                <svg className="h-5 w-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Loading more...
              </div>
            ) : (
              <Button variant="ghost" onClick={() => fetchNextPage()}>
                Load More
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Event Detail Modal */}
      <EventDetailModal
        open={!!selectedEventId}
        onOpenChange={(open) => !open && setSelectedEventId(null)}
        event={eventDetail}
        isLoading={isLoadingDetail}
        onRequestOverride={
          selectedEventId
            ? () => handleRequestOverride(selectedEventId)
            : undefined
        }
      />

      {/* Override Request Modal */}
      <OverrideRequestModal
        open={!!overrideEventId}
        onOpenChange={(open) => {
          if (!open) {
            setOverrideEventId(null)
            setOverridePrNumber('')
          }
        }}
        eventId={overrideEventId || ''}
        prNumber={overridePrNumber}
        onSubmit={handleOverrideSubmit}
        isSubmitting={requestOverrideMutation.isPending}
        error={requestOverrideMutation.error?.message}
      />
    </div>
  )
}
