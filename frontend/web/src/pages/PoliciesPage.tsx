/**
 * File: frontend/web/src/pages/PoliciesPage.tsx
 * Version: 2.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-11-27
 * Authority: Frontend Lead + CTO Approved
 * Foundation: SDLC 4.9 Complete Lifecycle, Zero Mock Policy
 *
 * Description:
 * Policies library page for managing gate policies and policy packs.
 * Uses TanStack Query for real API data fetching from /policies endpoint.
 *
 * Week 10 Update:
 * - Replaced static data with real API integration
 * - Added TanStack Query for policy fetching
 * - Added policy filtering by SDLC stage
 * - Added loading and error states
 */

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import DashboardLayout from '@/components/layout/DashboardLayout'
import apiClient from '@/api/client'
import type { PolicyListResponse, PolicyResponse, PolicySeverity } from '@/types/api'
import { SDLC_STAGES } from '@/types/api'

/**
 * Severity badge colors
 */
const severityColors: Record<PolicySeverity, string> = {
  INFO: 'bg-blue-100 text-blue-700',
  WARNING: 'bg-yellow-100 text-yellow-700',
  ERROR: 'bg-orange-100 text-orange-700',
  CRITICAL: 'bg-red-100 text-red-700',
}

/**
 * Policy card component
 */
function PolicyCard({ policy }: { policy: PolicyResponse }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="rounded-lg border p-4">
      <div className="flex items-start justify-between">
        <div className="space-y-1 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <h4 className="font-medium">{policy.policy_name}</h4>
            <Badge variant="outline" className="text-xs">
              {policy.stage}
            </Badge>
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                severityColors[policy.severity]
              }`}
            >
              {policy.severity}
            </span>
            {policy.is_active && (
              <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                Active
              </span>
            )}
          </div>
          <p className="text-sm text-muted-foreground">{policy.description}</p>
          <p className="text-xs text-muted-foreground">
            Code: {policy.policy_code} | Version: {policy.version}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link to={`/policies/${policy.id}`}>
            <Button variant="outline" size="sm">
              View Details
            </Button>
          </Link>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? 'Hide' : 'View'} Rego
          </Button>
        </div>
      </div>

      {expanded && (
        <div className="mt-4 rounded bg-muted p-3">
          <p className="text-xs text-muted-foreground mb-2">Rego Policy Code:</p>
          <pre className="text-xs font-mono overflow-x-auto whitespace-pre-wrap">
            {policy.rego_code || 'No Rego code available'}
          </pre>
        </div>
      )}
    </div>
  )
}

/**
 * Policy pack summary component
 */
function PolicyPackSummary({
  policies,
  isLoading,
}: {
  policies: PolicyResponse[]
  isLoading: boolean
}) {
  const stages = SDLC_STAGES.map((stage) => {
    const count = policies.filter((p) => p.stage === stage.name).length
    return { ...stage, count }
  })

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
        {[...Array(10)].map((_, i) => (
          <div
            key={i}
            className="h-16 animate-pulse bg-muted rounded-lg"
          />
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
      {stages.map((stage) => (
        <div
          key={stage.code}
          className="rounded-lg border p-3 text-center"
        >
          <p className="text-xs text-muted-foreground">{stage.name}</p>
          <p className="text-lg font-semibold">{stage.count}</p>
          <p className="text-xs text-muted-foreground truncate">{stage.description}</p>
        </div>
      ))}
    </div>
  )
}

/**
 * Policies page component
 *
 * @returns Policies library page with real API data
 */
export default function PoliciesPage() {
  const [selectedStage, setSelectedStage] = useState<string>('all')
  const [page, setPage] = useState(1)
  const pageSize = 20

  // Fetch policies from real API
  const {
    data: policiesData,
    isLoading,
    isError,
    error,
  } = useQuery<PolicyListResponse>({
    queryKey: ['policies', selectedStage, page],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        is_active: 'true',
      })

      if (selectedStage !== 'all') {
        params.append('stage', selectedStage)
      }

      const response = await apiClient.get<PolicyListResponse>(`/policies?${params}`)
      return response.data
    },
  })

  // Fetch all policies for summary (without stage filter)
  const { data: allPoliciesData, isLoading: allPoliciesLoading } = useQuery<PolicyListResponse>({
    queryKey: ['policies', 'all-summary'],
    queryFn: async () => {
      const response = await apiClient.get<PolicyListResponse>('/policies?page_size=100')
      return response.data
    },
  })

  const policies = policiesData?.items ?? []
  const totalPolicies = policiesData?.total ?? 0
  const totalPages = policiesData?.pages ?? 1
  const allPolicies = allPoliciesData?.items ?? []

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Policies</h1>
            <p className="text-muted-foreground">
              Manage policy packs and gate requirements ({totalPolicies} policies)
            </p>
          </div>
          <Button>
            <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create Policy
          </Button>
        </div>

        {/* Policy pack summary */}
        <Card>
          <CardHeader>
            <CardTitle>SDLC 5.1.1 Policy Pack</CardTitle>
            <CardDescription>
              Pre-configured policies for all 10 SDLC stages
            </CardDescription>
          </CardHeader>
          <CardContent>
            <PolicyPackSummary policies={allPolicies} isLoading={allPoliciesLoading} />
          </CardContent>
        </Card>

        {/* Policy list */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Policy Library</CardTitle>
                <CardDescription>
                  Gate policies with OPA Rego validation
                </CardDescription>
              </div>
              <Select value={selectedStage} onValueChange={(v) => { setSelectedStage(v); setPage(1); }}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by stage" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Stages</SelectItem>
                  {SDLC_STAGES.map((stage) => (
                    <SelectItem key={stage.code} value={stage.name}>
                      {stage.code} - {stage.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className="h-24 animate-pulse bg-muted rounded-lg"
                  />
                ))}
              </div>
            ) : isError ? (
              <div className="text-center py-8">
                <p className="text-red-500">Error loading policies</p>
                <p className="text-sm text-muted-foreground mt-1">
                  {error instanceof Error ? error.message : 'Unknown error'}
                </p>
                <Button
                  variant="outline"
                  className="mt-4"
                  onClick={() => window.location.reload()}
                >
                  Retry
                </Button>
              </div>
            ) : policies.length > 0 ? (
              <div className="space-y-4">
                {policies.map((policy) => (
                  <PolicyCard key={policy.id} policy={policy} />
                ))}

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-between pt-4">
                    <p className="text-sm text-muted-foreground">
                      Page {page} of {totalPages}
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={page <= 1}
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                      >
                        Previous
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={page >= totalPages}
                        onClick={() => setPage((p) => p + 1)}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <svg
                  className="h-12 w-12 text-muted-foreground mx-auto mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                  />
                </svg>
                <h3 className="text-lg font-medium">No policies found</h3>
                <p className="text-muted-foreground text-center mt-1">
                  {selectedStage !== 'all'
                    ? `No policies for stage ${selectedStage}`
                    : 'No policies configured yet'}
                </p>
                <Button className="mt-4">Create First Policy</Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Custom policies info */}
        <Card>
          <CardHeader>
            <CardTitle>Custom Policies</CardTitle>
            <CardDescription>Create your own policies using Rego language</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col items-center justify-center py-8">
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
                d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
              />
            </svg>
            <h3 className="text-lg font-medium">Write Custom Rego Policies</h3>
            <p className="text-muted-foreground text-center mt-1 max-w-md">
              Create custom policies using Open Policy Agent (OPA) Rego language
              for specific compliance requirements.
            </p>
            <div className="flex gap-2 mt-4">
              <Button variant="outline">
                View Documentation
              </Button>
              <Button>
                Create Policy
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
