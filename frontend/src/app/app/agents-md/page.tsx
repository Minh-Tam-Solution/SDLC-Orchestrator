/**
 * AGENTS.md Dashboard Page - SDLC Orchestrator
 *
 * @module frontend/src/app/app/agents-md/page
 * @description Multi-repo AGENTS.md management dashboard (TRUE MOAT)
 * @sdlc SDLC 5.1.3 Framework - Sprint 85 (AGENTS.md UI)
 * @status Sprint 85 - CTO APPROVED (January 20, 2026)
 */

"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import {
  useBulkRegenerateAgentsMd,
  useAgentsMdDashboardStats,
  useRegenerateAgentsMd,
} from "@/hooks/useAgentsMd";
import { getRepoStatus, getStatusLabel, formatRelativeTime } from "@/lib/types/agents-md";

// =============================================================================
// Icon Components
// =============================================================================

function DocumentTextIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
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

function ClockIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
  );
}

function QuestionMarkCircleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 5.25h.008v.008H12v-.008Z" />
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

function EyeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
    </svg>
  );
}

function MagnifyingGlassIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
    </svg>
  );
}

// =============================================================================
// Status Components
// =============================================================================

function StatusBadge({ status }: { status: "valid" | "invalid" | "outdated" | "missing" }) {
  const config = {
    valid: {
      bg: "bg-green-100",
      text: "text-green-800",
      icon: CheckCircleIcon,
    },
    invalid: {
      bg: "bg-red-100",
      text: "text-red-800",
      icon: ExclamationCircleIcon,
    },
    outdated: {
      bg: "bg-yellow-100",
      text: "text-yellow-800",
      icon: ClockIcon,
    },
    missing: {
      bg: "bg-gray-100",
      text: "text-gray-600",
      icon: QuestionMarkCircleIcon,
    },
  };

  const { bg, text, icon: Icon } = config[status];

  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${bg} ${text}`}>
      <Icon className="h-3.5 w-3.5" />
      {getStatusLabel(status)}
    </span>
  );
}

// =============================================================================
// Stats Cards
// =============================================================================

function StatsCards({ stats }: { stats: ReturnType<typeof useAgentsMdDashboardStats>["stats"] }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100">
            <DocumentTextIcon className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <p className="text-2xl font-semibold text-gray-900">{stats.totalRepos}</p>
            <p className="text-sm text-gray-500">Total Repos</p>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100">
            <CheckCircleIcon className="h-5 w-5 text-green-600" />
          </div>
          <div>
            <p className="text-2xl font-semibold text-gray-900">{stats.upToDate}</p>
            <p className="text-sm text-gray-500">Up to Date</p>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-yellow-100">
            <ClockIcon className="h-5 w-5 text-yellow-600" />
          </div>
          <div>
            <p className="text-2xl font-semibold text-gray-900">{stats.outdated}</p>
            <p className="text-sm text-gray-500">Outdated</p>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100">
            <ChartBarIcon className="h-5 w-5 text-purple-600" />
          </div>
          <div>
            <p className="text-2xl font-semibold text-gray-900">{stats.validRate.toFixed(1)}%</p>
            <p className="text-sm text-gray-500">Valid Rate</p>
          </div>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Repo Table
// =============================================================================

function RepoTable({
  repos,
  selectedRepos,
  onSelectRepo,
  onSelectAll,
  onRegenerate,
  regeneratingRepos,
}: {
  repos: ReturnType<typeof useAgentsMdDashboardStats>["repos"];
  selectedRepos: Set<string>;
  onSelectRepo: (id: string) => void;
  onSelectAll: () => void;
  onRegenerate: (id: string) => void;
  regeneratingRepos: Set<string>;
}) {
  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th scope="col" className="w-12 px-4 py-3">
              <input
                type="checkbox"
                checked={selectedRepos.size === repos.length && repos.length > 0}
                onChange={onSelectAll}
                className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </th>
            <th scope="col" className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Repository
            </th>
            <th scope="col" className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Status
            </th>
            <th scope="col" className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Last Updated
            </th>
            <th scope="col" className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Lines
            </th>
            <th scope="col" className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {repos.map((repo) => {
            const status = getRepoStatus(repo);
            const isRegenerating = regeneratingRepos.has(repo.id);

            return (
              <tr key={repo.id} className="hover:bg-gray-50">
                <td className="px-4 py-4">
                  <input
                    type="checkbox"
                    checked={selectedRepos.has(repo.id)}
                    onChange={() => onSelectRepo(repo.id)}
                    className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </td>
                <td className="px-4 py-4">
                  <div>
                    <p className="font-medium text-gray-900">{repo.project_name}</p>
                    <p className="text-sm text-gray-500">{repo.github_repo_full_name}</p>
                  </div>
                </td>
                <td className="px-4 py-4">
                  <StatusBadge status={status} />
                </td>
                <td className="px-4 py-4 text-sm text-gray-500">
                  {formatRelativeTime(repo.last_generated_at)}
                </td>
                <td className="px-4 py-4 text-sm text-gray-500">
                  {repo.line_count || "-"}
                </td>
                <td className="px-4 py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <Link
                      href={`/app/agents-md/${repo.id}`}
                      className="inline-flex items-center gap-1 rounded-md bg-white px-2.5 py-1.5 text-sm font-medium text-gray-700 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                    >
                      <EyeIcon className="h-4 w-4" />
                      View
                    </Link>
                    {repo.has_agents_md && (
                      <button
                        onClick={() => onRegenerate(repo.id)}
                        disabled={isRegenerating}
                        className="inline-flex items-center gap-1 rounded-md bg-blue-600 px-2.5 py-1.5 text-sm font-medium text-white shadow-sm hover:bg-blue-700 disabled:opacity-50"
                      >
                        <ArrowPathIcon className={`h-4 w-4 ${isRegenerating ? "animate-spin" : ""}`} />
                        {isRegenerating ? "..." : "Regen"}
                      </button>
                    )}
                    {!repo.has_agents_md && (
                      <button
                        onClick={() => onRegenerate(repo.id)}
                        disabled={isRegenerating}
                        className="inline-flex items-center gap-1 rounded-md bg-green-600 px-2.5 py-1.5 text-sm font-medium text-white shadow-sm hover:bg-green-700 disabled:opacity-50"
                      >
                        {isRegenerating ? "..." : "Generate"}
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// =============================================================================
// Main Page Component
// =============================================================================

export default function AgentsMdDashboard() {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "valid" | "invalid" | "outdated" | "missing">("all");
  const [selectedRepos, setSelectedRepos] = useState<Set<string>>(new Set());
  const [regeneratingRepos, setRegeneratingRepos] = useState<Set<string>>(new Set());

  const { stats, repos, isLoading, error } = useAgentsMdDashboardStats();
  const regenerateMutation = useRegenerateAgentsMd();
  const bulkRegenerateMutation = useBulkRegenerateAgentsMd();

  // Filter repos based on search and status
  const filteredRepos = useMemo(() => {
    return repos.filter((repo) => {
      const matchesSearch =
        repo.project_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        repo.github_repo_full_name.toLowerCase().includes(searchQuery.toLowerCase());

      const status = getRepoStatus(repo);
      const matchesStatus = statusFilter === "all" || status === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [repos, searchQuery, statusFilter]);

  const handleSelectRepo = (id: string) => {
    const newSelected = new Set(selectedRepos);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedRepos(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedRepos.size === filteredRepos.length) {
      setSelectedRepos(new Set());
    } else {
      setSelectedRepos(new Set(filteredRepos.map((r) => r.id)));
    }
  };

  const handleRegenerate = async (repoId: string) => {
    setRegeneratingRepos((prev) => new Set(prev).add(repoId));
    try {
      await regenerateMutation.mutateAsync({ repoId });
    } finally {
      setRegeneratingRepos((prev) => {
        const newSet = new Set(prev);
        newSet.delete(repoId);
        return newSet;
      });
    }
  };

  const handleBulkRegenerate = async () => {
    if (selectedRepos.size === 0) return;

    const repoIds = Array.from(selectedRepos);
    setRegeneratingRepos(new Set(repoIds));
    try {
      await bulkRegenerateMutation.mutateAsync({ repo_ids: repoIds });
      setSelectedRepos(new Set());
    } finally {
      setRegeneratingRepos(new Set());
    }
  };

  if (isLoading) {
    return <AgentsMdDashboardSkeleton />;
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
        <ExclamationCircleIcon className="mx-auto h-12 w-12 text-red-400" />
        <h3 className="mt-2 text-sm font-semibold text-red-800">Error loading AGENTS.md data</h3>
        <p className="mt-1 text-sm text-red-600">{(error as Error).message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AGENTS.md Management</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage AGENTS.md files across all your repositories (TRUE MOAT)
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/app/agents-md/analytics"
            className="inline-flex items-center gap-2 rounded-md bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
          >
            <ChartBarIcon className="h-4 w-4" />
            Analytics
          </Link>
          {selectedRepos.size > 0 && (
            <button
              onClick={handleBulkRegenerate}
              disabled={bulkRegenerateMutation.isPending}
              className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 disabled:opacity-50"
            >
              <ArrowPathIcon className={`h-4 w-4 ${bulkRegenerateMutation.isPending ? "animate-spin" : ""}`} />
              Regenerate ({selectedRepos.size})
            </button>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      <StatsCards stats={stats} />

      {/* Search and Filter */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search repositories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-4 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as typeof statusFilter)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="all">All Status</option>
          <option value="valid">Valid</option>
          <option value="outdated">Outdated</option>
          <option value="invalid">Invalid</option>
          <option value="missing">Missing</option>
        </select>
      </div>

      {/* Repos Table */}
      {filteredRepos.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-white p-12 text-center">
          <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-semibold text-gray-900">No repositories found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchQuery || statusFilter !== "all"
              ? "Try adjusting your search or filter"
              : "Connect a GitHub repository to get started"}
          </p>
        </div>
      ) : (
        <RepoTable
          repos={filteredRepos}
          selectedRepos={selectedRepos}
          onSelectRepo={handleSelectRepo}
          onSelectAll={handleSelectAll}
          onRegenerate={handleRegenerate}
          regeneratingRepos={regeneratingRepos}
        />
      )}
    </div>
  );
}

// =============================================================================
// Loading Skeleton
// =============================================================================

function AgentsMdDashboardSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div>
          <div className="h-8 w-64 rounded bg-gray-200 animate-pulse" />
          <div className="mt-2 h-4 w-96 rounded bg-gray-200 animate-pulse" />
        </div>
        <div className="h-10 w-32 rounded bg-gray-200 animate-pulse" />
      </div>

      {/* Stats skeleton */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="rounded-lg border border-gray-200 bg-white p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-gray-200 animate-pulse" />
              <div>
                <div className="h-8 w-16 rounded bg-gray-200 animate-pulse" />
                <div className="mt-1 h-4 w-24 rounded bg-gray-200 animate-pulse" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Search skeleton */}
      <div className="flex items-center gap-4">
        <div className="h-10 flex-1 rounded-lg bg-gray-200 animate-pulse" />
        <div className="h-10 w-32 rounded-lg bg-gray-200 animate-pulse" />
      </div>

      {/* Table skeleton */}
      <div className="rounded-lg border border-gray-200 bg-white">
        <div className="border-b border-gray-200 px-4 py-3">
          <div className="h-4 w-full rounded bg-gray-200 animate-pulse" />
        </div>
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="border-b border-gray-200 px-4 py-4">
            <div className="h-10 w-full rounded bg-gray-200 animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  );
}
