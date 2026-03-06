/**
 * GDPR TanStack Query Hooks
 * SDLC Orchestrator Dashboard
 *
 * @module frontend/src/hooks/useGdpr
 * @description React Query hooks for GDPR API — Sprint 214 Track A
 * @sdlc SDLC 6.1.1 — Sprint 214 (ENT Compliance #10)
 * @status Active — ENTERPRISE tier (ADR-063)
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";

// ---------------------------------------------------------------------------
// Types (mirrors backend schemas from gdpr.py)
// ---------------------------------------------------------------------------

export interface DSARRecord {
  id: string;
  request_type: string;
  requester_email: string;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface DSARListResponse {
  items: DSARRecord[];
  limit: number;
  offset: number;
  status_filter: string | null;
}

export interface DSARCreateRequest {
  request_type: "access" | "rectification" | "erasure" | "portability" | "restriction" | "objection";
  requester_email: string;
  description: string;
}

export interface DataExportSummary {
  user_id: string;
  categories: Record<string, number>;
  generated_at: string;
}

export interface FullDataExport {
  user_profile: Record<string, unknown>;
  consent_records: unknown[];
  dsar_requests: unknown[];
  agent_messages: unknown[];
  evidence_metadata: unknown[];
  exported_at: string;
}

export interface ConsentRecord {
  id: string;
  purpose: string;
  granted: boolean;
  version: string;
  recorded_at: string;
}

export interface ActiveConsentsResponse {
  user_id: string;
  consents: ConsentRecord[];
}

export interface ConsentRequest {
  purpose: "essential" | "analytics" | "marketing" | "ai_training" | "third_party";
  granted: boolean;
  version: string;
}

// ---------------------------------------------------------------------------
// API helper (local — apiRequest is not exported from api.ts)
// ---------------------------------------------------------------------------

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function gdprFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
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
    throw new Error(err.detail || `GDPR API error ${response.status}`);
  }
  return response.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const gdprKeys = {
  all: ["gdpr"] as const,
  dsarLists: () => [...gdprKeys.all, "dsar", "list"] as const,
  dsarList: (statusFilter?: string) => [...gdprKeys.dsarLists(), statusFilter] as const,
  dsarDetails: () => [...gdprKeys.all, "dsar", "detail"] as const,
  dsarDetail: (id: string) => [...gdprKeys.dsarDetails(), id] as const,
  exportSummary: () => [...gdprKeys.all, "export-summary"] as const,
  consents: () => [...gdprKeys.all, "consents"] as const,
};

// ---------------------------------------------------------------------------
// Query hooks
// ---------------------------------------------------------------------------

/** List all DSARs (DPO only) */
export function useDsarList(statusFilter?: string) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const params = new URLSearchParams();
  if (statusFilter) params.set("status_filter", statusFilter);
  const qs = params.toString();

  return useQuery({
    queryKey: gdprKeys.dsarList(statusFilter),
    queryFn: () => gdprFetch<DSARListResponse>(`/gdpr/dsar${qs ? `?${qs}` : ""}`),
    enabled: isAuthenticated && !authLoading,
    staleTime: 60_000,
  });
}

/** Get a single DSAR by ID */
export function useDsarDetail(dsarId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: gdprKeys.dsarDetail(dsarId || ""),
    queryFn: () => {
      if (!dsarId) throw new Error("Missing DSAR ID");
      return gdprFetch<DSARRecord>(`/gdpr/dsar/${dsarId}`);
    },
    enabled: isAuthenticated && !authLoading && !!dsarId,
    staleTime: 60_000,
  });
}

/** Get user data export summary (Art. 15) */
export function useDataExportSummary() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: gdprKeys.exportSummary(),
    queryFn: () => gdprFetch<DataExportSummary>("/gdpr/me/data-export"),
    enabled: isAuthenticated && !authLoading,
    staleTime: 5 * 60_000,
  });
}

/** Get active consents (Art. 7) */
export function useActiveConsents() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  return useQuery({
    queryKey: gdprKeys.consents(),
    queryFn: () => gdprFetch<ActiveConsentsResponse>("/gdpr/me/consents"),
    enabled: isAuthenticated && !authLoading,
    staleTime: 60_000,
  });
}

// ---------------------------------------------------------------------------
// Mutation hooks
// ---------------------------------------------------------------------------

/** Submit a new DSAR */
export function useCreateDsar() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: DSARCreateRequest) =>
      gdprFetch<DSARRecord>("/gdpr/dsar", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: gdprKeys.dsarLists() });
    },
  });
}

/** Request full data export (Art. 20 — rate limited 1/24h) */
export function useFullDataExport() {
  return useMutation({
    mutationFn: () => gdprFetch<FullDataExport>("/gdpr/me/data-export/full"),
  });
}

/** Record a consent decision (Art. 7) */
export function useRecordConsent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ConsentRequest) =>
      gdprFetch<ConsentRecord>("/gdpr/me/consent", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: gdprKeys.consents() });
    },
  });
}
