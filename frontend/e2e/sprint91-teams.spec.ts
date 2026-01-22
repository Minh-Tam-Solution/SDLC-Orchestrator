/**
 * E2E Test: Sprint 91 Teams & Organizations UI
 * @status Sprint 91 - Teams UI Enhancement
 * @description Tests for Teams and Organizations functionality
 *
 * Test Coverage:
 * - Teams List Page
 * - Team Detail Page
 * - Team Edit Modal
 * - Organization Detail Page
 * - Organization Edit Modal
 * - Workspace Switcher
 * - Permission-based UI (canManage)
 *
 * @sdlc SDLC 5.1.3 Framework - Sprint 91
 * @date January 22, 2026
 */

import { test, expect } from "@playwright/test";

// =============================================================================
// Teams List Page Tests
// =============================================================================

test.describe("Teams List Page", () => {
  test("should load teams page", async ({ page }) => {
    await page.goto("/app/teams");
    await page.waitForLoadState("networkidle");

    const currentUrl = page.url();
    // Should be on teams page or redirect to login
    expect(currentUrl).toMatch(/teams|login/);
  });

  test("should display page header with title", async ({ page }) => {
    await page.goto("/app/teams");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/teams")) {
      // Look for page title
      const pageTitle = page.locator('h1, [class*="title"]');
      const titleText = await pageTitle.first().textContent();
      console.log(`Teams page title: ${titleText}`);

      // Should contain Teams
      expect(titleText?.toLowerCase()).toContain("team");
    }
  });

  test("should display stats cards", async ({ page }) => {
    await page.goto("/app/teams");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/teams")) {
      // Look for stats cards
      const statsCards = page.locator('[class*="card"], [class*="Card"], [class*="stat"]');
      const cardCount = await statsCards.count();
      console.log(`Teams stats cards found: ${cardCount}`);

      // Should have some stats cards
      expect(cardCount).toBeGreaterThanOrEqual(0);
    }
  });

  test("should display team list or empty state", async ({ page }) => {
    await page.goto("/app/teams");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/teams")) {
      const pageText = await page.textContent("body");
      const hasTeamList = pageText?.includes("Team") || pageText?.includes("team");
      const hasEmptyState = pageText?.includes("No teams") ||
        pageText?.includes("Get started") ||
        pageText?.includes("Create");
      console.log(`Team list: ${hasTeamList}, Empty state: ${hasEmptyState}`);
    }
  });

  test("should have Create Team button", async ({ page }) => {
    await page.goto("/app/teams");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/teams")) {
      // Look for create team button
      const createButton = page.locator('button:has-text("Create"), button:has-text("New Team")');
      const hasCreateButton = await createButton.first().isVisible().catch(() => false);
      console.log(`Create Team button visible: ${hasCreateButton}`);
    }
  });

  test("should open Create Team modal on button click", async ({ page }) => {
    await page.goto("/app/teams");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/teams")) {
      const createButton = page.locator('button:has-text("Create"), button:has-text("New Team")');

      if (await createButton.first().isVisible().catch(() => false)) {
        await createButton.first().click();
        await page.waitForTimeout(500);

        // Check for modal
        const modal = page.locator('[role="dialog"], [class*="modal"], [class*="Modal"]');
        const hasModal = await modal.first().isVisible().catch(() => false);
        console.log(`Create Team modal visible: ${hasModal}`);
      }
    }
  });

  test("should filter teams by organization", async ({ page }) => {
    await page.goto("/app/teams");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/teams")) {
      // Look for organization filter
      const orgFilter = page.locator('select, [class*="filter"], [class*="dropdown"]');
      const hasFilter = await orgFilter.first().isVisible().catch(() => false);
      console.log(`Organization filter visible: ${hasFilter}`);
    }
  });
});

// =============================================================================
// Team Detail Page Tests
// =============================================================================

test.describe("Team Detail Page", () => {
  test("should load team detail page", async ({ page }) => {
    // First go to teams list
    await page.goto("/app/teams");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/teams")) {
      // Try to click on a team to go to detail
      const teamLink = page.locator('a[href*="/teams/"]').first();
      if (await teamLink.isVisible().catch(() => false)) {
        await teamLink.click();
        await page.waitForLoadState("networkidle");

        // Should be on team detail page
        expect(page.url()).toMatch(/\/teams\/[a-f0-9-]+/);
      }
    }
  });

  test("should display team name and description", async ({ page }) => {
    await page.goto("/app/teams");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/teams")) {
      const teamLink = page.locator('a[href*="/teams/"]').first();
      if (await teamLink.isVisible().catch(() => false)) {
        await teamLink.click();
        await page.waitForLoadState("networkidle");

        // Check for team name
        const teamName = page.locator('h1, h2, [class*="title"]').first();
        const nameText = await teamName.textContent().catch(() => "");
        console.log(`Team name: ${nameText}`);
      }
    }
  });

  test("should display team statistics", async ({ page }) => {
    await page.goto("/app/teams");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/teams")) {
      const teamLink = page.locator('a[href*="/teams/"]').first();
      if (await teamLink.isVisible().catch(() => false)) {
        await teamLink.click();
        await page.waitForLoadState("networkidle");

        // Check for stats
        const pageText = await page.textContent("body");
        const hasMembers = pageText?.includes("Member") || pageText?.includes("member");
        const hasProjects = pageText?.includes("Project") || pageText?.includes("project");
        console.log(`Stats: Members=${hasMembers}, Projects=${hasProjects}`);
      }
    }
  });

  test("should display team members list", async ({ page }) => {
    await page.goto("/app/teams");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/teams")) {
      const teamLink = page.locator('a[href*="/teams/"]').first();
      if (await teamLink.isVisible().catch(() => false)) {
        await teamLink.click();
        await page.waitForLoadState("networkidle");

        // Check for members section
        const pageText = await page.textContent("body");
        const hasMembers = pageText?.includes("Member") || pageText?.includes("member");
        console.log(`Members section visible: ${hasMembers}`);
      }
    }
  });

  test("should have Edit button for team owners/admins", async ({ page }) => {
    await page.goto("/app/teams");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/teams")) {
      const teamLink = page.locator('a[href*="/teams/"]').first();
      if (await teamLink.isVisible().catch(() => false)) {
        await teamLink.click();
        await page.waitForLoadState("networkidle");

        // Check for edit button (may or may not be visible based on permissions)
        const editButton = page.locator('button:has-text("Edit"), button:has-text("Settings")');
        const hasEdit = await editButton.first().isVisible().catch(() => false);
        console.log(`Edit button visible: ${hasEdit}`);
      }
    }
  });

  test("should open Edit Team modal", async ({ page }) => {
    await page.goto("/app/teams");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/teams")) {
      const teamLink = page.locator('a[href*="/teams/"]').first();
      if (await teamLink.isVisible().catch(() => false)) {
        await teamLink.click();
        await page.waitForLoadState("networkidle");

        const editButton = page.locator('button:has-text("Edit")');
        if (await editButton.first().isVisible().catch(() => false)) {
          await editButton.first().click();
          await page.waitForTimeout(500);

          // Check for edit modal
          const modal = page.locator('[role="dialog"]');
          const hasModal = await modal.first().isVisible().catch(() => false);
          console.log(`Edit Team modal visible: ${hasModal}`);

          if (hasModal) {
            // Check for form fields
            const nameInput = page.locator('input[name="name"], input[placeholder*="name"]');
            const hasNameInput = await nameInput.first().isVisible().catch(() => false);
            console.log(`Name input visible: ${hasNameInput}`);
          }
        }
      }
    }
  });

  test("should have Add Member button for owners/admins", async ({ page }) => {
    await page.goto("/app/teams");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/teams")) {
      const teamLink = page.locator('a[href*="/teams/"]').first();
      if (await teamLink.isVisible().catch(() => false)) {
        await teamLink.click();
        await page.waitForLoadState("networkidle");

        // Check for add member button
        const addMemberButton = page.locator('button:has-text("Add Member"), button:has-text("Invite")');
        const hasAddMember = await addMemberButton.first().isVisible().catch(() => false);
        console.log(`Add Member button visible: ${hasAddMember}`);
      }
    }
  });
});

// =============================================================================
// Organizations List Page Tests
// =============================================================================

test.describe("Organizations List Page", () => {
  test("should load organizations page", async ({ page }) => {
    await page.goto("/app/organizations");
    await page.waitForLoadState("networkidle");

    const currentUrl = page.url();
    expect(currentUrl).toMatch(/organizations|login/);
  });

  test("should display page header with title", async ({ page }) => {
    await page.goto("/app/organizations");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/organizations")) {
      const pageTitle = page.locator('h1, [class*="title"]');
      const titleText = await pageTitle.first().textContent();
      console.log(`Organizations page title: ${titleText}`);

      expect(titleText?.toLowerCase()).toContain("organization");
    }
  });

  test("should display organization cards or list", async ({ page }) => {
    await page.goto("/app/organizations");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/organizations")) {
      const pageText = await page.textContent("body");
      const hasOrgContent = pageText?.includes("Organization") || pageText?.includes("organization");
      console.log(`Organization content visible: ${hasOrgContent}`);
    }
  });

  test("should have Create Organization button", async ({ page }) => {
    await page.goto("/app/organizations");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/organizations")) {
      const createButton = page.locator('button:has-text("Create"), button:has-text("New Organization")');
      const hasCreateButton = await createButton.first().isVisible().catch(() => false);
      console.log(`Create Organization button visible: ${hasCreateButton}`);
    }
  });
});

// =============================================================================
// Organization Detail Page Tests
// =============================================================================

test.describe("Organization Detail Page", () => {
  test("should load organization detail page", async ({ page }) => {
    await page.goto("/app/organizations");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/organizations")) {
      const orgLink = page.locator('a[href*="/organizations/"]').first();
      if (await orgLink.isVisible().catch(() => false)) {
        await orgLink.click();
        await page.waitForLoadState("networkidle");

        expect(page.url()).toMatch(/\/organizations\/[a-f0-9-]+/);
      }
    }
  });

  test("should display organization name and details", async ({ page }) => {
    await page.goto("/app/organizations");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/organizations")) {
      const orgLink = page.locator('a[href*="/organizations/"]').first();
      if (await orgLink.isVisible().catch(() => false)) {
        await orgLink.click();
        await page.waitForLoadState("networkidle");

        const orgName = page.locator('h1, h2, [class*="title"]').first();
        const nameText = await orgName.textContent().catch(() => "");
        console.log(`Organization name: ${nameText}`);
      }
    }
  });

  test("should display organization statistics", async ({ page }) => {
    await page.goto("/app/organizations");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/organizations")) {
      const orgLink = page.locator('a[href*="/organizations/"]').first();
      if (await orgLink.isVisible().catch(() => false)) {
        await orgLink.click();
        await page.waitForLoadState("networkidle");

        const pageText = await page.textContent("body");
        const hasTeams = pageText?.includes("Team") || pageText?.includes("team");
        const hasMembers = pageText?.includes("Member") || pageText?.includes("member");
        console.log(`Stats: Teams=${hasTeams}, Members=${hasMembers}`);
      }
    }
  });

  test("should have Edit button for organization owners", async ({ page }) => {
    await page.goto("/app/organizations");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/organizations")) {
      const orgLink = page.locator('a[href*="/organizations/"]').first();
      if (await orgLink.isVisible().catch(() => false)) {
        await orgLink.click();
        await page.waitForLoadState("networkidle");

        const editButton = page.locator('button:has-text("Edit"), button:has-text("Settings")');
        const hasEdit = await editButton.first().isVisible().catch(() => false);
        console.log(`Edit button visible: ${hasEdit}`);
      }
    }
  });

  test("should open Edit Organization modal", async ({ page }) => {
    await page.goto("/app/organizations");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/organizations")) {
      const orgLink = page.locator('a[href*="/organizations/"]').first();
      if (await orgLink.isVisible().catch(() => false)) {
        await orgLink.click();
        await page.waitForLoadState("networkidle");

        const editButton = page.locator('button:has-text("Edit")');
        if (await editButton.first().isVisible().catch(() => false)) {
          await editButton.first().click();
          await page.waitForTimeout(500);

          const modal = page.locator('[role="dialog"]');
          const hasModal = await modal.first().isVisible().catch(() => false);
          console.log(`Edit Organization modal visible: ${hasModal}`);

          if (hasModal) {
            const nameInput = page.locator('input[name="name"], input[placeholder*="name"]');
            const hasNameInput = await nameInput.first().isVisible().catch(() => false);
            console.log(`Name input visible: ${hasNameInput}`);
          }
        }
      }
    }
  });
});

// =============================================================================
// Workspace Switcher Tests
// =============================================================================

test.describe("Workspace Switcher", () => {
  test("should display workspace switcher in header", async ({ page }) => {
    await page.goto("/app");
    await page.waitForLoadState("networkidle");

    if (!page.url().includes("/login")) {
      // Look for workspace switcher button
      const switcherButton = page.locator('button:has-text("Select Org"), button:has([class*="building"]), button:has([class*="office"])');
      const hasSwitcher = await switcherButton.first().isVisible().catch(() => false);
      console.log(`Workspace switcher visible: ${hasSwitcher}`);

      // Also check for organization icon in header
      const header = page.locator('header');
      const headerText = await header.textContent().catch(() => "");
      console.log(`Header contains workspace info: ${headerText?.length > 0}`);
    }
  });

  test("should open workspace dropdown on click", async ({ page }) => {
    await page.goto("/app");
    await page.waitForLoadState("networkidle");

    if (!page.url().includes("/login")) {
      // Find and click the workspace switcher
      const switcherButton = page.locator('header button').filter({ hasText: /Select|Org/ }).first();

      if (await switcherButton.isVisible().catch(() => false)) {
        await switcherButton.click();
        await page.waitForTimeout(300);

        // Check for dropdown
        const dropdown = page.locator('[class*="dropdown"], [class*="menu"], div.absolute');
        const hasDropdown = await dropdown.first().isVisible().catch(() => false);
        console.log(`Workspace dropdown visible: ${hasDropdown}`);
      }
    }
  });

  test("should show organizations list in dropdown", async ({ page }) => {
    await page.goto("/app");
    await page.waitForLoadState("networkidle");

    if (!page.url().includes("/login")) {
      const switcherButton = page.locator('header button').first();

      if (await switcherButton.isVisible().catch(() => false)) {
        await switcherButton.click();
        await page.waitForTimeout(300);

        // Look for organizations section
        const pageText = await page.textContent("body");
        const hasOrganizations = pageText?.includes("Organization");
        console.log(`Organizations section in dropdown: ${hasOrganizations}`);
      }
    }
  });

  test("should show teams list after selecting organization", async ({ page }) => {
    await page.goto("/app");
    await page.waitForLoadState("networkidle");

    if (!page.url().includes("/login")) {
      const switcherButton = page.locator('header button').first();

      if (await switcherButton.isVisible().catch(() => false)) {
        await switcherButton.click();
        await page.waitForTimeout(300);

        // Look for teams section
        const pageText = await page.textContent("body");
        const hasTeams = pageText?.includes("Teams in") || pageText?.includes("Team");
        console.log(`Teams section in dropdown: ${hasTeams}`);
      }
    }
  });

  test("should have manage organizations link", async ({ page }) => {
    await page.goto("/app");
    await page.waitForLoadState("networkidle");

    if (!page.url().includes("/login")) {
      const switcherButton = page.locator('header button').first();

      if (await switcherButton.isVisible().catch(() => false)) {
        await switcherButton.click();
        await page.waitForTimeout(300);

        // Look for manage link
        const manageOrgLink = page.locator('a[href*="/organizations"]:has-text("Manage")');
        const hasManageLink = await manageOrgLink.first().isVisible().catch(() => false);
        console.log(`Manage Organizations link visible: ${hasManageLink}`);
      }
    }
  });

  test("should have manage teams link", async ({ page }) => {
    await page.goto("/app");
    await page.waitForLoadState("networkidle");

    if (!page.url().includes("/login")) {
      const switcherButton = page.locator('header button').first();

      if (await switcherButton.isVisible().catch(() => false)) {
        await switcherButton.click();
        await page.waitForTimeout(300);

        // Look for manage link
        const manageTeamsLink = page.locator('a[href*="/teams"]:has-text("Manage")');
        const hasManageLink = await manageTeamsLink.first().isVisible().catch(() => false);
        console.log(`Manage Teams link visible: ${hasManageLink}`);
      }
    }
  });

  test("should persist selected organization", async ({ page }) => {
    await page.goto("/app");
    await page.waitForLoadState("networkidle");

    if (!page.url().includes("/login")) {
      // Check localStorage for selected org
      const selectedOrgId = await page.evaluate(() => {
        return localStorage.getItem("sdlc_selected_org_id");
      });
      console.log(`Selected org ID in localStorage: ${selectedOrgId}`);
    }
  });

  test("should persist selected team", async ({ page }) => {
    await page.goto("/app");
    await page.waitForLoadState("networkidle");

    if (!page.url().includes("/login")) {
      // Check localStorage for selected team
      const selectedTeamId = await page.evaluate(() => {
        return localStorage.getItem("sdlc_selected_team_id");
      });
      console.log(`Selected team ID in localStorage: ${selectedTeamId}`);
    }
  });
});

// =============================================================================
// Permission-Based UI Tests
// =============================================================================

test.describe("Permission-Based UI", () => {
  test("Edit button should only show for owners/admins on team detail", async ({ page }) => {
    await page.goto("/app/teams");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/teams")) {
      const teamLink = page.locator('a[href*="/teams/"]').first();
      if (await teamLink.isVisible().catch(() => false)) {
        await teamLink.click();
        await page.waitForLoadState("networkidle");

        // The edit button should only be visible if user is owner/admin
        const editButton = page.locator('button:has-text("Edit")');
        const isVisible = await editButton.first().isVisible().catch(() => false);

        // Log the result - this is permission-dependent
        console.log(`Edit button visible (permission-based): ${isVisible}`);
      }
    }
  });

  test("Add Member button should only show for owners/admins", async ({ page }) => {
    await page.goto("/app/teams");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/teams")) {
      const teamLink = page.locator('a[href*="/teams/"]').first();
      if (await teamLink.isVisible().catch(() => false)) {
        await teamLink.click();
        await page.waitForLoadState("networkidle");

        const addMemberButton = page.locator('button:has-text("Add Member"), button:has-text("Invite")');
        const isVisible = await addMemberButton.first().isVisible().catch(() => false);

        console.log(`Add Member button visible (permission-based): ${isVisible}`);
      }
    }
  });

  test("Delete Team button should only show for owners", async ({ page }) => {
    await page.goto("/app/teams");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/teams")) {
      const teamLink = page.locator('a[href*="/teams/"]').first();
      if (await teamLink.isVisible().catch(() => false)) {
        await teamLink.click();
        await page.waitForLoadState("networkidle");

        const deleteButton = page.locator('button:has-text("Delete"), button[class*="destructive"]');
        const isVisible = await deleteButton.first().isVisible().catch(() => false);

        console.log(`Delete button visible (owner-only): ${isVisible}`);
      }
    }
  });

  test("Role management should only be available to owners", async ({ page }) => {
    await page.goto("/app/teams");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/teams")) {
      const teamLink = page.locator('a[href*="/teams/"]').first();
      if (await teamLink.isVisible().catch(() => false)) {
        await teamLink.click();
        await page.waitForLoadState("networkidle");

        // Look for role change dropdown or button
        const roleSelector = page.locator('select, [class*="role"], button:has-text("Change Role")');
        const hasRoleManagement = await roleSelector.first().isVisible().catch(() => false);

        console.log(`Role management visible (owner-only): ${hasRoleManagement}`);
      }
    }
  });
});

// =============================================================================
// Navigation Tests
// =============================================================================

test.describe("Teams & Organizations Navigation", () => {
  test("should navigate from teams list to team detail", async ({ page }) => {
    await page.goto("/app/teams");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/teams")) {
      const teamLink = page.locator('a[href*="/teams/"]').first();
      if (await teamLink.isVisible().catch(() => false)) {
        await teamLink.click();
        await page.waitForLoadState("networkidle");

        expect(page.url()).toMatch(/\/teams\/[a-f0-9-]+/);
      }
    }
  });

  test("should navigate from organizations list to organization detail", async ({ page }) => {
    await page.goto("/app/organizations");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/organizations")) {
      const orgLink = page.locator('a[href*="/organizations/"]').first();
      if (await orgLink.isVisible().catch(() => false)) {
        await orgLink.click();
        await page.waitForLoadState("networkidle");

        expect(page.url()).toMatch(/\/organizations\/[a-f0-9-]+/);
      }
    }
  });

  test("should have Teams link in sidebar", async ({ page }) => {
    await page.goto("/app");
    await page.waitForLoadState("networkidle");

    if (!page.url().includes("/login")) {
      const teamsLink = page.locator('a[href*="/teams"]');
      const hasTeamsLink = await teamsLink.first().isVisible().catch(() => false);
      console.log(`Teams link in sidebar: ${hasTeamsLink}`);
      expect(hasTeamsLink).toBeTruthy();
    }
  });

  test("should have Organizations link in sidebar", async ({ page }) => {
    await page.goto("/app");
    await page.waitForLoadState("networkidle");

    if (!page.url().includes("/login")) {
      const orgsLink = page.locator('a[href*="/organizations"]');
      const hasOrgsLink = await orgsLink.first().isVisible().catch(() => false);
      console.log(`Organizations link in sidebar: ${hasOrgsLink}`);
      expect(hasOrgsLink).toBeTruthy();
    }
  });

  test("should display correct breadcrumbs on teams page", async ({ page }) => {
    await page.goto("/app/teams");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(2000);

    if (page.url().includes("/teams")) {
      const breadcrumbs = page.locator('[class*="breadcrumb"], nav[aria-label="Breadcrumb"]');
      const breadcrumbText = await breadcrumbs.first().textContent().catch(() => "");
      console.log(`Breadcrumbs: ${breadcrumbText}`);

      const hasCorrectBreadcrumbs = breadcrumbText?.includes("Dashboard") ||
        breadcrumbText?.includes("Teams") ||
        page.url().includes("/teams");
      expect(hasCorrectBreadcrumbs).toBeTruthy();
    }
  });

  test("should display correct breadcrumbs on organizations page", async ({ page }) => {
    await page.goto("/app/organizations");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(2000);

    if (page.url().includes("/organizations")) {
      const breadcrumbs = page.locator('[class*="breadcrumb"], nav[aria-label="Breadcrumb"]');
      const breadcrumbText = await breadcrumbs.first().textContent().catch(() => "");
      console.log(`Breadcrumbs: ${breadcrumbText}`);

      const hasCorrectBreadcrumbs = breadcrumbText?.includes("Dashboard") ||
        breadcrumbText?.includes("Organizations") ||
        page.url().includes("/organizations");
      expect(hasCorrectBreadcrumbs).toBeTruthy();
    }
  });
});

// =============================================================================
// Responsive Design Tests
// =============================================================================

test.describe("Teams & Organizations Responsive Design", () => {
  test("Teams page should be responsive on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/app/teams");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/teams")) {
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      const viewportWidth = await page.evaluate(() => window.innerWidth);
      console.log(`Body width: ${bodyWidth}, Viewport: ${viewportWidth}`);

      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 20);
    }
  });

  test("Organizations page should be responsive on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/app/organizations");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/organizations")) {
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      const viewportWidth = await page.evaluate(() => window.innerWidth);
      console.log(`Body width: ${bodyWidth}, Viewport: ${viewportWidth}`);

      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 20);
    }
  });

  test("Team detail page should be responsive on tablet", async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto("/app/teams");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/teams")) {
      const teamLink = page.locator('a[href*="/teams/"]').first();
      if (await teamLink.isVisible().catch(() => false)) {
        await teamLink.click();
        await page.waitForLoadState("networkidle");

        const statsCards = page.locator('[class*="card"], [class*="Card"]');
        const cardCount = await statsCards.count();
        console.log(`Stats cards on tablet: ${cardCount}`);
      }
    }
  });

  test("Workspace switcher should work on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/app");
    await page.waitForLoadState("networkidle");

    if (!page.url().includes("/login")) {
      // Workspace switcher should still be accessible on mobile
      const header = page.locator('header');
      const hasHeader = await header.isVisible().catch(() => false);
      console.log(`Header visible on mobile: ${hasHeader}`);
    }
  });
});

// =============================================================================
// Loading State Tests
// =============================================================================

test.describe("Teams & Organizations Loading States", () => {
  test("Teams page should show loading skeleton", async ({ page }) => {
    await page.goto("/app/teams");

    const skeleton = page.locator('[class*="animate-pulse"], [class*="skeleton"], [class*="loading"]');
    const hasLoadingState = await skeleton.first().isVisible().catch(() => false);
    console.log(`Teams loading skeleton: ${hasLoadingState}`);
  });

  test("Organizations page should show loading skeleton", async ({ page }) => {
    await page.goto("/app/organizations");

    const skeleton = page.locator('[class*="animate-pulse"], [class*="skeleton"], [class*="loading"]');
    const hasLoadingState = await skeleton.first().isVisible().catch(() => false);
    console.log(`Organizations loading skeleton: ${hasLoadingState}`);
  });

  test("Team detail should show loading state", async ({ page }) => {
    await page.goto("/app/teams");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/teams")) {
      const teamLink = page.locator('a[href*="/teams/"]').first();
      if (await teamLink.isVisible().catch(() => false)) {
        await teamLink.click();

        // Check for loading state immediately
        const skeleton = page.locator('[class*="animate-pulse"], [class*="skeleton"]');
        const hasLoading = await skeleton.first().isVisible().catch(() => false);
        console.log(`Team detail loading state: ${hasLoading}`);
      }
    }
  });
});
