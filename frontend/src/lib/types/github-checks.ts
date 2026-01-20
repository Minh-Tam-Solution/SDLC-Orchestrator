/**
 * GitHub Checks Types - SDLC Orchestrator
 *
 * @module frontend/src/lib/types/github-checks
 * @description TypeScript interfaces for GitHub Check Run API (P0 Blocker)
 * @sdlc SDLC 5.1.3 Framework - Sprint 86 (GitHub Check Run UI)
 * @status Sprint 86 - CTO APPROVED (January 20, 2026)
 */

// =============================================================================
// Enforcement Modes (Sprint 82 Enhancement)
// =============================================================================

/**
 * Check Run enforcement mode
 * - ADVISORY: Posts Check Run but doesn't block merge (default)
 * - BLOCKING: Blocks merge if gates fail (via branch protection)
 * - STRICT: Blocks merge + requires approval for bypass
 */
export type CheckRunMode = "advisory" | "blocking" | "strict";

/**
 * Check Run status
 */
export type CheckRunStatus = "queued" | "in_progress" | "completed";

/**
 * Check Run conclusion
 * - success: Gates passed (green checkmark)
 * - failure: Gates failed + blocking mode (red X)
 * - neutral: Gates failed but advisory mode (gray circle)
 * - action_required: Gates failed + strict mode (yellow)
 * - cancelled: Check was cancelled
 * - timed_out: Check timed out
 * - skipped: Check was skipped
 */
export type CheckRunConclusion =
  | "success"
  | "failure"
  | "neutral"
  | "action_required"
  | "cancelled"
  | "timed_out"
  | "skipped";

/**
 * Annotation level for file-level feedback
 */
export type AnnotationLevel = "notice" | "warning" | "failure";

// =============================================================================
// Check Run Models
// =============================================================================

/**
 * Check Run annotation for file-level feedback
 */
export interface CheckRunAnnotation {
  path: string;
  start_line: number;
  end_line: number;
  annotation_level: AnnotationLevel;
  message: string;
  title: string;
}

/**
 * Check Run output with summary and annotations
 */
export interface CheckRunOutput {
  title: string;
  summary: string;
  text?: string;
  annotations: CheckRunAnnotation[];
}

/**
 * GitHub Check Run result
 */
export interface CheckRun {
  id: string;
  check_run_id: number;
  project_id: string;
  repository_full_name: string;
  head_sha: string;
  pr_number?: number;
  pr_title?: string;
  pr_url?: string;
  status: CheckRunStatus;
  conclusion?: CheckRunConclusion;
  mode: CheckRunMode;
  bypassed: boolean;
  html_url: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  output?: CheckRunOutput;
}

/**
 * Check Run list item (simplified for list view)
 */
export interface CheckRunListItem {
  id: string;
  check_run_id: number;
  repository_full_name: string;
  head_sha: string;
  pr_number?: number;
  pr_title?: string;
  status: CheckRunStatus;
  conclusion?: CheckRunConclusion;
  mode: CheckRunMode;
  bypassed: boolean;
  html_url: string;
  created_at: string;
  completed_at?: string;
}

/**
 * Check Run detail with gate results
 */
export interface CheckRunDetail extends CheckRun {
  gate_result?: GateEvaluationResult;
  overlay?: ContextOverlaySummary;
  annotations_count: number;
  duration_ms?: number;
}

// =============================================================================
// Gate Evaluation
// =============================================================================

/**
 * Gate evaluation result from Check Run
 */
export interface GateEvaluationResult {
  passed: boolean;
  evaluated_at: string;
  issues: GateIssue[];
  gates_evaluated: number;
  gates_passed: number;
  gates_failed: number;
}

/**
 * Individual gate issue
 */
export interface GateIssue {
  file_path: string;
  line_number: number;
  severity: "info" | "warning" | "error";
  message: string;
  code: string;
  rule_id?: string;
}

// =============================================================================
// Context Overlay Summary
// =============================================================================

/**
 * Context overlay summary for Check Run
 */
export interface ContextOverlaySummary {
  stage_name: string;
  gate_status: string;
  strict_mode: boolean;
  sprint?: {
    number: number;
    goal: string;
    days_remaining: number;
  };
  constraints_count: number;
}

// =============================================================================
// API Request/Response Types
// =============================================================================

/**
 * Check Run list params
 */
export interface CheckRunListParams {
  page?: number;
  page_size?: number;
  project_id?: string;
  repository?: string;
  status?: CheckRunStatus;
  conclusion?: CheckRunConclusion;
  mode?: CheckRunMode;
  from_date?: string;
  to_date?: string;
}

/**
 * Check Run list response
 */
export interface CheckRunsResponse {
  items: CheckRunListItem[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

/**
 * Create Check Run request
 */
export interface CreateCheckRunRequest {
  project_id: string;
  repo_owner: string;
  repo_name: string;
  head_sha: string;
  pr_number?: number;
  mode?: CheckRunMode;
}

/**
 * Create Check Run response
 */
export interface CreateCheckRunResponse {
  check_run_id: number;
  status: CheckRunStatus;
  conclusion?: CheckRunConclusion;
  html_url: string;
}

/**
 * Re-run Check Run request
 */
export interface RerunCheckRunRequest {
  check_run_id: string;
  force?: boolean;
}

/**
 * Check Run statistics
 */
export interface CheckRunStats {
  total_runs: number;
  passed_runs: number;
  failed_runs: number;
  bypassed_runs: number;
  advisory_runs: number;
  blocking_runs: number;
  strict_runs: number;
  avg_duration_ms: number;
  pass_rate: number;
  period_start?: string;
  period_end?: string;
}

/**
 * Project Check Run configuration
 */
export interface ProjectCheckRunConfig {
  project_id: string;
  mode: CheckRunMode;
  auto_create_on_pr: boolean;
  require_status_check: boolean;
  bypass_label?: string;
  updated_at: string;
}

/**
 * Update project Check Run config request
 */
export interface UpdateCheckRunConfigRequest {
  mode?: CheckRunMode;
  auto_create_on_pr?: boolean;
  require_status_check?: boolean;
  bypass_label?: string;
}

// =============================================================================
// UI Helper Types
// =============================================================================

/**
 * Check Run mode metadata for UI
 */
export interface CheckRunModeMetadata {
  mode: CheckRunMode;
  label: string;
  description: string;
  icon: string;
  color: string;
  bgColor: string;
}

/**
 * Check Run conclusion metadata for UI
 */
export interface CheckRunConclusionMetadata {
  conclusion: CheckRunConclusion;
  label: string;
  description: string;
  icon: string;
  color: string;
  bgColor: string;
}

// =============================================================================
// Constants & Helpers
// =============================================================================

/**
 * Check Run mode metadata
 */
export const CHECK_RUN_MODES: CheckRunModeMetadata[] = [
  {
    mode: "advisory",
    label: "Advisory",
    description:
      "Check results are informational only and do not block merge",
    icon: "ℹ️",
    color: "text-blue-600",
    bgColor: "bg-blue-50",
  },
  {
    mode: "blocking",
    label: "Blocking",
    description:
      "Merge will be blocked if gates fail (configure via branch protection)",
    icon: "🛡️",
    color: "text-orange-600",
    bgColor: "bg-orange-50",
  },
  {
    mode: "strict",
    label: "Strict",
    description:
      "Merge blocked + manual approval required to bypass failing gates",
    icon: "🔒",
    color: "text-red-600",
    bgColor: "bg-red-50",
  },
];

/**
 * Check Run conclusion metadata
 */
export const CHECK_RUN_CONCLUSIONS: CheckRunConclusionMetadata[] = [
  {
    conclusion: "success",
    label: "Success",
    description: "All gates passed",
    icon: "✅",
    color: "text-green-600",
    bgColor: "bg-green-50",
  },
  {
    conclusion: "failure",
    label: "Failed",
    description: "Gates failed and merge is blocked",
    icon: "❌",
    color: "text-red-600",
    bgColor: "bg-red-50",
  },
  {
    conclusion: "neutral",
    label: "Neutral",
    description: "Gates failed but advisory mode (not blocking)",
    icon: "⚪",
    color: "text-gray-600",
    bgColor: "bg-gray-50",
  },
  {
    conclusion: "action_required",
    label: "Action Required",
    description: "Gates failed and requires manual approval",
    icon: "🟡",
    color: "text-yellow-600",
    bgColor: "bg-yellow-50",
  },
  {
    conclusion: "cancelled",
    label: "Cancelled",
    description: "Check was cancelled",
    icon: "🚫",
    color: "text-gray-500",
    bgColor: "bg-gray-50",
  },
  {
    conclusion: "timed_out",
    label: "Timed Out",
    description: "Check timed out",
    icon: "⏱️",
    color: "text-orange-500",
    bgColor: "bg-orange-50",
  },
  {
    conclusion: "skipped",
    label: "Skipped",
    description: "Check was skipped",
    icon: "⏭️",
    color: "text-gray-400",
    bgColor: "bg-gray-50",
  },
];

/**
 * Get mode metadata
 */
export function getModeMetadata(mode: CheckRunMode): CheckRunModeMetadata {
  return (
    CHECK_RUN_MODES.find((m) => m.mode === mode) ?? {
      mode: "advisory",
      label: "Advisory",
      description: "Unknown mode",
      icon: "ℹ️",
      color: "text-gray-600",
      bgColor: "bg-gray-50",
    }
  );
}

/**
 * Get conclusion metadata
 */
export function getConclusionMetadata(
  conclusion?: CheckRunConclusion
): CheckRunConclusionMetadata {
  if (!conclusion) {
    return {
      conclusion: "neutral",
      label: "Pending",
      description: "Check is still running",
      icon: "🔄",
      color: "text-blue-500",
      bgColor: "bg-blue-50",
    };
  }
  return (
    CHECK_RUN_CONCLUSIONS.find((c) => c.conclusion === conclusion) ?? {
      conclusion: "neutral",
      label: "Unknown",
      description: "Unknown conclusion",
      icon: "❓",
      color: "text-gray-600",
      bgColor: "bg-gray-50",
    }
  );
}

/**
 * Get status label
 */
export function getStatusLabel(status: CheckRunStatus): string {
  switch (status) {
    case "queued":
      return "Queued";
    case "in_progress":
      return "In Progress";
    case "completed":
      return "Completed";
    default:
      return "Unknown";
  }
}

/**
 * Format duration in milliseconds to human-readable
 */
export function formatDuration(ms?: number): string {
  if (!ms) return "N/A";
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.round((ms % 60000) / 1000);
  return `${minutes}m ${seconds}s`;
}

/**
 * Format relative time
 */
export function formatRelativeTime(dateString?: string): string {
  if (!dateString) return "N/A";
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

/**
 * Get short SHA (first 7 characters)
 */
export function getShortSha(sha: string): string {
  return sha.slice(0, 7);
}

/**
 * Check if Check Run can be re-run
 */
export function canRerun(checkRun: CheckRunListItem | CheckRun): boolean {
  return checkRun.status === "completed";
}

/**
 * Check if Check Run is blocking
 */
export function isBlocking(checkRun: CheckRunListItem | CheckRun): boolean {
  return (
    checkRun.mode === "blocking" ||
    checkRun.mode === "strict"
  );
}
