/**
 * NIST AI RMF GOVERN Dashboard Page - SDLC Orchestrator
 *
 * @module frontend/src/app/app/compliance/nist/govern/page
 * @description Sprint 156 - NIST AI RMF GOVERN: Governance compliance dashboard
 *   with score card, policy status, risk heatmap, RACI matrix, and risk register.
 * @sdlc SDLC 6.0.5 Universal Framework
 * @status Sprint 156 - NIST AI RMF GOVERN
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

async function governApiRequest<T>(
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

interface GovernDashboardData {
  overall_score: number;
  policies: PolicyStatus[];
  last_evaluated_at: string | null;
}

interface PolicyStatus {
  id: string;
  control_id: string;
  name: string;
  description: string;
  status: "pass" | "fail" | "warning" | "not_evaluated";
  details: string | null;
}

interface ComplianceRisk {
  id: string;
  title: string;
  description: string;
  likelihood: number;
  impact: number;
  risk_level: "critical" | "high" | "medium" | "low";
  owner: string;
  mitigation: string;
  status: "open" | "mitigating" | "accepted" | "closed";
  created_at: string;
}

interface RaciEntry {
  control_id: string;
  control_name: string;
  responsible: string;
  accountable: string;
  consulted: string;
  informed: string;
}

interface CreateRiskPayload {
  project_id: string;
  title: string;
  description: string;
  likelihood: number;
  impact: number;
  owner: string;
  mitigation: string;
}

// =============================================================================
// API Functions
// =============================================================================

async function fetchGovernDashboard(projectId: string): Promise<GovernDashboardData> {
  return governApiRequest<GovernDashboardData>(
    `/compliance/nist/govern/${projectId}/dashboard`
  );
}

async function fetchComplianceRisks(projectId: string): Promise<ComplianceRisk[]> {
  return governApiRequest<ComplianceRisk[]>(
    `/compliance/nist/govern/${projectId}/risks`
  );
}

async function fetchComplianceRaci(projectId: string): Promise<RaciEntry[]> {
  return governApiRequest<RaciEntry[]>(
    `/compliance/nist/govern/${projectId}/raci`
  );
}

async function evaluateGovern(projectId: string): Promise<GovernDashboardData> {
  return governApiRequest<GovernDashboardData>(
    `/compliance/nist/govern/${projectId}/evaluate`,
    { method: "POST" }
  );
}

async function createRisk(payload: CreateRiskPayload): Promise<ComplianceRisk> {
  return governApiRequest<ComplianceRisk>(
    `/compliance/nist/govern/${payload.project_id}/risks`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

// =============================================================================
// Hooks
// =============================================================================

function useGovernDashboard(projectId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  return useQuery({
    queryKey: ["compliance", "nist", "govern", "dashboard", projectId],
    queryFn: () => fetchGovernDashboard(projectId!),
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 60 * 1000,
  });
}

function useComplianceRisks(projectId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  return useQuery({
    queryKey: ["compliance", "nist", "govern", "risks", projectId],
    queryFn: () => fetchComplianceRisks(projectId!),
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 60 * 1000,
  });
}

function useComplianceRaci(projectId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  return useQuery({
    queryKey: ["compliance", "nist", "govern", "raci", projectId],
    queryFn: () => fetchComplianceRaci(projectId!),
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 5 * 60 * 1000,
  });
}

function useEvaluateGovern() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (projectId: string) => evaluateGovern(projectId),
    onSuccess: (_, projectId) => {
      queryClient.invalidateQueries({
        queryKey: ["compliance", "nist", "govern", "dashboard", projectId],
      });
    },
  });
}

function useCreateRisk() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateRiskPayload) => createRisk(payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["compliance", "nist", "govern", "risks", variables.project_id],
      });
    },
  });
}

// =============================================================================
// Icon Components
// =============================================================================

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

const POLICY_STATUS_CONFIG: Record<PolicyStatus["status"], { label: string; color: string; icon: React.ComponentType<{ className?: string }> }> = {
  pass: { label: "Pass", color: "bg-green-100 text-green-700", icon: CheckCircleIcon },
  fail: { label: "Fail", color: "bg-red-100 text-red-700", icon: XCircleIcon },
  warning: { label: "Warning", color: "bg-yellow-100 text-yellow-700", icon: ExclamationTriangleIcon },
  not_evaluated: { label: "Not Evaluated", color: "bg-gray-100 text-gray-500", icon: ShieldCheckIcon },
};

const RISK_LEVEL_CONFIG: Record<ComplianceRisk["risk_level"], { label: string; color: string }> = {
  critical: { label: "Critical", color: "bg-red-100 text-red-800" },
  high: { label: "High", color: "bg-orange-100 text-orange-800" },
  medium: { label: "Medium", color: "bg-yellow-100 text-yellow-800" },
  low: { label: "Low", color: "bg-green-100 text-green-800" },
};

const RISK_STATUS_CONFIG: Record<ComplianceRisk["status"], { label: string; color: string }> = {
  open: { label: "Open", color: "bg-red-100 text-red-700" },
  mitigating: { label: "Mitigating", color: "bg-blue-100 text-blue-700" },
  accepted: { label: "Accepted", color: "bg-yellow-100 text-yellow-700" },
  closed: { label: "Closed", color: "bg-gray-100 text-gray-500" },
};

// =============================================================================
// GovernScoreCard Component
// =============================================================================

function GovernScoreCard({
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
        <h3 className="text-lg font-semibold text-gray-900">GOVERN Compliance Score</h3>
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
              Evaluate Now
            </>
          )}
        </button>
      </div>

      <div className="mt-6 flex items-center gap-8">
        {/* Circular Progress */}
        <div className="relative h-32 w-32 flex-shrink-0">
          <svg className="h-32 w-32 -rotate-90" viewBox="0 0 120 120">
            <circle
              cx="60"
              cy="60"
              r="54"
              fill="none"
              stroke="#e5e7eb"
              strokeWidth="8"
            />
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
            <span className={cn("text-3xl font-bold", scoreColor)}>
              {percentage}%
            </span>
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
              <span className="text-sm font-medium text-gray-900">GOVERN</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Last Evaluated</span>
              <span className="text-sm font-medium text-gray-900">{formatDate(lastEvaluated)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Status</span>
              <span className={cn(
                "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
                percentage >= 80 ? "bg-green-100 text-green-800" : percentage >= 50 ? "bg-yellow-100 text-yellow-800" : "bg-red-100 text-red-800"
              )}>
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

function PolicyStatusList({ policies }: { policies: PolicyStatus[] }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900">Policy Status</h3>
      <p className="mt-1 text-sm text-gray-500">GOVERN function control assessment results</p>

      <div className="mt-4 divide-y divide-gray-200">
        {policies.map((policy) => {
          const config = POLICY_STATUS_CONFIG[policy.status];
          const StatusIcon = config.icon;
          return (
            <div key={policy.id} className="flex items-center justify-between py-3">
              <div className="flex items-start gap-3">
                <StatusIcon className={cn("mt-0.5 h-5 w-5 flex-shrink-0", {
                  "text-green-500": policy.status === "pass",
                  "text-red-500": policy.status === "fail",
                  "text-yellow-500": policy.status === "warning",
                  "text-gray-400": policy.status === "not_evaluated",
                })} />
                <div>
                  <p className="text-sm font-medium text-gray-900">{policy.name}</p>
                  <p className="text-xs text-gray-500">{policy.control_id}</p>
                  {policy.details && (
                    <p className="mt-1 text-xs text-gray-600">{policy.details}</p>
                  )}
                </div>
              </div>
              <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", config.color)}>
                {config.label}
              </span>
            </div>
          );
        })}
      </div>

      {policies.length === 0 && (
        <div className="py-8 text-center">
          <ShieldCheckIcon className="mx-auto h-8 w-8 text-gray-300" />
          <p className="mt-2 text-sm text-gray-500">No policies evaluated yet. Run an evaluation to check compliance.</p>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// RiskHeatmap Component
// =============================================================================

function RiskHeatmap({ risks }: { risks: ComplianceRisk[] }) {
  const heatmapData = useMemo(() => {
    const grid: Record<string, ComplianceRisk[]> = {};
    for (let likelihood = 1; likelihood <= 5; likelihood++) {
      for (let impact = 1; impact <= 5; impact++) {
        grid[`${likelihood}-${impact}`] = [];
      }
    }
    risks.forEach((risk) => {
      const key = `${risk.likelihood}-${risk.impact}`;
      if (grid[key]) {
        grid[key].push(risk);
      }
    });
    return grid;
  }, [risks]);

  const getCellColor = (likelihood: number, impact: number): string => {
    const score = likelihood * impact;
    if (score >= 20) return "bg-red-500 text-white";
    if (score >= 12) return "bg-orange-400 text-white";
    if (score >= 6) return "bg-yellow-300 text-gray-900";
    if (score >= 3) return "bg-green-200 text-gray-900";
    return "bg-green-100 text-gray-700";
  };

  const likelihoodLabels = ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"];
  const impactLabels = ["Negligible", "Minor", "Moderate", "Major", "Severe"];

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900">Risk Heatmap</h3>
      <p className="mt-1 text-sm text-gray-500">5x5 Likelihood vs. Impact risk assessment grid</p>

      <div className="mt-4 overflow-x-auto">
        <div className="inline-block min-w-[480px]">
          {/* Impact Header */}
          <div className="mb-1 ml-28 grid grid-cols-5 gap-1">
            {impactLabels.map((label) => (
              <div key={label} className="text-center text-xs font-medium text-gray-500 truncate px-0.5">
                {label}
              </div>
            ))}
          </div>

          <div className="flex">
            {/* Likelihood Labels */}
            <div className="flex w-28 flex-shrink-0 flex-col justify-between py-0.5">
              {likelihoodLabels.slice().reverse().map((label) => (
                <div key={label} className="flex h-16 items-center text-xs font-medium text-gray-500">
                  <span className="truncate">{label}</span>
                </div>
              ))}
            </div>

            {/* Grid */}
            <div className="flex-1">
              <div className="grid grid-rows-5 gap-1">
                {[5, 4, 3, 2, 1].map((likelihood) => (
                  <div key={likelihood} className="grid grid-cols-5 gap-1">
                    {[1, 2, 3, 4, 5].map((impact) => {
                      const key = `${likelihood}-${impact}`;
                      const cellRisks = heatmapData[key] || [];
                      return (
                        <div
                          key={key}
                          className={cn(
                            "flex h-16 items-center justify-center rounded-md text-xs font-semibold transition-transform hover:scale-105",
                            getCellColor(likelihood, impact)
                          )}
                          title={
                            cellRisks.length > 0
                              ? cellRisks.map((r) => r.title).join(", ")
                              : `L${likelihood} x I${impact} = ${likelihood * impact}`
                          }
                        >
                          {cellRisks.length > 0 ? (
                            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-white/30 text-sm font-bold">
                              {cellRisks.length}
                            </span>
                          ) : (
                            <span className="opacity-40">{likelihood * impact}</span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Axis labels */}
          <div className="mt-2 flex items-center justify-center gap-8">
            <span className="text-xs font-medium text-gray-500">Impact &rarr;</span>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <span className="text-xs text-gray-500">Risk Level:</span>
        <div className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-sm bg-green-100" />
          <span className="text-xs text-gray-600">Low</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-sm bg-yellow-300" />
          <span className="text-xs text-gray-600">Medium</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-sm bg-orange-400" />
          <span className="text-xs text-gray-600">High</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-sm bg-red-500" />
          <span className="text-xs text-gray-600">Critical</span>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// RACIMatrix Component
// =============================================================================

function RACIMatrix({ entries }: { entries: RaciEntry[] }) {
  const roleColors: Record<string, string> = {
    R: "bg-blue-100 text-blue-700",
    A: "bg-red-100 text-red-700",
    C: "bg-yellow-100 text-yellow-700",
    I: "bg-gray-100 text-gray-600",
  };

  function RaciBadge({ letter }: { letter: string }) {
    return (
      <span className={cn("inline-flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold", roleColors[letter] || "bg-gray-100 text-gray-500")}>
        {letter}
      </span>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900">RACI Matrix</h3>
      <p className="mt-1 text-sm text-gray-500">Control responsibility assignments</p>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="px-3 py-2 text-left font-medium text-gray-700">Control</th>
              <th className="px-3 py-2 text-center font-medium text-gray-700">Responsible</th>
              <th className="px-3 py-2 text-center font-medium text-gray-700">Accountable</th>
              <th className="px-3 py-2 text-center font-medium text-gray-700">Consulted</th>
              <th className="px-3 py-2 text-center font-medium text-gray-700">Informed</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {entries.map((entry) => (
              <tr key={entry.control_id} className="hover:bg-gray-50">
                <td className="px-3 py-3">
                  <div>
                    <p className="font-medium text-gray-900">{entry.control_name}</p>
                    <p className="text-xs text-gray-500">{entry.control_id}</p>
                  </div>
                </td>
                <td className="px-3 py-3 text-center">
                  <div className="flex flex-col items-center gap-1">
                    <RaciBadge letter="R" />
                    <span className="text-xs text-gray-500 truncate max-w-[100px]">{entry.responsible}</span>
                  </div>
                </td>
                <td className="px-3 py-3 text-center">
                  <div className="flex flex-col items-center gap-1">
                    <RaciBadge letter="A" />
                    <span className="text-xs text-gray-500 truncate max-w-[100px]">{entry.accountable}</span>
                  </div>
                </td>
                <td className="px-3 py-3 text-center">
                  <div className="flex flex-col items-center gap-1">
                    <RaciBadge letter="C" />
                    <span className="text-xs text-gray-500 truncate max-w-[100px]">{entry.consulted}</span>
                  </div>
                </td>
                <td className="px-3 py-3 text-center">
                  <div className="flex flex-col items-center gap-1">
                    <RaciBadge letter="I" />
                    <span className="text-xs text-gray-500 truncate max-w-[100px]">{entry.informed}</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {entries.length === 0 && (
        <div className="py-8 text-center">
          <p className="text-sm text-gray-500">No RACI assignments configured. Run an evaluation to generate assignments.</p>
        </div>
      )}

      {/* Legend */}
      <div className="mt-4 flex flex-wrap items-center gap-4 border-t border-gray-100 pt-3">
        <div className="flex items-center gap-1.5">
          <RaciBadge letter="R" />
          <span className="text-xs text-gray-600">Responsible</span>
        </div>
        <div className="flex items-center gap-1.5">
          <RaciBadge letter="A" />
          <span className="text-xs text-gray-600">Accountable</span>
        </div>
        <div className="flex items-center gap-1.5">
          <RaciBadge letter="C" />
          <span className="text-xs text-gray-600">Consulted</span>
        </div>
        <div className="flex items-center gap-1.5">
          <RaciBadge letter="I" />
          <span className="text-xs text-gray-600">Informed</span>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// RiskRegisterTable Component
// =============================================================================

function RiskRegisterTable({
  risks,
  onAddRisk,
}: {
  risks: ComplianceRisk[];
  onAddRisk: () => void;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Risk Register</h3>
          <p className="mt-1 text-sm text-gray-500">{risks.length} risk entries tracked</p>
        </div>
        <button
          onClick={onAddRisk}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <PlusIcon className="h-4 w-4" />
          Add Risk
        </button>
      </div>

      {risks.length > 0 ? (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="px-3 py-2 text-left font-medium text-gray-700">Title</th>
                <th className="px-3 py-2 text-center font-medium text-gray-700">Level</th>
                <th className="px-3 py-2 text-center font-medium text-gray-700">L x I</th>
                <th className="px-3 py-2 text-left font-medium text-gray-700">Owner</th>
                <th className="px-3 py-2 text-center font-medium text-gray-700">Status</th>
                <th className="px-3 py-2 text-left font-medium text-gray-700">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {risks.map((risk) => {
                const levelConfig = RISK_LEVEL_CONFIG[risk.risk_level];
                const statusConfig = RISK_STATUS_CONFIG[risk.status];
                return (
                  <tr key={risk.id} className="hover:bg-gray-50">
                    <td className="px-3 py-3">
                      <div>
                        <p className="font-medium text-gray-900">{risk.title}</p>
                        <p className="mt-0.5 text-xs text-gray-500 line-clamp-1">{risk.description}</p>
                      </div>
                    </td>
                    <td className="px-3 py-3 text-center">
                      <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", levelConfig.color)}>
                        {levelConfig.label}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-center">
                      <span className="text-sm font-medium text-gray-700">
                        {risk.likelihood} x {risk.impact}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-sm text-gray-700">{risk.owner}</td>
                    <td className="px-3 py-3 text-center">
                      <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", statusConfig.color)}>
                        {statusConfig.label}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-xs text-gray-500">{formatDate(risk.created_at)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="mt-4 py-8 text-center">
          <ExclamationTriangleIcon className="mx-auto h-8 w-8 text-gray-300" />
          <p className="mt-2 text-sm text-gray-500">No risks registered yet. Add your first risk entry to begin tracking.</p>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Create Risk Dialog
// =============================================================================

function CreateRiskDialog({
  projectId,
  onClose,
  onSuccess,
}: {
  projectId: string;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState<Omit<CreateRiskPayload, "project_id">>({
    title: "",
    description: "",
    likelihood: 3,
    impact: 3,
    owner: "",
    mitigation: "",
  });

  const createMutation = useCreateRisk();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title || !formData.description || !formData.owner) {
      return;
    }

    try {
      await createMutation.mutateAsync({
        project_id: projectId,
        ...formData,
      });
      onSuccess();
      onClose();
    } catch {
      // Error handled by mutation
    }
  };

  const computedScore = formData.likelihood * formData.impact;
  const computedLevel = computedScore >= 20 ? "Critical" : computedScore >= 12 ? "High" : computedScore >= 6 ? "Medium" : "Low";
  const computedColor = computedScore >= 20 ? "text-red-600" : computedScore >= 12 ? "text-orange-600" : computedScore >= 6 ? "text-yellow-600" : "text-green-600";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 w-full max-w-lg rounded-lg bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-200 p-4">
          <h2 className="text-lg font-semibold text-gray-900">Add Risk Entry</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 p-4">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Title *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData((prev) => ({ ...prev, title: e.target.value }))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Brief title for the risk"
              required
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Description *</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
              rows={3}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Detailed description of the risk and its potential consequences"
              required
            />
          </div>

          {/* Likelihood & Impact */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Likelihood (1-5): {formData.likelihood}
              </label>
              <input
                type="range"
                min={1}
                max={5}
                value={formData.likelihood}
                onChange={(e) => setFormData((prev) => ({ ...prev, likelihood: parseInt(e.target.value) }))}
                className="mt-2 w-full"
              />
              <div className="mt-1 flex justify-between text-xs text-gray-400">
                <span>Rare</span>
                <span>Certain</span>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Impact (1-5): {formData.impact}
              </label>
              <input
                type="range"
                min={1}
                max={5}
                value={formData.impact}
                onChange={(e) => setFormData((prev) => ({ ...prev, impact: parseInt(e.target.value) }))}
                className="mt-2 w-full"
              />
              <div className="mt-1 flex justify-between text-xs text-gray-400">
                <span>Negligible</span>
                <span>Severe</span>
              </div>
            </div>
          </div>

          {/* Computed Risk Level */}
          <div className="rounded-lg bg-gray-50 p-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Risk Score</span>
              <span className={cn("text-sm font-bold", computedColor)}>
                {computedScore} ({computedLevel})
              </span>
            </div>
          </div>

          {/* Owner */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Owner *</label>
            <input
              type="text"
              value={formData.owner}
              onChange={(e) => setFormData((prev) => ({ ...prev, owner: e.target.value }))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Person or team responsible"
              required
            />
          </div>

          {/* Mitigation */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Mitigation Plan</label>
            <textarea
              value={formData.mitigation}
              onChange={(e) => setFormData((prev) => ({ ...prev, mitigation: e.target.value }))}
              rows={2}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Planned actions to mitigate this risk"
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
                  Adding...
                </>
              ) : (
                <>
                  <PlusIcon className="h-4 w-4" />
                  Add Risk
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
// Main Page Component
// =============================================================================

export default function GovernDashboardPage() {
  const searchParams = useSearchParams();
  const projectIdParam = searchParams.get("project");

  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(projectIdParam);
  const [showCreateRisk, setShowCreateRisk] = useState(false);

  // Fetch projects for selector
  const { data: projects = [] } = useProjects();

  // Determine effective project ID
  const effectiveProjectId = selectedProjectId || projects[0]?.id;

  // Fetch dashboard data
  const {
    data: dashboard,
    isLoading: dashboardLoading,
    error: dashboardError,
  } = useGovernDashboard(effectiveProjectId);

  const {
    data: risks = [],
    isLoading: risksLoading,
    error: risksError,
  } = useComplianceRisks(effectiveProjectId);

  const {
    data: raciEntries = [],
    isLoading: raciLoading,
  } = useComplianceRaci(effectiveProjectId);

  // Mutations
  const evaluateMutation = useEvaluateGovern();

  const handleEvaluate = useCallback(() => {
    if (effectiveProjectId) {
      evaluateMutation.mutate(effectiveProjectId);
    }
  }, [effectiveProjectId, evaluateMutation]);

  // Derived state
  const isLoading = dashboardLoading || risksLoading || raciLoading;
  const hasError = dashboardError || risksError;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">GOVERN Function Dashboard</h2>
          <p className="mt-1 text-sm text-gray-500">
            AI governance policies, risk structures, and accountability frameworks
          </p>
        </div>

        {/* Project Selector */}
        <select
          value={effectiveProjectId || ""}
          onChange={(e) => setSelectedProjectId(e.target.value || null)}
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
          <ShieldCheckIcon className="mx-auto h-12 w-12 text-gray-300" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">Select a Project</h3>
          <p className="mt-2 text-sm text-gray-500">
            Choose a project from the dropdown to view NIST AI RMF GOVERN compliance status.
          </p>
        </div>
      )}

      {/* Error State */}
      {hasError && effectiveProjectId && (
        <ErrorAlert
          message={
            (dashboardError as Error)?.message ||
            (risksError as Error)?.message ||
            "Failed to load compliance dashboard data. Please try again."
          }
        />
      )}

      {/* Loading State */}
      {isLoading && effectiveProjectId && !hasError && <DashboardSkeleton />}

      {/* Dashboard Content */}
      {!isLoading && !hasError && effectiveProjectId && dashboard && (
        <>
          {/* Score Card */}
          <GovernScoreCard
            score={dashboard.overall_score}
            lastEvaluated={dashboard.last_evaluated_at}
            onEvaluate={handleEvaluate}
            isEvaluating={evaluateMutation.isPending}
          />

          {/* Two Column: Policies + Heatmap */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <PolicyStatusList policies={dashboard.policies} />
            <RiskHeatmap risks={risks} />
          </div>

          {/* RACI Matrix */}
          <RACIMatrix entries={raciEntries} />

          {/* Risk Register */}
          <RiskRegisterTable
            risks={risks}
            onAddRisk={() => setShowCreateRisk(true)}
          />
        </>
      )}

      {/* Create Risk Dialog */}
      {showCreateRisk && effectiveProjectId && (
        <CreateRiskDialog
          projectId={effectiveProjectId}
          onClose={() => setShowCreateRisk(false)}
          onSuccess={() => setShowCreateRisk(false)}
        />
      )}
    </div>
  );
}
