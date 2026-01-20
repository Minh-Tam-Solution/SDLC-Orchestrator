/**
 * Check Run Detail Page - SDLC Orchestrator
 *
 * @module frontend/src/app/app/check-runs/[id]/page
 * @description Detail view for individual GitHub Check Run
 * @sdlc SDLC 5.1.3 Framework - Sprint 86 (GitHub Check Run UI)
 * @status Sprint 86 - CTO APPROVED (January 20, 2026)
 */

"use client";

import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useCheckRunDetail, useRerunCheckRun } from "@/hooks/useGitHubChecks";
import {
  getModeMetadata,
  getConclusionMetadata,
  getStatusLabel,
  formatDuration,
  formatRelativeTime,
  getShortSha,
  canRerun,
  isBlocking,
  type GateIssue,
  type CheckRunAnnotation,
} from "@/lib/types/github-checks";

// =============================================================================
// Icon Components (Inline SVGs)
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

function ArrowTopRightIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
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

function ClockIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
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

function DocumentTextIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
    </svg>
  );
}

function CodeBracketIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
    </svg>
  );
}

// =============================================================================
// Conclusion Icon Component
// =============================================================================

function ConclusionIcon({
  conclusion,
  className = "h-8 w-8",
}: {
  conclusion?: string;
  className?: string;
}) {
  switch (conclusion) {
    case "success":
      return <CheckCircleIcon className={`${className} text-green-500`} />;
    case "failure":
      return <XCircleIcon className={`${className} text-red-500`} />;
    case "neutral":
      return (
        <div
          className={`${className} rounded-full bg-gray-200 flex items-center justify-center`}
        >
          <span className="text-gray-500 text-lg">-</span>
        </div>
      );
    case "action_required":
      return (
        <ExclamationTriangleIcon className={`${className} text-yellow-500`} />
      );
    case "cancelled":
    case "timed_out":
    case "skipped":
      return <ClockIcon className={`${className} text-gray-400`} />;
    default:
      return (
        <ArrowPathIcon className={`${className} text-blue-500 animate-spin`} />
      );
  }
}

// =============================================================================
// Info Card Component
// =============================================================================

function InfoCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border bg-white p-4">
      <h3 className="text-sm font-medium text-gray-500 mb-3">{title}</h3>
      {children}
    </div>
  );
}

// =============================================================================
// Gate Issue Row Component
// =============================================================================

function GateIssueRow({ issue }: { issue: GateIssue }) {
  const severityColors = {
    info: "bg-blue-50 text-blue-700",
    warning: "bg-yellow-50 text-yellow-700",
    error: "bg-red-50 text-red-700",
  };

  return (
    <div className="flex items-start gap-3 py-3 border-b last:border-0">
      <span
        className={`px-2 py-0.5 text-xs font-medium rounded ${severityColors[issue.severity]}`}
      >
        {issue.severity.toUpperCase()}
      </span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <CodeBracketIcon className="h-4 w-4 text-gray-400" />
          <span className="text-sm font-mono text-gray-600 truncate">
            {issue.file_path}:{issue.line_number}
          </span>
        </div>
        <p className="mt-1 text-sm text-gray-900">{issue.message}</p>
        {issue.rule_id && (
          <span className="text-xs text-gray-500">Rule: {issue.rule_id}</span>
        )}
      </div>
      <span className="text-xs font-mono text-gray-400">{issue.code}</span>
    </div>
  );
}

// =============================================================================
// Annotation Row Component
// =============================================================================

function AnnotationRow({ annotation }: { annotation: CheckRunAnnotation }) {
  const levelColors = {
    notice: "bg-blue-50 text-blue-700 border-blue-200",
    warning: "bg-yellow-50 text-yellow-700 border-yellow-200",
    failure: "bg-red-50 text-red-700 border-red-200",
  };

  return (
    <div
      className={`rounded-lg border p-3 ${levelColors[annotation.annotation_level]}`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-medium text-sm">{annotation.title}</span>
        <span className="text-xs font-mono">
          {annotation.path}:{annotation.start_line}
          {annotation.end_line !== annotation.start_line &&
            `-${annotation.end_line}`}
        </span>
      </div>
      <p className="text-sm">{annotation.message}</p>
    </div>
  );
}

// =============================================================================
// Main Check Run Detail Page
// =============================================================================

export default function CheckRunDetailPage() {
  const params = useParams();
  const router = useRouter();
  const checkRunId = params.id as string;

  const { checkRun, isLoading, error, refetch } =
    useCheckRunDetail(checkRunId);
  const rerunMutation = useRerunCheckRun();

  // Extract gate result from check run detail
  const gateResult = checkRun?.gate_result;

  const handleRerun = async () => {
    if (!checkRun || !canRerun(checkRun)) return;

    try {
      await rerunMutation.mutateAsync({ check_run_id: checkRun.id });
      refetch();
    } catch {
      // Error handled by mutation
    }
  };

  if (isLoading) {
    return <CheckRunDetailSkeleton />;
  }

  if (error || !checkRun) {
    return (
      <div className="flex flex-col items-center justify-center h-96">
        <XCircleIcon className="h-12 w-12 text-red-400 mb-4" />
        <h2 className="text-lg font-medium text-gray-900">
          Check Run Not Found
        </h2>
        <p className="text-gray-500 mt-1">
          The requested check run could not be loaded.
        </p>
        <Link
          href="/app/check-runs"
          className="mt-4 text-blue-600 hover:text-blue-700"
        >
          Back to Check Runs
        </Link>
      </div>
    );
  }

  const modeMetadata = getModeMetadata(checkRun.mode);
  const conclusionMetadata = getConclusionMetadata(checkRun.conclusion);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <button
            onClick={() => router.back()}
            className="mt-1 p-1 rounded hover:bg-gray-100"
          >
            <ArrowLeftIcon className="h-5 w-5 text-gray-500" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <ConclusionIcon conclusion={checkRun.conclusion} />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {checkRun.pr_title || `Check Run #${checkRun.check_run_id}`}
                </h1>
                <p className="text-gray-500 mt-1">
                  {checkRun.repository_full_name} •{" "}
                  <span className="font-mono">
                    {getShortSha(checkRun.head_sha)}
                  </span>
                </p>
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {canRerun(checkRun) && (
            <button
              onClick={handleRerun}
              disabled={rerunMutation.isPending}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              <ArrowPathIcon
                className={`h-4 w-4 ${rerunMutation.isPending ? "animate-spin" : ""}`}
              />
              Re-run
            </button>
          )}
          <a
            href={checkRun.html_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-900 text-white hover:bg-gray-800"
          >
            <ArrowTopRightIcon className="h-4 w-4" />
            View on GitHub
          </a>
        </div>
      </div>

      {/* Status Banner */}
      <div
        className={`rounded-lg p-4 ${conclusionMetadata.bgColor} flex items-center justify-between`}
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">{conclusionMetadata.icon}</span>
          <div>
            <h2
              className={`text-lg font-semibold ${conclusionMetadata.color}`}
            >
              {conclusionMetadata.label}
            </h2>
            <p className="text-sm text-gray-600">
              {conclusionMetadata.description}
            </p>
          </div>
        </div>
        {checkRun.bypassed && (
          <span className="px-3 py-1 rounded-full bg-yellow-200 text-yellow-800 text-sm font-medium">
            Bypassed
          </span>
        )}
      </div>

      {/* Info Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Status */}
        <InfoCard title="Status">
          <div className="flex items-center gap-2">
            <span
              className={`px-2 py-1 rounded text-sm font-medium ${
                checkRun.status === "completed"
                  ? "bg-gray-100 text-gray-700"
                  : checkRun.status === "in_progress"
                    ? "bg-blue-100 text-blue-700"
                    : "bg-gray-50 text-gray-500"
              }`}
            >
              {getStatusLabel(checkRun.status)}
            </span>
          </div>
        </InfoCard>

        {/* Mode */}
        <InfoCard title="Enforcement Mode">
          <div className="flex items-center gap-2">
            <span className="text-xl">{modeMetadata.icon}</span>
            <div>
              <span className={`font-medium ${modeMetadata.color}`}>
                {modeMetadata.label}
              </span>
              {isBlocking(checkRun) && (
                <div className="flex items-center gap-1 mt-1">
                  <ShieldCheckIcon className="h-4 w-4 text-orange-500" />
                  <span className="text-xs text-orange-600">
                    Blocks merge on failure
                  </span>
                </div>
              )}
            </div>
          </div>
        </InfoCard>

        {/* Duration */}
        <InfoCard title="Duration">
          <div className="flex items-center gap-2">
            <ClockIcon className="h-5 w-5 text-gray-400" />
            <span className="text-lg font-medium">
              {formatDuration(checkRun.duration_ms)}
            </span>
          </div>
        </InfoCard>

        {/* Timing */}
        <InfoCard title="Timing">
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Started:</span>
              <span>{formatRelativeTime(checkRun.started_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Completed:</span>
              <span>{formatRelativeTime(checkRun.completed_at)}</span>
            </div>
          </div>
        </InfoCard>
      </div>

      {/* PR Info */}
      {checkRun.pr_number && (
        <InfoCard title="Pull Request">
          <div className="flex items-center justify-between">
            <div>
              <a
                href={checkRun.pr_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                #{checkRun.pr_number}: {checkRun.pr_title}
              </a>
            </div>
            <ArrowTopRightIcon className="h-4 w-4 text-gray-400" />
          </div>
        </InfoCard>
      )}

      {/* Gate Results */}
      {gateResult && (
        <div className="rounded-lg border bg-white">
          <div className="p-4 border-b">
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-gray-900 flex items-center gap-2">
                <ShieldCheckIcon className="h-5 w-5 text-gray-500" />
                Gate Evaluation Results
              </h3>
              <div className="flex items-center gap-4 text-sm">
                <span className="text-green-600">
                  {gateResult.gates_passed} passed
                </span>
                <span className="text-red-600">
                  {gateResult.gates_failed} failed
                </span>
                <span className="text-gray-500">
                  of {gateResult.gates_evaluated} gates
                </span>
              </div>
            </div>
          </div>

          {gateResult.issues.length > 0 ? (
            <div className="p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-3">
                Issues Found ({gateResult.issues.length})
              </h4>
              <div className="divide-y">
                {gateResult.issues.map((issue, idx) => (
                  <GateIssueRow key={idx} issue={issue} />
                ))}
              </div>
            </div>
          ) : (
            <div className="p-8 text-center">
              <CheckCircleIcon className="h-12 w-12 text-green-400 mx-auto mb-2" />
              <p className="text-gray-500">All gates passed successfully</p>
            </div>
          )}
        </div>
      )}

      {/* Check Run Output */}
      {checkRun.output && (
        <div className="rounded-lg border bg-white">
          <div className="p-4 border-b">
            <h3 className="font-medium text-gray-900 flex items-center gap-2">
              <DocumentTextIcon className="h-5 w-5 text-gray-500" />
              Check Run Output
            </h3>
          </div>
          <div className="p-4 space-y-4">
            <div>
              <h4 className="text-sm font-medium text-gray-700">
                {checkRun.output.title}
              </h4>
              <p className="text-gray-600 mt-1">{checkRun.output.summary}</p>
            </div>

            {checkRun.output.text && (
              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">
                  Details
                </h4>
                <pre className="p-3 bg-gray-50 rounded text-sm text-gray-700 overflow-x-auto whitespace-pre-wrap">
                  {checkRun.output.text}
                </pre>
              </div>
            )}

            {/* Annotations */}
            {checkRun.output.annotations.length > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-3">
                  Annotations ({checkRun.output.annotations.length})
                </h4>
                <div className="space-y-2">
                  {checkRun.output.annotations.map((annotation, idx) => (
                    <AnnotationRow key={idx} annotation={annotation} />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Context Overlay */}
      {checkRun.overlay && (
        <div className="rounded-lg border bg-white">
          <div className="p-4 border-b">
            <h3 className="font-medium text-gray-900">Context Overlay</h3>
          </div>
          <div className="p-4">
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <span className="text-sm text-gray-500">Stage</span>
                <p className="font-medium">{checkRun.overlay.stage_name}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Gate Status</span>
                <p className="font-medium">{checkRun.overlay.gate_status}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Constraints</span>
                <p className="font-medium">
                  {checkRun.overlay.constraints_count} active
                </p>
              </div>
            </div>
            {checkRun.overlay.sprint && (
              <div className="mt-4 p-3 bg-gray-50 rounded">
                <span className="text-sm text-gray-500">Current Sprint</span>
                <p className="font-medium">
                  Sprint {checkRun.overlay.sprint.number}:{" "}
                  {checkRun.overlay.sprint.goal}
                </p>
                <p className="text-sm text-gray-500">
                  {checkRun.overlay.sprint.days_remaining} days remaining
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Loading Skeleton
// =============================================================================

function CheckRunDetailSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Header */}
      <div className="flex items-start gap-4">
        <div className="h-8 w-8 bg-gray-200 rounded" />
        <div className="flex-1">
          <div className="h-8 w-96 bg-gray-200 rounded" />
          <div className="mt-2 h-4 w-48 bg-gray-200 rounded" />
        </div>
      </div>

      {/* Status Banner */}
      <div className="h-20 bg-gray-100 rounded-lg" />

      {/* Info Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-24 bg-gray-100 rounded-lg" />
        ))}
      </div>

      {/* Gate Results */}
      <div className="h-64 bg-gray-100 rounded-lg" />
    </div>
  );
}
