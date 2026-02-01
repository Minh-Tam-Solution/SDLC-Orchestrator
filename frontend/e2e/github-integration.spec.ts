import { test, expect } from "@playwright/test";

test.describe("GitHub Integration", () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto("/login");
    await page.fill('input[type="email"]', "user@example.com");
    await page.fill('input[type="password"]', "password123");
    await page.click('button[type="submit"]');
    await page.waitForURL("/app/teams");
  });

  test("should display GitHub settings page", async ({ page }) => {
    await page.goto("/settings/github");

    // Check page title
    await expect(page.locator("h1")).toContainText("GitHub Integration");

    // Check description
    await expect(
      page.locator("text=Manage your GitHub connection")
    ).toBeVisible();
  });

  test("should show connect button when not connected", async ({ page }) => {
    await page.goto("/settings/github");

    // Check for connect button
    await expect(page.locator('button:has-text("Connect GitHub")')).toBeVisible();

    // Check for not connected message
    await expect(page.locator("text=Not Connected")).toBeVisible();
  });

  test("should initiate GitHub OAuth flow", async ({ page }) => {
    await page.goto("/settings/github");

    // Click connect button
    await page.click('button:has-text("Connect GitHub")');

    // Should redirect to GitHub OAuth
    await page.waitForURL(/github\.com\/login\/oauth/);
  });

  test("should display connection status when connected", async ({ page }) => {
    // Mock: User already connected to GitHub
    await page.goto("/settings/github");

    // Should show connected badge
    await expect(page.locator("text=Connected")).toBeVisible();

    // Should show GitHub username
    await expect(page.locator("text=octocat")).toBeVisible();

    // Should show disconnect button
    await expect(
      page.locator('button:has-text("Connected as octocat")')
    ).toBeVisible();
  });

  test("should disconnect GitHub account", async ({ page }) => {
    await page.goto("/settings/github");

    // Click disconnect button
    await page.click('button:has-text("Connected as octocat")');

    // Confirm disconnection in alert dialog
    await expect(page.locator("text=Disconnect GitHub?")).toBeVisible();
    await page.click('button:has-text("Disconnect")');

    // Should show connect button again
    await expect(page.locator('button:has-text("Connect GitHub")')).toBeVisible();
  });

  test("should display repositories list when connected", async ({ page }) => {
    await page.goto("/settings/github");

    // Check for repositories section
    await expect(page.locator("text=Your Repositories")).toBeVisible();

    // Check for repository cards
    await expect(page.locator('[class*="repository"]').first()).toBeVisible();
  });

  test("should sync repositories", async ({ page }) => {
    await page.goto("/settings/github");

    // Click sync button
    await page.click('button:has-text("Sync")');

    // Should show syncing state
    await expect(page.locator("text=Syncing...")).toBeVisible();

    // Wait for sync to complete
    await expect(page.locator("text=Syncing...")).not.toBeVisible();

    // Repository list should be updated
    await expect(page.locator('[class*="repository"]').first()).toBeVisible();
  });

  test("should search repositories", async ({ page }) => {
    await page.goto("/settings/github");

    // Type in search input
    await page.fill('input[placeholder*="Search repositories"]', "test-repo");

    // Should filter repositories
    await expect(page.locator("text=test-repo")).toBeVisible();
    await expect(page.locator("text=other-repo")).not.toBeVisible();
  });

  test("should connect repository to project", async ({ page }) => {
    await page.goto("/settings/github");

    // Click connect button on a repository
    await page.click('.repository-card button:has-text("Connect")');

    // Confirm connection in dialog
    await expect(page.locator("text=Connect Repository?")).toBeVisible();
    await page.click('button:has-text("Connect Repository")');

    // Should show success message
    await expect(page.locator("text=Repository connected")).toBeVisible();
  });

  test("should display repository metadata", async ({ page }) => {
    await page.goto("/settings/github");

    // Check for repository name
    await expect(page.locator("text=owner/repository")).toBeVisible();

    // Check for language badge
    await expect(page.locator("text=TypeScript")).toBeVisible();

    // Check for stars count
    await expect(page.locator("text=★")).toBeVisible();

    // Check for forks count
    await expect(page.locator('[class*="fork"]')).toBeVisible();
  });

  test("should show private repository badge", async ({ page }) => {
    await page.goto("/settings/github");

    // Check for private badge
    await expect(page.locator("text=Private").first()).toBeVisible();
  });

  test("should display token expiry warning", async ({ page }) => {
    await page.goto("/settings/github");

    // Check for expiry warning
    await expect(page.locator("text=Token Expiry")).toBeVisible();
    await expect(
      page.locator("text=Your GitHub access token expires")
    ).toBeVisible();
  });

  test("should display granted permissions", async ({ page }) => {
    await page.goto("/settings/github");

    // Check for permissions list
    await expect(page.locator("text=Granted Permissions")).toBeVisible();
    await expect(page.locator("text=Read user profile")).toBeVisible();
    await expect(page.locator("text=Access repositories")).toBeVisible();
    await expect(page.locator("text=Create webhooks")).toBeVisible();
    await expect(page.locator("text=Read pull requests")).toBeVisible();
  });

  test("should handle empty repository list", async ({ page }) => {
    await page.goto("/settings/github");

    // Check for empty state message
    await expect(page.locator("text=No repositories available")).toBeVisible();
    await expect(
      page.locator("text=Sync your repositories or adjust your GitHub permissions")
    ).toBeVisible();
  });

  test("should display help section", async ({ page }) => {
    await page.goto("/settings/github");

    // Check for help section
    await expect(page.locator("text=How GitHub Integration Works")).toBeVisible();

    // Check for steps
    await expect(page.locator("text=Connect your GitHub account")).toBeVisible();
    await expect(page.locator("text=Select repositories")).toBeVisible();
    await expect(page.locator("text=Automatic synchronization")).toBeVisible();
    await expect(page.locator("text=Quality gate integration")).toBeVisible();
  });

  test("should display privacy notice", async ({ page }) => {
    await page.goto("/settings/github");

    // Check for privacy notice
    await expect(page.locator("text=Privacy & Security")).toBeVisible();
    await expect(
      page.locator("text=Your GitHub access token is encrypted")
    ).toBeVisible();
  });

  test("should navigate back to settings", async ({ page }) => {
    await page.goto("/settings/github");

    // Click back button
    await page.click('button:has-text("Back to Settings")');

    // Should navigate to settings page
    await page.waitForURL("/app/settings");
  });
});

test.describe("GitHub Repository Connection (Project Context)", () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto("/login");
    await page.fill('input[type="email"]', "user@example.com");
    await page.fill('input[type="password"]', "password123");
    await page.click('button[type="submit"]');

    // Navigate to a project
    await page.goto("/app/projects/test-project-id");
  });

  test("should show GitHub connection status in project", async ({ page }) => {
    // Check for GitHub integration section
    await expect(page.locator("text=GitHub Integration")).toBeVisible();

    // Check for connected repository name
    await expect(page.locator("text=owner/repository")).toBeVisible();

    // Check for sync status
    await expect(page.locator("text=Last synced")).toBeVisible();
  });

  test("should trigger manual sync for project repository", async ({ page }) => {
    // Click sync button
    await page.click('button:has-text("Sync Now")');

    // Should show syncing state
    await expect(page.locator("text=Syncing...")).toBeVisible();

    // Wait for sync to complete
    await expect(page.locator("text=Syncing...")).not.toBeVisible();

    // Should update last synced time
    await expect(page.locator("text=Last synced just now")).toBeVisible();
  });

  test("should disconnect repository from project", async ({ page }) => {
    // Click disconnect button
    await page.click('button:has-text("Disconnect Repository")');

    // Confirm disconnection
    await expect(
      page.locator("text=Disconnect repository from project?")
    ).toBeVisible();
    await page.click('button:has-text("Disconnect")');

    // Should show connect repository button
    await expect(page.locator('button:has-text("Connect Repository")')).toBeVisible();
  });

  test("should handle sync errors gracefully", async ({ page }) => {
    // Mock sync error
    await page.click('button:has-text("Sync Now")');

    // Should show error message
    await expect(page.locator("text=Sync failed")).toBeVisible();
    await expect(page.locator("text=Retry")).toBeVisible();

    // Retry sync
    await page.click('button:has-text("Retry")');
  });
});

test.describe("GitHub OAuth Callback", () => {
  test("should handle successful OAuth callback", async ({ page }) => {
    // Navigate to OAuth callback with success code
    await page.goto("/settings/github/callback?code=success_code&state=valid_state");

    // Should redirect to GitHub settings
    await page.waitForURL("/settings/github");

    // Should show success message
    await expect(page.locator("text=GitHub connected successfully")).toBeVisible();

    // Should show connected status
    await expect(page.locator("text=Connected")).toBeVisible();
  });

  test("should handle OAuth callback error", async ({ page }) => {
    // Navigate to OAuth callback with error
    await page.goto("/settings/github/callback?error=access_denied");

    // Should show error message
    await expect(page.locator("text=GitHub connection failed")).toBeVisible();
    await expect(page.locator("text=Access denied")).toBeVisible();

    // Should still show connect button
    await expect(page.locator('button:has-text("Connect GitHub")')).toBeVisible();
  });

  test("should handle invalid state parameter", async ({ page }) => {
    // Navigate to OAuth callback with invalid state
    await page.goto("/settings/github/callback?code=code&state=invalid_state");

    // Should show security error
    await expect(page.locator("text=Invalid OAuth state")).toBeVisible();
  });
});
