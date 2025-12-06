/**
 * File: frontend/web/src/components/sdlc/IssueList.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-06
 * Authority: Frontend Lead + CTO Approved
 * Sprint: 30 - CI/CD & Web Integration (Day 4)
 *
 * Description:
 * List component displaying validation issues with severity,
 * path, and fix suggestions.
 */

import { memo, useState, useMemo } from 'react'
import { cn } from '@/lib/utils'
import type { IssueListProps, ValidationIssue, IssueSeverity } from '@/types/sdlcValidation'
import { getSeverityColor, getSeverityIcon, SDLC_STAGES } from '@/types/sdlcValidation'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'

/**
 * IssueList component
 *
 * Displays validation issues grouped by severity:
 * - Errors: Red, blocking issues
 * - Warnings: Yellow, should fix
 * - Info: Blue, informational
 *
 * @param issues - Array of validation issues
 * @param maxItems - Maximum items to show (default: 20)
 * @param showSuggestions - Whether to show fix suggestions (default: true)
 */
export const IssueList = memo(function IssueList({
  issues,
  maxItems = 20,
  showSuggestions = true,
}: IssueListProps) {
  const [filter, setFilter] = useState<IssueSeverity | 'all'>('all')

  const filteredIssues = useMemo(() => {
    let result = issues
    if (filter !== 'all') {
      result = issues.filter((i) => i.severity === filter)
    }
    return result.slice(0, maxItems)
  }, [issues, filter, maxItems])

  const counts = useMemo(() => ({
    all: issues.length,
    error: issues.filter((i) => i.severity === 'error').length,
    warning: issues.filter((i) => i.severity === 'warning').length,
    info: issues.filter((i) => i.severity === 'info').length,
  }), [issues])

  if (issues.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <div className="text-4xl mb-2">✅</div>
        <p className="text-lg font-medium text-green-600">No Issues Found</p>
        <p className="text-sm text-muted-foreground">
          SDLC structure validation passed without issues
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Filter tabs */}
      <div className="flex items-center gap-2 flex-wrap">
        <FilterTab
          label="All"
          count={counts.all}
          active={filter === 'all'}
          onClick={() => setFilter('all')}
        />
        {counts.error > 0 && (
          <FilterTab
            label="Errors"
            count={counts.error}
            active={filter === 'error'}
            onClick={() => setFilter('error')}
            className="text-red-600"
          />
        )}
        {counts.warning > 0 && (
          <FilterTab
            label="Warnings"
            count={counts.warning}
            active={filter === 'warning'}
            onClick={() => setFilter('warning')}
            className="text-yellow-600"
          />
        )}
        {counts.info > 0 && (
          <FilterTab
            label="Info"
            count={counts.info}
            active={filter === 'info'}
            onClick={() => setFilter('info')}
            className="text-blue-600"
          />
        )}
      </div>

      {/* Issue list */}
      <div className="divide-y border rounded-lg">
        {filteredIssues.map((issue, index) => (
          <IssueItem
            key={`${issue.code}-${index}`}
            issue={issue}
            showSuggestion={showSuggestions}
          />
        ))}
      </div>

      {/* Show more indicator */}
      {issues.length > maxItems && (
        <p className="text-sm text-center text-muted-foreground">
          Showing {maxItems} of {issues.length} issues
        </p>
      )}
    </div>
  )
})

/**
 * FilterTab component
 */
const FilterTab = memo(function FilterTab({
  label,
  count,
  active,
  onClick,
  className,
}: {
  label: string
  count: number
  active: boolean
  onClick: () => void
  className?: string
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'px-3 py-1.5 text-sm rounded-md border transition-colors',
        active
          ? 'bg-primary text-primary-foreground border-primary'
          : 'bg-background hover:bg-muted border-border',
        className
      )}
    >
      {label} ({count})
    </button>
  )
})

/**
 * IssueItem component
 */
const IssueItem = memo(function IssueItem({
  issue,
  showSuggestion,
}: {
  issue: ValidationIssue
  showSuggestion: boolean
}) {
  const [isOpen, setIsOpen] = useState(false)
  const stageName = issue.stageId ? SDLC_STAGES[issue.stageId]?.name : undefined

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <div className="p-3">
        <div className="flex items-start gap-3">
          <span className="text-lg" aria-hidden="true">
            {getSeverityIcon(issue.severity)}
          </span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge
                variant={
                  issue.severity === 'error'
                    ? 'destructive'
                    : issue.severity === 'warning'
                      ? 'secondary'
                      : 'outline'
                }
                className="text-xs"
              >
                {issue.code}
              </Badge>
              {stageName && (
                <Badge variant="outline" className="text-xs">
                  Stage {issue.stageId}: {stageName}
                </Badge>
              )}
            </div>
            <p className={cn('mt-1 text-sm', getSeverityColor(issue.severity))}>
              {issue.message}
            </p>
            {issue.path && (
              <code className="mt-1 block text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                {issue.path}
              </code>
            )}
          </div>
          {showSuggestion && issue.fixSuggestion && (
            <CollapsibleTrigger asChild>
              <Button variant="ghost" size="sm" className="shrink-0">
                {isOpen ? 'Hide Fix' : 'Show Fix'}
              </Button>
            </CollapsibleTrigger>
          )}
        </div>
        {showSuggestion && issue.fixSuggestion && (
          <CollapsibleContent>
            <div className="mt-3 ml-9 p-3 bg-blue-50 border border-blue-200 rounded-md">
              <p className="text-xs font-medium text-blue-800 mb-1">
                💡 Suggested Fix:
              </p>
              <p className="text-sm text-blue-700">{issue.fixSuggestion}</p>
            </div>
          </CollapsibleContent>
        )}
      </div>
    </Collapsible>
  )
})

/**
 * IssueSummary component
 *
 * Compact summary of issues by severity
 */
export const IssueSummary = memo(function IssueSummary({
  errors,
  warnings,
  info,
  className,
}: {
  errors: number
  warnings: number
  info: number
  className?: string
}) {
  const total = errors + warnings + info

  if (total === 0) {
    return (
      <div className={cn('flex items-center gap-2 text-green-600', className)}>
        <span>✅</span>
        <span className="text-sm font-medium">No issues</span>
      </div>
    )
  }

  return (
    <div className={cn('flex items-center gap-3', className)}>
      {errors > 0 && (
        <div className="flex items-center gap-1 text-red-600">
          <span>❌</span>
          <span className="text-sm font-medium">{errors}</span>
        </div>
      )}
      {warnings > 0 && (
        <div className="flex items-center gap-1 text-yellow-600">
          <span>⚠️</span>
          <span className="text-sm font-medium">{warnings}</span>
        </div>
      )}
      {info > 0 && (
        <div className="flex items-center gap-1 text-blue-600">
          <span>ℹ️</span>
          <span className="text-sm font-medium">{info}</span>
        </div>
      )}
    </div>
  )
})
