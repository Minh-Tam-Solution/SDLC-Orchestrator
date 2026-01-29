/**
 * =========================================================================
 * Tier Management React Query Hooks
 * SDLC Orchestrator - Sprint 118 (4-Tier Classification System)
 *
 * Version: 1.0.0
 * Date: January 29, 2026
 * Framework: SDLC 5.3.0 Quality Assurance System
 * ADR Reference: ADR-041
 *
 * Purpose: React Query hooks for 4-Tier Classification operations
 * Tiers: LITE, STANDARD, PROFESSIONAL, ENTERPRISE
 * =========================================================================
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "./useAuth";
import { apiClient } from "@/lib/apiClient";

// =============================================================================
// Types
// =============================================================================

export type TierLevel = "LITE" | "STANDARD" | "PROFESSIONAL" | "ENTERPRISE";

export interface TierRequirement {
  id: string;
  category: string;
  requirement: string;
  mandatory: boolean;
  automated_check: boolean;
  evidence_type?: string;
}

export interface ProjectTierResponse {
  project_id: string;
  project_name: string;
  current_tier: TierLevel;
  tier_since: string;
  compliance_score: number;
  requirements_met: number;
  requirements_total: number;
  next_tier: TierLevel | null;
  upgrade_eligibility: {
    eligible: boolean;
    missing_requirements: string[];
    completion_percentage: number;
  };
}

export interface TierRequirementsListResponse {
  tier: TierLevel;
  total_requirements: number;
  categories: {
    name: string;
    requirements: TierRequirement[];
  }[];
  comparison_to_previous: {
    previous_tier: TierLevel | null;
    additional_requirements: number;
  };
}

export interface TierUpgradeRequest {
  target_tier: TierLevel;
  justification: string;
  evidence_links?: string[];
}

export interface TierUpgradeResponse {
  request_id: string;
  project_id: string;
  current_tier: TierLevel;
  target_tier: TierLevel;
  status: "pending" | "approved" | "rejected" | "auto_approved";
  validation_result: {
    passed: boolean;
    checks_passed: number;
    checks_total: number;
    failed_checks: string[];
  };
  approver_required: string | null;
  estimated_review_time?: string;
  created_at: string;
}

export interface TierHistory {
  tier: TierLevel;
  effective_from: string;
  effective_until: string | null;
  reason: string;
  approved_by?: string;
}

// =============================================================================
// API Functions
// =============================================================================

async function getProjectTier(
  projectId: string
): Promise<ProjectTierResponse> {
  const response = await apiClient.get<ProjectTierResponse>(
    `/governance/tiers/${projectId}`
  );
  return response.data;
}

async function getTierRequirements(
  tier: TierLevel
): Promise<TierRequirementsListResponse> {
  const response = await apiClient.get<TierRequirementsListResponse>(
    `/governance/tiers/${tier}/requirements`
  );
  return response.data;
}

async function requestTierUpgrade(
  projectId: string,
  request: TierUpgradeRequest
): Promise<TierUpgradeResponse> {
  const response = await apiClient.post<TierUpgradeResponse>(
    `/governance/tiers/${projectId}/upgrade`,
    request
  );
  return response.data;
}

// =============================================================================
// Query Key Factory
// =============================================================================

export const tierKeys = {
  all: ["tiers"] as const,
  project: (projectId: string) =>
    [...tierKeys.all, "project", projectId] as const,
  requirements: (tier: TierLevel) =>
    [...tierKeys.all, "requirements", tier] as const,
  allRequirements: () =>
    [...tierKeys.all, "all-requirements"] as const,
};

// =============================================================================
// Query Hooks
// =============================================================================

/**
 * Hook to get project's current tier information
 */
export function useProjectTier(projectId: string) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: tierKeys.project(projectId),
    queryFn: () => getProjectTier(projectId),
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to get requirements for a specific tier
 */
export function useTierRequirements(tier: TierLevel) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: tierKeys.requirements(tier),
    queryFn: () => getTierRequirements(tier),
    enabled: isAuthenticated && !authLoading && !!tier,
    staleTime: 30 * 60 * 1000, // 30 minutes - requirements don't change often
  });
}

/**
 * Hook to get all tier requirements for comparison
 */
export function useAllTierRequirements() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const tiers: TierLevel[] = ["LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"];

  const queries = tiers.map((tier) => ({
    queryKey: tierKeys.requirements(tier),
    queryFn: () => getTierRequirements(tier),
    enabled: isAuthenticated && !authLoading,
    staleTime: 30 * 60 * 1000,
  }));

  // Note: In production, use useQueries from @tanstack/react-query
  // This is a simplified version
  const liteReq = useTierRequirements("LITE");
  const standardReq = useTierRequirements("STANDARD");
  const professionalReq = useTierRequirements("PROFESSIONAL");
  const enterpriseReq = useTierRequirements("ENTERPRISE");

  return {
    isLoading:
      liteReq.isLoading ||
      standardReq.isLoading ||
      professionalReq.isLoading ||
      enterpriseReq.isLoading,
    data: {
      LITE: liteReq.data,
      STANDARD: standardReq.data,
      PROFESSIONAL: professionalReq.data,
      ENTERPRISE: enterpriseReq.data,
    },
  };
}

// =============================================================================
// Mutation Hooks
// =============================================================================

/**
 * Hook to request a tier upgrade
 */
export function useRequestTierUpgrade() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      projectId,
      request,
    }: {
      projectId: string;
      request: TierUpgradeRequest;
    }) => requestTierUpgrade(projectId, request),
    onSuccess: (_, variables) => {
      // Invalidate project tier query
      queryClient.invalidateQueries({
        queryKey: tierKeys.project(variables.projectId),
      });
    },
  });
}

// =============================================================================
// Utility Hooks
// =============================================================================

/**
 * Hook to get tier display information
 */
export function useTierDisplay(tier: TierLevel): {
  name: string;
  description: string;
  bgColor: string;
  textColor: string;
  borderColor: string;
  icon: string;
  features: string[];
} {
  switch (tier) {
    case "LITE":
      return {
        name: "Lite",
        description: "Basic governance for small projects",
        bgColor: "bg-gray-100",
        textColor: "text-gray-700",
        borderColor: "border-gray-200",
        icon: "L",
        features: [
          "Basic gate evaluation",
          "Simple evidence collection",
          "GitHub PR integration",
          "Manual review workflow",
        ],
      };
    case "STANDARD":
      return {
        name: "Standard",
        description: "Full governance for production projects",
        bgColor: "bg-blue-100",
        textColor: "text-blue-700",
        borderColor: "border-blue-200",
        icon: "S",
        features: [
          "All Lite features",
          "SAST integration",
          "Context validation",
          "AI attestation tracking",
          "Basic analytics",
        ],
      };
    case "PROFESSIONAL":
      return {
        name: "Professional",
        description: "Advanced governance for teams",
        bgColor: "bg-purple-100",
        textColor: "text-purple-700",
        borderColor: "border-purple-200",
        icon: "P",
        features: [
          "All Standard features",
          "Custom policy packs",
          "Advanced analytics",
          "Team collaboration",
          "Priority support",
        ],
      };
    case "ENTERPRISE":
      return {
        name: "Enterprise",
        description: "Full compliance for regulated industries",
        bgColor: "bg-amber-100",
        textColor: "text-amber-700",
        borderColor: "border-amber-200",
        icon: "E",
        features: [
          "All Professional features",
          "SOC 2 compliance",
          "HIPAA support",
          "Custom integrations",
          "Dedicated support",
          "SLA guarantees",
        ],
      };
  }
}

/**
 * Hook to get tier progression (order and next tier)
 */
export function useTierProgression(currentTier: TierLevel): {
  currentIndex: number;
  nextTier: TierLevel | null;
  previousTier: TierLevel | null;
  progressPercentage: number;
} {
  const tierOrder: TierLevel[] = ["LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"];
  const currentIndex = tierOrder.indexOf(currentTier);

  return {
    currentIndex,
    nextTier: currentIndex < tierOrder.length - 1 ? tierOrder[currentIndex + 1] : null,
    previousTier: currentIndex > 0 ? tierOrder[currentIndex - 1] : null,
    progressPercentage: ((currentIndex + 1) / tierOrder.length) * 100,
  };
}

/**
 * Hook to check if user can request tier upgrade
 */
export function useCanRequestUpgrade() {
  const { user } = useAuth();

  if (!user) return false;

  // Check for roles that can request upgrades
  const allowedRoles = ["owner", "admin", "pm", "tech_lead", "cto", "ceo"];
  return (
    user.roles?.some((role) =>
      allowedRoles.includes(role.toLowerCase())
    ) || user.is_platform_admin
  );
}

/**
 * Hook to combine project tier with upgrade eligibility
 */
export function useTierUpgradeEligibility(projectId: string) {
  const projectTier = useProjectTier(projectId);
  const canRequest = useCanRequestUpgrade();

  const nextTier = projectTier.data?.next_tier;
  const nextTierReq = useTierRequirements(nextTier || "LITE");

  return {
    isLoading: projectTier.isLoading || (nextTier && nextTierReq.isLoading),
    currentTier: projectTier.data?.current_tier,
    nextTier,
    canRequestUpgrade: canRequest,
    isEligible: projectTier.data?.upgrade_eligibility?.eligible ?? false,
    missingRequirements: projectTier.data?.upgrade_eligibility?.missing_requirements ?? [],
    completionPercentage: projectTier.data?.upgrade_eligibility?.completion_percentage ?? 0,
    nextTierRequirements: nextTierReq.data,
  };
}
