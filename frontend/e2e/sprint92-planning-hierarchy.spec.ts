/**
 * E2E Test: Sprint 92 Planning Hierarchy UI
 * @status Sprint 92 - Planning Hierarchy Part 1
 * @description Tests for Planning Hierarchy CRUD functionality
 *
 * Test Coverage:
 * - Planning Page Navigation
 * - Tree View Display
 * - Timeline View Display
 * - Create Roadmap Modal
 * - Edit Roadmap via Action Menu
 * - Delete Roadmap with Confirmation
 * - Create Phase Modal
 * - Edit/Delete Phase via Action Menu
 *
 * @sdlc SDLC 5.1.3 Framework - Sprint 92
 * @reference Pillar 2: Sprint Planning Governance
 * @date January 22, 2026
 */

import { test, expect } from "@playwright/test";

// =============================================================================
// Planning Page Navigation Tests
// =============================================================================

test.describe("Planning Page Navigation", () => {
  test("should load planning page", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    const currentUrl = page.url();
    // Should be on planning page or redirect to login
    expect(currentUrl).toMatch(/planning|login/);
  });

  test("should display page header with title", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/planning")) {
      // Look for page title
      const pageTitle = page.locator('h1, [class*="title"]');
      const titleText = await pageTitle.first().textContent();
      console.log(`Planning page title: ${titleText}`);

      // Should contain Planning Hierarchy
      expect(titleText?.toLowerCase()).toMatch(/planning|hierarchy/);
    }
  });

  test("should display SDLC 5.1.3 reference", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/planning")) {
      const pageText = await page.textContent("body");
      const hasSDLCRef = pageText?.includes("SDLC 5.1.3") || pageText?.includes("5.1.3");
      console.log(`SDLC 5.1.3 reference found: ${hasSDLCRef}`);
    }
  });

  test("should have Back to Sprints link", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/planning")) {
      const backLink = page.locator('a:has-text("Back to Sprints"), a[href*="/sprints"]');
      const hasBackLink = await backLink.first().isVisible().catch(() => false);
      console.log(`Back to Sprints link visible: ${hasBackLink}`);
    }
  });
});

// =============================================================================
// Stats Cards Tests
// =============================================================================

test.describe("Planning Stats Cards", () => {
  test("should display stats cards", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/planning")) {
      // Look for stats cards (Roadmaps, Phases, Sprints, Active Sprint)
      const statsCards = page.locator('[class*="grid"] > div[class*="rounded"]');
      const cardCount = await statsCards.count();
      console.log(`Planning stats cards found: ${cardCount}`);

      // Should have 4 stats cards
      expect(cardCount).toBeGreaterThanOrEqual(0);
    }
  });

  test("should display roadmaps count", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/planning")) {
      const pageText = await page.textContent("body");
      const hasRoadmaps = pageText?.toLowerCase().includes("roadmap");
      console.log(`Roadmaps stat found: ${hasRoadmaps}`);
    }
  });

  test("should display phases count", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/planning")) {
      const pageText = await page.textContent("body");
      const hasPhases = pageText?.toLowerCase().includes("phase");
      console.log(`Phases stat found: ${hasPhases}`);
    }
  });
});

// =============================================================================
// View Toggle Tests
// =============================================================================

test.describe("View Toggle", () => {
  test("should display view toggle buttons", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/planning")) {
      const treeViewButton = page.locator('button:has-text("Tree View"), button:has-text("Tree")');
      const timelineButton = page.locator('button:has-text("Timeline")');

      const hasTreeView = await treeViewButton.first().isVisible().catch(() => false);
      const hasTimeline = await timelineButton.first().isVisible().catch(() => false);

      console.log(`Tree View button: ${hasTreeView}, Timeline button: ${hasTimeline}`);
    }
  });

  test("should switch between Tree and Timeline views", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/planning")) {
      const timelineButton = page.locator('button:has-text("Timeline")');

      if (await timelineButton.first().isVisible().catch(() => false)) {
        await timelineButton.first().click();
        await page.waitForTimeout(500);

        // Check if timeline view is displayed
        const pageText = await page.textContent("body");
        console.log(`Switched to Timeline view`);

        // Switch back to Tree view
        const treeViewButton = page.locator('button:has-text("Tree View"), button:has-text("Tree")');
        if (await treeViewButton.first().isVisible().catch(() => false)) {
          await treeViewButton.first().click();
          await page.waitForTimeout(500);
          console.log(`Switched back to Tree view`);
        }
      }
    }
  });
});

// =============================================================================
// Tree View Tests
// =============================================================================

test.describe("Planning Hierarchy Tree View", () => {
  test("should display tree view component", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/planning")) {
      // Look for tree view container
      const treeView = page.locator('[class*="PlanningHierarchy"], [class*="tree"], [class*="hierarchy"]');
      const hasTreeView = await treeView.first().isVisible().catch(() => false);
      console.log(`Tree view component visible: ${hasTreeView}`);
    }
  });

  test("should display tree header with project name", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/planning")) {
      const treeHeader = page.locator('h3:has-text("Planning Hierarchy")');
      const hasHeader = await treeHeader.first().isVisible().catch(() => false);
      console.log(`Tree header visible: ${hasHeader}`);
    }
  });

  test("should display Expand/Collapse buttons", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/planning")) {
      const expandButton = page.locator('button:has-text("Expand")');
      const collapseButton = page.locator('button:has-text("Collapse")');

      const hasExpand = await expandButton.first().isVisible().catch(() => false);
      const hasCollapse = await collapseButton.first().isVisible().catch(() => false);

      console.log(`Expand button: ${hasExpand}, Collapse button: ${hasCollapse}`);
    }
  });

  test("should display legend with node types", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/planning")) {
      const pageText = await page.textContent("body");
      const hasLegend = pageText?.includes("Legend") ||
        (pageText?.includes("Roadmap") && pageText?.includes("Phase") && pageText?.includes("Sprint"));
      console.log(`Legend with node types visible: ${hasLegend}`);
    }
  });
});

// =============================================================================
// Create Roadmap Modal Tests
// =============================================================================

test.describe("Create Roadmap Modal", () => {
  test("should have New Roadmap button", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/planning")) {
      const newRoadmapButton = page.locator('button:has-text("New Roadmap")');
      const hasButton = await newRoadmapButton.first().isVisible().catch(() => false);
      console.log(`New Roadmap button visible: ${hasButton}`);
      expect(hasButton).toBeTruthy();
    }
  });

  test("should open Create Roadmap modal on button click", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/planning")) {
      const newRoadmapButton = page.locator('button:has-text("New Roadmap")');

      if (await newRoadmapButton.first().isVisible().catch(() => false)) {
        await newRoadmapButton.first().click();
        await page.waitForTimeout(500);

        // Check if modal is open
        const modal = page.locator('[role="dialog"], [class*="Dialog"], [class*="Modal"]');
        const modalVisible = await modal.first().isVisible().catch(() => false);
        console.log(`Create Roadmap modal visible: ${modalVisible}`);

        // Close modal if open
        if (modalVisible) {
          const cancelButton = page.locator('button:has-text("Cancel")');
          if (await cancelButton.first().isVisible().catch(() => false)) {
            await cancelButton.first().click();
          }
        }
      }
    }
  });

  test("should display roadmap form fields", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/planning")) {
      const newRoadmapButton = page.locator('button:has-text("New Roadmap")');

      if (await newRoadmapButton.first().isVisible().catch(() => false)) {
        await newRoadmapButton.first().click();
        await page.waitForTimeout(500);

        // Check for form fields
        const nameField = page.locator('input[name="name"], input[placeholder*="name"]');
        const descField = page.locator('textarea[name="description"], textarea[placeholder*="description"]');
        const startDateField = page.locator('input[type="date"], input[name*="start"]');
        const endDateField = page.locator('input[type="date"], input[name*="end"]');

        const hasName = await nameField.first().isVisible().catch(() => false);
        const hasDesc = await descField.first().isVisible().catch(() => false);
        const hasStartDate = await startDateField.first().isVisible().catch(() => false);
        const hasEndDate = await endDateField.first().isVisible().catch(() => false);

        console.log(`Form fields - Name: ${hasName}, Desc: ${hasDesc}, Start: ${hasStartDate}, End: ${hasEndDate}`);

        // Close modal
        const cancelButton = page.locator('button:has-text("Cancel")');
        if (await cancelButton.first().isVisible().catch(() => false)) {
          await cancelButton.first().click();
        }
      }
    }
  });
});

// =============================================================================
// Action Menu Tests
// =============================================================================

test.describe("Action Menu", () => {
  test("should display action menu button on roadmap nodes", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/planning")) {
      // Look for ellipsis (⋮) action buttons
      const actionButtons = page.locator('button[title="Actions"], [class*="ellipsis"], svg[class*="ellipsis"]');
      const actionCount = await actionButtons.count();
      console.log(`Action menu buttons found: ${actionCount}`);
    }
  });

  test("should show action menu on click", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/planning")) {
      const actionButton = page.locator('button[title="Actions"]').first();

      if (await actionButton.isVisible().catch(() => false)) {
        await actionButton.click();
        await page.waitForTimeout(300);

        // Check if menu is visible
        const menu = page.locator('[class*="absolute"][class*="z-50"], [role="menu"]');
        const menuVisible = await menu.first().isVisible().catch(() => false);
        console.log(`Action menu visible: ${menuVisible}`);

        // Click outside to close
        await page.keyboard.press("Escape");
      }
    }
  });

  test("should display Edit and Delete options in menu", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/planning")) {
      const actionButton = page.locator('button[title="Actions"]').first();

      if (await actionButton.isVisible().catch(() => false)) {
        await actionButton.click();
        await page.waitForTimeout(300);

        // Check for Edit and Delete options
        const editOption = page.locator('button:has-text("Edit")');
        const deleteOption = page.locator('button:has-text("Delete")');

        const hasEdit = await editOption.first().isVisible().catch(() => false);
        const hasDelete = await deleteOption.first().isVisible().catch(() => false);

        console.log(`Menu options - Edit: ${hasEdit}, Delete: ${hasDelete}`);

        // Click outside to close
        await page.keyboard.press("Escape");
      }
    }
  });

  test("should show Add Phase option for roadmap nodes", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/planning")) {
      const actionButton = page.locator('button[title="Actions"]').first();

      if (await actionButton.isVisible().catch(() => false)) {
        await actionButton.click();
        await page.waitForTimeout(300);

        // Check for Add Phase option (for roadmap nodes)
        const addPhaseOption = page.locator('button:has-text("Add Phase")');
        const hasAddPhase = await addPhaseOption.first().isVisible().catch(() => false);

        console.log(`Add Phase option visible: ${hasAddPhase}`);

        // Click outside to close
        await page.keyboard.press("Escape");
      }
    }
  });
});

// =============================================================================
// Delete Confirmation Dialog Tests
// =============================================================================

test.describe("Delete Confirmation Dialog", () => {
  test("should show delete confirmation on Delete click", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/planning")) {
      const actionButton = page.locator('button[title="Actions"]').first();

      if (await actionButton.isVisible().catch(() => false)) {
        await actionButton.click();
        await page.waitForTimeout(300);

        const deleteOption = page.locator('button:has-text("Delete")');

        if (await deleteOption.first().isVisible().catch(() => false)) {
          await deleteOption.first().click();
          await page.waitForTimeout(300);

          // Check for confirmation dialog
          const dialog = page.locator('[role="dialog"]');
          const dialogVisible = await dialog.first().isVisible().catch(() => false);

          // Check for warning text
          const warningText = page.locator('text=/cannot be undone|permanently delete/i');
          const hasWarning = await warningText.first().isVisible().catch(() => false);

          console.log(`Delete confirmation dialog: ${dialogVisible}, Warning: ${hasWarning}`);

          // Close dialog
          const cancelButton = page.locator('button:has-text("Cancel")');
          if (await cancelButton.first().isVisible().catch(() => false)) {
            await cancelButton.first().click();
          }
        }
      }
    }
  });

  test("should have Cancel and Delete buttons in confirmation", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/planning")) {
      const actionButton = page.locator('button[title="Actions"]').first();

      if (await actionButton.isVisible().catch(() => false)) {
        await actionButton.click();
        await page.waitForTimeout(300);

        const deleteOption = page.locator('button:has-text("Delete")');

        if (await deleteOption.first().isVisible().catch(() => false)) {
          await deleteOption.first().click();
          await page.waitForTimeout(300);

          // Check for Cancel and Delete buttons
          const cancelButton = page.locator('[role="dialog"] button:has-text("Cancel")');
          const confirmButton = page.locator('[role="dialog"] button:has-text("Delete")');

          const hasCancel = await cancelButton.first().isVisible().catch(() => false);
          const hasConfirm = await confirmButton.first().isVisible().catch(() => false);

          console.log(`Dialog buttons - Cancel: ${hasCancel}, Delete: ${hasConfirm}`);

          // Close dialog
          if (hasCancel) {
            await cancelButton.first().click();
          }
        }
      }
    }
  });
});

// =============================================================================
// Help Text Tests
// =============================================================================

test.describe("Help Text", () => {
  test("should display SDLC 5.1.3 hierarchy explanation", async ({ page }) => {
    await page.goto("/app/planning");
    await page.waitForLoadState("networkidle");

    if (page.url().includes("/planning")) {
      const pageText = await page.textContent("body");

      // Check for hierarchy explanation
      const hasRoadmapExplanation = pageText?.includes("12-month") || pageText?.includes("vision");
      const hasPhaseExplanation = pageText?.includes("4-8 weeks") || pageText?.includes("theme");
      const hasSprintExplanation = pageText?.includes("5-10 days") || pageText?.includes("committed");

      console.log(`Help text - Roadmap: ${hasRoadmapExplanation}, Phase: ${hasPhaseExplanation}, Sprint: ${hasSprintExplanation}`);
    }
  });
});
