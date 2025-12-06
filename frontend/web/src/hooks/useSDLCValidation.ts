/**
 * File: frontend/web/src/hooks/useSDLCValidation.ts
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-06
 * Authority: Frontend Lead + CTO Approved
 * Sprint: 30 - CI/CD & Web Integration (Day 4)
 *
 * Description:
 * React Query hooks for SDLC 5.0.0 Structure Validation API.
 * Provides caching, optimistic updates, and error handling.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import type {
  ValidateStructureRequest,
  ValidateStructureResponse,
  ValidationHistoryItem,
  ComplianceSummary,
} from '@/types/sdlcValidation'

// =========================================================================
// QUERY KEYS
// =========================================================================

export const sdlcValidationKeys = {
  all: ['sdlcValidation'] as const,
  validation: (projectId: string) =>
    [...sdlcValidationKeys.all, 'validation', projectId] as const,
  history: (projectId: string) =>
    [...sdlcValidationKeys.all, 'history', projectId] as const,
  summary: (projectId: string) =>
    [...sdlcValidationKeys.all, 'summary', projectId] as const,
}

// =========================================================================
// API FUNCTIONS
// =========================================================================

/**
 * Validate SDLC 5.0.0 structure for a project
 */
async function validateStructure(
  projectId: string,
  request: ValidateStructureRequest
): Promise<ValidateStructureResponse> {
  const { data } = await apiClient.post<Record<string, unknown>>(
    `/projects/${projectId}/validate-structure`,
    {
      tier: request.tier,
      docs_root: request.docsRoot ?? 'docs',
      strict_mode: request.strictMode ?? false,
      include_p0: request.includeP0 ?? true,
    }
  )

  // Transform snake_case to camelCase
  return {
    id: (data['id'] as string) ?? '',
    projectId: (data['projectId'] ?? data['project_id']) as string,
    isCompliant: (data['isCompliant'] ?? data['is_compliant'] ?? data['valid']) as boolean,
    complianceScore: (data['complianceScore'] ?? data['compliance_score'] ?? data['score'] ?? 0) as number,
    tier: data['tier'] as ValidateStructureResponse['tier'],
    tierDetected: (data['tierDetected'] ?? data['tier_detected'] ?? false) as boolean,
    stagesFound: (data['stagesFound'] ?? data['stages_found'] ?? []) as ValidateStructureResponse['stagesFound'],
    stagesMissing: (data['stagesMissing'] ?? data['stages_missing'] ?? []) as string[],
    stagesRequired: (data['stagesRequired'] ?? data['stages_required'] ?? 0) as number,
    p0Status: (data['p0Status'] ?? data['p0_status'] ?? {
      total: 0,
      found: 0,
      missing: 0,
      coverage: 0,
    }) as ValidateStructureResponse['p0Status'],
    errorCount: (data['errorCount'] ?? data['error_count'] ?? data['errors'] ?? 0) as number,
    warningCount: (data['warningCount'] ?? data['warning_count'] ?? data['warnings'] ?? 0) as number,
    issues: (data['issues'] ?? []) as ValidateStructureResponse['issues'],
    validatedAt: (data['validatedAt'] ?? data['validated_at'] ?? new Date().toISOString()) as string,
    validationTimeMs: (data['validationTimeMs'] ?? data['validation_time_ms'] ?? 0) as number,
  }
}

/**
 * Get validation history for a project
 */
async function getValidationHistory(
  projectId: string,
  limit = 10,
  offset = 0
): Promise<ValidationHistoryItem[]> {
  const { data } = await apiClient.get<Record<string, unknown>[]>(
    `/projects/${projectId}/validation-history`,
    { params: { limit, offset } }
  )

  // Transform snake_case to camelCase
  return data.map((raw) => ({
    id: (raw['id'] as string) ?? '',
    isCompliant: (raw['isCompliant'] ?? raw['is_compliant'] ?? raw['valid']) as boolean,
    complianceScore: (raw['complianceScore'] ?? raw['compliance_score'] ?? raw['score'] ?? 0) as number,
    tier: raw['tier'] as ValidationHistoryItem['tier'],
    stagesFound: (raw['stagesFound'] ?? raw['stages_found'] ?? 0) as number,
    stagesRequired: (raw['stagesRequired'] ?? raw['stages_required'] ?? 0) as number,
    errorCount: (raw['errorCount'] ?? raw['error_count'] ?? raw['errors'] ?? 0) as number,
    warningCount: (raw['warningCount'] ?? raw['warning_count'] ?? raw['warnings'] ?? 0) as number,
    validatedAt: (raw['validatedAt'] ?? raw['validated_at'] ?? '') as string,
  }))
}

/**
 * Get compliance summary for a project
 */
async function getComplianceSummary(projectId: string): Promise<ComplianceSummary> {
  const { data } = await apiClient.get<Record<string, unknown>>(
    `/projects/${projectId}/compliance-summary`
  )

  // Transform snake_case to camelCase
  const lastValidatedAt = (data['lastValidatedAt'] ?? data['last_validated_at']) as string | undefined

  const result: ComplianceSummary = {
    projectId: (data['projectId'] ?? data['project_id']) as string,
    projectName: (data['projectName'] ?? data['project_name'] ?? '') as string,
    tier: data['tier'] as ComplianceSummary['tier'],
    currentScore: (data['currentScore'] ?? data['current_score'] ?? 0) as number,
    isCompliant: (data['isCompliant'] ?? data['is_compliant'] ?? false) as boolean,
    validationCount: (data['validationCount'] ?? data['validation_count'] ?? 0) as number,
    scoreTrend: (data['scoreTrend'] ?? data['score_trend'] ?? []) as number[],
    complianceHistory: (data['complianceHistory'] ?? data['compliance_history'] ?? []) as ComplianceSummary['complianceHistory'],
    stagesSummary: (data['stagesSummary'] ?? data['stages_summary'] ?? {
      found: 0,
      required: 0,
      missing: [],
    }) as ComplianceSummary['stagesSummary'],
    p0Summary: (data['p0Summary'] ?? data['p0_summary'] ?? {
      total: 0,
      found: 0,
      missing: 0,
      coverage: 0,
    }) as ComplianceSummary['p0Summary'],
    issueSummary: (data['issueSummary'] ?? data['issue_summary'] ?? {
      errors: 0,
      warnings: 0,
      info: 0,
    }) as ComplianceSummary['issueSummary'],
  }

  // Only add lastValidatedAt if it's defined (exactOptionalPropertyTypes)
  if (lastValidatedAt !== undefined) {
    result.lastValidatedAt = lastValidatedAt
  }

  return result
}

// =========================================================================
// HOOKS
// =========================================================================

/**
 * Hook for validating SDLC structure (mutation)
 *
 * @example
 * ```tsx
 * const { mutate: validate, isPending, data } = useValidateStructure()
 *
 * const handleValidate = () => {
 *   validate({
 *     projectId: project.id,
 *     request: { tier: 'professional', strictMode: true }
 *   })
 * }
 * ```
 */
export function useValidateStructure() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      projectId,
      request,
    }: {
      projectId: string
      request: ValidateStructureRequest
    }) => validateStructure(projectId, request),
    onSuccess: (data, variables) => {
      // Update latest validation cache
      queryClient.setQueryData(
        sdlcValidationKeys.validation(variables.projectId),
        data
      )

      // Invalidate history and summary to refresh
      queryClient.invalidateQueries({
        queryKey: sdlcValidationKeys.history(variables.projectId),
      })
      queryClient.invalidateQueries({
        queryKey: sdlcValidationKeys.summary(variables.projectId),
      })
    },
    onError: (error) => {
      console.error('SDLC validation failed:', error)
    },
  })
}

/**
 * Hook for getting latest validation result
 *
 * @param projectId - Project ID to get validation for
 * @param options - Query options
 *
 * @example
 * ```tsx
 * const { data: validation, isLoading } = useLatestValidation(projectId)
 *
 * if (validation) {
 *   console.log('Score:', validation.complianceScore)
 * }
 * ```
 */
export function useLatestValidation(
  projectId: string,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: sdlcValidationKeys.validation(projectId),
    queryFn: async () => {
      // Get latest from history
      const history = await getValidationHistory(projectId, 1, 0)
      if (history.length === 0) return null
      return history[0]
    },
    enabled: options?.enabled !== false && !!projectId,
    staleTime: 30_000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
  })
}

/**
 * Hook for getting validation history
 *
 * @param projectId - Project ID to get history for
 * @param limit - Number of records to return
 * @param offset - Offset for pagination
 * @param options - Query options
 *
 * @example
 * ```tsx
 * const { data: history, isLoading } = useValidationHistory(projectId, 10)
 *
 * if (history) {
 *   history.forEach(item => console.log(item.complianceScore))
 * }
 * ```
 */
export function useValidationHistory(
  projectId: string,
  limit = 10,
  offset = 0,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: [...sdlcValidationKeys.history(projectId), limit, offset],
    queryFn: () => getValidationHistory(projectId, limit, offset),
    enabled: options?.enabled !== false && !!projectId,
    staleTime: 60_000, // 1 minute
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}

/**
 * Hook for getting compliance summary
 *
 * @param projectId - Project ID to get summary for
 * @param options - Query options
 *
 * @example
 * ```tsx
 * const { data: summary, isLoading } = useComplianceSummary(projectId)
 *
 * if (summary) {
 *   console.log('Overall score:', summary.currentScore)
 *   console.log('Validation count:', summary.validationCount)
 * }
 * ```
 */
export function useComplianceSummary(
  projectId: string,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: sdlcValidationKeys.summary(projectId),
    queryFn: () => getComplianceSummary(projectId),
    enabled: options?.enabled !== false && !!projectId,
    staleTime: 60_000, // 1 minute
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}

/**
 * Hook for prefetching compliance summary
 *
 * @example
 * ```tsx
 * const prefetch = usePrefetchComplianceSummary()
 *
 * const handleProjectHover = (projectId: string) => {
 *   prefetch(projectId)
 * }
 * ```
 */
export function usePrefetchComplianceSummary() {
  const queryClient = useQueryClient()

  return (projectId: string) => {
    queryClient.prefetchQuery({
      queryKey: sdlcValidationKeys.summary(projectId),
      queryFn: () => getComplianceSummary(projectId),
      staleTime: 60_000,
    })
  }
}

/**
 * Hook for invalidating all validation queries
 */
export function useInvalidateValidationQueries() {
  const queryClient = useQueryClient()

  return (projectId?: string) => {
    if (projectId) {
      queryClient.invalidateQueries({
        queryKey: sdlcValidationKeys.validation(projectId),
      })
      queryClient.invalidateQueries({
        queryKey: sdlcValidationKeys.history(projectId),
      })
      queryClient.invalidateQueries({
        queryKey: sdlcValidationKeys.summary(projectId),
      })
    } else {
      queryClient.invalidateQueries({ queryKey: sdlcValidationKeys.all })
    }
  }
}
