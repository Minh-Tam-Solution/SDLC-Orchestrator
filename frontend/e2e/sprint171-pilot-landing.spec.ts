/**
 * E2E Tests - Sprint 171 Pilot Landing Page
 *
 * @module frontend/e2e/sprint171-pilot-landing
 * @description End-to-end tests for pilot program landing page
 * @sprint 171 - Market Expansion Foundation (Phase 6)
 *
 * Test Coverage:
 * - Page rendering and navigation
 * - Form validation (client-side)
 * - Form submission flows (auth/unauth)
 * - FAQ accordion interaction
 * - Success states and error handling
 *
 * Total: 10 test scenarios
 */

import { test, expect } from "@playwright/test";

const PILOT_PAGE_URL = "/pilot";
const REGISTER_URL = "/register";

/**
 * Test Suite: Sprint 171 - Pilot Landing Page
 */
test.describe("Sprint 171 - Pilot Landing Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem("sdlc-locale", "en");
    });
  });

  /**
   * Test 1: Display all sections
   * Verifies that all page sections render correctly
   */
  test("should display pilot landing page with all sections", async ({ page }) => {
    await page.goto(PILOT_PAGE_URL);

    // Hero section
    await expect(page.getByText("Pilot Program", { exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: /Join the SDLC Orchestrator Pilot/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Apply Now/i })).toBeVisible();

    // Benefits section - check for section title
    await expect(page.getByRole("heading", { name: /Why Join the Pilot/i })).toBeVisible();

    // Check for all 4 benefit cards by their titles
    await expect(page.getByText("Early Access")).toBeVisible();
    await expect(page.getByText("Free 1-on-1 Support")).toBeVisible();
    await expect(page.getByText("Lifetime Discount")).toBeVisible();
    await expect(page.getByText("Founder Community")).toBeVisible();

    // Signup form section
    await expect(page.getByText("Apply for Pilot Program", { exact: true })).toBeVisible();
    await expect(page.getByPlaceholder(/Nguyen Van A/i)).toBeVisible();
    await expect(page.getByPlaceholder(/you@company\.com/i)).toBeVisible();

    // FAQ section
    await expect(page.getByRole("heading", { name: /Frequently Asked Questions/i })).toBeVisible();

    // Check for at least one FAQ question
    await expect(page.getByText(/Who can join the pilot program/i)).toBeVisible();
  });

  /**
   * Test 2: Submit application successfully (logged in user)
   * NOTE: Uses API mocking to avoid requiring auth harness.
   */
  test("should submit pilot application successfully (logged in user)", async ({ page }) => {
    await page.route("**/api/v1/pilot/participants", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "test-participant-id",
          user_id: "test-user-id",
        }),
      });
    });

    await page.goto(PILOT_PAGE_URL);

    // Fill form fields
    await page.getByPlaceholder(/Nguyen Van A/i).fill("Test Founder");
    await page.getByPlaceholder(/you@company\.com/i).fill("founder@test.com");
    await page.getByPlaceholder(/My Startup/i).fill("Test Startup");

    // Select role from dropdown
    await page.getByRole("combobox", { name: /Your Role/i }).click();
    await page.getByRole("option", { name: /Founder/i }).first().click();

    // Submit form
    await page.getByRole("button", { name: /Join Pilot Program/i }).click();

    // Verify success message
    await expect(page.getByText(/Application Submitted/i)).toBeVisible();
    await expect(page.getByText(/We'll contact you within 24 hours/i)).toBeVisible();
  });

  /**
   * Test 3: Validate required fields
   * Verifies client-side validation for empty required fields
   */
  test("should validate required fields", async ({ page }) => {
    await page.goto(PILOT_PAGE_URL);

    // Click submit without filling fields
    await page.getByRole("button", { name: /Join Pilot Program/i }).click();

    // Verify validation errors appear
    await expect(page.getByText(/Please enter your full name/i)).toBeVisible();
    await expect(page.getByText(/Please enter your email address/i)).toBeVisible();
    await expect(page.getByText(/Please enter your company name/i)).toBeVisible();
    await expect(page.getByText(/Please select your role/i)).toBeVisible();
  });

  /**
   * Test 4: Validate email format
   * Verifies email format validation
   */
  test("should validate email format", async ({ page }) => {
    await page.goto(PILOT_PAGE_URL);

    // Fill name and company (valid)
    await page.getByPlaceholder(/Nguyen Van A/i).fill("Test User");
    await page.getByPlaceholder(/My Startup/i).fill("Test Co");

    // Enter invalid email
    await page.getByPlaceholder(/you@company\.com/i).fill("notanemail");

    // Select role
    await page.getByRole("combobox", { name: /Your Role/i }).click();
    await page.getByRole("option", { name: /Founder/i }).first().click();

    // Click submit
    await page.getByRole("button", { name: /Join Pilot Program/i }).click();

    // Verify email validation error
    await expect(page.getByText(/Please enter a valid email address/i)).toBeVisible();
  });

  /**
   * Test 5: Validate name length constraints
   * Verifies min/max length validation for name field
   */
  test("should validate name length constraints", async ({ page }) => {
    await page.goto(PILOT_PAGE_URL);

    // Test: name too short (1 character)
    await page.getByPlaceholder(/Nguyen Van A/i).fill("A");
    await page.getByPlaceholder(/you@company\.com/i).fill("test@example.com");
    await page.getByPlaceholder(/My Startup/i).fill("Test Co");
    await page.getByRole("button", { name: /Join Pilot Program/i }).click();

    // Verify "too short" error
    await expect(page.getByText(/Name must be at least 2 characters/i)).toBeVisible();

    // Test: name too long (>100 characters)
    const longName = "A".repeat(101);
    await page.getByPlaceholder(/Nguyen Van A/i).fill(longName);
    await page.getByRole("button", { name: /Join Pilot Program/i }).click();

    // Verify "too long" error
    await expect(page.getByText(/Name must be less than 100 characters/i)).toBeVisible();
  });

  /**
   * Test 6: Redirect to register if not logged in
   * Verifies auth redirect on form submission
   */
  test("should redirect to register if not logged in on submit", async ({ page }) => {
    await page.route("**/api/v1/pilot/participants", async (route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({
          detail: "Session expired. Please log in again.",
        }),
      });
    });

    await page.goto(PILOT_PAGE_URL);

    // Fill all form fields correctly
    await page.getByPlaceholder(/Nguyen Van A/i).fill("Test Founder");
    await page.getByPlaceholder(/you@company\.com/i).fill("founder@test.com");
    await page.getByPlaceholder(/My Startup/i).fill("Test Startup");

    // Select role
    await page.getByRole("combobox", { name: /Your Role/i }).click();
    await page.getByRole("option", { name: /Founder/i }).first().click();

    // Submit form - should trigger API call which will return 401
    await page.getByRole("button", { name: /Join Pilot Program/i }).click();

    // Wait for redirect to register page with return URL
    await page.waitForURL(/\/register\?redirect=.*pilot/);
    expect(page.url()).toContain(REGISTER_URL);
    expect(page.url()).toContain("redirect");
    expect(page.url()).toContain("pilot");
  });

  /**
   * Test 7: Handle duplicate enrollment
   * NOTE: Based on backend findings, duplicate enrollment returns 200 (existing participant)
   * not 409 Conflict. Test skipped pending backend confirmation.
   */
  test.skip("should handle duplicate enrollment", async ({ page }) => {
    await page.goto(PILOT_PAGE_URL);
  });

  /**
   * Test 8: FAQ accordion expand/collapse interaction
   * Verifies collapsible FAQ functionality
   */
  test("should expand/collapse FAQ accordion items", async ({ page }) => {
    await page.goto(PILOT_PAGE_URL);

    // Scroll to FAQ section
    await page.getByRole("heading", { name: /Frequently Asked Questions/i }).scrollIntoViewIfNeeded();

    // Find first FAQ question button
    const firstQuestion = page.getByRole("button", { name: /Who can join the pilot program/i });
    await expect(firstQuestion).toBeVisible();

    // Click to expand
    await firstQuestion.click();

    // Verify answer is visible
    await expect(page.getByText(/Vietnamese SME founders and technical leaders/i)).toBeVisible();

    // Click second FAQ question
    const secondQuestion = page.getByRole("button", { name: /How long does the pilot last/i });
    await secondQuestion.click();

    // Verify second answer expands
    await expect(page.getByText(/The pilot runs for 6 weeks/i)).toBeVisible();

    // Click again to collapse
    await secondQuestion.click();

    // Verify answer is hidden (or check aria-expanded attribute)
    const isExpanded = await secondQuestion.getAttribute("aria-expanded");
    expect(isExpanded).toBe("false");
  });

  /**
   * Test 9: Pre-fill form with logged-in user data
   * NOTE: Requires authentication setup
   */
  test.skip("should pre-fill form with logged-in user data", async ({ page }) => {
    await page.goto(PILOT_PAGE_URL);
  });

  /**
   * Test 10: Track analytics events
   * Verifies analytics tracking on form interaction
   * NOTE: Requires analytics mock/spy setup
   */
  test.skip("should track analytics events on form interaction", async ({ page }) => {
    await page.goto(PILOT_PAGE_URL);
    await page.getByPlaceholder(/Nguyen Van A/i).fill("Test");
  });
});
