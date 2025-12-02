/**
 * File: frontend/web/src/components/compliance/ComplianceScoreCard.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-02
 * Authority: Frontend Lead + CTO Approved
 * Foundation: Sprint 21 Day 4 (Compliance Dashboard)
 *
 * Description:
 * Compliance score card with circular progress indicator and scan controls.
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

interface ComplianceScoreCardProps {
  score: number
  violationsCount: number
  warningsCount: number
  isCompliant: boolean
  lastScannedAt: string | null
  onScan?: () => void
  isScanning?: boolean
}

/**
 * Get score color based on value
 */
function getScoreColor(score: number): string {
  if (score >= 90) return '#22c55e' // green-500
  if (score >= 70) return '#eab308' // yellow-500
  if (score >= 50) return '#f97316' // orange-500
  return '#ef4444' // red-500
}

/**
 * Circular progress component
 */
function CircularProgress({ value, size = 120, strokeWidth = 8 }: { value: number; size?: number; strokeWidth?: number }) {
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const offset = circumference - (value / 100) * circumference
  const color = getScoreColor(value)

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg className="transform -rotate-90" width={size} height={size}>
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-muted"
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-500"
        />
      </svg>
      {/* Score text */}
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-3xl font-bold" style={{ color }}>
          {value}
        </span>
      </div>
    </div>
  )
}

/**
 * Compliance Score Card Component
 */
export default function ComplianceScoreCard({
  score,
  violationsCount,
  warningsCount,
  isCompliant,
  lastScannedAt,
  onScan,
  isScanning = false,
}: ComplianceScoreCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Compliance Score</CardTitle>
          <Badge
            variant="outline"
            className={
              isCompliant
                ? 'bg-green-100 text-green-800 border-green-200'
                : 'bg-red-100 text-red-800 border-red-200'
            }
          >
            {isCompliant ? 'COMPLIANT' : 'NON-COMPLIANT'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-6">
          {/* Circular progress */}
          <CircularProgress value={score} />

          {/* Stats */}
          <div className="flex-1 space-y-3">
            {/* Violations */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 rounded-full bg-red-500" />
                <span className="text-sm text-muted-foreground">Violations</span>
              </div>
              <span className="text-lg font-semibold text-red-600">
                {violationsCount}
              </span>
            </div>

            {/* Warnings */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 rounded-full bg-yellow-500" />
                <span className="text-sm text-muted-foreground">Warnings</span>
              </div>
              <span className="text-lg font-semibold text-yellow-600">
                {warningsCount}
              </span>
            </div>

            {/* Last scanned */}
            {lastScannedAt && (
              <div className="text-xs text-muted-foreground pt-2 border-t">
                Last scan: {new Date(lastScannedAt).toLocaleString()}
              </div>
            )}
          </div>
        </div>

        {/* Scan button */}
        {onScan && (
          <div className="mt-4 pt-4 border-t">
            <Button
              onClick={onScan}
              disabled={isScanning}
              className="w-full"
            >
              {isScanning ? (
                <>
                  <svg className="animate-spin h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Scanning...
                </>
              ) : (
                <>
                  <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Run Compliance Scan
                </>
              )}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
