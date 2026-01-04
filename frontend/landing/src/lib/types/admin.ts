/**
 * Admin Types - Next.js App Router
 * @module frontend/landing/src/lib/types/admin
 * @status Sprint 68 - Admin Section Migration
 * @description Type definitions for admin panel functionality
 * @note Uses httpOnly cookies for auth (Sprint 63 migration)
 */

// =========================================================================
// Dashboard Stats
// =========================================================================

export interface AdminDashboardStats {
  total_users: number;
  active_users: number;
  inactive_users: number;
  superusers: number;
  total_projects: number;
  total_gates: number;
  active_projects: number;
  system_status: SystemStatus;
}

export type SystemStatus = "healthy" | "degraded" | "unhealthy";

// =========================================================================
// User Management
// =========================================================================

export interface AdminUser {
  id: string;
  email: string;
  name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  last_login: string | null;
}

export interface AdminUserDetail extends AdminUser {
  avatar_url: string | null;
  mfa_enabled: boolean;
  oauth_providers: string[];
  project_count: number;
  updated_at: string;
}

export interface AdminUserCreate {
  email: string;
  password: string;
  name?: string;
  is_active?: boolean;
  is_superuser?: boolean;
}

export interface AdminUserUpdate {
  name?: string;
  is_active?: boolean;
  is_superuser?: boolean;
}

export interface AdminUserUpdateFull {
  email?: string;
  name?: string;
  is_active?: boolean;
  is_superuser?: boolean;
  new_password?: string;
}

export interface AdminUserListResponse {
  items: AdminUser[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface AdminUserListParams {
  page?: number;
  page_size?: number;
  search?: string;
  is_active?: boolean;
  is_superuser?: boolean;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

// Bulk Actions
export type BulkUserAction = "activate" | "deactivate";

export interface BulkUserActionRequest {
  user_ids: string[];
  action: BulkUserAction;
}

export interface BulkUserActionResponse {
  success_count: number;
  failed_count: number;
  failed_users: Array<{ user_id: string; reason: string }>;
}

export interface BulkDeleteRequest {
  user_ids: string[];
}

export interface BulkDeleteResponse {
  success_count: number;
  failed_count: number;
  deleted_users: Array<{ user_id: string; email: string }>;
  failed_users: Array<{ user_id: string; reason: string }>;
}

// =========================================================================
// Audit Logs
// =========================================================================

export type AuditAction =
  | "USER_LOGIN"
  | "USER_LOGOUT"
  | "USER_CREATED"
  | "USER_UPDATED"
  | "USER_DELETED"
  | "USER_ACTIVATED"
  | "USER_DEACTIVATED"
  | "PROJECT_CREATED"
  | "PROJECT_UPDATED"
  | "PROJECT_DELETED"
  | "GATE_PASSED"
  | "GATE_FAILED"
  | "GATE_OVERRIDDEN"
  | "EVIDENCE_UPLOADED"
  | "EVIDENCE_DELETED"
  | "POLICY_CREATED"
  | "POLICY_UPDATED"
  | "POLICY_DELETED"
  | "SETTING_UPDATED"
  | "SETTING_ROLLBACK"
  | "SOP_CREATED"
  | "SOP_UPDATED"
  | "SOP_DELETED"
  | "CODE_GENERATED"
  | "OVERRIDE_APPROVED"
  | "OVERRIDE_REJECTED";

export interface AuditLogItem {
  id: string;
  timestamp: string;
  action: AuditAction;
  actor_id: string | null;
  actor_email: string | null;
  target_type: string | null;
  target_id: string | null;
  target_name: string | null;
  details: Record<string, unknown>;
  ip_address: string | null;
}

export interface AuditLogListResponse {
  items: AuditLogItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface AuditLogParams {
  page?: number;
  page_size?: number;
  action?: AuditAction | string;
  actor_id?: string;
  target_type?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
}

// Action metadata for UI
export const AUDIT_ACTION_META: Record<
  AuditAction,
  { label: string; color: string; icon: string }
> = {
  USER_LOGIN: { label: "User Login", color: "bg-green-100 text-green-800", icon: "LogIn" },
  USER_LOGOUT: { label: "User Logout", color: "bg-gray-100 text-gray-800", icon: "LogOut" },
  USER_CREATED: { label: "User Created", color: "bg-blue-100 text-blue-800", icon: "UserPlus" },
  USER_UPDATED: { label: "User Updated", color: "bg-yellow-100 text-yellow-800", icon: "UserCog" },
  USER_DELETED: { label: "User Deleted", color: "bg-red-100 text-red-800", icon: "UserMinus" },
  USER_ACTIVATED: { label: "User Activated", color: "bg-green-100 text-green-800", icon: "UserCheck" },
  USER_DEACTIVATED: { label: "User Deactivated", color: "bg-orange-100 text-orange-800", icon: "UserX" },
  PROJECT_CREATED: { label: "Project Created", color: "bg-blue-100 text-blue-800", icon: "FolderPlus" },
  PROJECT_UPDATED: { label: "Project Updated", color: "bg-yellow-100 text-yellow-800", icon: "FolderEdit" },
  PROJECT_DELETED: { label: "Project Deleted", color: "bg-red-100 text-red-800", icon: "FolderMinus" },
  GATE_PASSED: { label: "Gate Passed", color: "bg-green-100 text-green-800", icon: "CheckCircle" },
  GATE_FAILED: { label: "Gate Failed", color: "bg-red-100 text-red-800", icon: "XCircle" },
  GATE_OVERRIDDEN: { label: "Gate Overridden", color: "bg-orange-100 text-orange-800", icon: "AlertTriangle" },
  EVIDENCE_UPLOADED: { label: "Evidence Uploaded", color: "bg-blue-100 text-blue-800", icon: "Upload" },
  EVIDENCE_DELETED: { label: "Evidence Deleted", color: "bg-red-100 text-red-800", icon: "Trash2" },
  POLICY_CREATED: { label: "Policy Created", color: "bg-purple-100 text-purple-800", icon: "FilePlus" },
  POLICY_UPDATED: { label: "Policy Updated", color: "bg-yellow-100 text-yellow-800", icon: "FileEdit" },
  POLICY_DELETED: { label: "Policy Deleted", color: "bg-red-100 text-red-800", icon: "FileX" },
  SETTING_UPDATED: { label: "Setting Updated", color: "bg-yellow-100 text-yellow-800", icon: "Settings" },
  SETTING_ROLLBACK: { label: "Setting Rollback", color: "bg-orange-100 text-orange-800", icon: "RotateCcw" },
  SOP_CREATED: { label: "SOP Created", color: "bg-blue-100 text-blue-800", icon: "FileText" },
  SOP_UPDATED: { label: "SOP Updated", color: "bg-yellow-100 text-yellow-800", icon: "FileEdit" },
  SOP_DELETED: { label: "SOP Deleted", color: "bg-red-100 text-red-800", icon: "FileX" },
  CODE_GENERATED: { label: "Code Generated", color: "bg-purple-100 text-purple-800", icon: "Code" },
  OVERRIDE_APPROVED: { label: "Override Approved", color: "bg-green-100 text-green-800", icon: "Check" },
  OVERRIDE_REJECTED: { label: "Override Rejected", color: "bg-red-100 text-red-800", icon: "X" },
};

// Common audit actions for filtering
export const COMMON_AUDIT_ACTIONS: AuditAction[] = [
  "USER_LOGIN",
  "USER_CREATED",
  "USER_DELETED",
  "PROJECT_CREATED",
  "GATE_PASSED",
  "GATE_FAILED",
  "EVIDENCE_UPLOADED",
  "SETTING_UPDATED",
  "CODE_GENERATED",
];

// =========================================================================
// System Settings
// =========================================================================

export type SettingCategory =
  | "security"
  | "limits"
  | "features"
  | "notifications"
  | "general";

export interface SystemSetting {
  key: string;
  value: unknown;
  version: number;
  category: SettingCategory;
  description: string | null;
  updated_at: string;
  updated_by: string | null;
}

export interface SystemSettingsResponse {
  security: SystemSetting[];
  limits: SystemSetting[];
  features: SystemSetting[];
  notifications: SystemSetting[];
  general: SystemSetting[];
}

export interface SystemSettingUpdate {
  value: unknown;
}

// Setting category metadata
export const SETTING_CATEGORY_META: Record<
  SettingCategory,
  { label: string; color: string; description: string }
> = {
  security: {
    label: "Security",
    color: "bg-red-100 text-red-800",
    description: "Authentication, authorization, and security settings",
  },
  limits: {
    label: "Limits",
    color: "bg-yellow-100 text-yellow-800",
    description: "Rate limits, quotas, and resource constraints",
  },
  features: {
    label: "Features",
    color: "bg-blue-100 text-blue-800",
    description: "Feature flags and toggles",
  },
  notifications: {
    label: "Notifications",
    color: "bg-purple-100 text-purple-800",
    description: "Email, webhook, and notification settings",
  },
  general: {
    label: "General",
    color: "bg-gray-100 text-gray-800",
    description: "General system configuration",
  },
};

// =========================================================================
// System Health
// =========================================================================

export interface ServiceHealth {
  name: string;
  status: SystemStatus;
  response_time_ms: number | null;
  details: Record<string, unknown>;
}

export interface SystemMetrics {
  cpu_usage_percent: number | null;
  memory_usage_percent: number | null;
  disk_usage_percent: number | null;
  active_connections: number | null;
}

export interface SystemHealthResponse {
  overall_status: SystemStatus;
  services: ServiceHealth[];
  metrics: SystemMetrics;
  checked_at: string;
}

// Service names
export const CORE_SERVICES = [
  "postgresql",
  "redis",
  "minio",
  "opa",
  "ollama",
] as const;

// Health thresholds
export const HEALTH_THRESHOLDS = {
  warning: 70,
  danger: 90,
  responseTimeWarning: 500,
  responseTimeDanger: 1000,
} as const;

// =========================================================================
// Helper Functions
// =========================================================================

/**
 * Get status color class
 */
export function getStatusColor(status: SystemStatus): string {
  switch (status) {
    case "healthy":
      return "text-green-600 bg-green-100";
    case "degraded":
      return "text-yellow-600 bg-yellow-100";
    case "unhealthy":
      return "text-red-600 bg-red-100";
    default:
      return "text-gray-600 bg-gray-100";
  }
}

/**
 * Get metric color based on threshold
 */
export function getMetricColor(value: number | null): string {
  if (value === null) return "text-gray-400";
  if (value >= HEALTH_THRESHOLDS.danger) return "text-red-600";
  if (value >= HEALTH_THRESHOLDS.warning) return "text-yellow-600";
  return "text-green-600";
}

/**
 * Format setting value for display
 */
export function formatSettingValue(value: unknown): string {
  if (typeof value === "boolean") {
    return value ? "Enabled" : "Disabled";
  }
  if (typeof value === "number") {
    return value.toLocaleString();
  }
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "object" && value !== null) {
    return JSON.stringify(value, null, 2);
  }
  return String(value);
}

/**
 * Format timestamp for audit log display
 */
export function formatAuditTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString("vi-VN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

// =========================================================================
// Override Queue (VCR - Version Controlled Resolution)
// =========================================================================

export type OverrideType = "false_positive" | "approved_risk" | "emergency";
export type OverrideStatus = "pending" | "approved" | "rejected" | "expired" | "cancelled";

export interface OverrideItem {
  id: string;
  event_id: string;
  project_id: string;
  project_name?: string;
  override_type: OverrideType;
  reason: string;
  status: OverrideStatus;
  requested_by_id: string | null;
  requested_by_name: string | null;
  requested_at: string;
  resolved_by_id: string | null;
  resolved_by_name: string | null;
  resolved_at: string | null;
  resolution_comment: string | null;
  pr_number: string | null;
  pr_title: string | null;
  failed_validators: string[] | null;
  expires_at: string | null;
  is_expired: boolean;
  post_merge_review_required: boolean;
  created_at: string;
}

export interface OverrideQueueResponse {
  pending: OverrideItem[];
  recent_decisions: OverrideItem[];
  total_pending: number;
}

export interface OverrideStatsResponse {
  total: number;
  pending: number;
  by_status: Record<string, number>;
  by_type: Record<string, number>;
  approval_rate: number;
  days: number;
}

// Override type metadata for UI
export const OVERRIDE_TYPE_META: Record<OverrideType, { label: string; color: string; description: string }> = {
  false_positive: {
    label: "False Positive",
    color: "bg-blue-100 text-blue-800",
    description: "The validation failure is incorrect - the code is actually safe",
  },
  approved_risk: {
    label: "Approved Risk",
    color: "bg-yellow-100 text-yellow-800",
    description: "Risk has been reviewed and explicitly accepted",
  },
  emergency: {
    label: "Emergency",
    color: "bg-red-100 text-red-800",
    description: "Critical hotfix requiring immediate merge (requires post-merge review)",
  },
};

// Override status metadata for UI
export const OVERRIDE_STATUS_META: Record<OverrideStatus, { label: string; color: string }> = {
  pending: { label: "Pending Review", color: "bg-orange-100 text-orange-800" },
  approved: { label: "Approved", color: "bg-green-100 text-green-800" },
  rejected: { label: "Rejected", color: "bg-red-100 text-red-800" },
  expired: { label: "Expired", color: "bg-gray-100 text-gray-800" },
  cancelled: { label: "Cancelled", color: "bg-gray-100 text-gray-800" },
};
