/**
 * Feedback Learnings Dashboard Page - SDLC Orchestrator
 *
 * @module frontend/src/app/app/learnings/page
 * @description EP-11 Feedback Learning dashboard for PR review insights
 * @sdlc SDLC 5.1.3 Framework - Sprint 100 (Feedback Learning Service)
 * @status Sprint 100 - EP-11 Implementation
 */

"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { useProjects } from "@/hooks/useProjects";
import {
  useLearnings,
  useLearningStats,
  useDeleteLearning,
  useApplyLearning,
  type LearningFilterParams,
  type PRLearning,
} from "@/hooks/useLearnings";

// =============================================================================
// Icon Components
// =============================================================================

function LightBulbIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 0 0 1.5-.189m-1.5.189a6.01 6.01 0 0 1-1.5-.189m3.75 7.478a12.06 12.06 0 0 1-4.5 0m3.75 2.383a14.406 14.406 0 0 1-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 1 0-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
    </svg>
  );
}

function BookOpenIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
    </svg>
  );
}

function ChartPieIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6a7.5 7.5 0 1 0 7.5 7.5h-7.5V6Z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0 0 13.5 3v7.5Z" />
    </svg>
  );
}

function CheckBadgeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 0 1-1.043 3.296 3.745 3.745 0 0 1-3.296 1.043A3.745 3.745 0 0 1 12 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 0 1-3.296-1.043 3.746 3.746 0 0 1-1.043-3.296A3.745 3.745 0 0 1 3 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 0 1 1.043-3.296 3.746 3.746 0 0 1 3.296-1.043A3.746 3.746 0 0 1 12 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 0 1 3.296 1.043 3.746 3.746 0 0 1 1.043 3.296A3.745 3.745 0 0 1 21 12Z" />
    </svg>
  );
}

// ExclamationTriangleIcon - reserved for future use in warning displays

function ArrowPathIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
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

// =============================================================================
// Helper Functions
// =============================================================================

const FEEDBACK_TYPE_LABELS: Record<string, string> = {
  pattern_violation: "Pattern Violation",
  missing_requirement: "Missing Requirement",
  edge_case: "Edge Case",
  performance: "Performance",
  security_issue: "Security Issue",
  test_coverage: "Test Coverage",
  documentation: "Documentation",
  refactoring: "Refactoring",
  other: "Other",
};

const SEVERITY_COLORS: Record<string, string> = {
  low: "bg-gray-100 text-gray-700",
  medium: "bg-yellow-100 text-yellow-700",
  high: "bg-orange-100 text-orange-700",
  critical: "bg-red-100 text-red-700",
};

const STATUS_COLORS: Record<string, string> = {
  extracted: "bg-blue-100 text-blue-700",
  reviewed: "bg-purple-100 text-purple-700",
  applied: "bg-green-100 text-green-700",
  archived: "bg-gray-100 text-gray-700",
};

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "N/A";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
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
// Learning Card Component
// =============================================================================

function LearningCard({
  learning,
  onApply,
  onDelete,
}: {
  learning: PRLearning;
  onApply: (id: string, target: "claude_md" | "decomposition" | "both") => void;
  onDelete: (id: string) => void;
}) {
  const [showApplyMenu, setShowApplyMenu] = useState(false);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={`px-2 py-1 rounded text-xs font-medium ${SEVERITY_COLORS[learning.severity]}`}>
            {learning.severity.toUpperCase()}
          </span>
          <span className={`px-2 py-1 rounded text-xs font-medium ${STATUS_COLORS[learning.status]}`}>
            {learning.status}
          </span>
          {learning.ai_extracted && (
            <span className="px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-700 flex items-center gap-1">
              <SparklesIcon className="w-3 h-3" />
              AI
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Link
            href={learning.pr_url || "#"}
            target="_blank"
            className="text-xs text-blue-600 hover:underline"
          >
            PR #{learning.pr_number}
          </Link>
        </div>
      </div>

      {/* Feedback Type */}
      <div className="mb-2">
        <span className="text-sm font-medium text-gray-700">
          {FEEDBACK_TYPE_LABELS[learning.feedback_type] || learning.feedback_type}
        </span>
        {learning.file_path && (
          <span className="ml-2 text-xs text-gray-500">
            in {learning.file_path}
          </span>
        )}
      </div>

      {/* Review Comment */}
      <p className="text-sm text-gray-600 mb-3 line-clamp-2">
        {learning.review_comment}
      </p>

      {/* Pattern Extracted */}
      {learning.pattern_extracted && (
        <div className="bg-gray-50 rounded p-2 mb-3">
          <p className="text-xs text-gray-500 mb-1">Pattern Extracted:</p>
          <p className="text-sm text-gray-700 font-mono line-clamp-2">
            {learning.pattern_extracted}
          </p>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span>{formatDate(learning.created_at)}</span>
          {learning.reviewer_github_login && (
            <span>by @{learning.reviewer_github_login}</span>
          )}
          {learning.ai_confidence && (
            <span className="flex items-center gap-1">
              Confidence: {Math.round(learning.ai_confidence * 100)}%
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Apply Button */}
          {!learning.applied_to_claude_md || !learning.applied_to_decomposition ? (
            <div className="relative">
              <button
                onClick={() => setShowApplyMenu(!showApplyMenu)}
                className="px-3 py-1 text-xs font-medium text-green-700 bg-green-50 rounded hover:bg-green-100 flex items-center gap-1"
              >
                <CheckBadgeIcon className="w-4 h-4" />
                Apply
              </button>
              {showApplyMenu && (
                <div className="absolute right-0 top-8 bg-white border border-gray-200 rounded-lg shadow-lg z-10 w-48">
                  {!learning.applied_to_claude_md && (
                    <button
                      onClick={() => {
                        onApply(learning.id, "claude_md");
                        setShowApplyMenu(false);
                      }}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50"
                    >
                      Apply to CLAUDE.md
                    </button>
                  )}
                  {!learning.applied_to_decomposition && (
                    <button
                      onClick={() => {
                        onApply(learning.id, "decomposition");
                        setShowApplyMenu(false);
                      }}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50"
                    >
                      Apply to Decomposition
                    </button>
                  )}
                  {!learning.applied_to_claude_md && !learning.applied_to_decomposition && (
                    <button
                      onClick={() => {
                        onApply(learning.id, "both");
                        setShowApplyMenu(false);
                      }}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 font-medium"
                    >
                      Apply to Both
                    </button>
                  )}
                </div>
              )}
            </div>
          ) : (
            <span className="text-xs text-green-600 flex items-center gap-1">
              <CheckBadgeIcon className="w-4 h-4" />
              Applied
            </span>
          )}

          {/* Delete Button */}
          <button
            onClick={() => onDelete(learning.id)}
            className="p-1 text-gray-400 hover:text-red-600"
            title="Delete learning"
          >
            <TrashIcon className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Main Page Component
// =============================================================================

export default function LearningsPage() {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [filters, setFilters] = useState<LearningFilterParams>({
    page: 1,
    per_page: 20,
  });
  const [searchQuery, setSearchQuery] = useState("");

  // Fetch projects for selector
  const { data: projects = [] } = useProjects();

  // Auto-select first project
  const effectiveProjectId = selectedProjectId || projects[0]?.id;

  // Fetch learnings and stats
  const { data: learningsData, isLoading: learningsLoading, refetch } = useLearnings(
    effectiveProjectId,
    filters
  );
  const { data: stats } = useLearningStats(effectiveProjectId);

  // Mutations
  const applyMutation = useApplyLearning(effectiveProjectId || "");
  const deleteMutation = useDeleteLearning(effectiveProjectId || "");

  // Filter learnings by search query
  const filteredLearnings = useMemo(() => {
    if (!learningsData?.items) return [];
    if (!searchQuery) return learningsData.items;
    const query = searchQuery.toLowerCase();
    return learningsData.items.filter(
      (l) =>
        l.review_comment.toLowerCase().includes(query) ||
        l.pattern_extracted?.toLowerCase().includes(query) ||
        l.file_path?.toLowerCase().includes(query) ||
        l.pr_title?.toLowerCase().includes(query)
    );
  }, [learningsData?.items, searchQuery]);

  // Handlers
  const handleApply = (learningId: string, target: "claude_md" | "decomposition" | "both") => {
    applyMutation.mutate({ learningId, target });
  };

  const handleDelete = (learningId: string) => {
    if (confirm("Are you sure you want to delete this learning?")) {
      deleteMutation.mutate(learningId);
    }
  };

  const handleFilterChange = (key: keyof LearningFilterParams, value: string | undefined) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value || undefined,
      page: 1, // Reset to first page on filter change
    }));
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <LightBulbIcon className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Feedback Learnings</h1>
                <p className="text-sm text-gray-500">
                  EP-11: Extract patterns from PR reviews to improve AI code generation
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Project Selector */}
              <select
                value={effectiveProjectId || ""}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="">Select Project</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>

              {/* Quick Links */}
              <Link
                href="/app/learnings/hints"
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm font-medium"
              >
                View Hints
              </Link>
              <Link
                href="/app/learnings/aggregations"
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm font-medium"
              >
                Aggregations
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatsCard
              title="Total Learnings"
              value={stats.total_learnings}
              icon={BookOpenIcon}
              color="bg-blue-500"
            />
            <StatsCard
              title="AI Extracted"
              value={stats.ai_extracted_count}
              icon={SparklesIcon}
              color="bg-purple-500"
            />
            <StatsCard
              title="Applied to CLAUDE.md"
              value={stats.applied_to_claude_md}
              icon={CheckBadgeIcon}
              color="bg-green-500"
            />
            <StatsCard
              title="Decomposition Hints"
              value={stats.applied_to_decomposition}
              icon={ChartPieIcon}
              color="bg-orange-500"
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
                  placeholder="Search learnings..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
            </div>

            {/* Feedback Type Filter */}
            <select
              value={filters.feedback_type || ""}
              onChange={(e) => handleFilterChange("feedback_type", e.target.value as LearningFilterParams["feedback_type"])}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="">All Types</option>
              <option value="pattern_violation">Pattern Violation</option>
              <option value="missing_requirement">Missing Requirement</option>
              <option value="edge_case">Edge Case</option>
              <option value="performance">Performance</option>
              <option value="security_issue">Security Issue</option>
              <option value="test_coverage">Test Coverage</option>
              <option value="documentation">Documentation</option>
              <option value="refactoring">Refactoring</option>
            </select>

            {/* Severity Filter */}
            <select
              value={filters.severity || ""}
              onChange={(e) => handleFilterChange("severity", e.target.value as LearningFilterParams["severity"])}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>

            {/* Status Filter */}
            <select
              value={filters.status || ""}
              onChange={(e) => handleFilterChange("status", e.target.value as LearningFilterParams["status"])}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="">All Statuses</option>
              <option value="extracted">Extracted</option>
              <option value="reviewed">Reviewed</option>
              <option value="applied">Applied</option>
              <option value="archived">Archived</option>
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

        {/* Learnings List */}
        {learningsLoading ? (
          <div className="text-center py-12">
            <ArrowPathIcon className="w-8 h-8 text-gray-400 animate-spin mx-auto mb-4" />
            <p className="text-gray-500">Loading learnings...</p>
          </div>
        ) : filteredLearnings.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
            <LightBulbIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No learnings found</h3>
            <p className="text-gray-500 max-w-md mx-auto">
              {searchQuery || Object.keys(filters).length > 2
                ? "Try adjusting your filters or search query."
                : "Learnings are automatically extracted from PR review comments when PRs are merged."}
            </p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
              {filteredLearnings.map((learning) => (
                <LearningCard
                  key={learning.id}
                  learning={learning}
                  onApply={handleApply}
                  onDelete={handleDelete}
                />
              ))}
            </div>

            {/* Pagination */}
            {learningsData && learningsData.total > (filters.per_page || 20) && (
              <div className="flex items-center justify-between bg-white rounded-lg border border-gray-200 p-4">
                <p className="text-sm text-gray-500">
                  Showing {((filters.page || 1) - 1) * (filters.per_page || 20) + 1} to{" "}
                  {Math.min((filters.page || 1) * (filters.per_page || 20), learningsData.total)} of{" "}
                  {learningsData.total} learnings
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setFilters((prev) => ({ ...prev, page: (prev.page || 1) - 1 }))}
                    disabled={(filters.page || 1) <= 1}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setFilters((prev) => ({ ...prev, page: (prev.page || 1) + 1 }))}
                    disabled={!learningsData.has_next}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}

        {/* Summary Section */}
        {stats && (
          <div className="mt-8 bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Feedback Distribution</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(stats.by_feedback_type).map(([type, count]) => (
                <div key={type} className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-semibold text-gray-900">{count}</p>
                  <p className="text-sm text-gray-500">
                    {FEEDBACK_TYPE_LABELS[type] || type}
                  </p>
                </div>
              ))}
            </div>

            {stats.top_patterns && stats.top_patterns.length > 0 && (
              <div className="mt-6">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Top Patterns</h4>
                <div className="space-y-2">
                  {stats.top_patterns.slice(0, 5).map((item, i) => (
                    <div key={i} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-600 truncate max-w-[80%]">
                        {item.pattern}
                      </span>
                      <span className="text-sm font-medium text-gray-900">{item.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
