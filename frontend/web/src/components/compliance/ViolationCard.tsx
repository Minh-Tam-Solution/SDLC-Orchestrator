/**
 * File: frontend/web/src/components/compliance/ViolationCard.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-02
 * Authority: Frontend Lead + CTO Approved
 * Foundation: Sprint 21 Day 4 (Compliance Dashboard)
 *
 * Description:
 * Violation card component displaying SDLC 4.9.1 compliance violations
 * with severity indicators, AI recommendations, and resolution actions.
 */

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import {
  ViolationDetail,
  useResolveViolation,
  useGenerateViolationRecommendation,
} from '@/api/compliance'

// Severity configuration
const severityConfig = {
  critical: {
    color: 'bg-red-500',
    badge: 'bg-red-100 text-red-800 border-red-200',
    icon: (
      <svg className="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
        <path
          fillRule="evenodd"
          d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
  high: {
    color: 'bg-orange-500',
    badge: 'bg-orange-100 text-orange-800 border-orange-200',
    icon: (
      <svg className="h-5 w-5 text-orange-500" fill="currentColor" viewBox="0 0 20 20">
        <path
          fillRule="evenodd"
          d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
  medium: {
    color: 'bg-yellow-500',
    badge: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    icon: (
      <svg className="h-5 w-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
        <path
          fillRule="evenodd"
          d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
  low: {
    color: 'bg-blue-500',
    badge: 'bg-blue-100 text-blue-800 border-blue-200',
    icon: (
      <svg className="h-5 w-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
        <path
          fillRule="evenodd"
          d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
  info: {
    color: 'bg-gray-500',
    badge: 'bg-gray-100 text-gray-800 border-gray-200',
    icon: (
      <svg className="h-5 w-5 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
        <path
          fillRule="evenodd"
          d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
}

// Violation type labels
const violationTypeLabels: Record<string, string> = {
  missing_documentation: 'Missing Documentation',
  skipped_stage: 'Skipped Stage',
  insufficient_evidence: 'Insufficient Evidence',
  policy_violation: 'Policy Violation',
  doc_code_drift: 'Doc-Code Drift',
  api_not_documented: 'API Not Documented',
  db_schema_drift: 'DB Schema Drift',
  security_rule_missing: 'Security Rule Missing',
  test_coverage_low: 'Low Test Coverage',
  gate_skipped: 'Gate Skipped',
}

interface ViolationCardProps {
  violation: ViolationDetail
  onResolved?: () => void
}

/**
 * Violation Card Component
 *
 * Displays a compliance violation with:
 * - Severity indicator
 * - Violation type and description
 * - Location (if available)
 * - AI recommendation (if available)
 * - Resolution actions
 */
export default function ViolationCard({ violation, onResolved }: ViolationCardProps) {
  const [isResolveDialogOpen, setIsResolveDialogOpen] = useState(false)
  const [resolutionNotes, setResolutionNotes] = useState('')
  const [showAIRecommendation, setShowAIRecommendation] = useState(false)

  const resolveViolation = useResolveViolation()
  const generateRecommendation = useGenerateViolationRecommendation()

  const severity = severityConfig[violation.severity] || severityConfig.info
  const typeLabel = violationTypeLabels[violation.violation_type] || violation.violation_type

  const handleResolve = async () => {
    try {
      await resolveViolation.mutateAsync({
        violationId: violation.id,
        data: resolutionNotes ? { resolution_notes: resolutionNotes } : {},
      })
      setIsResolveDialogOpen(false)
      setResolutionNotes('')
      onResolved?.()
    } catch (error) {
      console.error('Failed to resolve violation:', error)
    }
  }

  const handleGenerateRecommendation = async () => {
    try {
      await generateRecommendation.mutateAsync(violation.id)
      setShowAIRecommendation(true)
    } catch (error) {
      console.error('Failed to generate AI recommendation:', error)
    }
  }

  return (
    <>
      <Card className={`border-l-4 ${violation.is_resolved ? 'opacity-60' : ''}`} style={{ borderLeftColor: severity.color.replace('bg-', '') === 'red-500' ? '#ef4444' : severity.color.replace('bg-', '') === 'orange-500' ? '#f97316' : severity.color.replace('bg-', '') === 'yellow-500' ? '#eab308' : severity.color.replace('bg-', '') === 'blue-500' ? '#3b82f6' : '#6b7280' }}>
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              {severity.icon}
              <CardTitle className="text-base font-medium">{typeLabel}</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className={severity.badge}>
                {violation.severity.toUpperCase()}
              </Badge>
              {violation.is_resolved && (
                <Badge variant="outline" className="bg-green-100 text-green-800 border-green-200">
                  RESOLVED
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Description */}
          <p className="text-sm text-muted-foreground">{violation.description}</p>

          {/* Location */}
          {violation.location && (
            <div className="flex items-center gap-2 text-sm">
              <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
              <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">
                {violation.location}
              </code>
            </div>
          )}

          {/* Recommendation */}
          {violation.recommendation && (
            <div className="rounded-md bg-muted p-3">
              <p className="text-sm font-medium mb-1">Recommendation:</p>
              <p className="text-sm text-muted-foreground">{violation.recommendation}</p>
            </div>
          )}

          {/* AI Recommendation */}
          {(violation.ai_recommendation || showAIRecommendation) && (
            <div className="rounded-md bg-blue-50 p-3 border border-blue-200">
              <div className="flex items-center gap-2 mb-2">
                <svg className="h-4 w-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM14 11a1 1 0 011 1v1h1a1 1 0 110 2h-1v1a1 1 0 11-2 0v-1h-1a1 1 0 110-2h1v-1a1 1 0 011-1z" />
                </svg>
                <p className="text-sm font-medium text-blue-800">AI Recommendation</p>
                {violation.ai_provider && (
                  <Badge variant="outline" className="text-xs bg-blue-100 border-blue-200">
                    {violation.ai_provider}
                  </Badge>
                )}
                {violation.ai_confidence && (
                  <span className="text-xs text-blue-600">
                    {violation.ai_confidence}% confidence
                  </span>
                )}
              </div>
              <p className="text-sm text-blue-900 whitespace-pre-wrap">
                {violation.ai_recommendation}
              </p>
            </div>
          )}

          {/* Resolution info */}
          {violation.is_resolved && violation.resolved_at && (
            <div className="rounded-md bg-green-50 p-3 border border-green-200">
              <p className="text-sm font-medium text-green-800 mb-1">Resolved</p>
              <p className="text-xs text-green-700">
                {new Date(violation.resolved_at).toLocaleString()}
              </p>
              {violation.resolution_notes && (
                <p className="text-sm text-green-900 mt-2">{violation.resolution_notes}</p>
              )}
            </div>
          )}

          {/* Actions */}
          {!violation.is_resolved && (
            <div className="flex items-center gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsResolveDialogOpen(true)}
              >
                <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Mark Resolved
              </Button>
              {!violation.ai_recommendation && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleGenerateRecommendation}
                  disabled={generateRecommendation.isPending}
                >
                  <svg className="h-4 w-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM14 11a1 1 0 011 1v1h1a1 1 0 110 2h-1v1a1 1 0 11-2 0v-1h-1a1 1 0 110-2h1v-1a1 1 0 011-1z" />
                  </svg>
                  {generateRecommendation.isPending ? 'Generating...' : 'Get AI Fix'}
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Resolve Dialog */}
      <Dialog open={isResolveDialogOpen} onOpenChange={setIsResolveDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Resolve Violation</DialogTitle>
            <DialogDescription>
              Mark this violation as resolved. Optionally add notes about how it was fixed.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="resolution-notes">Resolution Notes (optional)</Label>
              <Textarea
                id="resolution-notes"
                placeholder="Describe how this violation was resolved..."
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsResolveDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleResolve}
              disabled={resolveViolation.isPending}
            >
              {resolveViolation.isPending ? 'Resolving...' : 'Confirm Resolution'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
