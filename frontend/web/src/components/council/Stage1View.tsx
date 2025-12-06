/**
 * File: frontend/web/src/components/council/Stage1View.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-04
 * Authority: Frontend Lead + CTO Approved
 * Sprint: 28 - Web Dashboard AI Assistant
 *
 * Description:
 * Stage 1 view component for AI Council deliberation.
 * Displays individual AI responses from multiple providers.
 */

import { useState, memo } from 'react'
import { ChevronDown, ChevronRight, Clock, Cpu } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import type { Stage1ViewProps, AIResponse } from '@/types/council'

// Provider color mapping
const PROVIDER_COLORS: Record<string, { bg: string; border: string; text: string; icon: string }> = {
  claude: {
    bg: 'bg-orange-50',
    border: 'border-orange-200',
    text: 'text-orange-700',
    icon: '🟠',
  },
  openai: {
    bg: 'bg-teal-50',
    border: 'border-teal-200',
    text: 'text-teal-700',
    icon: '🟢',
  },
  gemini: {
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    text: 'text-blue-700',
    icon: '🔵',
  },
  ollama: {
    bg: 'bg-purple-50',
    border: 'border-purple-200',
    text: 'text-purple-700',
    icon: '🟣',
  },
}

function getProviderStyle(provider: string) {
  const key = provider.toLowerCase()
  return PROVIDER_COLORS[key] || {
    bg: 'bg-gray-50',
    border: 'border-gray-200',
    text: 'text-gray-700',
    icon: '⚪',
  }
}

function AIResponseCard({ response }: { response: AIResponse }) {
  const style = getProviderStyle(response.provider)
  const confidence = response.confidence ?? 0

  return (
    <div
      className={cn(
        'rounded-lg border p-4',
        style.bg,
        style.border
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-lg">{style.icon}</span>
          <div>
            <h4 className={cn('font-medium', style.text)}>
              {response.provider}
            </h4>
            <p className="text-xs text-muted-foreground">
              {response.model}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            <span>{response.duration_ms}ms</span>
          </div>
          {confidence > 0 && (
            <div className="flex items-center gap-1">
              <Cpu className="h-3 w-3" />
              <span>{confidence}%</span>
            </div>
          )}
        </div>
      </div>

      {/* Confidence bar */}
      {confidence > 0 && (
        <div className="mb-3">
          <Progress value={confidence} className="h-1.5" />
        </div>
      )}

      {/* Response content */}
      <div className="text-sm text-foreground whitespace-pre-wrap">
        {response.response}
      </div>
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="rounded-lg border p-4 bg-muted/30">
          <div className="flex items-center gap-2 mb-3">
            <Skeleton className="h-6 w-6 rounded-full" />
            <div className="space-y-1">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-3 w-32" />
            </div>
          </div>
          <Skeleton className="h-1.5 w-full mb-3" />
          <div className="space-y-2">
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-4/5" />
            <Skeleton className="h-3 w-3/5" />
          </div>
        </div>
      ))}
    </div>
  )
}

export const Stage1View = memo(function Stage1View({ responses, isLoading = false }: Stage1ViewProps) {
  const [isOpen, setIsOpen] = useState(false)

  const totalDuration = responses.reduce((sum, r) => sum + r.duration_ms, 0)
  const avgConfidence = responses.length > 0
    ? Math.round(responses.reduce((sum, r) => sum + (r.confidence ?? 0), 0) / responses.length)
    : 0

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger
        className={cn(
          'flex w-full items-center justify-between rounded-lg border p-3',
          'bg-muted/50 hover:bg-muted transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2'
        )}
        aria-label={`Stage 1: AI Responses, ${responses.length} providers`}
      >
        <div className="flex items-center gap-2">
          {isOpen ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          )}
          <span className="font-medium">Stage 1: AI Responses</span>
          <span className="text-xs text-muted-foreground px-2 py-0.5 bg-background rounded">
            {responses.length} providers
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          {!isLoading && avgConfidence > 0 && (
            <span>Avg: {avgConfidence}%</span>
          )}
          {!isLoading && totalDuration > 0 && (
            <span>{(totalDuration / 1000).toFixed(1)}s</span>
          )}
          {isLoading && (
            <span className="animate-pulse">Processing...</span>
          )}
        </div>
      </CollapsibleTrigger>

      <CollapsibleContent className="pt-3">
        {isLoading ? (
          <LoadingSkeleton />
        ) : (
          <div className="space-y-3">
            {responses.map((response, index) => (
              <AIResponseCard key={`${response.provider}-${index}`} response={response} />
            ))}
          </div>
        )}
      </CollapsibleContent>
    </Collapsible>
  )
})

export default Stage1View
