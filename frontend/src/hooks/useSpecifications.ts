/**
 * =========================================================================
 * Specifications React Query Hooks
 * SDLC Orchestrator - Sprint 118 (SPEC-0002 Specification Standard)
 *
 * Version: 1.0.0
 * Date: January 29, 2026
 * Framework: SDLC 5.3.0 Quality Assurance System
 * Spec Reference: SPEC-0002
 *
 * Purpose: React Query hooks for Specification validation and management
 * Features: YAML frontmatter validation, BDD requirements, acceptance criteria
 * =========================================================================
 */

import { useQuery, useMutation } from "@tanstack/react-query";
import { useAuth } from "./useAuth";
import { apiClient } from "@/lib/apiClient";

// =============================================================================
// Types
// =============================================================================

export interface FrontmatterValidationRequest {
  content: string;
  file_path?: string;
  tier?: "LITE" | "STANDARD" | "PROFESSIONAL" | "ENTERPRISE";
}

export interface ValidationError {
  field: string;
  message: string;
  severity: "error" | "warning";
  line_number?: number;
}

export interface FrontmatterValidationResponse {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationError[];
  parsed_metadata: {
    spec_version?: string;
    spec_id?: string;
    status?: string;
    tier?: string;
    stage?: string;
    owner?: string;
    created?: string;
    last_updated?: string;
    related_adrs?: string[];
  } | null;
  compliance_score: number;
  suggestions: string[];
}

export interface SpecMetadataResponse {
  spec_id: string;
  title: string;
  status: string;
  tier: string;
  stage: string;
  owner: string;
  created: string;
  last_updated: string;
  related_adrs: string[];
  spec_version: string;
  file_path: string;
}

export interface Requirement {
  id: string;
  type: "functional" | "non_functional";
  category: string;
  given: string;
  when: string;
  then: string;
  priority: "must" | "should" | "could" | "wont";
  tier_applicable: string[];
}

export interface RequirementsListResponse {
  spec_id: string;
  total_requirements: number;
  functional_requirements: Requirement[];
  non_functional_requirements: Requirement[];
  coverage_by_tier: {
    LITE: number;
    STANDARD: number;
    PROFESSIONAL: number;
    ENTERPRISE: number;
  };
}

export interface AcceptanceCriterion {
  id: string;
  description: string;
  testable: boolean;
  automated: boolean;
  linked_requirement_id?: string;
  status: "pending" | "passed" | "failed";
}

export interface AcceptanceCriteriaListResponse {
  spec_id: string;
  total_criteria: number;
  criteria: AcceptanceCriterion[];
  testable_percentage: number;
  automated_percentage: number;
  pass_rate: number;
}

// =============================================================================
// API Functions
// =============================================================================

async function validateFrontmatter(
  request: FrontmatterValidationRequest
): Promise<FrontmatterValidationResponse> {
  const response = await apiClient.post<FrontmatterValidationResponse>(
    "/governance/specs/validate",
    request
  );
  return response.data;
}

async function getSpecification(
  specId: string
): Promise<SpecMetadataResponse> {
  const response = await apiClient.get<SpecMetadataResponse>(
    `/governance/specs/${specId}`
  );
  return response.data;
}

async function getRequirements(
  specId: string
): Promise<RequirementsListResponse> {
  const response = await apiClient.get<RequirementsListResponse>(
    `/governance/specs/${specId}/requirements`
  );
  return response.data;
}

async function getAcceptanceCriteria(
  specId: string
): Promise<AcceptanceCriteriaListResponse> {
  const response = await apiClient.get<AcceptanceCriteriaListResponse>(
    `/governance/specs/${specId}/acceptance-criteria`
  );
  return response.data;
}

// =============================================================================
// Query Key Factory
// =============================================================================

export const specificationKeys = {
  all: ["specifications"] as const,
  detail: (specId: string) =>
    [...specificationKeys.all, "detail", specId] as const,
  requirements: (specId: string) =>
    [...specificationKeys.all, "requirements", specId] as const,
  acceptanceCriteria: (specId: string) =>
    [...specificationKeys.all, "acceptance-criteria", specId] as const,
  validation: () => [...specificationKeys.all, "validation"] as const,
};

// =============================================================================
// Query Hooks
// =============================================================================

/**
 * Hook to get specification metadata
 */
export function useSpecification(specId: string) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: specificationKeys.detail(specId),
    queryFn: () => getSpecification(specId),
    enabled: isAuthenticated && !authLoading && !!specId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to get specification requirements (BDD format)
 */
export function useSpecRequirements(specId: string) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: specificationKeys.requirements(specId),
    queryFn: () => getRequirements(specId),
    enabled: isAuthenticated && !authLoading && !!specId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to get acceptance criteria for a specification
 */
export function useAcceptanceCriteria(specId: string) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: specificationKeys.acceptanceCriteria(specId),
    queryFn: () => getAcceptanceCriteria(specId),
    enabled: isAuthenticated && !authLoading && !!specId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// =============================================================================
// Mutation Hooks
// =============================================================================

/**
 * Hook to validate YAML frontmatter
 */
export function useValidateFrontmatter() {
  return useMutation({
    mutationFn: validateFrontmatter,
  });
}

// =============================================================================
// Utility Hooks
// =============================================================================

/**
 * Hook to get status color and styling
 */
export function useStatusColor(status: string): {
  bgColor: string;
  textColor: string;
  borderColor: string;
} {
  switch (status?.toLowerCase()) {
    case "approved":
      return {
        bgColor: "bg-green-100",
        textColor: "text-green-700",
        borderColor: "border-green-200",
      };
    case "implemented":
      return {
        bgColor: "bg-blue-100",
        textColor: "text-blue-700",
        borderColor: "border-blue-200",
      };
    case "draft":
      return {
        bgColor: "bg-yellow-100",
        textColor: "text-yellow-700",
        borderColor: "border-yellow-200",
      };
    case "deprecated":
      return {
        bgColor: "bg-gray-100",
        textColor: "text-gray-700",
        borderColor: "border-gray-200",
      };
    default:
      return {
        bgColor: "bg-gray-100",
        textColor: "text-gray-700",
        borderColor: "border-gray-200",
      };
  }
}

/**
 * Hook to get tier color and styling
 */
export function useTierColor(tier: string): {
  bgColor: string;
  textColor: string;
  borderColor: string;
  icon: string;
} {
  switch (tier?.toUpperCase()) {
    case "LITE":
      return {
        bgColor: "bg-gray-100",
        textColor: "text-gray-700",
        borderColor: "border-gray-200",
        icon: "L",
      };
    case "STANDARD":
      return {
        bgColor: "bg-blue-100",
        textColor: "text-blue-700",
        borderColor: "border-blue-200",
        icon: "S",
      };
    case "PROFESSIONAL":
      return {
        bgColor: "bg-purple-100",
        textColor: "text-purple-700",
        borderColor: "border-purple-200",
        icon: "P",
      };
    case "ENTERPRISE":
      return {
        bgColor: "bg-amber-100",
        textColor: "text-amber-700",
        borderColor: "border-amber-200",
        icon: "E",
      };
    default:
      return {
        bgColor: "bg-gray-100",
        textColor: "text-gray-700",
        borderColor: "border-gray-200",
        icon: "?",
      };
  }
}

/**
 * Hook to get combined specification state
 */
export function useSpecificationState(specId: string) {
  const spec = useSpecification(specId);
  const requirements = useSpecRequirements(specId);
  const acceptanceCriteria = useAcceptanceCriteria(specId);

  return {
    isLoading: spec.isLoading || requirements.isLoading || acceptanceCriteria.isLoading,
    isError: spec.isError || requirements.isError || acceptanceCriteria.isError,
    specification: spec.data,
    requirements: requirements.data,
    acceptanceCriteria: acceptanceCriteria.data,
    refetch: () => {
      spec.refetch();
      requirements.refetch();
      acceptanceCriteria.refetch();
    },
  };
}

/**
 * Hook to calculate compliance score display
 */
export function useComplianceScoreDisplay(score: number): {
  color: string;
  label: string;
  percentage: string;
} {
  if (score >= 90) {
    return {
      color: "text-green-600",
      label: "Excellent",
      percentage: `${score}%`,
    };
  } else if (score >= 70) {
    return {
      color: "text-blue-600",
      label: "Good",
      percentage: `${score}%`,
    };
  } else if (score >= 50) {
    return {
      color: "text-yellow-600",
      label: "Fair",
      percentage: `${score}%`,
    };
  } else {
    return {
      color: "text-red-600",
      label: "Poor",
      percentage: `${score}%`,
    };
  }
}
