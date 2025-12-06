/**
 * File: frontend/web/src/components/sdlc/ValidationHistoryChart.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-06
 * Authority: Frontend Lead + CTO Approved
 * Sprint: 30 - CI/CD & Web Integration (Day 4)
 *
 * Description:
 * Chart component displaying validation history over time.
 * Uses Recharts for interactive line/area chart visualization.
 */

import { memo, useMemo } from 'react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { cn } from '@/lib/utils'
import type { ValidationHistoryChartProps, ValidationHistoryItem } from '@/types/sdlcValidation'
import { format, parseISO } from 'date-fns'

/**
 * ValidationHistoryChart component
 *
 * Displays validation history as an area chart:
 * - X-axis: Date/time
 * - Y-axis: Compliance score (0-100)
 * - Area color: Green for compliant, red for non-compliant
 * - Reference lines at 70 (standard) and 90 (good)
 *
 * @param history - Array of validation history items
 * @param maxItems - Maximum items to display (default: 30)
 */
export const ValidationHistoryChart = memo(function ValidationHistoryChart({
  history,
  maxItems = 30,
}: ValidationHistoryChartProps) {
  const chartData = useMemo(() => {
    const items = history.slice(0, maxItems).reverse()
    return items.map((item) => ({
      date: item.validatedAt,
      score: item.complianceScore,
      isCompliant: item.isCompliant,
      errors: item.errorCount,
      warnings: item.warningCount,
    }))
  }, [history, maxItems])

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-muted-foreground">
        No validation history available
      </div>
    )
  }

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={chartData}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#22c55e" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#22c55e" stopOpacity={0.1} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            tickFormatter={(value: string) => {
              try {
                return format(parseISO(value), 'MMM d')
              } catch {
                return value
              }
            }}
            stroke="#9ca3af"
            fontSize={12}
          />
          <YAxis
            domain={[0, 100]}
            stroke="#9ca3af"
            fontSize={12}
            tickFormatter={(value: number) => `${value}%`}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null
              const firstPayload = payload[0]
              if (!firstPayload) return null
              const data = firstPayload.payload as typeof chartData[0]
              return (
                <div className="bg-white border rounded-lg shadow-lg p-3">
                  <p className="text-sm font-medium">
                    {format(parseISO(data.date), 'MMM d, yyyy h:mm a')}
                  </p>
                  <p className={cn(
                    'text-lg font-bold',
                    data.score >= 90 ? 'text-green-600' :
                    data.score >= 70 ? 'text-yellow-600' : 'text-red-600'
                  )}>
                    {data.score}%
                  </p>
                  <div className="flex gap-3 text-xs mt-1">
                    {data.errors > 0 && (
                      <span className="text-red-600">{data.errors} errors</span>
                    )}
                    {data.warnings > 0 && (
                      <span className="text-yellow-600">{data.warnings} warnings</span>
                    )}
                    {data.errors === 0 && data.warnings === 0 && (
                      <span className="text-green-600">No issues</span>
                    )}
                  </div>
                </div>
              )
            }}
          />
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
          <Area
            type="monotone"
            dataKey="score"
            stroke="#22c55e"
            strokeWidth={2}
            fill="url(#scoreGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
})

/**
 * ValidationHistoryList component
 *
 * Alternative list view for validation history
 */
export const ValidationHistoryList = memo(function ValidationHistoryList({
  history,
  maxItems = 10,
  onItemClick,
}: {
  history: ValidationHistoryItem[]
  maxItems?: number
  onItemClick?: (item: ValidationHistoryItem) => void
}) {
  const items = history.slice(0, maxItems)

  if (items.length === 0) {
    return (
      <div className="text-center py-4 text-muted-foreground">
        No validation history
      </div>
    )
  }

  return (
    <div className="divide-y">
      {items.map((item) => (
        <div
          key={item.id}
          className={cn(
            'flex items-center justify-between py-3 px-2 hover:bg-muted/50 rounded',
            onItemClick && 'cursor-pointer'
          )}
          onClick={() => onItemClick?.(item)}
        >
          <div className="flex items-center gap-3">
            <div
              className={cn(
                'w-2 h-2 rounded-full',
                item.isCompliant ? 'bg-green-500' : 'bg-red-500'
              )}
            />
            <div>
              <p className="text-sm font-medium">
                {format(parseISO(item.validatedAt), 'MMM d, yyyy h:mm a')}
              </p>
              <p className="text-xs text-muted-foreground">
                {item.stagesFound}/{item.stagesRequired} stages
                {item.errorCount > 0 && ` • ${item.errorCount} errors`}
                {item.warningCount > 0 && ` • ${item.warningCount} warnings`}
              </p>
            </div>
          </div>
          <div
            className={cn(
              'text-lg font-bold',
              item.complianceScore >= 90 ? 'text-green-600' :
              item.complianceScore >= 70 ? 'text-yellow-600' : 'text-red-600'
            )}
          >
            {item.complianceScore}%
          </div>
        </div>
      ))}
    </div>
  )
})

/**
 * MiniTrendChart component
 *
 * Small inline sparkline chart for compact displays
 */
export const MiniTrendChart = memo(function MiniTrendChart({
  data,
  width = 100,
  height = 30,
  className,
}: {
  data: number[]
  width?: number
  height?: number
  className?: string
}) {
  if (data.length < 2) {
    return <div className={cn('bg-muted rounded', className)} style={{ width, height }} />
  }

  const chartData = data.map((score, index) => ({ score, index }))
  const latestScore = data[data.length - 1] ?? 0
  const strokeColor = latestScore >= 90 ? '#22c55e' : latestScore >= 70 ? '#eab308' : '#ef4444'

  return (
    <div className={cn('inline-block', className)} style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
          <Area
            type="monotone"
            dataKey="score"
            stroke={strokeColor}
            strokeWidth={1.5}
            fill={strokeColor}
            fillOpacity={0.2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
})
