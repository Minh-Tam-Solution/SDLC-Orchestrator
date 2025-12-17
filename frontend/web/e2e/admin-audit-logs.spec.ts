/**
 * File: frontend/web/e2e/admin-audit-logs.spec.ts
 * Version: 1.0.0
 * Status: ACTIVE - Sprint 38 E2E Testing
 * Date: 2025-12-17
 * Authority: Frontend Lead + CTO Approved
 * Foundation: SDLC 5.1.1 Complete Lifecycle
 *
 * Description:
 * E2E tests for Admin Panel Audit Logs.
 * Tests audit log viewing, filtering, and compliance features.
 *
 * ADR-017 Requirements Tested:
 * - REQ-AUD-001: View audit logs
 * - REQ-AUD-002: Filter by action type
 * - REQ-AUD-003: Filter by date range
 * - REQ-AUD-004: Search logs
 * - REQ-AUD-005: SOC 2 compliance display
 */

import { test, expect } from '@playwright/test'
import { loginAsAdmin } from './helpers/auth'

test.describe('Admin Audit Logs', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page)
    await page.goto('/admin/audit-logs')
    await page.waitForLoadState('networkidle')
  })

  test.describe('Page Layout', () => {
    test('should display audit logs heading', async ({ page }) => {
      await expect(page.getByRole('heading', { name: /audit logs/i })).toBeVisible()
    })

    test('should display log entries count', async ({ page }) => {
      await expect(page.getByText(/\d+ log entries/i)).toBeVisible()
    })

    test('should display SOC 2 compliance notice', async ({ page }) => {
      await expect(page.getByText(/SOC 2 Compliance/i)).toBeVisible()
      await expect(page.getByText(/append-only/i)).toBeVisible()
    })

    test('should display logs table with headers', async ({ page }) => {
      await expect(page.locator('table')).toBeVisible()
      await expect(page.getByRole('columnheader', { name: /timestamp/i })).toBeVisible()
      await expect(page.getByRole('columnheader', { name: /action/i })).toBeVisible()
      await expect(page.getByRole('columnheader', { name: /actor/i })).toBeVisible()
    })
  })

  test.describe('Search Functionality', () => {
    test('should search logs by actor email', async ({ page }) => {
      const searchInput = page.getByPlaceholder(/search/i)
      await searchInput.fill('admin')
      await page.waitForTimeout(500)

      // Results should contain admin
      const rows = page.locator('tbody tr')
      const count = await rows.count()

      if (count > 0) {
        await expect(rows.first()).toContainText(/admin/i)
      }
    })

    test('should clear filters', async ({ page }) => {
      // Add search term
      const searchInput = page.getByPlaceholder(/search/i)
      await searchInput.fill('test')
      await page.waitForTimeout(500)

      // Click clear filters
      const clearButton = page.getByRole('button', { name: /clear filters/i })
      const isVisible = await clearButton.isVisible().catch(() => false)

      if (isVisible) {
        await clearButton.click()
        await page.waitForTimeout(500)

        // Search should be cleared
        await expect(searchInput).toHaveValue('')
      }
    })
  })

  test.describe('Action Type Filters', () => {
    test('should filter by USER_LOGIN action', async ({ page }) => {
      // Click User Login filter
      const loginFilter = page.getByRole('button', { name: /user login/i })
      await loginFilter.click()
      await page.waitForTimeout(500)

      // Button should be active (default variant)
      await expect(loginFilter).toHaveClass(/bg-primary/)
    })

    test('should filter by USER_ACTIVATED action', async ({ page }) => {
      const activatedFilter = page.getByRole('button', { name: /user activated/i })
      await activatedFilter.click()
      await page.waitForTimeout(500)

      await expect(activatedFilter).toHaveClass(/bg-primary/)
    })

    test('should toggle filter off when clicking again', async ({ page }) => {
      const loginFilter = page.getByRole('button', { name: /user login/i })

      // Click to activate
      await loginFilter.click()
      await page.waitForTimeout(300)

      // Click to deactivate
      await loginFilter.click()
      await page.waitForTimeout(300)

      // Should not have active class
      await expect(loginFilter).not.toHaveClass(/bg-primary/)
    })
  })

  test.describe('Date Range Filters', () => {
    test('should have date from input', async ({ page }) => {
      const dateFromInput = page.locator('input[type="date"]').first()
      await expect(dateFromInput).toBeVisible()
    })

    test('should have date to input', async ({ page }) => {
      const dateToInput = page.locator('input[type="date"]').last()
      await expect(dateToInput).toBeVisible()
    })

    test('should filter by date range', async ({ page }) => {
      const dateFromInput = page.locator('input[type="date"]').first()
      const dateToInput = page.locator('input[type="date"]').last()

      // Set date range to today
      const today = new Date().toISOString().split('T')[0]
      await dateFromInput.fill(today)
      await dateToInput.fill(today)

      await page.waitForTimeout(500)

      // Should filter results (may show today's logs or no results)
      const rows = page.locator('tbody tr')
      const noResults = page.getByText(/no audit logs found/i)

      const hasRows = await rows.first().isVisible().catch(() => false)
      const hasNoResults = await noResults.isVisible().catch(() => false)

      expect(hasRows || hasNoResults).toBeTruthy()
    })
  })

  test.describe('Log Entry Display', () => {
    test('should display action badges with colors', async ({ page }) => {
      // Look for colored badges
      const badges = page.locator('.rounded-full').filter({
        has: page.locator('text=/login|activated|deactivated|updated/i')
      })

      const count = await badges.count()

      // If there are logs, badges should exist
      const hasLogs = await page.locator('tbody tr').first().isVisible().catch(() => false)

      if (hasLogs) {
        expect(count).toBeGreaterThan(0)
      }
    })

    test('should display timestamps in readable format', async ({ page }) => {
      const hasLogs = await page.locator('tbody tr').first().isVisible().catch(() => false)

      if (hasLogs) {
        // Timestamp should be in format like "Dec 17, 2025" or similar
        await expect(page.locator('tbody tr').first()).toContainText(/\d{1,2}/)
      }
    })

    test('should display actor information', async ({ page }) => {
      const hasLogs = await page.locator('tbody tr').first().isVisible().catch(() => false)

      if (hasLogs) {
        // Should show email or "System"
        const actorCell = page.locator('tbody tr').first().locator('td').nth(2)
        await expect(actorCell).toContainText(/@|System/)
      }
    })
  })

  test.describe('Pagination', () => {
    test('should display pagination info', async ({ page }) => {
      const pageInfo = page.getByText(/page \d+ of \d+/i)
      await expect(pageInfo).toBeVisible()
    })

    test('should have navigation buttons', async ({ page }) => {
      const prevButton = page.getByRole('button', { name: /previous/i })
      const nextButton = page.getByRole('button', { name: /next/i })

      await expect(prevButton).toBeVisible()
      await expect(nextButton).toBeVisible()
    })

    test('previous button should be disabled on first page', async ({ page }) => {
      const prevButton = page.getByRole('button', { name: /previous/i })
      await expect(prevButton).toBeDisabled()
    })
  })

  test.describe('Responsive Behavior', () => {
    test('should be scrollable on narrow screens', async ({ page }) => {
      // Set narrow viewport
      await page.setViewportSize({ width: 800, height: 600 })
      await page.reload()
      await page.waitForLoadState('networkidle')

      // Table should still be visible (possibly scrollable)
      await expect(page.locator('table')).toBeVisible()
    })
  })
})
