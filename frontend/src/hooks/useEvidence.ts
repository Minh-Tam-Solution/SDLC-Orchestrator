/**
 * Evidence TanStack Query Hooks - SDLC Orchestrator Dashboard
 *
 * @module frontend/landing/src/hooks/useEvidence
 * @description React Query hooks for Evidence API
 * @sdlc SDLC 6.0.5 Universal Framework
 * @status Sprint 147 - Telemetry Integration
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getEvidenceList,
  getEvidence,
  uploadEvidence,
  checkEvidenceIntegrity,
  type Evidence,
  type EvidenceListResponse,
  type EvidenceListOptions,
  type EvidenceUploadRequest,
  type EvidenceDownloadResponse,
  type IntegrityCheckRequest,
  type IntegrityCheckResponse,
} from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { trackFirstEvidenceUploaded, trackEvent, TELEMETRY_EVENTS } from "@/lib/telemetry";

// Query keys for cache management
export const evidenceKeys = {
  all: ["evidence"] as const,
  lists: () => [...evidenceKeys.all, "list"] as const,
  list: (options?: EvidenceListOptions) =>
    [...evidenceKeys.lists(), options] as const,
  details: () => [...evidenceKeys.all, "detail"] as const,
  detail: (id: string) => [...evidenceKeys.details(), id] as const,
};

/**
 * Hook to fetch list of evidence with pagination and filters
 * Sprint 69: Uses httpOnly cookie auth (credentials: "include")
 */
export function useEvidenceList(options?: EvidenceListOptions) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: evidenceKeys.list(options),
    queryFn: () => getEvidenceList(options),
    enabled: isAuthenticated && !authLoading,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Hook to fetch evidence by gate ID
 */
export function useGateEvidence(gateId: string | undefined) {
  return useEvidenceList(gateId ? { gate_id: gateId } : undefined);
}

/**
 * Hook to fetch evidence by type
 */
export function useEvidenceByType(evidenceType: string | undefined) {
  return useEvidenceList(evidenceType ? { evidence_type: evidenceType } : undefined);
}

/**
 * Hook to fetch a single evidence item by ID
 * Sprint 69: Uses httpOnly cookie auth (credentials: "include")
 */
export function useEvidence(evidenceId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: evidenceKeys.detail(evidenceId || ""),
    queryFn: () => {
      if (!evidenceId) {
        throw new Error("Missing evidence ID");
      }
      return getEvidence(evidenceId);
    },
    enabled: isAuthenticated && !authLoading && !!evidenceId,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Hook to invalidate evidence cache
 */
export function useInvalidateEvidence() {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: evidenceKeys.all });
  };
}

/**
 * Hook to upload evidence file
 * Sprint 69: File upload to MinIO S3-compatible storage
 * Sprint 147: Added telemetry tracking for evidence upload events
 */
export function useUploadEvidence() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ data, file }: { data: EvidenceUploadRequest; file: File }) =>
      uploadEvidence(data, file),
    onSuccess: (response, variables) => {
      // Invalidate evidence list
      queryClient.invalidateQueries({ queryKey: evidenceKeys.lists() });
      // Invalidate gate-specific evidence list
      queryClient.invalidateQueries({
        queryKey: evidenceKeys.list({ gate_id: variables.data.gate_id }),
      });

      // Track evidence upload event for activation funnel (Sprint 147)
      trackFirstEvidenceUploaded(
        variables.data.project_id || "",
        variables.data.evidence_type || "unknown",
        variables.file.size
      );
    },
  });
}

/**
 * Hook to download evidence file
 * Sprint 69: Direct download through backend (avoids mixed content issues)
 */
export function useDownloadEvidence() {
  return useMutation({
    mutationFn: async (evidenceId: string) => {
      // Use direct file download endpoint (streams through backend)
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const url = `${API_BASE_URL}/evidence/${evidenceId}/file`;

      // Fetch with credentials (httpOnly cookies)
      const response = await fetch(url, {
        method: "GET",
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error(`Download failed: ${response.statusText}`);
      }

      // Get filename from Content-Disposition header or use default
      const contentDisposition = response.headers.get("Content-Disposition");
      let filename = "download";
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^"]+)"?/);
        if (match) {
          filename = match[1];
        }
      }

      // Convert response to blob and trigger download
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

      return { success: true, filename };
    },
  });
}

/**
 * Hook to run integrity check on evidence file
 * Sprint 69: SHA256 verification against stored hash
 */
export function useCheckEvidenceIntegrity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      evidenceId,
      data,
    }: {
      evidenceId: string;
      data?: IntegrityCheckRequest;
    }) => checkEvidenceIntegrity(evidenceId, data),
    onSuccess: (_, variables) => {
      // Invalidate the specific evidence detail
      queryClient.invalidateQueries({
        queryKey: evidenceKeys.detail(variables.evidenceId),
      });
    },
  });
}

// Export types for use in components
export type {
  Evidence,
  EvidenceListResponse,
  EvidenceListOptions,
  EvidenceUploadRequest,
  EvidenceDownloadResponse,
  IntegrityCheckRequest,
  IntegrityCheckResponse,
};
