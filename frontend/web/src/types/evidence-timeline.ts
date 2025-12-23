/**
 * Evidence Timeline Types
 *
 * SDLC Stage: 04 - BUILD
 * Sprint: 43 - Policy Guards & Evidence UI
 * Framework: SDLC 5.1.1
 * Epic: EP-02 AI Safety Layer v1
 *
 * Purpose:
 * TypeScript interfaces for Evidence Timeline feature.
 * Maps to backend Pydantic schemas in evidence_timeline.py.
 */

// =============================================================================
// Enums
// =============================================================================

export enum AIToolType {
  CURSOR = 'cursor',
  COPILOT = 'copilot',
  CLAUDE = 'claude',
  CHATGPT = 'chatgpt',
  WINDSURF = 'windsurf',
  CODY = 'cody',
  TABNINE = 'tabnine',
  OTHER = 'other',
  MANUAL = 'manual',
}

export enum ValidationStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  PASSED = 'passed',
  FAILED = 'failed',
  OVERRIDDEN = 'overridden',
  ERROR = 'error',
}

export enum OverrideStatus {
  NONE = 'none',
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
}

export enum OverrideType {
  FALSE_POSITIVE = 'false_positive',
  APPROVED_RISK = 'approved_risk',
  EMERGENCY = 'emergency',
}

export enum ValidatorName {
  LINT = 'lint',
  TESTS = 'tests',
  COVERAGE = 'coverage',
  SAST = 'sast',
  POLICY_GUARDS = 'policy_guards',
  AI_SECURITY = 'ai_security',
}

export enum ExportFormat {
  CSV = 'csv',
  JSON = 'json',
}

// =============================================================================
// Validator Result
// =============================================================================

export interface ValidatorResultSummary {
  name: ValidatorName
  status: 'passed' | 'failed' | 'skipped' | 'error'
  duration_ms: number
  message: string | null
  details: Record<string, unknown> | null
  blocking: boolean
}

// =============================================================================
// Evidence Event
// =============================================================================

export interface EvidenceEventBase {
  // PR/Commit info
  pr_number: string
  pr_title: string
  pr_author: string
  commit_sha: string | null
  branch_name: string | null

  // AI Detection
  ai_tool: AIToolType
  ai_model: string | null
  confidence_score: number
  detection_method: string

  // Validation
  validation_status: ValidationStatus
  validation_duration_ms: number

  // Files
  files_changed: number
  lines_added: number
  lines_deleted: number
}

export interface EvidenceEventSummary extends EvidenceEventBase {
  id: string
  project_id: string
  created_at: string

  // Validators summary
  validators_passed: number
  validators_failed: number
  validators_total: number

  // Override info
  override_status: OverrideStatus
  override_requested_at: string | null
}

export interface EvidenceEventDetail extends EvidenceEventSummary {
  // Validation results
  validator_results: ValidatorResultSummary[]

  // Evidence data
  detection_evidence: Record<string, unknown>

  // Override history
  override_history: OverrideRecord[]

  // GitHub integration
  github_check_run_id: string | null
  github_pr_url: string | null
}

// =============================================================================
// Override Records
// =============================================================================

export interface OverrideRecord {
  id: string
  event_id: string

  // Request
  override_type: OverrideType
  reason: string
  requested_by_id: string
  requested_by_name: string
  requested_at: string

  // Resolution
  status: OverrideStatus
  resolved_by_id: string | null
  resolved_by_name: string | null
  resolved_at: string | null
  resolution_comment: string | null
}

export interface OverrideRequest {
  override_type: OverrideType
  reason: string
}

export interface OverrideApproval {
  comment?: string
}

export interface OverrideRejection {
  reason: string
}

// =============================================================================
// Filters and Pagination
// =============================================================================

export interface EvidenceFilters {
  date_start?: string
  date_end?: string
  ai_tool?: AIToolType
  confidence_min?: number
  confidence_max?: number
  validation_status?: ValidationStatus
  override_status?: OverrideStatus
  pr_author?: string
  search?: string
}

export interface PaginationParams {
  page: number
  limit: number
}

// =============================================================================
// Response Models
// =============================================================================

export interface EvidenceTimelineStats {
  total_events: number
  ai_detected: number
  pass_rate: number
  override_rate: number
  by_tool: Record<string, number>
  by_status: Record<string, number>
}

export interface EvidenceTimelineResponse {
  events: EvidenceEventSummary[]
  stats: EvidenceTimelineStats
  total: number
  page: number
  pages: number
  has_next: boolean
}

export interface OverrideQueueItem {
  id: string
  event_id: string

  // PR info
  pr_number: string
  pr_title: string
  project_name: string
  project_id: string

  // Request details
  override_type: OverrideType
  reason: string
  requested_by_name: string
  requested_at: string

  // Validation failures
  failed_validators: string[]
  ai_tool: AIToolType
  confidence_score: number
}

export interface OverrideQueueResponse {
  pending: OverrideQueueItem[]
  recent_decisions: OverrideRecord[]
  total_pending: number
}

// =============================================================================
// Export
// =============================================================================

export interface ExportRequest {
  format: ExportFormat
  date_start?: string
  date_end?: string
  include_details?: boolean
}

export interface ExportResponse {
  download_url: string
  format: ExportFormat
  events_count: number
  expires_at: string
}

// =============================================================================
// UI Helper Types
// =============================================================================

export interface TimelineFilterState extends EvidenceFilters, PaginationParams {}

export type ValidationStatusColor = 'green' | 'red' | 'yellow' | 'gray' | 'blue'

export const ValidationStatusColors: Record<ValidationStatus, ValidationStatusColor> = {
  [ValidationStatus.PASSED]: 'green',
  [ValidationStatus.FAILED]: 'red',
  [ValidationStatus.PENDING]: 'gray',
  [ValidationStatus.RUNNING]: 'blue',
  [ValidationStatus.OVERRIDDEN]: 'yellow',
  [ValidationStatus.ERROR]: 'red',
}

export const AIToolLabels: Record<AIToolType, string> = {
  [AIToolType.CURSOR]: 'Cursor',
  [AIToolType.COPILOT]: 'GitHub Copilot',
  [AIToolType.CLAUDE]: 'Claude',
  [AIToolType.CHATGPT]: 'ChatGPT',
  [AIToolType.WINDSURF]: 'Windsurf',
  [AIToolType.CODY]: 'Sourcegraph Cody',
  [AIToolType.TABNINE]: 'Tabnine',
  [AIToolType.OTHER]: 'Other',
  [AIToolType.MANUAL]: 'Manual',
}

export const OverrideTypeLabels: Record<OverrideType, string> = {
  [OverrideType.FALSE_POSITIVE]: 'False Positive',
  [OverrideType.APPROVED_RISK]: 'Approved Risk',
  [OverrideType.EMERGENCY]: 'Emergency',
}
