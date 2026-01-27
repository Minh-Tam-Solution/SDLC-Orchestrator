/**
 * Plan Review Detail Page - SDLC Orchestrator
 *
 * @module frontend/src/app/app/plan-review/[id]/page
 * @description Single planning session review with approval workflow
 * @sdlc SDLC 5.2.0 Framework - Sprint 99 (Planning Sub-agent Part 2)
 * @reference ADR-034 Planning Sub-agent Orchestration
 * @status Sprint 99 - Implementation
 */

"use client";

import React, { useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  usePlanningSession,
  useApprovePlanningSession,
  useRejectPlanningSession,
} from "@/hooks/usePlanningReview";
import {
  ConformanceScoreBadge,
  PlanningStatusBadge,
  DeviationList,
  PatternSummaryCard,
  ImplementationPlanCard,
  PlanApprovalDialog,
} from "@/components/planning";

// =============================================================================
// ICONS
// =============================================================================

function ArrowLeftIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18"
      />
    </svg>
  );
}

function CheckCircleIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
      />
    </svg>
  );
}

function XCircleIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="m9.75 9.75 4.5 4.5m0-4.5-4.5 4.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
      />
    </svg>
  );
}

function ExclamationTriangleIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
      />
    </svg>
  );
}

function ClockIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
      />
    </svg>
  );
}

function DocumentTextIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
      />
    </svg>
  );
}

// UserIcon - reserved for future use in user display components

// =============================================================================
// METADATA CARD
// =============================================================================

interface MetadataCardProps {
  label: string;
  value: string | number | undefined;
  icon: React.ReactNode;
}

function MetadataCard({ label, value, icon }: MetadataCardProps) {
  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
      <div className="text-gray-400">{icon}</div>
      <div>
        <p className="text-xs text-gray-500">{label}</p>
        <p className="text-sm font-medium text-gray-900">{value ?? "N/A"}</p>
      </div>
    </div>
  );
}

// =============================================================================
// APPROVAL INFO
// =============================================================================

interface ApprovalInfoProps {
  approvedBy?: string;
  approvedAt?: string;
  approvalNotes?: string;
  status: string;
}

function ApprovalInfo({
  approvedBy,
  approvedAt,
  approvalNotes,
  status,
}: ApprovalInfoProps) {
  if (status !== "approved" && status !== "rejected") {
    return null;
  }

  const isApproved = status === "approved";
  const formatDate = (dateString?: string) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div
      className={`rounded-lg border p-4 ${
        isApproved
          ? "bg-green-50 border-green-200"
          : "bg-red-50 border-red-200"
      }`}
    >
      <div className="flex items-center gap-2 mb-2">
        {isApproved ? (
          <CheckCircleIcon className="h-5 w-5 text-green-600" />
        ) : (
          <XCircleIcon className="h-5 w-5 text-red-600" />
        )}
        <h4
          className={`font-medium ${
            isApproved ? "text-green-800" : "text-red-800"
          }`}
        >
          {isApproved ? "Plan Approved" : "Plan Rejected"}
        </h4>
      </div>
      <div className="space-y-1 text-sm">
        <p className={isApproved ? "text-green-700" : "text-red-700"}>
          <span className="font-medium">By:</span> {approvedBy || "Unknown"}
        </p>
        <p className={isApproved ? "text-green-700" : "text-red-700"}>
          <span className="font-medium">At:</span> {formatDate(approvedAt)}
        </p>
        {approvalNotes && (
          <p className={isApproved ? "text-green-700" : "text-red-700"}>
            <span className="font-medium">Notes:</span> {approvalNotes}
          </p>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// RECOMMENDATIONS LIST
// =============================================================================

function RecommendationsList({
  recommendations,
}: {
  recommendations: string[];
}) {
  if (recommendations.length === 0) {
    return (
      <div className="text-center py-4 text-gray-500 text-sm">
        No recommendations
      </div>
    );
  }

  return (
    <ul className="space-y-2">
      {recommendations.map((rec, index) => (
        <li key={index} className="flex items-start gap-2 text-sm">
          <span className="text-blue-500 mt-0.5">•</span>
          <span className="text-gray-700">{rec}</span>
        </li>
      ))}
    </ul>
  );
}

// =============================================================================
// LOADING SKELETON
// =============================================================================

function LoadingSkeleton() {
  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="h-8 w-48 bg-gray-200 rounded animate-pulse" />
      <div className="h-4 w-full max-w-lg bg-gray-200 rounded animate-pulse" />

      {/* Status Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-16 bg-gray-200 rounded-lg animate-pulse" />
        ))}
      </div>

      {/* Main Content */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="h-64 bg-gray-200 rounded-lg animate-pulse" />
        <div className="h-64 bg-gray-200 rounded-lg animate-pulse" />
      </div>

      <div className="h-96 bg-gray-200 rounded-lg animate-pulse" />
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function PlanReviewDetailPage() {
  const params = useParams();
  useRouter(); // Initialize router for navigation
  const sessionId = params.id as string;

  const [approvalDialogOpen, setApprovalDialogOpen] = useState(false);

  // Fetch session
  const {
    data: session,
    isLoading,
    error,
    refetch,
  } = usePlanningSession(sessionId);

  // Mutations
  const approveMutation = useApprovePlanningSession();
  const rejectMutation = useRejectPlanningSession();

  const handleApproveClick = useCallback(() => {
    setApprovalDialogOpen(true);
  }, []);

  const handleRejectClick = useCallback(() => {
    setApprovalDialogOpen(true);
  }, []);

  const formatDate = (dateString?: string) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="text-center py-12 bg-red-50 rounded-lg">
          <ExclamationTriangleIcon className="h-12 w-12 mx-auto mb-4 text-red-400" />
          <h3 className="text-lg font-medium text-red-900 mb-2">
            Error Loading Session
          </h3>
          <p className="text-red-700">
            {error instanceof Error ? error.message : "Failed to load data"}
          </p>
          <div className="flex justify-center gap-4 mt-4">
            <button
              onClick={() => refetch()}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
            >
              Retry
            </button>
            <Link
              href="/app/plan-review"
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
            >
              Back to List
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <ExclamationTriangleIcon className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Session Not Found
          </h3>
          <p className="text-gray-500 mb-4">
            The planning session you&apos;re looking for doesn&apos;t exist or
            has been deleted.
          </p>
          <Link
            href="/app/plan-review"
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Back to List
          </Link>
        </div>
      </div>
    );
  }

  const canApprove =
    session.requires_approval && session.status === "pending_approval";

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link
            href="/app/plan-review"
            className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-2"
          >
            <ArrowLeftIcon className="h-4 w-4" />
            Back to Plan Review
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 mb-1">
            Planning Session
          </h1>
          <div className="flex items-center gap-3">
            <PlanningStatusBadge status={session.status} />
            <span className="text-sm text-gray-500 font-mono">
              {session.id.slice(0, 8)}
            </span>
          </div>
        </div>

        {canApprove && (
          <div className="flex items-center gap-2">
            <button
              onClick={handleRejectClick}
              className="inline-flex items-center gap-2 px-4 py-2 border border-red-300 text-red-700 rounded-md hover:bg-red-50"
            >
              <XCircleIcon className="h-4 w-4" />
              Reject
            </button>
            <button
              onClick={handleApproveClick}
              className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              <CheckCircleIcon className="h-4 w-4" />
              Approve
            </button>
          </div>
        )}
      </div>

      {/* Task Description */}
      <div className="bg-white rounded-lg border p-4">
        <h2 className="text-sm font-medium text-gray-500 mb-1">
          Task Description
        </h2>
        <p className="text-gray-900">{session.task}</p>
      </div>

      {/* Metadata Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <MetadataCard
          label="Conformance Score"
          value={`${session.conformance.score}/100`}
          icon={<ConformanceScoreBadge score={session.conformance.score} size="sm" />}
        />
        <MetadataCard
          label="Created At"
          value={formatDate(session.created_at)}
          icon={<ClockIcon className="h-5 w-5" />}
        />
        <MetadataCard
          label="Execution Time"
          value={`${Math.round(session.execution_time_ms / 1000)}s`}
          icon={<ClockIcon className="h-5 w-5" />}
        />
        <MetadataCard
          label="Total LOC Estimated"
          value={session.plan.total_estimated_loc}
          icon={<DocumentTextIcon className="h-5 w-5" />}
        />
      </div>

      {/* Approval Info (if approved/rejected) */}
      <ApprovalInfo
        approvedBy={session.approved_by}
        approvedAt={session.approved_at}
        approvalNotes={session.approval_notes}
        status={session.status}
      />

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Pattern Summary */}
        <PatternSummaryCard patterns={session.patterns} />

        {/* Conformance Summary */}
        <div className="bg-white rounded-lg border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <ConformanceScoreBadge
              score={session.conformance.score}
              showLabel={true}
            />
          </h3>

          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-500 mb-2">Patterns Checked</p>
              <div className="flex flex-wrap gap-1">
                {session.conformance.patterns_checked.slice(0, 5).map((pattern) => (
                  <span
                    key={pattern}
                    className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                  >
                    {pattern}
                  </span>
                ))}
                {session.conformance.patterns_checked.length > 5 && (
                  <span className="px-2 py-1 bg-gray-100 text-gray-500 text-xs rounded">
                    +{session.conformance.patterns_checked.length - 5} more
                  </span>
                )}
              </div>
            </div>

            <div>
              <p className="text-sm text-gray-500 mb-2">Recommendations</p>
              <RecommendationsList
                recommendations={session.conformance.recommendations}
              />
            </div>

            {session.conformance.requires_adr && (
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                <div className="flex items-center gap-2">
                  <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600" />
                  <p className="text-sm text-yellow-800 font-medium">
                    ADR Required
                  </p>
                </div>
                <p className="text-sm text-yellow-700 mt-1">
                  This implementation introduces new patterns that should be
                  documented in an ADR.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Deviations */}
      {session.conformance.deviations.length > 0 && (
        <div className="bg-white rounded-lg border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Pattern Deviations ({session.conformance.deviations.length})
          </h3>
          <DeviationList deviations={session.conformance.deviations} />
        </div>
      )}

      {/* Implementation Plan */}
      <ImplementationPlanCard plan={session.plan} />

      {/* ADRs Referenced */}
      {session.plan.adrs_referenced.length > 0 && (
        <div className="bg-white rounded-lg border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            ADRs Referenced
          </h3>
          <div className="flex flex-wrap gap-2">
            {session.plan.adrs_referenced.map((adr) => (
              <span
                key={adr}
                className="px-3 py-1 bg-purple-100 text-purple-700 text-sm rounded-full"
              >
                {adr}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Risks */}
      {session.plan.risks.length > 0 && (
        <div className="bg-white rounded-lg border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <ExclamationTriangleIcon className="h-5 w-5 text-orange-500" />
            Identified Risks
          </h3>
          <ul className="space-y-2">
            {session.plan.risks.map((risk, index) => (
              <li key={index} className="flex items-start gap-2 text-sm">
                <span className="text-orange-500 mt-0.5">•</span>
                <span className="text-gray-700">{risk}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Help Text */}
      <div className="rounded-lg bg-gray-50 p-4">
        <h4 className="text-sm font-medium text-gray-900">
          Planning Sub-agent Review (ADR-034)
        </h4>
        <p className="mt-1 text-xs text-gray-500">
          Review the implementation plan, conformance score, and pattern
          deviations. Approve plans that follow established patterns or provide
          justification for deviations. Rejected plans will require revision
          before implementation.
        </p>
      </div>

      {/* Approval Dialog */}
      <PlanApprovalDialog
        plan={session}
        isOpen={approvalDialogOpen}
        onOpenChange={setApprovalDialogOpen}
        onApprove={async (notes) => {
          await approveMutation.mutateAsync({ sessionId, notes });
          setApprovalDialogOpen(false);
          refetch();
        }}
        onReject={async (notes) => {
          await rejectMutation.mutateAsync({ sessionId, notes });
          setApprovalDialogOpen(false);
          refetch();
        }}
        isApproving={approveMutation.isPending}
        isRejecting={rejectMutation.isPending}
      />
    </div>
  );
}
