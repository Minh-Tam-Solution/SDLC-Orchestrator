/**
 * Event Detail Modal Component
 *
 * SDLC Stage: 04 - BUILD
 * Sprint: 43 - Policy Guards & Evidence UI
 * Framework: SDLC 5.1.1
 * Epic: EP-02 AI Safety Layer v1
 *
 * Purpose:
 * Modal dialog displaying detailed information about an AI code event:
 * - Full event metadata
 * - Individual validator results
 * - Detection evidence
 * - Override history
 * - Action buttons (request override, view PR)
 */

import { formatDistanceToNow, format } from 'date-fns'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'
import {
  AIToolLabels,
  ValidationStatus,
  ValidationStatusColors,
  type EvidenceEventDetail,
  type ValidatorResultSummary,
} from '@/types/evidence-timeline'

interface EventDetailModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  event: EvidenceEventDetail | undefined
  isLoading: boolean
  onRequestOverride?: () => void
}

export default function EventDetailModal({
  open,
  onOpenChange,
  event,
  isLoading,
  onRequestOverride,
}: EventDetailModalProps) {
  if (isLoading) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-72 mt-2" />
          </DialogHeader>
          <div className="space-y-4 py-4">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  if (!event) {
    return null
  }

  // Get status badge
  const getStatusBadge = (status: ValidationStatus) => {
    const color = ValidationStatusColors[status]
    const colorClasses = {
      green: 'bg-green-100 text-green-800',
      red: 'bg-red-100 text-red-800',
      yellow: 'bg-yellow-100 text-yellow-800',
      gray: 'bg-gray-100 text-gray-800',
      blue: 'bg-blue-100 text-blue-800',
    }
    return <Badge className={colorClasses[color]}>{status}</Badge>
  }

  // Get validator status icon
  const getValidatorIcon = (status: string) => {
    switch (status) {
      case 'passed':
        return (
          <svg className="h-5 w-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      case 'failed':
        return (
          <svg className="h-5 w-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      case 'skipped':
        return (
          <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        )
      default:
        return (
          <svg className="h-5 w-5 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        )
    }
  }

  // Render validator result row
  const ValidatorRow = ({ result }: { result: ValidatorResultSummary }) => (
    <div className={`flex items-center justify-between p-3 rounded-lg ${
      result.status === 'failed' ? 'bg-red-50' : 'bg-muted/50'
    }`}>
      <div className="flex items-center gap-3">
        {getValidatorIcon(result.status)}
        <div>
          <p className="font-medium capitalize">{result.name.replace('_', ' ')}</p>
          {result.message && (
            <p className="text-sm text-muted-foreground">{result.message}</p>
          )}
        </div>
      </div>
      <div className="text-right">
        <Badge variant={result.blocking ? 'destructive' : 'secondary'} className="text-xs">
          {result.blocking ? 'Blocking' : 'Non-blocking'}
        </Badge>
        <p className="text-xs text-muted-foreground mt-1">{result.duration_ms}ms</p>
      </div>
    </div>
  )

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <span className="text-xl">PR #{event.pr_number}</span>
            {getStatusBadge(event.validation_status)}
          </DialogTitle>
          <DialogDescription>{event.pr_title}</DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="overview" className="mt-4">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="validators">Validators</TabsTrigger>
            <TabsTrigger value="detection">Detection</TabsTrigger>
            <TabsTrigger value="history">History</TabsTrigger>
          </TabsList>

          <ScrollArea className="h-[400px] mt-4">
            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-6">
              {/* PR Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-2">PR Information</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">Author</span>
                      <span className="text-sm font-medium">{event.pr_author}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Branch</span>
                      <span className="text-sm font-medium">{event.branch_name || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Commit</span>
                      <span className="text-sm font-mono">{event.commit_sha?.slice(0, 8) || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Created</span>
                      <span className="text-sm">{format(new Date(event.created_at), 'PPpp')}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-2">Changes</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">Files Changed</span>
                      <span className="text-sm font-medium">{event.files_changed}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Lines Added</span>
                      <span className="text-sm font-medium text-green-600">+{event.lines_added}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Lines Deleted</span>
                      <span className="text-sm font-medium text-red-600">-{event.lines_deleted}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Validation Time</span>
                      <span className="text-sm font-medium">{event.validation_duration_ms}ms</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* AI Detection Summary */}
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">AI Detection</h4>
                <div className="p-4 rounded-lg bg-muted/50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-full bg-purple-100">
                        <svg className="h-5 w-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                      </div>
                      <div>
                        <p className="font-medium">{AIToolLabels[event.ai_tool]}</p>
                        <p className="text-sm text-muted-foreground">
                          {event.detection_method} detection
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold">{event.confidence_score}%</p>
                      <p className="text-xs text-muted-foreground">confidence</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Validator Summary */}
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">Validation Summary</h4>
                <div className="flex items-center gap-4">
                  <div className="flex-1 bg-green-100 rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-green-700">{event.validators_passed}</p>
                    <p className="text-xs text-green-600">Passed</p>
                  </div>
                  <div className="flex-1 bg-red-100 rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-red-700">{event.validators_failed}</p>
                    <p className="text-xs text-red-600">Failed</p>
                  </div>
                  <div className="flex-1 bg-gray-100 rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-gray-700">{event.validators_total}</p>
                    <p className="text-xs text-gray-600">Total</p>
                  </div>
                </div>
              </div>
            </TabsContent>

            {/* Validators Tab */}
            <TabsContent value="validators" className="space-y-3">
              {event.validator_results.length > 0 ? (
                event.validator_results.map((result, index) => (
                  <ValidatorRow key={index} result={result} />
                ))
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  No validator results available
                </p>
              )}
            </TabsContent>

            {/* Detection Tab */}
            <TabsContent value="detection" className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">Detection Evidence</h4>
                <pre className="p-4 rounded-lg bg-muted text-sm overflow-x-auto">
                  {JSON.stringify(event.detection_evidence, null, 2)}
                </pre>
              </div>

              {event.github_pr_url && (
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-2">GitHub</h4>
                  <a
                    href={event.github_pr_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-primary hover:underline"
                  >
                    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                      <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                    </svg>
                    View on GitHub
                  </a>
                </div>
              )}
            </TabsContent>

            {/* History Tab */}
            <TabsContent value="history" className="space-y-4">
              {event.override_history.length > 0 ? (
                event.override_history.map((record) => (
                  <div
                    key={record.id}
                    className="p-4 rounded-lg border"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <Badge>{record.override_type}</Badge>
                      <Badge variant={record.status === 'approved' ? 'default' : record.status === 'rejected' ? 'destructive' : 'secondary'}>
                        {record.status}
                      </Badge>
                    </div>
                    <p className="text-sm mb-2">{record.reason}</p>
                    <div className="text-xs text-muted-foreground">
                      <p>Requested by {record.requested_by_name} {formatDistanceToNow(new Date(record.requested_at), { addSuffix: true })}</p>
                      {record.resolved_at && (
                        <p>Resolved by {record.resolved_by_name} {formatDistanceToNow(new Date(record.resolved_at), { addSuffix: true })}</p>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  No override history
                </p>
              )}
            </TabsContent>
          </ScrollArea>
        </Tabs>

        <DialogFooter className="mt-4">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          {event.github_pr_url && (
            <Button variant="outline" asChild>
              <a href={event.github_pr_url} target="_blank" rel="noopener noreferrer">
                View PR
              </a>
            </Button>
          )}
          {event.validation_status === ValidationStatus.FAILED && onRequestOverride && (
            <Button onClick={onRequestOverride}>
              Request Override
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
