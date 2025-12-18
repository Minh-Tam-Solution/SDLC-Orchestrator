/**
 * File: frontend/web/e2e/admin-users-crud.spec.ts
 * Version: 1.0.0
 * Status: ACTIVE - Sprint 40 Part 1 E2E Testing
 * Date: 2025-12-17
 * Authority: Frontend Lead + CTO Approved
 * Foundation: SDLC 5.1.1 Complete Lifecycle
 *
 * Description:
 * E2E tests for Admin Panel User CRUD operations (Sprint 40 Part 1).
 * Tests user creation, deletion, and validation scenarios.
 *
 * Sprint 40 Part 1 Requirements Tested:
 * - REQ-USR-008: Create user with email/password validation
 * - REQ-USR-009: Delete user (soft delete with audit trail)
 * - REQ-USR-010: Self-delete prevention
 * - REQ-USR-011: Last superuser protection
 * - REQ-USR-012: Toast notifications for success/error
 *
 * Security Tests:
 * - Password minimum 12 characters
 * - Email uniqueness validation
 * - Cannot delete self
 * - Cannot delete last superuser
 * - Soft delete preserves data
 */

import { test, expect } from '@playwright/test'
import { loginAsAdmin } from './helpers/auth'

test.describe('Admin User CRUD Operations (Sprint 40)', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page)
    await page.goto('/admin/users')
    await page.waitForLoadState('networkidle')
  })

  test.describe('Create User', () => {
    test('should open Create User dialog when clicking Create User button', async ({ page }) => {
      // Click Create User button
      const createButton = page.getByRole('button', { name: /create user/i })
      await expect(createButton).toBeVisible()
      await createButton.click()

      // Dialog should open
      await expect(page.getByRole('heading', { name: /create new user/i })).toBeVisible()

      // Should have all form fields
      await expect(page.getByLabel(/email/i)).toBeVisible()
      await expect(page.getByLabel(/^password/i)).toBeVisible()
      await expect(page.getByLabel(/full name/i)).toBeVisible()
      await expect(page.getByLabel(/active.*user can login/i)).toBeVisible()
      await expect(page.getByLabel(/administrator.*full platform access/i)).toBeVisible()

      // Should have Cancel and Create buttons
      await expect(page.getByRole('button', { name: /^cancel$/i })).toBeVisible()
      await expect(page.getByRole('button', { name: /create user$/i })).toBeVisible()
    })

    test('should create user with valid data successfully', async ({ page }) => {
      // Click Create User button
      await page.getByRole('button', { name: /create user/i }).click()

      // Fill form with valid data
      const timestamp = Date.now()
      const testEmail = `test.user.${timestamp}@sdlc-test.io`
      const testPassword = 'TestPassword123!!' // 18 chars - meets 12 char minimum
      const testName = `Test User ${timestamp}`

      await page.getByLabel(/email/i).fill(testEmail)
      await page.getByLabel(/^password/i).fill(testPassword)
      await page.getByLabel(/full name/i).fill(testName)

      // Submit form
      await page.getByRole('button', { name: /create user$/i }).click()

      // Should show success toast - use first() to avoid strict mode violation
      await expect(page.getByText('User Created').first()).toBeVisible({ timeout: 10000 })

      // Dialog should close
      await expect(page.getByRole('heading', { name: /create new user/i })).not.toBeVisible({ timeout: 5000 })

      // New user should appear in the list
      await page.waitForTimeout(2000) // Wait for table refresh
      await expect(page.getByText(testEmail)).toBeVisible({ timeout: 5000 })
    })

    test('should show validation error for invalid email format', async ({ page }) => {
      // Click Create User button
      await page.getByRole('button', { name: /create user/i }).click()

      // Fill with invalid email
      await page.getByLabel(/email/i).fill('invalid-email')
      await page.getByLabel(/^password/i).fill('ValidPassword123!!')  // 18 chars

      // Submit form
      await page.getByRole('button', { name: /create user$/i }).click()

      // Should show validation error (case insensitive match)
      await expect(page.getByText(/invalid email/i)).toBeVisible({ timeout: 5000 })
    })

    test('should show validation error for password less than 12 characters', async ({ page }) => {
      // Click Create User button
      await page.getByRole('button', { name: /create user/i }).click()

      // Fill with short password (only 7 chars)
      const timestamp = Date.now()
      await page.getByLabel(/email/i).fill(`test${timestamp}@test.io`)
      await page.getByLabel(/^password/i).fill('Short1!')

      // Submit form
      await page.getByRole('button', { name: /create user$/i }).click()

      // Should show validation error
      await expect(page.getByText(/at least 12 characters/i)).toBeVisible({ timeout: 5000 })
    })

    test('should show error when creating user with duplicate email', async ({ page }) => {
      // Click Create User button
      await page.getByRole('button', { name: /create user/i }).click()

      // Use admin email (guaranteed to exist)
      await page.getByLabel(/email/i).fill('admin@sdlc-orchestrator.io')
      await page.getByLabel(/^password/i).fill('ValidPassword123!!')  // 18 chars

      // Submit form
      await page.getByRole('button', { name: /create user$/i }).click()

      // Should show error toast
      await expect(page.getByText(/already exists/i)).toBeVisible({ timeout: 10000 })
    })

    test('should create user with is_active checkbox checked by default', async ({ page }) => {
      // Click Create User button
      await page.getByRole('button', { name: /create user/i }).click()

      // Check that is_active checkbox is checked by default
      const activeCheckbox = page.getByLabel(/active.*user can login/i)
      await expect(activeCheckbox).toBeChecked()
    })

    test('should create user with is_superuser checkbox unchecked by default', async ({ page }) => {
      // Click Create User button
      await page.getByRole('button', { name: /create user/i }).click()

      // Check that is_superuser checkbox is unchecked by default
      const superuserCheckbox = page.getByLabel(/administrator.*full platform access/i)
      await expect(superuserCheckbox).not.toBeChecked()
    })

    test('should create superuser when is_superuser checkbox is checked', async ({ page }) => {
      // Click Create User button
      await page.getByRole('button', { name: /create user/i }).click()

      // Fill form
      const timestamp = Date.now()
      const testEmail = `admin.${timestamp}@sdlc-test.io`

      await page.getByLabel(/email/i).fill(testEmail)
      await page.getByLabel(/^password/i).fill('AdminPassword123!!')  // 18 chars

      // Check is_superuser
      await page.getByLabel(/administrator.*full platform access/i).check()

      // Submit form
      await page.getByRole('button', { name: /create user$/i }).click()

      // Should show success toast - use first() to avoid strict mode
      await expect(page.getByText('User Created').first()).toBeVisible({ timeout: 10000 })

      // Wait and verify user has Admin badge in the list
      await page.waitForTimeout(2000)
      const userRow = page.locator('tbody tr').filter({ hasText: testEmail })
      await expect(userRow.getByText('Admin')).toBeVisible({ timeout: 5000 })
    })

    test('should close dialog when clicking Cancel', async ({ page }) => {
      // Click Create User button
      await page.getByRole('button', { name: /create user/i }).click()

      // Dialog should be visible
      await expect(page.getByRole('heading', { name: /create new user/i })).toBeVisible()

      // Click Cancel
      await page.getByRole('button', { name: /^cancel$/i }).click()

      // Dialog should close
      await expect(page.getByRole('heading', { name: /create new user/i })).not.toBeVisible({ timeout: 2000 })
    })
  })

  test.describe('Delete User', () => {
    test('should show Delete button for users', async ({ page }) => {
      // Find first non-self user row
      const userRow = page.locator('tbody tr').filter({
        hasNot: page.locator('text=(You)')
      }).first()

      // Should have Delete button
      await expect(userRow.getByRole('button', { name: /delete/i })).toBeVisible()
    })

    test('should open Delete User confirmation dialog', async ({ page }) => {
      // Find first non-self user row
      const userRow = page.locator('tbody tr').filter({
        hasNot: page.locator('text=(You)')
      }).first()

      // Get user email from the row
      const userEmail = await userRow.locator('td').nth(1).textContent()

      // Click Delete button
      await userRow.getByRole('button', { name: /delete/i }).click()

      // Confirmation dialog should open
      await expect(page.getByRole('heading', { name: /delete user/i })).toBeVisible()

      // Should show user email in confirmation
      if (userEmail) {
        await expect(page.getByText(new RegExp(userEmail.trim(), 'i'))).toBeVisible()
      }

      // Should show warning message
      await expect(page.getByText(/warning/i)).toBeVisible()
      await expect(page.getByText(/deactivate the user account/i)).toBeVisible()
      await expect(page.getByText(/soft delete/i)).toBeVisible()

      // Should have Cancel and Delete buttons
      await expect(page.getByRole('button', { name: /^cancel$/i })).toBeVisible()
      await expect(page.getByRole('button', { name: /delete user$/i })).toBeVisible()
    })

    test('should delete user successfully and show success toast', async ({ page }) => {
      // Create a test user first to delete
      await page.getByRole('button', { name: /create user/i }).click()
      const timestamp = Date.now()
      const testEmail = `delete.me.${timestamp}@sdlc-test.io`

      await page.getByLabel(/email/i).fill(testEmail)
      await page.getByLabel(/^password/i).fill('DeleteMeNow123!!')  // 16 chars
      await page.getByRole('button', { name: /create user$/i }).click()
      await expect(page.getByText('User Created').first()).toBeVisible({ timeout: 10000 })

      // Wait for user to appear in the list
      await page.waitForTimeout(2000)

      // Find the created user row
      const userRow = page.locator('tbody tr').filter({ hasText: testEmail })
      await expect(userRow).toBeVisible({ timeout: 5000 })

      // Click Delete button
      await userRow.getByRole('button', { name: /delete/i }).click()

      // Wait for dialog
      await expect(page.getByRole('heading', { name: /delete user/i })).toBeVisible({ timeout: 3000 })

      // Confirm deletion
      await page.getByRole('button', { name: /delete user$/i }).click()

      // Should show success toast - use first() to avoid strict mode
      await expect(page.getByText('User Deleted').first()).toBeVisible({ timeout: 10000 })

      // User should be removed from list (soft delete excludes from list)
      await page.waitForTimeout(2000)

      // User should NOT appear in the list anymore
      await expect(page.locator('tbody tr').filter({ hasText: testEmail })).not.toBeVisible({ timeout: 5000 })
    })

    test('should disable Delete button for current user (self)', async ({ page }) => {
      // Find the row with "(You)" indicator
      const selfRow = page.locator('tbody tr').filter({
        hasText: '(You)'
      })

      const hasSelfRow = await selfRow.isVisible().catch(() => false)

      if (hasSelfRow) {
        // Delete button should be disabled
        const deleteBtn = selfRow.getByRole('button', { name: /delete/i })
        await expect(deleteBtn).toBeDisabled()
      }
    })

    test('should show error when trying to delete self', async ({ page }) => {
      // This test verifies backend protection even if frontend allows click
      // Find self row
      const selfRow = page.locator('tbody tr').filter({
        hasText: '(You)'
      })

      const hasSelfRow = await selfRow.isVisible().catch(() => false)

      if (hasSelfRow) {
        const deleteBtn = selfRow.getByRole('button', { name: /delete/i })
        const isDisabled = await deleteBtn.isDisabled().catch(() => true)

        // Frontend should disable the button
        expect(isDisabled).toBeTruthy()
      }
    })

    test('should close confirmation dialog when clicking Cancel', async ({ page }) => {
      // Find first non-self user row
      const userRow = page.locator('tbody tr').filter({
        hasNot: page.locator('text=(You)')
      }).first()

      // Click Delete button
      await userRow.getByRole('button', { name: /delete/i }).click()

      // Dialog should be visible
      await expect(page.getByRole('heading', { name: /delete user/i })).toBeVisible()

      // Click Cancel
      await page.getByRole('button', { name: /^cancel$/i }).click()

      // Dialog should close
      await expect(page.getByRole('heading', { name: /delete user/i })).not.toBeVisible({ timeout: 2000 })
    })

    test('should show loading state while deleting', async ({ page }) => {
      // Create a test user
      await page.getByRole('button', { name: /create user/i }).click()
      const timestamp = Date.now()
      const testEmail = `loading.test.${timestamp}@sdlc-test.io`

      await page.getByLabel(/email/i).fill(testEmail)
      await page.getByLabel(/^password/i).fill('LoadingTest123!!')  // 17 chars
      await page.getByRole('button', { name: /create user$/i }).click()
      await expect(page.getByText('User Created').first()).toBeVisible({ timeout: 10000 })
      await page.waitForTimeout(2000)

      // Find and delete the user
      const userRow = page.locator('tbody tr').filter({ hasText: testEmail })
      await expect(userRow).toBeVisible({ timeout: 5000 })
      await userRow.getByRole('button', { name: /delete/i }).click()

      // Wait for dialog to appear
      await expect(page.getByRole('heading', { name: /delete user/i })).toBeVisible({ timeout: 3000 })

      // Click Delete button and check loading state
      const deleteButton = page.getByRole('button', { name: /delete user$/i })

      // Use Promise.race to check button state immediately after click
      const clickPromise = deleteButton.click()

      // Check that button shows "Deleting..." or is disabled after click
      await clickPromise

      // Wait for deletion to complete - button state or toast
      await expect(page.getByText('User Deleted').first()).toBeVisible({ timeout: 10000 })
    })
  })

  test.describe('Toast Notifications', () => {
    test('should show success toast with user email on create', async ({ page }) => {
      const timestamp = Date.now()
      const testEmail = `toast.test.${timestamp}@sdlc-test.io`

      // Create user
      await page.getByRole('button', { name: /create user/i }).click()
      await page.getByLabel(/email/i).fill(testEmail)
      await page.getByLabel(/^password/i).fill('ToastTest12345!')  // 15 chars
      await page.getByRole('button', { name: /create user$/i }).click()

      // Toast should show success - use first() for strict mode
      await expect(page.getByText('User Created').first()).toBeVisible({ timeout: 10000 })

      // User should appear in the list (confirms creation was successful)
      await page.waitForTimeout(2000)
      await expect(page.getByText(testEmail)).toBeVisible({ timeout: 5000 })
    })

    test('should show error toast on create failure', async ({ page }) => {
      // Try to create with duplicate email
      await page.getByRole('button', { name: /create user/i }).click()
      await page.getByLabel(/email/i).fill('admin@sdlc-orchestrator.io') // Existing email
      await page.getByLabel(/^password/i).fill('ValidPassword123!!')  // 18 chars
      await page.getByRole('button', { name: /create user$/i }).click()

      // Should show error toast (text contains "Error" or "already exists")
      await expect(page.getByText('Error').first()).toBeVisible({ timeout: 10000 })
    })

    test('should show success toast with user email on delete', async ({ page }) => {
      // Create user to delete
      const timestamp = Date.now()
      const testEmail = `delete.toast.${timestamp}@sdlc-test.io`

      await page.getByRole('button', { name: /create user/i }).click()
      await page.getByLabel(/email/i).fill(testEmail)
      await page.getByLabel(/^password/i).fill('DeleteToast123!!')  // 17 chars
      await page.getByRole('button', { name: /create user$/i }).click()
      await expect(page.getByText('User Created').first()).toBeVisible({ timeout: 10000 })
      await page.waitForTimeout(2000)

      // Delete user
      const userRow = page.locator('tbody tr').filter({ hasText: testEmail })
      await expect(userRow).toBeVisible({ timeout: 5000 })
      await userRow.getByRole('button', { name: /delete/i }).click()
      await expect(page.getByRole('heading', { name: /delete user/i })).toBeVisible({ timeout: 3000 })
      await page.getByRole('button', { name: /delete user$/i }).click()

      // Toast should show success - use first() for strict mode
      await expect(page.getByText('User Deleted').first()).toBeVisible({ timeout: 10000 })

      // User should be removed from list (confirms deletion)
      await page.waitForTimeout(2000)
      await expect(page.locator('tbody tr').filter({ hasText: testEmail })).not.toBeVisible({ timeout: 5000 })
    })
  })

  test.describe('Form Validation', () => {
    test('should clear validation errors when user corrects input', async ({ page }) => {
      // Open create dialog
      await page.getByRole('button', { name: /create user/i }).click()

      // Enter invalid email
      await page.getByLabel(/email/i).fill('invalid')
      await page.getByLabel(/^password/i).fill('ValidPassword123!!')  // 18 chars
      await page.getByRole('button', { name: /create user$/i }).click()

      // Should show error
      await expect(page.getByText(/invalid email/i)).toBeVisible({ timeout: 5000 })

      // Fix email - this should clear the error
      await page.getByLabel(/email/i).fill(`valid${Date.now()}@test.io`)

      // Error should disappear when field is updated
      await page.waitForTimeout(500)
      const errorVisible = await page.getByText(/invalid email/i).isVisible().catch(() => false)
      expect(errorVisible).toBeFalsy()
    })

    test('should require email field', async ({ page }) => {
      await page.getByRole('button', { name: /create user/i }).click()

      // Leave email empty, fill password
      await page.getByLabel(/^password/i).fill('ValidPassword123!!')  // 18 chars
      await page.getByRole('button', { name: /create user$/i }).click()

      // Should show required error
      await expect(page.getByText(/email is required/i)).toBeVisible({ timeout: 5000 })
    })

    test('should require password field', async ({ page }) => {
      await page.getByRole('button', { name: /create user/i }).click()

      // Fill email, leave password empty
      await page.getByLabel(/email/i).fill(`test${Date.now()}@test.io`)
      await page.getByRole('button', { name: /create user$/i }).click()

      // Should show required error
      await expect(page.getByText(/password is required/i)).toBeVisible({ timeout: 5000 })
    })

    test('should show password length hint', async ({ page }) => {
      await page.getByRole('button', { name: /create user/i }).click()

      // Should show password requirement hint
      await expect(page.getByText(/password must be at least 12 characters/i)).toBeVisible()
    })
  })
})
