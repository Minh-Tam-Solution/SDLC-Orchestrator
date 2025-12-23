/**
 * Timeline Event Card Component
 *
 * SDLC Stage: 04 - BUILD
 * Sprint: 43 - Policy Guards & Evidence UI
 * Framework: SDLC 5.1.1
 * Epic: EP-02 AI Safety Layer v1
 *
 * Purpose:
 * Individual event card in the Evidence Timeline displaying:
 * - PR/commit info
 * - AI tool detection
 * - Validation status with validator breakdown
 * - Quick actions (view detail, request override)
 */

import { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  AIToolLabels,
  ValidationStatus,
  ValidationStatusColors,
  OverrideStatus,
  type EvidenceEventSummary,
} from '@/types/evidence-timeline'

interface TimelineEventCardProps {
  event: EvidenceEventSummary
  onViewDetail: (eventId: string) => void
  onRequestOverride?: (eventId: string) => void
  onPrefetch?: (eventId: string) => void
}

export default function TimelineEventCard({
  event,
  onViewDetail,
  onRequestOverride,
  onPrefetch,
}: TimelineEventCardProps) {
  const [isHovered, setIsHovered] = useState(false)

  // Get status badge styling
  const getStatusBadge = () => {
    const color = ValidationStatusColors[event.validation_status]
    const colorClasses = {
      green: 'bg-green-100 text-green-800 border-green-200',
      red: 'bg-red-100 text-red-800 border-red-200',
      yellow: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      gray: 'bg-gray-100 text-gray-800 border-gray-200',
      blue: 'bg-blue-100 text-blue-800 border-blue-200',
    }

    const icons = {
      [ValidationStatus.PASSED]: (
        <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      ),
      [ValidationStatus.FAILED]: (
        <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      ),
      [ValidationStatus.PENDING]: (
        <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      [ValidationStatus.RUNNING]: (
        <svg className="h-3 w-3 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      ),
      [ValidationStatus.OVERRIDDEN]: (
        <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
      [ValidationStatus.ERROR]: (
        <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      ),
    }

    return (
      <Badge className={`${colorClasses[color]} flex items-center gap-1`}>
        {icons[event.validation_status]}
        {event.validation_status}
      </Badge>
    )
  }

  // Get AI tool icon
  const getAIToolIcon = () => {
    const iconMap: Record<string, string> = {
      cursor: '🖱️',
      copilot: '🤖',
      claude: '🧠',
      chatgpt: '💬',
      windsurf: '🏄',
      cody: '🔍',
      tabnine: '📝',
      other: '❓',
      manual: '✋',
    }
    return iconMap[event.ai_tool] || '❓'
  }

  // Format confidence score
  const getConfidenceColor = () => {
    if (event.confidence_score >= 80) return 'text-green-600'
    if (event.confidence_score >= 50) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <Card
      className={`transition-all duration-200 cursor-pointer ${
        isHovered ? 'shadow-md border-primary/50' : ''
      }`}
      onMouseEnter={() => {
        setIsHovered(true)
        onPrefetch?.(event.id)
      }}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => onViewDetail(event.id)}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          {/* Left: PR/Commit Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-semibold text-primary">
                PR #{event.pr_number}
              </span>
              {event.override_status !== OverrideStatus.NONE && (
                <Badge variant="outline" className="text-xs">
                  Override: {event.override_status}
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground truncate">
              {event.pr_title}
            </p>
            <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                {event.pr_author}
              </span>
              {event.branch_name && (
                <span className="flex items-center gap-1">
                  <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                  </svg>
                  {event.branch_name}
                </span>
              )}
              <span>
                {formatDistanceToNow(new Date(event.created_at), { addSuffix: true })}
              </span>
            </div>
          </div>

          {/* Center: AI Tool & Confidence */}
          <div className="flex flex-col items-center gap-1">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-muted">
                    <span className="text-lg">{getAIToolIcon()}</span>
                    <span className="text-sm font-medium">
                      {AIToolLabels[event.ai_tool]}
                    </span>
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p>AI Tool: {AIToolLabels[event.ai_tool]}</p>
                  <p>Detection: {event.detection_method}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <span className={`text-xs font-medium ${getConfidenceColor()}`}>
              {event.confidence_score}% confidence
            </span>
          </div>

          {/* Right: Validation Status */}
          <div className="flex flex-col items-end gap-2">
            {getStatusBadge()}

            {/* Validators Summary */}
            <div className="flex items-center gap-1 text-xs">
              <span className="text-green-600">{event.validators_passed} passed</span>
              <span className="text-muted-foreground">/</span>
              <span className="text-red-600">{event.validators_failed} failed</span>
            </div>

            {/* Quick Actions */}
            {isHovered && (
              <div className="flex gap-1 mt-1">
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-7 px-2"
                  onClick={(e) => {
                    e.stopPropagation()
                    onViewDetail(event.id)
                  }}
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                </Button>
                {event.validation_status === ValidationStatus.FAILED && onRequestOverride && (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 px-2"
                    onClick={(e) => {
                      e.stopPropagation()
                      onRequestOverride(event.id)
                    }}
                  >
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Bottom: Files Changed */}
        <div className="flex items-center gap-4 mt-3 pt-3 border-t text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            {event.files_changed} files
          </span>
          <span className="text-green-600">+{event.lines_added}</span>
          <span className="text-red-600">-{event.lines_deleted}</span>
          <span className="ml-auto">
            {event.validation_duration_ms}ms
          </span>
        </div>
      </CardContent>
    </Card>
  )
}
