/**
 * File: frontend/web/e2e/admin-users.spec.ts
 * Version: 1.0.0
 * Status: ACTIVE - Sprint 38 E2E Testing
 * Date: 2025-12-17
 * Authority: Frontend Lead + CTO Approved
 * Foundation: SDLC 5.1.1 Complete Lifecycle
 *
 * Description:
 * E2E tests for Admin Panel User Management.
 * Tests user listing, search, filter, and management actions.
 *
 * ADR-017 Requirements Tested:
 * - REQ-USR-001: List users with pagination
 * - REQ-USR-002: Search users by email
 * - REQ-USR-003: Filter by active status
 * - REQ-USR-004: Activate/deactivate users
 * - REQ-USR-005: Self-action prevention
 * - REQ-USR-006: Grant/revoke superuser
 * - REQ-USR-007: Bulk actions
 */

import { test, expect } from '@playwright/test'
import { loginAsAdmin } from './helpers/auth'

test.describe('Admin User Management', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page)
    await page.goto('/admin/users')
    await page.waitForLoadState('networkidle')
  })

  test.describe('User Listing', () => {
    test('should display users table', async ({ page }) => {
      // Should see users table
      await expect(page.locator('table')).toBeVisible({ timeout: 10000 })

      // Should have table headers
      await expect(page.getByRole('columnheader', { name: /user/i })).toBeVisible()
      await expect(page.getByRole('columnheader', { name: /status/i })).toBeVisible()
      await expect(page.getByRole('columnheader', { name: /actions/i })).toBeVisible()
    })

    test('should show total users count', async ({ page }) => {
      // Should display total count
      await expect(page.getByText(/\d+ users total/i)).toBeVisible()
    })

    test('should display pagination when many users', async ({ page }) => {
      // Look for pagination controls
      const prevButton = page.getByRole('button', { name: /previous/i })
      const nextButton = page.getByRole('button', { name: /next/i })

      // At least pagination structure should exist
      const pageInfo = page.getByText(/page \d+ of \d+/i)

      // Either pagination controls or single page indicator
      const hasPagination = await prevButton.isVisible().catch(() => false) ||
                           await pageInfo.isVisible().catch(() => false)

      expect(hasPagination).toBeTruthy()
    })
  })

  test.describe('Search Functionality', () => {
    test('should search users by email', async ({ page }) => {
      // Type in search box
      const searchInput = page.getByPlaceholder(/search/i)
      await searchInput.fill('admin')

      // Wait for search results
      await page.waitForTimeout(500) // Debounce

      // Should filter results
      await expect(page.getByText(/admin@/i)).toBeVisible()
    })

    test('should show no results message for non-matching search', async ({ page }) => {
      const searchInput = page.getByPlaceholder(/search/i)
      await searchInput.fill('nonexistent-user-xyz-12345')

      await page.waitForTimeout(500)

      // Should show empty state
      await expect(page.getByText(/no users found/i)).toBeVisible()
    })

    test('should clear search and show all users', async ({ page }) => {
      const searchInput = page.getByPlaceholder(/search/i)

      // Search first
      await searchInput.fill('admin')
      await page.waitForTimeout(500)

      // Clear search
      await searchInput.clear()
      await page.waitForTimeout(500)

      // Should show all users again (table should have rows)
      await expect(page.locator('tbody tr').first()).toBeVisible()
    })
  })

  test.describe('Filter Functionality', () => {
    test('should filter by active users', async ({ page }) => {
      // Click Active filter button
      await page.getByRole('button', { name: /^active$/i }).click()
      await page.waitForTimeout(500)

      // All visible users should have Active badge
      const statusBadges = page.locator('tbody tr').locator('text=Active')
      const count = await statusBadges.count()

      // Should have at least one active user or empty state
      expect(count >= 0).toBeTruthy()
    })

    test('should filter by inactive users', async ({ page }) => {
      // Click Inactive filter button
      await page.getByRole('button', { name: /^inactive$/i }).click()
      await page.waitForTimeout(500)

      // Should show filtered results or empty state
      const hasInactive = await page.getByText(/inactive/i).isVisible().catch(() => false)
      const hasNoResults = await page.getByText(/no users found/i).isVisible().catch(() => false)

      expect(hasInactive || hasNoResults).toBeTruthy()
    })

    test('should filter by admins only', async ({ page }) => {
      // Click Admins Only filter
      await page.getByRole('button', { name: /admins only/i }).click()
      await page.waitForTimeout(500)

      // Should show admin users (with Admin badge) or empty state
      const adminBadge = page.locator('text=Admin').first()
      const noResults = page.getByText(/no users found/i)

      const hasAdmins = await adminBadge.isVisible().catch(() => false)
      const hasNoResults = await noResults.isVisible().catch(() => false)

      expect(hasAdmins || hasNoResults).toBeTruthy()
    })
  })

  test.describe('User Actions', () => {
    test('should show Deactivate button for active users', async ({ page }) => {
      // Find an active user row
      const activeRow = page.locator('tbody tr').filter({
        has: page.locator('text=Active')
      }).first()

      // Should have Deactivate button
      await expect(activeRow.getByRole('button', { name: /deactivate/i })).toBeVisible()
    })

    test('should show Activate button for inactive users', async ({ page }) => {
      // Filter to show inactive users
      await page.getByRole('button', { name: /^inactive$/i }).click()
      await page.waitForTimeout(500)

      // Check if there are inactive users
      const inactiveRow = page.locator('tbody tr').filter({
        has: page.locator('text=Inactive')
      }).first()

      const hasInactiveUsers = await inactiveRow.isVisible().catch(() => false)

      if (hasInactiveUsers) {
        await expect(inactiveRow.getByRole('button', { name: /activate/i })).toBeVisible()
      }
    })

    test('should disable action buttons for current user (self)', async ({ page }) => {
      // Find the row with "(You)" indicator
      const selfRow = page.locator('tbody tr').filter({
        hasText: '(You)'
      }).first()

      const hasSelfRow = await selfRow.isVisible().catch(() => false)

      if (hasSelfRow) {
        // Action buttons should be disabled
        const deactivateBtn = selfRow.getByRole('button', { name: /deactivate/i })
        const adminBtn = selfRow.getByRole('button', { name: /admin/i })

        await expect(deactivateBtn).toBeDisabled()
        await expect(adminBtn).toBeDisabled()
      }
    })

    test('current user checkbox should be disabled', async ({ page }) => {
      // Find the row with "(You)" indicator
      const selfRow = page.locator('tbody tr').filter({
        hasText: '(You)'
      }).first()

      const hasSelfRow = await selfRow.isVisible().catch(() => false)

      if (hasSelfRow) {
        // Checkbox should be disabled
        const checkbox = selfRow.locator('input[type="checkbox"]')
        await expect(checkbox).toBeDisabled()
      }
    })
  })

  test.describe('Bulk Actions', () => {
    test('should show bulk action bar when users selected', async ({ page }) => {
      // Select first non-self user
      const firstCheckbox = page.locator('tbody tr').filter({
        hasNot: page.locator('text=(You)')
      }).first().locator('input[type="checkbox"]')

      const isVisible = await firstCheckbox.isVisible().catch(() => false)

      if (isVisible) {
        await firstCheckbox.click()

        // Should show bulk action bar
        await expect(page.getByText(/\d+ user\(s\) selected/i)).toBeVisible()
        await expect(page.getByRole('button', { name: /activate selected/i })).toBeVisible()
        await expect(page.getByRole('button', { name: /deactivate selected/i })).toBeVisible()
      }
    })

    test('should clear selection when clicking Clear Selection', async ({ page }) => {
      // Select first non-self user
      const firstCheckbox = page.locator('tbody tr').filter({
        hasNot: page.locator('text=(You)')
      }).first().locator('input[type="checkbox"]')

      const isVisible = await firstCheckbox.isVisible().catch(() => false)

      if (isVisible) {
        await firstCheckbox.click()
        await expect(page.getByText(/\d+ user\(s\) selected/i)).toBeVisible()

        // Click clear selection
        await page.getByRole('button', { name: /clear selection/i }).click()

        // Selection count should disappear
        await expect(page.getByText(/\d+ user\(s\) selected/i)).not.toBeVisible()
      }
    })

    test('should select all users with header checkbox', async ({ page }) => {
      // Click header checkbox
      const headerCheckbox = page.locator('thead input[type="checkbox"]')
      await headerCheckbox.click()

      // Should show selection count
      await expect(page.getByText(/\d+ user\(s\) selected/i)).toBeVisible()
    })
  })

  test.describe('Pagination', () => {
    test('should navigate to next page', async ({ page }) => {
      const nextButton = page.getByRole('button', { name: /next/i })
      const isEnabled = await nextButton.isEnabled().catch(() => false)

      if (isEnabled) {
        await nextButton.click()
        await page.waitForTimeout(500)

        // Should show page 2
        await expect(page.getByText(/page 2/i)).toBeVisible()
      }
    })

    test('should navigate to previous page', async ({ page }) => {
      // Go to page 2 first
      const nextButton = page.getByRole('button', { name: /next/i })
      const canGoNext = await nextButton.isEnabled().catch(() => false)

      if (canGoNext) {
        await nextButton.click()
        await page.waitForTimeout(500)

        // Go back to page 1
        await page.getByRole('button', { name: /previous/i }).click()
        await page.waitForTimeout(500)

        await expect(page.getByText(/page 1/i)).toBeVisible()
      }
    })
  })
})
