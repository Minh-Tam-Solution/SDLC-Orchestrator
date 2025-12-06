/**
 * File: frontend/web/src/components/council/ChatMessage.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-04
 * Authority: Frontend Lead + CTO Approved
 * Sprint: 28 - Web Dashboard AI Assistant
 *
 * Description:
 * Chat message component for AI Council chat.
 * Displays user and assistant messages with Council deliberation.
 */

import { useState, memo } from 'react'
import { Bot, User, AlertCircle, ChevronDown, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { Stage1View } from './Stage1View'
import { Stage2View } from './Stage2View'
import { Stage3View } from './Stage3View'
import type { ChatMessage as ChatMessageType } from '@/types/council'

interface ChatMessageProps {
  message: ChatMessageType
  onApplyRecommendation?: () => void
}

function formatTime(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

const CouncilDeliberationView = memo(function CouncilDeliberationView({
  deliberation,
  onApply,
}: {
  deliberation: ChatMessageType['councilDeliberation']
  onApply?: () => void
}) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!deliberation) return null

  return (
    <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
      <CollapsibleTrigger
        className={cn(
          'flex w-full items-center gap-2 text-xs text-muted-foreground',
          'hover:text-foreground transition-colors mt-3 pt-3 border-t',
          'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded'
        )}
        aria-label="Toggle Council Deliberation details"
      >
        {isExpanded ? (
          <ChevronDown className="h-3 w-3" />
        ) : (
          <ChevronRight className="h-3 w-3" />
        )}
        <span>Council Deliberation ({deliberation.providers_used.length} stages)</span>
        <span className="ml-auto">
          {(deliberation.total_duration_ms / 1000).toFixed(1)}s
        </span>
      </CollapsibleTrigger>

      <CollapsibleContent className="pt-3 space-y-3">
        <Stage1View responses={deliberation.stage1_responses} />
        <Stage2View rankings={deliberation.stage2_rankings} />
        <Stage3View
          synthesis={deliberation.stage3_synthesis}
          {...(onApply ? { onApply } : {})}
        />

        {/* Cost info */}
        <div className="text-xs text-muted-foreground text-right">
          Cost: ${deliberation.total_cost_usd.toFixed(4)} |
          Providers: {deliberation.providers_used.join(', ')}
        </div>
      </CollapsibleContent>
    </Collapsible>
  )
})

export const ChatMessage = memo(function ChatMessage({ message, onApplyRecommendation }: ChatMessageProps) {
  const isUser = message.role === 'user'
  const isSystem = message.role === 'system'
  // isAssistant is implicit (not user and not system)

  // Loading state
  if (message.isLoading) {
    return (
      <div className="flex gap-3">
        <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
          <Bot className="h-4 w-4 text-primary animate-pulse" />
        </div>
        <div className="flex-1">
          <div className="text-xs text-muted-foreground mb-1">AI Assistant</div>
          <div className="rounded-lg bg-muted/50 p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <div className="animate-bounce">.</div>
              <div className="animate-bounce" style={{ animationDelay: '0.1s' }}>.</div>
              <div className="animate-bounce" style={{ animationDelay: '0.2s' }}>.</div>
              <span className="ml-2">AI is thinking...</span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (message.error) {
    return (
      <div className="flex gap-3">
        <div className="h-8 w-8 rounded-full bg-destructive/10 flex items-center justify-center flex-shrink-0">
          <AlertCircle className="h-4 w-4 text-destructive" />
        </div>
        <div className="flex-1">
          <div className="text-xs text-muted-foreground mb-1">Error</div>
          <div className="rounded-lg bg-destructive/10 border border-destructive/20 p-4">
            <p className="text-sm text-destructive">{message.error}</p>
          </div>
        </div>
      </div>
    )
  }

  // System message
  if (isSystem) {
    return (
      <div className="flex justify-center">
        <div className="text-xs text-muted-foreground bg-muted/50 px-3 py-1.5 rounded-full">
          {message.content}
        </div>
      </div>
    )
  }

  // User message
  if (isUser) {
    return (
      <div className="flex gap-3 justify-end">
        <div className="flex-1 max-w-[80%]">
          <div className="text-xs text-muted-foreground mb-1 text-right">
            You &middot; {formatTime(message.timestamp)}
          </div>
          <div className="rounded-lg bg-primary text-primary-foreground p-4 ml-auto">
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          </div>
        </div>
        <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
          <User className="h-4 w-4 text-primary-foreground" />
        </div>
      </div>
    )
  }

  // Assistant message
  return (
    <div className="flex gap-3">
      <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
        <Bot className="h-4 w-4 text-primary" />
      </div>
      <div className="flex-1">
        <div className="text-xs text-muted-foreground mb-1">
          AI Assistant &middot; {formatTime(message.timestamp)}
        </div>
        <div className="rounded-lg bg-muted/50 p-4">
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>

          {/* Council Deliberation */}
          {message.councilDeliberation && (
            <CouncilDeliberationView
              deliberation={message.councilDeliberation}
              {...(onApplyRecommendation ? { onApply: onApplyRecommendation } : {})}
            />
          )}
        </div>
      </div>
    </div>
  )
})

export default ChatMessage
