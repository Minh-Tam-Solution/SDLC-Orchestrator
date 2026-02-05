/**
 * VCR (Version Controlled Resolution) Dashboard Page - SDLC Orchestrator
 *
 * @module frontend/src/app/app/vcr/page
 * @description Sprint 151 - SASE Artifacts Enhancement: VCR workflow management
 * @sdlc SDLC 6.0.3 Universal Framework
 * @status Sprint 151 - SASE Artifacts Enhancement
 */

"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { useProjects } from "@/hooks/useProjects";
import {
  useVcrs,
  useVcrStats,
  useCreateVcr,
  useDeleteVcr,
  useSubmitVcr,
  useAutoGenerateVcr,
  type VCRListOptions,
  type VCR,
  type VCRCreate,
  type VCRStatus,
  type VCRAutoGenerateRequest,
} from "@/hooks/useVcr";

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

function PlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
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

function TrashIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
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

function MagnifyingGlassIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
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

function PaperAirplaneIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5" />
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

// =============================================================================
// Helper Functions
// =============================================================================

const STATUS_CONFIG: Record<VCRStatus, { label: string; color: string; icon: React.ComponentType<{ className?: string }> }> = {
  draft: { label: "Draft", color: "bg-gray-100 text-gray-700", icon: PencilSquareIcon },
  submitted: { label: "Pending Review", color: "bg-blue-100 text-blue-700", icon: ClockIcon },
  approved: { label: "Approved", color: "bg-green-100 text-green-700", icon: CheckCircleIcon },
  rejected: { label: "Rejected", color: "bg-red-100 text-red-700", icon: XCircleIcon },
};

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "N/A";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatAITools(tools: string[]): string {
  if (!tools || tools.length === 0) return "None";
  return tools.map(t => t.charAt(0).toUpperCase() + t.slice(1)).join(", ");
}

// =============================================================================
// Stats Card Component
// =============================================================================

function StatsCard({
  title,
  value,
  icon: Icon,
  color,
}: {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// VCR Card Component
// =============================================================================

function VCRCard({
  vcr,
  onSubmit,
  onDelete,
}: {
  vcr: VCR;
  onSubmit: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  const statusConfig = STATUS_CONFIG[vcr.status];
  const StatusIcon = statusConfig.icon;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={`px-2 py-1 rounded text-xs font-medium flex items-center gap-1 ${statusConfig.color}`}>
            <StatusIcon className="w-3 h-3" />
            {statusConfig.label}
          </span>
          {vcr.ai_generated_percentage > 0 && (
            <span className="px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-700 flex items-center gap-1">
              <SparklesIcon className="w-3 h-3" />
              {Math.round(vcr.ai_generated_percentage * 100)}% AI
            </span>
          )}
        </div>
        {vcr.pr_number && (
          <Link
            href={vcr.pr_url || "#"}
            target="_blank"
            className="text-xs text-blue-600 hover:underline"
          >
            PR #{vcr.pr_number}
          </Link>
        )}
      </div>

      {/* Title */}
      <Link href={`/app/vcr/${vcr.id}`} className="block mb-2">
        <h3 className="text-lg font-semibold text-gray-900 hover:text-blue-600 transition-colors">
          {vcr.title}
        </h3>
      </Link>

      {/* Problem Statement (truncated) */}
      <p className="text-sm text-gray-600 mb-3 line-clamp-2">
        {vcr.problem_statement}
      </p>

      {/* AI Tools Used */}
      {vcr.ai_tools_used && vcr.ai_tools_used.length > 0 && (
        <div className="mb-3">
          <span className="text-xs text-gray-500">AI Tools: </span>
          <span className="text-xs text-gray-700 font-medium">
            {formatAITools(vcr.ai_tools_used)}
          </span>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span>{formatDate(vcr.created_at)}</span>
          {vcr.created_by?.name && (
            <span>by {vcr.created_by.name}</span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {vcr.status === "draft" && (
            <>
              <button
                onClick={() => onSubmit(vcr.id)}
                className="px-3 py-1 text-xs font-medium text-blue-700 bg-blue-50 rounded hover:bg-blue-100 flex items-center gap-1"
              >
                <PaperAirplaneIcon className="w-3 h-3" />
                Submit
              </button>
              <Link
                href={`/app/vcr/${vcr.id}/edit`}
                className="px-3 py-1 text-xs font-medium text-gray-700 bg-gray-50 rounded hover:bg-gray-100"
              >
                Edit
              </Link>
              <button
                onClick={() => onDelete(vcr.id)}
                className="p-1 text-gray-400 hover:text-red-600"
                title="Delete VCR"
              >
                <TrashIcon className="w-4 h-4" />
              </button>
            </>
          )}
          {vcr.status === "submitted" && (
            <span className="text-xs text-blue-600">Awaiting approval</span>
          )}
          {vcr.status === "approved" && vcr.approved_by?.name && (
            <span className="text-xs text-green-600">
              Approved by {vcr.approved_by.name}
            </span>
          )}
          {vcr.status === "rejected" && (
            <Link
              href={`/app/vcr/${vcr.id}`}
              className="text-xs text-red-600 hover:underline"
            >
              View rejection reason
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Create VCR Modal Component
// =============================================================================

function CreateVCRModal({
  projectId,
  onClose,
  onSuccess,
}: {
  projectId: string;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState<Partial<VCRCreate>>({
    project_id: projectId,
    title: "",
    problem_statement: "",
    solution_approach: "",
    ai_generated_percentage: 0,
    ai_tools_used: [],
  });
  const [aiToolInput, setAiToolInput] = useState("");

  // Auto-generate state - Sprint 151 Day 4
  const [showAutoGenerate, setShowAutoGenerate] = useState(false);
  const [autoGenInput, setAutoGenInput] = useState({
    pr_diff: "",
    commit_messages: "",
    pr_title: "",
    pr_description: "",
  });
  const [autoGenMessage, setAutoGenMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const createMutation = useCreateVcr();
  const autoGenerateMutation = useAutoGenerateVcr();

  // Handle auto-generate from PR
  const handleAutoGenerate = async () => {
    if (!autoGenInput.pr_diff && !autoGenInput.commit_messages) {
      setAutoGenMessage({ type: "error", text: "Please provide PR diff or commit messages" });
      return;
    }

    setAutoGenMessage(null);

    try {
      const request: VCRAutoGenerateRequest = {
        pr_diff: autoGenInput.pr_diff,
        commit_messages: autoGenInput.commit_messages.split("\n").filter(m => m.trim()),
        pr_title: autoGenInput.pr_title || undefined,
        pr_description: autoGenInput.pr_description || undefined,
      };

      const result = await autoGenerateMutation.mutateAsync(request);

      // Fill the form with generated content
      setFormData(prev => ({
        ...prev,
        title: result.title,
        problem_statement: result.problem_statement,
        solution_approach: result.solution_approach,
        root_cause_analysis: result.root_cause_analysis || undefined,
        implementation_notes: result.implementation_notes || undefined,
        ai_generated_percentage: result.ai_generated_percentage,
        ai_tools_used: result.ai_tools_used,
      }));

      setAutoGenMessage({
        type: "success",
        text: `Generated in ${Math.round(result.generation_time_ms)}ms (${result.provider_used}${result.fallback_used ? " - fallback" : ""}, ${Math.round(result.confidence * 100)}% confidence)`
      });
      setShowAutoGenerate(false);
    } catch {
      setAutoGenMessage({ type: "error", text: "Failed to auto-generate VCR content" });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title || !formData.problem_statement || !formData.solution_approach) {
      return;
    }

    try {
      await createMutation.mutateAsync(formData as VCRCreate);
      onSuccess();
      onClose();
    } catch {
      // Error handling is done by the mutation
    }
  };

  const addAiTool = () => {
    if (aiToolInput.trim()) {
      setFormData(prev => ({
        ...prev,
        ai_tools_used: [...(prev.ai_tools_used || []), aiToolInput.trim().toLowerCase()],
      }));
      setAiToolInput("");
    }
  };

  const removeAiTool = (tool: string) => {
    setFormData(prev => ({
      ...prev,
      ai_tools_used: (prev.ai_tools_used || []).filter(t => t !== tool),
    }));
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Create New VCR</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Auto-Generate Section - Sprint 151 Day 4 */}
          <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <SparklesIcon className="w-5 h-5 text-purple-600" />
                <h3 className="text-sm font-medium text-purple-900">AI-Assisted Generation</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowAutoGenerate(!showAutoGenerate)}
                className="text-sm text-purple-600 hover:text-purple-800 font-medium"
              >
                {showAutoGenerate ? "Hide" : "Auto-generate from PR"}
              </button>
            </div>

            {showAutoGenerate && (
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-purple-700 mb-1">
                    PR Title
                  </label>
                  <input
                    type="text"
                    value={autoGenInput.pr_title}
                    onChange={(e) => setAutoGenInput(prev => ({ ...prev, pr_title: e.target.value }))}
                    className="w-full px-3 py-2 text-sm border border-purple-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="feat: Add user authentication"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-purple-700 mb-1">
                    Commit Messages (one per line)
                  </label>
                  <textarea
                    value={autoGenInput.commit_messages}
                    onChange={(e) => setAutoGenInput(prev => ({ ...prev, commit_messages: e.target.value }))}
                    rows={2}
                    className="w-full px-3 py-2 text-sm border border-purple-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="feat: Add login API endpoint&#10;fix: Handle edge cases"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-purple-700 mb-1">
                    PR Diff (git diff output)
                  </label>
                  <textarea
                    value={autoGenInput.pr_diff}
                    onChange={(e) => setAutoGenInput(prev => ({ ...prev, pr_diff: e.target.value }))}
                    rows={4}
                    className="w-full px-3 py-2 text-sm border border-purple-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono text-xs"
                    placeholder="--- a/src/auth.py&#10;+++ b/src/auth.py&#10;@@ -1,5 +1,10 @@&#10;+def login(username, password):"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-purple-700 mb-1">
                    PR Description (optional)
                  </label>
                  <textarea
                    value={autoGenInput.pr_description}
                    onChange={(e) => setAutoGenInput(prev => ({ ...prev, pr_description: e.target.value }))}
                    rows={2}
                    className="w-full px-3 py-2 text-sm border border-purple-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="This PR adds user authentication using JWT..."
                  />
                </div>
                <button
                  type="button"
                  onClick={handleAutoGenerate}
                  disabled={autoGenerateMutation.isPending}
                  className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 text-sm font-medium flex items-center justify-center gap-2"
                >
                  {autoGenerateMutation.isPending ? (
                    <>
                      <ArrowPathIcon className="w-4 h-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <SparklesIcon className="w-4 h-4" />
                      Generate VCR Content
                    </>
                  )}
                </button>
              </div>
            )}

            {autoGenMessage && (
              <div className={`mt-2 p-2 rounded text-sm ${
                autoGenMessage.type === "success"
                  ? "bg-green-100 text-green-700"
                  : "bg-red-100 text-red-700"
              }`}>
                {autoGenMessage.text}
              </div>
            )}
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Title *
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Brief title describing the resolution"
              required
            />
          </div>

          {/* PR Number & URL */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                PR Number
              </label>
              <input
                type="number"
                value={formData.pr_number || ""}
                onChange={(e) => setFormData(prev => ({ ...prev, pr_number: e.target.value ? parseInt(e.target.value) : undefined }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="123"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                PR URL
              </label>
              <input
                type="url"
                value={formData.pr_url || ""}
                onChange={(e) => setFormData(prev => ({ ...prev, pr_url: e.target.value || undefined }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="https://github.com/..."
              />
            </div>
          </div>

          {/* Problem Statement */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Problem Statement *
            </label>
            <textarea
              value={formData.problem_statement}
              onChange={(e) => setFormData(prev => ({ ...prev, problem_statement: e.target.value }))}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="What problem was solved? Describe the issue or requirement."
              required
            />
          </div>

          {/* Root Cause Analysis */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Root Cause Analysis (for bugs)
            </label>
            <textarea
              value={formData.root_cause_analysis || ""}
              onChange={(e) => setFormData(prev => ({ ...prev, root_cause_analysis: e.target.value || undefined }))}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="What was the root cause? (Optional, for bug fixes)"
            />
          </div>

          {/* Solution Approach */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Solution Approach *
            </label>
            <textarea
              value={formData.solution_approach}
              onChange={(e) => setFormData(prev => ({ ...prev, solution_approach: e.target.value }))}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="How was it solved? Describe the implementation approach."
              required
            />
          </div>

          {/* Implementation Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Implementation Notes
            </label>
            <textarea
              value={formData.implementation_notes || ""}
              onChange={(e) => setFormData(prev => ({ ...prev, implementation_notes: e.target.value || undefined }))}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Any caveats, trade-offs, or notes for reviewers"
            />
          </div>

          {/* AI Attribution */}
          <div className="border-t border-gray-200 pt-4">
            <h3 className="text-sm font-medium text-gray-900 mb-3 flex items-center gap-2">
              <SparklesIcon className="w-4 h-4 text-purple-600" />
              AI Attribution
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  AI Generated Percentage
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={(formData.ai_generated_percentage || 0) * 100}
                    onChange={(e) => setFormData(prev => ({ ...prev, ai_generated_percentage: parseInt(e.target.value) / 100 }))}
                    className="flex-1"
                  />
                  <span className="text-sm font-medium text-gray-700 w-12 text-right">
                    {Math.round((formData.ai_generated_percentage || 0) * 100)}%
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  AI Tools Used
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={aiToolInput}
                    onChange={(e) => setAiToolInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addAiTool())}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    placeholder="e.g., cursor, copilot"
                  />
                  <button
                    type="button"
                    onClick={addAiTool}
                    className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                  >
                    Add
                  </button>
                </div>
              </div>
            </div>

            {formData.ai_tools_used && formData.ai_tools_used.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {formData.ai_tools_used.map(tool => (
                  <span
                    key={tool}
                    className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-medium flex items-center gap-1"
                  >
                    {tool}
                    <button
                      type="button"
                      onClick={() => removeAiTool(tool)}
                      className="hover:text-purple-900"
                    >
                      <XMarkIcon className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              {createMutation.isPending ? (
                <>
                  <ArrowPathIcon className="w-4 h-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <PlusIcon className="w-4 h-4" />
                  Create VCR
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

export default function VCRPage() {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [filters, setFilters] = useState<VCRListOptions>({
    limit: 20,
    offset: 0,
  });
  const [searchQuery, setSearchQuery] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Fetch projects for selector
  const { data: projects = [] } = useProjects();

  // Auto-select first project
  const effectiveProjectId = selectedProjectId || projects[0]?.id;

  // Fetch VCRs and stats
  const { data: vcrsData, isLoading: vcrsLoading, refetch } = useVcrs(
    effectiveProjectId ? { ...filters, project_id: effectiveProjectId } : filters
  );
  const { data: stats } = useVcrStats(effectiveProjectId);

  // Mutations
  const submitMutation = useSubmitVcr();
  const deleteMutation = useDeleteVcr();

  // Filter VCRs by search query
  const filteredVcrs = useMemo(() => {
    if (!vcrsData?.items) return [];
    if (!searchQuery) return vcrsData.items;
    const query = searchQuery.toLowerCase();
    return vcrsData.items.filter(
      (v) =>
        v.title.toLowerCase().includes(query) ||
        v.problem_statement.toLowerCase().includes(query) ||
        v.solution_approach.toLowerCase().includes(query)
    );
  }, [vcrsData?.items, searchQuery]);

  // Handlers
  const handleSubmit = async (vcrId: string) => {
    if (confirm("Submit this VCR for approval? You won't be able to edit it after submission.")) {
      try {
        await submitMutation.mutateAsync(vcrId);
      } catch {
        // Error handling done by mutation
      }
    }
  };

  const handleDelete = async (vcrId: string) => {
    if (confirm("Are you sure you want to delete this VCR?")) {
      try {
        await deleteMutation.mutateAsync(vcrId);
      } catch {
        // Error handling done by mutation
      }
    }
  };

  const handleFilterChange = (key: keyof VCRListOptions, value: string | undefined) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value || undefined,
      offset: 0, // Reset to first page on filter change
    }));
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <DocumentTextIcon className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Version Controlled Resolutions</h1>
                <p className="text-sm text-gray-500">
                  Sprint 151 SASE: Document changes with AI attribution for governance compliance
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Project Selector */}
              <select
                value={effectiveProjectId || ""}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select Project</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>

              {/* Create Button */}
              {effectiveProjectId && (
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium flex items-center gap-2"
                >
                  <PlusIcon className="w-4 h-4" />
                  New VCR
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatsCard
              title="Total VCRs"
              value={stats.total}
              icon={DocumentTextIcon}
              color="bg-blue-500"
            />
            <StatsCard
              title="Pending Review"
              value={stats.submitted}
              icon={ClockIcon}
              color="bg-yellow-500"
            />
            <StatsCard
              title="Approved"
              value={stats.approved}
              icon={CheckCircleIcon}
              color="bg-green-500"
            />
            <StatsCard
              title="Avg AI Involvement"
              value={`${Math.round(stats.ai_involvement_percentage * 100)}%`}
              icon={SparklesIcon}
              color="bg-purple-500"
            />
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
          <div className="flex flex-wrap gap-4">
            {/* Search */}
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search VCRs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Status Filter */}
            <select
              value={filters.status || ""}
              onChange={(e) => handleFilterChange("status", e.target.value as VCRStatus | undefined)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="draft">Draft</option>
              <option value="submitted">Pending Review</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>

            {/* Refresh Button */}
            <button
              onClick={() => refetch()}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
              title="Refresh"
            >
              <ArrowPathIcon className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* VCRs List */}
        {vcrsLoading ? (
          <div className="text-center py-12">
            <ArrowPathIcon className="w-8 h-8 text-gray-400 animate-spin mx-auto mb-4" />
            <p className="text-gray-500">Loading VCRs...</p>
          </div>
        ) : !effectiveProjectId ? (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
            <DocumentTextIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Select a Project</h3>
            <p className="text-gray-500 max-w-md mx-auto">
              Choose a project from the dropdown to view and manage VCRs.
            </p>
          </div>
        ) : filteredVcrs.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
            <DocumentTextIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No VCRs found</h3>
            <p className="text-gray-500 max-w-md mx-auto mb-4">
              {searchQuery || filters.status
                ? "Try adjusting your filters or search query."
                : "Create your first Version Controlled Resolution to document changes with AI attribution."}
            </p>
            {!searchQuery && !filters.status && (
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium inline-flex items-center gap-2"
              >
                <PlusIcon className="w-4 h-4" />
                Create First VCR
              </button>
            )}
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
              {filteredVcrs.map((vcr) => (
                <VCRCard
                  key={vcr.id}
                  vcr={vcr}
                  onSubmit={handleSubmit}
                  onDelete={handleDelete}
                />
              ))}
            </div>

            {/* Pagination */}
            {vcrsData && vcrsData.total > (filters.limit || 20) && (
              <div className="flex items-center justify-between bg-white rounded-lg border border-gray-200 p-4">
                <p className="text-sm text-gray-500">
                  Showing {(filters.offset || 0) + 1} to{" "}
                  {Math.min((filters.offset || 0) + (filters.limit || 20), vcrsData.total)} of{" "}
                  {vcrsData.total} VCRs
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setFilters((prev) => ({ ...prev, offset: Math.max(0, (prev.offset || 0) - (prev.limit || 20)) }))}
                    disabled={(filters.offset || 0) <= 0}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setFilters((prev) => ({ ...prev, offset: (prev.offset || 0) + (prev.limit || 20) }))}
                    disabled={!vcrsData.has_more}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {/* Create VCR Modal */}
      {showCreateModal && effectiveProjectId && (
        <CreateVCRModal
          projectId={effectiveProjectId}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => refetch()}
        />
      )}
    </div>
  );
}
