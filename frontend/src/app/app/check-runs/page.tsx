/**
 * GitHub Check Runs Page - SDLC Orchestrator
 *
 * @module frontend/src/app/app/check-runs/page
 * @description GitHub Check Run management dashboard (P0 Blocker)
 * @sdlc SDLC 5.1.3 Framework - Sprint 86 (GitHub Check Run UI)
 * @status Sprint 86 - CTO APPROVED (January 20, 2026)
 */

"use client";

import { useState } from "react";
import Link from "next/link";
import { useCheckRunsDashboard, useRerunCheckRun } from "@/hooks/useGitHubChecks";
import {
  getModeMetadata,
  getConclusionMetadata,
  getStatusLabel,
  formatRelativeTime,
  formatDuration,
  getShortSha,
  canRerun,
} from "@/lib/types/github-checks";
import type { CheckRunListItem, CheckRunConclusion, CheckRunMode } from "@/lib/types/github-checks";

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

function ArrowPathIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
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

function ExternalLinkIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
    </svg>
  );
}

function FunnelIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 3c2.755 0 5.455.232 8.083.678.533.09.917.556.917 1.096v1.044a2.25 2.25 0 0 1-.659 1.591l-5.432 5.432a2.25 2.25 0 0 0-.659 1.591v2.927a2.25 2.25 0 0 1-1.244 2.013L9.75 21v-6.568a2.25 2.25 0 0 0-.659-1.591L3.659 7.409A2.25 2.25 0 0 1 3 5.818V4.774c0-.54.384-1.006.917-1.096A48.32 48.32 0 0 1 12 3Z" />
    </svg>
  );
}

// =============================================================================
// Stats Card Component
// =============================================================================

function StatsCard({
  title,
  value,
  subtitle,
  icon,
  color = "blue",
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color?: "blue" | "green" | "red" | "yellow" | "gray";
}) {
  const colorClasses = {
    blue: "bg-blue-50 text-blue-600",
    green: "bg-green-50 text-green-600",
    red: "bg-red-50 text-red-600",
    yellow: "bg-yellow-50 text-yellow-600",
    gray: "bg-gray-50 text-gray-600",
  };

  return (
    <div className="rounded-lg border bg-white p-4">
      <div className="flex items-center gap-3">
        <div className={`rounded-lg p-2 ${colorClasses[color]}`}>{icon}</div>
        <div>
          <p className="text-xs text-gray-500">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
          {subtitle && <p className="text-xs text-gray-400">{subtitle}</p>}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Check Run Row Component
// =============================================================================

function CheckRunRow({
  checkRun,
  onRerun,
  isRerunning,
}: {
  checkRun: CheckRunListItem;
  onRerun: (id: string) => void;
  isRerunning: boolean;
}) {
  const modeMetadata = getModeMetadata(checkRun.mode);
  const conclusionMetadata = getConclusionMetadata(checkRun.conclusion);

  return (
    <div className="rounded-lg border bg-white p-4 hover:border-gray-300 transition-colors">
      <div className="flex items-start justify-between gap-4">
        {/* Left: Status & Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            {/* Conclusion Icon */}
            <span className="text-lg" title={conclusionMetadata.label}>
              {conclusionMetadata.icon}
            </span>

            {/* Repository & PR */}
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-medium text-gray-900 truncate">
                {checkRun.repository_full_name}
              </span>
              {checkRun.pr_number && (
                <span className="text-sm text-gray-500">
                  #{checkRun.pr_number}
                </span>
              )}
            </div>

            {/* Mode Badge */}
            <span
              className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${modeMetadata.bgColor} ${modeMetadata.color}`}
            >
              {modeMetadata.icon} {modeMetadata.label}
            </span>

            {/* Bypassed Badge */}
            {checkRun.bypassed && (
              <span className="inline-flex items-center gap-1 rounded-full bg-orange-50 px-2 py-0.5 text-xs font-medium text-orange-600">
                Bypassed
              </span>
            )}
          </div>

          {/* PR Title */}
          {checkRun.pr_title && (
            <p className="mt-1 text-sm text-gray-600 truncate">
              {checkRun.pr_title}
            </p>
          )}

          {/* Meta Info */}
          <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
            <span>SHA: {getShortSha(checkRun.head_sha)}</span>
            <span>{getStatusLabel(checkRun.status)}</span>
            <span>{formatRelativeTime(checkRun.created_at)}</span>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          {/* Re-run Button */}
          {canRerun(checkRun) && (
            <button
              onClick={() => onRerun(checkRun.id)}
              disabled={isRerunning}
              className="inline-flex items-center gap-1 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              <ArrowPathIcon className={`h-4 w-4 ${isRerunning ? "animate-spin" : ""}`} />
              Re-run
            </button>
          )}

          {/* View on GitHub */}
          <a
            href={checkRun.html_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            <ExternalLinkIcon className="h-4 w-4" />
            GitHub
          </a>

          {/* Detail Link */}
          <Link
            href={`/app/check-runs/${checkRun.id}`}
            className="inline-flex items-center rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
          >
            Details
            <ChevronRightIcon className="ml-1 h-4 w-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Filter Panel Component
// =============================================================================

function FilterPanel({
  filters,
  onFilterChange,
}: {
  filters: {
    conclusion?: CheckRunConclusion;
    mode?: CheckRunMode;
  };
  onFilterChange: (key: string, value: string | undefined) => void;
}) {
  return (
    <div className="rounded-lg border bg-white p-4">
      <div className="flex items-center gap-2 mb-4">
        <FunnelIcon className="h-5 w-5 text-gray-500" />
        <h3 className="text-sm font-medium text-gray-900">Filters</h3>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Conclusion Filter */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Result
          </label>
          <select
            value={filters.conclusion || ""}
            onChange={(e) =>
              onFilterChange("conclusion", e.target.value || undefined)
            }
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="">All Results</option>
            <option value="success">Success</option>
            <option value="failure">Failed</option>
            <option value="neutral">Neutral</option>
            <option value="action_required">Action Required</option>
          </select>
        </div>

        {/* Mode Filter */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Mode
          </label>
          <select
            value={filters.mode || ""}
            onChange={(e) => onFilterChange("mode", e.target.value || undefined)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="">All Modes</option>
            <option value="advisory">Advisory</option>
            <option value="blocking">Blocking</option>
            <option value="strict">Strict</option>
          </select>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Main Page Component
// =============================================================================

export default function CheckRunsPage() {
  const [filters, setFilters] = useState<{
    conclusion?: CheckRunConclusion;
    mode?: CheckRunMode;
  }>({});
  const [showFilters, setShowFilters] = useState(false);

  const { checkRuns, totalCheckRuns, stats, isLoading, error, refetchAll } =
    useCheckRunsDashboard({
      ...filters,
      page_size: 20,
    });

  const rerunMutation = useRerunCheckRun();

  const handleFilterChange = (key: string, value: string | undefined) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleRerun = async (checkRunId: string) => {
    try {
      await rerunMutation.mutateAsync({ check_run_id: checkRunId });
    } catch (err) {
      console.error("Failed to re-run check:", err);
    }
  };

  if (isLoading) {
    return <CheckRunsLoading />;
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6">
        <h3 className="text-lg font-medium text-red-800">Error Loading Check Runs</h3>
        <p className="mt-2 text-sm text-red-600">
          {error instanceof Error ? error.message : "An error occurred"}
        </p>
        <button
          onClick={() => refetchAll()}
          className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Check Runs</h1>
          <p className="mt-1 text-sm text-gray-500">
            GitHub Check Runs for SDLC Gate Evaluation (P0 - Pre-Launch)
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium ${
              showFilters
                ? "border-blue-600 bg-blue-50 text-blue-600"
                : "border-gray-300 bg-white text-gray-700 hover:bg-gray-50"
            }`}
          >
            <FunnelIcon className="h-4 w-4" />
            Filters
          </button>
          <button
            onClick={() => refetchAll()}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            <ArrowPathIcon className="h-4 w-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Runs"
          value={stats?.total_runs ?? 0}
          subtitle="Last 7 days"
          icon={<ShieldCheckIcon className="h-5 w-5" />}
          color="blue"
        />
        <StatsCard
          title="Pass Rate"
          value={`${((stats?.pass_rate ?? 0) * 100).toFixed(1)}%`}
          subtitle={`${stats?.passed_runs ?? 0} passed`}
          icon={<span className="text-lg">✅</span>}
          color="green"
        />
        <StatsCard
          title="Failed"
          value={stats?.failed_runs ?? 0}
          subtitle="Requires attention"
          icon={<span className="text-lg">❌</span>}
          color="red"
        />
        <StatsCard
          title="Avg Duration"
          value={formatDuration(stats?.avg_duration_ms)}
          subtitle="Per check run"
          icon={<span className="text-lg">⏱️</span>}
          color="gray"
        />
      </div>

      {/* Enforcement Mode Stats */}
      <div className="rounded-lg border bg-gradient-to-r from-blue-50 to-indigo-50 p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Enforcement Modes</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-2xl font-semibold text-blue-600">
              {stats?.advisory_runs ?? 0}
            </p>
            <p className="text-xs text-gray-500">Advisory</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-semibold text-orange-600">
              {stats?.blocking_runs ?? 0}
            </p>
            <p className="text-xs text-gray-500">Blocking</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-semibold text-red-600">
              {stats?.strict_runs ?? 0}
            </p>
            <p className="text-xs text-gray-500">Strict</p>
          </div>
        </div>
        {stats?.bypassed_runs !== undefined && stats.bypassed_runs > 0 && (
          <p className="mt-3 text-xs text-orange-600 text-center">
            {stats.bypassed_runs} runs bypassed with label
          </p>
        )}
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <FilterPanel filters={filters} onFilterChange={handleFilterChange} />
      )}

      {/* Check Runs List */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Recent Check Runs
            <span className="ml-2 text-sm font-normal text-gray-500">
              ({totalCheckRuns} total)
            </span>
          </h2>
        </div>

        {checkRuns.length === 0 ? (
          <div className="rounded-lg border border-dashed bg-gray-50 p-8 text-center">
            <ShieldCheckIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">
              No Check Runs Yet
            </h3>
            <p className="mt-2 text-sm text-gray-500">
              Check Runs will appear here when PRs are opened on connected repositories.
            </p>
            <p className="mt-4 text-sm text-gray-500">
              Make sure your GitHub App is installed and the project is connected.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {checkRuns.map((checkRun) => (
              <CheckRunRow
                key={checkRun.id}
                checkRun={checkRun}
                onRerun={handleRerun}
                isRerunning={rerunMutation.isPending}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// Loading Skeleton
// =============================================================================

function CheckRunsLoading() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div className="flex items-start justify-between">
        <div>
          <div className="h-8 w-40 bg-gray-200 rounded animate-pulse" />
          <div className="mt-2 h-4 w-64 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="flex gap-2">
          <div className="h-10 w-24 bg-gray-200 rounded animate-pulse" />
          <div className="h-10 w-24 bg-gray-200 rounded animate-pulse" />
        </div>
      </div>

      {/* Stats skeleton */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-24 rounded-lg border bg-white p-4 animate-pulse">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-gray-200" />
              <div className="space-y-2">
                <div className="h-3 w-16 bg-gray-200 rounded" />
                <div className="h-6 w-12 bg-gray-200 rounded" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Mode stats skeleton */}
      <div className="h-24 rounded-lg bg-gray-100 animate-pulse" />

      {/* List skeleton */}
      <div>
        <div className="h-6 w-48 bg-gray-200 rounded animate-pulse mb-4" />
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="rounded-lg border bg-white p-4 animate-pulse">
              <div className="flex items-center gap-3">
                <div className="h-6 w-6 bg-gray-200 rounded-full" />
                <div className="flex-1 space-y-2">
                  <div className="h-5 w-48 bg-gray-200 rounded" />
                  <div className="h-4 w-32 bg-gray-100 rounded" />
                </div>
                <div className="flex gap-2">
                  <div className="h-8 w-20 bg-gray-200 rounded" />
                  <div className="h-8 w-20 bg-gray-200 rounded" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
