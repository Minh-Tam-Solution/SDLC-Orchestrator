/**
 * File: frontend/web/src/components/council/GateProgressBar.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-04
 * Authority: Frontend Lead + CTO Approved
 * Foundation: SDLC 4.9 Complete Lifecycle, Zero Mock Policy
 * Sprint: 28 - Web Dashboard AI Assistant
 *
 * Description:
 * Horizontal gate progress bar displaying G0.1 → G5 gates
 * with status indicators (passed, current, pending, blocked).
 */

import * as React from 'react'
import { memo, useCallback } from 'react'
import {
  GateType,
  GateProgressStatus,
  ComplianceTier,
  GATE_DEFINITIONS,
} from '@/types/council'
import { cn } from '@/lib/utils'

export interface GateProgressBarProps {
  currentGate: GateType
  gateStatuses: Record<GateType, GateProgressStatus>
  tier: ComplianceTier
  onGateClick?: (gate: GateType) => void
  className?: string
}

const GATE_ORDER: GateType[] = ['G0.1', 'G0.2', 'G1', 'G2', 'G3', 'G4', 'G5']

/**
 * Get gate status styling classes
 */
function getGateStatusClasses(status: GateProgressStatus): string {
  const baseClasses = 'flex items-center justify-center rounded-md border-2 font-semibold transition-all'
  
  switch (status) {
    case 'passed':
      return cn(
        baseClasses,
        'bg-green-500 border-green-600 text-white',
        'hover:bg-green-600'
      )
    case 'current':
      return cn(
        baseClasses,
        'bg-blue-500 border-blue-600 text-white',
        'animate-pulse shadow-lg shadow-blue-500/50'
      )
    case 'blocked':
      return cn(
        baseClasses,
        'bg-red-500 border-red-600 text-white',
        'hover:bg-red-600'
      )
    case 'pending':
    default:
      return cn(
        baseClasses,
        'bg-gray-300 border-gray-400 text-gray-700',
        'hover:bg-gray-400'
      )
  }
}

/**
 * Get gate status icon
 */
function getGateIcon(status: GateProgressStatus): string {
  switch (status) {
    case 'passed':
      return '✓'
    case 'current':
      return '●'
    case 'blocked':
      return '⊘'
    case 'pending':
    default:
      return '○'
  }
}

/**
 * GateProgressBar component
 *
 * Displays horizontal progress bar with all gates (G0.1 → G5).
 * Shows current gate with pulse animation, passed gates with checkmark,
 * and pending/blocked gates with appropriate indicators.
 *
 * @param currentGate - Currently active gate
 * @param gateStatuses - Status for each gate
 * @param tier - Compliance tier (affects styling)
 * @param onGateClick - Optional click handler for gates
 * @param className - Additional CSS classes
 */
export const GateProgressBar = memo(function GateProgressBar({
  currentGate,
  gateStatuses,
  onGateClick,
  className,
}: GateProgressBarProps) {
  const handleGateClick = useCallback((gate: GateType) => {
    onGateClick?.(gate)
  }, [onGateClick])

  return (
    <div className={cn('space-y-4', className)}>
      {/* Progress Bar */}
      <div className="flex items-center gap-2">
        {GATE_ORDER.map((gate, index) => {
          const status = gateStatuses[gate]
          const isCurrent = gate === currentGate
          const gateDef = GATE_DEFINITIONS[gate]
          const isClickable = !!onGateClick

          return (
            <React.Fragment key={gate}>
              {/* Gate Button */}
              <button
                type="button"
                onClick={() => handleGateClick(gate)}
                disabled={!isClickable}
                className={cn(
                  getGateStatusClasses(status),
                  isCurrent && 'animate-pulse shadow-lg shadow-blue-500/50',
                  'h-12 w-16 flex-col gap-0.5',
                  isClickable && 'cursor-pointer',
                  !isClickable && 'cursor-default'
                )}
                aria-label={`Gate ${gate}: ${gateDef.label} - ${status}`}
                aria-current={isCurrent ? 'step' : undefined}
              >
                <span className="text-xs">{gate}</span>
                <span className="text-lg leading-none" aria-hidden="true">
                  {getGateIcon(status)}
                </span>
                <span className="text-[10px] leading-tight opacity-90">
                  {gateDef.label}
                </span>
              </button>

              {/* Connector Line */}
              {index < GATE_ORDER.length - 1 && (
                <div
                  className={cn(
                    'h-0.5 flex-1 transition-colors',
                    status === 'passed'
                      ? 'bg-green-500'
                      : status === 'current'
                      ? 'bg-blue-500'
                      : status === 'blocked'
                      ? 'bg-red-500'
                      : 'bg-gray-300'
                  )}
                  aria-hidden="true"
                />
              )}
            </React.Fragment>
          )
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span className="text-green-500">✓</span>
          <span>Passed</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="text-blue-500 animate-pulse">●</span>
          <span>Current</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="text-gray-500">○</span>
          <span>Pending</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="text-red-500">⊘</span>
          <span>Blocked</span>
        </span>
      </div>
    </div>
  )
})

