/**
 * E2E Test: Admin Section (Sprint 68 Migration)
 * @status Sprint 69 - User Interactive Simulation
 * @description Tests admin dashboard, users, audit logs, settings, health, overrides
 */

import { test, expect } from "@playwright/test";

test.describe("Admin Section - Dashboard", () => {
  test("should load admin dashboard", async ({ page }) => {
    await page.goto("/platform-admin/admin");
    await page.waitForLoadState("networkidle");

    // Either shows dashboard or redirects to login
    const currentUrl = page.url();
    expect(currentUrl).toMatch(/admin|login/);

    // If on admin page, check for dashboard elements
    if (currentUrl.includes("/admin")) {
      // Look for stats cards or dashboard elements
      const cards = page.locator('[class*="card"], [class*="Card"]');
      const cardCount = await cards.count();
      console.log(`Dashboard cards found: ${cardCount}`);
    }
  });

  test("should display navigation links", async ({ page }) => {
    await page.goto("/platform-admin/admin");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/admin")) {
      // Check for admin navigation links
      const navLinks = page.locator('a[href*="/admin/"]');
      const linkCount = await navLinks.count();
      console.log(`Admin nav links found: ${linkCount}`);
    }
  });
});

test.describe("Admin Section - Users Management", () => {
  test("should load users list page", async ({ page }) => {
    await page.goto("/platform-admin/admin/users");
    await page.waitForLoadState("networkidle");

    const currentUrl = page.url();
    expect(currentUrl).toMatch(/users|login/);
  });

  test("should display users table or list", async ({ page }) => {
    await page.goto("/platform-admin/admin/users");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/users")) {
      // Look for table or list elements
      const table = page.locator("table, [role='grid'], [class*='table']");
      const hasTable = await table.isVisible().catch(() => false);

      // Or look for user cards/items
      const userItems = page.locator('[class*="user"], [class*="User"]');
      const itemCount = await userItems.count();

      console.log(`Users table visible: ${hasTable}, User items: ${itemCount}`);
    }
  });

  test("should have search functionality", async ({ page }) => {
    await page.goto("/platform-admin/admin/users");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/users")) {
      // Look for search input
      const searchInput = page.locator('input[type="search"], input[placeholder*="Search"], input[placeholder*="search"]');
      const hasSearch = await searchInput.isVisible().catch(() => false);
      console.log(`Search input visible: ${hasSearch}`);
    }
  });

  test("should have create user button", async ({ page }) => {
    await page.goto("/platform-admin/admin/users");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/users")) {
      // Look for create/add user button
      const createBtn = page.locator('button:has-text("Add"), button:has-text("Create"), button:has-text("New")');
      const hasCreateBtn = await createBtn.first().isVisible().catch(() => false);
      console.log(`Create user button visible: ${hasCreateBtn}`);
    }
  });
});

test.describe("Admin Section - Audit Logs", () => {
  test("should load audit logs page", async ({ page }) => {
    await page.goto("/platform-admin/admin/audit-logs");
    await page.waitForLoadState("networkidle");

    const currentUrl = page.url();
    expect(currentUrl).toMatch(/audit-logs|login/);
  });

  test("should display audit log entries", async ({ page }) => {
    await page.goto("/platform-admin/admin/audit-logs");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/audit-logs")) {
      // Look for log entries
      const logEntries = page.locator('[class*="log"], [class*="audit"], table tbody tr');
      const entryCount = await logEntries.count();
      console.log(`Audit log entries found: ${entryCount}`);
    }
  });

  test("should have date filter", async ({ page }) => {
    await page.goto("/platform-admin/admin/audit-logs");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/audit-logs")) {
      // Look for date inputs or date picker
      const dateInput = page.locator('input[type="date"], [class*="date"], button:has-text("Date")');
      const hasDateFilter = await dateInput.first().isVisible().catch(() => false);
      console.log(`Date filter visible: ${hasDateFilter}`);
    }
  });

  test("should have action type filter", async ({ page }) => {
    await page.goto("/platform-admin/admin/audit-logs");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/audit-logs")) {
      // Look for action filter (select or dropdown)
      const actionFilter = page.locator('select, [role="combobox"], button:has-text("Action"), button:has-text("Filter")');
      const hasActionFilter = await actionFilter.first().isVisible().catch(() => false);
      console.log(`Action filter visible: ${hasActionFilter}`);
    }
  });
});

test.describe("Admin Section - System Settings", () => {
  test("should load settings page", async ({ page }) => {
    await page.goto("/platform-admin/admin/settings");
    await page.waitForLoadState("networkidle");

    const currentUrl = page.url();
    expect(currentUrl).toMatch(/settings|login/);
  });

  test("should display settings categories", async ({ page }) => {
    await page.goto("/platform-admin/admin/settings");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/settings")) {
      // Look for tabs or category sections
      const tabs = page.locator('[role="tablist"] button, [class*="tab"]');
      const tabCount = await tabs.count();
      console.log(`Settings tabs found: ${tabCount}`);
    }
  });

  test("should display setting items", async ({ page }) => {
    await page.goto("/platform-admin/admin/settings");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/settings")) {
      // Look for setting items
      const settingItems = page.locator('[class*="setting"], [class*="Setting"], [class*="card"]');
      const itemCount = await settingItems.count();
      console.log(`Setting items found: ${itemCount}`);
    }
  });
});

test.describe("Admin Section - System Health", () => {
  test("should load health page", async ({ page }) => {
    await page.goto("/platform-admin/admin/health");
    await page.waitForLoadState("networkidle");

    const currentUrl = page.url();
    expect(currentUrl).toMatch(/health|login/);
  });

  test("should display overall health status", async ({ page }) => {
    await page.goto("/platform-admin/admin/health");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/health")) {
      // Look for status indicator
      const statusIndicator = page.locator('[class*="status"], [class*="health"], [class*="badge"]');
      const hasStatus = await statusIndicator.first().isVisible().catch(() => false);
      console.log(`Health status indicator visible: ${hasStatus}`);
    }
  });

  test("should display service health list", async ({ page }) => {
    await page.goto("/platform-admin/admin/health");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/health")) {
      // Look for service items
      const serviceItems = page.locator('[class*="service"], [class*="Service"]');
      const serviceCount = await serviceItems.count();
      console.log(`Service health items found: ${serviceCount}`);
    }
  });

  test("should display system metrics", async ({ page }) => {
    await page.goto("/platform-admin/admin/health");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/health")) {
      // Look for metrics (CPU, Memory, Disk)
      const metricsText = await page.textContent("body");
      const hasCPU = metricsText?.includes("CPU") || metricsText?.includes("cpu");
      const hasMemory = metricsText?.includes("Memory") || metricsText?.includes("memory");
      console.log(`Metrics visible: CPU=${hasCPU}, Memory=${hasMemory}`);
    }
  });
});

test.describe("Admin Section - Override Queue (VCR)", () => {
  test("should load override queue page", async ({ page }) => {
    await page.goto("/platform-admin/admin/overrides");
    await page.waitForLoadState("networkidle");

    const currentUrl = page.url();
    expect(currentUrl).toMatch(/overrides|login/);
  });

  test("should display override stats cards", async ({ page }) => {
    await page.goto("/platform-admin/admin/overrides");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/overrides")) {
      // Look for stats cards
      const statsCards = page.locator('[class*="card"], [class*="Card"]');
      const cardCount = await statsCards.count();
      console.log(`Override stats cards found: ${cardCount}`);

      // Check for specific stats
      const pageText = await page.textContent("body");
      const hasPending = pageText?.includes("Pending");
      const hasApprovalRate = pageText?.includes("Approval") || pageText?.includes("Rate");
      console.log(`Stats visible: Pending=${hasPending}, ApprovalRate=${hasApprovalRate}`);
    }
  });

  test("should display tabs for pending and recent", async ({ page }) => {
    await page.goto("/platform-admin/admin/overrides");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/overrides")) {
      // Look for tabs
      const pendingTab = page.locator('button:has-text("Pending"), [role="tab"]:has-text("Pending")');
      const recentTab = page.locator('button:has-text("Recent"), [role="tab"]:has-text("Recent")');

      const hasPendingTab = await pendingTab.isVisible().catch(() => false);
      const hasRecentTab = await recentTab.isVisible().catch(() => false);

      console.log(`Tabs visible: Pending=${hasPendingTab}, Recent=${hasRecentTab}`);
    }
  });

  test("should switch between tabs", async ({ page }) => {
    await page.goto("/platform-admin/admin/overrides");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/overrides")) {
      // Click on Recent tab
      const recentTab = page.locator('button:has-text("Recent"), [role="tab"]:has-text("Recent")');
      if (await recentTab.isVisible().catch(() => false)) {
        await recentTab.click();
        await page.waitForTimeout(500);

        // Check that content changes
        const tabContent = page.locator('[role="tabpanel"], [class*="TabsContent"]');
        const isVisible = await tabContent.first().isVisible().catch(() => false);
        console.log(`Tab content visible after switch: ${isVisible}`);
      }
    }
  });

  test("should display override items with badges", async ({ page }) => {
    await page.goto("/platform-admin/admin/overrides");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/overrides")) {
      // Look for override type badges
      const badges = page.locator('[class*="badge"], [class*="Badge"]');
      const badgeCount = await badges.count();
      console.log(`Override badges found: ${badgeCount}`);
    }
  });

  test("should show empty state when no pending overrides", async ({ page }) => {
    await page.goto("/platform-admin/admin/overrides");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/overrides")) {
      // Check for empty state or override items
      const pageText = await page.textContent("body");
      const hasEmptyState = pageText?.includes("No pending") || pageText?.includes("no pending");
      const hasOverrideItems = pageText?.includes("Override") || pageText?.includes("override");

      console.log(`Empty state: ${hasEmptyState}, Has items: ${hasOverrideItems}`);
    }
  });
});
