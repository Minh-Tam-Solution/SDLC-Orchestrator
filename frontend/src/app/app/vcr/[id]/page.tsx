/**
 * VCR Detail Page - SDLC Orchestrator
 *
 * @module frontend/src/app/app/vcr/[id]/page
 * @description Sprint 151 - SASE Artifacts Enhancement: VCR detail view and approval workflow
 * @sdlc SDLC 6.0.5 Universal Framework
 * @status Sprint 151 - SASE Artifacts Enhancement
 */

"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  useVcr,
  useApproveVcr,
  useRejectVcr,
  useReopenVcr,
  type VCRStatus,
} from "@/hooks/useVcr";
import { useAuth } from "@/hooks/useAuth";

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

function ArrowLeftIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
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

function ClockIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
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

function PencilSquareIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10" />
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

function SparklesIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
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

function LinkIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m13.35-.622 1.757-1.757a4.5 4.5 0 0 0-6.364-6.364l-4.5 4.5a4.5 4.5 0 0 0 1.242 7.244" />
    </svg>
  );
}

// =============================================================================
// Helper Functions
// =============================================================================

const STATUS_CONFIG: Record<VCRStatus, { label: string; color: string; bgColor: string; icon: React.ComponentType<{ className?: string }> }> = {
  draft: { label: "Draft", color: "text-gray-700", bgColor: "bg-gray-100", icon: PencilSquareIcon },
  submitted: { label: "Pending Review", color: "text-blue-700", bgColor: "bg-blue-100", icon: ClockIcon },
  approved: { label: "Approved", color: "text-green-700", bgColor: "bg-green-100", icon: CheckCircleIcon },
  rejected: { label: "Rejected", color: "text-red-700", bgColor: "bg-red-100", icon: XCircleIcon },
};

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "N/A";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatAITools(tools: string[]): string {
  if (!tools || tools.length === 0) return "None";
  return tools.map(t => t.charAt(0).toUpperCase() + t.slice(1)).join(", ");
}

// =============================================================================
// Section Component
// =============================================================================

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mb-6">
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">
        {title}
      </h3>
      <div className="text-gray-900">{children}</div>
    </div>
  );
}

// =============================================================================
// Reject Modal Component
// =============================================================================

function RejectModal({
  onClose,
  onReject,
  isLoading,
}: {
  onClose: () => void;
  onReject: (reason: string) => void;
  isLoading: boolean;
}) {
  const [reason, setReason] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (reason.trim().length >= 10) {
      onReject(reason);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Reject VCR</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4">
          <p className="text-sm text-gray-600 mb-4">
            Please provide a reason for rejection. This will help the author improve the VCR.
          </p>

          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
            placeholder="Explain why this VCR is being rejected (min 10 characters)..."
            required
            minLength={10}
          />

          <div className="flex justify-end gap-3 mt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || reason.trim().length < 10}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <ArrowPathIcon className="w-4 h-4 animate-spin" />
                  Rejecting...
                </>
              ) : (
                <>
                  <XCircleIcon className="w-4 h-4" />
                  Reject VCR
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
// Main Page Component
// =============================================================================

export default function VCRDetailPage() {
  const params = useParams();
  const router = useRouter();
  const vcrId = params.id as string;

  const { user } = useAuth();
  const { data: vcr, isLoading, error, refetch } = useVcr(vcrId);

  const approveMutation = useApproveVcr();
  const rejectMutation = useRejectVcr();
  const reopenMutation = useReopenVcr();

  const [showRejectModal, setShowRejectModal] = useState(false);

  // Check if user can approve/reject (CTO/CEO/Admin)
  const canApprove = user?.roles?.some(role =>
    ["cto", "ceo", "admin", "platform_admin"].includes(role.toLowerCase())
  ) || user?.is_platform_admin;

  // Handlers
  const handleApprove = async () => {
    if (confirm("Are you sure you want to approve this VCR?")) {
      try {
        await approveMutation.mutateAsync(vcrId);
        refetch();
      } catch {
        // Error handling done by mutation
      }
    }
  };

  const handleReject = async (reason: string) => {
    try {
      await rejectMutation.mutateAsync({ vcrId, request: { reason } });
      setShowRejectModal(false);
      refetch();
    } catch {
      // Error handling done by mutation
    }
  };

  const handleReopen = async () => {
    if (confirm("Reopen this VCR? It will return to draft status for editing.")) {
      try {
        await reopenMutation.mutateAsync(vcrId);
        refetch();
      } catch {
        // Error handling done by mutation
      }
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <ArrowPathIcon className="w-8 h-8 text-gray-400 animate-spin mx-auto mb-4" />
          <p className="text-gray-500">Loading VCR...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !vcr) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <XCircleIcon className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-lg font-medium text-gray-900 mb-2">VCR Not Found</h2>
          <p className="text-gray-500 mb-4">The requested VCR could not be found.</p>
          <Link
            href="/app/vcr"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <ArrowLeftIcon className="w-4 h-4" />
            Back to VCRs
          </Link>
        </div>
      </div>
    );
  }

  const statusConfig = STATUS_CONFIG[vcr.status];
  const StatusIcon = statusConfig.icon;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {/* Breadcrumb */}
          <div className="mb-4">
            <Link
              href="/app/vcr"
              className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700"
            >
              <ArrowLeftIcon className="w-4 h-4" />
              Back to VCRs
            </Link>
          </div>

          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4">
              <div className={`p-3 rounded-lg ${statusConfig.bgColor}`}>
                <StatusIcon className={`w-6 h-6 ${statusConfig.color}`} />
              </div>
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${statusConfig.bgColor} ${statusConfig.color}`}>
                    {statusConfig.label}
                  </span>
                  {vcr.ai_generated_percentage > 0 && (
                    <span className="px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-700 flex items-center gap-1">
                      <SparklesIcon className="w-3 h-3" />
                      {Math.round(vcr.ai_generated_percentage * 100)}% AI Generated
                    </span>
                  )}
                </div>
                <h1 className="text-2xl font-bold text-gray-900">{vcr.title}</h1>
                <p className="text-sm text-gray-500 mt-1">
                  Created by {vcr.created_by?.name || "Unknown"} on {formatDate(vcr.created_at)}
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              {vcr.pr_url && (
                <a
                  href={vcr.pr_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 text-sm font-medium inline-flex items-center gap-2"
                >
                  <LinkIcon className="w-4 h-4" />
                  PR #{vcr.pr_number}
                </a>
              )}

              {vcr.status === "submitted" && canApprove && (
                <>
                  <button
                    onClick={() => setShowRejectModal(true)}
                    disabled={rejectMutation.isPending}
                    className="px-4 py-2 text-red-700 bg-red-50 rounded-lg hover:bg-red-100 text-sm font-medium inline-flex items-center gap-2"
                  >
                    <XCircleIcon className="w-4 h-4" />
                    Reject
                  </button>
                  <button
                    onClick={handleApprove}
                    disabled={approveMutation.isPending}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium inline-flex items-center gap-2"
                  >
                    {approveMutation.isPending ? (
                      <ArrowPathIcon className="w-4 h-4 animate-spin" />
                    ) : (
                      <CheckCircleIcon className="w-4 h-4" />
                    )}
                    Approve
                  </button>
                </>
              )}

              {vcr.status === "rejected" && (
                <button
                  onClick={handleReopen}
                  disabled={reopenMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium inline-flex items-center gap-2"
                >
                  {reopenMutation.isPending ? (
                    <ArrowPathIcon className="w-4 h-4 animate-spin" />
                  ) : (
                    <ArrowPathIcon className="w-4 h-4" />
                  )}
                  Reopen
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          {/* Problem Statement */}
          <Section title="Problem Statement">
            <p className="text-gray-700 whitespace-pre-wrap">{vcr.problem_statement}</p>
          </Section>

          {/* Root Cause Analysis (if present) */}
          {vcr.root_cause_analysis && (
            <Section title="Root Cause Analysis">
              <p className="text-gray-700 whitespace-pre-wrap">{vcr.root_cause_analysis}</p>
            </Section>
          )}

          {/* Solution Approach */}
          <Section title="Solution Approach">
            <p className="text-gray-700 whitespace-pre-wrap">{vcr.solution_approach}</p>
          </Section>

          {/* Implementation Notes (if present) */}
          {vcr.implementation_notes && (
            <Section title="Implementation Notes">
              <p className="text-gray-700 whitespace-pre-wrap">{vcr.implementation_notes}</p>
            </Section>
          )}

          {/* AI Attribution */}
          {(vcr.ai_generated_percentage > 0 || vcr.ai_tools_used.length > 0) && (
            <div className="border-t border-gray-200 pt-6 mt-6">
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4 flex items-center gap-2">
                <SparklesIcon className="w-4 h-4 text-purple-600" />
                AI Attribution
              </h3>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-purple-50 rounded-lg p-4">
                  <p className="text-sm text-purple-600 mb-1">AI Generated Code</p>
                  <p className="text-2xl font-semibold text-purple-900">
                    {Math.round(vcr.ai_generated_percentage * 100)}%
                  </p>
                </div>
                <div className="bg-purple-50 rounded-lg p-4">
                  <p className="text-sm text-purple-600 mb-1">AI Tools Used</p>
                  <p className="text-lg font-medium text-purple-900">
                    {formatAITools(vcr.ai_tools_used)}
                  </p>
                </div>
              </div>

              {vcr.ai_generation_details && Object.keys(vcr.ai_generation_details).length > 0 && (
                <div className="mt-4 bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-2">AI Generation Details:</p>
                  <pre className="text-xs text-gray-700 overflow-x-auto">
                    {JSON.stringify(vcr.ai_generation_details, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}

          {/* Rejection Reason (if rejected) */}
          {vcr.status === "rejected" && vcr.rejection_reason && (
            <div className="border-t border-gray-200 pt-6 mt-6">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-red-700 mb-2 flex items-center gap-2">
                  <XCircleIcon className="w-4 h-4" />
                  Rejection Reason
                </h3>
                <p className="text-red-700">{vcr.rejection_reason}</p>
              </div>
            </div>
          )}

          {/* Approval Info (if approved) */}
          {vcr.status === "approved" && vcr.approved_by && (
            <div className="border-t border-gray-200 pt-6 mt-6">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-green-700 mb-2 flex items-center gap-2">
                  <CheckCircleIcon className="w-4 h-4" />
                  Approved
                </h3>
                <p className="text-green-700">
                  Approved by <strong>{vcr.approved_by.name}</strong> on {formatDate(vcr.approved_at)}
                </p>
              </div>
            </div>
          )}

          {/* Metadata */}
          <div className="border-t border-gray-200 pt-6 mt-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Created</p>
                <p className="font-medium text-gray-900">{formatDate(vcr.created_at)}</p>
              </div>
              <div>
                <p className="text-gray-500">Last Updated</p>
                <p className="font-medium text-gray-900">{formatDate(vcr.updated_at)}</p>
              </div>
              {vcr.submitted_at && (
                <div>
                  <p className="text-gray-500">Submitted</p>
                  <p className="font-medium text-gray-900">{formatDate(vcr.submitted_at)}</p>
                </div>
              )}
              {vcr.evidence_ids.length > 0 && (
                <div>
                  <p className="text-gray-500">Linked Evidence</p>
                  <p className="font-medium text-gray-900">{vcr.evidence_ids.length} items</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Reject Modal */}
      {showRejectModal && (
        <RejectModal
          onClose={() => setShowRejectModal(false)}
          onReject={handleReject}
          isLoading={rejectMutation.isPending}
        />
      )}
    </div>
  );
}
