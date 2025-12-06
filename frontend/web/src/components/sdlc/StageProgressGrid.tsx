/**
 * File: frontend/web/src/components/sdlc/StageProgressGrid.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-06
 * Authority: Frontend Lead + CTO Approved
 * Sprint: 30 - CI/CD & Web Integration (Day 4)
 *
 * Description:
 * Grid display of SDLC 5.0.0 stages showing which are found/missing.
 * Visual representation of 11-stage lifecycle compliance.
 */

import { memo, useMemo } from 'react'
import { cn } from '@/lib/utils'
import type { SDLCTier, StageProgressGridProps, SDLCStageId } from '@/types/sdlcValidation'
import { SDLC_STAGES, SDLC_TIER_CONFIGS } from '@/types/sdlcValidation'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

/**
 * Get required stages for a tier
 */
function getRequiredStagesForTier(tier: SDLCTier): SDLCStageId[] {
  const stageCount = SDLC_TIER_CONFIGS[tier].requiredStages
  const allStages: SDLCStageId[] = ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10']
  return allStages.slice(0, stageCount)
}

/**
 * StageProgressGrid component
 *
 * Displays SDLC stages in a grid format with status indicators:
 * - Green: Stage found
 * - Red: Stage missing (required)
 * - Gray: Stage optional (not required for tier)
 *
 * @param stagesFound - List of found stages with details
 * @param stagesMissing - List of missing stage IDs
 * @param tier - SDLC tier determining required stages
 */
export const StageProgressGrid = memo(function StageProgressGrid({
  stagesFound,
  stagesMissing,
  tier,
}: StageProgressGridProps) {
  const requiredStages = useMemo(() => getRequiredStagesForTier(tier), [tier])

  const foundStageIds = useMemo(
    () => new Set(stagesFound.map((s) => s.stageId)),
    [stagesFound]
  )

  const missingStageIds = useMemo(
    () => new Set(stagesMissing),
    [stagesMissing]
  )

  const allStages = useMemo(() => {
    const stages: SDLCStageId[] = ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10']
    return stages.map((stageId) => {
      const config = SDLC_STAGES[stageId]
      const isRequired = requiredStages.includes(stageId)
      const isFound = foundStageIds.has(stageId)
      const isMissing = missingStageIds.has(stageId)

      let status: 'found' | 'missing' | 'optional'
      if (isFound) status = 'found'
      else if (isMissing || isRequired) status = 'missing'
      else status = 'optional'

      const stageDetail = stagesFound.find((s) => s.stageId === stageId)

      return {
        ...config,
        status,
        isRequired,
        fileCount: stageDetail?.fileCount ?? 0,
        hasReadme: stageDetail?.hasReadme ?? false,
      }
    })
  }, [requiredStages, foundStageIds, missingStageIds, stagesFound])

  return (
    <TooltipProvider>
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-medium text-muted-foreground">
            Stage Coverage
          </h4>
          <div className="flex items-center gap-3 text-xs">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-sm bg-green-500" />
              <span>Found</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-sm bg-red-500" />
              <span>Missing</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-sm bg-gray-300" />
              <span>Optional</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-6 gap-2">
          {allStages.map((stage) => (
            <Tooltip key={stage.id}>
              <TooltipTrigger asChild>
                <div
                  className={cn(
                    'relative p-2 rounded-lg border text-center cursor-default transition-colors',
                    stage.status === 'found' &&
                      'bg-green-50 border-green-300 text-green-800',
                    stage.status === 'missing' &&
                      'bg-red-50 border-red-300 text-red-800',
                    stage.status === 'optional' &&
                      'bg-gray-50 border-gray-200 text-gray-500'
                  )}
                  role="gridcell"
                  aria-label={`Stage ${stage.id}: ${stage.name} - ${stage.status}`}
                >
                  <div className="text-lg font-bold">{stage.id}</div>
                  <div className="text-[10px] truncate">{stage.name.split(' ')[0]}</div>
                  {stage.status === 'found' && (
                    <span className="absolute top-1 right-1 text-green-500">✓</span>
                  )}
                  {stage.status === 'missing' && stage.isRequired && (
                    <span className="absolute top-1 right-1 text-red-500">!</span>
                  )}
                </div>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-xs">
                <div className="space-y-1">
                  <p className="font-semibold">
                    Stage {stage.id}: {stage.name}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {stage.description}
                  </p>
                  <p className="text-xs">
                    Folder: <code>{stage.folderName}</code>
                  </p>
                  {stage.status === 'found' && (
                    <p className="text-xs text-green-600">
                      {stage.fileCount} files found
                      {stage.hasReadme && ' • README.md present'}
                    </p>
                  )}
                  {stage.status === 'missing' && stage.isRequired && (
                    <p className="text-xs text-red-600">
                      Required for {SDLC_TIER_CONFIGS[tier].label} tier
                    </p>
                  )}
                  {stage.status === 'optional' && (
                    <p className="text-xs text-gray-500">
                      Not required for {SDLC_TIER_CONFIGS[tier].label} tier
                    </p>
                  )}
                </div>
              </TooltipContent>
            </Tooltip>
          ))}
        </div>

        {/* Progress summary */}
        <div className="flex items-center justify-between pt-2 border-t">
          <span className="text-sm text-muted-foreground">
            {foundStageIds.size} of {requiredStages.length} required stages found
          </span>
          <span
            className={cn(
              'text-sm font-medium',
              foundStageIds.size >= requiredStages.length
                ? 'text-green-600'
                : 'text-yellow-600'
            )}
          >
            {Math.round((foundStageIds.size / requiredStages.length) * 100)}%
            Complete
          </span>
        </div>
      </div>
    </TooltipProvider>
  )
})

/**
 * CompactStageProgress component
 *
 * Horizontal bar showing stage progress
 */
export const CompactStageProgress = memo(function CompactStageProgress({
  found,
  required,
  className,
}: {
  found: number
  required: number
  className?: string
}) {
  const percentage = required > 0 ? Math.round((found / required) * 100) : 0

  return (
    <div className={cn('space-y-1', className)}>
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">Stages</span>
        <span className="font-medium">
          {found}/{required}
        </span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={cn(
            'h-full rounded-full transition-all duration-500',
            percentage >= 100
              ? 'bg-green-500'
              : percentage >= 70
                ? 'bg-yellow-500'
                : 'bg-red-500'
          )}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={found}
          aria-valuemax={required}
        />
      </div>
    </div>
  )
})
