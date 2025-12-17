/**
 * File: frontend/web/src/pages/CompliancePage.tsx
 * Version: 1.1.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-02
 * Authority: Frontend Lead + CTO Approved
 * Foundation: Sprint 22 Day 4 (Compliance Trend Charts)
 *
 * Description:
 * SDLC 4.9.1 Compliance Dashboard showing scan results, violations, and AI recommendations.
 * Includes Recharts-based trend visualizations for compliance scores and violations.
 * Provides project selection, scan triggering, and violation management.
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import ComplianceScoreCard from '@/components/compliance/ComplianceScoreCard'
import ViolationCard from '@/components/compliance/ViolationCard'
import ComplianceTrendChart from '@/components/compliance/ComplianceTrendChart'
import ViolationsByCategoryChart from '@/components/compliance/ViolationsByCategoryChart'
import ViolationsBySeverityChart from '@/components/compliance/ViolationsBySeverityChart'
import ScanHistoryTimeline from '@/components/compliance/ScanHistoryTimeline'
// Sprint 28: AI Council Chat components (using lazy-loaded version for performance)
import { AICouncilChatLazy, TierBadge, GateProgressBar } from '@/components/council'
import { useGateStatus } from '@/hooks/useCouncil'
import {
  useLatestScan,
  useScanHistory,
  useViolations,
  useTriggerScan,
  useAIProvidersStatus,
  useAIBudgetStatus,
  ScanHistoryItem,
} from '@/api/compliance'
import apiClient from '@/api/client'

interface Project {
  id: string
  name: string
  key: string
}

/**
 * Compliance Dashboard Page
 */
export default function CompliancePage() {
  const [selectedProjectId, setSelectedProjectId] = useState<string>('')
  const [violationFilter, setViolationFilter] = useState<'all' | 'unresolved' | 'resolved'>('unresolved')

  // Sprint 28: Gate status for AI Council integration
  const gateStatus = useGateStatus(selectedProjectId, { enabled: !!selectedProjectId })

  // Fetch projects for selector
  const { data: projects = [], isLoading: projectsLoading } = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: async () => {
      try {
        const response = await apiClient.get<Project[]>('/projects')
        return response.data
      } catch {
        return []
      }
    },
  })

  // Set first project as default when loaded
  if (projects.length > 0 && !selectedProjectId && projects[0]) {
    setSelectedProjectId(projects[0].id)
  }

  // Compliance hooks
  const latestScan = useLatestScan(selectedProjectId)
  const scanHistory = useScanHistory(selectedProjectId, 10) // Increased for charts
  const resolvedFilter = violationFilter === 'all' ? undefined : violationFilter === 'resolved'
  const violations = useViolations(selectedProjectId, {
    ...(resolvedFilter !== undefined ? { resolved: resolvedFilter } : {}),
    limit: 50, // Increased for charts
  })
  const triggerScan = useTriggerScan()

  // AI status hooks
  const aiProviders = useAIProvidersStatus()
  const aiBudget = useAIBudgetStatus()

  const handleTriggerScan = async () => {
    if (!selectedProjectId) return
    try {
      await triggerScan.mutateAsync({
        projectId: selectedProjectId,
        options: { include_doc_code_sync: true },
      })
    } catch (error) {
      console.error('Failed to trigger scan:', error)
    }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold tracking-tight">Compliance Dashboard</h1>
              {/* Sprint 28: Tier Badge */}
              {selectedProjectId && gateStatus.data && (
                <TierBadge
                  tier={gateStatus.data.tier}
                  size="md"
                />
              )}
            </div>
            <p className="text-muted-foreground">
              SDLC 5.1.1 compliance scanning and violation tracking
            </p>
          </div>

          <div className="flex items-center gap-4">
            {/* Sprint 28: AI Council Chat Button (lazy-loaded for performance) */}
            <AICouncilChatLazy
              projectId={selectedProjectId}
              defaultCouncilMode={false}
              onRecommendationApplied={(recommendation) => {
                console.log('Recommendation applied:', recommendation)
                // Refetch violations after applying recommendation
                violations.refetch()
              }}
            />

            {/* Project Selector */}
            <div className="w-64">
              <Select
                value={selectedProjectId}
                onValueChange={setSelectedProjectId}
                disabled={projectsLoading}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a project..." />
                </SelectTrigger>
                <SelectContent>
                  {projects.map((project) => (
                    <SelectItem key={project.id} value={project.id}>
                      {project.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* Sprint 28: Gate Progress Bar */}
        {selectedProjectId && gateStatus.data && (
          <GateProgressBar
            currentGate={gateStatus.data.current_gate}
            gateStatuses={gateStatus.data.gates}
            tier={gateStatus.data.tier}
          />
        )}

        {!selectedProjectId ? (
          /* No project selected state */
          <Card className="py-12">
            <CardContent className="text-center">
              <svg
                className="mx-auto h-12 w-12 text-muted-foreground"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                />
              </svg>
              <h3 className="mt-4 text-lg font-medium">Select a Project</h3>
              <p className="mt-2 text-muted-foreground">
                Choose a project from the dropdown above to view compliance status
              </p>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Stats Grid */}
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {/* Compliance Score Card */}
              <ComplianceScoreCard
                score={latestScan.data?.compliance_score ?? 0}
                violationsCount={latestScan.data?.violations_count ?? 0}
                warningsCount={latestScan.data?.warnings_count ?? 0}
                isCompliant={latestScan.data?.is_compliant ?? true}
                lastScannedAt={latestScan.data?.scanned_at ?? null}
                onScan={handleTriggerScan}
                isScanning={triggerScan.isPending}
              />

              {/* AI Status Card */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg">AI Recommendations</CardTitle>
                  <CardDescription>Ollama-powered fix suggestions</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Provider Status */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Ollama</span>
                      <Badge
                        variant="outline"
                        className={
                          aiProviders.data?.ollama?.healthy
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }
                      >
                        {aiProviders.data?.ollama?.healthy ? 'Online' : 'Offline'}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Claude (Fallback)</span>
                      <Badge
                        variant="outline"
                        className={
                          aiProviders.data?.claude?.available
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }
                      >
                        {aiProviders.data?.claude?.available ? 'Available' : 'Not Configured'}
                      </Badge>
                    </div>
                  </div>

                  {/* Budget */}
                  {aiBudget.data && (
                    <div className="pt-2 border-t">
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span className="text-muted-foreground">Monthly Budget</span>
                        <span className="font-medium">
                          ${aiBudget.data.total_spent.toFixed(2)} / ${aiBudget.data.budget}
                        </span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-2">
                        <div
                          className="bg-primary h-2 rounded-full transition-all"
                          style={{ width: `${Math.min(aiBudget.data.percentage_used, 100)}%` }}
                        />
                      </div>
                      {aiBudget.data.alerts.length > 0 && (
                        <p className="text-xs text-orange-600 mt-1">
                          {aiBudget.data.alerts[0] === 'budget_exceeded'
                            ? 'Budget exceeded!'
                            : `${aiBudget.data.percentage_used}% of budget used`}
                        </p>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Scan History Card */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg">Recent Scans</CardTitle>
                  <CardDescription>Last 5 compliance scans</CardDescription>
                </CardHeader>
                <CardContent>
                  {scanHistory.isLoading ? (
                    <div className="text-center text-muted-foreground py-4">Loading...</div>
                  ) : scanHistory.data && scanHistory.data.length > 0 ? (
                    <div className="space-y-2">
                      {scanHistory.data.slice(0, 5).map((scan: ScanHistoryItem) => (
                        <div
                          key={scan.id}
                          className="flex items-center justify-between py-2 border-b last:border-0"
                        >
                          <div className="flex items-center gap-2">
                            <div
                              className="h-8 w-8 rounded-full flex items-center justify-center text-xs font-bold text-white"
                              style={{
                                backgroundColor:
                                  scan.compliance_score >= 90
                                    ? '#22c55e'
                                    : scan.compliance_score >= 70
                                    ? '#eab308'
                                    : scan.compliance_score >= 50
                                    ? '#f97316'
                                    : '#ef4444',
                              }}
                            >
                              {scan.compliance_score}
                            </div>
                            <div>
                              <p className="text-sm font-medium">
                                {scan.violations_count} violations
                              </p>
                              <p className="text-xs text-muted-foreground">
                                {new Date(scan.scanned_at).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                          <Badge variant="outline" className="text-xs">
                            {scan.trigger_type}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center text-muted-foreground py-4">
                      No scans yet. Run your first scan!
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Trend Charts Section */}
            <div className="grid gap-6 md:grid-cols-2">
              {/* Compliance Score Trend */}
              <ComplianceTrendChart
                data={scanHistory.data ?? []}
                isLoading={scanHistory.isLoading}
                title="Compliance Score Trend"
                description="Score progression over recent scans"
                height={280}
              />

              {/* Violations by Severity */}
              <ViolationsBySeverityChart
                data={scanHistory.data ?? []}
                isLoading={scanHistory.isLoading}
                title="Violations Over Time"
                description="Severity breakdown across scans"
                height={280}
              />
            </div>

            {/* Second Row of Charts */}
            <div className="grid gap-6 md:grid-cols-2">
              {/* Violations by Category */}
              <ViolationsByCategoryChart
                data={violations.data ?? []}
                isLoading={violations.isLoading}
                title="Violations by Category"
                description="Distribution by policy type"
                height={300}
              />

              {/* Scan History Timeline */}
              <ScanHistoryTimeline
                data={scanHistory.data ?? []}
                isLoading={scanHistory.isLoading}
                title="Scan History Timeline"
                description="Score vs violations correlation"
                height={300}
              />
            </div>

            {/* Violations Section */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Violations</CardTitle>
                    <CardDescription>
                      SDLC 5.1.1 compliance issues requiring attention
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Select
                      value={violationFilter}
                      onValueChange={(value: 'all' | 'unresolved' | 'resolved') =>
                        setViolationFilter(value)
                      }
                    >
                      <SelectTrigger className="w-40">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Violations</SelectItem>
                        <SelectItem value="unresolved">Unresolved</SelectItem>
                        <SelectItem value="resolved">Resolved</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {violations.isLoading ? (
                  <div className="text-center text-muted-foreground py-8">
                    Loading violations...
                  </div>
                ) : violations.data && violations.data.length > 0 ? (
                  <div className="grid gap-4 md:grid-cols-2">
                    {violations.data.map((violation) => (
                      <ViolationCard
                        key={violation.id}
                        violation={violation}
                        onResolved={() => violations.refetch()}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <svg
                      className="mx-auto h-12 w-12 text-green-500"
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
                    <h3 className="mt-4 text-lg font-medium text-green-700">
                      {violationFilter === 'unresolved'
                        ? 'No Unresolved Violations'
                        : violationFilter === 'resolved'
                        ? 'No Resolved Violations'
                        : 'No Violations Found'}
                    </h3>
                    <p className="mt-2 text-muted-foreground">
                      {violationFilter === 'unresolved'
                        ? 'All violations have been resolved!'
                        : 'Run a compliance scan to check for issues.'}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </DashboardLayout>
  )
}
