/**
 * File: frontend/web/src/pages/admin/AdminDashboardPage.tsx
 * Version: 1.0.0
 * Status: ACTIVE - Sprint 37 Admin Panel
 * Date: 2025-12-16
 * Authority: CTO Approved (ADR-017)
 * Framework: SDLC 5.1.1 Complete Lifecycle
 *
 * Description:
 * Admin Dashboard page showing system-wide statistics.
 * Displays user counts, project metrics, and system health.
 *
 * Security:
 * - Requires is_superuser=true (enforced by ProtectedRoute)
 * - All data fetched from /admin/* endpoints
 */

import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { useAdminStats, useSystemHealth } from '@/api/admin'

/**
 * Stat card component for admin metrics
 */
function StatCard({
  title,
  value,
  description,
  icon,
  onClick,
  variant = 'default',
}: {
  title: string
  value: string | number
  description?: string
  icon: React.ReactNode
  onClick?: () => void
  variant?: 'default' | 'success' | 'warning' | 'danger'
}) {
  const variantClasses = {
    default: '',
    success: 'border-green-500/50',
    warning: 'border-yellow-500/50',
    danger: 'border-red-500/50',
  }

  return (
    <Card
      className={`${onClick ? 'cursor-pointer hover:bg-muted/50 transition-colors' : ''} ${variantClasses[variant]}`}
      onClick={onClick}
    >
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className="text-muted-foreground">{icon}</div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground">{description}</p>
        )}
      </CardContent>
    </Card>
  )
}

/**
 * System status badge component
 */
function StatusBadge({ status }: { status: string }) {
  const defaultConfig = { color: 'bg-red-100 text-red-700', label: 'Unhealthy' }
  const statusConfig: Record<string, { color: string; label: string }> = {
    healthy: { color: 'bg-green-100 text-green-700', label: 'Healthy' },
    degraded: { color: 'bg-yellow-100 text-yellow-700', label: 'Degraded' },
    unhealthy: defaultConfig,
  }

  const config = statusConfig[status] ?? defaultConfig

  return (
    <span className={`rounded-full px-2 py-1 text-xs font-medium ${config.color}`}>
      {config.label}
    </span>
  )
}

/**
 * Admin Dashboard page component
 */
export default function AdminDashboardPage() {
  const navigate = useNavigate()

  // Fetch admin stats
  const { data: stats, isLoading: statsLoading } = useAdminStats()

  // Fetch system health
  const { data: health, isLoading: healthLoading } = useSystemHealth()

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Admin Dashboard</h1>
            <p className="text-muted-foreground">
              System-wide statistics and health overview
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">System Status:</span>
            {healthLoading ? (
              <span className="text-sm text-muted-foreground">Loading...</span>
            ) : (
              <StatusBadge status={health?.overall_status || 'unknown'} />
            )}
          </div>
        </div>

        {/* User stats grid */}
        <div>
          <h2 className="text-lg font-semibold mb-4">User Statistics</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <StatCard
              title="Total Users"
              value={statsLoading ? '...' : stats?.total_users ?? 0}
              description="All registered users"
              onClick={() => navigate('/admin/users')}
              icon={
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              }
            />
            <StatCard
              title="Active Users"
              value={statsLoading ? '...' : stats?.active_users ?? 0}
              description="Users with is_active=true"
              variant="success"
              icon={
                <svg className="h-4 w-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              }
            />
            <StatCard
              title="Inactive Users"
              value={statsLoading ? '...' : stats?.inactive_users ?? 0}
              description="Deactivated accounts"
              variant={stats?.inactive_users && stats.inactive_users > 0 ? 'warning' : 'default'}
              icon={
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                </svg>
              }
            />
            <StatCard
              title="Superusers"
              value={statsLoading ? '...' : stats?.superusers ?? 0}
              description="Admin accounts"
              icon={
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              }
            />
          </div>
        </div>

        {/* Project stats grid */}
        <div>
          <h2 className="text-lg font-semibold mb-4">Project Statistics</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <StatCard
              title="Total Projects"
              value={statsLoading ? '...' : stats?.total_projects ?? 0}
              description="All projects in system"
              onClick={() => navigate('/projects')}
              icon={
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
              }
            />
            <StatCard
              title="Active Projects"
              value={statsLoading ? '...' : stats?.active_projects ?? 0}
              description="Projects with active gates"
              variant="success"
              icon={
                <svg className="h-4 w-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              }
            />
            <StatCard
              title="Total Gates"
              value={statsLoading ? '...' : stats?.total_gates ?? 0}
              description="All quality gates"
              onClick={() => navigate('/gates')}
              icon={
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              }
            />
          </div>
        </div>

        {/* Quick actions and system health */}
        <div className="grid gap-4 md:grid-cols-2">
          {/* Quick actions */}
          <Card>
            <CardHeader>
              <CardTitle>Admin Actions</CardTitle>
              <CardDescription>Quick access to admin functions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div
                  className="flex items-center gap-3 rounded-lg border p-3 hover:bg-muted transition-colors cursor-pointer"
                  onClick={() => navigate('/admin/users')}
                >
                  <svg className="h-5 w-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                  <div className="flex-1">
                    <p className="font-medium">User Management</p>
                    <p className="text-sm text-muted-foreground">Manage user accounts and permissions</p>
                  </div>
                  <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
                <div
                  className="flex items-center gap-3 rounded-lg border p-3 hover:bg-muted transition-colors cursor-pointer"
                  onClick={() => navigate('/admin/audit-logs')}
                >
                  <svg className="h-5 w-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  <div className="flex-1">
                    <p className="font-medium">Audit Logs</p>
                    <p className="text-sm text-muted-foreground">View system audit trail</p>
                  </div>
                  <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
                <div
                  className="flex items-center gap-3 rounded-lg border p-3 hover:bg-muted transition-colors cursor-pointer"
                  onClick={() => navigate('/admin/settings')}
                >
                  <svg className="h-5 w-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <div className="flex-1">
                    <p className="font-medium">System Settings</p>
                    <p className="text-sm text-muted-foreground">Configure system parameters</p>
                  </div>
                  <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
                <div
                  className="flex items-center gap-3 rounded-lg border p-3 hover:bg-muted transition-colors cursor-pointer"
                  onClick={() => navigate('/admin/health')}
                >
                  <svg className="h-5 w-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <div className="flex-1">
                    <p className="font-medium">System Health</p>
                    <p className="text-sm text-muted-foreground">Monitor service status and metrics</p>
                  </div>
                  <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* System health overview */}
          <Card>
            <CardHeader>
              <CardTitle>System Health</CardTitle>
              <CardDescription>
                Service status overview
                {health?.checked_at && (
                  <span className="ml-2 text-xs">
                    (Last checked: {new Date(health.checked_at).toLocaleTimeString()})
                  </span>
                )}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {healthLoading ? (
                <div className="text-center text-muted-foreground py-4">Loading...</div>
              ) : health?.services && health.services.length > 0 ? (
                <div className="space-y-3">
                  {health.services.map((service) => (
                    <div
                      key={service.name}
                      className="flex items-center justify-between border-b pb-2 last:border-0"
                    >
                      <div className="flex items-center gap-2">
                        <div
                          className={`h-2 w-2 rounded-full ${
                            service.status === 'healthy'
                              ? 'bg-green-500'
                              : service.status === 'degraded'
                              ? 'bg-yellow-500'
                              : 'bg-red-500'
                          }`}
                        />
                        <span className="font-medium">{service.name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {service.response_time_ms !== null && (
                          <span className="text-xs text-muted-foreground">
                            {service.response_time_ms}ms
                          </span>
                        )}
                        <StatusBadge status={service.status} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-muted-foreground py-4">
                  No service data available
                </div>
              )}

              {/* System metrics */}
              {health?.metrics && (
                <div className="mt-4 pt-4 border-t">
                  <h4 className="text-sm font-medium mb-3">Resource Usage</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="text-center p-2 rounded-lg bg-muted/50">
                      <p className="text-xs text-muted-foreground">CPU</p>
                      <p className="text-lg font-semibold">
                        {health.metrics.cpu_usage_percent !== null
                          ? `${health.metrics.cpu_usage_percent.toFixed(1)}%`
                          : 'N/A'}
                      </p>
                    </div>
                    <div className="text-center p-2 rounded-lg bg-muted/50">
                      <p className="text-xs text-muted-foreground">Memory</p>
                      <p className="text-lg font-semibold">
                        {health.metrics.memory_usage_percent !== null
                          ? `${health.metrics.memory_usage_percent.toFixed(1)}%`
                          : 'N/A'}
                      </p>
                    </div>
                    <div className="text-center p-2 rounded-lg bg-muted/50">
                      <p className="text-xs text-muted-foreground">Disk</p>
                      <p className="text-lg font-semibold">
                        {health.metrics.disk_usage_percent !== null
                          ? `${health.metrics.disk_usage_percent.toFixed(1)}%`
                          : 'N/A'}
                      </p>
                    </div>
                    <div className="text-center p-2 rounded-lg bg-muted/50">
                      <p className="text-xs text-muted-foreground">DB Connections</p>
                      <p className="text-lg font-semibold">
                        {health.metrics.active_connections ?? 'N/A'}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  )
}
