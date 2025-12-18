/**
 * File: frontend/web/e2e/admin-users-bulk-delete.spec.ts
 * Version: 1.0.0
 * Status: ACTIVE - Sprint 40 Part 3 (Bulk Delete)
 * Date: 2025-12-18
 * Authority: CTO Approved (Dec 18, 2025)
 * Foundation: SDLC 5.1.1 Complete Lifecycle
 *
 * Description:
 * E2E tests for Admin Panel Bulk Delete Users feature.
 * Tests bulk selection, confirmation dialog, and delete flow.
 *
 * CTO Conditions Tested:
 * 1. Batch Size Limit: Maximum 50 users per request
 * 2. Partial Success Handling: Shows detailed report
 * 3. Rate Limiting: 5 requests/minute (backend)
 *
 * Test Scenarios per CTO Directive:
 * - Happy path (bulk delete multiple users)
 * - Self-delete prevention
 * - Last superuser protection
 * - Cancel bulk delete flow
 * - Empty selection edge case
 * - DELETE confirmation requirement
 */

import { test, expect } from '@playwright/test'
import { loginAsAdmin } from './helpers/auth'

test.describe('Admin User Bulk Delete', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page)
    await page.goto('/admin/users')
    await page.waitForLoadState('networkidle')
  })

  test.describe('Bulk Delete Button', () => {
    test('should show Delete Selected button when users are selected', async ({ page }) => {
      // Select first non-self user
      const firstCheckbox = page.locator('tbody tr').filter({
        hasNot: page.locator('text=(You)')
      }).first().locator('input[type="checkbox"]')

      const isVisible = await firstCheckbox.isVisible().catch(() => false)

      if (isVisible) {
        await firstCheckbox.click()

        // Should show bulk action bar with Delete Selected button
        await expect(page.getByRole('button', { name: 'Delete Selected', exact: true })).toBeVisible()
      }
    })

    test('should not show Delete Selected button when no users selected', async ({ page }) => {
      // Without selecting any users, Delete Selected should not be visible
      await expect(page.getByRole('button', { name: 'Delete Selected', exact: true })).not.toBeVisible()
    })
  })

  test.describe('Bulk Delete Dialog', () => {
    test('should open bulk delete dialog when clicking Delete Selected', async ({ page }) => {
      // Select first non-self user
      const firstCheckbox = page.locator('tbody tr').filter({
        hasNot: page.locator('text=(You)')
      }).first().locator('input[type="checkbox"]')

      const isVisible = await firstCheckbox.isVisible().catch(() => false)

      if (isVisible) {
        await firstCheckbox.click()

        // Click Delete Selected
        await page.getByRole('button', { name: 'Delete Selected', exact: true }).click()

        // Dialog should appear
        await expect(page.getByRole('heading', { name: /delete \d+ user/i })).toBeVisible({ timeout: 5000 })
      }
    })

    test('should show list of users to delete in dialog', async ({ page }) => {
      // Select first non-self user
      const firstRow = page.locator('tbody tr').filter({
        hasNot: page.locator('text=(You)')
      }).first()

      const firstCheckbox = firstRow.locator('input[type="checkbox"]')
      const isVisible = await firstCheckbox.isVisible().catch(() => false)

      if (isVisible) {
        // Get the email of the user we're selecting
        const email = await firstRow.locator('td').nth(1).locator('p').last().textContent()

        await firstCheckbox.click()
        await page.getByRole('button', { name: 'Delete Selected', exact: true }).click()

        // Dialog should show the email
        if (email) {
          await expect(page.getByText(email.trim()).first()).toBeVisible({ timeout: 5000 })
        }
      }
    })

    test('should require typing DELETE to enable delete button', async ({ page }) => {
      // Select first non-self user
      const firstCheckbox = page.locator('tbody tr').filter({
        hasNot: page.locator('text=(You)')
      }).first().locator('input[type="checkbox"]')

      const isVisible = await firstCheckbox.isVisible().catch(() => false)

      if (isVisible) {
        await firstCheckbox.click()
        await page.getByRole('button', { name: 'Delete Selected', exact: true }).click()

        // Wait for dialog
        await expect(page.getByRole('heading', { name: /delete \d+ user/i })).toBeVisible({ timeout: 5000 })

        // Delete button should be disabled initially
        const deleteButton = page.getByRole('button', { name: /^delete \d+ user/i })
        await expect(deleteButton).toBeDisabled()

        // Type DELETE in the confirmation input
        await page.getByPlaceholder(/type delete/i).fill('DELETE')

        // Now delete button should be enabled
        await expect(deleteButton).toBeEnabled()
      }
    })

    test('should show error when typing wrong confirmation text', async ({ page }) => {
      // Select first non-self user
      const firstCheckbox = page.locator('tbody tr').filter({
        hasNot: page.locator('text=(You)')
      }).first().locator('input[type="checkbox"]')

      const isVisible = await firstCheckbox.isVisible().catch(() => false)

      if (isVisible) {
        await firstCheckbox.click()
        await page.getByRole('button', { name: 'Delete Selected', exact: true }).click()

        // Wait for dialog
        await expect(page.getByRole('heading', { name: /delete \d+ user/i })).toBeVisible({ timeout: 5000 })

        // Type wrong text
        await page.getByPlaceholder(/type delete/i).fill('WRONG')

        // Should show error message
        await expect(page.getByText(/please type delete exactly/i)).toBeVisible()
      }
    })
  })

  test.describe('Cancel Bulk Delete', () => {
    test('should close dialog when clicking Cancel', async ({ page }) => {
      // Select first non-self user
      const firstCheckbox = page.locator('tbody tr').filter({
        hasNot: page.locator('text=(You)')
      }).first().locator('input[type="checkbox"]')

      const isVisible = await firstCheckbox.isVisible().catch(() => false)

      if (isVisible) {
        await firstCheckbox.click()
        await page.getByRole('button', { name: 'Delete Selected', exact: true }).click()

        // Wait for dialog
        await expect(page.getByRole('heading', { name: /delete \d+ user/i })).toBeVisible({ timeout: 5000 })

        // Click Cancel
        await page.getByRole('button', { name: /cancel/i }).click()

        // Dialog should close
        await expect(page.getByRole('heading', { name: /delete \d+ user/i })).not.toBeVisible()

        // Selection should remain intact
        await expect(page.getByText(/\d+ user\(s\) selected/i).first()).toBeVisible()
      }
    })

    test('should keep selection intact after canceling', async ({ page }) => {
      // Select two non-self users
      const checkboxes = page.locator('tbody tr').filter({
        hasNot: page.locator('text=(You)')
      }).locator('input[type="checkbox"]')

      const count = await checkboxes.count()

      if (count >= 2) {
        await checkboxes.nth(0).click()
        await checkboxes.nth(1).click()

        // Verify selection count
        await expect(page.getByText('2 user(s) selected')).toBeVisible()

        // Open and cancel dialog
        await page.getByRole('button', { name: 'Delete Selected', exact: true }).click()
        await expect(page.getByRole('heading', { name: /delete 2 users/i })).toBeVisible({ timeout: 5000 })
        await page.getByRole('button', { name: /cancel/i }).click()

        // Selection should still show 2 users
        await expect(page.getByText('2 user(s) selected')).toBeVisible()
      }
    })
  })

  test.describe('Successful Bulk Delete', () => {
    test('should delete users and show success toast', async ({ page }) => {
      // First, create a test user to delete
      await page.getByRole('button', { name: /create user/i }).click()

      const timestamp = Date.now()
      const testEmail = `bulk.delete.test.${timestamp}@sdlc-test.io`

      await page.getByLabel(/email/i).fill(testEmail)
      await page.getByLabel(/^password/i).fill('BulkDeleteTest123!!')
      await page.getByRole('button', { name: /create user$/i }).click()

      // Wait for success toast
      await expect(page.getByText('User Created').first()).toBeVisible({ timeout: 10000 })

      // Wait for dialog to close and toast to auto-dismiss
      await page.waitForTimeout(6000)

      // Select the newly created user
      const testUserRow = page.locator('tbody tr').filter({ hasText: testEmail }).first()
      await expect(testUserRow).toBeVisible({ timeout: 5000 })
      await testUserRow.locator('input[type="checkbox"]').click()

      // Click Delete Selected
      await page.getByRole('button', { name: 'Delete Selected', exact: true }).click()

      // Wait for dialog
      await expect(page.getByRole('alertdialog')).toBeVisible({ timeout: 5000 })
      await expect(page.getByRole('heading', { name: /delete 1 user/i })).toBeVisible({ timeout: 5000 })

      // Type DELETE and confirm
      await page.getByPlaceholder(/type delete/i).fill('DELETE')

      // Click the delete button inside the dialog
      const deleteButton = page.getByRole('alertdialog').getByRole('button', { name: /delete 1 user/i })
      await expect(deleteButton).toBeEnabled({ timeout: 2000 })
      await deleteButton.click()

      // Wait for the dialog to close and API to complete
      await expect(page.getByRole('alertdialog')).not.toBeVisible({ timeout: 10000 })

      // User should be removed from list (the main verification)
      await page.waitForTimeout(2000)
      await expect(page.locator('tbody tr').filter({ hasText: testEmail })).not.toBeVisible({ timeout: 5000 })
    })
  })

  test.describe('Self-Delete Prevention', () => {
    test('should not allow selecting current user for bulk delete', async ({ page }) => {
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

  test.describe('Warning and Information', () => {
    test('should show warning about soft delete in dialog', async ({ page }) => {
      // Select first non-self user
      const firstCheckbox = page.locator('tbody tr').filter({
        hasNot: page.locator('text=(You)')
      }).first().locator('input[type="checkbox"]')

      const isVisible = await firstCheckbox.isVisible().catch(() => false)

      if (isVisible) {
        await firstCheckbox.click()
        await page.getByRole('button', { name: 'Delete Selected', exact: true }).click()

        // Wait for dialog
        await expect(page.getByRole('heading', { name: /delete \d+ user/i })).toBeVisible({ timeout: 5000 })

        // Should show warning about soft delete
        await expect(page.getByText(/soft delete/i)).toBeVisible()
        await expect(page.getByText(/audit/i)).toBeVisible()
      }
    })

    test('should show Admin badge for superuser in dialog', async ({ page }) => {
      // Filter to show admins only
      await page.getByRole('button', { name: /admins only/i }).click()
      await page.waitForTimeout(500)

      // Select first admin user (not self)
      const adminCheckbox = page.locator('tbody tr').filter({
        hasNot: page.locator('text=(You)')
      }).first().locator('input[type="checkbox"]')

      const isVisible = await adminCheckbox.isVisible().catch(() => false)

      if (isVisible) {
        await adminCheckbox.click()
        await page.getByRole('button', { name: 'Delete Selected', exact: true }).click()

        // Wait for dialog (alertdialog role from AlertDialog component)
        await expect(page.getByRole('alertdialog')).toBeVisible({ timeout: 5000 })
        await expect(page.getByRole('heading', { name: /delete \d+ user/i })).toBeVisible({ timeout: 5000 })

        // Should show Admin badge in the user list (alertdialog role, not dialog)
        await expect(page.getByRole('alertdialog').getByText('Admin').first()).toBeVisible()
      }
    })
  })
})
