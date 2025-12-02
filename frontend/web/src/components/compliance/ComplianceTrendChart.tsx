/**
 * File: frontend/web/src/components/compliance/ComplianceTrendChart.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-02
 * Authority: Frontend Lead + CTO Approved
 * Foundation: Sprint 22 Day 4 (Compliance Trend Charts)
 *
 * Description:
 * Compliance score trend line chart using Recharts.
 * Displays historical compliance scores over time with threshold markers.
 */

import { useMemo } from 'react'
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { ScanHistoryItem } from '@/api/compliance'
import { format } from 'date-fns'

interface ComplianceTrendChartProps {
  /** Scan history data */
  data: ScanHistoryItem[]
  /** Chart title */
  title?: string
  /** Chart description */
  description?: string
  /** Height of the chart in pixels */
  height?: number
  /** Show area fill under the line */
  showArea?: boolean
  /** Show threshold reference lines */
  showThresholds?: boolean
  /** Loading state */
  isLoading?: boolean
}

/**
 * Get color based on compliance score
 */
function getScoreColor(score: number): string {
  if (score >= 90) return '#22c55e' // green-500
  if (score >= 70) return '#eab308' // yellow-500
  if (score >= 50) return '#f97316' // orange-500
  return '#ef4444' // red-500
}

/**
 * Custom tooltip for the chart
 */
function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number }>; label?: string }) {
  if (!active || !payload || !payload.length) return null

  const score = payload[0]?.value ?? 0
  const color = getScoreColor(score)

  return (
    <div className="bg-popover border rounded-lg shadow-lg p-3 min-w-[150px]">
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <div className="flex items-center gap-2">
        <div
          className="h-3 w-3 rounded-full"
          style={{ backgroundColor: color }}
        />
        <span className="font-semibold" style={{ color }}>
          {score}%
        </span>
        <span className="text-xs text-muted-foreground">Compliance Score</span>
      </div>
    </div>
  )
}

/**
 * Compliance Trend Chart Component
 */
export default function ComplianceTrendChart({
  data,
  title = 'Compliance Score Trend',
  description = 'Historical compliance scores over time',
  height = 300,
  showArea = true,
  showThresholds = true,
  isLoading = false,
}: ComplianceTrendChartProps) {
  // Transform data for chart
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return []

    return data
      .slice()
      .reverse() // Oldest first for timeline
      .map((item) => ({
        ...item,
        date: format(new Date(item.scanned_at), 'MMM dd'),
        fullDate: format(new Date(item.scanned_at), 'MMM dd, yyyy HH:mm'),
        score: item.compliance_score,
        color: getScoreColor(item.compliance_score),
      }))
  }, [data])

  // Calculate min/max for Y axis
  const yDomain = useMemo(() => {
    if (chartData.length === 0) return [0, 100]
    const scores = chartData.map((d) => d.score)
    const min = Math.min(...scores)
    const max = Math.max(...scores)
    return [Math.max(0, min - 10), Math.min(100, max + 10)]
  }, [chartData])

  // Get latest score for trend indicator
  const latestScore = chartData.length > 0 ? chartData[chartData.length - 1]?.score ?? null : null
  const previousScore = chartData.length > 1 ? chartData[chartData.length - 2]?.score ?? null : null
  const trend = latestScore !== null && previousScore !== null ? latestScore - previousScore : null

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
          {trend !== null && (
            <div className={`flex items-center gap-1 text-sm ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {trend >= 0 ? (
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                </svg>
              ) : (
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              )}
              <span className="font-medium">{trend > 0 ? '+' : ''}{trend.toFixed(1)}%</span>
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
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <p className="mt-2 text-sm text-muted-foreground">No scan history available</p>
              <p className="text-xs text-muted-foreground">Run a compliance scan to see trends</p>
            </div>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={height}>
            <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={{ className: 'stroke-muted' }}
              />
              <YAxis
                domain={yDomain}
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={{ className: 'stroke-muted' }}
                tickFormatter={(value) => `${value}%`}
              />
              <Tooltip content={<CustomTooltip />} />

              {/* Threshold reference lines */}
              {showThresholds && (
                <>
                  <ReferenceLine
                    y={90}
                    stroke="#22c55e"
                    strokeDasharray="5 5"
                    label={{ value: 'Excellent', position: 'right', fontSize: 10, fill: '#22c55e' }}
                  />
                  <ReferenceLine
                    y={70}
                    stroke="#eab308"
                    strokeDasharray="5 5"
                    label={{ value: 'Good', position: 'right', fontSize: 10, fill: '#eab308' }}
                  />
                  <ReferenceLine
                    y={50}
                    stroke="#f97316"
                    strokeDasharray="5 5"
                    label={{ value: 'Fair', position: 'right', fontSize: 10, fill: '#f97316' }}
                  />
                </>
              )}

              {/* Area fill */}
              {showArea && (
                <Area
                  type="monotone"
                  dataKey="score"
                  fill="url(#colorGradient)"
                  stroke="none"
                />
              )}

              {/* Main line */}
              <Line
                type="monotone"
                dataKey="score"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, stroke: '#3b82f6', strokeWidth: 2 }}
              />

              {/* Gradient definition */}
              <defs>
                <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
            </ComposedChart>
          </ResponsiveContainer>
        )}

        {/* Legend */}
        {!isLoading && chartData.length > 0 && showThresholds && (
          <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t">
            <div className="flex items-center gap-2">
              <div className="h-2 w-4 rounded bg-green-500" />
              <span className="text-xs text-muted-foreground">Excellent (90+)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-2 w-4 rounded bg-yellow-500" />
              <span className="text-xs text-muted-foreground">Good (70-89)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-2 w-4 rounded bg-orange-500" />
              <span className="text-xs text-muted-foreground">Fair (50-69)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-2 w-4 rounded bg-red-500" />
              <span className="text-xs text-muted-foreground">Poor (&lt;50)</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
