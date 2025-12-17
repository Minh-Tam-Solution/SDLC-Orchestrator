/**
 * File: frontend/web/e2e/helpers/auth.ts
 * Version: 1.1.0
 * Status: ACTIVE - Sprint 38 E2E Testing
 * Date: 2025-12-17
 * Authority: Frontend Lead + CTO Approved
 * Foundation: SDLC 5.1.1 Complete Lifecycle, Zero Mock Policy
 *
 * Description:
 * Authentication helper functions for E2E tests.
 * Provides reusable login/logout utilities.
 *
 * Changelog:
 * - v1.1.0 (2025-12-17): Add admin login helper for Admin Panel tests
 * - v1.0.0 (2025-11-27): Initial implementation
 */

import { Page, expect } from '@playwright/test'

export const TEST_USER = {
  email: 'admin@sdlc-orchestrator.io',
  password: 'Admin@123',
}

export const TEST_ADMIN = {
  email: 'admin@sdlc-orchestrator.io',
  password: 'Admin@123',
  is_superuser: true,
}

export const TEST_REGULAR_USER = {
  email: 'user@sdlc-orchestrator.io',
  password: 'User@123',
  is_superuser: false,
}

/**
 * Login to the application with test credentials.
 * Uses flexible selectors to handle different input implementations.
 * Includes retry logic for parallel test stability.
 */
export async function login(page: Page, email = TEST_USER.email, password = TEST_USER.password): Promise<void> {
  const maxRetries = 3
  let lastError: Error | null = null

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      // Navigate to login page
      await page.goto('/login', { waitUntil: 'domcontentloaded' })

      // Wait for page to be ready
      await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {
        // Continue even if networkidle times out
      })

      // Check if already logged in (redirected to dashboard)
      if (!page.url().includes('/login')) {
        return // Already logged in
      }

      // Find and fill email input (try multiple selectors)
      const emailInput = page.locator('input[type="email"], input#email, input[name="email"]').first()
      await emailInput.waitFor({ state: 'visible', timeout: 10000 })
      await emailInput.clear()
      await emailInput.fill(email)

      // Find and fill password input
      const passwordInput = page.locator('input[type="password"], input#password, input[name="password"]').first()
      await passwordInput.waitFor({ state: 'visible', timeout: 5000 })
      await passwordInput.clear()
      await passwordInput.fill(password)

      // Click login button
      const loginButton = page.getByRole('button', { name: /sign in|login|submit/i })
      await loginButton.click()

      // Wait for navigation away from login page
      await Promise.race([
        page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 15000 }),
        page.waitForSelector('.error, [role="alert"]', { timeout: 15000 }).then(() => {
          throw new Error('Login error displayed')
        }).catch(() => {
          // No error displayed, continue waiting for redirect
        })
      ])

      // Verify we're not on login page
      if (!page.url().includes('/login')) {
        return // Success
      }

      throw new Error('Still on login page after submit')
    } catch (error) {
      lastError = error as Error
      if (attempt < maxRetries) {
        // Wait before retry with exponential backoff
        await page.waitForTimeout(1000 * attempt)
      }
    }
  }

  throw lastError || new Error('Login failed after max retries')
}

/**
 * Login as admin user (superuser).
 * Verifies that the logged-in user has admin privileges.
 */
export async function loginAsAdmin(page: Page): Promise<void> {
  await login(page, TEST_ADMIN.email, TEST_ADMIN.password)

  // Verify admin sidebar item is visible (only for superusers)
  await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {})

  // Admin Panel link should be visible in sidebar
  const adminLink = page.locator('a[href="/admin"]')
  await expect(adminLink).toBeVisible({ timeout: 5000 })
}

/**
 * Login as regular user (non-superuser).
 * Verifies that admin features are NOT visible.
 */
export async function loginAsRegularUser(page: Page): Promise<void> {
  await login(page, TEST_REGULAR_USER.email, TEST_REGULAR_USER.password)

  // Verify admin sidebar item is NOT visible
  await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {})

  // Admin Panel link should NOT be visible
  const adminLink = page.locator('a[href="/admin"]')
  await expect(adminLink).not.toBeVisible({ timeout: 3000 })
}

/**
 * Logout from the application.
 * Handles different logout implementations (button, menu item).
 */
export async function logout(page: Page): Promise<void> {
  // Try direct logout button first (with testid)
  const logoutButtonTestId = page.getByTestId('logout')
  if (await logoutButtonTestId.isVisible({ timeout: 2000 }).catch(() => false)) {
    await logoutButtonTestId.click()
    await expect(page).toHaveURL(/\/(login|auth)/, { timeout: 5000 })
    return
  }

  // Try logout button by role
  const logoutButton = page.getByRole('button', { name: /logout|sign out/i })
  if (await logoutButton.isVisible({ timeout: 2000 }).catch(() => false)) {
    await logoutButton.click()
  } else {
    // Try user menu dropdown
    const userMenuTrigger = page.locator('[data-testid="user-menu"], button:has-text("Account"), .user-menu-trigger').first()

    if (await userMenuTrigger.isVisible({ timeout: 2000 }).catch(() => false)) {
      await userMenuTrigger.click()
      await page.getByRole('menuitem', { name: /logout|sign out/i }).click()
    } else {
      // Last resort - find any logout link
      const logoutLink = page.locator('a[href*="logout"], button:has-text("Log out")').first()
      if (await logoutLink.isVisible({ timeout: 2000 }).catch(() => false)) {
        await logoutLink.click()
      }
    }
  }

  // Wait for redirect to auth page
  await expect(page).toHaveURL(/\/(login|auth)/, { timeout: 5000 })
}

/**
 * Check if user is logged in by verifying dashboard access.
 */
export async function isLoggedIn(page: Page): Promise<boolean> {
  try {
    await page.goto('/')
    await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {})
    return !page.url().includes('/login')
  } catch {
    return false
  }
}

/**
 * Navigate to Admin Panel.
 * Requires admin login first.
 */
export async function navigateToAdmin(page: Page): Promise<void> {
  await page.goto('/admin')
  await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {})

  // Verify we're on admin page
  await expect(page.getByRole('heading', { name: /admin dashboard/i })).toBeVisible({ timeout: 5000 })
}
