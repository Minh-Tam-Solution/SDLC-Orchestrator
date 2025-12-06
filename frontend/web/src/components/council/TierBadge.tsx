/**
 * File: frontend/web/src/components/council/TierBadge.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-04
 * Authority: Frontend Lead + CTO Approved
 * Foundation: SDLC 4.9 Complete Lifecycle, Zero Mock Policy
 * Sprint: 28 - Web Dashboard AI Assistant
 *
 * Description:
 * Tier badge component displaying compliance tier (Lite/Standard/Enterprise)
 * with tier-based styling, icons, and optional coverage percentage.
 */

import { memo } from 'react'
import { ComplianceTier, TIER_CONFIGS } from '@/types/council'
import { cn } from '@/lib/utils'

export interface TierBadgeProps {
  tier: ComplianceTier
  showLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

/**
 * TierBadge component
 *
 * Displays compliance tier with appropriate styling:
 * - Lite: 🌱 Green
 * - Standard: ⚡ Blue
 * - Enterprise: 👑 Amber
 *
 * @param tier - Compliance tier (lite, standard, enterprise)
 * @param showLabel - Whether to show tier label (default: true)
 * @param size - Badge size (sm, md, lg)
 * @param className - Additional CSS classes
 */
export const TierBadge = memo(function TierBadge({
  tier,
  showLabel = true,
  size = 'md',
  className,
}: TierBadgeProps) {
  const config = TIER_CONFIGS[tier]

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-2 text-base',
  }

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md border font-medium',
        config.bgColor,
        config.borderColor,
        config.textColor,
        sizeClasses[size],
        className
      )}
      role="status"
      aria-label={`${config.label} tier`}
    >
      <span aria-hidden="true">{config.icon}</span>
      {showLabel && (
        <span className="font-semibold">{config.label}</span>
      )}
      {size === 'lg' && (
        <span className="text-xs opacity-75">
          {config.coverage}% coverage
        </span>
      )}
    </div>
  )
})

