/**
 * NIST AI RMF MAP Dashboard Page - SDLC Orchestrator
 *
 * @module frontend/src/app/app/compliance/nist/map/page
 * @description Sprint 156 - NIST AI RMF MAP: AI system mapping, stakeholder coverage,
 *   dependency tracking, and risk-to-impact compliance dashboard.
 * @sdlc SDLC 6.0.5 Universal Framework
 * @status Sprint 156 - NIST AI RMF MAP
 */

"use client";

import { useState, useMemo, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { useProjects } from "@/hooks/useProjects";
import { useAuth } from "@/hooks/useAuth";

// =============================================================================
// Local API Wrapper
// =============================================================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function mapApiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (typeof window !== "undefined") {
    const accessToken = localStorage.getItem("access_token");
    if (accessToken) {
      headers["Authorization"] = `Bearer ${accessToken}`;
    }
  }

  const response = await fetch(url, {
    ...options,
    headers: { ...headers, ...(options.headers as Record<string, string>) },
    credentials: "include",
  });

  if (!response.ok) {
    const errorBody = await response.text();
    let detail = `API error: ${response.status}`;
    try {
      const parsed = JSON.parse(errorBody);
      detail = parsed.detail || detail;
    } catch {
      // Use default error message
    }
    throw new Error(detail);
  }

  return response.json();
}

// =============================================================================
// Types
// =============================================================================

interface MapDashboardData {
  overall_score: number;
  policies: MapPolicyStatus[];
  last_evaluated_at: string | null;
}

interface MapPolicyStatus {
  id: string;
  control_id: string;
  name: string;
  description: string;
  status: "pass" | "fail" | "warning" | "not_evaluated";
  details: string | null;
}

interface AISystem {
  id: string;
  project_id: string;
  name: string;
  system_type: "nlp" | "vision" | "recommendation" | "decision" | "generative";
  risk_level: "minimal" | "limited" | "high" | "unacceptable";
  purpose: string;
  scope: string;
  owner_id: string;
  stakeholders: Stakeholder[];
  dependencies: Dependency[];
  created_at: string;
  updated_at: string;
}

interface Stakeholder {
  name: string;
  role: string;
  organization: string;
}

interface Dependency {
  name: string;
  type: string;
  version: string;
  provider: string;
}

interface AISystemListResponse {
  items: AISystem[];
  total: number;
  limit: number;
  offset: number;
}

interface RiskImpactMapping {
  id: string;
  ai_system_id: string;
  ai_system_name: string;
  risk_category: string;
  impact_area: string;
  likelihood: number;
  severity: number;
  mitigation_status: "planned" | "in_progress" | "implemented" | "verified";
  description: string;
}

interface CreateAISystemPayload {
  project_id: string;
  name: string;
  system_type: string;
  risk_level: string;
  purpose: string;
  scope: string;
  owner_id: string;
  stakeholders: Stakeholder[];
  dependencies: Dependency[];
}

interface UpdateAISystemPayload {
  name?: string;
  system_type?: string;
  risk_level?: string;
  purpose?: string;
  scope?: string;
  owner_id?: string;
  stakeholders?: Stakeholder[];
  dependencies?: Dependency[];
}

// =============================================================================
// API Functions
// =============================================================================

async function fetchMapDashboard(projectId: string): Promise<MapDashboardData> {
  return mapApiRequest<MapDashboardData>(
    `/compliance/nist/map/dashboard?project_id=${projectId}`
  );
}

async function evaluateMap(projectId: string): Promise<MapDashboardData> {
  return mapApiRequest<MapDashboardData>(
    `/compliance/nist/map/evaluate`,
    { method: "POST", body: JSON.stringify({ project_id: projectId }) }
  );
}

async function fetchAISystems(
  projectId: string,
  limit: number = 20,
  offset: number = 0
): Promise<AISystemListResponse> {
  return mapApiRequest<AISystemListResponse>(
    `/compliance/nist/map/ai-systems?project_id=${projectId}&limit=${limit}&offset=${offset}`
  );
}

async function createAISystem(payload: CreateAISystemPayload): Promise<AISystem> {
  return mapApiRequest<AISystem>(
    `/compliance/nist/map/ai-systems`,
    { method: "POST", body: JSON.stringify(payload) }
  );
}

async function updateAISystem(
  systemId: string,
  payload: UpdateAISystemPayload
): Promise<AISystem> {
  return mapApiRequest<AISystem>(
    `/compliance/nist/map/ai-systems/${systemId}`,
    { method: "PUT", body: JSON.stringify(payload) }
  );
}

async function deleteAISystem(systemId: string): Promise<void> {
  return mapApiRequest<void>(
    `/compliance/nist/map/ai-systems/${systemId}`,
    { method: "DELETE" }
  );
}

async function fetchRiskImpacts(projectId: string): Promise<RiskImpactMapping[]> {
  return mapApiRequest<RiskImpactMapping[]>(
    `/compliance/nist/map/risk-impacts?project_id=${projectId}`
  );
}

// =============================================================================
// Hooks
// =============================================================================

function useMapDashboard(projectId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  return useQuery({
    queryKey: ["compliance", "nist", "map", "dashboard", projectId],
    queryFn: () => fetchMapDashboard(projectId!),
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 60 * 1000,
  });
}

function useAISystems(projectId: string | undefined, limit: number = 20, offset: number = 0) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  return useQuery({
    queryKey: ["compliance", "nist", "map", "ai-systems", projectId, limit, offset],
    queryFn: () => fetchAISystems(projectId!, limit, offset),
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 60 * 1000,
  });
}

function useRiskImpacts(projectId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  return useQuery({
    queryKey: ["compliance", "nist", "map", "risk-impacts", projectId],
    queryFn: () => fetchRiskImpacts(projectId!),
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 60 * 1000,
  });
}

function useEvaluateMap() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (projectId: string) => evaluateMap(projectId),
    onSuccess: (_, projectId) => {
      queryClient.invalidateQueries({
        queryKey: ["compliance", "nist", "map", "dashboard", projectId],
      });
    },
  });
}

function useCreateAISystem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateAISystemPayload) => createAISystem(payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["compliance", "nist", "map", "ai-systems", variables.project_id],
      });
    },
  });
}

function useDeleteAISystem(projectId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (systemId: string) => deleteAISystem(systemId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["compliance", "nist", "map", "ai-systems", projectId],
      });
    },
  });
}

// =============================================================================
// Icon Components
// =============================================================================

function MapIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498 4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 0 0-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0Z" />
    </svg>
  );
}

function ShieldCheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
    </svg>
  );
}

function CheckCircleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
  );
}

function XCircleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m9.75 9.75 4.5 4.5m0-4.5-4.5 4.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
  );
}

function ExclamationTriangleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
    </svg>
  );
}

function ArrowPathIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
    </svg>
  );
}

function PlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
    </svg>
  );
}

function XMarkIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
    </svg>
  );
}

function PencilSquareIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10" />
    </svg>
  );
}

function TrashIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
    </svg>
  );
}

function UsersIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
    </svg>
  );
}

function CubeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m21 7.5-9-5.25L3 7.5m18 0-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" />
    </svg>
  );
}

// =============================================================================
// Helper Functions
// =============================================================================

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "Never";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const POLICY_STATUS_CONFIG: Record<
  MapPolicyStatus["status"],
  { label: string; color: string; icon: React.ComponentType<{ className?: string }> }
> = {
  pass: { label: "Pass", color: "bg-green-100 text-green-700", icon: CheckCircleIcon },
  fail: { label: "Fail", color: "bg-red-100 text-red-700", icon: XCircleIcon },
  warning: { label: "Warning", color: "bg-yellow-100 text-yellow-700", icon: ExclamationTriangleIcon },
  not_evaluated: { label: "Not Evaluated", color: "bg-gray-100 text-gray-500", icon: ShieldCheckIcon },
};

const RISK_LEVEL_BADGE: Record<AISystem["risk_level"], { label: string; color: string }> = {
  minimal: { label: "Minimal", color: "bg-green-100 text-green-800" },
  limited: { label: "Limited", color: "bg-blue-100 text-blue-800" },
  high: { label: "High", color: "bg-orange-100 text-orange-800" },
  unacceptable: { label: "Unacceptable", color: "bg-red-100 text-red-800" },
};

const SYSTEM_TYPE_LABELS: Record<AISystem["system_type"], string> = {
  nlp: "NLP",
  vision: "Computer Vision",
  recommendation: "Recommendation",
  decision: "Decision Support",
  generative: "Generative AI",
};

const MITIGATION_STATUS_CONFIG: Record<
  RiskImpactMapping["mitigation_status"],
  { label: string; color: string }
> = {
  planned: { label: "Planned", color: "bg-gray-100 text-gray-700" },
  in_progress: { label: "In Progress", color: "bg-blue-100 text-blue-700" },
  implemented: { label: "Implemented", color: "bg-yellow-100 text-yellow-700" },
  verified: { label: "Verified", color: "bg-green-100 text-green-700" },
};

const STAKEHOLDER_ROLE_COLORS: Record<string, string> = {
  owner: "bg-purple-100 text-purple-800",
  developer: "bg-blue-100 text-blue-800",
  operator: "bg-indigo-100 text-indigo-800",
  auditor: "bg-orange-100 text-orange-800",
  user: "bg-green-100 text-green-800",
  regulator: "bg-red-100 text-red-800",
  data_scientist: "bg-cyan-100 text-cyan-800",
  risk_manager: "bg-yellow-100 text-yellow-800",
};

function getStakeholderRoleColor(role: string): string {
  const normalized = role.toLowerCase().replace(/\s+/g, "_");
  return STAKEHOLDER_ROLE_COLORS[normalized] || "bg-gray-100 text-gray-700";
}

// =============================================================================
// MapScoreCard Component
// =============================================================================

function MapScoreCard({
  score,
  lastEvaluated,
  onEvaluate,
  isEvaluating,
}: {
  score: number;
  lastEvaluated: string | null;
  onEvaluate: () => void;
  isEvaluating: boolean;
}) {
  const percentage = Math.round(score * 100);
  const circumference = 2 * Math.PI * 54;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const scoreColor = percentage >= 80 ? "text-green-600" : percentage >= 50 ? "text-yellow-600" : "text-red-600";
  const strokeColor = percentage >= 80 ? "#16a34a" : percentage >= 50 ? "#ca8a04" : "#dc2626";

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">MAP Compliance Score</h3>
        <button
          onClick={onEvaluate}
          disabled={isEvaluating}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {isEvaluating ? (
            <>
              <ArrowPathIcon className="h-4 w-4 animate-spin" />
              Evaluating...
            </>
          ) : (
            <>
              <ShieldCheckIcon className="h-4 w-4" />
              Re-Evaluate
            </>
          )}
        </button>
      </div>

      <div className="mt-6 flex items-center gap-8">
        {/* Circular Progress */}
        <div className="relative h-32 w-32 flex-shrink-0">
          <svg className="h-32 w-32 -rotate-90" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="54" fill="none" stroke="#e5e7eb" strokeWidth="8" />
            <circle
              cx="60"
              cy="60"
              r="54"
              fill="none"
              stroke={strokeColor}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              className="transition-all duration-700 ease-out"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className={cn("text-3xl font-bold", scoreColor)}>{percentage}%</span>
          </div>
        </div>

        {/* Score Details */}
        <div className="flex-1">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Framework</span>
              <span className="text-sm font-medium text-gray-900">NIST AI RMF 1.0</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Function</span>
              <span className="text-sm font-medium text-gray-900">MAP</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Last Evaluated</span>
              <span className="text-sm font-medium text-gray-900">{formatDate(lastEvaluated)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Status</span>
              <span
                className={cn(
                  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
                  percentage >= 80
                    ? "bg-green-100 text-green-800"
                    : percentage >= 50
                      ? "bg-yellow-100 text-yellow-800"
                      : "bg-red-100 text-red-800"
                )}
              >
                {percentage >= 80 ? "Compliant" : percentage >= 50 ? "Partially Compliant" : "Non-Compliant"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// PolicyStatusList Component
// =============================================================================

function PolicyStatusList({ policies }: { policies: MapPolicyStatus[] }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900">MAP Control Status</h3>
      <p className="mt-1 text-sm text-gray-500">MAP function control assessment results (5 controls)</p>

      <div className="mt-4 divide-y divide-gray-200">
        {policies.map((policy) => {
          const config = POLICY_STATUS_CONFIG[policy.status];
          const StatusIcon = config.icon;
          return (
            <div key={policy.id} className="flex items-center justify-between py-3">
              <div className="flex items-start gap-3">
                <StatusIcon
                  className={cn("mt-0.5 h-5 w-5 flex-shrink-0", {
                    "text-green-500": policy.status === "pass",
                    "text-red-500": policy.status === "fail",
                    "text-yellow-500": policy.status === "warning",
                    "text-gray-400": policy.status === "not_evaluated",
                  })}
                />
                <div>
                  <p className="text-sm font-medium text-gray-900">{policy.name}</p>
                  <p className="text-xs text-gray-500">{policy.control_id}</p>
                  {policy.details && <p className="mt-1 text-xs text-gray-600">{policy.details}</p>}
                </div>
              </div>
              <span
                className={cn(
                  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
                  config.color
                )}
              >
                {config.label}
              </span>
            </div>
          );
        })}
      </div>

      {policies.length === 0 && (
        <div className="py-8 text-center">
          <MapIcon className="mx-auto h-8 w-8 text-gray-300" />
          <p className="mt-2 text-sm text-gray-500">
            No MAP controls evaluated yet. Run an evaluation to check compliance.
          </p>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// AISystemsTable Component
// =============================================================================

function AISystemsTable({
  systems,
  total,
  limit,
  offset,
  onPageChange,
  onAddSystem,
  onEditSystem,
  onDeleteSystem,
  isDeleting,
}: {
  systems: AISystem[];
  total: number;
  limit: number;
  offset: number;
  onPageChange: (newOffset: number) => void;
  onAddSystem: () => void;
  onEditSystem: (system: AISystem) => void;
  onDeleteSystem: (systemId: string) => void;
  isDeleting: boolean;
}) {
  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(offset / limit) + 1;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">AI Systems Registry</h3>
          <p className="mt-1 text-sm text-gray-500">{total} AI system(s) registered</p>
        </div>
        <button
          onClick={onAddSystem}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <PlusIcon className="h-4 w-4" />
          Register AI System
        </button>
      </div>

      {systems.length > 0 ? (
        <>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="px-3 py-2 text-left font-medium text-gray-700">Name</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">Type</th>
                  <th className="px-3 py-2 text-center font-medium text-gray-700">Risk Level</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">Purpose</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">Owner</th>
                  <th className="px-3 py-2 text-center font-medium text-gray-700">Deps</th>
                  <th className="px-3 py-2 text-center font-medium text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {systems.map((system) => {
                  const riskBadge = RISK_LEVEL_BADGE[system.risk_level];
                  return (
                    <tr key={system.id} className="hover:bg-gray-50">
                      <td className="px-3 py-3">
                        <p className="font-medium text-gray-900">{system.name}</p>
                      </td>
                      <td className="px-3 py-3 text-sm text-gray-700">
                        {SYSTEM_TYPE_LABELS[system.system_type] || system.system_type}
                      </td>
                      <td className="px-3 py-3 text-center">
                        <span
                          className={cn(
                            "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
                            riskBadge.color
                          )}
                        >
                          {riskBadge.label}
                        </span>
                      </td>
                      <td className="max-w-[200px] px-3 py-3 text-sm text-gray-700">
                        <p className="line-clamp-1">{system.purpose || "Not specified"}</p>
                      </td>
                      <td className="px-3 py-3 text-sm text-gray-700">{system.owner_id || "Unassigned"}</td>
                      <td className="px-3 py-3 text-center">
                        <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-gray-100 text-xs font-medium text-gray-700">
                          {system.dependencies?.length || 0}
                        </span>
                      </td>
                      <td className="px-3 py-3 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={() => onEditSystem(system)}
                            className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-blue-600"
                            title="Edit AI System"
                          >
                            <PencilSquareIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => onDeleteSystem(system.id)}
                            disabled={isDeleting}
                            className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-red-600 disabled:opacity-50"
                            title="Delete AI System"
                          >
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-4 flex items-center justify-between border-t border-gray-100 pt-4">
              <p className="text-sm text-gray-500">
                Showing {offset + 1}-{Math.min(offset + limit, total)} of {total}
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => onPageChange(Math.max(0, offset - limit))}
                  disabled={offset === 0}
                  className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  Previous
                </button>
                <span className="text-sm text-gray-600">
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  onClick={() => onPageChange(offset + limit)}
                  disabled={offset + limit >= total}
                  className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="mt-4 py-8 text-center">
          <CubeIcon className="mx-auto h-8 w-8 text-gray-300" />
          <p className="mt-2 text-sm text-gray-500">
            No AI systems registered yet. Register your first AI system to begin MAP compliance tracking.
          </p>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// CreateAISystemDialog Component
// =============================================================================

function CreateAISystemDialog({
  projectId,
  editSystem,
  onClose,
  onSuccess,
}: {
  projectId: string;
  editSystem: AISystem | null;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const isEdit = editSystem !== null;

  const [formData, setFormData] = useState({
    name: editSystem?.name || "",
    system_type: editSystem?.system_type || "nlp",
    risk_level: editSystem?.risk_level || "minimal",
    purpose: editSystem?.purpose || "",
    scope: editSystem?.scope || "",
    owner_id: editSystem?.owner_id || "",
    stakeholders_json: editSystem?.stakeholders
      ? JSON.stringify(editSystem.stakeholders, null, 2)
      : '[{"name": "", "role": "", "organization": ""}]',
    dependencies_json: editSystem?.dependencies
      ? JSON.stringify(editSystem.dependencies, null, 2)
      : '[{"name": "", "type": "", "version": "", "provider": ""}]',
  });

  const createMutation = useCreateAISystem();

  const [submitError, setSubmitError] = useState<string | null>(null);

  const parseJsonField = <T,>(json: string, fieldName: string): T[] | null => {
    try {
      const parsed = JSON.parse(json);
      if (!Array.isArray(parsed)) {
        setSubmitError(`${fieldName} must be a JSON array`);
        return null;
      }
      return parsed as T[];
    } catch {
      setSubmitError(`Invalid JSON in ${fieldName} field`);
      return null;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);

    if (!formData.name.trim()) {
      setSubmitError("Name is required");
      return;
    }

    const stakeholders = parseJsonField<Stakeholder>(formData.stakeholders_json, "Stakeholders");
    if (stakeholders === null) return;

    const dependencies = parseJsonField<Dependency>(formData.dependencies_json, "Dependencies");
    if (dependencies === null) return;

    const filteredStakeholders = stakeholders.filter((s) => s.name && s.name.trim() !== "");
    const filteredDependencies = dependencies.filter((d) => d.name && d.name.trim() !== "");

    try {
      if (isEdit && editSystem) {
        await mapApiRequest<AISystem>(`/compliance/nist/map/ai-systems/${editSystem.id}`, {
          method: "PUT",
          body: JSON.stringify({
            name: formData.name,
            system_type: formData.system_type,
            risk_level: formData.risk_level,
            purpose: formData.purpose,
            scope: formData.scope,
            owner_id: formData.owner_id,
            stakeholders: filteredStakeholders,
            dependencies: filteredDependencies,
          }),
        });
      } else {
        await createMutation.mutateAsync({
          project_id: projectId,
          name: formData.name,
          system_type: formData.system_type,
          risk_level: formData.risk_level,
          purpose: formData.purpose,
          scope: formData.scope,
          owner_id: formData.owner_id,
          stakeholders: filteredStakeholders,
          dependencies: filteredDependencies,
        });
      }
      onSuccess();
      onClose();
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Failed to save AI system");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 w-full max-w-lg rounded-lg bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-200 p-4">
          <h2 className="text-lg font-semibold text-gray-900">
            {isEdit ? "Edit AI System" : "Register AI System"}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="max-h-[70vh] space-y-4 overflow-y-auto p-4">
          {submitError && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-3">
              <p className="text-sm text-red-700">{submitError}</p>
            </div>
          )}

          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="AI system name (e.g., Customer Support Chatbot)"
              required
            />
          </div>

          {/* System Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700">System Type *</label>
            <select
              value={formData.system_type}
              onChange={(e) => setFormData((prev) => ({ ...prev, system_type: e.target.value }))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="nlp">NLP</option>
              <option value="vision">Computer Vision</option>
              <option value="recommendation">Recommendation</option>
              <option value="decision">Decision Support</option>
              <option value="generative">Generative AI</option>
            </select>
          </div>

          {/* Risk Level */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Risk Level *</label>
            <select
              value={formData.risk_level}
              onChange={(e) => setFormData((prev) => ({ ...prev, risk_level: e.target.value }))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="minimal">Minimal</option>
              <option value="limited">Limited</option>
              <option value="high">High</option>
              <option value="unacceptable">Unacceptable</option>
            </select>
          </div>

          {/* Purpose */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Purpose</label>
            <textarea
              value={formData.purpose}
              onChange={(e) => setFormData((prev) => ({ ...prev, purpose: e.target.value }))}
              rows={2}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Describe the purpose and intended use of this AI system"
            />
          </div>

          {/* Scope */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Scope</label>
            <input
              type="text"
              value={formData.scope}
              onChange={(e) => setFormData((prev) => ({ ...prev, scope: e.target.value }))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Internal, Customer-facing, Regulatory"
            />
          </div>

          {/* Owner */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Owner ID</label>
            <input
              type="text"
              value={formData.owner_id}
              onChange={(e) => setFormData((prev) => ({ ...prev, owner_id: e.target.value }))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Person or team responsible for this system"
            />
          </div>

          {/* Stakeholders JSON */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Stakeholders (JSON Array)
            </label>
            <p className="mb-1 text-xs text-gray-400">
              Format: [&#123;&quot;name&quot;, &quot;role&quot;, &quot;organization&quot;&#125;, ...]
            </p>
            <textarea
              value={formData.stakeholders_json}
              onChange={(e) => setFormData((prev) => ({ ...prev, stakeholders_json: e.target.value }))}
              rows={3}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 font-mono text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder='[{"name": "Jane Doe", "role": "Owner", "organization": "Engineering"}]'
            />
          </div>

          {/* Dependencies JSON */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Dependencies (JSON Array)
            </label>
            <p className="mb-1 text-xs text-gray-400">
              Format: [&#123;&quot;name&quot;, &quot;type&quot;, &quot;version&quot;, &quot;provider&quot;&#125;, ...]
            </p>
            <textarea
              value={formData.dependencies_json}
              onChange={(e) => setFormData((prev) => ({ ...prev, dependencies_json: e.target.value }))}
              rows={3}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 font-mono text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder='[{"name": "TensorFlow", "type": "framework", "version": "2.15", "provider": "Google"}]'
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 border-t border-gray-200 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {createMutation.isPending ? (
                <>
                  <ArrowPathIcon className="h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <PlusIcon className="h-4 w-4" />
                  {isEdit ? "Update System" : "Register System"}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// =============================================================================
// StakeholderMap Component
// =============================================================================

function StakeholderMap({ systems }: { systems: AISystem[] }) {
  const systemsWithStakeholders = useMemo(
    () => systems.filter((s) => s.stakeholders && s.stakeholders.length > 0),
    [systems]
  );

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900">Stakeholder Coverage</h3>
      <p className="mt-1 text-sm text-gray-500">
        Stakeholder assignments across registered AI systems
      </p>

      {systemsWithStakeholders.length > 0 ? (
        <div className="mt-4 space-y-4">
          {systemsWithStakeholders.map((system) => (
            <div key={system.id} className="rounded-lg border border-gray-100 bg-gray-50 p-4">
              <div className="flex items-center gap-2">
                <CubeIcon className="h-4 w-4 text-gray-500" />
                <h4 className="text-sm font-semibold text-gray-900">{system.name}</h4>
                <span
                  className={cn(
                    "ml-auto inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                    RISK_LEVEL_BADGE[system.risk_level].color
                  )}
                >
                  {RISK_LEVEL_BADGE[system.risk_level].label}
                </span>
              </div>

              <div className="mt-3 flex flex-wrap gap-2">
                {system.stakeholders.map((stakeholder, idx) => (
                  <div
                    key={`${system.id}-stakeholder-${idx}`}
                    className="inline-flex items-center gap-1.5 rounded-full border border-gray-200 bg-white px-3 py-1"
                  >
                    <span className="text-xs font-medium text-gray-900">{stakeholder.name}</span>
                    <span
                      className={cn(
                        "inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-medium",
                        getStakeholderRoleColor(stakeholder.role)
                      )}
                    >
                      {stakeholder.role}
                    </span>
                    {stakeholder.organization && (
                      <span className="text-[10px] text-gray-400">{stakeholder.organization}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="mt-4 py-8 text-center">
          <UsersIcon className="mx-auto h-8 w-8 text-gray-300" />
          <p className="mt-2 text-sm text-gray-500">
            No stakeholders configured for any AI system. Edit an AI system to add stakeholders.
          </p>
        </div>
      )}

      {/* Summary stats */}
      {systemsWithStakeholders.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-4 border-t border-gray-100 pt-3">
          <div className="text-center">
            <p className="text-lg font-bold text-gray-900">
              {systems.length}
            </p>
            <p className="text-xs text-gray-500">Total Systems</p>
          </div>
          <div className="text-center">
            <p className="text-lg font-bold text-gray-900">
              {systemsWithStakeholders.length}
            </p>
            <p className="text-xs text-gray-500">With Stakeholders</p>
          </div>
          <div className="text-center">
            <p className="text-lg font-bold text-gray-900">
              {systemsWithStakeholders.reduce((sum, s) => sum + s.stakeholders.length, 0)}
            </p>
            <p className="text-xs text-gray-500">Total Assignments</p>
          </div>
          <div className="text-center">
            <p className="text-lg font-bold text-gray-900">
              {new Set(
                systemsWithStakeholders.flatMap((s) =>
                  s.stakeholders.map((st) => st.role.toLowerCase())
                )
              ).size}
            </p>
            <p className="text-xs text-gray-500">Unique Roles</p>
          </div>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// DependencyTable Component
// =============================================================================

function DependencyTable({ systems }: { systems: AISystem[] }) {
  const flatDependencies = useMemo(() => {
    const deps: Array<{ systemId: string; systemName: string; dependency: Dependency }> = [];
    systems.forEach((system) => {
      if (system.dependencies && system.dependencies.length > 0) {
        system.dependencies.forEach((dep) => {
          if (dep.name && dep.name.trim() !== "") {
            deps.push({
              systemId: system.id,
              systemName: system.name,
              dependency: dep,
            });
          }
        });
      }
    });
    return deps;
  }, [systems]);

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900">Dependencies Overview</h3>
      <p className="mt-1 text-sm text-gray-500">
        All dependencies across registered AI systems ({flatDependencies.length} total)
      </p>

      {flatDependencies.length > 0 ? (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="px-3 py-2 text-left font-medium text-gray-700">AI System</th>
                <th className="px-3 py-2 text-left font-medium text-gray-700">Dependency Name</th>
                <th className="px-3 py-2 text-left font-medium text-gray-700">Type</th>
                <th className="px-3 py-2 text-left font-medium text-gray-700">Version</th>
                <th className="px-3 py-2 text-left font-medium text-gray-700">Provider</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {flatDependencies.map((item, idx) => (
                <tr key={`dep-${item.systemId}-${idx}`} className="hover:bg-gray-50">
                  <td className="px-3 py-3">
                    <p className="font-medium text-gray-900">{item.systemName}</p>
                  </td>
                  <td className="px-3 py-3 text-sm text-gray-700">{item.dependency.name}</td>
                  <td className="px-3 py-3">
                    <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700">
                      {item.dependency.type || "Unknown"}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-sm text-gray-700">
                    {item.dependency.version || "N/A"}
                  </td>
                  <td className="px-3 py-3 text-sm text-gray-700">
                    {item.dependency.provider || "N/A"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="mt-4 py-8 text-center">
          <CubeIcon className="mx-auto h-8 w-8 text-gray-300" />
          <p className="mt-2 text-sm text-gray-500">
            No dependencies found. Edit AI systems to add dependency information.
          </p>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// RiskImpactTable Component (Overview tab extra content)
// =============================================================================

function RiskImpactTable({ riskImpacts }: { riskImpacts: RiskImpactMapping[] }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900">Risk-to-Impact Mappings</h3>
      <p className="mt-1 text-sm text-gray-500">
        Risk categories mapped to impact areas across AI systems
      </p>

      {riskImpacts.length > 0 ? (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="px-3 py-2 text-left font-medium text-gray-700">AI System</th>
                <th className="px-3 py-2 text-left font-medium text-gray-700">Risk Category</th>
                <th className="px-3 py-2 text-left font-medium text-gray-700">Impact Area</th>
                <th className="px-3 py-2 text-center font-medium text-gray-700">L x S</th>
                <th className="px-3 py-2 text-center font-medium text-gray-700">Mitigation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {riskImpacts.map((mapping) => {
                const score = mapping.likelihood * mapping.severity;
                const scoreColor =
                  score >= 16
                    ? "text-red-600"
                    : score >= 10
                      ? "text-orange-600"
                      : score >= 5
                        ? "text-yellow-600"
                        : "text-green-600";
                const mitigationConfig = MITIGATION_STATUS_CONFIG[mapping.mitigation_status];

                return (
                  <tr key={mapping.id} className="hover:bg-gray-50">
                    <td className="px-3 py-3">
                      <p className="font-medium text-gray-900">{mapping.ai_system_name}</p>
                    </td>
                    <td className="px-3 py-3 text-sm text-gray-700">{mapping.risk_category}</td>
                    <td className="px-3 py-3 text-sm text-gray-700">{mapping.impact_area}</td>
                    <td className="px-3 py-3 text-center">
                      <span className={cn("text-sm font-semibold", scoreColor)}>
                        {mapping.likelihood} x {mapping.severity} = {score}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-center">
                      <span
                        className={cn(
                          "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
                          mitigationConfig.color
                        )}
                      >
                        {mitigationConfig.label}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="mt-4 py-8 text-center">
          <ExclamationTriangleIcon className="mx-auto h-8 w-8 text-gray-300" />
          <p className="mt-2 text-sm text-gray-500">
            No risk-to-impact mappings found. Evaluate MAP compliance to generate mappings.
          </p>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Loading Skeleton
// =============================================================================

function DashboardSkeleton() {
  return (
    <div className="animate-pulse space-y-6">
      {/* Score Card Skeleton */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="h-6 w-48 rounded bg-gray-200" />
          <div className="h-10 w-32 rounded-lg bg-gray-200" />
        </div>
        <div className="mt-6 flex items-center gap-8">
          <div className="h-32 w-32 rounded-full bg-gray-200" />
          <div className="flex-1 space-y-3">
            <div className="h-4 w-full rounded bg-gray-200" />
            <div className="h-4 w-3/4 rounded bg-gray-200" />
            <div className="h-4 w-1/2 rounded bg-gray-200" />
            <div className="h-4 w-2/3 rounded bg-gray-200" />
          </div>
        </div>
      </div>

      {/* Two Column Skeleton */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <div className="h-6 w-32 rounded bg-gray-200" />
          <div className="mt-4 space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-12 rounded bg-gray-100" />
            ))}
          </div>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <div className="h-6 w-32 rounded bg-gray-200" />
          <div className="mt-4 h-64 rounded bg-gray-100" />
        </div>
      </div>

      {/* Table Skeleton */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="h-6 w-48 rounded bg-gray-200" />
        <div className="mt-4 space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-14 rounded bg-gray-100" />
          ))}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Error Alert
// =============================================================================

function ErrorAlert({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-4">
      <div className="flex items-center gap-3">
        <XCircleIcon className="h-5 w-5 flex-shrink-0 text-red-500" />
        <div>
          <h3 className="text-sm font-medium text-red-800">Error Loading Dashboard</h3>
          <p className="mt-1 text-sm text-red-700">{message}</p>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Tab Configuration
// =============================================================================

type TabId = "overview" | "ai_systems" | "stakeholders" | "dependencies";

interface TabConfig {
  id: TabId;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const TABS: TabConfig[] = [
  { id: "overview", label: "Overview", icon: MapIcon },
  { id: "ai_systems", label: "AI Systems", icon: CubeIcon },
  { id: "stakeholders", label: "Stakeholders", icon: UsersIcon },
  { id: "dependencies", label: "Dependencies", icon: ShieldCheckIcon },
];

// =============================================================================
// Main Page Component
// =============================================================================

export default function NistMapPage() {
  const searchParams = useSearchParams();
  const projectIdParam = searchParams.get("project");

  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(projectIdParam);
  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editingSystem, setEditingSystem] = useState<AISystem | null>(null);
  const [aiSystemsOffset, setAiSystemsOffset] = useState(0);
  const aiSystemsLimit = 20;

  // Fetch projects for selector
  const { data: projects = [] } = useProjects();

  // Determine effective project ID
  const effectiveProjectId = selectedProjectId || projects[0]?.id;

  // Fetch dashboard data
  const {
    data: dashboard,
    isLoading: dashboardLoading,
    error: dashboardError,
  } = useMapDashboard(effectiveProjectId);

  const {
    data: aiSystemsData,
    isLoading: aiSystemsLoading,
    error: aiSystemsError,
  } = useAISystems(effectiveProjectId, aiSystemsLimit, aiSystemsOffset);

  const {
    data: riskImpacts = [],
    isLoading: riskImpactsLoading,
  } = useRiskImpacts(effectiveProjectId);

  // Mutations
  const evaluateMutation = useEvaluateMap();
  const deleteMutation = useDeleteAISystem(effectiveProjectId);
  const queryClient = useQueryClient();

  const handleEvaluate = useCallback(() => {
    if (effectiveProjectId) {
      evaluateMutation.mutate(effectiveProjectId);
    }
  }, [effectiveProjectId, evaluateMutation]);

  const handleDeleteSystem = useCallback(
    (systemId: string) => {
      if (window.confirm("Are you sure you want to delete this AI system? This action cannot be undone.")) {
        deleteMutation.mutate(systemId);
      }
    },
    [deleteMutation]
  );

  const handleDialogSuccess = useCallback(() => {
    if (effectiveProjectId) {
      queryClient.invalidateQueries({
        queryKey: ["compliance", "nist", "map", "ai-systems", effectiveProjectId],
      });
    }
  }, [effectiveProjectId, queryClient]);

  const handleEditSystem = useCallback((system: AISystem) => {
    setEditingSystem(system);
    setShowCreateDialog(true);
  }, []);

  const handleCloseDialog = useCallback(() => {
    setShowCreateDialog(false);
    setEditingSystem(null);
  }, []);

  // Derived state
  const aiSystems = aiSystemsData?.items || [];
  const aiSystemsTotal = aiSystemsData?.total || 0;
  const isLoading = dashboardLoading || aiSystemsLoading || riskImpactsLoading;
  const hasError = dashboardError || aiSystemsError;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">MAP Function Dashboard</h2>
          <p className="mt-1 text-sm text-gray-500">
            AI system mapping, stakeholder coverage, risk-to-impact analysis, and dependency tracking
          </p>
        </div>

        {/* Project Selector */}
        <select
          value={effectiveProjectId || ""}
          onChange={(e) => {
            setSelectedProjectId(e.target.value || null);
            setAiSystemsOffset(0);
          }}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Select Project</option>
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </div>

      {/* No Project Selected */}
      {!effectiveProjectId && (
        <div className="rounded-lg border border-gray-200 bg-white py-12 text-center shadow-sm">
          <MapIcon className="mx-auto h-12 w-12 text-gray-300" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">Select a Project</h3>
          <p className="mt-2 text-sm text-gray-500">
            Choose a project from the dropdown to view NIST AI RMF MAP compliance status.
          </p>
        </div>
      )}

      {/* Error State */}
      {hasError && effectiveProjectId && (
        <ErrorAlert
          message={
            (dashboardError as Error)?.message ||
            (aiSystemsError as Error)?.message ||
            "Failed to load MAP dashboard data. Please try again."
          }
        />
      )}

      {/* Loading State */}
      {isLoading && effectiveProjectId && !hasError && <DashboardSkeleton />}

      {/* Dashboard Content */}
      {!isLoading && !hasError && effectiveProjectId && dashboard && (
        <>
          {/* Tab Navigation */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-6" aria-label="MAP Dashboard Tabs">
              {TABS.map((tab) => {
                const TabIcon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={cn(
                      "flex items-center gap-2 border-b-2 px-1 py-3 text-sm font-medium transition-colors",
                      isActive
                        ? "border-blue-600 text-blue-600"
                        : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
                    )}
                  >
                    <TabIcon className="h-4 w-4" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Overview Tab */}
          {activeTab === "overview" && (
            <div className="space-y-6">
              {/* Score Card */}
              <MapScoreCard
                score={dashboard.overall_score}
                lastEvaluated={dashboard.last_evaluated_at}
                onEvaluate={handleEvaluate}
                isEvaluating={evaluateMutation.isPending}
              />

              {/* Two Column: Policies + Risk Impacts Summary */}
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <PolicyStatusList policies={dashboard.policies} />
                <div className="space-y-6">
                  {/* Quick Stats */}
                  <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                    <h3 className="text-lg font-semibold text-gray-900">MAP Overview</h3>
                    <p className="mt-1 text-sm text-gray-500">AI system mapping summary</p>
                    <div className="mt-4 grid grid-cols-2 gap-4">
                      <div className="rounded-lg bg-blue-50 p-4 text-center">
                        <p className="text-2xl font-bold text-blue-700">{aiSystemsTotal}</p>
                        <p className="text-xs font-medium text-blue-600">AI Systems</p>
                      </div>
                      <div className="rounded-lg bg-purple-50 p-4 text-center">
                        <p className="text-2xl font-bold text-purple-700">
                          {aiSystems.reduce(
                            (sum, s) => sum + (s.stakeholders?.length || 0),
                            0
                          )}
                        </p>
                        <p className="text-xs font-medium text-purple-600">Stakeholders</p>
                      </div>
                      <div className="rounded-lg bg-orange-50 p-4 text-center">
                        <p className="text-2xl font-bold text-orange-700">
                          {aiSystems.reduce(
                            (sum, s) => sum + (s.dependencies?.length || 0),
                            0
                          )}
                        </p>
                        <p className="text-xs font-medium text-orange-600">Dependencies</p>
                      </div>
                      <div className="rounded-lg bg-green-50 p-4 text-center">
                        <p className="text-2xl font-bold text-green-700">{riskImpacts.length}</p>
                        <p className="text-xs font-medium text-green-600">Risk Mappings</p>
                      </div>
                    </div>
                  </div>

                  {/* Risk Level Distribution */}
                  <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                    <h3 className="text-sm font-semibold text-gray-900">Risk Level Distribution</h3>
                    <div className="mt-3 space-y-2">
                      {(["minimal", "limited", "high", "unacceptable"] as const).map((level) => {
                        const count = aiSystems.filter((s) => s.risk_level === level).length;
                        const pct = aiSystemsTotal > 0 ? Math.round((count / aiSystemsTotal) * 100) : 0;
                        const badge = RISK_LEVEL_BADGE[level];
                        return (
                          <div key={level} className="flex items-center gap-3">
                            <span
                              className={cn(
                                "inline-flex w-24 items-center justify-center rounded-full px-2 py-0.5 text-xs font-medium",
                                badge.color
                              )}
                            >
                              {badge.label}
                            </span>
                            <div className="flex-1">
                              <div className="h-2 w-full rounded-full bg-gray-100">
                                <div
                                  className={cn("h-2 rounded-full transition-all duration-500", {
                                    "bg-green-400": level === "minimal",
                                    "bg-blue-400": level === "limited",
                                    "bg-orange-400": level === "high",
                                    "bg-red-400": level === "unacceptable",
                                  })}
                                  style={{ width: `${pct}%` }}
                                />
                              </div>
                            </div>
                            <span className="w-12 text-right text-xs font-medium text-gray-600">
                              {count} ({pct}%)
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>

              {/* Risk Impact Mappings */}
              <RiskImpactTable riskImpacts={riskImpacts} />
            </div>
          )}

          {/* AI Systems Tab */}
          {activeTab === "ai_systems" && (
            <AISystemsTable
              systems={aiSystems}
              total={aiSystemsTotal}
              limit={aiSystemsLimit}
              offset={aiSystemsOffset}
              onPageChange={setAiSystemsOffset}
              onAddSystem={() => {
                setEditingSystem(null);
                setShowCreateDialog(true);
              }}
              onEditSystem={handleEditSystem}
              onDeleteSystem={handleDeleteSystem}
              isDeleting={deleteMutation.isPending}
            />
          )}

          {/* Stakeholders Tab */}
          {activeTab === "stakeholders" && <StakeholderMap systems={aiSystems} />}

          {/* Dependencies Tab */}
          {activeTab === "dependencies" && <DependencyTable systems={aiSystems} />}
        </>
      )}

      {/* Create/Edit AI System Dialog */}
      {showCreateDialog && effectiveProjectId && (
        <CreateAISystemDialog
          projectId={effectiveProjectId}
          editSystem={editingSystem}
          onClose={handleCloseDialog}
          onSuccess={handleDialogSuccess}
        />
      )}
    </div>
  );
}
