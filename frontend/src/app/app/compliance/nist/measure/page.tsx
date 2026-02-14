/**
 * NIST AI RMF MEASURE Dashboard Page - SDLC Orchestrator
 *
 * @module frontend/src/app/app/compliance/nist/measure/page
 * @description Sprint 156 - NIST AI RMF MEASURE: Performance metrics, bias analysis,
 *   trend visualization, and measurement compliance dashboard.
 * @sdlc SDLC 6.0.5 Universal Framework
 * @status Sprint 156 - NIST AI RMF MEASURE
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

async function measureApiRequest<T>(
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

interface MeasureDashboardData {
  overall_score: number;
  policies: MeasurePolicyStatus[];
  last_evaluated_at: string | null;
  total_metrics: number;
  within_threshold_count: number;
  bias_groups_count: number;
  disparity_compliant: number;
  disparity_non_compliant: number;
}

interface MeasurePolicyStatus {
  id: string;
  control_id: string;
  name: string;
  description: string;
  status: "pass" | "fail" | "warning" | "not_evaluated";
  details: string | null;
}

interface PerformanceMetric {
  id: string;
  ai_system_id: string;
  ai_system_name: string;
  metric_type: string;
  metric_name: string;
  metric_value: number;
  threshold_min: number | null;
  threshold_max: number | null;
  unit: string;
  demographic_group: string | null;
  measured_at: string;
  notes: string | null;
  within_threshold: boolean;
}

interface MetricTrendPoint {
  date: string;
  value: number;
  within_threshold: boolean;
}

interface MetricTrendData {
  ai_system_id: string;
  ai_system_name: string;
  metric_type: string;
  points: MetricTrendPoint[];
}

interface BiasSummaryEntry {
  ai_system_id: string;
  ai_system_name: string;
  demographic_group: string;
  bias_score: number;
  within_threshold: boolean;
}

interface BiasSummaryData {
  entries: BiasSummaryEntry[];
  systems: { id: string; name: string }[];
  groups: string[];
  disparity_ratios: Record<string, { ratio: number; compliant: boolean }>;
}

interface AISystem {
  id: string;
  name: string;
  description: string | null;
}

interface CreateMetricPayload {
  project_id: string;
  ai_system_id: string;
  metric_type: string;
  metric_name: string;
  metric_value: number;
  threshold_min: number | null;
  threshold_max: number | null;
  unit: string;
  demographic_group: string | null;
  measured_at: string;
  notes: string | null;
}

// =============================================================================
// API Functions
// =============================================================================

async function fetchMeasureDashboard(projectId: string): Promise<MeasureDashboardData> {
  return measureApiRequest<MeasureDashboardData>(
    `/compliance/nist/measure/dashboard?project_id=${projectId}`
  );
}

async function evaluateMeasure(projectId: string): Promise<MeasureDashboardData> {
  return measureApiRequest<MeasureDashboardData>(
    `/compliance/nist/measure/evaluate`,
    { method: "POST", body: JSON.stringify({ project_id: projectId }) }
  );
}

async function fetchMetrics(
  projectId: string,
  aiSystemId?: string,
  metricType?: string
): Promise<PerformanceMetric[]> {
  const params = new URLSearchParams({ project_id: projectId });
  if (aiSystemId) params.set("ai_system_id", aiSystemId);
  if (metricType) params.set("metric_type", metricType);
  return measureApiRequest<PerformanceMetric[]>(
    `/compliance/nist/measure/metrics?${params.toString()}`
  );
}

async function createMetric(payload: CreateMetricPayload): Promise<PerformanceMetric> {
  return measureApiRequest<PerformanceMetric>(
    `/compliance/nist/measure/metrics`,
    { method: "POST", body: JSON.stringify(payload) }
  );
}

async function fetchMetricTrend(
  aiSystemId: string,
  metricType: string,
  days: number = 30
): Promise<MetricTrendData> {
  return measureApiRequest<MetricTrendData>(
    `/compliance/nist/measure/metrics/trend?ai_system_id=${aiSystemId}&metric_type=${metricType}&days=${days}`
  );
}

async function fetchBiasSummary(projectId: string): Promise<BiasSummaryData> {
  return measureApiRequest<BiasSummaryData>(
    `/compliance/nist/measure/bias-summary?project_id=${projectId}`
  );
}

async function fetchAISystems(projectId: string): Promise<AISystem[]> {
  return measureApiRequest<AISystem[]>(
    `/compliance/nist/map/ai-systems?project_id=${projectId}`
  );
}

// =============================================================================
// Hooks
// =============================================================================

function useMeasureDashboard(projectId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  return useQuery({
    queryKey: ["compliance", "nist", "measure", "dashboard", projectId],
    queryFn: () => fetchMeasureDashboard(projectId!),
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 60 * 1000,
  });
}

function useEvaluateMeasure() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (projectId: string) => evaluateMeasure(projectId),
    onSuccess: (_, projectId) => {
      queryClient.invalidateQueries({
        queryKey: ["compliance", "nist", "measure", "dashboard", projectId],
      });
      queryClient.invalidateQueries({
        queryKey: ["compliance", "nist", "measure", "metrics"],
      });
    },
  });
}

function useMetrics(
  projectId: string | undefined,
  aiSystemId?: string,
  metricType?: string
) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  return useQuery({
    queryKey: ["compliance", "nist", "measure", "metrics", projectId, aiSystemId, metricType],
    queryFn: () => fetchMetrics(projectId!, aiSystemId, metricType),
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 60 * 1000,
  });
}

function useCreateMetric() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateMetricPayload) => createMetric(payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["compliance", "nist", "measure", "metrics", variables.project_id],
      });
      queryClient.invalidateQueries({
        queryKey: ["compliance", "nist", "measure", "dashboard", variables.project_id],
      });
      queryClient.invalidateQueries({
        queryKey: ["compliance", "nist", "measure", "bias-summary", variables.project_id],
      });
    },
  });
}

function useMetricTrend(
  aiSystemId: string | undefined,
  metricType: string | undefined,
  days: number = 30
) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  return useQuery({
    queryKey: ["compliance", "nist", "measure", "trend", aiSystemId, metricType, days],
    queryFn: () => fetchMetricTrend(aiSystemId!, metricType!, days),
    enabled: isAuthenticated && !authLoading && !!aiSystemId && !!metricType,
    staleTime: 60 * 1000,
  });
}

function useBiasSummary(projectId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  return useQuery({
    queryKey: ["compliance", "nist", "measure", "bias-summary", projectId],
    queryFn: () => fetchBiasSummary(projectId!),
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 60 * 1000,
  });
}

function useAISystems(projectId: string | undefined) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  return useQuery({
    queryKey: ["compliance", "nist", "map", "ai-systems", projectId],
    queryFn: () => fetchAISystems(projectId!),
    enabled: isAuthenticated && !authLoading && !!projectId,
    staleTime: 5 * 60 * 1000,
  });
}

// =============================================================================
// Icon Components
// =============================================================================

function ChartBarIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
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

function ShieldCheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
    </svg>
  );
}

function ChevronLeftIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
    </svg>
  );
}

function ChevronRightIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
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

function formatShortDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

function formatMetricValue(value: number, unit: string): string {
  if (unit === "%" || unit === "percent") {
    return `${(value * 100).toFixed(1)}%`;
  }
  if (unit === "ms") {
    return `${value.toFixed(0)}ms`;
  }
  if (unit === "s") {
    return `${value.toFixed(2)}s`;
  }
  return value.toFixed(4);
}

const METRIC_TYPES = [
  { value: "accuracy", label: "Accuracy" },
  { value: "precision", label: "Precision" },
  { value: "recall", label: "Recall" },
  { value: "f1_score", label: "F1 Score" },
  { value: "latency_p95", label: "Latency (P95)" },
  { value: "bias_score", label: "Bias Score" },
  { value: "disparity_index", label: "Disparity Index" },
  { value: "custom", label: "Custom" },
];

const POLICY_STATUS_CONFIG: Record<
  MeasurePolicyStatus["status"],
  { label: string; color: string; icon: React.ComponentType<{ className?: string }> }
> = {
  pass: { label: "Pass", color: "bg-green-100 text-green-700", icon: CheckCircleIcon },
  fail: { label: "Fail", color: "bg-red-100 text-red-700", icon: XCircleIcon },
  warning: { label: "Warning", color: "bg-yellow-100 text-yellow-700", icon: ExclamationTriangleIcon },
  not_evaluated: { label: "Not Evaluated", color: "bg-gray-100 text-gray-500", icon: ChartBarIcon },
};

const ITEMS_PER_PAGE = 10;

// =============================================================================
// MeasureScoreCard Component
// =============================================================================

function MeasureScoreCard({
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
        <h3 className="text-lg font-semibold text-gray-900">MEASURE Compliance Score</h3>
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
              <ChartBarIcon className="h-4 w-4" />
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
              <span className="text-sm font-medium text-gray-900">MEASURE</span>
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

function PolicyStatusList({ policies }: { policies: MeasurePolicyStatus[] }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900">Policy Status</h3>
      <p className="mt-1 text-sm text-gray-500">MEASURE function control assessment results</p>

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
          <ChartBarIcon className="mx-auto h-8 w-8 text-gray-300" />
          <p className="mt-2 text-sm text-gray-500">
            No policies evaluated yet. Run an evaluation to check MEASURE compliance.
          </p>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// MetricSummaryCards Component
// =============================================================================

function MetricSummaryCards({
  totalMetrics,
  withinThreshold,
  biasGroups,
  disparityCompliant,
  disparityNonCompliant,
}: {
  totalMetrics: number;
  withinThreshold: number;
  biasGroups: number;
  disparityCompliant: number;
  disparityNonCompliant: number;
}) {
  const thresholdPercentage = totalMetrics > 0 ? Math.round((withinThreshold / totalMetrics) * 100) : 0;

  const cards = [
    {
      title: "Total Metrics",
      value: totalMetrics.toString(),
      subtitle: "Recorded measurements",
      color: "border-blue-200 bg-blue-50",
      textColor: "text-blue-700",
    },
    {
      title: "Within Threshold",
      value: `${withinThreshold}`,
      subtitle: `${thresholdPercentage}% of total`,
      color: "border-green-200 bg-green-50",
      textColor: "text-green-700",
    },
    {
      title: "Bias Groups",
      value: biasGroups.toString(),
      subtitle: "Distinct demographic groups",
      color: "border-purple-200 bg-purple-50",
      textColor: "text-purple-700",
    },
    {
      title: "Disparity Status",
      value: `${disparityCompliant}/${disparityCompliant + disparityNonCompliant}`,
      subtitle: disparityNonCompliant > 0 ? `${disparityNonCompliant} non-compliant` : "All compliant",
      color: disparityNonCompliant > 0 ? "border-red-200 bg-red-50" : "border-green-200 bg-green-50",
      textColor: disparityNonCompliant > 0 ? "text-red-700" : "text-green-700",
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <div key={card.title} className={cn("rounded-lg border p-4 shadow-sm", card.color)}>
          <p className="text-sm font-medium text-gray-600">{card.title}</p>
          <p className={cn("mt-1 text-2xl font-bold", card.textColor)}>{card.value}</p>
          <p className="mt-1 text-xs text-gray-500">{card.subtitle}</p>
        </div>
      ))}
    </div>
  );
}

// =============================================================================
// MetricTrendChart Component
// =============================================================================

function MetricTrendChart({
  aiSystems,
  projectId,
}: {
  aiSystems: AISystem[];
  projectId: string;
}) {
  const [selectedSystemId, setSelectedSystemId] = useState<string>("");
  const [selectedMetricType, setSelectedMetricType] = useState<string>("");

  const {
    data: trendData,
    isLoading,
  } = useMetricTrend(
    selectedSystemId || undefined,
    selectedMetricType || undefined
  );

  const maxValue = useMemo(() => {
    if (!trendData?.points?.length) return 1;
    return Math.max(...trendData.points.map((p) => p.value), 0.001);
  }, [trendData]);

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900">Metric Trends</h3>
      <p className="mt-1 text-sm text-gray-500">Last 30 days of performance data points</p>

      {/* Filters */}
      <div className="mt-4 flex flex-wrap gap-3">
        <select
          value={selectedSystemId}
          onChange={(e) => setSelectedSystemId(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Select AI System</option>
          {aiSystems.map((sys) => (
            <option key={sys.id} value={sys.id}>
              {sys.name}
            </option>
          ))}
        </select>
        <select
          value={selectedMetricType}
          onChange={(e) => setSelectedMetricType(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Select Metric Type</option>
          {METRIC_TYPES.map((mt) => (
            <option key={mt.value} value={mt.value}>
              {mt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Content */}
      {!selectedSystemId || !selectedMetricType ? (
        <div className="mt-6 py-8 text-center">
          <ChartBarIcon className="mx-auto h-8 w-8 text-gray-300" />
          <p className="mt-2 text-sm text-gray-500">
            Select an AI system and metric type to view trends.
          </p>
        </div>
      ) : isLoading ? (
        <div className="mt-6 animate-pulse space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-8 rounded bg-gray-100" />
          ))}
        </div>
      ) : !trendData?.points?.length ? (
        <div className="mt-6 py-8 text-center">
          <ChartBarIcon className="mx-auto h-8 w-8 text-gray-300" />
          <p className="mt-2 text-sm text-gray-500">No trend data available for this selection.</p>
        </div>
      ) : (
        <div className="mt-4">
          {/* Simple bar visualization */}
          <div className="space-y-1.5">
            {trendData.points.map((point, idx) => {
              const barWidth = Math.max((point.value / maxValue) * 100, 2);
              return (
                <div key={idx} className="flex items-center gap-3">
                  <span className="w-16 flex-shrink-0 text-xs text-gray-500 text-right">
                    {formatShortDate(point.date)}
                  </span>
                  <div className="flex-1">
                    <div
                      className={cn(
                        "h-5 rounded-r transition-all",
                        point.within_threshold ? "bg-green-400" : "bg-red-400"
                      )}
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                  <span className="w-16 flex-shrink-0 text-xs font-medium text-gray-700 text-right">
                    {point.value.toFixed(4)}
                  </span>
                  <span className="w-5 flex-shrink-0">
                    {point.within_threshold ? (
                      <CheckCircleIcon className="h-4 w-4 text-green-500" />
                    ) : (
                      <XCircleIcon className="h-4 w-4 text-red-500" />
                    )}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Legend */}
          <div className="mt-4 flex items-center gap-4 border-t border-gray-100 pt-3">
            <div className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-sm bg-green-400" />
              <span className="text-xs text-gray-600">Within Threshold</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-sm bg-red-400" />
              <span className="text-xs text-gray-600">Exceeded Threshold</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// BiasHeatmap Component
// =============================================================================

function BiasHeatmap({ projectId }: { projectId: string }) {
  const { data: biasSummary, isLoading } = useBiasSummary(projectId);

  const heatmapGrid = useMemo(() => {
    if (!biasSummary) return {};
    const grid: Record<string, BiasSummaryEntry> = {};
    biasSummary.entries.forEach((entry) => {
      grid[`${entry.ai_system_id}::${entry.demographic_group}`] = entry;
    });
    return grid;
  }, [biasSummary]);

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900">Bias Analysis Heatmap</h3>
      <p className="mt-1 text-sm text-gray-500">
        Bias scores by AI system and demographic group (4/5ths rule: ratio &le; 1.25)
      </p>

      {isLoading ? (
        <div className="mt-4 animate-pulse">
          <div className="h-48 rounded bg-gray-100" />
        </div>
      ) : !biasSummary || biasSummary.entries.length === 0 ? (
        <div className="mt-6 py-8 text-center">
          <ChartBarIcon className="mx-auto h-8 w-8 text-gray-300" />
          <p className="mt-2 text-sm text-gray-500">
            No bias data available. Record metrics with demographic groups to populate this view.
          </p>
        </div>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="px-3 py-2 text-left font-medium text-gray-700">AI System</th>
                {biasSummary.groups.map((group) => (
                  <th key={group} className="px-3 py-2 text-center font-medium text-gray-700">
                    {group}
                  </th>
                ))}
                <th className="px-3 py-2 text-center font-medium text-gray-700">Disparity Ratio</th>
                <th className="px-3 py-2 text-center font-medium text-gray-700">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {biasSummary.systems.map((system) => {
                const disparityInfo = biasSummary.disparity_ratios[system.id];
                return (
                  <tr key={system.id} className="hover:bg-gray-50">
                    <td className="px-3 py-3 font-medium text-gray-900">{system.name}</td>
                    {biasSummary.groups.map((group) => {
                      const entry = heatmapGrid[`${system.id}::${group}`];
                      if (!entry) {
                        return (
                          <td key={group} className="px-3 py-3 text-center">
                            <span className="inline-flex h-8 w-16 items-center justify-center rounded bg-gray-100 text-xs text-gray-400">
                              N/A
                            </span>
                          </td>
                        );
                      }
                      return (
                        <td key={group} className="px-3 py-3 text-center">
                          <span
                            className={cn(
                              "inline-flex h-8 w-16 items-center justify-center rounded text-xs font-semibold",
                              entry.within_threshold
                                ? "bg-green-100 text-green-800"
                                : "bg-red-100 text-red-800"
                            )}
                          >
                            {entry.bias_score.toFixed(3)}
                          </span>
                        </td>
                      );
                    })}
                    <td className="px-3 py-3 text-center">
                      <span className="text-sm font-medium text-gray-700">
                        {disparityInfo ? disparityInfo.ratio.toFixed(3) : "N/A"}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-center">
                      {disparityInfo ? (
                        <span
                          className={cn(
                            "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
                            disparityInfo.compliant
                              ? "bg-green-100 text-green-800"
                              : "bg-red-100 text-red-800"
                          )}
                        >
                          {disparityInfo.compliant ? "Compliant" : "Non-Compliant"}
                        </span>
                      ) : (
                        <span className="text-xs text-gray-400">N/A</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {/* Legend */}
          <div className="mt-4 flex flex-wrap items-center gap-4 border-t border-gray-100 pt-3">
            <span className="text-xs text-gray-500">Cell Color:</span>
            <div className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-sm bg-green-100 ring-1 ring-green-200" />
              <span className="text-xs text-gray-600">Within Threshold</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-sm bg-red-100 ring-1 ring-red-200" />
              <span className="text-xs text-gray-600">Exceeds Threshold</span>
            </div>
            <span className="text-xs text-gray-400">|</span>
            <span className="text-xs text-gray-500">
              4/5ths Rule: Disparity ratio &le; 1.25 = Compliant
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// RecordMetricDialog Component
// =============================================================================

function RecordMetricDialog({
  projectId,
  aiSystems,
  onClose,
  onSuccess,
}: {
  projectId: string;
  aiSystems: AISystem[];
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState<Omit<CreateMetricPayload, "project_id">>({
    ai_system_id: aiSystems[0]?.id || "",
    metric_type: "accuracy",
    metric_name: "",
    metric_value: 0,
    threshold_min: null,
    threshold_max: null,
    unit: "%",
    demographic_group: null,
    measured_at: new Date().toISOString().slice(0, 16),
    notes: null,
  });

  const createMutation = useCreateMetric();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.ai_system_id || !formData.metric_name) {
      return;
    }

    try {
      await createMutation.mutateAsync({
        project_id: projectId,
        ...formData,
        measured_at: new Date(formData.measured_at).toISOString(),
      });
      onSuccess();
      onClose();
    } catch {
      // Error handled by mutation
    }
  };

  const updateField = <K extends keyof typeof formData>(key: K, value: (typeof formData)[K]) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 w-full max-w-lg rounded-lg bg-white shadow-xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between border-b border-gray-200 p-4">
          <h2 className="text-lg font-semibold text-gray-900">Record Performance Metric</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 p-4">
          {/* AI System */}
          <div>
            <label className="block text-sm font-medium text-gray-700">AI System *</label>
            <select
              value={formData.ai_system_id}
              onChange={(e) => updateField("ai_system_id", e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">Select AI System</option>
              {aiSystems.map((sys) => (
                <option key={sys.id} value={sys.id}>
                  {sys.name}
                </option>
              ))}
            </select>
          </div>

          {/* Metric Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Metric Type *</label>
            <select
              value={formData.metric_type}
              onChange={(e) => updateField("metric_type", e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              {METRIC_TYPES.map((mt) => (
                <option key={mt.value} value={mt.value}>
                  {mt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Metric Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Metric Name *</label>
            <input
              type="text"
              value={formData.metric_name}
              onChange={(e) => updateField("metric_name", e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Overall Accuracy - Production Model"
              required
            />
          </div>

          {/* Metric Value + Unit */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Value *</label>
              <input
                type="number"
                step="any"
                value={formData.metric_value}
                onChange={(e) => updateField("metric_value", parseFloat(e.target.value) || 0)}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Unit</label>
              <select
                value={formData.unit}
                onChange={(e) => updateField("unit", e.target.value)}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="%">% (Percent)</option>
                <option value="ratio">Ratio</option>
                <option value="ms">ms (Milliseconds)</option>
                <option value="s">s (Seconds)</option>
                <option value="score">Score</option>
                <option value="index">Index</option>
              </select>
            </div>
          </div>

          {/* Thresholds */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Threshold Min</label>
              <input
                type="number"
                step="any"
                value={formData.threshold_min ?? ""}
                onChange={(e) =>
                  updateField("threshold_min", e.target.value ? parseFloat(e.target.value) : null)
                }
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Optional"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Threshold Max</label>
              <input
                type="number"
                step="any"
                value={formData.threshold_max ?? ""}
                onChange={(e) =>
                  updateField("threshold_max", e.target.value ? parseFloat(e.target.value) : null)
                }
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Optional"
              />
            </div>
          </div>

          {/* Demographic Group */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Demographic Group</label>
            <input
              type="text"
              value={formData.demographic_group ?? ""}
              onChange={(e) => updateField("demographic_group", e.target.value || null)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., age_18-25, gender_female, ethnicity_asian"
            />
          </div>

          {/* Measured At */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Measured At *</label>
            <input
              type="datetime-local"
              value={formData.measured_at}
              onChange={(e) => updateField("measured_at", e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Notes</label>
            <textarea
              value={formData.notes ?? ""}
              onChange={(e) => updateField("notes", e.target.value || null)}
              rows={2}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Additional context or observations"
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
                  Recording...
                </>
              ) : (
                <>
                  <PlusIcon className="h-4 w-4" />
                  Record Metric
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
// MetricHistoryTable Component
// =============================================================================

function MetricHistoryTable({
  projectId,
  aiSystems,
  onRecordMetric,
}: {
  projectId: string;
  aiSystems: AISystem[];
  onRecordMetric: () => void;
}) {
  const [filterSystemId, setFilterSystemId] = useState<string>("");
  const [filterMetricType, setFilterMetricType] = useState<string>("");
  const [currentPage, setCurrentPage] = useState(0);

  const { data: metrics = [], isLoading } = useMetrics(
    projectId,
    filterSystemId || undefined,
    filterMetricType || undefined
  );

  const totalPages = Math.max(1, Math.ceil(metrics.length / ITEMS_PER_PAGE));
  const paginatedMetrics = useMemo(() => {
    const start = currentPage * ITEMS_PER_PAGE;
    return metrics.slice(start, start + ITEMS_PER_PAGE);
  }, [metrics, currentPage]);

  // Reset page when filters change
  const handleFilterSystem = useCallback((value: string) => {
    setFilterSystemId(value);
    setCurrentPage(0);
  }, []);

  const handleFilterType = useCallback((value: string) => {
    setFilterMetricType(value);
    setCurrentPage(0);
  }, []);

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Metric History</h3>
          <p className="mt-1 text-sm text-gray-500">{metrics.length} metric recordings</p>
        </div>
        <button
          onClick={onRecordMetric}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <PlusIcon className="h-4 w-4" />
          Record Metric
        </button>
      </div>

      {/* Filters */}
      <div className="mt-4 flex flex-wrap gap-3">
        <select
          value={filterSystemId}
          onChange={(e) => handleFilterSystem(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All AI Systems</option>
          {aiSystems.map((sys) => (
            <option key={sys.id} value={sys.id}>
              {sys.name}
            </option>
          ))}
        </select>
        <select
          value={filterMetricType}
          onChange={(e) => handleFilterType(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Metric Types</option>
          {METRIC_TYPES.map((mt) => (
            <option key={mt.value} value={mt.value}>
              {mt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="mt-4 animate-pulse space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-10 rounded bg-gray-100" />
          ))}
        </div>
      ) : metrics.length === 0 ? (
        <div className="mt-4 py-8 text-center">
          <ChartBarIcon className="mx-auto h-8 w-8 text-gray-300" />
          <p className="mt-2 text-sm text-gray-500">
            No metrics recorded yet. Click &ldquo;Record Metric&rdquo; to add the first measurement.
          </p>
        </div>
      ) : (
        <>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="px-3 py-2 text-left font-medium text-gray-700">Metric Name</th>
                  <th className="px-3 py-2 text-center font-medium text-gray-700">Type</th>
                  <th className="px-3 py-2 text-right font-medium text-gray-700">Value</th>
                  <th className="px-3 py-2 text-center font-medium text-gray-700">Threshold</th>
                  <th className="px-3 py-2 text-center font-medium text-gray-700">Status</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">AI System</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">Group</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {paginatedMetrics.map((metric) => {
                  const thresholdStr = [
                    metric.threshold_min != null ? `min: ${metric.threshold_min}` : null,
                    metric.threshold_max != null ? `max: ${metric.threshold_max}` : null,
                  ]
                    .filter(Boolean)
                    .join(", ");

                  return (
                    <tr key={metric.id} className="hover:bg-gray-50">
                      <td className="px-3 py-3">
                        <p className="font-medium text-gray-900 truncate max-w-[180px]">
                          {metric.metric_name}
                        </p>
                      </td>
                      <td className="px-3 py-3 text-center">
                        <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-700">
                          {METRIC_TYPES.find((mt) => mt.value === metric.metric_type)?.label ||
                            metric.metric_type}
                        </span>
                      </td>
                      <td className="px-3 py-3 text-right font-mono text-sm text-gray-900">
                        {formatMetricValue(metric.metric_value, metric.unit)}
                      </td>
                      <td className="px-3 py-3 text-center text-xs text-gray-500">
                        {thresholdStr || "None"}
                      </td>
                      <td className="px-3 py-3 text-center">
                        <span
                          className={cn(
                            "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
                            metric.within_threshold
                              ? "bg-green-100 text-green-700"
                              : "bg-red-100 text-red-700"
                          )}
                        >
                          {metric.within_threshold ? "Within" : "Exceeded"}
                        </span>
                      </td>
                      <td className="px-3 py-3 text-sm text-gray-700 truncate max-w-[120px]">
                        {metric.ai_system_name}
                      </td>
                      <td className="px-3 py-3 text-xs text-gray-500">
                        {metric.demographic_group || "-"}
                      </td>
                      <td className="px-3 py-3 text-xs text-gray-500">
                        {formatDate(metric.measured_at)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-4 flex items-center justify-between border-t border-gray-100 pt-3">
              <p className="text-xs text-gray-500">
                Showing {currentPage * ITEMS_PER_PAGE + 1} -{" "}
                {Math.min((currentPage + 1) * ITEMS_PER_PAGE, metrics.length)} of {metrics.length}
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
                  disabled={currentPage === 0}
                  className="inline-flex items-center rounded-lg border border-gray-300 px-2 py-1 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  <ChevronLeftIcon className="h-4 w-4" />
                </button>
                <span className="text-sm text-gray-600">
                  {currentPage + 1} / {totalPages}
                </span>
                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages - 1, p + 1))}
                  disabled={currentPage >= totalPages - 1}
                  className="inline-flex items-center rounded-lg border border-gray-300 px-2 py-1 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  <ChevronRightIcon className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </>
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

      {/* Summary Cards Skeleton */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <div className="h-4 w-24 rounded bg-gray-200" />
            <div className="mt-2 h-8 w-16 rounded bg-gray-200" />
            <div className="mt-2 h-3 w-32 rounded bg-gray-200" />
          </div>
        ))}
      </div>

      {/* Policy + Trend Skeleton */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <div className="h-6 w-32 rounded bg-gray-200" />
          <div className="mt-4 space-y-4">
            {[1, 2, 3, 4].map((i) => (
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
// Tab Navigation
// =============================================================================

type TabId = "overview" | "metrics" | "trends" | "bias";

const TABS: { id: TabId; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "metrics", label: "Metrics" },
  { id: "trends", label: "Trends" },
  { id: "bias", label: "Bias Analysis" },
];

// =============================================================================
// Main Page Component
// =============================================================================

export default function NistMeasurePage() {
  const searchParams = useSearchParams();
  const projectIdParam = searchParams.get("project");

  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(projectIdParam);
  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const [showRecordMetric, setShowRecordMetric] = useState(false);

  // Fetch projects for selector
  const { data: projects = [] } = useProjects();

  // Determine effective project ID
  const effectiveProjectId = selectedProjectId || projects[0]?.id;

  // Fetch dashboard data
  const {
    data: dashboard,
    isLoading: dashboardLoading,
    error: dashboardError,
  } = useMeasureDashboard(effectiveProjectId);

  // Fetch AI systems for dropdowns
  const { data: aiSystems = [] } = useAISystems(effectiveProjectId);

  // Mutations
  const evaluateMutation = useEvaluateMeasure();

  const handleEvaluate = useCallback(() => {
    if (effectiveProjectId) {
      evaluateMutation.mutate(effectiveProjectId);
    }
  }, [effectiveProjectId, evaluateMutation]);

  // Derived state
  const isLoading = dashboardLoading;
  const hasError = !!dashboardError;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">MEASURE Function Dashboard</h2>
          <p className="mt-1 text-sm text-gray-500">
            AI performance measurement, bias analysis, and threshold compliance tracking
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
          <ChartBarIcon className="mx-auto h-12 w-12 text-gray-300" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">Select a Project</h3>
          <p className="mt-2 text-sm text-gray-500">
            Choose a project from the dropdown to view NIST AI RMF MEASURE compliance status.
          </p>
        </div>
      )}

      {/* Error State */}
      {hasError && effectiveProjectId && (
        <ErrorAlert
          message={
            (dashboardError as Error)?.message ||
            "Failed to load MEASURE dashboard data. Please try again."
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
            <nav className="-mb-px flex space-x-8">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "whitespace-nowrap border-b-2 px-1 py-3 text-sm font-medium transition-colors",
                    activeTab === tab.id
                      ? "border-blue-500 text-blue-600"
                      : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
                  )}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Overview Tab */}
          {activeTab === "overview" && (
            <div className="space-y-6">
              {/* Score Card */}
              <MeasureScoreCard
                score={dashboard.overall_score}
                lastEvaluated={dashboard.last_evaluated_at}
                onEvaluate={handleEvaluate}
                isEvaluating={evaluateMutation.isPending}
              />

              {/* Summary Cards */}
              <MetricSummaryCards
                totalMetrics={dashboard.total_metrics}
                withinThreshold={dashboard.within_threshold_count}
                biasGroups={dashboard.bias_groups_count}
                disparityCompliant={dashboard.disparity_compliant}
                disparityNonCompliant={dashboard.disparity_non_compliant}
              />

              {/* Policy Status */}
              <PolicyStatusList policies={dashboard.policies} />
            </div>
          )}

          {/* Metrics Tab */}
          {activeTab === "metrics" && (
            <MetricHistoryTable
              projectId={effectiveProjectId}
              aiSystems={aiSystems}
              onRecordMetric={() => setShowRecordMetric(true)}
            />
          )}

          {/* Trends Tab */}
          {activeTab === "trends" && (
            <MetricTrendChart
              aiSystems={aiSystems}
              projectId={effectiveProjectId}
            />
          )}

          {/* Bias Analysis Tab */}
          {activeTab === "bias" && <BiasHeatmap projectId={effectiveProjectId} />}
        </>
      )}

      {/* Record Metric Dialog */}
      {showRecordMetric && effectiveProjectId && (
        <RecordMetricDialog
          projectId={effectiveProjectId}
          aiSystems={aiSystems}
          onClose={() => setShowRecordMetric(false)}
          onSuccess={() => setShowRecordMetric(false)}
        />
      )}
    </div>
  );
}
