/**
 * Data Residency TanStack Query Hooks
 * SDLC Orchestrator Dashboard
 *
 * @module frontend/src/hooks/useDataResidency
 * @description React Query hooks for Data Residency API — Sprint 214 Track A
 * @sdlc SDLC 6.1.1 — Sprint 214 (ENT Compliance #10)
 * @status Active — ENTERPRISE tier (ADR-063)
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";

// ---------------------------------------------------------------------------
// Types (mirrors backend schemas from data_residency.py)
// ---------------------------------------------------------------------------

export interface RegionInfo {
  region: string;
  display_name: string;
  endpoint_url: string;
  bucket: string;
  gdpr_compliant: boolean;
}

export interface RegionsResponse {
  regions: RegionInfo[];
}

export interface ProjectRegion {
  project_id: string;
  project_name: string;
  data_region: string;
  bucket: string;
  endpoint_url: string;
}

export interface RegionUpdateRequest {
  data_region: "VN" | "EU" | "US";
}

export interface RegionUpdateResponse {
  project_id: string;
  project_name: string;
  old_region: string;
  new_region: string;
  new_bucket: string;
  changed: boolean;
  message: string;
}

export interface ProjectStorageInfo {
  project_id: string;
  project_name: string;
  data_region: string;
  storage: {
    endpoint_url: string;
    bucket: string;
    aws_region: string;
    evidence_prefix: string;
    gdpr_compliant: boolean;
  };
}

// ---------------------------------------------------------------------------
// API helper (local — apiRequest is not exported from api.ts)
// ---------------------------------------------------------------------------

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function residencyFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: { ...headers, ...options.headers },
    credentials: "include",
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(err.detail || `Data Residency API error ${response.status}`);
  }
  return response.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const dataResidencyKeys = {
  all: ["data-residency"] as const,
  regions: () => [...dataResidencyKeys.all, "regions"] as const,
  projectRegions: () => [...dataResidencyKeys.all, "project-region"] as const,
  projectRegion: (projectId: string) => [...dataResidencyKeys.projectRegions(), projectId] as const,
  projectStorages: () => [...dataResidencyKeys.all, "project-storage"] as const,
  projectStorage: (projectId: string) => [...dataResidencyKeys.projectStorages(), projectId] as const,
};

// ---------------------------------------------------------------------------
// Query hooks
// ---------------------------------------------------------------------------

/** List available regions */
export function useAvailableRegions() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: dataResidencyKeys.regions(),
    queryFn: () => residencyFetch<RegionsResponse>("/data-residency/regions"),
    enabled: isAuthenticated && !authLoading,
    staleTime: 10 * 60_000, // 10 min — regions rarely change
  });
}

/** Get a project's current region */
export function useProjectRegion(projectId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: dataResidencyKeys.projectRegion(projectId || ""),
    queryFn: () => {
      if (!projectId) throw new Error("Missing project ID");
      return residencyFetch<ProjectRegion>(`/data-residency/projects/${projectId}/region`);
    },
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 60_000,
  });
}

/** Get a project's full storage routing */
export function useProjectStorage(projectId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: dataResidencyKeys.projectStorage(projectId || ""),
    queryFn: () => {
      if (!projectId) throw new Error("Missing project ID");
      return residencyFetch<ProjectStorageInfo>(`/data-residency/projects/${projectId}/storage`);
    },
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 60_000,
  });
}

// ---------------------------------------------------------------------------
// Mutation hooks
// ---------------------------------------------------------------------------

/** Update a project's data region */
export function useUpdateProjectRegion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, data }: { projectId: string; data: RegionUpdateRequest }) =>
      residencyFetch<RegionUpdateResponse>(`/data-residency/projects/${projectId}/region`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: dataResidencyKeys.projectRegion(result.project_id) });
      queryClient.invalidateQueries({ queryKey: dataResidencyKeys.projectStorage(result.project_id) });
    },
  });
}
