/**
 * AGENTS.md Repository Detail Page - SDLC Orchestrator
 *
 * @module frontend/src/app/app/agents-md/[repoId]/page
 * @description Single repo AGENTS.md editor with dynamic context (TRUE MOAT)
 * @sdlc SDLC 5.1.3 Framework - Sprint 85 (AGENTS.md UI)
 * @status Sprint 85 - CTO APPROVED (January 20, 2026)
 */

"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import {
  useAgentsMdRepoWithContext,
  useRegenerateAgentsMd,
} from "@/hooks/useAgentsMd";
import { useContextAnalysis } from "@/hooks/useContextOverlay";
import {
  getRepoStatus,
  getStatusLabel,
  formatRelativeTime,
} from "@/lib/types/agents-md";

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

function ExclamationTriangleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
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

function ClockIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
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

function DocumentTextIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
    </svg>
  );
}

// =============================================================================
// Status Badge
// =============================================================================

function StatusBadge({ status }: { status: "valid" | "invalid" | "outdated" | "missing" }) {
  const config = {
    valid: { bg: "bg-green-100", text: "text-green-800", icon: "✅" },
    invalid: { bg: "bg-red-100", text: "text-red-800", icon: "❌" },
    outdated: { bg: "bg-yellow-100", text: "text-yellow-800", icon: "⚠️" },
    missing: { bg: "bg-gray-100", text: "text-gray-600", icon: "❓" },
  };

  const { bg, text, icon } = config[status];

  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${bg} ${text}`}>
      {icon} {getStatusLabel(status)}
    </span>
  );
}

// =============================================================================
// Context Overlay Panel
// =============================================================================

function ContextOverlayPanel({ context }: { context: ReturnType<typeof useContextAnalysis> }) {
  if (!context.hasConstraints && !context.sprintInfo && !context.gateInfo) {
    return (
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-center">
        <p className="text-sm text-gray-500">No dynamic context available</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Strict Mode Warning */}
      {context.isStrictMode && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <div className="flex items-center gap-2">
            <ShieldCheckIcon className="h-5 w-5 text-red-600" />
            <span className="font-semibold text-red-800">STRICT MODE</span>
          </div>
          <p className="mt-1 text-sm text-red-700">
            Post-G3 mode active. Only bug fixes allowed, no new features.
          </p>
        </div>
      )}

      {/* Gate Status */}
      {context.gateInfo && (
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h4 className="flex items-center gap-2 font-medium text-gray-900">
            <CheckCircleIcon className="h-5 w-5 text-blue-600" />
            Current Gate
          </h4>
          <div className="mt-2 flex items-center gap-2">
            <span className="text-lg font-semibold">{context.gateInfo.name}</span>
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                context.gateInfo.status === "PASSED"
                  ? "bg-green-100 text-green-800"
                  : context.gateInfo.status === "FAILED"
                  ? "bg-red-100 text-red-800"
                  : "bg-yellow-100 text-yellow-800"
              }`}
            >
              {context.gateInfo.status}
            </span>
          </div>
        </div>
      )}

      {/* Sprint Info */}
      {context.sprintInfo && (
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h4 className="flex items-center gap-2 font-medium text-gray-900">
            <BoltIcon className="h-5 w-5 text-purple-600" />
            Current Sprint
          </h4>
          <p className="mt-2 text-lg font-semibold">
            Sprint {context.sprintInfo.number}
            {context.sprintInfo.name && ` - ${context.sprintInfo.name}`}
          </p>
          {context.sprintInfo.goal && (
            <p className="mt-1 text-sm text-gray-600">{context.sprintInfo.goal}</p>
          )}
        </div>
      )}

      {/* Constraints */}
      {context.hasConstraints && (
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h4 className="flex items-center gap-2 font-medium text-gray-900">
            <ExclamationTriangleIcon className="h-5 w-5 text-orange-600" />
            Constraints ({context.criticalConstraints.length + context.highConstraints.length + context.mediumConstraints.length + context.lowConstraints.length})
          </h4>
          <ul className="mt-2 space-y-2">
            {context.criticalConstraints.map((c, i) => (
              <li key={`critical-${i}`} className="flex items-start gap-2 text-sm">
                <span className="mt-0.5 h-2 w-2 rounded-full bg-red-500" />
                <span className="text-gray-700">{c.message}</span>
              </li>
            ))}
            {context.highConstraints.map((c, i) => (
              <li key={`high-${i}`} className="flex items-start gap-2 text-sm">
                <span className="mt-0.5 h-2 w-2 rounded-full bg-orange-500" />
                <span className="text-gray-700">{c.message}</span>
              </li>
            ))}
            {context.mediumConstraints.map((c, i) => (
              <li key={`medium-${i}`} className="flex items-start gap-2 text-sm">
                <span className="mt-0.5 h-2 w-2 rounded-full bg-yellow-500" />
                <span className="text-gray-700">{c.message}</span>
              </li>
            ))}
            {context.lowConstraints.slice(0, 3).map((c, i) => (
              <li key={`low-${i}`} className="flex items-start gap-2 text-sm">
                <span className="mt-0.5 h-2 w-2 rounded-full bg-gray-400" />
                <span className="text-gray-700">{c.message}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Known Issues */}
      {context.hasKnownIssues && (
        <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
          <h4 className="font-medium text-yellow-800">Known Issues</h4>
          <p className="mt-1 text-sm text-yellow-700">
            There are known issues that may affect development.
          </p>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Version History
// =============================================================================

function VersionHistory({ versions }: { versions: Array<{ id: string; version_number: number; generated_at: string; change_summary?: string }> }) {
  if (!versions || versions.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-center">
        <p className="text-sm text-gray-500">No version history available</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      <div className="border-b border-gray-200 px-4 py-3">
        <h3 className="font-medium text-gray-900">Version History</h3>
      </div>
      <ul className="divide-y divide-gray-200">
        {versions.slice(0, 5).map((version, index) => (
          <li key={version.id} className="flex items-center justify-between px-4 py-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-900">v{version.version_number}</span>
                {index === 0 && (
                  <span className="rounded bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-800">
                    current
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-500">
                {version.change_summary || formatRelativeTime(version.generated_at)}
              </p>
            </div>
            <span className="text-xs text-gray-400">
              {new Date(version.generated_at).toLocaleDateString()}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

// =============================================================================
// AGENTS.md Content Viewer
// =============================================================================

function AgentsMdContentViewer({ content }: { content: string }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      <div className="border-b border-gray-200 px-4 py-3">
        <h3 className="flex items-center gap-2 font-medium text-gray-900">
          <DocumentTextIcon className="h-5 w-5 text-gray-400" />
          AGENTS.md Content
        </h3>
      </div>
      <div className="max-h-[600px] overflow-auto">
        <pre className="p-4 text-sm leading-relaxed text-gray-800">
          <code>{content}</code>
        </pre>
      </div>
    </div>
  );
}

// =============================================================================
// Main Page Component
// =============================================================================

export default function AgentsMdRepoDetail() {
  const params = useParams();
  const repoId = params.repoId as string;

  const { repo, context, isLoading, error } = useAgentsMdRepoWithContext(repoId);
  const regenerateMutation = useRegenerateAgentsMd();
  const contextAnalysis = useContextAnalysis(context);

  const handleRegenerate = async () => {
    await regenerateMutation.mutateAsync({ repoId });
  };

  if (isLoading) {
    return <AgentsMdRepoDetailSkeleton />;
  }

  if (error || !repo) {
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
          <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-400" />
          <h3 className="mt-2 text-sm font-semibold text-red-800">Error loading repository</h3>
          <p className="mt-1 text-sm text-red-600">{(error as Error)?.message || "Repository not found"}</p>
        </div>
      </div>
    );
  }

  const status = getRepoStatus(repo.repo);

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        href="/app/agents-md"
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
      >
        <ArrowLeftIcon className="h-4 w-4" />
        Back to AGENTS.md
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100">
            <DocumentTextIcon className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{repo.repo.project_name}</h1>
            <p className="text-sm text-gray-500">{repo.repo.github_repo_full_name}</p>
          </div>
          <StatusBadge status={status} />
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRegenerate}
            disabled={regenerateMutation.isPending}
            className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 disabled:opacity-50"
          >
            <ArrowPathIcon className={`h-4 w-4 ${regenerateMutation.isPending ? "animate-spin" : ""}`} />
            {regenerateMutation.isPending ? "Regenerating..." : "Regenerate"}
          </button>
        </div>
      </div>

      {/* Metadata */}
      <div className="flex flex-wrap gap-4 text-sm text-gray-500">
        <div className="flex items-center gap-1">
          <ClockIcon className="h-4 w-4" />
          Last updated: {formatRelativeTime(repo.repo.last_generated_at)}
        </div>
        {repo.repo.line_count && (
          <div className="flex items-center gap-1">
            <DocumentTextIcon className="h-4 w-4" />
            {repo.repo.line_count} lines
          </div>
        )}
        {repo.repo.generator_version && (
          <div className="flex items-center gap-1">
            Generator: v{repo.repo.generator_version}
          </div>
        )}
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left: AGENTS.md Content */}
        <div className="lg:col-span-2 space-y-6">
          {repo.file ? (
            <AgentsMdContentViewer content={repo.file.content} />
          ) : (
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-12 text-center">
              <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-semibold text-gray-900">No AGENTS.md file</h3>
              <p className="mt-1 text-sm text-gray-500">
                Click &quot;Regenerate&quot; to generate an AGENTS.md file for this repository.
              </p>
            </div>
          )}

          {/* Version History */}
          {repo.versions && repo.versions.length > 0 && (
            <VersionHistory versions={repo.versions} />
          )}
        </div>

        {/* Right: Dynamic Context */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Dynamic Context</h2>
            <span className="text-xs text-gray-500">Live</span>
          </div>
          <ContextOverlayPanel context={contextAnalysis} />
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Loading Skeleton
// =============================================================================

function AgentsMdRepoDetailSkeleton() {
  return (
    <div className="space-y-6">
      {/* Back link skeleton */}
      <div className="h-5 w-36 rounded bg-gray-200 animate-pulse" />

      {/* Header skeleton */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 rounded-lg bg-gray-200 animate-pulse" />
          <div>
            <div className="h-8 w-48 rounded bg-gray-200 animate-pulse" />
            <div className="mt-2 h-4 w-32 rounded bg-gray-200 animate-pulse" />
          </div>
        </div>
        <div className="h-10 w-32 rounded bg-gray-200 animate-pulse" />
      </div>

      {/* Metadata skeleton */}
      <div className="flex gap-4">
        <div className="h-4 w-32 rounded bg-gray-200 animate-pulse" />
        <div className="h-4 w-24 rounded bg-gray-200 animate-pulse" />
      </div>

      {/* Content Grid skeleton */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <div className="h-[400px] rounded-lg border border-gray-200 bg-gray-100 animate-pulse" />
          <div className="h-48 rounded-lg border border-gray-200 bg-gray-100 animate-pulse" />
        </div>
        <div className="space-y-4">
          <div className="h-6 w-32 rounded bg-gray-200 animate-pulse" />
          <div className="h-32 rounded-lg border border-gray-200 bg-gray-100 animate-pulse" />
          <div className="h-32 rounded-lg border border-gray-200 bg-gray-100 animate-pulse" />
        </div>
      </div>
    </div>
  );
}
