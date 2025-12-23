/**
 * Admin Override Queue Page Component
 *
 * SDLC Stage: 04 - BUILD
 * Sprint: 43 - Policy Guards & Evidence UI
 * Framework: SDLC 5.1.1
 * Epic: EP-02 AI Safety Layer v1
 *
 * Purpose:
 * Admin page for managing pending override requests.
 * Displays queue of pending overrides with approve/reject actions.
 *
 * Features:
 * - Pending override queue
 * - Recent decisions history
 * - Quick approve/reject actions
 * - Override statistics
 * - Filtering by project
 */

import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { formatDistanceToNow, format } from 'date-fns'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import apiClient from '@/api/client'

// =============================================================================
// Types
// =============================================================================

interface OverrideItem {
  id: string
  event_id: string
  project_id: string
  override_type: string
  reason: string
  status: string
  requested_by_id: string | null
  requested_by_name: string | null
  requested_at: string
  resolved_by_id: string | null
  resolved_by_name: string | null
  resolved_at: string | null
  resolution_comment: string | null
  pr_number: string | null
  pr_title: string | null
  failed_validators: string[] | null
  expires_at: string | null
  is_expired: boolean
  post_merge_review_required: boolean
  created_at: string
}

interface OverrideQueueResponse {
  pending: OverrideItem[]
  recent_decisions: OverrideItem[]
  total_pending: number
}

interface OverrideStatsResponse {
  total: number
  by_status: Record<string, number>
  by_type: Record<string, number>
  approval_rate: number
  pending: number
  days: number
}

// =============================================================================
// API Hooks
// =============================================================================

function useOverrideQueue() {
  return useQuery<OverrideQueueResponse>({
    queryKey: ['admin', 'override-queue'],
    queryFn: async () => {
      const response = await apiClient.get<OverrideQueueResponse>('/admin/override-queue')
      return response.data
    },
    staleTime: 30 * 1000,
  })
}

function useOverrideStats(days = 30) {
  return useQuery<OverrideStatsResponse>({
    queryKey: ['admin', 'override-stats', days],
    queryFn: async () => {
      const response = await apiClient.get<OverrideStatsResponse>(
        `/admin/override-stats?days=${days}`
      )
      return response.data
    },
    staleTime: 60 * 1000,
  })
}

function useApproveOverride() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ overrideId, comment }: { overrideId: string; comment?: string }) => {
      const response = await apiClient.post(`/overrides/${overrideId}/approve`, { comment })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'override-queue'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'override-stats'] })
    },
  })
}

function useRejectOverride() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ overrideId, reason }: { overrideId: string; reason: string }) => {
      const response = await apiClient.post(`/overrides/${overrideId}/reject`, { reason })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'override-queue'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'override-stats'] })
    },
  })
}

// =============================================================================
// Stats Card Component
// =============================================================================

function StatsCards({ stats, isLoading }: { stats?: OverrideStatsResponse; isLoading: boolean }) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardContent className="p-4">
              <Skeleton className="h-4 w-20 mb-2" />
              <Skeleton className="h-8 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (!stats) return null

  const items = [
    {
      label: 'Pending',
      value: stats.pending,
      color: stats.pending > 0 ? 'text-orange-600' : 'text-green-600',
      bgColor: stats.pending > 0 ? 'bg-orange-50' : 'bg-green-50',
    },
    {
      label: 'Total (30d)',
      value: stats.total,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      label: 'Approval Rate',
      value: `${stats.approval_rate.toFixed(1)}%`,
      color: stats.approval_rate >= 70 ? 'text-green-600' : 'text-yellow-600',
      bgColor: stats.approval_rate >= 70 ? 'bg-green-50' : 'bg-yellow-50',
    },
    {
      label: 'By Type',
      value: Object.entries(stats.by_type)
        .map(([k, v]) => `${k}: ${v}`)
        .join(', ') || 'None',
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      isSmall: true,
    },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      {items.map((item) => (
        <Card key={item.label} className={item.bgColor}>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">{item.label}</p>
            <p className={`${item.isSmall ? 'text-sm' : 'text-2xl'} font-bold ${item.color}`}>
              {item.value}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

// =============================================================================
// Override Card Component
// =============================================================================

interface OverrideCardProps {
  override: OverrideItem
  onApprove: (id: string) => void
  onReject: (id: string) => void
  isPending?: boolean
}

function OverrideCard({ override, onApprove, onReject, isPending }: OverrideCardProps) {
  const getTypeBadge = () => {
    const colors: Record<string, string> = {
      false_positive: 'bg-blue-100 text-blue-800',
      approved_risk: 'bg-yellow-100 text-yellow-800',
      emergency: 'bg-red-100 text-red-800',
    }
    return (
      <Badge className={colors[override.override_type] || 'bg-gray-100 text-gray-800'}>
        {override.override_type.replace('_', ' ')}
      </Badge>
    )
  }

  const getStatusBadge = () => {
    const colors: Record<string, string> = {
      pending: 'bg-orange-100 text-orange-800',
      approved: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
      expired: 'bg-gray-100 text-gray-800',
      cancelled: 'bg-gray-100 text-gray-800',
    }
    return (
      <Badge className={colors[override.status] || 'bg-gray-100 text-gray-800'}>
        {override.status}
      </Badge>
    )
  }

  return (
    <Card className={override.post_merge_review_required ? 'border-red-300' : ''}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="font-semibold">PR #{override.pr_number || 'N/A'}</span>
              {getTypeBadge()}
              {getStatusBadge()}
              {override.post_merge_review_required && (
                <Badge variant="destructive" className="text-xs">
                  POST-MERGE REVIEW
                </Badge>
              )}
            </div>

            <p className="text-sm text-muted-foreground mb-2">{override.pr_title}</p>

            <div className="bg-muted/50 p-3 rounded-lg mb-3">
              <p className="text-sm font-medium mb-1">Justification:</p>
              <p className="text-sm text-muted-foreground">{override.reason}</p>
            </div>

            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span>By: {override.requested_by_name || 'Unknown'}</span>
              <span>
                {formatDistanceToNow(new Date(override.requested_at), { addSuffix: true })}
              </span>
              {override.failed_validators && override.failed_validators.length > 0 && (
                <span>
                  Failed: {override.failed_validators.join(', ')}
                </span>
              )}
              {override.expires_at && override.status === 'pending' && (
                <span className="text-orange-600">
                  Expires: {format(new Date(override.expires_at), 'MMM d, yyyy')}
                </span>
              )}
            </div>

            {override.status !== 'pending' && override.resolved_at && (
              <div className="mt-2 text-xs text-muted-foreground">
                {override.status === 'approved' ? 'Approved' : 'Rejected'} by{' '}
                {override.resolved_by_name || 'Unknown'}{' '}
                {formatDistanceToNow(new Date(override.resolved_at), { addSuffix: true })}
                {override.resolution_comment && (
                  <span className="block mt-1 italic">"{override.resolution_comment}"</span>
                )}
              </div>
            )}
          </div>

          {isPending && override.status === 'pending' && (
            <div className="flex flex-col gap-2">
              <Button
                size="sm"
                className="bg-green-600 hover:bg-green-700"
                onClick={() => onApprove(override.id)}
              >
                <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Approve
              </Button>
              <Button
                size="sm"
                variant="destructive"
                onClick={() => onReject(override.id)}
              >
                <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                Reject
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

// =============================================================================
// Main Component
// =============================================================================

export default function OverrideQueuePage() {
  const [selectedOverride, setSelectedOverride] = useState<string | null>(null)
  const [actionType, setActionType] = useState<'approve' | 'reject' | null>(null)
  const [comment, setComment] = useState('')

  const { data: queue, isLoading: isLoadingQueue, error: queueError } = useOverrideQueue()
  const { data: stats, isLoading: isLoadingStats } = useOverrideStats()

  const approveMutation = useApproveOverride()
  const rejectMutation = useRejectOverride()

  const handleApprove = useCallback((overrideId: string) => {
    setSelectedOverride(overrideId)
    setActionType('approve')
    setComment('')
  }, [])

  const handleReject = useCallback((overrideId: string) => {
    setSelectedOverride(overrideId)
    setActionType('reject')
    setComment('')
  }, [])

  const handleConfirmAction = useCallback(async () => {
    if (!selectedOverride || !actionType) return

    if (actionType === 'approve') {
      await approveMutation.mutateAsync({
        overrideId: selectedOverride,
        comment: comment || undefined,
      })
    } else {
      if (comment.length < 10) {
        alert('Rejection reason must be at least 10 characters')
        return
      }
      await rejectMutation.mutateAsync({
        overrideId: selectedOverride,
        reason: comment,
      })
    }

    setSelectedOverride(null)
    setActionType(null)
    setComment('')
  }, [selectedOverride, actionType, comment, approveMutation, rejectMutation])

  const handleCloseDialog = useCallback(() => {
    setSelectedOverride(null)
    setActionType(null)
    setComment('')
  }, [])

  if (queueError) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Failed to load override queue: {(queueError as Error).message}
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Override Approval Queue</h1>
        <p className="text-muted-foreground">
          Review and approve/reject override requests for failed validations
        </p>
      </div>

      {/* Stats */}
      <StatsCards stats={stats} isLoading={isLoadingStats} />

      {/* Tabs */}
      <Tabs defaultValue="pending">
        <TabsList>
          <TabsTrigger value="pending" className="relative">
            Pending
            {queue && queue.total_pending > 0 && (
              <span className="ml-2 px-2 py-0.5 text-xs bg-orange-500 text-white rounded-full">
                {queue.total_pending}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="recent">Recent Decisions</TabsTrigger>
        </TabsList>

        <TabsContent value="pending" className="space-y-4 mt-4">
          {isLoadingQueue ? (
            Array.from({ length: 3 }).map((_, i) => (
              <Card key={i}>
                <CardContent className="p-4">
                  <Skeleton className="h-4 w-32 mb-2" />
                  <Skeleton className="h-20 w-full mb-2" />
                  <Skeleton className="h-4 w-48" />
                </CardContent>
              </Card>
            ))
          ) : queue?.pending.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <svg
                  className="h-12 w-12 text-green-500 mx-auto mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <h3 className="text-lg font-medium mb-2">Queue is empty!</h3>
                <p className="text-muted-foreground">
                  No pending override requests at this time.
                </p>
              </CardContent>
            </Card>
          ) : (
            queue?.pending.map((override) => (
              <OverrideCard
                key={override.id}
                override={override}
                onApprove={handleApprove}
                onReject={handleReject}
                isPending
              />
            ))
          )}
        </TabsContent>

        <TabsContent value="recent" className="space-y-4 mt-4">
          {isLoadingQueue ? (
            Array.from({ length: 3 }).map((_, i) => (
              <Card key={i}>
                <CardContent className="p-4">
                  <Skeleton className="h-4 w-32 mb-2" />
                  <Skeleton className="h-16 w-full" />
                </CardContent>
              </Card>
            ))
          ) : queue?.recent_decisions.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <p className="text-muted-foreground">No recent decisions.</p>
              </CardContent>
            </Card>
          ) : (
            queue?.recent_decisions.map((override) => (
              <OverrideCard
                key={override.id}
                override={override}
                onApprove={() => {}}
                onReject={() => {}}
              />
            ))
          )}
        </TabsContent>
      </Tabs>

      {/* Approve/Reject Dialog */}
      <Dialog open={!!selectedOverride} onOpenChange={(open) => !open && handleCloseDialog()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {actionType === 'approve' ? 'Approve Override' : 'Reject Override'}
            </DialogTitle>
            <DialogDescription>
              {actionType === 'approve'
                ? 'Add an optional comment for the approval.'
                : 'Provide a reason for rejecting this override request.'}
            </DialogDescription>
          </DialogHeader>

          <div className="py-4">
            <Label htmlFor="comment">
              {actionType === 'approve' ? 'Comment (optional)' : 'Rejection Reason (required)'}
            </Label>
            <Textarea
              id="comment"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder={
                actionType === 'approve'
                  ? 'Optional approval comment...'
                  : 'Why is this override being rejected?'
              }
              className="mt-2"
              rows={4}
            />
            {actionType === 'reject' && comment.length < 10 && comment.length > 0 && (
              <p className="text-xs text-red-500 mt-1">
                Reason must be at least 10 characters ({10 - comment.length} more needed)
              </p>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={handleCloseDialog}>
              Cancel
            </Button>
            <Button
              onClick={handleConfirmAction}
              disabled={
                (actionType === 'reject' && comment.length < 10) ||
                approveMutation.isPending ||
                rejectMutation.isPending
              }
              className={actionType === 'approve' ? 'bg-green-600 hover:bg-green-700' : ''}
              variant={actionType === 'reject' ? 'destructive' : 'default'}
            >
              {(approveMutation.isPending || rejectMutation.isPending) ? (
                <>
                  <svg
                    className="mr-2 h-4 w-4 animate-spin"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                  Processing...
                </>
              ) : actionType === 'approve' ? (
                'Confirm Approval'
              ) : (
                'Confirm Rejection'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
