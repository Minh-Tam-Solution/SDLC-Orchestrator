/**
 * NIST AI RMF MANAGE Dashboard Page - SDLC Orchestrator
 *
 * @module frontend/src/app/app/compliance/nist/manage/page
 * @description Sprint 158 - NIST AI RMF MANAGE: Risk response management,
 *   incident tracking, deactivation criteria, and compliance scoring.
 * @sdlc SDLC 6.0.5 Universal Framework
 * @status Sprint 158 - NIST AI RMF MANAGE
 */

"use client";

import { useState, useMemo, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";
import { useProjects } from "@/hooks/useProjects";
import {
  useManageDashboard,
  useRiskResponses,
  useIncidents,
  useEvaluateManage,
  useCreateRiskResponse,
  useUpdateRiskResponse,
  useCreateIncident,
  useUpdateIncident,
  type ManageRiskResponse,
  type RiskResponseCreate,
  type ManageIncident,
  type IncidentCreate,
  type ManageDashboardResponse,
} from "@/hooks/useCompliance";
import { useComplianceRisks, useAISystems } from "@/hooks/useCompliance";
import type {
  PolicyEvaluationResult,
  ManageResponseType,
  ManageResponseStatus,
  ManageResponsePriority,
  ManageIncidentSeverity,
  ManageIncidentType,
  ManageIncidentStatus,
} from "@/lib/api";

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

function BellAlertIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0M3.124 7.5A8.969 8.969 0 0 1 5.292 3m13.416 0a8.969 8.969 0 0 1 2.168 4.5" />
    </svg>
  );
}

function ClockIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
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

function formatShortDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "N/A";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function daysAgo(dateStr: string): number {
  const d = new Date(dateStr);
  const now = new Date();
  return Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24));
}

// =============================================================================
// Status/Badge Configuration
// =============================================================================

const POLICY_STATUS_CONFIG: Record<
  "pass" | "fail" | "warning" | "not_evaluated",
  { label: string; color: string; icon: React.ComponentType<{ className?: string }> }
> = {
  pass: { label: "Pass", color: "bg-green-100 text-green-700", icon: CheckCircleIcon },
  fail: { label: "Fail", color: "bg-red-100 text-red-700", icon: XCircleIcon },
  warning: { label: "Warning", color: "bg-yellow-100 text-yellow-700", icon: ExclamationTriangleIcon },
  not_evaluated: { label: "Not Evaluated", color: "bg-gray-100 text-gray-500", icon: ShieldCheckIcon },
};

const SEVERITY_CONFIG: Record<ManageIncidentSeverity, { label: string; color: string }> = {
  critical: { label: "Critical", color: "bg-red-100 text-red-800" },
  high: { label: "High", color: "bg-orange-100 text-orange-800" },
  medium: { label: "Medium", color: "bg-yellow-100 text-yellow-800" },
  low: { label: "Low", color: "bg-green-100 text-green-800" },
};

const PRIORITY_CONFIG: Record<ManageResponsePriority, { label: string; color: string }> = {
  critical: { label: "Critical", color: "bg-red-100 text-red-800" },
  high: { label: "High", color: "bg-orange-100 text-orange-800" },
  medium: { label: "Medium", color: "bg-yellow-100 text-yellow-800" },
  low: { label: "Low", color: "bg-green-100 text-green-800" },
};

const RESPONSE_TYPE_CONFIG: Record<ManageResponseType, { label: string; color: string }> = {
  mitigate: { label: "Mitigate", color: "bg-blue-100 text-blue-700" },
  accept: { label: "Accept", color: "bg-gray-100 text-gray-700" },
  transfer: { label: "Transfer", color: "bg-purple-100 text-purple-700" },
  avoid: { label: "Avoid", color: "bg-red-100 text-red-700" },
};

const RESPONSE_STATUS_CONFIG: Record<ManageResponseStatus, { label: string; color: string }> = {
  planned: { label: "Planned", color: "bg-gray-100 text-gray-700" },
  in_progress: { label: "In Progress", color: "bg-blue-100 text-blue-700" },
  completed: { label: "Completed", color: "bg-green-100 text-green-700" },
  deferred: { label: "Deferred", color: "bg-yellow-100 text-yellow-700" },
};

const INCIDENT_STATUS_CONFIG: Record<ManageIncidentStatus, { label: string; color: string }> = {
  open: { label: "Open", color: "bg-red-100 text-red-700" },
  investigating: { label: "Investigating", color: "bg-orange-100 text-orange-700" },
  mitigating: { label: "Mitigating", color: "bg-yellow-100 text-yellow-700" },
  resolved: { label: "Resolved", color: "bg-green-100 text-green-700" },
  closed: { label: "Closed", color: "bg-gray-100 text-gray-500" },
};

const INCIDENT_TYPE_LABELS: Record<ManageIncidentType, string> = {
  performance_degradation: "Performance Degradation",
  bias_detected: "Bias Detected",
  security_breach: "Security Breach",
  availability: "Availability",
  data_quality: "Data Quality",
  compliance_violation: "Compliance Violation",
};

const SEVERITY_DOT_COLORS: Record<ManageIncidentSeverity, string> = {
  critical: "bg-red-500",
  high: "bg-orange-500",
  medium: "bg-yellow-500",
  low: "bg-green-500",
};

// =============================================================================
// ManageScoreCard Component
// =============================================================================

function ManageScoreCard({
  dashboard,
  onEvaluate,
  isEvaluating,
}: {
  dashboard: ManageDashboardResponse;
  onEvaluate: () => void;
  isEvaluating: boolean;
}) {
  const percentage = Math.round(dashboard.compliance_percentage);
  const circumference = 2 * Math.PI * 54;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const scoreColor = percentage >= 80 ? "text-green-600" : percentage >= 50 ? "text-yellow-600" : "text-red-600";
  const strokeColor = percentage >= 80 ? "#16a34a" : percentage >= 50 ? "#ca8a04" : "#dc2626";

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">MANAGE Compliance Score</h3>
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
              <span className="text-sm font-medium text-gray-900">MANAGE</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Policies</span>
              <span className="text-sm font-medium text-gray-900">
                {dashboard.policies_passed}/{dashboard.policies_total} Passed
              </span>
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

      {/* Summary Stats */}
      <div className="mt-6 grid grid-cols-2 gap-4 border-t border-gray-100 pt-4 sm:grid-cols-4">
        <div className="text-center">
          <p className="text-2xl font-bold text-gray-900">{dashboard.total_risk_responses}</p>
          <p className="text-xs text-gray-500">Risk Responses</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-green-600">{dashboard.completed_responses}</p>
          <p className="text-xs text-gray-500">Completed</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-gray-900">{dashboard.total_incidents}</p>
          <p className="text-xs text-gray-500">Total Incidents</p>
        </div>
        <div className="text-center">
          <p className={cn("text-2xl font-bold", dashboard.critical_incidents > 0 ? "text-red-600" : "text-gray-900")}>
            {dashboard.critical_incidents}
          </p>
          <p className="text-xs text-gray-500">Critical</p>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// PolicyStatusList Component
// =============================================================================

function PolicyStatusList({ policies }: { policies: PolicyEvaluationResult[] }) {
  const getPolicyStatus = (policy: PolicyEvaluationResult): "pass" | "fail" | "warning" | "not_evaluated" => {
    if (policy.allowed === true) return "pass";
    if (policy.allowed === false) return "fail";
    return "not_evaluated";
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900">Policy Status</h3>
      <p className="mt-1 text-sm text-gray-500">MANAGE function control assessment results</p>

      <div className="mt-4 divide-y divide-gray-200">
        {policies.map((policy) => {
          const status = getPolicyStatus(policy);
          const config = POLICY_STATUS_CONFIG[status];
          const StatusIcon = config.icon;
          return (
            <div key={policy.control_code} className="flex items-center justify-between py-3">
              <div className="flex items-start gap-3">
                <StatusIcon className={cn("mt-0.5 h-5 w-5 flex-shrink-0", {
                  "text-green-500": status === "pass",
                  "text-red-500": status === "fail",
                  "text-yellow-500": status === "warning",
                  "text-gray-400": status === "not_evaluated",
                })} />
                <div>
                  <p className="text-sm font-medium text-gray-900">{policy.title}</p>
                  <p className="text-xs text-gray-500">{policy.control_code}</p>
                  {policy.reason && !policy.allowed && (
                    <p className="mt-1 text-xs text-gray-600">{policy.reason}</p>
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
// RiskResponseTable Component
// =============================================================================

function RiskResponseTable({
  responses,
  onAddResponse,
}: {
  responses: ManageRiskResponse[];
  onAddResponse: () => void;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Risk Responses</h3>
          <p className="mt-1 text-sm text-gray-500">{responses.length} response plans tracked</p>
        </div>
        <button
          onClick={onAddResponse}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <PlusIcon className="h-4 w-4" />
          Add Response
        </button>
      </div>

      {responses.length > 0 ? (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="px-3 py-2 text-left font-medium text-gray-700">Description</th>
                <th className="px-3 py-2 text-center font-medium text-gray-700">Type</th>
                <th className="px-3 py-2 text-left font-medium text-gray-700">Assigned To</th>
                <th className="px-3 py-2 text-center font-medium text-gray-700">Priority</th>
                <th className="px-3 py-2 text-center font-medium text-gray-700">Status</th>
                <th className="px-3 py-2 text-left font-medium text-gray-700">Due Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {responses.map((resp) => {
                const typeConfig = RESPONSE_TYPE_CONFIG[resp.response_type];
                const priorityConfig = PRIORITY_CONFIG[resp.priority];
                const statusConfig = RESPONSE_STATUS_CONFIG[resp.status];
                return (
                  <tr key={resp.id} className="hover:bg-gray-50">
                    <td className="px-3 py-3">
                      <p className="font-medium text-gray-900 line-clamp-2">{resp.description}</p>
                      {resp.deactivation_criteria && (
                        <p className="mt-0.5 text-xs text-orange-600">Has deactivation criteria</p>
                      )}
                    </td>
                    <td className="px-3 py-3 text-center">
                      <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", typeConfig.color)}>
                        {typeConfig.label}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-sm text-gray-700">{resp.assigned_to || "Unassigned"}</td>
                    <td className="px-3 py-3 text-center">
                      <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", priorityConfig.color)}>
                        {priorityConfig.label}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-center">
                      <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", statusConfig.color)}>
                        {statusConfig.label}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-xs text-gray-500">{formatShortDate(resp.due_date)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="mt-4 py-8 text-center">
          <ShieldCheckIcon className="mx-auto h-8 w-8 text-gray-300" />
          <p className="mt-2 text-sm text-gray-500">No risk responses yet. Add a response plan to begin tracking mitigation efforts.</p>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// CreateRiskResponseDialog Component
// =============================================================================

function CreateRiskResponseDialog({
  projectId,
  onClose,
  onSuccess,
}: {
  projectId: string;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState<{
    risk_id: string;
    response_type: ManageResponseType;
    description: string;
    assigned_to: string;
    priority: ManageResponsePriority;
    due_date: string;
    resources_json: string;
    deactivation_conditions: string;
    deactivation_action: string;
  }>({
    risk_id: "",
    response_type: "mitigate",
    description: "",
    assigned_to: "",
    priority: "medium",
    due_date: "",
    resources_json: "",
    deactivation_conditions: "",
    deactivation_action: "",
  });

  const { data: risksData } = useComplianceRisks(projectId);
  const risks = useMemo(() => {
    if (!risksData) return [];
    if (Array.isArray(risksData)) return risksData;
    if (risksData && typeof risksData === "object" && "items" in risksData) {
      return (risksData as { items: Array<{ id: string; title: string; risk_code: string }> }).items;
    }
    return [];
  }, [risksData]);

  const createMutation = useCreateRiskResponse();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.risk_id || !formData.description) {
      return;
    }

    const payload: RiskResponseCreate = {
      project_id: projectId,
      risk_id: formData.risk_id,
      response_type: formData.response_type,
      description: formData.description,
    };

    if (formData.assigned_to.trim()) {
      payload.assigned_to = formData.assigned_to.trim();
    }
    payload.priority = formData.priority;
    if (formData.due_date) {
      payload.due_date = formData.due_date;
    }

    if (formData.resources_json.trim()) {
      try {
        const parsed = JSON.parse(formData.resources_json);
        if (Array.isArray(parsed)) {
          payload.resources_allocated = parsed;
        }
      } catch {
        // Invalid JSON ignored, skip resources
      }
    }

    if (formData.deactivation_conditions.trim() && formData.deactivation_action.trim()) {
      payload.deactivation_criteria = {
        conditions: formData.deactivation_conditions.split("\n").filter((c) => c.trim()),
        action: formData.deactivation_action.trim(),
      };
    }

    try {
      await createMutation.mutateAsync(payload);
      onSuccess();
      onClose();
    } catch {
      // Error handled by mutation state
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-lg bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-200 p-4">
          <h2 className="text-lg font-semibold text-gray-900">Add Risk Response</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 p-4">
          {/* Risk Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Risk *</label>
            <select
              value={formData.risk_id}
              onChange={(e) => setFormData((prev) => ({ ...prev, risk_id: e.target.value }))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">Select a risk</option>
              {risks.map((risk) => (
                <option key={risk.id} value={risk.id}>
                  {risk.risk_code} - {risk.title}
                </option>
              ))}
            </select>
          </div>

          {/* Response Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Response Type *</label>
            <select
              value={formData.response_type}
              onChange={(e) => setFormData((prev) => ({ ...prev, response_type: e.target.value as ManageResponseType }))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="mitigate">Mitigate</option>
              <option value="accept">Accept</option>
              <option value="transfer">Transfer</option>
              <option value="avoid">Avoid</option>
            </select>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Description *</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
              rows={3}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Describe the risk response plan and actions"
              required
            />
          </div>

          {/* Assigned To */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Assigned To</label>
            <input
              type="text"
              value={formData.assigned_to}
              onChange={(e) => setFormData((prev) => ({ ...prev, assigned_to: e.target.value }))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Person or team responsible"
            />
          </div>

          {/* Priority */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Priority</label>
            <select
              value={formData.priority}
              onChange={(e) => setFormData((prev) => ({ ...prev, priority: e.target.value as ManageResponsePriority }))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          {/* Due Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Due Date</label>
            <input
              type="date"
              value={formData.due_date}
              onChange={(e) => setFormData((prev) => ({ ...prev, due_date: e.target.value }))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Resources (JSON) */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Resources (JSON Array)
            </label>
            <textarea
              value={formData.resources_json}
              onChange={(e) => setFormData((prev) => ({ ...prev, resources_json: e.target.value }))}
              rows={2}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder='[{"type": "personnel", "description": "Security analyst", "budget": 5000}]'
            />
            <p className="mt-1 text-xs text-gray-400">Optional. Format: [{'"type"'}, {'"description"'}, {'"budget"'}]</p>
          </div>

          {/* Deactivation Criteria */}
          <div className="rounded-lg border border-orange-200 bg-orange-50 p-3">
            <p className="text-sm font-medium text-orange-800">Deactivation Criteria (MANAGE-2.4)</p>
            <div className="mt-2 space-y-2">
              <div>
                <label className="block text-xs font-medium text-gray-700">Conditions (one per line)</label>
                <textarea
                  value={formData.deactivation_conditions}
                  onChange={(e) => setFormData((prev) => ({ ...prev, deactivation_conditions: e.target.value }))}
                  rows={2}
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder={"Risk score exceeds threshold\nNo remediation within 30 days"}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700">Action</label>
                <input
                  type="text"
                  value={formData.deactivation_action}
                  onChange={(e) => setFormData((prev) => ({ ...prev, deactivation_action: e.target.value }))}
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Deactivate AI system and escalate to CTO"
                />
              </div>
            </div>
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
                  Add Response
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
// IncidentTable Component
// =============================================================================

function IncidentTable({
  incidents,
  onReportIncident,
}: {
  incidents: ManageIncident[];
  onReportIncident: () => void;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Incidents</h3>
          <p className="mt-1 text-sm text-gray-500">{incidents.length} incidents recorded</p>
        </div>
        <button
          onClick={onReportIncident}
          className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
        >
          <BellAlertIcon className="h-4 w-4" />
          Report Incident
        </button>
      </div>

      {incidents.length > 0 ? (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="px-3 py-2 text-left font-medium text-gray-700">Title</th>
                <th className="px-3 py-2 text-left font-medium text-gray-700">AI System</th>
                <th className="px-3 py-2 text-center font-medium text-gray-700">Severity</th>
                <th className="px-3 py-2 text-center font-medium text-gray-700">Type</th>
                <th className="px-3 py-2 text-center font-medium text-gray-700">Status</th>
                <th className="px-3 py-2 text-left font-medium text-gray-700">Occurred At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {incidents.map((incident) => {
                const severityConfig = SEVERITY_CONFIG[incident.severity];
                const statusConfig = INCIDENT_STATUS_CONFIG[incident.status];
                const typeLabel = INCIDENT_TYPE_LABELS[incident.incident_type] || incident.incident_type;
                return (
                  <tr key={incident.id} className="hover:bg-gray-50">
                    <td className="px-3 py-3">
                      <div>
                        <p className="font-medium text-gray-900">{incident.title}</p>
                        {incident.description && (
                          <p className="mt-0.5 text-xs text-gray-500 line-clamp-1">{incident.description}</p>
                        )}
                      </div>
                    </td>
                    <td className="px-3 py-3 text-sm text-gray-700 truncate max-w-[120px]">
                      {incident.ai_system_id.slice(0, 8)}...
                    </td>
                    <td className="px-3 py-3 text-center">
                      <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", severityConfig.color)}>
                        {severityConfig.label}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-center">
                      <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-700">
                        {typeLabel}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-center">
                      <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", statusConfig.color)}>
                        {statusConfig.label}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-xs text-gray-500">{formatDate(incident.occurred_at)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="mt-4 py-8 text-center">
          <BellAlertIcon className="mx-auto h-8 w-8 text-gray-300" />
          <p className="mt-2 text-sm text-gray-500">No incidents reported. Report an incident when AI system issues are detected.</p>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// ReportIncidentDialog Component
// =============================================================================

function ReportIncidentDialog({
  projectId,
  onClose,
  onSuccess,
}: {
  projectId: string;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState<{
    ai_system_id: string;
    title: string;
    description: string;
    severity: ManageIncidentSeverity;
    incident_type: ManageIncidentType;
    occurred_at: string;
  }>({
    ai_system_id: "",
    title: "",
    description: "",
    severity: "medium",
    incident_type: "performance_degradation",
    occurred_at: new Date().toISOString().slice(0, 16),
  });

  const { data: systemsData } = useAISystems(projectId);
  const systems = useMemo(() => {
    if (!systemsData) return [];
    if (Array.isArray(systemsData)) return systemsData;
    if (systemsData && typeof systemsData === "object" && "items" in systemsData) {
      return (systemsData as { items: Array<{ id: string; name: string }> }).items;
    }
    return [];
  }, [systemsData]);

  const createMutation = useCreateIncident();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.ai_system_id || !formData.title || !formData.occurred_at) {
      return;
    }

    const payload: IncidentCreate = {
      project_id: projectId,
      ai_system_id: formData.ai_system_id,
      title: formData.title,
      severity: formData.severity,
      incident_type: formData.incident_type,
      occurred_at: new Date(formData.occurred_at).toISOString(),
    };

    if (formData.description.trim()) {
      payload.description = formData.description.trim();
    }

    try {
      await createMutation.mutateAsync(payload);
      onSuccess();
      onClose();
    } catch {
      // Error handled by mutation state
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 w-full max-w-lg rounded-lg bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-200 p-4">
          <h2 className="text-lg font-semibold text-gray-900">Report Incident</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 p-4">
          {/* AI System Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700">AI System *</label>
            <select
              value={formData.ai_system_id}
              onChange={(e) => setFormData((prev) => ({ ...prev, ai_system_id: e.target.value }))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">Select an AI system</option>
              {systems.map((sys) => (
                <option key={sys.id} value={sys.id}>
                  {sys.name}
                </option>
              ))}
            </select>
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Title *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData((prev) => ({ ...prev, title: e.target.value }))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Brief title of the incident"
              required
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
              rows={3}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Detailed description of the incident, including root cause if known"
            />
          </div>

          {/* Severity */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Severity *</label>
            <select
              value={formData.severity}
              onChange={(e) => setFormData((prev) => ({ ...prev, severity: e.target.value as ManageIncidentSeverity }))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          {/* Incident Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Incident Type *</label>
            <select
              value={formData.incident_type}
              onChange={(e) => setFormData((prev) => ({ ...prev, incident_type: e.target.value as ManageIncidentType }))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="performance_degradation">Performance Degradation</option>
              <option value="bias_detected">Bias Detected</option>
              <option value="security_breach">Security Breach</option>
              <option value="availability">Availability</option>
              <option value="data_quality">Data Quality</option>
              <option value="compliance_violation">Compliance Violation</option>
            </select>
          </div>

          {/* Occurred At */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Occurred At *</label>
            <input
              type="datetime-local"
              value={formData.occurred_at}
              onChange={(e) => setFormData((prev) => ({ ...prev, occurred_at: e.target.value }))}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
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
              className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
            >
              {createMutation.isPending ? (
                <>
                  <ArrowPathIcon className="h-4 w-4 animate-spin" />
                  Reporting...
                </>
              ) : (
                <>
                  <BellAlertIcon className="h-4 w-4" />
                  Report Incident
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
// IncidentTimeline Component
// =============================================================================

function IncidentTimeline({ incidents }: { incidents: ManageIncident[] }) {
  const recentIncidents = useMemo(() => {
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

    return incidents
      .filter((inc) => new Date(inc.occurred_at) >= thirtyDaysAgo)
      .sort((a, b) => new Date(b.occurred_at).getTime() - new Date(a.occurred_at).getTime());
  }, [incidents]);

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-center gap-2">
        <ClockIcon className="h-5 w-5 text-gray-500" />
        <h3 className="text-lg font-semibold text-gray-900">Incident Timeline</h3>
      </div>
      <p className="mt-1 text-sm text-gray-500">Last 30 days of reported incidents</p>

      {recentIncidents.length > 0 ? (
        <div className="mt-4">
          <div className="relative">
            {/* Vertical line */}
            <div className="absolute left-3 top-2 h-[calc(100%-16px)] w-0.5 bg-gray-200" />

            <div className="space-y-4">
              {recentIncidents.map((incident) => {
                const dotColor = SEVERITY_DOT_COLORS[incident.severity];
                const statusConfig = INCIDENT_STATUS_CONFIG[incident.status];
                const days = daysAgo(incident.occurred_at);
                const daysLabel = days === 0 ? "Today" : days === 1 ? "1 day ago" : `${days} days ago`;

                return (
                  <div key={incident.id} className="relative flex items-start gap-4 pl-8">
                    {/* Severity dot */}
                    <div className={cn(
                      "absolute left-1.5 top-1.5 h-3 w-3 rounded-full ring-2 ring-white",
                      dotColor
                    )} />

                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-gray-900 truncate">{incident.title}</p>
                        <span className={cn(
                          "inline-flex flex-shrink-0 items-center rounded-full px-2 py-0.5 text-xs font-medium",
                          statusConfig.color
                        )}>
                          {statusConfig.label}
                        </span>
                      </div>
                      <div className="mt-0.5 flex items-center gap-2">
                        <span className={cn(
                          "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                          SEVERITY_CONFIG[incident.severity].color
                        )}>
                          {SEVERITY_CONFIG[incident.severity].label}
                        </span>
                        <span className="text-xs text-gray-400">{daysLabel}</span>
                        <span className="text-xs text-gray-400">{formatShortDate(incident.occurred_at)}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      ) : (
        <div className="mt-4 py-8 text-center">
          <ClockIcon className="mx-auto h-8 w-8 text-gray-300" />
          <p className="mt-2 text-sm text-gray-500">No incidents in the last 30 days.</p>
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

      {/* Policy Status Skeleton */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="h-6 w-32 rounded bg-gray-200" />
        <div className="mt-4 space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-12 rounded bg-gray-100" />
          ))}
        </div>
      </div>

      {/* Tables Skeleton */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="h-6 w-40 rounded bg-gray-200" />
        <div className="mt-4 h-48 rounded bg-gray-100" />
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="h-6 w-32 rounded bg-gray-200" />
        <div className="mt-4 h-48 rounded bg-gray-100" />
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

export default function ManageDashboardPage() {
  const searchParams = useSearchParams();
  const projectIdParam = searchParams.get("project");

  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(projectIdParam);
  const [showCreateResponse, setShowCreateResponse] = useState(false);
  const [showReportIncident, setShowReportIncident] = useState(false);

  // Fetch projects for selector
  const { data: projects = [] } = useProjects();

  // Determine effective project ID
  const effectiveProjectId = selectedProjectId || projects[0]?.id;

  // Fetch dashboard data
  const {
    data: dashboard,
    isLoading: dashboardLoading,
    error: dashboardError,
  } = useManageDashboard(effectiveProjectId);

  const {
    data: responsesData,
    isLoading: responsesLoading,
    error: responsesError,
  } = useRiskResponses(effectiveProjectId);

  const {
    data: incidentsData,
    isLoading: incidentsLoading,
    error: incidentsError,
  } = useIncidents(effectiveProjectId);

  // Extract items arrays from paginated responses
  const responses: ManageRiskResponse[] = useMemo(() => {
    if (!responsesData) return [];
    if (Array.isArray(responsesData)) return responsesData;
    if (responsesData && typeof responsesData === "object" && "items" in responsesData) {
      return (responsesData as { items: ManageRiskResponse[] }).items;
    }
    return [];
  }, [responsesData]);

  const incidents: ManageIncident[] = useMemo(() => {
    if (!incidentsData) return [];
    if (Array.isArray(incidentsData)) return incidentsData;
    if (incidentsData && typeof incidentsData === "object" && "items" in incidentsData) {
      return (incidentsData as { items: ManageIncident[] }).items;
    }
    return [];
  }, [incidentsData]);

  // Mutations
  const evaluateMutation = useEvaluateManage();

  const handleEvaluate = useCallback(() => {
    if (effectiveProjectId) {
      evaluateMutation.mutate(effectiveProjectId);
    }
  }, [effectiveProjectId, evaluateMutation]);

  // Derived state
  const isLoading = dashboardLoading || responsesLoading || incidentsLoading;
  const hasError = dashboardError || responsesError || incidentsError;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">MANAGE Function Dashboard</h2>
          <p className="mt-1 text-sm text-gray-500">
            Risk response management, incident tracking, and deactivation criteria
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
            Choose a project from the dropdown to view NIST AI RMF MANAGE compliance status.
          </p>
        </div>
      )}

      {/* Error State */}
      {hasError && effectiveProjectId && (
        <ErrorAlert
          message={
            (dashboardError as Error)?.message ||
            (responsesError as Error)?.message ||
            (incidentsError as Error)?.message ||
            "Failed to load MANAGE dashboard data. Please try again."
          }
        />
      )}

      {/* Loading State */}
      {isLoading && effectiveProjectId && !hasError && <DashboardSkeleton />}

      {/* Dashboard Content */}
      {!isLoading && !hasError && effectiveProjectId && dashboard && (
        <>
          {/* Score Card */}
          <ManageScoreCard
            dashboard={dashboard}
            onEvaluate={handleEvaluate}
            isEvaluating={evaluateMutation.isPending}
          />

          {/* Policy Status List */}
          <PolicyStatusList policies={dashboard.policy_results || []} />

          {/* Risk Response Section */}
          <RiskResponseTable
            responses={responses}
            onAddResponse={() => setShowCreateResponse(true)}
          />

          {/* Incident Section */}
          <IncidentTable
            incidents={incidents}
            onReportIncident={() => setShowReportIncident(true)}
          />

          {/* Incident Timeline */}
          <IncidentTimeline incidents={incidents} />
        </>
      )}

      {/* Create Risk Response Dialog */}
      {showCreateResponse && effectiveProjectId && (
        <CreateRiskResponseDialog
          projectId={effectiveProjectId}
          onClose={() => setShowCreateResponse(false)}
          onSuccess={() => setShowCreateResponse(false)}
        />
      )}

      {/* Report Incident Dialog */}
      {showReportIncident && effectiveProjectId && (
        <ReportIncidentDialog
          projectId={effectiveProjectId}
          onClose={() => setShowReportIncident(false)}
          onSuccess={() => setShowReportIncident(false)}
        />
      )}
    </div>
  );
}
