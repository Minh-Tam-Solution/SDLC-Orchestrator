/**
 * Override Types - VCR (Version Controlled Resolution) Flow
 *
 * SDLC Stage: 04 - BUILD
 * Sprint: 43 - Policy Guards & Evidence UI
 * Framework: SDLC 5.1.1
 * Epic: EP-02 AI Safety Layer v1
 *
 * Purpose:
 * TypeScript interfaces for VCR Override Flow.
 * Maps to backend Pydantic schemas in override.py.
 */

import type { AIToolType, OverrideType, OverrideStatus } from './evidence-timeline'

// Re-export for convenience
export { OverrideType, OverrideStatus } from './evidence-timeline'

// =============================================================================
// Additional Override Enums
// =============================================================================

export enum OverrideAuditAction {
  REQUEST_CREATED = 'request_created',
  REQUEST_UPDATED = 'request_updated',
  REQUEST_CANCELLED = 'request_cancelled',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  EXPIRED = 'expired',
  ESCALATED = 'escalated',
  COMMENT_ADDED = 'comment_added',
}

// Extended status for VCR flow (includes expired/cancelled)
export enum VCROverrideStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  EXPIRED = 'expired',
  CANCELLED = 'cancelled',
}

// =============================================================================
// User Types
// =============================================================================

export interface UserBrief {
  id: string
  username: string
  display_name: string | null
}

// =============================================================================
// Request Types
// =============================================================================

export interface OverrideRequestCreate {
  event_id: string
  override_type: OverrideType
  reason: string
}

export interface OverrideApprovalRequest {
  comment?: string
}

export interface OverrideRejectionRequest {
  reason: string
}

export interface OverrideCancellationRequest {
  reason?: string
}

// =============================================================================
// Response Types
// =============================================================================

export interface OverrideAuditLogResponse {
  id: string
  action: OverrideAuditAction
  action_by: UserBrief | null
  action_at: string
  previous_status: VCROverrideStatus | null
  new_status: VCROverrideStatus | null
  comment: string | null
  ip_address: string | null
}

export interface OverrideResponse {
  id: string
  event_id: string
  project_id: string
  override_type: OverrideType
  reason: string
  status: VCROverrideStatus

  // Requester
  requested_by: UserBrief | null
  requested_at: string

  // Resolution
  resolved_by: UserBrief | null
  resolved_at: string | null
  resolution_comment: string | null

  // PR info (denormalized)
  pr_number: string | null
  pr_title: string | null
  failed_validators: string[]

  // Expiry
  expires_at: string | null
  is_expired: boolean

  // Emergency override
  post_merge_review_required: boolean
  post_merge_review_completed: boolean
  post_merge_reviewed_at: string | null

  // Timestamps
  created_at: string
  updated_at: string

  // Audit trail
  audit_logs: OverrideAuditLogResponse[]
}

export interface OverrideSummary {
  id: string
  event_id: string
  project_id: string
  override_type: OverrideType
  status: VCROverrideStatus
  pr_number: string | null
  pr_title: string | null
  requested_by_name: string | null
  requested_at: string
  resolved_at: string | null
}

// =============================================================================
// Queue Types
// =============================================================================

export interface VCRQueueItem {
  id: string
  event_id: string
  project_id: string
  project_name: string

  // Request details
  override_type: OverrideType
  reason: string
  status: VCROverrideStatus

  // PR info
  pr_number: string | null
  pr_title: string | null

  // Requester
  requested_by_name: string
  requested_at: string

  // Validation info
  failed_validators: string[]
  ai_tool: AIToolType | null
  confidence_score: number | null

  // Expiry
  expires_at: string | null
  hours_until_expiry: number | null
}

export interface RecentDecision {
  id: string
  event_id: string
  project_name: string
  override_type: OverrideType
  status: VCROverrideStatus
  pr_number: string | null
  requested_by_name: string
  resolved_by_name: string | null
  resolved_at: string | null
  resolution_comment: string | null
}

export interface VCRQueueResponse {
  pending: VCRQueueItem[]
  recent_decisions: RecentDecision[]
  total_pending: number
}

// =============================================================================
// Statistics Types
// =============================================================================

export interface OverrideStats {
  total_requests: number
  pending_count: number
  approved_count: number
  rejected_count: number
  expired_count: number
  cancelled_count: number

  // Rates
  approval_rate: number
  rejection_rate: number

  // Timing
  avg_resolution_hours: number

  // By type breakdown
  by_type: Record<string, number>

  // Emergency override tracking
  emergency_total: number
  emergency_pending_review: number
}

export interface OverrideStatsResponse {
  stats: OverrideStats
  period_days: number
  generated_at: string
}

// =============================================================================
// Filter Types
// =============================================================================

export interface OverrideListFilters {
  status?: VCROverrideStatus
  override_type?: OverrideType
  requested_by_id?: string
  date_start?: string
  date_end?: string
  pr_number?: string
}

export interface OverrideListResponse {
  overrides: OverrideSummary[]
  total: number
  page: number
  pages: number
  has_next: boolean
}

// =============================================================================
// UI Helper Types
// =============================================================================

export type VCRStatusColor = 'green' | 'red' | 'yellow' | 'gray' | 'orange'

export const VCRStatusColors: Record<VCROverrideStatus, VCRStatusColor> = {
  [VCROverrideStatus.PENDING]: 'yellow',
  [VCROverrideStatus.APPROVED]: 'green',
  [VCROverrideStatus.REJECTED]: 'red',
  [VCROverrideStatus.EXPIRED]: 'gray',
  [VCROverrideStatus.CANCELLED]: 'gray',
}

export const VCRStatusLabels: Record<VCROverrideStatus, string> = {
  [VCROverrideStatus.PENDING]: 'Pending Review',
  [VCROverrideStatus.APPROVED]: 'Approved',
  [VCROverrideStatus.REJECTED]: 'Rejected',
  [VCROverrideStatus.EXPIRED]: 'Expired',
  [VCROverrideStatus.CANCELLED]: 'Cancelled',
}

export const OverrideTypeLabels: Record<OverrideType, string> = {
  [OverrideType.FALSE_POSITIVE]: 'False Positive',
  [OverrideType.APPROVED_RISK]: 'Approved Risk',
  [OverrideType.EMERGENCY]: 'Emergency',
}

export const OverrideTypeDescriptions: Record<OverrideType, string> = {
  [OverrideType.FALSE_POSITIVE]: 'The validation failure is a false positive',
  [OverrideType.APPROVED_RISK]: 'Risk has been reviewed and accepted',
  [OverrideType.EMERGENCY]: 'Critical hotfix requiring immediate merge',
}

export const OverrideAuditActionLabels: Record<OverrideAuditAction, string> = {
  [OverrideAuditAction.REQUEST_CREATED]: 'Request Created',
  [OverrideAuditAction.REQUEST_UPDATED]: 'Request Updated',
  [OverrideAuditAction.REQUEST_CANCELLED]: 'Request Cancelled',
  [OverrideAuditAction.APPROVED]: 'Approved',
  [OverrideAuditAction.REJECTED]: 'Rejected',
  [OverrideAuditAction.EXPIRED]: 'Expired',
  [OverrideAuditAction.ESCALATED]: 'Escalated',
  [OverrideAuditAction.COMMENT_ADDED]: 'Comment Added',
}

// =============================================================================
// Utility Functions
// =============================================================================

export function isOverridePending(status: VCROverrideStatus): boolean {
  return status === VCROverrideStatus.PENDING
}

export function isOverrideResolved(status: VCROverrideStatus): boolean {
  return [
    VCROverrideStatus.APPROVED,
    VCROverrideStatus.REJECTED,
    VCROverrideStatus.EXPIRED,
    VCROverrideStatus.CANCELLED,
  ].includes(status)
}

export function isEmergencyOverride(type: OverrideType): boolean {
  return type === OverrideType.EMERGENCY
}

export function formatTimeUntilExpiry(hoursUntilExpiry: number | null): string {
  if (hoursUntilExpiry === null) return 'N/A'
  if (hoursUntilExpiry <= 0) return 'Expired'
  if (hoursUntilExpiry < 24) return `${Math.round(hoursUntilExpiry)}h`
  const days = Math.floor(hoursUntilExpiry / 24)
  return `${days}d`
}
