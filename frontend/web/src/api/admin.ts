/**
 * File: frontend/web/src/api/admin.ts
 * Version: 1.0.0
 * Status: ACTIVE - Sprint 37 Admin Panel
 * Date: 2025-12-16
 * Authority: CTO Approved (ADR-017)
 * Framework: SDLC 5.1.1 Complete Lifecycle
 *
 * Description:
 * Admin Panel API types and hooks for SDLC Orchestrator.
 * Provides React Query hooks for admin endpoints.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from './client'

// =========================================================================
// Types - Dashboard Stats
// =========================================================================

export interface AdminDashboardStats {
  total_users: number
  active_users: number
  inactive_users: number
  superusers: number
  total_projects: number
  total_gates: number
  active_projects: number
  system_status: 'healthy' | 'degraded' | 'unhealthy'
}

// =========================================================================
// Types - User Management
// =========================================================================

export interface AdminUserListItem {
  id: string
  email: string
  name: string | null
  is_active: boolean
  is_superuser: boolean
  created_at: string
  last_login: string | null
}

export interface AdminUserDetail {
  id: string
  email: string
  name: string | null
  avatar_url: string | null
  is_active: boolean
  is_superuser: boolean
  mfa_enabled: boolean
  oauth_providers: string[]
  project_count: number
  created_at: string
  updated_at: string
  last_login: string | null
}

export interface AdminUserUpdate {
  name?: string
  is_active?: boolean
  is_superuser?: boolean
}

export interface AdminUserListResponse {
  items: AdminUserListItem[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface BulkUserActionRequest {
  user_ids: string[]
  action: 'activate' | 'deactivate'
}

export interface BulkUserActionResponse {
  success_count: number
  failed_count: number
  failed_users: Array<{ user_id: string; reason: string }>
}

// =========================================================================
// Types - Audit Logs
// =========================================================================

export interface AuditLogItem {
  id: string
  timestamp: string
  action: string
  actor_id: string | null
  actor_email: string | null
  target_type: string | null
  target_id: string | null
  target_name: string | null
  details: Record<string, unknown>
  ip_address: string | null
}

export interface AuditLogListResponse {
  items: AuditLogItem[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface AuditLogFilter {
  action?: string
  actor_id?: string
  target_type?: string
  date_from?: string
  date_to?: string
  search?: string
}

// =========================================================================
// Types - System Settings
// =========================================================================

export interface SystemSettingItem {
  key: string
  value: unknown
  version: number
  category: string
  description: string | null
  updated_at: string
  updated_by: string | null
}

export interface SystemSettingsListResponse {
  security: SystemSettingItem[]
  limits: SystemSettingItem[]
  features: SystemSettingItem[]
  notifications: SystemSettingItem[]
  general: SystemSettingItem[]
}

export interface SystemSettingUpdate {
  value: unknown
}

// =========================================================================
// Types - System Health
// =========================================================================

export interface ServiceHealthStatus {
  name: string
  status: 'healthy' | 'degraded' | 'unhealthy'
  response_time_ms: number | null
  details: Record<string, unknown>
}

export interface SystemMetrics {
  cpu_usage_percent: number | null
  memory_usage_percent: number | null
  disk_usage_percent: number | null
  active_connections: number | null
}

export interface SystemHealthResponse {
  overall_status: 'healthy' | 'degraded' | 'unhealthy'
  services: ServiceHealthStatus[]
  metrics: SystemMetrics
  checked_at: string
}

// =========================================================================
// Query Keys
// =========================================================================

export const adminQueryKeys = {
  all: ['admin'] as const,
  stats: () => [...adminQueryKeys.all, 'stats'] as const,
  users: () => [...adminQueryKeys.all, 'users'] as const,
  userList: (params: Record<string, unknown>) => [...adminQueryKeys.users(), 'list', params] as const,
  userDetail: (id: string) => [...adminQueryKeys.users(), 'detail', id] as const,
  auditLogs: () => [...adminQueryKeys.all, 'audit-logs'] as const,
  auditLogList: (params: Record<string, unknown>) => [...adminQueryKeys.auditLogs(), 'list', params] as const,
  settings: () => [...adminQueryKeys.all, 'settings'] as const,
  setting: (key: string) => [...adminQueryKeys.settings(), key] as const,
  health: () => [...adminQueryKeys.all, 'health'] as const,
}

// =========================================================================
// Hooks - Dashboard Stats
// =========================================================================

export function useAdminStats() {
  return useQuery({
    queryKey: adminQueryKeys.stats(),
    queryFn: async () => {
      const response = await apiClient.get<AdminDashboardStats>('/admin/stats')
      return response.data
    },
  })
}

// =========================================================================
// Hooks - User Management
// =========================================================================

export interface UseAdminUsersParams {
  page?: number
  page_size?: number
  search?: string
  is_active?: boolean
  is_superuser?: boolean
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export function useAdminUsers(params: UseAdminUsersParams = {}) {
  return useQuery({
    queryKey: adminQueryKeys.userList(params as Record<string, unknown>),
    queryFn: async () => {
      const response = await apiClient.get<AdminUserListResponse>('/admin/users', { params })
      return response.data
    },
  })
}

export function useAdminUserDetail(userId: string) {
  return useQuery({
    queryKey: adminQueryKeys.userDetail(userId),
    queryFn: async () => {
      const response = await apiClient.get<AdminUserDetail>(`/admin/users/${userId}`)
      return response.data
    },
    enabled: !!userId,
  })
}

export function useUpdateAdminUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ userId, data }: { userId: string; data: AdminUserUpdate }) => {
      const response = await apiClient.patch<AdminUserDetail>(`/admin/users/${userId}`, data)
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.users() })
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.userDetail(variables.userId) })
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.stats() })
    },
  })
}

export function useBulkUserAction() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: BulkUserActionRequest) => {
      const response = await apiClient.post<BulkUserActionResponse>('/admin/users/bulk', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.users() })
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.stats() })
    },
  })
}

// =========================================================================
// Hooks - Audit Logs
// =========================================================================

export interface UseAuditLogsParams {
  page?: number
  page_size?: number
  action?: string
  actor_id?: string
  target_type?: string
  date_from?: string
  date_to?: string
  search?: string
}

export function useAuditLogs(params: UseAuditLogsParams = {}) {
  return useQuery({
    queryKey: adminQueryKeys.auditLogList(params as Record<string, unknown>),
    queryFn: async () => {
      const response = await apiClient.get<AuditLogListResponse>('/admin/audit-logs', { params })
      return response.data
    },
  })
}

// =========================================================================
// Hooks - System Settings
// =========================================================================

export function useSystemSettings() {
  return useQuery({
    queryKey: adminQueryKeys.settings(),
    queryFn: async () => {
      const response = await apiClient.get<SystemSettingsListResponse>('/admin/settings')
      return response.data
    },
  })
}

export function useSystemSetting(key: string) {
  return useQuery({
    queryKey: adminQueryKeys.setting(key),
    queryFn: async () => {
      const response = await apiClient.get<SystemSettingItem>(`/admin/settings/${key}`)
      return response.data
    },
    enabled: !!key,
  })
}

export function useUpdateSystemSetting() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ key, data }: { key: string; data: SystemSettingUpdate }) => {
      const response = await apiClient.patch<SystemSettingItem>(`/admin/settings/${key}`, data)
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.settings() })
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.setting(variables.key) })
    },
  })
}

export function useRollbackSystemSetting() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (key: string) => {
      const response = await apiClient.post<SystemSettingItem>(`/admin/settings/${key}/rollback`)
      return response.data
    },
    onSuccess: (_, key) => {
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.settings() })
      queryClient.invalidateQueries({ queryKey: adminQueryKeys.setting(key) })
    },
  })
}

// =========================================================================
// Hooks - System Health
// =========================================================================

export function useSystemHealth() {
  return useQuery({
    queryKey: adminQueryKeys.health(),
    queryFn: async () => {
      const response = await apiClient.get<SystemHealthResponse>('/admin/system/health')
      return response.data
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  })
}
