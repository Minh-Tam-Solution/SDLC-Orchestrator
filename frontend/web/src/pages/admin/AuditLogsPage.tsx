/**
 * File: frontend/web/src/pages/admin/AuditLogsPage.tsx
 * Version: 1.0.0
 * Status: ACTIVE - Sprint 37 Admin Panel
 * Date: 2025-12-16
 * Authority: CTO Approved (ADR-017)
 * Framework: SDLC 5.1.1 Complete Lifecycle
 *
 * Description:
 * Audit Logs page for admin panel.
 * Displays immutable audit trail for SOC 2 compliance (CC7.1).
 *
 * Security:
 * - Requires is_superuser=true
 * - Append-only audit logs (cannot be deleted)
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { useAuditLogs, AuditLogItem } from '@/api/admin'

/**
 * Action type badge with color coding
 */
function ActionBadge({ action }: { action: string }) {
  const actionConfig: Record<string, { color: string; label: string }> = {
    // User actions
    USER_LOGIN: { color: 'bg-blue-100 text-blue-700', label: 'Login' },
    USER_LOGOUT: { color: 'bg-gray-100 text-gray-700', label: 'Logout' },
    USER_CREATED: { color: 'bg-green-100 text-green-700', label: 'User Created' },
    USER_ACTIVATED: { color: 'bg-green-100 text-green-700', label: 'Activated' },
    USER_DEACTIVATED: { color: 'bg-red-100 text-red-700', label: 'Deactivated' },
    USER_SUPERUSER_GRANTED: { color: 'bg-purple-100 text-purple-700', label: 'Admin Granted' },
    USER_SUPERUSER_REVOKED: { color: 'bg-orange-100 text-orange-700', label: 'Admin Revoked' },
    USER_BULK_ACTIVATED: { color: 'bg-green-100 text-green-700', label: 'Bulk Activated' },
    USER_BULK_DEACTIVATED: { color: 'bg-red-100 text-red-700', label: 'Bulk Deactivated' },
    // Setting actions
    SETTING_UPDATED: { color: 'bg-yellow-100 text-yellow-700', label: 'Setting Updated' },
    SETTING_ROLLBACK: { color: 'bg-orange-100 text-orange-700', label: 'Setting Rollback' },
    // Project actions
    PROJECT_CREATED: { color: 'bg-green-100 text-green-700', label: 'Project Created' },
    PROJECT_UPDATED: { color: 'bg-blue-100 text-blue-700', label: 'Project Updated' },
    PROJECT_DELETED: { color: 'bg-red-100 text-red-700', label: 'Project Deleted' },
    // Gate actions
    GATE_CREATED: { color: 'bg-green-100 text-green-700', label: 'Gate Created' },
    GATE_PASSED: { color: 'bg-green-100 text-green-700', label: 'Gate Passed' },
    GATE_FAILED: { color: 'bg-red-100 text-red-700', label: 'Gate Failed' },
    // Evidence actions
    EVIDENCE_UPLOADED: { color: 'bg-blue-100 text-blue-700', label: 'Evidence Uploaded' },
    EVIDENCE_DOWNLOADED: { color: 'bg-gray-100 text-gray-700', label: 'Evidence Downloaded' },
  }

  const config = actionConfig[action] || { color: 'bg-gray-100 text-gray-700', label: action }

  return (
    <span className={`rounded-full px-2 py-1 text-xs font-medium ${config.color}`}>
      {config.label}
    </span>
  )
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

/**
 * Audit log row component
 */
function AuditLogRow({ log }: { log: AuditLogItem }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <tr className="border-b hover:bg-muted/50">
      <td className="p-3 text-sm text-muted-foreground whitespace-nowrap">
        {formatTimestamp(log.timestamp)}
      </td>
      <td className="p-3">
        <ActionBadge action={log.action} />
      </td>
      <td className="p-3">
        <div>
          <p className="text-sm font-medium">{log.actor_email || 'System'}</p>
          {log.ip_address && (
            <p className="text-xs text-muted-foreground">{log.ip_address}</p>
          )}
        </div>
      </td>
      <td className="p-3">
        {log.target_type && (
          <div>
            <p className="text-sm">{log.target_name || log.target_id}</p>
            <p className="text-xs text-muted-foreground capitalize">{log.target_type}</p>
          </div>
        )}
      </td>
      <td className="p-3">
        {log.details && Object.keys(log.details).length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? 'Hide' : 'Details'}
          </Button>
        )}
      </td>
    </tr>
  )
}

/**
 * Audit Logs page component
 */
export default function AuditLogsPage() {
  const navigate = useNavigate()

  // Search and filter state
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [actionFilter, setActionFilter] = useState<string | undefined>(undefined)
  const [dateFrom, setDateFrom] = useState<string>('')
  const [dateTo, setDateTo] = useState<string>('')

  // Fetch audit logs
  const { data: logsData, isLoading } = useAuditLogs({
    page,
    page_size: 50,
    ...(search ? { search } : {}),
    ...(actionFilter ? { action: actionFilter } : {}),
    ...(dateFrom ? { date_from: dateFrom } : {}),
    ...(dateTo ? { date_to: dateTo } : {}),
  })

  // Common action types for filter
  const actionTypes = [
    'USER_LOGIN',
    'USER_ACTIVATED',
    'USER_DEACTIVATED',
    'USER_SUPERUSER_GRANTED',
    'USER_SUPERUSER_REVOKED',
    'SETTING_UPDATED',
    'PROJECT_CREATED',
    'GATE_PASSED',
    'GATE_FAILED',
  ]

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
              <h1 className="text-3xl font-bold tracking-tight">Audit Logs</h1>
            </div>
            <p className="text-muted-foreground">
              System audit trail for compliance and security monitoring
            </p>
          </div>
          <div className="text-sm text-muted-foreground">
            {logsData?.total ?? 0} log entries
          </div>
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-wrap gap-4">
              {/* Search */}
              <div className="flex-1 min-w-[200px]">
                <Input
                  placeholder="Search by actor email or target name..."
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value)
                    setPage(1)
                  }}
                  className="w-full"
                />
              </div>

              {/* Date range */}
              <div className="flex gap-2">
                <Input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => {
                    setDateFrom(e.target.value)
                    setPage(1)
                  }}
                  className="w-[150px]"
                  placeholder="From"
                />
                <Input
                  type="date"
                  value={dateTo}
                  onChange={(e) => {
                    setDateTo(e.target.value)
                    setPage(1)
                  }}
                  className="w-[150px]"
                  placeholder="To"
                />
              </div>

              {/* Clear filters */}
              {(search || dateFrom || dateTo || actionFilter) && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setSearch('')
                    setDateFrom('')
                    setDateTo('')
                    setActionFilter(undefined)
                    setPage(1)
                  }}
                >
                  Clear Filters
                </Button>
              )}
            </div>

            {/* Action type filters */}
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="text-sm text-muted-foreground py-1">Filter by action:</span>
              {actionTypes.map((action) => (
                <Button
                  key={action}
                  variant={actionFilter === action ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => {
                    setActionFilter(actionFilter === action ? undefined : action)
                    setPage(1)
                  }}
                >
                  {action.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase())}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Audit logs table */}
        <Card>
          <CardHeader>
            <CardTitle>Log Entries</CardTitle>
            <CardDescription>
              Immutable audit trail for SOC 2 compliance (CC7.1)
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="text-center py-8 text-muted-foreground">
                Loading audit logs...
              </div>
            ) : logsData?.items && logsData.items.length > 0 ? (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b text-left">
                        <th className="p-3 font-medium">Timestamp</th>
                        <th className="p-3 font-medium">Action</th>
                        <th className="p-3 font-medium">Actor</th>
                        <th className="p-3 font-medium">Target</th>
                        <th className="p-3 font-medium">Details</th>
                      </tr>
                    </thead>
                    <tbody>
                      {logsData.items.map((log) => (
                        <AuditLogRow key={log.id} log={log} />
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                {logsData.pages > 1 && (
                  <div className="flex items-center justify-between mt-4 pt-4 border-t">
                    <div className="text-sm text-muted-foreground">
                      Page {logsData.page} of {logsData.pages}
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page === 1}
                      >
                        Previous
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage((p) => Math.min(logsData.pages, p + 1))}
                        disabled={page === logsData.pages}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <p>No audit logs found</p>
                {(search || dateFrom || dateTo || actionFilter) && (
                  <p className="text-sm mt-1">
                    Try adjusting your search or filters
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Compliance notice */}
        <Card className="bg-muted/50">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <svg className="h-5 w-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <p className="text-sm font-medium">SOC 2 Compliance (CC7.1)</p>
                <p className="text-xs text-muted-foreground">
                  Audit logs are append-only and cannot be modified or deleted. All admin actions are automatically logged.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
