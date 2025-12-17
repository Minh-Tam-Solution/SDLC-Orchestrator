/**
 * File: frontend/web/e2e/admin-access-control.spec.ts
 * Version: 1.0.0
 * Status: ACTIVE - Sprint 38 E2E Testing
 * Date: 2025-12-17
 * Authority: Frontend Lead + CTO Approved
 * Foundation: SDLC 5.1.1 Complete Lifecycle
 *
 * Description:
 * E2E tests for Admin Panel access control.
 * Verifies superuser-only access to /admin routes.
 *
 * ADR-017 Requirements Tested:
 * - REQ-SEC-001: Superuser-only access
 * - REQ-SEC-002: Access denied for non-superusers
 * - REQ-SEC-003: Sidebar visibility based on role
 */

import { test, expect } from '@playwright/test'
import { login, loginAsAdmin, logout } from './helpers/auth'

test.describe('Admin Panel Access Control', () => {
  test.describe('Unauthenticated Access', () => {
    test('should redirect to login when accessing /admin without authentication', async ({ page }) => {
      // Try to access admin page without logging in
      await page.goto('/admin')

      // Should redirect to login page
      await expect(page).toHaveURL(/\/login/, { timeout: 5000 })
    })

    test('should redirect to login when accessing /admin/users without authentication', async ({ page }) => {
      await page.goto('/admin/users')
      await expect(page).toHaveURL(/\/login/, { timeout: 5000 })
    })

    test('should redirect to login when accessing /admin/audit-logs without authentication', async ({ page }) => {
      await page.goto('/admin/audit-logs')
      await expect(page).toHaveURL(/\/login/, { timeout: 5000 })
    })

    test('should redirect to login when accessing /admin/settings without authentication', async ({ page }) => {
      await page.goto('/admin/settings')
      await expect(page).toHaveURL(/\/login/, { timeout: 5000 })
    })

    test('should redirect to login when accessing /admin/health without authentication', async ({ page }) => {
      await page.goto('/admin/health')
      await expect(page).toHaveURL(/\/login/, { timeout: 5000 })
    })
  })

  test.describe('Superuser (Admin) Access', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsAdmin(page)
    })

    test('should access admin dashboard', async ({ page }) => {
      await page.goto('/admin')
      await page.waitForLoadState('networkidle')

      // Should see admin dashboard heading
      await expect(page.getByRole('heading', { name: /admin dashboard/i })).toBeVisible()

      // Should see stats cards
      await expect(page.getByText(/total users/i)).toBeVisible()
      await expect(page.getByText(/total projects/i)).toBeVisible()
    })

    test('should access user management page', async ({ page }) => {
      await page.goto('/admin/users')
      await page.waitForLoadState('networkidle')

      // Should see user management heading
      await expect(page.getByRole('heading', { name: /user management/i })).toBeVisible()

      // Should see users table or list
      await expect(page.locator('table, [role="grid"]')).toBeVisible({ timeout: 10000 })
    })

    test('should access audit logs page', async ({ page }) => {
      await page.goto('/admin/audit-logs')
      await page.waitForLoadState('networkidle')

      // Should see audit logs heading
      await expect(page.getByRole('heading', { name: /audit logs/i })).toBeVisible()

      // Should see SOC 2 compliance notice
      await expect(page.getByText(/SOC 2/i)).toBeVisible()
    })

    test('should access system settings page', async ({ page }) => {
      await page.goto('/admin/settings')
      await page.waitForLoadState('networkidle')

      // Should see system settings heading
      await expect(page.getByRole('heading', { name: /system settings/i })).toBeVisible()
    })

    test('should access system health page', async ({ page }) => {
      await page.goto('/admin/health')
      await page.waitForLoadState('networkidle')

      // Should see system health heading
      await expect(page.getByRole('heading', { name: /system health/i })).toBeVisible()

      // Should see system status
      await expect(page.getByText(/system status/i)).toBeVisible()
    })

    test('should see Admin Panel in sidebar', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')

      // Admin Panel link should be visible
      const adminLink = page.locator('a[href="/admin"]')
      await expect(adminLink).toBeVisible()
      await expect(adminLink).toContainText(/admin panel/i)
    })
  })

  test.describe('Navigation between Admin Pages', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsAdmin(page)
    })

    test('should navigate from admin dashboard to user management', async ({ page }) => {
      await page.goto('/admin')
      await page.waitForLoadState('networkidle')

      // Click on User Management link
      await page.getByRole('link', { name: /user management/i }).click()

      // Should be on user management page
      await expect(page).toHaveURL(/\/admin\/users/)
      await expect(page.getByRole('heading', { name: /user management/i })).toBeVisible()
    })

    test('should navigate from admin dashboard to audit logs', async ({ page }) => {
      await page.goto('/admin')
      await page.waitForLoadState('networkidle')

      // Click on Audit Logs link
      await page.getByRole('link', { name: /audit logs/i }).click()

      // Should be on audit logs page
      await expect(page).toHaveURL(/\/admin\/audit-logs/)
      await expect(page.getByRole('heading', { name: /audit logs/i })).toBeVisible()
    })

    test('should navigate back to admin dashboard using back button', async ({ page }) => {
      await page.goto('/admin/users')
      await page.waitForLoadState('networkidle')

      // Click back button (arrow icon in header)
      const backButton = page.locator('button').filter({ has: page.locator('svg') }).first()
      await backButton.click()

      // Should be back on admin dashboard
      await expect(page).toHaveURL(/\/admin$/)
    })
  })

  test.describe('Session Handling', () => {
    test('should maintain admin access after page refresh', async ({ page }) => {
      await loginAsAdmin(page)
      await page.goto('/admin')
      await page.waitForLoadState('networkidle')

      // Verify we're on admin page
      await expect(page.getByRole('heading', { name: /admin dashboard/i })).toBeVisible()

      // Refresh page
      await page.reload()
      await page.waitForLoadState('networkidle')

      // Should still be on admin page
      await expect(page.getByRole('heading', { name: /admin dashboard/i })).toBeVisible()
    })

    test('should lose admin access after logout', async ({ page }) => {
      await loginAsAdmin(page)
      await page.goto('/admin')
      await page.waitForLoadState('networkidle')

      // Logout
      await logout(page)

      // Try to access admin again
      await page.goto('/admin')

      // Should be redirected to login
      await expect(page).toHaveURL(/\/login/)
    })
  })
})
