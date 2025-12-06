/**
 * File: frontend/web/src/components/council/CouncilToggle.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-04
 * Authority: Frontend Lead + CTO Approved
 * Foundation: SDLC 4.9 Complete Lifecycle, Zero Mock Policy
 * Sprint: 28 - Web Dashboard AI Assistant
 *
 * Description:
 * Council mode toggle switch component with accessibility support.
 * Enables/disables 3-stage AI Council deliberation mode.
 */

import { memo, useCallback } from 'react'
import * as SwitchPrimitives from '@radix-ui/react-switch'
import { cn } from '@/lib/utils'

export interface CouncilToggleProps {
  enabled: boolean
  onChange: (enabled: boolean) => void
  disabled?: boolean
  className?: string
}

/**
 * CouncilToggle component
 *
 * Toggle switch for enabling/disabling AI Council mode.
 * When enabled, uses 3 AI providers for deliberation.
 * When disabled, uses single AI for faster responses.
 *
 * @param enabled - Whether council mode is enabled
 * @param onChange - Callback when toggle state changes
 * @param disabled - Whether toggle is disabled
 * @param className - Additional CSS classes
 */
export const CouncilToggle = memo(function CouncilToggle({
  enabled,
  onChange,
  disabled = false,
  className,
}: CouncilToggleProps) {
  const handleChange = useCallback((checked: boolean) => {
    onChange(checked)
  }, [onChange])

  return (
    <div className={cn('flex items-center gap-3', className)}>
      <div className="flex flex-col">
        <label
          htmlFor="council-toggle"
          className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
        >
          Council Mode
        </label>
        <p
          id="council-mode-description"
          className="text-xs text-muted-foreground mt-1"
        >
          {enabled
            ? '3 AI providers for best answer'
            : 'Single AI for faster responses'}
        </p>
      </div>
      <SwitchPrimitives.Root
        id="council-toggle"
        checked={enabled}
        onCheckedChange={handleChange}
        disabled={disabled}
        className={cn(
          'peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background',
          'disabled:cursor-not-allowed disabled:opacity-50',
          enabled
            ? 'bg-primary'
            : 'bg-input',
          'data-[state=checked]:bg-primary'
        )}
        aria-label="Council Mode toggle"
        aria-describedby="council-mode-description"
      >
        <SwitchPrimitives.Thumb
          className={cn(
            'pointer-events-none block h-5 w-5 rounded-full bg-background shadow-lg ring-0 transition-transform',
            'data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0'
          )}
        />
      </SwitchPrimitives.Root>
    </div>
  )
})

