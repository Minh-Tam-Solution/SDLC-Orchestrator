/**
 * AGENTS.md TypeScript Types - SDLC Orchestrator
 *
 * @module frontend/src/lib/types/agents-md
 * @description TypeScript interfaces for AGENTS.md management (TRUE MOAT)
 * @sdlc SDLC 5.1.3 Framework - Sprint 85 (AGENTS.md UI)
 * @status Sprint 85 - AGENTS.md Frontend
 */

// =============================================================================
// Enums & Constants
// =============================================================================

/**
 * Validation status for AGENTS.md files
 */
export type ValidationStatus = "pending" | "valid" | "invalid";

/**
 * Trigger types for context overlay generation
 */
export type TriggerType = "pr_webhook" | "cli" | "api" | "scheduled" | "manual";

/**
 * Constraint severity levels
 */
export type ConstraintSeverity = "critical" | "high" | "medium" | "low";

/**
 * Diff change types
 */
export type DiffChangeType = "added" | "removed" | "modified";

// =============================================================================
// AGENTS.md Repository
// =============================================================================

/**
 * AGENTS.md repository summary (list view)
 */
export interface AgentsMdRepo {
  id: string;
  project_id: string;
  project_name: string;
  github_repo_full_name: string;
  has_agents_md: boolean;
  last_generated_at?: string;
  validation_status: ValidationStatus;
  line_count?: number;
  sections?: string[];
  is_outdated: boolean;
  /** Generator version used */
  generator_version?: string;
  /** Created timestamp */
  created_at?: string;
  /** Updated timestamp */
  updated_at?: string;
}

/**
 * Full AGENTS.md file content with metadata
 */
export interface AgentsMdFile {
  id: string;
  project_id: string;
  content: string;
  content_hash: string;
  line_count: number;
  sections: string[];
  generated_at: string;
  generated_by?: string;
  generator_version: string;
  validation_status: ValidationStatus;
  validation_errors?: ValidationError[];
  validation_warnings?: ValidationWarning[];
  /** Repository information */
  repo?: {
    full_name: string;
    default_branch: string;
    url: string;
  };
}

/**
 * AGENTS.md repo detail (full response)
 */
export interface AgentsMdRepoDetail {
  repo: AgentsMdRepo;
  file?: AgentsMdFile;
  context?: ContextOverlay;
  versions: AgentsMdVersion[];
}

/**
 * AGENTS.md version history entry
 */
export interface AgentsMdVersion {
  id: string;
  version_number: number;
  content_hash: string;
  line_count: number;
  generated_at: string;
  generated_by?: string;
  trigger_type: TriggerType;
  trigger_ref?: string;
  change_summary?: string;
}

// =============================================================================
// Validation
// =============================================================================

/**
 * Validation error
 */
export interface ValidationError {
  line?: number;
  column?: number;
  message: string;
  severity: "error";
  rule?: string;
}

/**
 * Validation warning
 */
export interface ValidationWarning {
  line?: number;
  column?: number;
  message: string;
  severity: "warning";
  rule?: string;
}

/**
 * Validation result from POST /agents-md/validate
 */
export interface ValidationResult {
  is_valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  sections_found: string[];
  line_count: number;
  missing_required_sections: string[];
  suggestions?: string[];
}

// =============================================================================
// Context Overlay (Dynamic Context - TRUE MOAT)
// =============================================================================

/**
 * Dynamic context overlay for a project
 */
export interface ContextOverlay {
  id: string;
  project_id: string;
  generated_at: string;
  /** Current SDLC stage */
  stage_name?: string;
  /** Current gate status */
  gate_status?: string;
  gate_name?: string;
  /** Current sprint information */
  sprint?: SprintContext;
  /** Active constraints */
  constraints: Constraint[];
  /** Whether strict mode is active (post-G3) */
  strict_mode: boolean;
  /** What triggered this overlay generation */
  trigger_type: TriggerType;
  /** Reference (PR number, CLI command, etc.) */
  trigger_ref?: string;
  /** Whether delivered to PR comment */
  delivered_to_pr: boolean;
  /** Whether delivered via Check Run */
  delivered_to_check_run: boolean;
  /** Known issues */
  known_issues?: KnownIssue[];
  /** Pending tasks */
  pending_tasks?: PendingTask[];
}

/**
 * Sprint context within overlay
 */
export interface SprintContext {
  id?: string;
  number?: number;
  name?: string;
  goal?: string;
  status?: "planning" | "in_progress" | "completed" | "cancelled";
  start_date?: string;
  end_date?: string;
}

/**
 * Constraint in context overlay
 */
export interface Constraint {
  type: string;
  severity: ConstraintSeverity;
  message: string;
  source?: string;
  expires_at?: string;
}

/**
 * Known issue in context
 */
export interface KnownIssue {
  id: string;
  title: string;
  severity: ConstraintSeverity;
  affected_files?: string[];
  workaround?: string;
}

/**
 * Pending task in context
 */
export interface PendingTask {
  id: string;
  title: string;
  priority: "p0" | "p1" | "p2" | "p3";
  assignee?: string;
  due_date?: string;
}

/**
 * Context history entry
 */
export interface ContextHistoryEntry {
  id: string;
  generated_at: string;
  trigger_type: TriggerType;
  trigger_ref?: string;
  strict_mode: boolean;
  constraints_count: number;
  change_summary?: string;
}

// =============================================================================
// Diff
// =============================================================================

/**
 * Diff between two AGENTS.md versions
 */
export interface AgentsMdDiff {
  old_version: string;
  new_version: string;
  old_content: string;
  new_content: string;
  old_generated_at: string;
  new_generated_at: string;
  changes: DiffChange[];
  summary: DiffSummary;
}

/**
 * Individual diff change
 */
export interface DiffChange {
  type: DiffChangeType;
  line_number: number;
  old_line?: string;
  new_line?: string;
  section?: string;
}

/**
 * Summary of diff changes
 */
export interface DiffSummary {
  lines_added: number;
  lines_removed: number;
  lines_modified: number;
  sections_added: string[];
  sections_removed: string[];
  sections_modified: string[];
}


// =============================================================================
// API Request/Response Types
// =============================================================================

/**
 * List repos response
 */
export interface AgentsMdReposResponse {
  repos: AgentsMdRepo[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Regenerate request
 */
export interface RegenerateRequest {
  force?: boolean;
  sections?: string[];
  include_context?: boolean;
}

/**
 * Regenerate response
 */
export interface RegenerateResponse {
  success: boolean;
  file: AgentsMdFile;
  context?: ContextOverlay;
  diff?: AgentsMdDiff;
}

/**
 * Bulk regenerate request
 */
export interface BulkRegenerateRequest {
  repo_ids: string[];
  force?: boolean;
  include_context?: boolean;
}

/**
 * Bulk regenerate response
 */
export interface BulkRegenerateResponse {
  total: number;
  success: number;
  failed: number;
  results: Array<{
    repo_id: string;
    success: boolean;
    error?: string;
    file?: AgentsMdFile;
  }>;
}

/**
 * Validate request
 */
export interface ValidateRequest {
  content: string;
  strict?: boolean;
}

/**
 * Export analytics request
 */
export interface ExportAnalyticsRequest {
  format: "json" | "csv";
  metrics?: string[];
  period_start?: string;
  period_end?: string;
}

// =============================================================================
// UI Helper Types
// =============================================================================

/**
 * Repo card display data
 */
export interface RepoCardData {
  id: string;
  name: string;
  fullName: string;
  status: "valid" | "invalid" | "outdated" | "missing";
  statusLabel: string;
  lastUpdated?: string;
  lineCount?: number;
  canRegenerate: boolean;
}

/**
 * Dashboard summary stats
 */
export interface DashboardStats {
  totalRepos: number;
  upToDate: number;
  outdated: number;
  missing: number;
  validRate: number;
}

// =============================================================================
// Metadata & Constants
// =============================================================================

/**
 * Validation status metadata
 */
export const VALIDATION_STATUS_META: Record<
  ValidationStatus,
  { label: string; color: string; icon: string }
> = {
  pending: { label: "Pending", color: "yellow", icon: "⏳" },
  valid: { label: "Valid", color: "green", icon: "✅" },
  invalid: { label: "Invalid", color: "red", icon: "❌" },
};

/**
 * Trigger type metadata
 */
export const TRIGGER_TYPE_META: Record<
  TriggerType,
  { label: string; description: string }
> = {
  pr_webhook: {
    label: "PR Webhook",
    description: "Triggered by Pull Request event",
  },
  cli: { label: "CLI", description: "Triggered via CLI command" },
  api: { label: "API", description: "Triggered via direct API call" },
  scheduled: { label: "Scheduled", description: "Triggered by schedule" },
  manual: { label: "Manual", description: "Manually triggered by user" },
};

/**
 * Constraint severity metadata
 */
export const SEVERITY_META: Record<
  ConstraintSeverity,
  { label: string; color: string; priority: number }
> = {
  critical: { label: "Critical", color: "red", priority: 0 },
  high: { label: "High", color: "orange", priority: 1 },
  medium: { label: "Medium", color: "yellow", priority: 2 },
  low: { label: "Low", color: "gray", priority: 3 },
};

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Get repo status from AgentsMdRepo
 */
export function getRepoStatus(
  repo: AgentsMdRepo
): "valid" | "invalid" | "outdated" | "missing" {
  if (!repo.has_agents_md) return "missing";
  if (repo.is_outdated) return "outdated";
  if (repo.validation_status === "invalid") return "invalid";
  return "valid";
}

/**
 * Get status label
 */
export function getStatusLabel(
  status: "valid" | "invalid" | "outdated" | "missing"
): string {
  const labels: Record<string, string> = {
    valid: "Up to date",
    invalid: "Invalid",
    outdated: "Outdated",
    missing: "Missing",
  };
  return labels[status] || "Unknown";
}

/**
 * Get status color for styling
 */
export function getStatusColor(
  status: "valid" | "invalid" | "outdated" | "missing"
): string {
  const colors: Record<string, string> = {
    valid: "green",
    invalid: "red",
    outdated: "yellow",
    missing: "gray",
  };
  return colors[status] || "gray";
}

/**
 * Convert repo to card data
 */
export function toRepoCardData(repo: AgentsMdRepo): RepoCardData {
  const status = getRepoStatus(repo);
  return {
    id: repo.id,
    name: repo.project_name,
    fullName: repo.github_repo_full_name,
    status,
    statusLabel: getStatusLabel(status),
    lastUpdated: repo.last_generated_at,
    lineCount: repo.line_count,
    canRegenerate: status !== "missing" || repo.has_agents_md,
  };
}

/**
 * Calculate dashboard stats from repos list
 */
export function calculateDashboardStats(repos: AgentsMdRepo[]): DashboardStats {
  const total = repos.length;
  const upToDate = repos.filter(
    (r) => r.has_agents_md && !r.is_outdated && r.validation_status === "valid"
  ).length;
  const outdated = repos.filter((r) => r.has_agents_md && r.is_outdated).length;
  const missing = repos.filter((r) => !r.has_agents_md).length;
  const valid = repos.filter((r) => r.validation_status === "valid").length;

  return {
    totalRepos: total,
    upToDate,
    outdated,
    missing,
    validRate: total > 0 ? (valid / total) * 100 : 0,
  };
}

/**
 * Sort constraints by severity
 */
export function sortConstraintsBySeverity(
  constraints: Constraint[]
): Constraint[] {
  return [...constraints].sort(
    (a, b) => SEVERITY_META[a.severity].priority - SEVERITY_META[b.severity].priority
  );
}

/**
 * Format relative time
 */
export function formatRelativeTime(dateString?: string): string {
  if (!dateString) return "Never";

  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}
