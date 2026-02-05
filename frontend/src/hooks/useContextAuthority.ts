/**
 * =========================================================================
 * Context Authority V2 React Query Hooks
 * SDLC Orchestrator - Sprint 152 (Context Authority UI)
 *
 * Version: 1.0.0
 * Date: February 3, 2026
 * Status: ACTIVE - Sprint 152 Implementation
 * Authority: Frontend Lead + Backend Lead Approved
 * Framework: SDLC 6.0.3
 *
 * TanStack Query hooks for Context Authority V2 API endpoints:
 * - Validation & Overlay generation
 * - Template CRUD management
 * - Snapshot retrieval
 * - Health & Statistics
 *
 * Zero Mock Policy: Production-ready hooks with real API calls
 * =========================================================================
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// =========================================================================
// Types (matching backend Pydantic schemas)
// =========================================================================

export type TierEnum = "LITE" | "STANDARD" | "PROFESSIONAL" | "ENTERPRISE";
export type VibecodingZoneEnum = "GREEN" | "YELLOW" | "ORANGE" | "RED";
export type TriggerTypeEnum =
  | "gate_pass"
  | "gate_fail"
  | "index_zone"
  | "stage_constraint";
export type SubmissionTypeEnum = "PR" | "COMMIT" | "RELEASE";

export interface GateStatus {
  current_stage: string;
  last_passed_gate: string | null;
  pending_gates: string[];
}

export interface V1Result {
  adr_linkage: boolean;
  design_doc_exists: boolean;
  agents_md_fresh: boolean;
  module_annotation_consistent: boolean;
  orphan_code: boolean;
}

export interface V2Result {
  gate_violations: Record<string, unknown>[];
  index_warnings: Record<string, unknown>[];
  applied_templates: Record<string, unknown>[];
  stage_allowed: boolean;
}

// =========================================================================
// Request Types
// =========================================================================

export interface ContextValidationRequest {
  submission_id: string;
  submission_type?: SubmissionTypeEnum;
  project_id: string;
  project_tier: TierEnum;
  vibecoding_index: number;
  vibecoding_zone: VibecodingZoneEnum;
  gate_status: GateStatus;
  v1_result?: V1Result;
  changed_paths?: string[];
  top_signals?: Record<string, unknown>[];
}

export interface OverlayGenerateRequest {
  project_id: string;
  project_tier: TierEnum;
  gate_status: GateStatus;
  vibecoding_index?: number;
  vibecoding_zone?: VibecodingZoneEnum;
  top_signals?: Record<string, unknown>[];
}

export interface TemplateCreateRequest {
  name: string;
  trigger_type: TriggerTypeEnum;
  trigger_value: string;
  tier?: TierEnum;
  overlay_content: string;
  priority?: number;
  is_active?: boolean;
  description?: string;
}

export interface TemplateUpdateRequest {
  name?: string;
  trigger_type?: TriggerTypeEnum;
  trigger_value?: string;
  tier?: TierEnum;
  overlay_content?: string;
  priority?: number;
  is_active?: boolean;
  description?: string;
}

export interface TemplateFilters {
  trigger_type?: TriggerTypeEnum;
  tier?: TierEnum;
  active_only?: boolean;
  page?: number;
  page_size?: number;
}

export interface SnapshotFilters {
  valid_only?: boolean;
  zone?: VibecodingZoneEnum;
  limit?: number;
  offset?: number;
}

// =========================================================================
// Response Types
// =========================================================================

export interface ContextValidationResponse {
  submission_id: string;
  is_valid: boolean;
  v1_result: V1Result;
  v2_result: V2Result;
  dynamic_overlay: string;
  snapshot_id: string;
  validated_at: string;
}

export interface OverlayGenerateResponse {
  overlay_content: string;
  applied_templates: Record<string, unknown>[];
  variables: Record<string, unknown>;
  generated_at: string;
}

export interface TemplateResponse {
  id: string;
  name: string;
  trigger_type: string;
  trigger_value: string;
  tier: string | null;
  overlay_content: string;
  priority: number;
  is_active: boolean;
  description: string | null;
  created_by_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface TemplateListResponse {
  templates: TemplateResponse[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface TemplateApplicationRecord {
  snapshot_id: string;
  rendered_content: string;
  variables_used: Record<string, unknown> | null;
  applied_at: string;
}

export interface TemplateUsageResponse {
  template_id: string;
  template_name: string;
  application_count: number;
  recent_applications: TemplateApplicationRecord[];
  first_applied_at: string | null;
  last_applied_at: string | null;
}

export interface SnapshotResponse {
  id: string;
  submission_id: string;
  project_id: string;
  gate_status: Record<string, unknown>;
  vibecoding_index: number;
  vibecoding_zone: string;
  dynamic_overlay: string;
  v1_result: Record<string, unknown> | null;
  gate_violations: Record<string, unknown>[] | null;
  index_warnings: Record<string, unknown>[] | null;
  tier: string;
  is_valid: boolean;
  applied_template_ids: string[] | null;
  snapshot_at: string;
  created_at: string;
}

export interface SnapshotListResponse {
  submission_id: string;
  snapshots: SnapshotResponse[];
  total: number;
}

export interface ContextAuthorityHealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  version: string;
  template_count: number;
  snapshot_count_24h: number;
  avg_validation_ms: number;
  avg_overlay_ms: number;
  last_check: string;
}

export interface ContextAuthorityStatsResponse {
  total_validations: number;
  total_snapshots: number;
  validation_pass_rate: number;
  zone_distribution: Record<string, number>;
  tier_distribution: Record<string, number>;
  top_triggered_templates: Record<string, unknown>[];
  avg_templates_per_validation: number;
  period_start: string;
  period_end: string;
}

// =========================================================================
// Query Keys
// =========================================================================

export const contextAuthorityKeys = {
  all: ["context-authority"] as const,
  health: () => [...contextAuthorityKeys.all, "health"] as const,
  stats: (days?: number) => [...contextAuthorityKeys.all, "stats", days] as const,
  templates: () => [...contextAuthorityKeys.all, "templates"] as const,
  templateList: (filters?: TemplateFilters) =>
    [...contextAuthorityKeys.templates(), "list", filters] as const,
  template: (id: string) =>
    [...contextAuthorityKeys.templates(), "detail", id] as const,
  templateUsage: (id: string, days?: number) =>
    [...contextAuthorityKeys.templates(), "usage", id, days] as const,
  snapshots: () => [...contextAuthorityKeys.all, "snapshots"] as const,
  snapshot: (submissionId: string) =>
    [...contextAuthorityKeys.snapshots(), "detail", submissionId] as const,
  projectSnapshots: (projectId: string, filters?: SnapshotFilters) =>
    [...contextAuthorityKeys.snapshots(), "project", projectId, filters] as const,
};

// =========================================================================
// API Functions
// =========================================================================

const BASE_URL = "/context-authority/v2";

async function fetchHealth(): Promise<ContextAuthorityHealthResponse> {
  const response = await api.get(`${BASE_URL}/health`);
  return response.data;
}

async function fetchStats(
  days: number = 30
): Promise<ContextAuthorityStatsResponse> {
  const response = await api.get(`${BASE_URL}/stats`, { params: { days } });
  return response.data;
}

async function fetchTemplates(
  filters?: TemplateFilters
): Promise<TemplateListResponse> {
  const response = await api.get(`${BASE_URL}/templates`, { params: filters });
  return response.data;
}

async function fetchTemplate(id: string): Promise<TemplateResponse> {
  const response = await api.get(`${BASE_URL}/templates/${id}`);
  return response.data;
}

async function fetchTemplateUsage(
  id: string,
  days: number = 30
): Promise<TemplateUsageResponse> {
  const response = await api.get(`${BASE_URL}/templates/${id}/usage`, {
    params: { days },
  });
  return response.data;
}

async function createTemplate(
  data: TemplateCreateRequest
): Promise<TemplateResponse> {
  const response = await api.post(`${BASE_URL}/templates`, data);
  return response.data;
}

async function updateTemplate(
  id: string,
  data: TemplateUpdateRequest
): Promise<TemplateResponse> {
  const response = await api.put(`${BASE_URL}/templates/${id}`, data);
  return response.data;
}

async function fetchSnapshot(submissionId: string): Promise<SnapshotResponse> {
  const response = await api.get(`${BASE_URL}/snapshot/${submissionId}`);
  return response.data;
}

async function fetchProjectSnapshots(
  projectId: string,
  filters?: SnapshotFilters
): Promise<SnapshotListResponse> {
  const response = await api.get(`${BASE_URL}/snapshots/${projectId}`, {
    params: filters,
  });
  return response.data;
}

async function validateContext(
  data: ContextValidationRequest
): Promise<ContextValidationResponse> {
  const response = await api.post(`${BASE_URL}/validate`, data);
  return response.data;
}

async function generateOverlay(
  data: OverlayGenerateRequest
): Promise<OverlayGenerateResponse> {
  const response = await api.post(`${BASE_URL}/overlay`, data);
  return response.data;
}

// =========================================================================
// Query Hooks
// =========================================================================

/**
 * Fetch Context Authority V2 health status.
 */
export function useContextAuthorityHealth() {
  return useQuery({
    queryKey: contextAuthorityKeys.health(),
    queryFn: fetchHealth,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refresh every minute
  });
}

/**
 * Fetch Context Authority V2 statistics.
 * @param days Number of days to look back (default: 30)
 */
export function useContextAuthorityStats(days: number = 30) {
  return useQuery({
    queryKey: contextAuthorityKeys.stats(days),
    queryFn: () => fetchStats(days),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Fetch list of overlay templates with filtering and pagination.
 */
export function useTemplates(filters?: TemplateFilters) {
  return useQuery({
    queryKey: contextAuthorityKeys.templateList(filters),
    queryFn: () => fetchTemplates(filters),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Fetch a specific template by ID.
 */
export function useTemplate(id: string, enabled: boolean = true) {
  return useQuery({
    queryKey: contextAuthorityKeys.template(id),
    queryFn: () => fetchTemplate(id),
    enabled: !!id && enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Fetch template usage statistics.
 */
export function useTemplateUsage(id: string, days: number = 30) {
  return useQuery({
    queryKey: contextAuthorityKeys.templateUsage(id, days),
    queryFn: () => fetchTemplateUsage(id, days),
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Fetch a context snapshot by submission ID.
 */
export function useSnapshot(submissionId: string, enabled: boolean = true) {
  return useQuery({
    queryKey: contextAuthorityKeys.snapshot(submissionId),
    queryFn: () => fetchSnapshot(submissionId),
    enabled: !!submissionId && enabled,
    staleTime: 10 * 60 * 1000, // 10 minutes (snapshots are immutable)
  });
}

/**
 * Fetch snapshots for a project.
 */
export function useProjectSnapshots(
  projectId: string,
  filters?: SnapshotFilters,
  enabled: boolean = true
) {
  return useQuery({
    queryKey: contextAuthorityKeys.projectSnapshots(projectId, filters),
    queryFn: () => fetchProjectSnapshots(projectId, filters),
    enabled: !!projectId && enabled,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

// =========================================================================
// Mutation Hooks
// =========================================================================

/**
 * Create a new overlay template.
 */
export function useCreateTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: contextAuthorityKeys.templates(),
      });
    },
  });
}

/**
 * Update an existing overlay template.
 */
export function useUpdateTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TemplateUpdateRequest }) =>
      updateTemplate(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: contextAuthorityKeys.templates(),
      });
      queryClient.invalidateQueries({
        queryKey: contextAuthorityKeys.template(variables.id),
      });
    },
  });
}

/**
 * Validate code submission context.
 */
export function useValidateContext() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: validateContext,
    onSuccess: (data) => {
      // Invalidate snapshot queries as new snapshot is created
      queryClient.invalidateQueries({
        queryKey: contextAuthorityKeys.snapshots(),
      });
      // Optionally prefetch the new snapshot
      if (data.snapshot_id) {
        queryClient.setQueryData(
          contextAuthorityKeys.snapshot(data.submission_id),
          // Note: We'd need to fetch the full snapshot separately
          undefined
        );
      }
    },
  });
}

/**
 * Generate dynamic overlay without validation.
 */
export function useGenerateOverlay() {
  return useMutation({
    mutationFn: generateOverlay,
  });
}

// =========================================================================
// Utility Functions
// =========================================================================

/**
 * Get vibecoding zone color for UI styling.
 */
export function getZoneColor(zone: VibecodingZoneEnum): string {
  switch (zone) {
    case "GREEN":
      return "text-green-600 bg-green-100 border-green-200";
    case "YELLOW":
      return "text-yellow-600 bg-yellow-100 border-yellow-200";
    case "ORANGE":
      return "text-orange-600 bg-orange-100 border-orange-200";
    case "RED":
      return "text-red-600 bg-red-100 border-red-200";
    default:
      return "text-gray-600 bg-gray-100 border-gray-200";
  }
}

/**
 * Get vibecoding zone badge variant for shadcn/ui Badge component.
 */
export function getZoneBadgeVariant(
  zone: VibecodingZoneEnum
): "default" | "secondary" | "destructive" | "outline" {
  switch (zone) {
    case "GREEN":
      return "default";
    case "YELLOW":
      return "secondary";
    case "ORANGE":
      return "secondary";
    case "RED":
      return "destructive";
    default:
      return "outline";
  }
}

/**
 * Get tier badge color for UI styling.
 */
export function getTierColor(tier: TierEnum): string {
  switch (tier) {
    case "LITE":
      return "text-blue-600 bg-blue-100 border-blue-200";
    case "STANDARD":
      return "text-indigo-600 bg-indigo-100 border-indigo-200";
    case "PROFESSIONAL":
      return "text-purple-600 bg-purple-100 border-purple-200";
    case "ENTERPRISE":
      return "text-amber-600 bg-amber-100 border-amber-200";
    default:
      return "text-gray-600 bg-gray-100 border-gray-200";
  }
}

/**
 * Get trigger type display label.
 */
export function getTriggerTypeLabel(type: TriggerTypeEnum): string {
  switch (type) {
    case "gate_pass":
      return "Gate Pass";
    case "gate_fail":
      return "Gate Fail";
    case "index_zone":
      return "Index Zone";
    case "stage_constraint":
      return "Stage Constraint";
    default:
      return type;
  }
}

/**
 * Get health status color.
 */
export function getHealthStatusColor(
  status: "healthy" | "degraded" | "unhealthy"
): string {
  switch (status) {
    case "healthy":
      return "text-green-600";
    case "degraded":
      return "text-yellow-600";
    case "unhealthy":
      return "text-red-600";
    default:
      return "text-gray-600";
  }
}
