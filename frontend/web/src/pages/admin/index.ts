/**
 * File: frontend/web/src/pages/admin/index.ts
 * Version: 1.0.0
 * Status: ACTIVE - Sprint 37 Admin Panel
 * Date: 2025-12-16
 * Authority: CTO Approved (ADR-017)
 * Framework: SDLC 5.1.1 Complete Lifecycle
 *
 * Description:
 * Export all admin pages for lazy loading in App.tsx
 */

export { default as AdminDashboardPage } from './AdminDashboardPage'
export { default as UserManagementPage } from './UserManagementPage'
export { default as AuditLogsPage } from './AuditLogsPage'
export { default as SystemSettingsPage } from './SystemSettingsPage'
export { default as SystemHealthPage } from './SystemHealthPage'
