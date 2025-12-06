/**
 * File: frontend/web/src/components/council/AICouncilChatLazy.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-05
 * Authority: Frontend Lead + CTO Approved
 * Sprint: 28 - Web Dashboard AI Assistant (Day 4: Performance)
 *
 * Description:
 * Lazy-loaded wrapper for AICouncilChat component.
 * Defers loading of Sheet and chat components until user interaction.
 * Reduces initial bundle size by ~30KB.
 */

import { lazy, Suspense, useState, useCallback, memo } from 'react'
import { Bot } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import type { AICouncilChatProps } from '@/types/council'

// Lazy load the full AICouncilChat component
const AICouncilChatFull = lazy(() => import('./AICouncilChat'))

// Loading fallback for the sheet content
function ChatLoadingFallback() {
  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[450px] sm:max-w-[450px] bg-background border-l shadow-lg z-50">
      <div className="p-4 border-b">
        <div className="flex items-center gap-2">
          <Skeleton className="h-5 w-5 rounded-full" />
          <Skeleton className="h-5 w-40" />
        </div>
        <div className="mt-3">
          <Skeleton className="h-8 w-full" />
        </div>
      </div>
      <div className="p-4 space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex gap-3">
            <Skeleton className="h-8 w-8 rounded-full" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-16 w-full rounded-lg" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/**
 * Lazy-loaded AI Council Chat component
 *
 * Only loads the full Sheet component when user clicks the button.
 * This reduces initial page load by deferring ~30KB of JS.
 */
export const AICouncilChatLazy = memo(function AICouncilChatLazy(props: AICouncilChatProps) {
  const [isActivated, setIsActivated] = useState(false)

  const handleActivate = useCallback(() => {
    setIsActivated(true)
  }, [])

  // If not yet activated, show just the trigger button
  if (!isActivated) {
    return (
      <Button
        variant="default"
        size="lg"
        className={cn('gap-2', props.className)}
        onClick={handleActivate}
      >
        <Bot className="h-5 w-5" />
        AI Assistant
      </Button>
    )
  }

  // Once activated, load the full component
  return (
    <Suspense fallback={<ChatLoadingFallback />}>
      <AICouncilChatFull {...props} />
    </Suspense>
  )
})

export default AICouncilChatLazy
