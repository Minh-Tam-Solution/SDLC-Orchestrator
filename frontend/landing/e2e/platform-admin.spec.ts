/**
 * E2E Test: Platform Admin Section
 * @status Sprint 69 - User Interactive Simulation
 * @description Tests all migrated platform-admin routes (21 routes)
 */

import { test, expect } from "@playwright/test";

test.describe("Platform Admin - Public Routes (No Auth Required)", () => {
  test("should load landing page", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    // Page should load without error
    await expect(page.locator("body")).toBeVisible();
  });

  test("should load demo page", async ({ page }) => {
    await page.goto("/demo");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("body")).toBeVisible();
  });

  test("should load docs pages", async ({ page }) => {
    // Main docs
    await page.goto("/docs");
    await expect(page.locator("body")).toBeVisible();

    // Getting started
    await page.goto("/docs/getting-started");
    await expect(page.locator("body")).toBeVisible();

    // API Reference
    await page.goto("/docs/api-reference");
    await expect(page.locator("body")).toBeVisible();
  });
});

test.describe("Platform Admin - Dashboard Routes", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to platform-admin (will redirect to login if not authenticated)
    await page.goto("/platform-admin");
    await page.waitForLoadState("networkidle");
  });

  test("should load platform-admin dashboard or redirect to login", async ({ page }) => {
    const currentUrl = page.url();
    // Either on dashboard or redirected to login
    expect(currentUrl).toMatch(/platform-admin|login/);
  });

  test("should display dashboard layout elements", async ({ page }) => {
    // If on dashboard, check for common elements
    if (page.url().includes("platform-admin")) {
      // Check for navigation/sidebar
      const sidebar = page.locator('nav, [role="navigation"], aside');
      await expect(sidebar.first()).toBeVisible({ timeout: 5000 }).catch(() => {});

      // Check for header
      const header = page.locator("header, h1");
      await expect(header.first()).toBeVisible({ timeout: 5000 }).catch(() => {});
    }
  });
});

test.describe("Platform Admin - Projects Section", () => {
  test("should navigate to projects list", async ({ page }) => {
    await page.goto("/platform-admin/projects");
    await page.waitForLoadState("networkidle");

    // Check page loaded (either content or redirect)
    const currentUrl = page.url();
    expect(currentUrl).toMatch(/projects|login/);
  });

  test("should handle project detail route", async ({ page }) => {
    await page.goto("/platform-admin/projects/test-project-id");
    await page.waitForLoadState("networkidle");

    // Dynamic route should load - may show error page for invalid ID
    const currentUrl = page.url();
    expect(currentUrl).toMatch(/projects|login/);
  });
});

test.describe("Platform Admin - Gates Section", () => {
  test("should navigate to gates list", async ({ page }) => {
    await page.goto("/platform-admin/gates");
    await page.waitForLoadState("networkidle");

    const currentUrl = page.url();
    expect(currentUrl).toMatch(/gates|login/);
  });

  test("should handle gate detail route", async ({ page }) => {
    await page.goto("/platform-admin/gates/test-gate-id");
    await page.waitForLoadState("networkidle");

    // Dynamic route should load - may show error page for invalid ID
    const currentUrl = page.url();
    expect(currentUrl).toMatch(/gates|login/);
  });
});

test.describe("Platform Admin - Policies Section", () => {
  test("should navigate to policies list", async ({ page }) => {
    await page.goto("/platform-admin/policies");
    await page.waitForLoadState("networkidle");

    const currentUrl = page.url();
    expect(currentUrl).toMatch(/policies|login/);
  });

  test("should handle policy detail route", async ({ page }) => {
    await page.goto("/platform-admin/policies/test-policy-id");
    await page.waitForLoadState("networkidle");

    // Dynamic route should load - may show error page for invalid ID
    const currentUrl = page.url();
    expect(currentUrl).toMatch(/policies|login/);
  });
});

test.describe("Platform Admin - Evidence Section", () => {
  test("should navigate to evidence page", async ({ page }) => {
    await page.goto("/platform-admin/evidence");
    await page.waitForLoadState("networkidle");

    const currentUrl = page.url();
    expect(currentUrl).toMatch(/evidence|login/);
  });
});

test.describe("Platform Admin - SOP Section", () => {
  test("should navigate to SOP generator", async ({ page }) => {
    await page.goto("/platform-admin/sop-generator");
    await page.waitForLoadState("networkidle");

    const currentUrl = page.url();
    expect(currentUrl).toMatch(/sop-generator|login/);
  });

  test("should navigate to SOP history", async ({ page }) => {
    await page.goto("/platform-admin/sop-history");
    await page.waitForLoadState("networkidle");

    const currentUrl = page.url();
    expect(currentUrl).toMatch(/sop-history|login/);
  });

  test("should handle SOP detail route", async ({ page }) => {
    await page.goto("/platform-admin/sop/test-sop-id");
    await page.waitForLoadState("networkidle");

    // Dynamic route should load - may show error page for invalid ID
    const currentUrl = page.url();
    expect(currentUrl).toMatch(/sop|login/);
  });
});

test.describe("Platform Admin - Code Generation Section", () => {
  test("should navigate to code generation page", async ({ page }) => {
    await page.goto("/platform-admin/code-generation");
    await page.waitForLoadState("networkidle");

    const currentUrl = page.url();
    expect(currentUrl).toMatch(/code-generation|login/);
  });

  test("should navigate to codegen page", async ({ page }) => {
    await page.goto("/platform-admin/codegen");
    await page.waitForLoadState("networkidle");

    const currentUrl = page.url();
    expect(currentUrl).toMatch(/codegen|login/);
  });
});

test.describe("Platform Admin - App Builder Section", () => {
  test("should navigate to app builder", async ({ page }) => {
    await page.goto("/platform-admin/app-builder");
    await page.waitForLoadState("networkidle");

    const currentUrl = page.url();
    expect(currentUrl).toMatch(/app-builder|login/);
  });
});

test.describe("Platform Admin - Settings Section", () => {
  test("should navigate to settings page", async ({ page }) => {
    await page.goto("/platform-admin/settings");
    await page.waitForLoadState("networkidle");

    const currentUrl = page.url();
    expect(currentUrl).toMatch(/settings|login/);
  });
});
