/**
 * File: frontend/web/src/components/sdlc/ComplianceScoreCircle.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-06
 * Authority: Frontend Lead + CTO Approved
 * Sprint: 30 - CI/CD & Web Integration (Day 4)
 *
 * Description:
 * Circular progress indicator for SDLC compliance score.
 * Animated SVG with color coding based on score.
 */

import { memo, useMemo } from 'react'
import { cn } from '@/lib/utils'
import type { ComplianceScoreCircleProps } from '@/types/sdlcValidation'
import { getScoreColor } from '@/types/sdlcValidation'

/**
 * ComplianceScoreCircle component
 *
 * Displays compliance score as a circular progress indicator:
 * - 90-100: Green (Excellent)
 * - 70-89: Yellow (Good)
 * - 50-69: Orange (Needs Improvement)
 * - 0-49: Red (Poor)
 *
 * @param score - Compliance score (0-100)
 * @param size - Circle size (sm, md, lg)
 * @param showLabel - Whether to show score label (default: true)
 * @param animate - Whether to animate on mount (default: true)
 */
export const ComplianceScoreCircle = memo(function ComplianceScoreCircle({
  score,
  size = 'md',
  showLabel = true,
  animate = true,
}: ComplianceScoreCircleProps) {
  const sizeConfig = useMemo(() => {
    switch (size) {
      case 'sm':
        return { width: 64, strokeWidth: 6, fontSize: 'text-sm', labelSize: 'text-xs' }
      case 'md':
        return { width: 96, strokeWidth: 8, fontSize: 'text-xl', labelSize: 'text-xs' }
      case 'lg':
        return { width: 128, strokeWidth: 10, fontSize: 'text-3xl', labelSize: 'text-sm' }
      default:
        return { width: 96, strokeWidth: 8, fontSize: 'text-xl', labelSize: 'text-xs' }
    }
  }, [size])

  const { width, strokeWidth, fontSize, labelSize } = sizeConfig
  const radius = (width - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const strokeDashoffset = circumference - (score / 100) * circumference

  const strokeColor = useMemo(() => {
    if (score >= 90) return '#22c55e' // green-500
    if (score >= 70) return '#eab308' // yellow-500
    if (score >= 50) return '#f97316' // orange-500
    return '#ef4444' // red-500
  }, [score])

  const bgStrokeColor = useMemo(() => {
    if (score >= 90) return '#dcfce7' // green-100
    if (score >= 70) return '#fef9c3' // yellow-100
    if (score >= 50) return '#ffedd5' // orange-100
    return '#fee2e2' // red-100
  }, [score])

  return (
    <div
      className="relative inline-flex items-center justify-center"
      role="img"
      aria-label={`Compliance score: ${score}%`}
    >
      <svg
        width={width}
        height={width}
        className={cn(
          'transform -rotate-90',
          animate && 'transition-all duration-1000 ease-out'
        )}
      >
        {/* Background circle */}
        <circle
          cx={width / 2}
          cy={width / 2}
          r={radius}
          fill="none"
          stroke={bgStrokeColor}
          strokeWidth={strokeWidth}
        />
        {/* Progress circle */}
        <circle
          cx={width / 2}
          cy={width / 2}
          r={radius}
          fill="none"
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={animate ? strokeDashoffset : circumference}
          className={animate ? 'transition-all duration-1000 ease-out' : ''}
          style={
            animate
              ? { strokeDashoffset }
              : undefined
          }
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={cn('font-bold', fontSize, getScoreColor(score))}>
          {score}
        </span>
        {showLabel && (
          <span className={cn('text-muted-foreground', labelSize)}>
            {getScoreLabel(score)}
          </span>
        )}
      </div>
    </div>
  )
})

/**
 * Get score label based on score value
 */
function getScoreLabel(score: number): string {
  if (score >= 90) return 'Excellent'
  if (score >= 70) return 'Good'
  if (score >= 50) return 'Fair'
  return 'Poor'
}

/**
 * ComplianceScoreBar component
 *
 * Alternative horizontal bar display for compliance score
 */
export const ComplianceScoreBar = memo(function ComplianceScoreBar({
  score,
  showLabel = true,
  className,
}: {
  score: number
  showLabel?: boolean
  className?: string
}) {
  const barColor = useMemo(() => {
    if (score >= 90) return 'bg-green-500'
    if (score >= 70) return 'bg-yellow-500'
    if (score >= 50) return 'bg-orange-500'
    return 'bg-red-500'
  }, [score])

  const bgColor = useMemo(() => {
    if (score >= 90) return 'bg-green-100'
    if (score >= 70) return 'bg-yellow-100'
    if (score >= 50) return 'bg-orange-100'
    return 'bg-red-100'
  }, [score])

  return (
    <div className={cn('w-full', className)}>
      {showLabel && (
        <div className="flex justify-between mb-1">
          <span className="text-sm font-medium text-muted-foreground">
            Compliance Score
          </span>
          <span className={cn('text-sm font-bold', getScoreColor(score))}>
            {score}%
          </span>
        </div>
      )}
      <div className={cn('w-full h-2 rounded-full', bgColor)}>
        <div
          className={cn('h-2 rounded-full transition-all duration-500', barColor)}
          style={{ width: `${score}%` }}
          role="progressbar"
          aria-valuenow={score}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  )
})
