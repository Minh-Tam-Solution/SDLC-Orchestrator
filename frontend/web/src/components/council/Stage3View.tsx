/**
 * File: frontend/web/src/components/council/Stage3View.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-04
 * Authority: Frontend Lead + CTO Approved
 * Sprint: 28 - Web Dashboard AI Assistant
 *
 * Description:
 * Stage 3 view component for AI Council deliberation.
 * Displays final synthesis and action button.
 */

import { useState, memo } from 'react'
import { ChevronDown, ChevronRight, Sparkles, CheckCircle2, Lightbulb } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import type { Stage3ViewProps } from '@/types/council'

function getConfidenceLevel(confidence: number): {
  label: string
  color: string
  bgColor: string
} {
  if (confidence >= 90) {
    return { label: 'Very High', color: 'text-green-700', bgColor: 'bg-green-500' }
  }
  if (confidence >= 75) {
    return { label: 'High', color: 'text-blue-700', bgColor: 'bg-blue-500' }
  }
  if (confidence >= 50) {
    return { label: 'Medium', color: 'text-yellow-700', bgColor: 'bg-yellow-500' }
  }
  return { label: 'Low', color: 'text-red-700', bgColor: 'bg-red-500' }
}

function LoadingSkeleton() {
  return (
    <div className="space-y-4">
      <div className="rounded-lg border p-4 bg-card">
        <Skeleton className="h-4 w-32 mb-2" />
        <Skeleton className="h-2 w-full mb-1" />
        <Skeleton className="h-3 w-20" />
      </div>
      <div className="rounded-lg border p-4 bg-card">
        <Skeleton className="h-4 w-24 mb-2" />
        <div className="space-y-2">
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-4/5" />
          <Skeleton className="h-3 w-3/5" />
        </div>
      </div>
      <Skeleton className="h-10 w-full rounded-md" />
    </div>
  )
}

export const Stage3View = memo(function Stage3View({ synthesis, isLoading = false, onApply }: Stage3ViewProps) {
  const [isOpen, setIsOpen] = useState(true) // Stage 3 expanded by default
  const [isApplying, setIsApplying] = useState(false)

  const confidenceLevel = getConfidenceLevel(synthesis?.confidence ?? 0)

  const handleApply = async () => {
    if (!onApply) return
    setIsApplying(true)
    try {
      onApply()
    } finally {
      setIsApplying(false)
    }
  }

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger
        className={cn(
          'flex w-full items-center justify-between rounded-lg border p-3',
          'bg-primary/5 border-primary/20 hover:bg-primary/10 transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2'
        )}
        aria-label="Stage 3: Final Synthesis"
      >
        <div className="flex items-center gap-2">
          {isOpen ? (
            <ChevronDown className="h-4 w-4 text-primary" />
          ) : (
            <ChevronRight className="h-4 w-4 text-primary" />
          )}
          <Sparkles className="h-4 w-4 text-primary" />
          <span className="font-medium text-primary">Stage 3: Final Synthesis</span>
        </div>
        <div className="text-xs">
          {isLoading ? (
            <span className="animate-pulse text-muted-foreground">Synthesizing...</span>
          ) : synthesis ? (
            <span className={confidenceLevel.color}>
              {synthesis.confidence}% confidence
            </span>
          ) : null}
        </div>
      </CollapsibleTrigger>

      <CollapsibleContent className="pt-3">
        {isLoading ? (
          <LoadingSkeleton />
        ) : synthesis ? (
          <div className="space-y-4">
            {/* Confidence Score */}
            <div className="rounded-lg border p-4 bg-card">
              <h4 className="text-sm font-medium mb-2 flex items-center gap-2" id="confidence-label">
                <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
                Confidence Score
              </h4>
              <Progress
                value={synthesis.confidence}
                className="h-2 mb-1"
                aria-label={`Confidence score: ${synthesis.confidence}%`}
              />
              <div className="flex items-center justify-between text-xs">
                <span className={confidenceLevel.color}>
                  {confidenceLevel.label}
                </span>
                <span className="text-muted-foreground">
                  {synthesis.confidence}%
                </span>
              </div>
            </div>

            {/* Reasoning */}
            <div className="rounded-lg border p-4 bg-card">
              <h4 className="text-sm font-medium mb-2">Reasoning</h4>
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                {synthesis.reasoning}
              </p>
            </div>

            {/* Suggested Action */}
            {synthesis.suggested_action && (
              <div className="rounded-lg border p-4 bg-blue-50 border-blue-200">
                <h4 className="text-sm font-medium mb-2 flex items-center gap-2 text-blue-700">
                  <Lightbulb className="h-4 w-4" />
                  Suggested Action
                </h4>
                <p className="text-sm text-blue-600">
                  {synthesis.suggested_action}
                </p>
              </div>
            )}

            {/* Apply Button */}
            {onApply && (
              <Button
                onClick={handleApply}
                disabled={isApplying}
                className="w-full"
                size="lg"
              >
                {isApplying ? (
                  <>
                    <span className="animate-spin mr-2">
                      <svg className="h-4 w-4" viewBox="0 0 24 24">
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                          fill="none"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                        />
                      </svg>
                    </span>
                    Applying...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    Apply Recommendation
                  </>
                )}
              </Button>
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            No synthesis available
          </div>
        )}
      </CollapsibleContent>
    </Collapsible>
  )
})

export default Stage3View
