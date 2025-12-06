/**
 * File: frontend/web/src/components/sdlc/SDLCTierBadge.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-06
 * Authority: Frontend Lead + CTO Approved
 * Sprint: 30 - CI/CD & Web Integration (Day 4)
 *
 * Description:
 * SDLC 5.0.0 tier badge component displaying tier classification
 * (Lite/Standard/Professional/Enterprise) with tier-based styling.
 */

import { memo } from 'react'
import { cn } from '@/lib/utils'
import type { SDLCTier, TierBadgeSDLCProps } from '@/types/sdlcValidation'
import { SDLC_TIER_CONFIGS } from '@/types/sdlcValidation'

/**
 * SDLCTierBadge component
 *
 * Displays SDLC 5.0.0 tier with appropriate styling:
 * - Lite: 🌱 Green (5 stages)
 * - Standard: ⚡ Blue (8 stages)
 * - Professional: 🏆 Purple (10 stages)
 * - Enterprise: 👑 Amber (11 stages)
 *
 * @param tier - SDLC tier (lite, standard, professional, enterprise)
 * @param showLabel - Whether to show tier label (default: true)
 * @param size - Badge size (sm, md, lg)
 */
export const SDLCTierBadge = memo(function SDLCTierBadge({
  tier,
  showLabel = true,
  size = 'md',
}: TierBadgeSDLCProps) {
  const config = SDLC_TIER_CONFIGS[tier]

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
        sizeClasses[size]
      )}
      role="status"
      aria-label={`${config.label} tier - requires ${config.requiredStages} stages`}
    >
      <span aria-hidden="true">{config.icon}</span>
      {showLabel && <span className="font-semibold">{config.label}</span>}
      {size === 'lg' && (
        <span className="text-xs opacity-75">
          {config.requiredStages} stages
        </span>
      )}
    </div>
  )
})

/**
 * Get tier from compliance score
 */
export function getTierFromScore(score: number): SDLCTier {
  if (score >= 95) return 'enterprise'
  if (score >= 85) return 'professional'
  if (score >= 70) return 'standard'
  return 'lite'
}

/**
 * Get tier color classes
 */
export function getTierColorClasses(tier: SDLCTier): {
  bg: string
  border: string
  text: string
} {
  const config = SDLC_TIER_CONFIGS[tier]
  return {
    bg: config.bgColor,
    border: config.borderColor,
    text: config.textColor,
  }
}
