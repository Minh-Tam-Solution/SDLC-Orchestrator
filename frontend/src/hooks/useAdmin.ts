/**
 * useAdmin Hooks - Next.js App Router
 * @module frontend/landing/src/hooks/useAdmin
 * @status Sprint 68 - Admin Section Migration
 * @description React Query hooks for admin panel functionality
 * @note Uses httpOnly cookies for auth (Sprint 63 migration)
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type {
  AdminDashboardStats,
  AdminUser,
  AdminUserDetail,
  AdminUserCreate,
  AdminUserUpdate,
  AdminUserUpdateFull,
  AdminUserListResponse,
  AdminUserListParams,
  BulkUserActionRequest,
  BulkUserActionResponse,
  BulkDeleteRequest,
  BulkDeleteResponse,
  AuditLogListResponse,
  AuditLogParams,
  SystemSettingsResponse,
  SystemSetting,
  SystemSettingUpdate,
  SystemHealthResponse,
  OverrideQueueResponse,
  OverrideStatsResponse,
} from "@/lib/types/admin";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// =========================================================================
// Fetch Helper (httpOnly cookies)
// =========================================================================

async function fetchWithAuth<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    credentials: "include", // httpOnly cookies (Sprint 63)
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  // Handle 204 No Content (e.g., DELETE responses)
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// =========================================================================
// Query Keys
// =========================================================================

export const adminQueryKeys = {
  all: ["admin"] as const,
  stats: () => [...adminQueryKeys.all, "stats"] as const,
  users: () => [...adminQueryKeys.all, "users"] as const,
  userList: (params: AdminUserListParams) =>
    [...adminQueryKeys.users(), "list", params] as const,
  userDetail: (id: string) =>
    [...adminQueryKeys.users(), "detail", id] as const,
  auditLogs: () => [...adminQueryKeys.all, "audit-logs"] as const,
  auditLogList: (params: AuditLogParams) =>
    [...adminQueryKeys.auditLogs(), "list", params] as const,
  settings: () => [...adminQueryKeys.all, "settings"] as const,
  setting: (key: string) => [...adminQueryKeys.settings(), key] as const,
  health: () => [...adminQueryKeys.all, "health"] as const,
  overrides: () => [...adminQueryKeys.all, "overrides"] as const,
  overrideQueue: () => [...adminQueryKeys.overrides(), "queue"] as const,
  overrideStats: (days?: number) =>
    [...adminQueryKeys.overrides(), "stats", days] as const,
};

// =========================================================================
// Dashboard Stats
// =========================================================================

/**
 * Fetch admin dashboard statistics
 */
export function useAdminStats() {
  return useQuery({
    queryKey: adminQueryKeys.stats(),
    queryFn: () => fetchWithAuth<AdminDashboardStats>("/admin/stats"),
    staleTime: 30 * 1000, // 30 seconds
  });
}

// =========================================================================
// User Management
// =========================================================================

/**
 * Fetch paginated user list with filters
 */
export function useAdminUsers(params: AdminUserListParams = {}) {
  const queryParams = new URLSearchParams();

  if (params.page) queryParams.set("page", params.page.toString());
  if (params.page_size) queryParams.set("page_size", params.page_size.toString());
  if (params.search) queryParams.set("search", params.search);
  if (params.is_active !== undefined) queryParams.set("is_active", params.is_active.toString());
  if (params.is_superuser !== undefined) queryParams.set("is_superuser", params.is_superuser.toString());
  // Sprint 105: Show Deleted Users feature
  if (params.include_deleted !== undefined) queryParams.set("include_deleted", params.include_deleted.toString());
  if (params.sort_by) queryParams.set("sort_by", params.sort_by);
  if (params.sort_order) queryParams.set("sort_order", params.sort_order);

  const queryString = queryParams.toString();
  const url = queryString ? `/admin/users?${queryString}` : "/admin/users";

  return useQuery({
    queryKey: adminQueryKeys.userList(params),
    queryFn: () => fetchWithAuth<AdminUserListResponse>(url),
    staleTime: 30 * 1000,
  });
}

/**
 * Fetch single user details
 */
export function useAdminUserDetail(userId: string) {
  return useQuery({
    queryKey: adminQueryKeys.userDetail(userId),
    queryFn: () => fetchWithAuth<AdminUserDetail>(`/admin/users/${userId}`),
    enabled: !!userId,
  });
}

/**
 * Create new user
 */
export function useCreateAdminUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AdminUserCreate) =>
      fetchWithAuth<AdminUserDetail>("/admin/users", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.users() });
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.stats() });
    },
  });
}

/**
 * Update user (partial)
 */
export function useUpdateAdminUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: AdminUserUpdate }) =>
      fetchWithAuth<AdminUserDetail>(`/admin/users/${userId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.users() });
      queryClient.invalidateQueries({
        queryKey: adminQueryKeys.userDetail(variables.userId),
      });
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.stats() });
    },
  });
}

/**
 * Update user (full - including email and password)
 */
export function useUpdateAdminUserFull() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      userId,
      data,
    }: {
      userId: string;
      data: AdminUserUpdateFull;
    }) =>
      fetchWithAuth<AdminUserDetail>(`/admin/users/${userId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.users() });
      queryClient.invalidateQueries({
        queryKey: adminQueryKeys.userDetail(variables.userId),
      });
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.stats() });
    },
  });
}

/**
 * Delete user (soft delete)
 */
export function useDeleteAdminUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userId: string) =>
      fetchWithAuth<void>(`/admin/users/${userId}`, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.users() });
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.stats() });
    },
  });
}

/**
 * Bulk activate/deactivate users
 */
export function useBulkUserAction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BulkUserActionRequest) =>
      fetchWithAuth<BulkUserActionResponse>("/admin/users/bulk", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.users() });
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.stats() });
    },
  });
}

/**
 * Bulk delete users
 * CTO Conditions:
 * - Maximum 50 users per request
 * - Returns detailed success/failed report
 * - Rate limited to 5 requests/minute
 */
export function useBulkDeleteUsers() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BulkDeleteRequest) =>
      fetchWithAuth<BulkDeleteResponse>("/admin/users/bulk", {
        method: "DELETE",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.users() });
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.stats() });
    },
  });
}

/**
 * Restore soft-deleted user
 * Sprint 105: Show Deleted Users feature
 * - Restores user account by clearing deleted_at
 * - Reactivates user (is_active=true)
 */
export function useRestoreUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userId: string) =>
      fetchWithAuth<AdminUserDetail>(`/admin/users/${userId}/restore`, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.users() });
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.stats() });
    },
  });
}

/**
 * Permanently delete a soft-deleted user
 * Sprint 105: Show Deleted Users feature
 * - IRREVERSIBLE: Permanently removes user from database
 * - Only works on users that are already soft-deleted
 */
export function usePermanentDeleteUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userId: string) =>
      fetchWithAuth<void>(`/admin/users/${userId}/permanent`, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.users() });
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.stats() });
    },
  });
}

// =========================================================================
// Audit Logs
// =========================================================================

/**
 * Fetch paginated audit logs with filters
 * Note: Audit logs are append-only (SOC 2 CC7.1 compliance)
 */
export function useAuditLogs(params: AuditLogParams = {}) {
  const queryParams = new URLSearchParams();

  if (params.page) queryParams.set("page", params.page.toString());
  if (params.page_size) queryParams.set("page_size", params.page_size.toString());
  if (params.action) queryParams.set("action", params.action);
  if (params.actor_id) queryParams.set("actor_id", params.actor_id);
  if (params.target_type) queryParams.set("target_type", params.target_type);
  if (params.date_from) queryParams.set("date_from", params.date_from);
  if (params.date_to) queryParams.set("date_to", params.date_to);
  if (params.search) queryParams.set("search", params.search);

  const queryString = queryParams.toString();
  const url = queryString ? `/admin/audit-logs?${queryString}` : "/admin/audit-logs";

  return useQuery({
    queryKey: adminQueryKeys.auditLogList(params),
    queryFn: () => fetchWithAuth<AuditLogListResponse>(url),
    staleTime: 60 * 1000, // 1 minute (logs don't change often)
  });
}

// =========================================================================
// System Settings
// =========================================================================

/**
 * Fetch all system settings grouped by category
 */
export function useSystemSettings() {
  return useQuery({
    queryKey: adminQueryKeys.settings(),
    queryFn: () => fetchWithAuth<SystemSettingsResponse>("/admin/settings"),
    staleTime: 60 * 1000,
  });
}

/**
 * Fetch single setting by key
 */
export function useSystemSetting(key: string) {
  return useQuery({
    queryKey: adminQueryKeys.setting(key),
    queryFn: () => fetchWithAuth<SystemSetting>(`/admin/settings/${key}`),
    enabled: !!key,
  });
}

/**
 * Update system setting
 */
export function useUpdateSystemSetting() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ key, data }: { key: string; data: SystemSettingUpdate }) =>
      fetchWithAuth<SystemSetting>(`/admin/settings/${key}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.settings() });
      queryClient.invalidateQueries({
        queryKey: adminQueryKeys.setting(variables.key),
      });
    },
  });
}

/**
 * Rollback setting to previous version
 */
export function useRollbackSystemSetting() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (key: string) =>
      fetchWithAuth<SystemSetting>(`/admin/settings/${key}/rollback`, {
        method: "POST",
      }),
    onSuccess: (_, key) => {
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.settings() });
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.setting(key) });
    },
  });
}

// =========================================================================
// System Health
// =========================================================================

/**
 * Fetch system health status
 * Auto-refreshes every 30 seconds
 */
export function useSystemHealth() {
  return useQuery({
    queryKey: adminQueryKeys.health(),
    queryFn: () => fetchWithAuth<SystemHealthResponse>("/admin/system/health"),
    refetchInterval: 30 * 1000, // Auto-refresh every 30 seconds
    staleTime: 15 * 1000, // Consider stale after 15 seconds
  });
}

// =========================================================================
// Override Queue (VCR - Version Controlled Resolution)
// =========================================================================

/**
 * Fetch override queue (pending + recent decisions)
 * Auto-refreshes every 30 seconds
 */
export function useOverrideQueue() {
  return useQuery({
    queryKey: adminQueryKeys.overrideQueue(),
    queryFn: () => fetchWithAuth<OverrideQueueResponse>("/admin/override-queue"),
    refetchInterval: 30 * 1000, // Auto-refresh for real-time queue updates
    staleTime: 15 * 1000,
  });
}

/**
 * Fetch override statistics
 */
export function useOverrideStats(days: number = 30) {
  return useQuery({
    queryKey: adminQueryKeys.overrideStats(days),
    queryFn: () =>
      fetchWithAuth<OverrideStatsResponse>(`/admin/override-stats?days=${days}`),
    staleTime: 60 * 1000, // Stats don't change as frequently
  });
}

/**
 * Approve an override request
 * Requires comment for audit trail
 */
export function useApproveOverride() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ overrideId, comment }: { overrideId: string; comment: string }) =>
      fetchWithAuth<{ success: boolean }>(`/overrides/${overrideId}/approve`, {
        method: "POST",
        body: JSON.stringify({ comment }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.overrides() });
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.auditLogs() });
    },
  });
}

/**
 * Reject an override request
 * Requires reason (minimum 10 characters) for audit trail
 */
export function useRejectOverride() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ overrideId, reason }: { overrideId: string; reason: string }) =>
      fetchWithAuth<{ success: boolean }>(`/overrides/${overrideId}/reject`, {
        method: "POST",
        body: JSON.stringify({ reason }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.overrides() });
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.auditLogs() });
    },
  });
}

// =========================================================================
// Exports
// =========================================================================

export type {
  AdminDashboardStats,
  AdminUser,
  AdminUserDetail,
  AdminUserCreate,
  AdminUserUpdate,
  AdminUserUpdateFull,
  AdminUserListResponse,
  AdminUserListParams,
  BulkUserActionRequest,
  BulkUserActionResponse,
  BulkDeleteRequest,
  BulkDeleteResponse,
  AuditLogListResponse,
  AuditLogParams,
  SystemSettingsResponse,
  SystemSetting,
  SystemSettingUpdate,
  SystemHealthResponse,
  OverrideQueueResponse,
  OverrideStatsResponse,
};
