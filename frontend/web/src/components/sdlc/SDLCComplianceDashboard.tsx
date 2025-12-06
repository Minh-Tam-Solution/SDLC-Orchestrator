/**
 * File: frontend/web/src/components/sdlc/SDLCComplianceDashboard.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-06
 * Authority: Frontend Lead + CTO Approved
 * Sprint: 30 - CI/CD & Web Integration (Day 4)
 *
 * Description:
 * Main dashboard component for SDLC 5.0.0 structure validation.
 * Displays compliance score, tier, stages, history, and issues.
 */

import { memo, useState, useCallback } from 'react'
import { cn } from '@/lib/utils'
import type { SDLCComplianceDashboardProps, SDLCTier, ValidateStructureRequest } from '@/types/sdlcValidation'
import {
  useValidateStructure,
  useComplianceSummary,
  useValidationHistory,
} from '@/hooks/useSDLCValidation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { SDLCTierBadge } from './SDLCTierBadge'
import { ComplianceScoreCircle } from './ComplianceScoreCircle'
import { StageProgressGrid, CompactStageProgress } from './StageProgressGrid'
import { ValidationHistoryChart, ValidationHistoryList, MiniTrendChart } from './ValidationHistoryChart'
import { IssueList, IssueSummary } from './IssueList'

/**
 * SDLCComplianceDashboard component
 *
 * Main dashboard for SDLC 5.0.0 structure validation:
 * - Compliance score circle
 * - Tier badge and selector
 * - Stage progress grid
 * - Validation history chart
 * - Issue list with suggestions
 *
 * @param projectId - Project ID to validate
 * @param onValidate - Callback when validation completes
 * @param className - Additional CSS classes
 */
export const SDLCComplianceDashboard = memo(function SDLCComplianceDashboard({
  projectId,
  onValidate,
  className,
}: SDLCComplianceDashboardProps) {
  const [selectedTier, setSelectedTier] = useState<SDLCTier | undefined>(undefined)
  const [strictMode, setStrictMode] = useState(false)

  // Queries
  const {
    data: summary,
    isLoading: summaryLoading,
    error: summaryError,
  } = useComplianceSummary(projectId)

  const {
    data: history,
    isLoading: historyLoading,
  } = useValidationHistory(projectId, 30)

  // Mutation
  const {
    mutate: validate,
    isPending: isValidating,
    data: validationResult,
    error: validationError,
  } = useValidateStructure()

  // Handle validation
  const handleValidate = useCallback(() => {
    const request: ValidateStructureRequest = {
      strictMode,
      includeP0: true,
    }
    if (selectedTier) {
      request.tier = selectedTier
    }
    validate(
      {
        projectId,
        request,
      },
      {
        onSuccess: () => {
          onValidate?.()
        },
      }
    )
  }, [projectId, selectedTier, strictMode, validate, onValidate])

  // Loading state
  if (summaryLoading) {
    return <DashboardSkeleton />
  }

  // Error state
  if (summaryError) {
    return (
      <Card className={cn('border-red-200', className)}>
        <CardContent className="pt-6">
          <div className="text-center py-8">
            <p className="text-red-600">Failed to load compliance data</p>
            <Button variant="outline" className="mt-4" onClick={handleValidate}>
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Use latest validation result if available, otherwise use summary
  const currentScore = validationResult?.complianceScore ?? summary?.currentScore ?? 0
  const currentTier = validationResult?.tier ?? summary?.tier ?? 'lite'
  const isCompliant = validationResult?.isCompliant ?? summary?.isCompliant ?? false

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-3">
                SDLC 5.0.0 Compliance
                <SDLCTierBadge tier={currentTier} size="md" />
              </CardTitle>
              <CardDescription>
                Validate documentation structure against SDLC 5.0.0 framework
              </CardDescription>
            </div>
            <Badge
              variant={isCompliant ? 'default' : 'destructive'}
              className={cn(
                'text-sm',
                isCompliant ? 'bg-green-600' : 'bg-red-600'
              )}
            >
              {isCompliant ? '✓ Compliant' : '✗ Non-Compliant'}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between gap-6">
            {/* Score Circle */}
            <div className="flex items-center gap-6">
              <ComplianceScoreCircle score={currentScore} size="lg" />
              <div className="space-y-2">
                <div className="text-sm text-muted-foreground">
                  Last validated:{' '}
                  {summary?.lastValidatedAt
                    ? new Date(summary.lastValidatedAt).toLocaleDateString()
                    : 'Never'}
                </div>
                <div className="text-sm text-muted-foreground">
                  Total validations: {summary?.validationCount ?? 0}
                </div>
                {summary?.scoreTrend && summary.scoreTrend.length > 1 && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">Trend:</span>
                    <MiniTrendChart data={summary.scoreTrend} width={80} height={24} />
                  </div>
                )}
              </div>
            </div>

            {/* Validation Controls */}
            <div className="flex items-center gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Target Tier</label>
                <Select
                  value={selectedTier ?? 'auto'}
                  onValueChange={(v) =>
                    setSelectedTier(v === 'auto' ? undefined : (v as SDLCTier))
                  }
                >
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="Auto-detect" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">Auto-detect</SelectItem>
                    <SelectItem value="lite">🌱 Lite</SelectItem>
                    <SelectItem value="standard">⚡ Standard</SelectItem>
                    <SelectItem value="professional">🏆 Professional</SelectItem>
                    <SelectItem value="enterprise">👑 Enterprise</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Mode</label>
                <Select
                  value={strictMode ? 'strict' : 'normal'}
                  onValueChange={(v) => setStrictMode(v === 'strict')}
                >
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="normal">Normal</SelectItem>
                    <SelectItem value="strict">Strict</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button
                onClick={handleValidate}
                disabled={isValidating}
                className="mt-6"
              >
                {isValidating ? 'Validating...' : 'Validate Now'}
              </Button>
            </div>
          </div>

          {validationError && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
              Validation failed: {(validationError as Error).message}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Stage Progress Section */}
      {validationResult && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Stage Coverage</CardTitle>
            <CardDescription>
              SDLC 5.0.0 documentation stages ({validationResult.stagesFound.length}/
              {validationResult.stagesRequired} found)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <StageProgressGrid
              stagesFound={validationResult.stagesFound}
              stagesMissing={validationResult.stagesMissing}
              tier={validationResult.tier}
            />
          </CardContent>
        </Card>
      )}

      {/* History and Issues Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Validation History */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Validation History</CardTitle>
            <CardDescription>
              Compliance score trend over time
            </CardDescription>
          </CardHeader>
          <CardContent>
            {historyLoading ? (
              <Skeleton className="h-64 w-full" />
            ) : history && history.length > 0 ? (
              <ValidationHistoryChart history={history} />
            ) : (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                No validation history yet
              </div>
            )}
          </CardContent>
        </Card>

        {/* Issues Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center justify-between">
              Issues
              {validationResult && (
                <IssueSummary
                  errors={validationResult.errorCount}
                  warnings={validationResult.warningCount}
                  info={validationResult.issues.filter((i) => i.severity === 'info').length}
                />
              )}
            </CardTitle>
            <CardDescription>
              Validation issues and fix suggestions
            </CardDescription>
          </CardHeader>
          <CardContent>
            {validationResult ? (
              <IssueList
                issues={validationResult.issues}
                maxItems={10}
                showSuggestions
              />
            ) : summary?.issueSummary ? (
              <div className="text-center py-8 text-muted-foreground">
                <p>Run validation to see detailed issues</p>
                <IssueSummary
                  errors={summary.issueSummary.errors}
                  warnings={summary.issueSummary.warnings}
                  info={summary.issueSummary.info}
                  className="justify-center mt-4"
                />
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                Run validation to see issues
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Validations List */}
      {history && history.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Validations</CardTitle>
          </CardHeader>
          <CardContent>
            <ValidationHistoryList history={history} maxItems={5} />
          </CardContent>
        </Card>
      )}
    </div>
  )
})

/**
 * Dashboard skeleton for loading state
 */
const DashboardSkeleton = memo(function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-4 w-64" />
            </div>
            <Skeleton className="h-8 w-24" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-6">
            <Skeleton className="h-32 w-32 rounded-full" />
            <div className="space-y-2">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-4 w-24" />
            </div>
          </div>
        </CardContent>
      </Card>
      <div className="grid grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-40" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
      </div>
    </div>
  )
})

/**
 * CompactComplianceCard component
 *
 * Smaller card for project list displays
 */
export const CompactComplianceCard = memo(function CompactComplianceCard({
  projectName,
  score,
  tier,
  onClick,
}: {
  projectId: string
  projectName: string
  score: number
  tier: SDLCTier
  isCompliant: boolean
  onClick?: () => void
}) {
  return (
    <Card
      className={cn(
        'cursor-pointer hover:shadow-md transition-shadow',
        onClick && 'cursor-pointer'
      )}
      onClick={onClick}
    >
      <CardContent className="pt-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <p className="font-medium">{projectName}</p>
            <SDLCTierBadge tier={tier} size="sm" />
          </div>
          <div className="flex items-center gap-4">
            <CompactStageProgress found={score} required={100} />
            <div
              className={cn(
                'text-2xl font-bold',
                score >= 90
                  ? 'text-green-600'
                  : score >= 70
                    ? 'text-yellow-600'
                    : 'text-red-600'
              )}
            >
              {score}%
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
})
