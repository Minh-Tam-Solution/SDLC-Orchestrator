/**
 * =========================================================================
 * MRP/VCR React Query Hooks
 * SDLC Orchestrator - Sprint 152 (MRP Integration)
 *
 * Version: 1.0.0
 * Date: February 3, 2026
 * Status: ACTIVE - Sprint 152 Implementation
 * Authority: Frontend Lead + Backend Lead Approved
 * Framework: SDLC 6.0.5
 *
 * TanStack Query hooks for MRP (Merge Readiness Protocol) API endpoints:
 * - MRP 5-Point Validation
 * - VCR (Verification Completion Report) management
 * - Policy tier enforcement
 * - Tier compliance reporting
 *
 * Context Authority Integration (Sprint 152):
 * - context_snapshot_id linking
 * - Context validation as part of MRP
 *
 * Zero Mock Policy: Production-ready hooks with real API calls
 * =========================================================================
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// =========================================================================
// Types (matching backend Pydantic schemas)
// =========================================================================

export type MRPPointStatus =
  | "PASSED"
  | "FAILED"
  | "SKIPPED"
  | "NOT_AVAILABLE"
  | "IN_PROGRESS";

export type VCRVerdict = "PASS" | "FAIL" | "PENDING" | "BLOCKED";

export type EvidenceSource =
  | "GITHUB_ACTIONS"
  | "LOCAL_CLI"
  | "JENKINS"
  | "GITLAB_CI"
  | "MANUAL"
  | "ORCHESTRATOR";

export type PolicyTier = "LITE" | "STANDARD" | "PROFESSIONAL" | "ENTERPRISE";

export type VibecodingZone = "GREEN" | "YELLOW" | "ORANGE" | "RED";

// =========================================================================
// Evidence Point Types
// =========================================================================

export interface BaseEvidencePoint {
  status: MRPPointStatus;
  message: string;
  required: boolean;
  collected_at: string;
  source: EvidenceSource;
  details: Record<string, unknown>;
}

export interface TestEvidence extends BaseEvidencePoint {
  coverage: number;
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  skipped_tests: number;
  execution_time_seconds: number;
  unit_coverage: number | null;
  integration_coverage: number | null;
}

export interface LintEvidence extends BaseEvidencePoint {
  total_errors: number;
  total_warnings: number;
  files_checked: number;
  linters_used: string[];
  errors_by_type: Record<string, number>;
}

export interface SecurityEvidence extends BaseEvidencePoint {
  critical_vulnerabilities: number;
  high_vulnerabilities: number;
  medium_vulnerabilities: number;
  low_vulnerabilities: number;
  scanners_used: string[];
  scan_time_seconds: number;
  vulnerabilities_by_scanner: Record<string, Record<string, unknown>>;
}

export interface BuildEvidence extends BaseEvidencePoint {
  build_success: boolean;
  build_time_seconds: number;
  build_warnings: number;
  artifacts_generated: string[];
  docker_image_tag: string | null;
  docker_image_size_mb: number | null;
}

export interface ConformanceEvidence extends BaseEvidencePoint {
  conformance_score: number;
  patterns_matched: number;
  patterns_violated: number;
  adrs_referenced: string[];
  adr_alignment_passed: boolean;
  risk_analysis_score: number | null;
  deviations: string[];
}

// =========================================================================
// MRP Validation Types
// =========================================================================

export interface MRPValidation {
  id: string;
  project_id: string;
  pr_id: string;
  commit_sha: string | null;
  test: TestEvidence;
  lint: LintEvidence;
  security: SecurityEvidence;
  build: BuildEvidence;
  conformance: ConformanceEvidence;
  tier: PolicyTier;
  // Context Authority Integration (Sprint 152)
  context_snapshot_id: string | null;
  context_validation_passed: boolean | null;
  vibecoding_index: number | null;
  vibecoding_zone: VibecodingZone | null;
  // Overall Result
  overall_passed: boolean;
  points_passed: number;
  points_required: number;
  created_at: string;
  validation_duration_ms: number;
}

// =========================================================================
// VCR Types
// =========================================================================

export interface VCR {
  id: string;
  project_id: string;
  pr_id: string;
  commit_sha: string | null;
  mrp_validation: MRPValidation;
  verdict: VCRVerdict;
  verdict_reason: string;
  evidence_hash: string | null;
  evidence_path: string | null;
  previous_hash: string | null;
  created_at: string;
  created_by: string | null;
  tier: PolicyTier;
  crp_id: string | null;
  crp_approved: boolean | null;
  // Context Authority Integration (Sprint 152)
  context_snapshot_id: string | null;
  context_snapshot_hash: string | null;
}

// =========================================================================
// Request Types
// =========================================================================

export interface ValidateMRPRequest {
  project_id: string;
  pr_id: string;
  commit_sha?: string;
  force_refresh?: boolean;
  // Context Authority Integration (Sprint 152)
  context_snapshot_id?: string;
  include_context_validation?: boolean;
}

export interface EnforcePoliciesRequest {
  project_id: string;
  pr_id: string;
  tier_override?: PolicyTier;
  commit_sha?: string;
}

export interface CompareTiersRequest {
  current_tier: PolicyTier;
  target_tier: PolicyTier;
}

// =========================================================================
// Response Types
// =========================================================================

export interface ValidateMRPResponse {
  mrp_validation: MRPValidation;
  vcr: VCR | null;
  github_check_url: string | null;
  // Context Authority Integration (Sprint 152)
  context_validation_message: string | null;
  context_overlay_applied: string | null;
}

export interface VCRHistoryResponse {
  vcrs: VCR[];
  total: number;
  project_id: string;
  pr_id: string | null;
}

export interface PolicyTierInfo {
  tier: PolicyTier;
  display_name: string;
  description: string;
  target_audience: string;
  enforcement_mode: string;
  test_coverage_required: number;
  mrp_points_required: number;
  required_checks: string[];
}

export interface AllTiersResponse {
  tiers: PolicyTierInfo[];
}

export interface CompareTiersResponse {
  current_tier: PolicyTier;
  target_tier: PolicyTier;
  direction: "upgrade" | "downgrade" | "same";
  new_requirements: string[];
  removed_requirements: string[];
  stricter_thresholds: Record<string, unknown>;
  relaxed_thresholds: Record<string, unknown>;
  current_mrp_points: number;
  target_mrp_points: number;
}

export interface TierComplianceReport {
  project_id: string;
  current_tier: PolicyTier;
  is_compliant: boolean;
  compliance_score: number;
  missing_requirements: string[];
  recommendations: string[];
  suggested_tier: PolicyTier | null;
  generated_at: string;
}

export interface EnforcePoliciesResponse {
  tier: PolicyTier;
  enforcement_mode: string;
  should_block_merge: boolean;
  github_check_conclusion: string;
  enforcement_actions: string[];
  vcr: VCR;
}

export interface MRPHealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  service: string;
  version: string;
  features: string[];
}

// =========================================================================
// Query Keys
// =========================================================================

export const mrpKeys = {
  all: ["mrp"] as const,
  health: () => [...mrpKeys.all, "health"] as const,
  validation: (projectId: string, prId: string) =>
    [...mrpKeys.all, "validation", projectId, prId] as const,
  vcr: (projectId: string, prId: string) =>
    [...mrpKeys.all, "vcr", projectId, prId] as const,
  vcrHistory: (projectId: string, prId?: string) =>
    [...mrpKeys.all, "vcr-history", projectId, prId] as const,
  tiers: () => [...mrpKeys.all, "tiers"] as const,
  compliance: (projectId: string) =>
    [...mrpKeys.all, "compliance", projectId] as const,
};

// =========================================================================
// API Functions
// =========================================================================

const BASE_URL = "/mrp";

async function fetchHealth(): Promise<MRPHealthResponse> {
  const response = await api.get(`${BASE_URL}/health`);
  return response.data;
}

async function validateMRP(
  data: ValidateMRPRequest
): Promise<ValidateMRPResponse> {
  const response = await api.post(`${BASE_URL}/validate`, data);
  return response.data;
}

async function fetchMRPValidation(
  projectId: string,
  prId: string
): Promise<MRPValidation> {
  const response = await api.get(`${BASE_URL}/validate/${projectId}/${prId}`);
  return response.data;
}

async function fetchVCR(projectId: string, prId: string): Promise<VCR> {
  const response = await api.get(`${BASE_URL}/vcr/${projectId}/${prId}`);
  return response.data;
}

async function fetchVCRHistory(
  projectId: string,
  prId?: string,
  limit: number = 20
): Promise<VCRHistoryResponse> {
  const params: Record<string, unknown> = { limit };
  if (prId) params.pr_id = prId;
  const response = await api.get(`${BASE_URL}/vcr/${projectId}/history`, {
    params,
  });
  return response.data;
}

async function fetchPolicyTiers(): Promise<AllTiersResponse> {
  const response = await api.get(`${BASE_URL}/policies/tiers`);
  return response.data;
}

async function fetchTierCompliance(
  projectId: string
): Promise<TierComplianceReport> {
  const response = await api.get(`${BASE_URL}/policies/compliance/${projectId}`);
  return response.data;
}

async function enforcePolicies(
  data: EnforcePoliciesRequest
): Promise<EnforcePoliciesResponse> {
  const response = await api.post(`${BASE_URL}/policies/enforce`, data);
  return response.data;
}

async function compareTiers(
  data: CompareTiersRequest
): Promise<CompareTiersResponse> {
  const response = await api.post(`${BASE_URL}/policies/compare`, data);
  return response.data;
}

// =========================================================================
// Query Hooks
// =========================================================================

/**
 * Fetch MRP service health status.
 */
export function useMRPHealth() {
  return useQuery({
    queryKey: mrpKeys.health(),
    queryFn: fetchHealth,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refresh every minute
  });
}

/**
 * Fetch MRP validation for a specific PR.
 */
export function useMRPValidation(
  projectId: string,
  prId: string,
  enabled: boolean = true
) {
  return useQuery({
    queryKey: mrpKeys.validation(projectId, prId),
    queryFn: () => fetchMRPValidation(projectId, prId),
    enabled: !!projectId && !!prId && enabled,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Fetch VCR for a specific PR.
 */
export function useVCR(projectId: string, prId: string, enabled: boolean = true) {
  return useQuery({
    queryKey: mrpKeys.vcr(projectId, prId),
    queryFn: () => fetchVCR(projectId, prId),
    enabled: !!projectId && !!prId && enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes (VCRs are relatively stable)
  });
}

/**
 * Fetch VCR history for a project or PR.
 */
export function useVCRHistory(
  projectId: string,
  prId?: string,
  limit: number = 20,
  enabled: boolean = true
) {
  return useQuery({
    queryKey: mrpKeys.vcrHistory(projectId, prId),
    queryFn: () => fetchVCRHistory(projectId, prId, limit),
    enabled: !!projectId && enabled,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Fetch all available policy tiers.
 */
export function usePolicyTiers() {
  return useQuery({
    queryKey: mrpKeys.tiers(),
    queryFn: fetchPolicyTiers,
    staleTime: 30 * 60 * 1000, // 30 minutes (tiers rarely change)
  });
}

/**
 * Fetch tier compliance report for a project.
 */
export function useTierCompliance(projectId: string, enabled: boolean = true) {
  return useQuery({
    queryKey: mrpKeys.compliance(projectId),
    queryFn: () => fetchTierCompliance(projectId),
    enabled: !!projectId && enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// =========================================================================
// Mutation Hooks
// =========================================================================

/**
 * Validate MRP 5-point structure for a PR.
 */
export function useValidateMRP() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: validateMRP,
    onSuccess: (data) => {
      // Invalidate related queries
      queryClient.invalidateQueries({
        queryKey: mrpKeys.validation(
          data.mrp_validation.project_id,
          data.mrp_validation.pr_id
        ),
      });
      if (data.vcr) {
        queryClient.invalidateQueries({
          queryKey: mrpKeys.vcr(data.vcr.project_id, data.vcr.pr_id),
        });
        queryClient.invalidateQueries({
          queryKey: mrpKeys.vcrHistory(data.vcr.project_id),
        });
      }
    },
  });
}

/**
 * Enforce policies for a PR.
 */
export function useEnforcePolicies() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: enforcePolicies,
    onSuccess: (data) => {
      // Invalidate related queries
      queryClient.invalidateQueries({
        queryKey: mrpKeys.vcr(data.vcr.project_id, data.vcr.pr_id),
      });
      queryClient.invalidateQueries({
        queryKey: mrpKeys.vcrHistory(data.vcr.project_id),
      });
    },
  });
}

/**
 * Compare two policy tiers.
 */
export function useCompareTiers() {
  return useMutation({
    mutationFn: compareTiers,
  });
}

// =========================================================================
// Utility Functions
// =========================================================================

/**
 * Get MRP point status color for UI styling.
 */
export function getMRPPointStatusColor(status: MRPPointStatus): string {
  switch (status) {
    case "PASSED":
      return "text-green-600 bg-green-100 border-green-200";
    case "FAILED":
      return "text-red-600 bg-red-100 border-red-200";
    case "SKIPPED":
      return "text-gray-600 bg-gray-100 border-gray-200";
    case "NOT_AVAILABLE":
      return "text-yellow-600 bg-yellow-100 border-yellow-200";
    case "IN_PROGRESS":
      return "text-blue-600 bg-blue-100 border-blue-200";
    default:
      return "text-gray-600 bg-gray-100 border-gray-200";
  }
}

/**
 * Get VCR verdict color for UI styling.
 */
export function getVCRVerdictColor(verdict: VCRVerdict): string {
  switch (verdict) {
    case "PASS":
      return "text-green-600 bg-green-100 border-green-200";
    case "FAIL":
      return "text-red-600 bg-red-100 border-red-200";
    case "PENDING":
      return "text-yellow-600 bg-yellow-100 border-yellow-200";
    case "BLOCKED":
      return "text-orange-600 bg-orange-100 border-orange-200";
    default:
      return "text-gray-600 bg-gray-100 border-gray-200";
  }
}

/**
 * Get policy tier color for UI styling.
 */
export function getPolicyTierColor(tier: PolicyTier): string {
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
 * Get MRP point label.
 */
export function getMRPPointLabel(point: keyof MRPValidation): string {
  switch (point) {
    case "test":
      return "Test Evidence";
    case "lint":
      return "Lint Evidence";
    case "security":
      return "Security Evidence";
    case "build":
      return "Build Evidence";
    case "conformance":
      return "Conformance Evidence";
    default:
      return point;
  }
}

/**
 * Get MRP point icon name (for use with icon libraries).
 */
export function getMRPPointIcon(point: keyof MRPValidation): string {
  switch (point) {
    case "test":
      return "beaker";
    case "lint":
      return "code";
    case "security":
      return "shield-check";
    case "build":
      return "cube";
    case "conformance":
      return "clipboard-check";
    default:
      return "document";
  }
}

/**
 * Get MRP summary text.
 */
export function getMRPSummary(validation: MRPValidation): string {
  return `${validation.points_passed}/${validation.points_required} points passed (${validation.overall_passed ? "PASS" : "FAIL"})`;
}

/**
 * Get vibecoding zone from index.
 */
export function getZoneFromIndex(index: number): VibecodingZone {
  if (index <= 20) return "GREEN";
  if (index <= 40) return "YELLOW";
  if (index <= 60) return "ORANGE";
  return "RED";
}

/**
 * Get vibecoding zone color for UI styling.
 */
export function getVibecodingZoneColor(zone: VibecodingZone): string {
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
 * Check if MRP validation includes context authority validation.
 */
export function hasContextValidation(validation: MRPValidation): boolean {
  return validation.context_snapshot_id !== null;
}

/**
 * Get context validation status text.
 */
export function getContextValidationStatus(validation: MRPValidation): string {
  if (!hasContextValidation(validation)) {
    return "Not performed";
  }
  if (validation.context_validation_passed === null) {
    return "Pending";
  }
  return validation.context_validation_passed ? "Passed" : "Failed";
}
