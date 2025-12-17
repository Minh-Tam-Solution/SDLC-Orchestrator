/**
 * File: frontend/web/src/pages/admin/SystemHealthPage.tsx
 * Version: 1.0.0
 * Status: ACTIVE - Sprint 37 Admin Panel
 * Date: 2025-12-16
 * Authority: CTO Approved (ADR-017)
 * Framework: SDLC 5.1.1 Complete Lifecycle
 *
 * Description:
 * System Health page for admin panel.
 * Displays service status, resource metrics, and health checks.
 *
 * Security:
 * - Requires is_superuser=true
 * - Auto-refresh every 30 seconds
 */

import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { useSystemHealth, ServiceHealthStatus } from '@/api/admin'

/**
 * Status indicator component
 */
function StatusIndicator({ status }: { status: string }) {
  const defaultConfig = { color: 'text-red-600', bgColor: 'bg-red-500', label: 'Unhealthy' }
  const statusConfig: Record<string, { color: string; bgColor: string; label: string }> = {
    healthy: { color: 'text-green-600', bgColor: 'bg-green-500', label: 'Healthy' },
    degraded: { color: 'text-yellow-600', bgColor: 'bg-yellow-500', label: 'Degraded' },
    unhealthy: defaultConfig,
  }

  const config = statusConfig[status] ?? defaultConfig

  return (
    <div className="flex items-center gap-2">
      <div className={`h-3 w-3 rounded-full ${config.bgColor} animate-pulse`} />
      <span className={`font-medium ${config.color}`}>{config.label}</span>
    </div>
  )
}

/**
 * Service health card
 */
function ServiceHealthCard({ service }: { service: ServiceHealthStatus }) {
  return (
    <Card className={`
      ${service.status === 'healthy' ? 'border-green-500/30' : ''}
      ${service.status === 'degraded' ? 'border-yellow-500/30' : ''}
      ${service.status === 'unhealthy' ? 'border-red-500/30' : ''}
    `}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{service.name}</CardTitle>
          <StatusIndicator status={service.status} />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {service.response_time_ms !== null && (
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Response Time</span>
              <span className="font-medium">{service.response_time_ms}ms</span>
            </div>
          )}
          {service.details && Object.keys(service.details).length > 0 && (
            <div className="pt-2 border-t">
              {Object.entries(service.details).map(([key, value]) => (
                <div key={key} className="flex justify-between text-sm">
                  <span className="text-muted-foreground capitalize">
                    {key.replace(/_/g, ' ')}
                  </span>
                  <span className="font-medium">
                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Metric gauge component
 */
function MetricGauge({
  label,
  value,
  unit = '%',
  thresholds = { warning: 70, danger: 90 },
}: {
  label: string
  value: number | null
  unit?: string
  thresholds?: { warning: number; danger: number }
}) {
  if (value === null) {
    return (
      <div className="text-center p-4">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="text-2xl font-bold text-muted-foreground">N/A</p>
      </div>
    )
  }

  const getColor = () => {
    if (value >= thresholds.danger) return 'text-red-600'
    if (value >= thresholds.warning) return 'text-yellow-600'
    return 'text-green-600'
  }

  const getBarColor = () => {
    if (value >= thresholds.danger) return 'bg-red-500'
    if (value >= thresholds.warning) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-muted-foreground">{label}</span>
        <span className={`text-lg font-bold ${getColor()}`}>
          {value.toFixed(1)}{unit}
        </span>
      </div>
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-500 ${getBarColor()}`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
    </div>
  )
}

/**
 * System Health page component
 */
export default function SystemHealthPage() {
  const navigate = useNavigate()

  // Fetch system health (auto-refreshes every 30 seconds via React Query)
  const { data: health, isLoading, refetch, dataUpdatedAt } = useSystemHealth()

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page header */}
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/admin')}
                className="h-8 w-8 p-0"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </Button>
              <h1 className="text-3xl font-bold tracking-tight">System Health</h1>
            </div>
            <p className="text-muted-foreground">
              Monitor service status and resource usage
            </p>
          </div>
          <div className="flex items-center gap-4">
            {dataUpdatedAt && (
              <span className="text-sm text-muted-foreground">
                Last updated: {new Date(dataUpdatedAt).toLocaleTimeString()}
              </span>
            )}
            <Button variant="outline" onClick={() => refetch()} disabled={isLoading}>
              {isLoading ? 'Refreshing...' : 'Refresh'}
            </Button>
          </div>
        </div>

        {/* Overall status banner */}
        {health && (
          <Card className={`
            ${health.overall_status === 'healthy' ? 'bg-green-50 border-green-500/50' : ''}
            ${health.overall_status === 'degraded' ? 'bg-yellow-50 border-yellow-500/50' : ''}
            ${health.overall_status === 'unhealthy' ? 'bg-red-50 border-red-500/50' : ''}
          `}>
            <CardContent className="py-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`
                    h-12 w-12 rounded-full flex items-center justify-center
                    ${health.overall_status === 'healthy' ? 'bg-green-100' : ''}
                    ${health.overall_status === 'degraded' ? 'bg-yellow-100' : ''}
                    ${health.overall_status === 'unhealthy' ? 'bg-red-100' : ''}
                  `}>
                    {health.overall_status === 'healthy' ? (
                      <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    ) : health.overall_status === 'degraded' ? (
                      <svg className="h-6 w-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                    ) : (
                      <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    )}
                  </div>
                  <div>
                    <h2 className="text-xl font-bold">
                      System Status: {health.overall_status.charAt(0).toUpperCase() + health.overall_status.slice(1)}
                    </h2>
                    <p className="text-sm text-muted-foreground">
                      {health.services?.filter((s) => s.status === 'healthy').length || 0} of{' '}
                      {health.services?.length || 0} services operational
                    </p>
                  </div>
                </div>
                {health.checked_at && (
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Health Check</p>
                    <p className="text-sm font-medium">
                      {new Date(health.checked_at).toLocaleTimeString()}
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Resource metrics */}
        <Card>
          <CardHeader>
            <CardTitle>Resource Usage</CardTitle>
            <CardDescription>System resource utilization metrics</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="text-center py-8 text-muted-foreground">
                Loading metrics...
              </div>
            ) : health?.metrics ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MetricGauge
                  label="CPU Usage"
                  value={health.metrics.cpu_usage_percent}
                  thresholds={{ warning: 70, danger: 90 }}
                />
                <MetricGauge
                  label="Memory Usage"
                  value={health.metrics.memory_usage_percent}
                  thresholds={{ warning: 80, danger: 95 }}
                />
                <MetricGauge
                  label="Disk Usage"
                  value={health.metrics.disk_usage_percent}
                  thresholds={{ warning: 75, danger: 90 }}
                />
                <div className="p-4 text-center">
                  <p className="text-sm text-muted-foreground">DB Connections</p>
                  <p className="text-2xl font-bold">
                    {health.metrics.active_connections ?? 'N/A'}
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No metrics available
              </div>
            )}
          </CardContent>
        </Card>

        {/* Service status grid */}
        <div>
          <h2 className="text-lg font-semibold mb-4">Service Status</h2>
          {isLoading ? (
            <Card>
              <CardContent className="py-8">
                <div className="text-center text-muted-foreground">
                  Loading services...
                </div>
              </CardContent>
            </Card>
          ) : health?.services && health.services.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {health.services.map((service) => (
                <ServiceHealthCard key={service.name} service={service} />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-8">
                <div className="text-center text-muted-foreground">
                  No services to display
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Auto-refresh notice */}
        <Card className="bg-muted/50">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <svg className="h-5 w-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <div>
                <p className="text-sm font-medium">Auto-Refresh Enabled</p>
                <p className="text-xs text-muted-foreground">
                  Health data automatically refreshes every 30 seconds. Click Refresh for immediate update.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
