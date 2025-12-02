/**
 * File: frontend/web/src/components/compliance/ScanHistoryTimeline.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-02
 * Authority: Frontend Lead + CTO Approved
 * Foundation: Sprint 22 Day 4 (Compliance Trend Charts)
 *
 * Description:
 * Scan history timeline with combined score and violations chart.
 * Shows correlation between compliance score and violation count.
 */

import { useMemo } from 'react'
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScanHistoryItem } from '@/api/compliance'
import { format, formatDistanceToNow } from 'date-fns'

interface ScanHistoryTimelineProps {
  /** Scan history data */
  data: ScanHistoryItem[]
  /** Chart title */
  title?: string
  /** Chart description */
  description?: string
  /** Height of the chart in pixels */
  height?: number
  /** Loading state */
  isLoading?: boolean
}

/**
 * Get status badge color
 */
function getStatusColor(score: number): string {
  if (score >= 90) return 'bg-green-100 text-green-800'
  if (score >= 70) return 'bg-yellow-100 text-yellow-800'
  if (score >= 50) return 'bg-orange-100 text-orange-800'
  return 'bg-red-100 text-red-800'
}

/**
 * Custom tooltip
 */
function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ name: string; value: number; color: string; dataKey: string }>; label?: string }) {
  if (!active || !payload || !payload.length) return null

  const scoreData = payload.find(p => p.dataKey === 'score')
  const violationsData = payload.find(p => p.dataKey === 'violations')
  const warningsData = payload.find(p => p.dataKey === 'warnings')

  return (
    <div className="bg-popover border rounded-lg shadow-lg p-3 min-w-[200px]">
      <p className="font-medium mb-2">{label}</p>
      <div className="space-y-2">
        {scoreData && (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-blue-500" />
              <span className="text-sm">Score</span>
            </div>
            <Badge variant="outline" className={getStatusColor(scoreData.value)}>
              {scoreData.value}%
            </Badge>
          </div>
        )}
        {violationsData && (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-red-500" />
              <span className="text-sm">Violations</span>
            </div>
            <span className="font-medium text-red-600">{violationsData.value}</span>
          </div>
        )}
        {warningsData && (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-yellow-500" />
              <span className="text-sm">Warnings</span>
            </div>
            <span className="font-medium text-yellow-600">{warningsData.value}</span>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Scan History Timeline Component
 */
export default function ScanHistoryTimeline({
  data,
  title = 'Scan History',
  description = 'Compliance score vs violations over time',
  height = 350,
  isLoading = false,
}: ScanHistoryTimelineProps) {
  // Transform data for chart
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return []

    return data
      .slice()
      .reverse()
      .map((item) => ({
        ...item,
        date: format(new Date(item.scanned_at), 'MMM dd HH:mm'),
        fullDate: format(new Date(item.scanned_at), 'MMM dd, yyyy HH:mm'),
        score: item.compliance_score,
        violations: item.violations_count,
        warnings: item.warnings_count,
      }))
  }, [data])

  // Latest scan stats
  const latestScan = useMemo(() => {
    if (!data || data.length === 0) return null
    return data[0] // Already sorted desc
  }, [data])

  // Calculate stats
  const stats = useMemo(() => {
    if (chartData.length === 0) return null

    const scores = chartData.map(d => d.score)
    const avgScore = scores.reduce((a, b) => a + b, 0) / scores.length
    const maxScore = Math.max(...scores)
    const minScore = Math.min(...scores)
    const totalViolations = chartData.reduce((sum, d) => sum + d.violations, 0)

    return { avgScore, maxScore, minScore, totalViolations, scanCount: chartData.length }
  }, [chartData])

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
          {latestScan && (
            <div className="text-right">
              <Badge variant="outline" className={getStatusColor(latestScan.compliance_score)}>
                {latestScan.compliance_score}% Latest
              </Badge>
              <p className="text-xs text-muted-foreground mt-1">
                {formatDistanceToNow(new Date(latestScan.scanned_at), { addSuffix: true })}
              </p>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center" style={{ height }}>
            <div className="flex flex-col items-center gap-2">
              <svg className="animate-spin h-8 w-8 text-primary" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <span className="text-sm text-muted-foreground">Loading chart data...</span>
            </div>
          </div>
        ) : chartData.length === 0 ? (
          <div className="flex items-center justify-center" style={{ height }}>
            <div className="text-center">
              <svg className="mx-auto h-12 w-12 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="mt-2 text-sm text-muted-foreground">No scan history</p>
              <p className="text-xs text-muted-foreground">Run your first compliance scan</p>
            </div>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={height}>
            <ComposedChart data={chartData} margin={{ top: 20, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11 }}
                tickLine={false}
                axisLine={{ className: 'stroke-muted' }}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis
                yAxisId="left"
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={{ className: 'stroke-muted' }}
                domain={[0, 100]}
                tickFormatter={(value) => `${value}%`}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={{ className: 'stroke-muted' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                formatter={(value) => (
                  <span className="text-sm capitalize">
                    {value === 'score' ? 'Compliance Score' : value}
                  </span>
                )}
                wrapperStyle={{ fontSize: 12, paddingTop: 10 }}
              />

              {/* Violations as bars */}
              <Bar
                yAxisId="right"
                dataKey="violations"
                fill="#ef4444"
                fillOpacity={0.6}
                radius={[4, 4, 0, 0]}
                name="violations"
              />

              {/* Warnings as bars */}
              <Bar
                yAxisId="right"
                dataKey="warnings"
                fill="#eab308"
                fillOpacity={0.6}
                radius={[4, 4, 0, 0]}
                name="warnings"
              />

              {/* Score as line */}
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="score"
                stroke="#3b82f6"
                strokeWidth={3}
                dot={{ fill: '#3b82f6', r: 5 }}
                activeDot={{ r: 8 }}
                name="score"
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}

        {/* Summary stats */}
        {!isLoading && stats && (
          <div className="grid grid-cols-5 gap-4 mt-4 pt-4 border-t">
            <div className="text-center">
              <p className="text-lg font-bold text-blue-600">{stats.avgScore.toFixed(0)}%</p>
              <p className="text-xs text-muted-foreground">Avg Score</p>
            </div>
            <div className="text-center">
              <p className="text-lg font-bold text-green-600">{stats.maxScore}%</p>
              <p className="text-xs text-muted-foreground">Best</p>
            </div>
            <div className="text-center">
              <p className="text-lg font-bold text-orange-600">{stats.minScore}%</p>
              <p className="text-xs text-muted-foreground">Worst</p>
            </div>
            <div className="text-center">
              <p className="text-lg font-bold text-red-600">{stats.totalViolations}</p>
              <p className="text-xs text-muted-foreground">Total Violations</p>
            </div>
            <div className="text-center">
              <p className="text-lg font-bold">{stats.scanCount}</p>
              <p className="text-xs text-muted-foreground">Scans</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
