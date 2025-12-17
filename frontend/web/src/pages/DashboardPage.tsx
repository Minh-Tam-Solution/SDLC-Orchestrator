/**
 * File: frontend/web/src/pages/DashboardPage.tsx
 * Version: 1.1.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-16
 * Authority: Frontend Lead + CTO Approved
 * Foundation: SDLC 5.1.1 Complete Lifecycle, Zero Mock Policy
 *
 * Description:
 * Dashboard page showing overview statistics and recent activity.
 * Displays gate pass rates, active projects, and pending approvals.
 *
 * Design References:
 * - Data Model: docs/01-planning/03-Data-Model/Database-Schema.md
 * - Gate Model: backend/app/models/gate.py (source of truth for status values)
 * - Dashboard API: backend/app/api/routes/dashboard.py
 * - Gates Page: frontend/web/src/pages/GatesPage.tsx (navigation target)
 *
 * Navigation:
 * - Active Gates → /gates?status=ACTIVE
 * - Pending Approvals → /gates?status=PENDING_APPROVAL
 * - Total Projects → /projects
 * - Pass Rate → /compliance
 *
 * Changelog:
 * - v1.1.0 (2025-12-16): Add clickable stat cards with navigation
 * - v1.0.0 (2025-11-27): Initial implementation
 */

import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import DashboardLayout from '@/components/layout/DashboardLayout'
import apiClient from '@/api/client'

interface DashboardStats {
  total_projects: number
  active_gates: number
  pending_approvals: number
  pass_rate: number
}

interface RecentGate {
  id: string
  project_name: string
  gate_name: string
  status: 'passed' | 'failed' | 'pending'
  updated_at: string
}

/**
 * Stat card component - clickable to navigate to detail page
 */
function StatCard({
  title,
  value,
  description,
  icon,
  onClick,
}: {
  title: string
  value: string | number
  description?: string
  icon: React.ReactNode
  onClick?: () => void
}) {
  return (
    <Card
      className={onClick ? 'cursor-pointer hover:bg-muted/50 transition-colors' : ''}
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
 * Dashboard page component
 *
 * @returns Dashboard with statistics and recent activity
 */
export default function DashboardPage() {
  const navigate = useNavigate()

  // Fetch dashboard stats
  const { data: stats, isLoading: statsLoading } = useQuery<DashboardStats>({
    queryKey: ['dashboard', 'stats'],
    queryFn: async () => {
      try {
        const response = await apiClient.get<DashboardStats>('/dashboard/stats')
        return response.data
      } catch {
        // Return default stats if API not available yet
        return {
          total_projects: 0,
          active_gates: 0,
          pending_approvals: 0,
          pass_rate: 0,
        }
      }
    },
  })

  // Fetch recent gates
  const { data: recentGates, isLoading: gatesLoading } = useQuery<RecentGate[]>({
    queryKey: ['dashboard', 'recent-gates'],
    queryFn: async () => {
      try {
        const response = await apiClient.get<RecentGate[]>('/dashboard/recent-gates')
        return response.data
      } catch {
        // Return empty array if API not available yet
        return []
      }
    },
  })

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Overview of your SDLC projects and quality gates
          </p>
        </div>

        {/* Stats grid - Click to navigate to detail pages */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Total Projects"
            value={statsLoading ? '...' : stats?.total_projects ?? 0}
            description="Click to view all projects"
            onClick={() => navigate('/projects')}
            icon={
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
            }
          />
          <StatCard
            title="Active Gates"
            value={statsLoading ? '...' : stats?.active_gates ?? 0}
            description="Gates in progress or pending"
            onClick={() => navigate('/gates?status=ACTIVE')}
            icon={
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            }
          />
          <StatCard
            title="Pending Approvals"
            value={statsLoading ? '...' : stats?.pending_approvals ?? 0}
            description="Click to review pending gates"
            onClick={() => navigate('/gates?status=PENDING_APPROVAL')}
            icon={
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
          <StatCard
            title="Pass Rate"
            value={statsLoading ? '...' : `${stats?.pass_rate ?? 0}%`}
            description="Click to view compliance details"
            onClick={() => navigate('/compliance')}
            icon={
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            }
          />
        </div>

        {/* Recent activity */}
        <div className="grid gap-4 md:grid-cols-2">
          {/* Recent gates */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Gate Activity</CardTitle>
              <CardDescription>Latest gate evaluations across your projects</CardDescription>
            </CardHeader>
            <CardContent>
              {gatesLoading ? (
                <div className="text-center text-muted-foreground py-4">Loading...</div>
              ) : recentGates && recentGates.length > 0 ? (
                <div className="space-y-4">
                  {recentGates.map((gate) => (
                    <div
                      key={gate.id}
                      className="flex items-center justify-between border-b pb-2 last:border-0 cursor-pointer hover:bg-muted/50 rounded-lg p-2 -mx-2 transition-colors"
                      onClick={() => navigate(`/gates/${gate.id}`)}
                    >
                      <div>
                        <p className="font-medium">{gate.gate_name}</p>
                        <p className="text-sm text-muted-foreground">{gate.project_name}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <div
                          className={`rounded-full px-2 py-1 text-xs font-medium ${
                            gate.status === 'passed'
                              ? 'bg-green-100 text-green-700'
                              : gate.status === 'failed'
                              ? 'bg-red-100 text-red-700'
                              : 'bg-yellow-100 text-yellow-700'
                          }`}
                        >
                          {gate.status}
                        </div>
                        <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-muted-foreground py-8">
                  <p>No recent gate activity</p>
                  <p className="text-sm mt-1">
                    <span
                      className="text-primary cursor-pointer hover:underline"
                      onClick={() => navigate('/projects')}
                    >
                      Create a project
                    </span>{' '}
                    to get started
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
              <CardDescription>Common tasks and shortcuts</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div
                  className="flex items-center gap-3 rounded-lg border p-3 hover:bg-muted transition-colors cursor-pointer"
                  onClick={() => navigate('/projects')}
                >
                  <svg className="h-5 w-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  <div className="flex-1">
                    <p className="font-medium">Create New Project</p>
                    <p className="text-sm text-muted-foreground">Start a new SDLC project</p>
                  </div>
                  <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
                <div
                  className="flex items-center gap-3 rounded-lg border p-3 hover:bg-muted transition-colors cursor-pointer"
                  onClick={() => navigate('/evidence')}
                >
                  <svg className="h-5 w-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                  <div className="flex-1">
                    <p className="font-medium">Evidence Vault</p>
                    <p className="text-sm text-muted-foreground">View and manage evidence documents</p>
                  </div>
                  <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
                <div
                  className="flex items-center gap-3 rounded-lg border p-3 hover:bg-muted transition-colors cursor-pointer"
                  onClick={() => navigate('/policies')}
                >
                  <svg className="h-5 w-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  <div className="flex-1">
                    <p className="font-medium">Manage Policies</p>
                    <p className="text-sm text-muted-foreground">Configure gate policies</p>
                  </div>
                  <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
                <div
                  className="flex items-center gap-3 rounded-lg border p-3 hover:bg-muted transition-colors cursor-pointer"
                  onClick={() => navigate('/compliance')}
                >
                  <svg className="h-5 w-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="flex-1">
                    <p className="font-medium">Compliance Dashboard</p>
                    <p className="text-sm text-muted-foreground">Monitor compliance violations</p>
                  </div>
                  <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  )
}
