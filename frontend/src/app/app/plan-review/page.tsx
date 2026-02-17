/**
 * Plan Review Dashboard - SDLC Orchestrator
 *
 * @module frontend/src/app/app/plan-review/page
 * @description Planning session list with conformance scores and approval workflow
 * @sdlc SDLC 6.0.6 Framework - Sprint 175 (Frontend Feature Completion)
 * @reference ADR-034 Planning Sub-agent Orchestration
 * @status Sprint 99 - Implementation
 */

"use client";

import React, { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  usePlanningSessions,
  useCreatePlanningSession,
  useApprovePlanningSession,
  useRejectPlanningSession,
  usePlanningSubagentHealth,
} from "@/hooks/usePlanningReview";
import {
  ConformanceScoreBadge,
  PlanningStatusBadge,
} from "@/components/planning";
import type {
  PlanningStatus,
  PlanningSessionSummary,
} from "@/lib/types/planning-subagent";

// =============================================================================
// ICONS
// =============================================================================

function PlusIcon({ className }: { className?: string }) {
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
        d="M12 4.5v15m7.5-7.5h-15"
      />
    </svg>
  );
}

function ClipboardDocumentListIcon({ className }: { className?: string }) {
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
        d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25ZM6.75 12h.008v.008H6.75V12Zm0 3h.008v.008H6.75V15Zm0 3h.008v.008H6.75V18Z"
      />
    </svg>
  );
}

function FunnelIcon({ className }: { className?: string }) {
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
        d="M12 3c2.755 0 5.455.232 8.083.678.533.09.917.556.917 1.096v1.044a2.25 2.25 0 0 1-.659 1.591l-5.432 5.432a2.25 2.25 0 0 0-.659 1.591v2.927a2.25 2.25 0 0 1-1.244 2.013L9.75 21v-6.568a2.25 2.25 0 0 0-.659-1.591L3.659 7.409A2.25 2.25 0 0 1 3 5.818V4.774c0-.54.384-1.006.917-1.096A48.32 48.32 0 0 1 12 3Z"
      />
    </svg>
  );
}

function ArrowPathIcon({ className }: { className?: string }) {
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
        d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99"
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

function CheckIcon({ className }: { className?: string }) {
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
        d="M4.5 12.75l6 6 9-13.5"
      />
    </svg>
  );
}

function XMarkIcon({ className }: { className?: string }) {
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
        d="M6 18L18 6M6 6l12 12"
      />
    </svg>
  );
}

// =============================================================================
// STATUS FILTER OPTIONS
// =============================================================================

const STATUS_OPTIONS: { value: PlanningStatus | "all"; label: string }[] = [
  { value: "all", label: "All Sessions" },
  { value: "pending_approval", label: "Pending Approval" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
  { value: "extracting", label: "Extracting" },
  { value: "synthesizing", label: "Synthesizing" },
  { value: "expired", label: "Expired" },
];

// =============================================================================
// STATS CARDS
// =============================================================================

interface StatsCardsProps {
  total: number;
  pending: number;
  approved: number;
  rejected: number;
}

function StatsCards({ total, pending, approved, rejected }: StatsCardsProps) {
  return (
    <div className="grid gap-4 md:grid-cols-4">
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
        <div className="text-2xl font-bold text-blue-700">{total}</div>
        <div className="text-sm text-blue-600">Total Sessions</div>
      </div>
      <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
        <div className="text-2xl font-bold text-yellow-700">{pending}</div>
        <div className="text-sm text-yellow-600">Pending Approval</div>
      </div>
      <div className="rounded-lg border border-green-200 bg-green-50 p-4">
        <div className="text-2xl font-bold text-green-700">{approved}</div>
        <div className="text-sm text-green-600">Approved</div>
      </div>
      <div className="rounded-lg border border-red-200 bg-red-50 p-4">
        <div className="text-2xl font-bold text-red-700">{rejected}</div>
        <div className="text-sm text-red-600">Rejected</div>
      </div>
    </div>
  );
}

// =============================================================================
// SESSION LIST ITEM
// =============================================================================

interface SessionListItemProps {
  session: PlanningSessionSummary;
  onClick: () => void;
  onApprove?: (sessionId: string) => void;
  onReject?: (sessionId: string, notes: string) => void;
  isApproving?: boolean;
  isRejecting?: boolean;
}

function SessionListItem({
  session,
  onClick,
  onApprove,
  onReject,
  isApproving,
  isRejecting,
}: SessionListItemProps) {
  const [rejectNotes, setRejectNotes] = useState("");
  const [showRejectInput, setShowRejectInput] = useState(false);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const isPending = session.status === "pending_approval";

  return (
    <div
      className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0 cursor-pointer" onClick={onClick}>
          <div className="flex items-center gap-3 mb-2">
            <PlanningStatusBadge status={session.status} />
            {session.requires_approval && isPending && (
              <span className="px-2 py-0.5 bg-orange-100 text-orange-700 text-xs rounded-full font-medium">
                Needs Review
              </span>
            )}
          </div>
          <h3 className="text-base font-medium text-gray-900 truncate mb-1">
            {session.task}
          </h3>
          <p className="text-sm text-gray-500">
            Created {formatDate(session.created_at)}
          </p>
        </div>

        <div className="ml-4 flex flex-col items-end gap-2">
          <ConformanceScoreBadge
            score={session.conformance_score}
            showLabel={true}
          />
          <span className="text-xs text-gray-400 font-mono">
            {session.id.slice(0, 8)}
          </span>
        </div>
      </div>

      {/* Inline approve/reject actions for pending sessions */}
      {isPending && onApprove && onReject && (
        <div className="mt-3 pt-3 border-t">
          {showRejectInput ? (
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={rejectNotes}
                onChange={(e) => setRejectNotes(e.target.value)}
                placeholder="Rejection reason..."
                className="flex-1 px-3 py-1.5 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
                onClick={(e) => e.stopPropagation()}
              />
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (rejectNotes.trim()) {
                    onReject(session.id, rejectNotes.trim());
                    setShowRejectInput(false);
                    setRejectNotes("");
                  }
                }}
                disabled={isRejecting || !rejectNotes.trim()}
                className="px-3 py-1.5 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md disabled:opacity-50"
              >
                {isRejecting ? "Rejecting..." : "Confirm"}
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowRejectInput(false);
                  setRejectNotes("");
                }}
                className="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-md"
              >
                Cancel
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onApprove(session.id);
                }}
                disabled={isApproving}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-green-700 bg-green-50 hover:bg-green-100 border border-green-200 rounded-md disabled:opacity-50"
              >
                <CheckIcon className="h-4 w-4" />
                {isApproving ? "Approving..." : "Approve"}
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowRejectInput(true);
                }}
                disabled={isRejecting}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-red-700 bg-red-50 hover:bg-red-100 border border-red-200 rounded-md disabled:opacity-50"
              >
                <XMarkIcon className="h-4 w-4" />
                Reject
              </button>
              <span className="text-xs text-gray-400 ml-auto">
                Click row to view full plan
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// CREATE SESSION MODAL
// =============================================================================

interface CreateSessionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (task: string) => void;
  isSubmitting: boolean;
}

function CreateSessionModal({
  open,
  onOpenChange,
  onSubmit,
  isSubmitting,
}: CreateSessionModalProps) {
  const [task, setTask] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (task.trim()) {
      onSubmit(task.trim());
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50"
        onClick={() => onOpenChange(false)}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Create Planning Session
        </h2>
        <p className="text-sm text-gray-500 mb-4">
          Describe the task you want to implement. The planning sub-agent will
          extract patterns and generate an implementation plan.
        </p>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label
              htmlFor="task"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Task Description
            </label>
            <textarea
              id="task"
              value={task}
              onChange={(e) => setTask(e.target.value)}
              placeholder="e.g., Add user authentication with JWT tokens..."
              rows={4}
              className="w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
            <p className="mt-1 text-xs text-gray-500">
              Per ADR-034: Planning mode is recommended for changes &gt;15 LOC
            </p>
          </div>

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={() => onOpenChange(false)}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              disabled={isSubmitting || !task.trim()}
            >
              {isSubmitting ? (
                <>
                  <ArrowPathIcon className="h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <PlusIcon className="h-4 w-4" />
                  Create Session
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
// LOADING SKELETON
// =============================================================================

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      {/* Stats Skeleton */}
      <div className="grid gap-4 md:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-20 animate-pulse rounded-lg bg-gray-200" />
        ))}
      </div>

      {/* List Skeleton */}
      <div className="space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-24 animate-pulse rounded-lg bg-gray-200" />
        ))}
      </div>
    </div>
  );
}

// =============================================================================
// EMPTY STATE
// =============================================================================

function EmptyState({ onCreateClick }: { onCreateClick: () => void }) {
  return (
    <div className="text-center py-12 bg-gray-50 rounded-lg">
      <ClipboardDocumentListIcon className="h-16 w-16 mx-auto mb-4 text-gray-300" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        No Planning Sessions
      </h3>
      <p className="text-gray-500 mb-4">
        Create your first planning session to get started with pattern-aware
        implementation.
      </p>
      <button
        onClick={onCreateClick}
        className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
      >
        <PlusIcon className="h-4 w-4" />
        Create Planning Session
      </button>
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function PlanReviewPage() {
  const router = useRouter();
  const [statusFilter, setStatusFilter] = useState<PlanningStatus | "all">(
    "all"
  );
  const [createModalOpen, setCreateModalOpen] = useState(false);

  // Fetch sessions
  const {
    data: sessionsData,
    isLoading,
    error,
    refetch,
  } = usePlanningSessions(
    statusFilter === "all" ? undefined : { status: statusFilter }
  );

  // Mutations
  const createSessionMutation = useCreatePlanningSession();
  const approveMutation = useApprovePlanningSession();
  const rejectMutation = useRejectPlanningSession();

  // Service health
  const { data: healthData } = usePlanningSubagentHealth();
  const isServiceHealthy = healthData?.status === "healthy";

  const handleApproveSession = useCallback(
    async (sessionId: string) => {
      try {
        await approveMutation.mutateAsync({ sessionId });
      } catch (err) {
        console.error("Failed to approve session:", err);
      }
    },
    [approveMutation]
  );

  const handleRejectSession = useCallback(
    async (sessionId: string, notes: string) => {
      try {
        await rejectMutation.mutateAsync({ sessionId, notes });
      } catch (err) {
        console.error("Failed to reject session:", err);
      }
    },
    [rejectMutation]
  );

  const handleSelectSession = useCallback(
    (sessionId: string) => {
      router.push(`/app/plan-review/${sessionId}`);
    },
    [router]
  );

  const handleCreateSession = useCallback(
    async (task: string) => {
      try {
        const result = await createSessionMutation.mutateAsync({ task });
        setCreateModalOpen(false);
        // Navigate to the new session
        router.push(`/app/plan-review/${result.id}`);
      } catch (error) {
        console.error("Failed to create planning session:", error);
      }
    },
    [createSessionMutation, router]
  );

  // Calculate stats
  const sessions = sessionsData?.sessions || [];
  const stats = {
    total: sessionsData?.total || 0,
    pending: sessions.filter((s) => s.status === "pending_approval").length,
    approved: sessions.filter((s) => s.status === "approved").length,
    rejected: sessions.filter((s) => s.status === "rejected").length,
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">Plan Review</h1>
            {healthData && (
              <span
                className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 text-xs font-medium rounded-full ${
                  isServiceHealthy
                    ? "bg-green-100 text-green-700"
                    : "bg-red-100 text-red-700"
                }`}
                title={`Planning sub-agent: ${healthData.status}${healthData.version ? ` v${healthData.version}` : ""}`}
              >
                <span
                  className={`h-2 w-2 rounded-full ${
                    isServiceHealthy ? "bg-green-500" : "bg-red-500"
                  }`}
                />
                {isServiceHealthy ? "Service Online" : "Service Offline"}
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500 mt-1">
            ADR-034: Planning Sub-agent sessions and conformance review
          </p>
        </div>
        <button
          onClick={() => setCreateModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <PlusIcon className="h-4 w-4" />
          New Session
        </button>
      </div>

      {isLoading ? (
        <LoadingSkeleton />
      ) : error ? (
        <div className="text-center py-12 bg-red-50 rounded-lg">
          <ExclamationTriangleIcon className="h-12 w-12 mx-auto mb-4 text-red-400" />
          <h3 className="text-lg font-medium text-red-900 mb-2">
            Error Loading Sessions
          </h3>
          <p className="text-red-700">
            {error instanceof Error ? error.message : "Failed to load data"}
          </p>
          <button
            onClick={() => refetch()}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Stats Cards */}
          <StatsCards {...stats} />

          {/* Filter Bar */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FunnelIcon className="h-5 w-5 text-gray-400" />
              <select
                value={statusFilter}
                onChange={(e) =>
                  setStatusFilter(e.target.value as PlanningStatus | "all")
                }
                className="px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={() => refetch()}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md"
              title="Refresh"
            >
              <ArrowPathIcon className="h-5 w-5" />
            </button>
          </div>

          {/* Session List */}
          {sessions.length === 0 ? (
            <EmptyState onCreateClick={() => setCreateModalOpen(true)} />
          ) : (
            <div className="space-y-3">
              {sessions.map((session) => (
                <SessionListItem
                  key={session.id}
                  session={session}
                  onClick={() => handleSelectSession(session.id)}
                  onApprove={handleApproveSession}
                  onReject={handleRejectSession}
                  isApproving={approveMutation.isPending}
                  isRejecting={rejectMutation.isPending}
                />
              ))}
            </div>
          )}

          {/* Help Text */}
          <div className="rounded-lg bg-gray-50 p-4">
            <h4 className="text-sm font-medium text-gray-900">
              Planning Sub-agent (ADR-034)
            </h4>
            <p className="mt-1 text-xs text-gray-500">
              Planning mode extracts codebase patterns, ADR constraints, and test
              conventions before generating an implementation plan. Per SDLC 6.0.6,
              planning mode is <strong>mandatory for changes &gt;15 LOC</strong> to
              prevent architectural drift.
            </p>
          </div>
        </div>
      )}

      {/* Create Session Modal */}
      <CreateSessionModal
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
        onSubmit={handleCreateSession}
        isSubmitting={createSessionMutation.isPending}
      />
    </div>
  );
}
