/**
 * File: frontend/web/src/components/compliance/ViolationsByCategoryChart.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-02
 * Authority: Frontend Lead + CTO Approved
 * Foundation: Sprint 22 Day 4 (Compliance Trend Charts)
 *
 * Description:
 * Violations by category bar/pie chart using Recharts.
 * Displays distribution of violations across SDLC 4.9.1 policy categories.
 */

import { useMemo, useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
  Legend,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ViolationDetail } from '@/api/compliance'

interface ViolationsByCategoryChartProps {
  /** Violations data */
  data: ViolationDetail[]
  /** Chart title */
  title?: string
  /** Chart description */
  description?: string
  /** Height of the chart in pixels */
  height?: number
  /** Default chart type */
  defaultType?: 'bar' | 'pie'
  /** Loading state */
  isLoading?: boolean
}

/**
 * Category colors mapping
 */
const CATEGORY_COLORS: Record<string, string> = {
  documentation: '#3b82f6', // blue
  testing: '#22c55e', // green
  security: '#ef4444', // red
  performance: '#f97316', // orange
  code_quality: '#8b5cf6', // purple
  architecture: '#06b6d4', // cyan
  deployment: '#ec4899', // pink
  monitoring: '#eab308', // yellow
  compliance: '#14b8a6', // teal
  other: '#6b7280', // gray
}

/**
 * Severity colors mapping
 */
const SEVERITY_COLORS: Record<string, string> = {
  critical: '#991b1b', // dark red
  high: '#ef4444', // red
  medium: '#f97316', // orange
  low: '#eab308', // yellow
  info: '#3b82f6', // blue
}

/**
 * Get color for category
 */
function getCategoryColor(category: string): string {
  const normalizedCategory = category.toLowerCase().replace(/[^a-z]/g, '_')
  return CATEGORY_COLORS[normalizedCategory] ?? CATEGORY_COLORS['other'] ?? '#6b7280'
}

interface BarPayload {
  category: string
  count: number
  critical: number
  high: number
  medium: number
  low: number
}

/**
 * Custom tooltip for bar chart
 */
function CustomBarTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number; payload: BarPayload }>; label?: string }) {
  if (!active || !payload || !payload.length) return null

  const data = payload[0]?.payload

  if (!data) return null

  return (
    <div className="bg-popover border rounded-lg shadow-lg p-3 min-w-[180px]">
      <p className="font-medium mb-2">{label}</p>
      <div className="space-y-1 text-sm">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Total:</span>
          <span className="font-medium">{data.count}</span>
        </div>
        {data.critical > 0 && (
          <div className="flex justify-between">
            <span className="text-red-600">Critical:</span>
            <span>{data.critical}</span>
          </div>
        )}
        {data.high > 0 && (
          <div className="flex justify-between">
            <span className="text-orange-600">High:</span>
            <span>{data.high}</span>
          </div>
        )}
        {data.medium > 0 && (
          <div className="flex justify-between">
            <span className="text-yellow-600">Medium:</span>
            <span>{data.medium}</span>
          </div>
        )}
        {data.low > 0 && (
          <div className="flex justify-between">
            <span className="text-blue-600">Low:</span>
            <span>{data.low}</span>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Custom tooltip for pie chart
 */
function CustomPieTooltip({ active, payload }: { active?: boolean; payload?: Array<{ name: string; value: number; payload: { percentage: number } }> }) {
  if (!active || !payload || !payload.length) return null

  const data = payload[0]

  return (
    <div className="bg-popover border rounded-lg shadow-lg p-3">
      <p className="font-medium">{data?.name}</p>
      <div className="text-sm text-muted-foreground">
        {data?.value} violations ({data?.payload?.percentage?.toFixed(1)}%)
      </div>
    </div>
  )
}

/**
 * Violations by Category Chart Component
 */
export default function ViolationsByCategoryChart({
  data,
  title = 'Violations by Category',
  description = 'Distribution across SDLC 4.9.1 policy categories',
  height = 300,
  defaultType = 'bar',
  isLoading = false,
}: ViolationsByCategoryChartProps) {
  const [chartType, setChartType] = useState<'bar' | 'pie'>(defaultType)

  // Transform data for chart
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return []

    // Group by violation_type (category)
    const categoryMap = new Map<string, { count: number; critical: number; high: number; medium: number; low: number; info: number }>()

    data.forEach((violation) => {
      const category = violation.violation_type || 'other'
      const current = categoryMap.get(category) || { count: 0, critical: 0, high: 0, medium: 0, low: 0, info: 0 }
      current.count++
      current[violation.severity]++
      categoryMap.set(category, current)
    })

    // Convert to array and sort by count
    const total = data.length
    return Array.from(categoryMap.entries())
      .map(([category, stats]) => ({
        category: category.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' '),
        originalCategory: category,
        ...stats,
        color: getCategoryColor(category),
        percentage: (stats.count / total) * 100,
      }))
      .sort((a, b) => b.count - a.count)
  }, [data])

  // Severity breakdown for pie chart
  const severityData = useMemo(() => {
    if (!data || data.length === 0) return []

    const severityMap = new Map<string, number>()
    data.forEach((violation) => {
      severityMap.set(violation.severity, (severityMap.get(violation.severity) || 0) + 1)
    })

    const total = data.length
    return Array.from(severityMap.entries())
      .map(([severity, count]) => ({
        name: severity.charAt(0).toUpperCase() + severity.slice(1),
        value: count,
        color: SEVERITY_COLORS[severity] ?? SEVERITY_COLORS['info'] ?? '#3b82f6',
        percentage: (count / total) * 100,
      }))
      .sort((a, b) => {
        const order = ['critical', 'high', 'medium', 'low', 'info']
        return order.indexOf(a.name.toLowerCase()) - order.indexOf(b.name.toLowerCase())
      })
  }, [data])

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
          <div className="flex items-center gap-1 bg-muted rounded-lg p-1">
            <Button
              variant={chartType === 'bar' ? 'secondary' : 'ghost'}
              size="sm"
              className="h-7 px-2"
              onClick={() => setChartType('bar')}
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </Button>
            <Button
              variant={chartType === 'pie' ? 'secondary' : 'ghost'}
              size="sm"
              className="h-7 px-2"
              onClick={() => setChartType('pie')}
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
              </svg>
            </Button>
          </div>
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
              <svg className="mx-auto h-12 w-12 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="mt-2 text-sm text-muted-foreground">No violations found</p>
              <p className="text-xs text-muted-foreground">Great job! Your project is compliant</p>
            </div>
          </div>
        ) : chartType === 'bar' ? (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={chartData} layout="vertical" margin={{ top: 10, right: 30, left: 80, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 12 }} tickLine={false} axisLine={{ className: 'stroke-muted' }} />
              <YAxis
                type="category"
                dataKey="category"
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={{ className: 'stroke-muted' }}
                width={75}
              />
              <Tooltip content={<CustomBarTooltip />} cursor={{ fill: 'hsl(var(--muted))', opacity: 0.5 }} />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <ResponsiveContainer width="100%" height={height}>
            <PieChart>
              <Pie
                data={severityData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
                dataKey="value"
                nameKey="name"
                label={({ name, percentage }) => `${name} (${percentage.toFixed(0)}%)`}
                labelLine={{ stroke: 'hsl(var(--muted-foreground))', strokeWidth: 1 }}
              >
                {severityData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip content={<CustomPieTooltip />} />
              <Legend
                formatter={(value) => <span className="text-sm">{value}</span>}
                wrapperStyle={{ fontSize: 12 }}
              />
            </PieChart>
          </ResponsiveContainer>
        )}

        {/* Summary stats */}
        {!isLoading && chartData.length > 0 && (
          <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t">
            <div className="text-center">
              <p className="text-2xl font-bold">{data.length}</p>
              <p className="text-xs text-muted-foreground">Total Violations</p>
            </div>
            <div className="h-8 w-px bg-border" />
            <div className="text-center">
              <p className="text-2xl font-bold">{chartData.length}</p>
              <p className="text-xs text-muted-foreground">Categories</p>
            </div>
            <div className="h-8 w-px bg-border" />
            <div className="text-center">
              <p className="text-2xl font-bold text-red-600">
                {data.filter(v => v.severity === 'critical' || v.severity === 'high').length}
              </p>
              <p className="text-xs text-muted-foreground">Critical/High</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
