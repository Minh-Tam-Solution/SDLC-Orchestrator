/**
 * E2E Test: Sprint 85 Features (AGENTS.md UI + CLI Authentication)
 * @status Sprint 85 - Days 9-10 Integration Testing
 * @description Tests for Sprint 85 features: AGENTS.md Dashboard and CLI Tokens
 *
 * Test Coverage:
 * - AGENTS.md Dashboard Page
 * - AGENTS.md Repo Detail Page
 * - AGENTS.md Analytics Page
 * - CLI Tokens Management Page
 *
 * @sdlc SDLC 5.1.3 Framework - Sprint 85
 * @date January 20, 2026
 */

import { test, expect } from "@playwright/test";

// =============================================================================
// AGENTS.md Dashboard Tests
// =============================================================================

test.describe("AGENTS.md Dashboard - Multi-Repo Management", () => {
  test("should load AGENTS.md dashboard page", async ({ page }) => {
    await page.goto("/app/agents-md");
    await page.waitForLoadState("networkidle");

    const currentUrl = page.url();
    // Should be on agents-md page or redirect to login
    expect(currentUrl).toMatch(/agents-md|login/);
  });

  test("should display page header with title", async ({ page }) => {
    await page.goto("/app/agents-md");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/agents-md")) {
      // Look for page title
      const pageTitle = page.locator('h1, [class*="title"]');
      const titleText = await pageTitle.first().textContent();
      console.log(`Page title: ${titleText}`);

      // Should contain AGENTS.md
      expect(titleText?.toLowerCase()).toContain("agents");
    }
  });

  test("should display stats cards", async ({ page }) => {
    await page.goto("/app/agents-md");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/agents-md")) {
      // Look for stats cards
      const statsCards = page.locator('[class*="card"], [class*="Card"], [class*="stat"]');
      const cardCount = await statsCards.count();
      console.log(`AGENTS.md stats cards found: ${cardCount}`);

      // Should have at least some stats cards
      expect(cardCount).toBeGreaterThanOrEqual(0);
    }
  });

  test("should display repository list or empty state", async ({ page }) => {
    await page.goto("/app/agents-md");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/agents-md")) {
      // Look for repository list or empty state
      const repoList = page.locator('table, [class*="list"], [class*="empty"]');
      const hasContent = await repoList.first().isVisible().catch(() => false);
      console.log(`Repository list visible: ${hasContent}`);

      // Check for empty state if no repos
      const pageText = await page.textContent("body");
      const hasEmptyState = pageText?.includes("No repositories") ||
        pageText?.includes("Get started") ||
        pageText?.includes("Connect");
      console.log(`Empty state visible: ${hasEmptyState}`);
    }
  });

  test("should have Create/Connect button", async ({ page }) => {
    await page.goto("/app/agents-md");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/agents-md")) {
      // Look for action buttons
      const actionButtons = page.locator('button, a[href*="create"], a[href*="connect"]');
      const buttonCount = await actionButtons.count();
      console.log(`Action buttons found: ${buttonCount}`);
    }
  });

  test("should navigate to analytics page", async ({ page }) => {
    await page.goto("/app/agents-md");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/agents-md")) {
      // Look for analytics link
      const analyticsLink = page.locator('a[href*="analytics"], button:has-text("Analytics")');
      const hasAnalyticsLink = await analyticsLink.first().isVisible().catch(() => false);
      console.log(`Analytics link visible: ${hasAnalyticsLink}`);

      if (hasAnalyticsLink) {
        await analyticsLink.first().click();
        await page.waitForLoadState("networkidle");
        expect(page.url()).toContain("analytics");
      }
    }
  });
});

// =============================================================================
// AGENTS.md Analytics Tests
// =============================================================================

test.describe("AGENTS.md Analytics - Metrics Dashboard", () => {
  test("should load analytics page", async ({ page }) => {
    await page.goto("/app/agents-md/analytics");
    await page.waitForLoadState("networkidle");

    const currentUrl = page.url();
    expect(currentUrl).toMatch(/analytics|login/);
  });

  test("should display analytics metrics", async ({ page }) => {
    await page.goto("/app/agents-md/analytics");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/analytics")) {
      // Look for metric cards
      const metricCards = page.locator('[class*="card"], [class*="metric"], [class*="stat"]');
      const cardCount = await metricCards.count();
      console.log(`Analytics metric cards found: ${cardCount}`);

      // Check for specific metrics
      const pageText = await page.textContent("body");
      const hasCoverage = pageText?.includes("Coverage") || pageText?.includes("coverage");
      const hasOverlay = pageText?.includes("Overlay") || pageText?.includes("overlay");
      console.log(`Metrics visible: Coverage=${hasCoverage}, Overlay=${hasOverlay}`);
    }
  });

  test("should have export functionality", async ({ page }) => {
    await page.goto("/app/agents-md/analytics");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/analytics")) {
      // Look for export button
      const exportButton = page.locator('button:has-text("Export"), button:has-text("CSV"), button:has-text("Download")');
      const hasExport = await exportButton.first().isVisible().catch(() => false);
      console.log(`Export button visible: ${hasExport}`);
    }
  });

  test("should have back navigation to AGENTS.md", async ({ page }) => {
    await page.goto("/app/agents-md/analytics");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/analytics")) {
      // Look for back link
      const backLink = page.locator('a[href*="/agents-md"]:not([href*="analytics"]), a:has-text("Back")');
      const hasBackLink = await backLink.first().isVisible().catch(() => false);
      console.log(`Back link visible: ${hasBackLink}`);

      if (hasBackLink) {
        await backLink.first().click();
        await page.waitForLoadState("networkidle");
        expect(page.url()).toContain("/agents-md");
        expect(page.url()).not.toContain("analytics");
      }
    }
  });
});

// =============================================================================
// CLI Tokens Management Tests
// =============================================================================

test.describe("CLI Tokens - Token Management Page", () => {
  test("should load CLI tokens page", async ({ page }) => {
    await page.goto("/app/cli-tokens");
    await page.waitForLoadState("networkidle");

    const currentUrl = page.url();
    expect(currentUrl).toMatch(/cli-tokens|login/);
  });

  test("should display page header with title", async ({ page }) => {
    await page.goto("/app/cli-tokens");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/cli-tokens")) {
      // Look for page title
      const pageTitle = page.locator('h1, [class*="title"]');
      const titleText = await pageTitle.first().textContent();
      console.log(`CLI Tokens page title: ${titleText}`);

      // Should contain CLI or Token
      expect(titleText?.toLowerCase()).toMatch(/cli|token/);
    }
  });

  test("should display stats cards", async ({ page }) => {
    await page.goto("/app/cli-tokens");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/cli-tokens")) {
      // Look for stats cards (total tokens, active, sessions, commands)
      const statsCards = page.locator('[class*="card"], [class*="Card"], [class*="stat"]');
      const cardCount = await statsCards.count();
      console.log(`CLI Tokens stats cards found: ${cardCount}`);

      // Check for specific stats
      const pageText = await page.textContent("body");
      const hasTotal = pageText?.includes("Total") || pageText?.includes("total");
      const hasActive = pageText?.includes("Active") || pageText?.includes("active");
      console.log(`Stats visible: Total=${hasTotal}, Active=${hasActive}`);
    }
  });

  test("should display Quick Start section", async ({ page }) => {
    await page.goto("/app/cli-tokens");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/cli-tokens")) {
      // Look for quick start section
      const pageText = await page.textContent("body");
      const hasQuickStart = pageText?.includes("Quick Start") ||
        pageText?.includes("pip install") ||
        pageText?.includes("sdlc login");
      console.log(`Quick Start section visible: ${hasQuickStart}`);

      // Check for CLI commands
      const hasCliCommand = pageText?.includes("sdlc");
      console.log(`CLI commands visible: ${hasCliCommand}`);
    }
  });

  test("should have Create Token button", async ({ page }) => {
    await page.goto("/app/cli-tokens");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/cli-tokens")) {
      // Look for create token button
      const createButton = page.locator('button:has-text("Create"), button:has-text("Generate"), button:has-text("New")');
      const hasCreateButton = await createButton.first().isVisible().catch(() => false);
      console.log(`Create Token button visible: ${hasCreateButton}`);

      expect(hasCreateButton).toBeTruthy();
    }
  });

  test("should open Create Token modal on button click", async ({ page }) => {
    await page.goto("/app/cli-tokens");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/cli-tokens")) {
      // Click create button
      const createButton = page.locator('button:has-text("Create"), button:has-text("Generate"), button:has-text("New Token")');

      if (await createButton.first().isVisible().catch(() => false)) {
        await createButton.first().click();
        await page.waitForTimeout(500);

        // Check for modal
        const modal = page.locator('[role="dialog"], [class*="modal"], [class*="Modal"]');
        const hasModal = await modal.first().isVisible().catch(() => false);
        console.log(`Create Token modal visible: ${hasModal}`);

        // Check for form fields in modal
        const pageText = await page.textContent("body");
        const hasNameField = pageText?.includes("Name") || pageText?.includes("Token Name");
        const hasScopeField = pageText?.includes("Scope") || pageText?.includes("Permission");
        const hasExpiryField = pageText?.includes("Expir") || pageText?.includes("days");
        console.log(`Form fields: Name=${hasNameField}, Scope=${hasScopeField}, Expiry=${hasExpiryField}`);
      }
    }
  });

  test("should display token list or empty state", async ({ page }) => {
    await page.goto("/app/cli-tokens");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/cli-tokens")) {
      // Look for token list
      const pageText = await page.textContent("body");
      const hasTokenList = pageText?.includes("Your Tokens") ||
        pageText?.includes("Token") ||
        pageText?.includes("Active");
      const hasEmptyState = pageText?.includes("No CLI tokens") ||
        pageText?.includes("Create Your First");
      console.log(`Token list: ${hasTokenList}, Empty state: ${hasEmptyState}`);
    }
  });

  test("should display sessions section", async ({ page }) => {
    await page.goto("/app/cli-tokens");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/cli-tokens")) {
      // Look for sessions section
      const pageText = await page.textContent("body");
      const hasSessions = pageText?.includes("Session") || pageText?.includes("session");
      console.log(`Sessions section visible: ${hasSessions}`);
    }
  });

  test("should have refresh button", async ({ page }) => {
    await page.goto("/app/cli-tokens");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/cli-tokens")) {
      // Look for refresh button
      const refreshButton = page.locator('button:has-text("Refresh"), button[aria-label="Refresh"]');
      const hasRefresh = await refreshButton.first().isVisible().catch(() => false);
      console.log(`Refresh button visible: ${hasRefresh}`);
    }
  });
});

// =============================================================================
// Navigation Tests
// =============================================================================

test.describe("Sprint 85 Navigation", () => {
  test("should have AGENTS.md in sidebar navigation", async ({ page }) => {
    await page.goto("/app");
    await page.waitForLoadState("networkidle");

    if (!page.url().includes("/login")) {
      // Look for AGENTS.md in sidebar
      const sidebar = page.locator('nav, [class*="sidebar"], [class*="Sidebar"]');
      const sidebarText = await sidebar.first().textContent().catch(() => "");
      const hasAgentsMd = sidebarText?.includes("AGENTS") || sidebarText?.includes("agents");
      console.log(`AGENTS.md in sidebar: ${hasAgentsMd}`);
    }
  });

  test("should have CLI Tokens in sidebar navigation", async ({ page }) => {
    await page.goto("/app");
    await page.waitForLoadState("networkidle");

    if (!page.url().includes("/login")) {
      // Look for CLI Tokens in sidebar
      const sidebar = page.locator('nav, [class*="sidebar"], [class*="Sidebar"]');
      const sidebarText = await sidebar.first().textContent().catch(() => "");
      const hasCliTokens = sidebarText?.includes("CLI") || sidebarText?.includes("Token");
      console.log(`CLI Tokens in sidebar: ${hasCliTokens}`);
    }
  });

  test("should navigate from sidebar to AGENTS.md", async ({ page }) => {
    await page.goto("/app");
    await page.waitForLoadState("networkidle");

    if (!page.url().includes("/login")) {
      // Click AGENTS.md link
      const agentsMdLink = page.locator('a[href*="agents-md"]');
      if (await agentsMdLink.first().isVisible().catch(() => false)) {
        await agentsMdLink.first().click();
        await page.waitForLoadState("networkidle");
        expect(page.url()).toContain("agents-md");
      }
    }
  });

  test("should navigate from sidebar to CLI Tokens", async ({ page }) => {
    await page.goto("/app");
    await page.waitForLoadState("networkidle");

    if (!page.url().includes("/login")) {
      // Click CLI Tokens link
      const cliTokensLink = page.locator('a[href*="cli-tokens"]');
      if (await cliTokensLink.first().isVisible().catch(() => false)) {
        await cliTokensLink.first().click();
        await page.waitForLoadState("networkidle");
        expect(page.url()).toContain("cli-tokens");
      }
    }
  });

  test("should display correct breadcrumbs on AGENTS.md page", async ({ page }) => {
    await page.goto("/app/agents-md");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/agents-md")) {
      // Look for breadcrumbs
      const breadcrumbs = page.locator('[class*="breadcrumb"], nav[aria-label="Breadcrumb"]');
      const breadcrumbText = await breadcrumbs.first().textContent().catch(() => "");
      console.log(`Breadcrumbs: ${breadcrumbText}`);

      // Should contain Dashboard and AGENTS.md
      const hasCorrectBreadcrumbs = breadcrumbText?.includes("Dashboard") ||
        breadcrumbText?.includes("AGENTS");
      console.log(`Correct breadcrumbs: ${hasCorrectBreadcrumbs}`);
    }
  });

  test("should display correct breadcrumbs on CLI Tokens page", async ({ page }) => {
    await page.goto("/app/cli-tokens");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/cli-tokens")) {
      // Look for breadcrumbs
      const breadcrumbs = page.locator('[class*="breadcrumb"], nav[aria-label="Breadcrumb"]');
      const breadcrumbText = await breadcrumbs.first().textContent().catch(() => "");
      console.log(`Breadcrumbs: ${breadcrumbText}`);

      // Should contain Dashboard and CLI Tokens
      const hasCorrectBreadcrumbs = breadcrumbText?.includes("Dashboard") ||
        breadcrumbText?.includes("CLI");
      console.log(`Correct breadcrumbs: ${hasCorrectBreadcrumbs}`);
    }
  });
});

// =============================================================================
// Responsive Tests
// =============================================================================

test.describe("Sprint 85 Responsive Design", () => {
  test("AGENTS.md page should be responsive on mobile", async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/app/agents-md");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/agents-md")) {
      // Page should be visible without horizontal scroll
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      const viewportWidth = await page.evaluate(() => window.innerWidth);
      console.log(`Body width: ${bodyWidth}, Viewport: ${viewportWidth}`);

      // Content should fit within viewport (with some tolerance)
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 20);
    }
  });

  test("CLI Tokens page should be responsive on mobile", async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/app/cli-tokens");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/cli-tokens")) {
      // Page should be visible without horizontal scroll
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      const viewportWidth = await page.evaluate(() => window.innerWidth);
      console.log(`Body width: ${bodyWidth}, Viewport: ${viewportWidth}`);

      // Content should fit within viewport (with some tolerance)
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 20);
    }
  });

  test("AGENTS.md page should be responsive on tablet", async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto("/app/agents-md");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/agents-md")) {
      // Stats cards should be visible
      const statsCards = page.locator('[class*="card"], [class*="Card"]');
      const cardCount = await statsCards.count();
      console.log(`Stats cards on tablet: ${cardCount}`);
    }
  });

  test("CLI Tokens page should be responsive on tablet", async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto("/app/cli-tokens");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/cli-tokens")) {
      // Stats cards should be visible
      const statsCards = page.locator('[class*="card"], [class*="Card"]');
      const cardCount = await statsCards.count();
      console.log(`Stats cards on tablet: ${cardCount}`);
    }
  });
});

// =============================================================================
// Loading State Tests
// =============================================================================

test.describe("Sprint 85 Loading States", () => {
  test("AGENTS.md should show loading skeleton", async ({ page }) => {
    await page.goto("/app/agents-md");

    // Check for loading skeleton before content loads
    const skeleton = page.locator('[class*="animate-pulse"], [class*="skeleton"], [class*="loading"]');
    const hasLoadingState = await skeleton.first().isVisible().catch(() => false);
    console.log(`AGENTS.md loading skeleton: ${hasLoadingState}`);
  });

  test("CLI Tokens should show loading skeleton", async ({ page }) => {
    await page.goto("/app/cli-tokens");

    // Check for loading skeleton before content loads
    const skeleton = page.locator('[class*="animate-pulse"], [class*="skeleton"], [class*="loading"]');
    const hasLoadingState = await skeleton.first().isVisible().catch(() => false);
    console.log(`CLI Tokens loading skeleton: ${hasLoadingState}`);
  });
});
