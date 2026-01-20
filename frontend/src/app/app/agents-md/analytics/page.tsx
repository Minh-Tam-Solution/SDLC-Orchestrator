/**
 * AGENTS.md Analytics Page - SDLC Orchestrator
 *
 * @module frontend/src/app/app/agents-md/analytics/page
 * @description Analytics dashboard for AGENTS.md engagement and metrics
 * @sdlc SDLC 5.1.3 Framework - Sprint 85 (AGENTS.md UI)
 * @status Sprint 85 - CTO APPROVED (January 20, 2026)
 */

"use client";

import Link from "next/link";
import {
  useAllAnalytics,
  useExportAnalytics,
  formatAnalyticsValue,
  getRateColor,
} from "@/hooks/useAgentsMdAnalytics";

// =============================================================================
// Icon Components
// =============================================================================

function ArrowLeftIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
    </svg>
  );
}

function ArrowDownTrayIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
    </svg>
  );
}

function ChartBarIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
    </svg>
  );
}

function DocumentTextIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
    </svg>
  );
}

function BoltIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m3.75 13.5 10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z" />
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

function ArrowPathIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
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

function ExclamationCircleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
    </svg>
  );
}

// =============================================================================
// Metric Card Component
// =============================================================================

function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  iconBg,
  iconColor,
  trend,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
  iconBg: string;
  iconColor: string;
  trend?: { direction: "up" | "down" | "stable"; value: string };
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex items-center justify-between">
        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${iconBg}`}>
          <Icon className={`h-5 w-5 ${iconColor}`} />
        </div>
        {trend && (
          <span
            className={`text-xs font-medium ${
              trend.direction === "up"
                ? "text-green-600"
                : trend.direction === "down"
                ? "text-red-600"
                : "text-gray-500"
            }`}
          >
            {trend.direction === "up" ? "↑" : trend.direction === "down" ? "↓" : "→"} {trend.value}
          </span>
        )}
      </div>
      <p className="mt-4 text-2xl font-semibold text-gray-900">{value}</p>
      <p className="text-sm text-gray-500">{title}</p>
      {subtitle && <p className="mt-1 text-xs text-gray-400">{subtitle}</p>}
    </div>
  );
}

// =============================================================================
// Progress Bar Component
// =============================================================================

function ProgressBar({ value, max, color }: { value: number; max: number; color: string }) {
  const percentage = max > 0 ? (value / max) * 100 : 0;
  const colorClasses: Record<string, string> = {
    green: "bg-green-500",
    yellow: "bg-yellow-500",
    orange: "bg-orange-500",
    red: "bg-red-500",
    blue: "bg-blue-500",
  };

  return (
    <div className="h-2 w-full rounded-full bg-gray-200">
      <div
        className={`h-2 rounded-full ${colorClasses[color] || "bg-blue-500"}`}
        style={{ width: `${Math.min(percentage, 100)}%` }}
      />
    </div>
  );
}

// =============================================================================
// Main Page Component
// =============================================================================

export default function AgentsMdAnalytics() {
  const { overlay, engagement, gates, security, agentsMd, isLoading, error, refetch } =
    useAllAnalytics();
  const exportMutation = useExportAnalytics();

  const handleExport = (format: "json" | "csv") => {
    exportMutation.mutate({ format });
  };

  if (isLoading) {
    return <AnalyticsSkeleton />;
  }

  if (error) {
    return (
      <div className="space-y-6">
        <Link
          href="/app/agents-md"
          className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
        >
          <ArrowLeftIcon className="h-4 w-4" />
          Back to AGENTS.md
        </Link>
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
          <ExclamationCircleIcon className="mx-auto h-12 w-12 text-red-400" />
          <h3 className="mt-2 text-sm font-semibold text-red-800">Error loading analytics</h3>
          <p className="mt-1 text-sm text-red-600">{(error as Error).message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link
            href="/app/agents-md"
            className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
          >
            <ArrowLeftIcon className="h-4 w-4" />
            Back to AGENTS.md
          </Link>
          <h1 className="mt-2 text-2xl font-bold text-gray-900">AGENTS.md Analytics</h1>
          <p className="mt-1 text-sm text-gray-500">
            Track engagement, quality metrics, and governance compliance
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleExport("csv")}
            disabled={exportMutation.isPending}
            className="inline-flex items-center gap-2 rounded-md bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:opacity-50"
          >
            <ArrowDownTrayIcon className="h-4 w-4" />
            Export CSV
          </button>
          <button
            onClick={() => refetch()}
            className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700"
          >
            <ArrowPathIcon className="h-4 w-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* AGENTS.md Metrics */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">AGENTS.md Coverage</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Total Repos"
            value={formatAnalyticsValue(agentsMd?.total_repos || 0, "count")}
            icon={DocumentTextIcon}
            iconBg="bg-blue-100"
            iconColor="text-blue-600"
          />
          <MetricCard
            title="With AGENTS.md"
            value={formatAnalyticsValue(agentsMd?.repos_with_agents_md || 0, "count")}
            subtitle={`${agentsMd?.coverage_rate?.toFixed(1) || 0}% coverage`}
            icon={CheckCircleIcon}
            iconBg="bg-green-100"
            iconColor="text-green-600"
          />
          <MetricCard
            title="Valid Files"
            value={formatAnalyticsValue(agentsMd?.valid_files || 0, "count")}
            icon={ShieldCheckIcon}
            iconBg="bg-purple-100"
            iconColor="text-purple-600"
          />
          <MetricCard
            title="Regenerations"
            value={formatAnalyticsValue(agentsMd?.regenerations_this_period || 0, "count")}
            subtitle="This period"
            icon={ArrowPathIcon}
            iconBg="bg-yellow-100"
            iconColor="text-yellow-600"
          />
        </div>
      </div>

      {/* Overlay Metrics */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Context Overlays (Dynamic Updates)</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Total Overlays"
            value={formatAnalyticsValue(overlay?.total_overlays || 0, "count")}
            icon={BoltIcon}
            iconBg="bg-orange-100"
            iconColor="text-orange-600"
          />
          <MetricCard
            title="Avg per Project"
            value={(overlay?.avg_overlays_per_project || 0).toFixed(1)}
            icon={ChartBarIcon}
            iconBg="bg-blue-100"
            iconColor="text-blue-600"
          />
          <MetricCard
            title="Strict Mode Activations"
            value={formatAnalyticsValue(overlay?.strict_mode_activations || 0, "count")}
            icon={ShieldCheckIcon}
            iconBg="bg-red-100"
            iconColor="text-red-600"
          />
          <MetricCard
            title="Active Projects"
            value={formatAnalyticsValue(engagement?.active_projects || 0, "count")}
            icon={DocumentTextIcon}
            iconBg="bg-green-100"
            iconColor="text-green-600"
          />
        </div>
      </div>

      {/* Gate Metrics */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quality Gates</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Total Gates"
            value={formatAnalyticsValue(gates?.total || 0, "count")}
            icon={ShieldCheckIcon}
            iconBg="bg-blue-100"
            iconColor="text-blue-600"
          />
          <MetricCard
            title="Passed"
            value={formatAnalyticsValue(gates?.passed || 0, "count")}
            icon={CheckCircleIcon}
            iconBg="bg-green-100"
            iconColor="text-green-600"
          />
          <MetricCard
            title="Failed"
            value={formatAnalyticsValue(gates?.failed || 0, "count")}
            icon={ExclamationCircleIcon}
            iconBg="bg-red-100"
            iconColor="text-red-600"
          />
          <MetricCard
            title="Pass Rate"
            value={formatAnalyticsValue(gates?.pass_rate || 0, "rate")}
            icon={ChartBarIcon}
            iconBg={`bg-${getRateColor(gates?.pass_rate || 0)}-100`}
            iconColor={`text-${getRateColor(gates?.pass_rate || 0)}-600`}
          />
        </div>
      </div>

      {/* Security Metrics */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Security Scans</h2>
        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Scans Passed</span>
                <span className="text-sm text-gray-500">
                  {security?.scans_passed || 0} / {security?.scans_total || 0}
                </span>
              </div>
              <ProgressBar
                value={security?.scans_passed || 0}
                max={security?.scans_total || 1}
                color={getRateColor(security?.pass_rate || 0)}
              />
              <p className="mt-2 text-sm text-gray-500">
                Pass rate: {security?.pass_rate?.toFixed(1) || 0}%
              </p>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Vulnerabilities Found</span>
                <span className="text-sm text-gray-500">
                  {security?.vulnerabilities_found || 0} total
                </span>
              </div>
              <div className="space-y-1">
                {security?.vulnerabilities_by_severity &&
                  Object.entries(security.vulnerabilities_by_severity).map(([severity, count]) => (
                    <div key={severity} className="flex items-center justify-between text-sm">
                      <span className="capitalize text-gray-600">{severity}</span>
                      <span className="font-medium text-gray-900">{count}</span>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Trigger Distribution */}
      {overlay?.overlays_by_trigger && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Overlay Triggers</h2>
          <div className="rounded-lg border border-gray-200 bg-white p-6">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
              {Object.entries(overlay.overlays_by_trigger).map(([trigger, count]) => (
                <div key={trigger} className="text-center">
                  <p className="text-2xl font-semibold text-gray-900">{count}</p>
                  <p className="text-sm text-gray-500 capitalize">{trigger.replace("_", " ")}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Loading Skeleton
// =============================================================================

function AnalyticsSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div>
        <div className="h-5 w-36 rounded bg-gray-200 animate-pulse" />
        <div className="mt-2 h-8 w-64 rounded bg-gray-200 animate-pulse" />
        <div className="mt-2 h-4 w-96 rounded bg-gray-200 animate-pulse" />
      </div>

      {/* Metrics sections skeleton */}
      {[1, 2, 3].map((section) => (
        <div key={section}>
          <div className="h-6 w-48 rounded bg-gray-200 animate-pulse mb-4" />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="rounded-lg border border-gray-200 bg-white p-4">
                <div className="h-10 w-10 rounded-lg bg-gray-200 animate-pulse" />
                <div className="mt-4 h-8 w-20 rounded bg-gray-200 animate-pulse" />
                <div className="mt-1 h-4 w-24 rounded bg-gray-200 animate-pulse" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
