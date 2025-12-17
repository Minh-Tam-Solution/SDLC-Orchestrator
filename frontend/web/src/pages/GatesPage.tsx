/**
 * File: frontend/web/src/pages/GatesPage.tsx
 * Version: 1.1.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-16
 * Authority: Frontend Lead + CTO Approved
 * Foundation: SDLC 5.1.1 Complete Lifecycle, Zero Mock Policy
 *
 * Description:
 * Gates list page showing all quality gates across projects.
 * Supports URL query param filtering by status.
 *
 * Design References:
 * - Data Model: docs/01-planning/03-Data-Model/Database-Schema.md
 * - Gate Model: backend/app/models/gate.py (source of truth for status values)
 * - Gate Status: DRAFT | PENDING_APPROVAL | IN_PROGRESS | APPROVED | REJECTED | ARCHIVED
 * - Dashboard Integration: frontend/web/src/pages/DashboardPage.tsx
 *
 * Changelog:
 * - v1.1.0 (2025-12-16): Add URL query param filtering, normalize to UPPERCASE status
 * - v1.0.0 (2025-11-27): Initial implementation
 */

import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import DashboardLayout from '@/components/layout/DashboardLayout'
import apiClient from '@/api/client'

interface Gate {
  id: string
  name: string
  project_id: string
  project_name: string
  stage: string
  // Status values are normalized to UPPERCASE in database
  status: 'DRAFT' | 'PENDING_APPROVAL' | 'IN_PROGRESS' | 'APPROVED' | 'REJECTED' | 'ARCHIVED'
  created_at: string
  updated_at: string
}

// Status options for filtering
const STATUS_OPTIONS = [
  { value: 'all', label: 'All Statuses' },
  { value: 'ACTIVE', label: 'Active (In Progress/Pending)' },
  { value: 'PENDING_APPROVAL', label: 'Pending Approval' },
  { value: 'IN_PROGRESS', label: 'In Progress' },
  { value: 'DRAFT', label: 'Draft' },
  { value: 'APPROVED', label: 'Approved' },
  { value: 'REJECTED', label: 'Rejected' },
]

// Map ACTIVE filter to multiple statuses for API
const ACTIVE_STATUSES = ['PENDING', 'PENDING_APPROVAL', 'IN_PROGRESS']

/**
 * Gates page component with URL query param filtering
 *
 * @returns Gates list with status filtering
 */
export default function GatesPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const statusFilter = searchParams.get('status') || 'all'

  // Fetch gates with optional status filter
  const { data: gatesData, isLoading } = useQuery<{ items: Gate[], total: number }>({
    queryKey: ['gates', statusFilter],
    queryFn: async () => {
      try {
        const params = new URLSearchParams()
        // For ACTIVE filter, we fetch all and filter client-side
        // For specific statuses, we can pass to API
        if (statusFilter && statusFilter !== 'all' && statusFilter !== 'ACTIVE') {
          params.append('status', statusFilter)
        }
        params.append('page_size', '100') // Get all gates for filtering
        const url = `/gates?${params}`
        const response = await apiClient.get<{ items: Gate[], total: number }>(url)

        // Client-side filter for ACTIVE status (multiple statuses)
        if (statusFilter === 'ACTIVE') {
          const filteredItems = response.data.items.filter(gate =>
            ACTIVE_STATUSES.includes(gate.status.toUpperCase())
          )
          return {
            items: filteredItems,
            total: filteredItems.length
          }
        }

        return response.data
      } catch {
        // Return empty array if API not available yet
        return { items: [], total: 0 }
      }
    },
  })

  // Handle status filter change
  const handleStatusChange = (value: string) => {
    if (value === 'all') {
      searchParams.delete('status')
    } else {
      searchParams.set('status', value)
    }
    setSearchParams(searchParams)
  }

  // Clear all filters
  const handleClearFilters = () => {
    setSearchParams({})
  }

  const gates = gatesData?.items || []

  // Get status color (all statuses are UPPERCASE)
  const getStatusColor = (status: Gate['status']) => {
    switch (status) {
      case 'APPROVED':
        return 'bg-green-100 text-green-700'
      case 'REJECTED':
        return 'bg-red-100 text-red-700'
      case 'IN_PROGRESS':
        return 'bg-blue-100 text-blue-700'
      case 'PENDING_APPROVAL':
        return 'bg-yellow-100 text-yellow-700'
      case 'DRAFT':
        return 'bg-gray-100 text-gray-700'
      case 'ARCHIVED':
        return 'bg-slate-100 text-slate-700'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  // Format status for display (all statuses are UPPERCASE)
  const formatStatus = (status: Gate['status']) => {
    const statusMap: Record<string, string> = {
      'DRAFT': 'Draft',
      'PENDING_APPROVAL': 'Pending Approval',
      'IN_PROGRESS': 'In Progress',
      'APPROVED': 'Approved',
      'REJECTED': 'Rejected',
      'ARCHIVED': 'Archived',
    }
    return statusMap[status] || status
  }

  const getStageLabel = (stage: string) => {
    const stages: Record<string, string> = {
      'G0': 'G0 - Problem Definition',
      'G1': 'G1 - Solution Validation',
      'G2': 'G2 - Design Ready',
      'G3': 'G3 - Ship Ready',
      'G4': 'G4 - Launch Ready',
      'G5': 'G5 - Operate Ready',
      'G6': 'G6 - Optimize Ready',
    }
    return stages[stage] || stage
  }

  // Get page title based on filter
  const getPageTitle = () => {
    switch (statusFilter) {
      case 'ACTIVE':
        return 'Active Gates'
      case 'PENDING_APPROVAL':
        return 'Pending Approvals'
      case 'IN_PROGRESS':
        return 'Gates In Progress'
      case 'DRAFT':
        return 'Draft Gates'
      case 'APPROVED':
        return 'Approved Gates'
      case 'REJECTED':
        return 'Rejected Gates'
      default:
        return 'All Gates'
    }
  }

  // Get page description based on filter
  const getPageDescription = () => {
    switch (statusFilter) {
      case 'ACTIVE':
        return 'Gates that are in progress, pending, or awaiting approval'
      case 'PENDING_APPROVAL':
        return 'Gates waiting for approval from authorized reviewers'
      case 'IN_PROGRESS':
        return 'Gates currently being worked on'
      case 'DRAFT':
        return 'Gates that are still being drafted'
      case 'APPROVED':
        return 'Gates that have passed quality checks'
      case 'REJECTED':
        return 'Gates that did not meet quality criteria'
      default:
        return 'Review and approve quality gates across all projects'
    }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{getPageTitle()}</h1>
            <p className="text-muted-foreground">
              {getPageDescription()}
            </p>
          </div>
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="flex-1 max-w-xs">
                <Select value={statusFilter} onValueChange={handleStatusChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Filter by status" />
                  </SelectTrigger>
                  <SelectContent>
                    {STATUS_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {statusFilter !== 'all' && (
                <Button variant="outline" onClick={handleClearFilters}>
                  Clear Filter
                </Button>
              )}
              <div className="ml-auto text-sm text-muted-foreground">
                {gatesData?.total ?? 0} gate{(gatesData?.total ?? 0) !== 1 ? 's' : ''} found
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Gates list */}
        {isLoading ? (
          <div className="text-center text-muted-foreground py-12">Loading gates...</div>
        ) : gates && gates.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {gates.map((gate) => (
              <Link key={gate.id} to={`/gates/${gate.id}`}>
                <Card className="h-full hover:shadow-md transition-shadow cursor-pointer">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg">{gate.name}</CardTitle>
                        <CardDescription className="mt-1">
                          {gate.project_name}
                        </CardDescription>
                      </div>
                      <span
                        className={`rounded-full px-2 py-1 text-xs font-medium ${getStatusColor(
                          gate.status
                        )}`}
                      >
                        {formatStatus(gate.status)}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {/* Stage */}
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Stage</span>
                        <span className="font-medium">{getStageLabel(gate.stage)}</span>
                      </div>

                      {/* Updated at */}
                      <div className="text-xs text-muted-foreground">
                        Updated {new Date(gate.updated_at).toLocaleDateString()}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <svg
                className="h-12 w-12 text-muted-foreground mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <h3 className="text-lg font-medium">No gates yet</h3>
              <p className="text-muted-foreground text-center mt-1">
                Gates will appear here when projects reach quality checkpoints
              </p>
              <Link to="/projects">
                <button className="mt-4 inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">
                  View Projects
                </button>
              </Link>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  )
}
