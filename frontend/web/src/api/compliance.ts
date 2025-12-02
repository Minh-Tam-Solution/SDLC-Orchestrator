/**
 * File: frontend/web/src/api/compliance.ts
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-02
 * Authority: Frontend Lead + CTO Approved
 * Foundation: Sprint 21 Day 4 (Compliance Dashboard)
 *
 * Description:
 * Compliance API client with TanStack Query hooks for SDLC 4.9.1 compliance scanning.
 * Provides hooks for scan management, violation tracking, and AI recommendations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from './client'

// ============================================================================
// Types
// ============================================================================

export interface Violation {
  type: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  location: string | null
  description: string
  recommendation: string | null
  metadata?: Record<string, unknown>
}

export interface ComplianceScan {
  id: string
  project_id: string
  triggered_by: string | null
  trigger_type: 'scheduled' | 'manual' | 'webhook' | 'ci_cd'
  compliance_score: number
  violations_count: number
  warnings_count: number
  violations: Violation[]
  warnings: Violation[]
  scanned_at: string
  duration_ms: number | null
  is_compliant: boolean
}

export interface ScanHistoryItem {
  id: string
  compliance_score: number
  violations_count: number
  warnings_count: number
  trigger_type: string
  scanned_at: string
}

export interface ViolationDetail {
  id: string
  scan_id: string
  project_id: string
  violation_type: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  location: string | null
  description: string
  recommendation: string | null
  ai_recommendation: string | null
  ai_provider: string | null
  ai_confidence: number | null
  is_resolved: boolean
  resolved_by: string | null
  resolved_at: string | null
  resolution_notes: string | null
  created_at: string
}

export interface TriggerScanRequest {
  include_doc_code_sync?: boolean
}

export interface TriggerScanResponse {
  scan_id: string
  message: string
  compliance_score: number
  violations_count: number
  warnings_count: number
  is_compliant: boolean
  scanned_at: string
}

export interface ScheduleScanRequest {
  priority?: 'high' | 'normal' | 'low'
  include_doc_code_sync?: boolean
}

export interface ScheduleScanResponse {
  job_id: string
  status: string
  message: string
  queued_at: string
}

export interface ScanJobStatus {
  job_id: string
  project_id: string
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'
  queued_at: string | null
  started_at: string | null
  completed_at: string | null
  result: Record<string, unknown> | null
  error: string | null
}

export interface QueueStatus {
  pending: number
  running: number
  completed: number
  failed: number
  total_jobs: number
}

export interface ResolveViolationRequest {
  resolution_notes?: string
}

export interface ResolveViolationResponse {
  id: string
  is_resolved: boolean
  resolved_by: string
  resolved_at: string
  resolution_notes: string | null
  message: string
}

// AI Types
export interface AIRecommendationRequest {
  violation_type: string
  severity: string
  location?: string
  description: string
  context?: Record<string, unknown>
  force_provider?: 'ollama' | 'claude' | 'gpt4' | 'rule_based'
}

export interface AIRecommendationResponse {
  recommendation: string
  provider: string
  model: string
  confidence: number
  duration_ms: number
  tokens_used: number
  cost_usd: number
  fallback_used: boolean
  fallback_reason: string | null
}

export interface GenerateViolationRecommendationResponse {
  violation_id: string
  ai_recommendation: string
  ai_provider: string
  ai_confidence: number
  message: string
}

export interface AIBudgetStatus {
  month: string
  total_spent: number
  budget: number
  remaining: number
  percentage_used: number
  by_provider: Record<string, number>
  alerts: string[]
}

export interface AIProvidersStatus {
  ollama: {
    healthy: boolean
    models?: string[]
    version?: string
    error?: string
  }
  claude: { available: boolean }
  gpt4: { available: boolean }
  rule_based: { available: boolean }
}

export interface OllamaModels {
  models: Array<{
    name: string
    size: string
    modified: string
    digest: string
  }>
  default_model: string
  ollama_url: string
}

// ============================================================================
// Query Keys
// ============================================================================

export const complianceKeys = {
  all: ['compliance'] as const,
  scans: (projectId: string) => [...complianceKeys.all, 'scans', projectId] as const,
  latestScan: (projectId: string) => [...complianceKeys.scans(projectId), 'latest'] as const,
  scanHistory: (projectId: string) => [...complianceKeys.scans(projectId), 'history'] as const,
  violations: (projectId: string) => [...complianceKeys.all, 'violations', projectId] as const,
  violation: (violationId: string) => [...complianceKeys.all, 'violation', violationId] as const,
  job: (jobId: string) => [...complianceKeys.all, 'job', jobId] as const,
  queue: () => [...complianceKeys.all, 'queue'] as const,
  ai: () => [...complianceKeys.all, 'ai'] as const,
  aiBudget: () => [...complianceKeys.ai(), 'budget'] as const,
  aiProviders: () => [...complianceKeys.ai(), 'providers'] as const,
  aiModels: () => [...complianceKeys.ai(), 'models'] as const,
}

// ============================================================================
// Scan Hooks
// ============================================================================

/**
 * Hook to get latest compliance scan for a project
 */
export function useLatestScan(projectId: string) {
  return useQuery({
    queryKey: complianceKeys.latestScan(projectId),
    queryFn: async () => {
      const response = await apiClient.get<ComplianceScan>(
        `/compliance/scans/${projectId}/latest`
      )
      return response.data
    },
    enabled: !!projectId,
    staleTime: 30000, // 30 seconds
  })
}

/**
 * Hook to get scan history for a project
 */
export function useScanHistory(projectId: string, limit = 10, offset = 0) {
  return useQuery({
    queryKey: [...complianceKeys.scanHistory(projectId), limit, offset],
    queryFn: async () => {
      const response = await apiClient.get<ScanHistoryItem[]>(
        `/compliance/scans/${projectId}/history`,
        { params: { limit, offset } }
      )
      return response.data
    },
    enabled: !!projectId,
    staleTime: 60000, // 1 minute
  })
}

/**
 * Hook to trigger immediate compliance scan
 */
export function useTriggerScan() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      projectId,
      options,
    }: {
      projectId: string
      options?: TriggerScanRequest
    }) => {
      const response = await apiClient.post<TriggerScanResponse>(
        `/compliance/scans/${projectId}`,
        options ?? {}
      )
      return response.data
    },
    onSuccess: (_data, variables) => {
      // Invalidate related queries
      queryClient.invalidateQueries({
        queryKey: complianceKeys.scans(variables.projectId),
      })
      queryClient.invalidateQueries({
        queryKey: complianceKeys.violations(variables.projectId),
      })
    },
  })
}

/**
 * Hook to schedule background compliance scan
 */
export function useScheduleScan() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      projectId,
      options,
    }: {
      projectId: string
      options?: ScheduleScanRequest
    }) => {
      const response = await apiClient.post<ScheduleScanResponse>(
        `/compliance/scans/${projectId}/schedule`,
        options ?? {}
      )
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: complianceKeys.queue(),
      })
    },
  })
}

/**
 * Hook to get scan job status
 */
export function useScanJobStatus(jobId: string) {
  return useQuery({
    queryKey: complianceKeys.job(jobId),
    queryFn: async () => {
      const response = await apiClient.get<ScanJobStatus>(
        `/compliance/jobs/${jobId}`
      )
      return response.data
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      // Poll every 2 seconds if job is still running
      const data = query.state.data
      if (data && (data.status === 'queued' || data.status === 'running')) {
        return 2000
      }
      return false
    },
  })
}

/**
 * Hook to get queue status
 */
export function useQueueStatus() {
  return useQuery({
    queryKey: complianceKeys.queue(),
    queryFn: async () => {
      const response = await apiClient.get<QueueStatus>('/compliance/queue/status')
      return response.data
    },
    staleTime: 10000, // 10 seconds
  })
}

// ============================================================================
// Violation Hooks
// ============================================================================

/**
 * Hook to get project violations
 */
export function useViolations(
  projectId: string,
  options?: {
    resolved?: boolean
    severity?: string
    limit?: number
    offset?: number
  }
) {
  return useQuery({
    queryKey: [...complianceKeys.violations(projectId), options],
    queryFn: async () => {
      const response = await apiClient.get<ViolationDetail[]>(
        `/compliance/violations/${projectId}`,
        { params: options }
      )
      return response.data
    },
    enabled: !!projectId,
    staleTime: 30000,
  })
}

/**
 * Hook to resolve a violation
 */
export function useResolveViolation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      violationId,
      data,
    }: {
      violationId: string
      data?: ResolveViolationRequest
    }) => {
      const response = await apiClient.put<ResolveViolationResponse>(
        `/compliance/violations/${violationId}/resolve`,
        data ?? {}
      )
      return response.data
    },
    onSuccess: () => {
      // Invalidate violation queries
      queryClient.invalidateQueries({
        queryKey: complianceKeys.all,
      })
    },
  })
}

// ============================================================================
// AI Recommendation Hooks
// ============================================================================

/**
 * Hook to generate AI recommendation
 */
export function useGenerateRecommendation() {
  return useMutation({
    mutationFn: async (request: AIRecommendationRequest) => {
      const response = await apiClient.post<AIRecommendationResponse>(
        '/compliance/ai/recommendations',
        request
      )
      return response.data
    },
  })
}

/**
 * Hook to generate and store AI recommendation for a violation
 */
export function useGenerateViolationRecommendation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (violationId: string) => {
      const response = await apiClient.post<GenerateViolationRecommendationResponse>(
        `/compliance/violations/${violationId}/ai-recommendation`
      )
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: complianceKeys.all,
      })
    },
  })
}

/**
 * Hook to get AI budget status
 */
export function useAIBudgetStatus() {
  return useQuery({
    queryKey: complianceKeys.aiBudget(),
    queryFn: async () => {
      const response = await apiClient.get<AIBudgetStatus>('/compliance/ai/budget')
      return response.data
    },
    staleTime: 60000, // 1 minute
  })
}

/**
 * Hook to get AI providers status
 */
export function useAIProvidersStatus() {
  return useQuery({
    queryKey: complianceKeys.aiProviders(),
    queryFn: async () => {
      const response = await apiClient.get<AIProvidersStatus>('/compliance/ai/providers')
      return response.data
    },
    staleTime: 30000,
  })
}

/**
 * Hook to get available Ollama models
 */
export function useOllamaModels() {
  return useQuery({
    queryKey: complianceKeys.aiModels(),
    queryFn: async () => {
      const response = await apiClient.get<OllamaModels>('/compliance/ai/models')
      return response.data
    },
    staleTime: 300000, // 5 minutes
  })
}
