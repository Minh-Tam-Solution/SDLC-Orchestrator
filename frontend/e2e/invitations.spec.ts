import { test, expect } from "@playwright/test";

test.describe("Team Invitations", () => {
  test.beforeEach(async ({ page }) => {
    // Login as team owner/admin
    await page.goto("/login");
    await page.fill('input[type="email"]', "owner@example.com");
    await page.fill('input[type="password"]', "password123");
    await page.click('button[type="submit"]');
    await page.waitForURL("/app/teams");
  });

  test("should display invitations page", async ({ page }) => {
    // Navigate to a team
    await page.click('a:has-text("Engineering Team")');
    await page.waitForURL(/\/app\/teams\/.+/);

    // Navigate to invitations
    await page.click('text=Invitations');
    await page.waitForURL(/\/app\/teams\/.+\/invitations/);

    // Check page title
    await expect(page.locator("h1")).toContainText("Engineering Team");

    // Check tabs are visible
    await expect(page.locator('button[role="tab"]:has-text("Pending")')).toBeVisible();
    await expect(page.locator('button[role="tab"]:has-text("Accepted")')).toBeVisible();
    await expect(page.locator('button[role="tab"]:has-text("Expired")')).toBeVisible();
    await expect(page.locator('button[role="tab"]:has-text("Declined")')).toBeVisible();
  });

  test("should send invitation successfully", async ({ page }) => {
    // Navigate to invitations page
    await page.goto("/app/teams/test-team-id/invitations");

    // Click "Invite Member" button
    await page.click('button:has-text("Invite Member")');

    // Fill invitation form
    await page.fill('input[type="email"]', "newmember@example.com");
    await page.click('button:has-text("Select a role")');
    await page.click('text=Member');

    // Submit invitation
    await page.click('button[type="submit"]:has-text("Send Invitation")');

    // Wait for success (modal should close)
    await expect(page.locator('dialog[open]')).not.toBeVisible();

    // Verify invitation appears in pending tab
    await expect(page.locator("text=newmember@example.com")).toBeVisible();
    await expect(page.locator('text=Pending').first()).toBeVisible();
  });

  test("should validate email format", async ({ page }) => {
    await page.goto("/app/teams/test-team-id/invitations");

    // Click "Invite Member" button
    await page.click('button:has-text("Invite Member")');

    // Enter invalid email
    await page.fill('input[type="email"]', "invalid-email");

    // Try to submit
    await page.click('button[type="submit"]:has-text("Send Invitation")');

    // Error should be displayed
    await expect(page.locator("text=Please enter a valid email address")).toBeVisible();
  });

  test("should handle duplicate invitation", async ({ page }) => {
    await page.goto("/app/teams/test-team-id/invitations");

    // Click "Invite Member" button
    await page.click('button:has-text("Invite Member")');

    // Enter email that already has pending invitation
    await page.fill('input[type="email"]', "existing@example.com");
    await page.click('button:has-text("Select a role")');
    await page.click('text=Member');

    // Submit invitation
    await page.click('button[type="submit"]:has-text("Send Invitation")');

    // Error should be displayed
    await expect(
      page.locator("text=An invitation has already been sent")
    ).toBeVisible();
  });

  test("should cancel invitation", async ({ page }) => {
    await page.goto("/app/teams/test-team-id/invitations");

    // Find pending invitation and click cancel
    const invitationCard = page.locator("text=pending@example.com").locator("..");
    await invitationCard.locator('button:has-text("Cancel")').click();

    // Confirm cancellation in alert dialog
    await page.click('button:has-text("Cancel Invitation")');

    // Invitation should be removed
    await expect(page.locator("text=pending@example.com")).not.toBeVisible();
  });

  test("should resend invitation", async ({ page }) => {
    await page.goto("/app/teams/test-team-id/invitations");

    // Navigate to expired tab
    await page.click('button[role="tab"]:has-text("Expired")');

    // Find expired invitation and click resend
    const invitationCard = page.locator("text=expired@example.com").locator("..");
    await invitationCard.locator('button:has-text("Resend")').click();

    // Wait for API call to complete
    await page.waitForTimeout(1000);

    // Success message or invitation moved to pending tab
    await page.click('button[role="tab"]:has-text("Pending")');
    await expect(page.locator("text=expired@example.com")).toBeVisible();
  });

  test("should filter invitations by status tabs", async ({ page }) => {
    await page.goto("/app/teams/test-team-id/invitations");

    // Check pending tab (default)
    await expect(page.locator("text=Waiting for response").first()).toBeVisible();

    // Switch to accepted tab
    await page.click('button[role="tab"]:has-text("Accepted")');
    await expect(page.locator("text=Joined the team").first()).toBeVisible();

    // Switch to expired tab
    await page.click('button[role="tab"]:has-text("Expired")');
    await expect(page.locator("text=Link expired").first()).toBeVisible();

    // Switch to declined tab
    await page.click('button[role="tab"]:has-text("Declined")');
    await expect(page.locator("text=Invitation declined").first()).toBeVisible();
  });

  test("should show permission warning for non-admin users", async ({ page }) => {
    // Logout and login as member (not owner/admin)
    await page.goto("/logout");
    await page.goto("/login");
    await page.fill('input[type="email"]', "member@example.com");
    await page.fill('input[type="password"]', "password123");
    await page.click('button[type="submit"]');

    // Navigate to invitations
    await page.goto("/app/teams/test-team-id/invitations");

    // Permission warning should be visible
    await expect(page.locator("text=Limited Access")).toBeVisible();
    await expect(
      page.locator("text=You can view invitations but cannot send or manage them")
    ).toBeVisible();

    // "Invite Member" button should not be visible
    await expect(page.locator('button:has-text("Invite Member")')).not.toBeVisible();
  });

  test("should display empty state when no invitations", async ({ page }) => {
    await page.goto("/app/teams/empty-team-id/invitations");

    // Check for empty state message
    await expect(page.locator("text=No pending invitations")).toBeVisible();
    await expect(
      page.locator("text=Invite members to collaborate on your team")
    ).toBeVisible();
  });

  test("should select different roles when inviting", async ({ page }) => {
    await page.goto("/app/teams/test-team-id/invitations");

    // Click "Invite Member" button
    await page.click('button:has-text("Invite Member")');

    // Fill email
    await page.fill('input[type="email"]', "admin@example.com");

    // Select Owner role
    await page.click('button:has-text("Select a role")');
    await page.click('text=Owner');
    await expect(
      page.locator("text=Full access including team deletion and billing")
    ).toBeVisible();

    // Select Admin role
    await page.click('button:has-text("Owner")');
    await page.click('text=Admin');
    await expect(
      page.locator("text=Manage team members, projects, and settings")
    ).toBeVisible();

    // Select Member role
    await page.click('button:has-text("Admin")');
    await page.click('text=Member');
    await expect(
      page.locator("text=Access team projects and contribute")
    ).toBeVisible();

    // Select Viewer role
    await page.click('button:has-text("Member")');
    await page.click('text=Viewer');
    await expect(
      page.locator("text=Read-only access to team projects")
    ).toBeVisible();
  });
});

test.describe("Accept Invitation Flow", () => {
  test("should accept invitation from email link", async ({ page }) => {
    // Navigate to invitation acceptance page with token
    const token = "test-invitation-token-123";
    await page.goto(`/invitations/accept/${token}`);

    // Invitation details should be displayed
    await expect(page.locator("text=Join")).toBeVisible();
    await expect(page.locator("h2")).toContainText("Engineering Team");

    // Click accept button
    await page.click('button:has-text("Accept Invitation")');

    // Wait for redirect to team page
    await page.waitForURL(/\/app\/teams\/.+/);

    // Success message should be displayed
    await expect(page.locator("text=Welcome to the team!")).toBeVisible();
  });

  test("should decline invitation from email link", async ({ page }) => {
    const token = "test-invitation-token-456";
    await page.goto(`/invitations/accept/${token}`);

    // Click decline button
    await page.click('button:has-text("Decline")');

    // Confirm decline in alert dialog
    await page.click('button:has-text("Decline Invitation")');

    // Confirmation message should be displayed
    await expect(page.locator("text=Invitation declined")).toBeVisible();
  });

  test("should handle expired invitation token", async ({ page }) => {
    const expiredToken = "expired-token-789";
    await page.goto(`/invitations/accept/${expiredToken}`);

    // Error message should be displayed
    await expect(page.locator("text=This invitation has expired")).toBeVisible();
    await expect(
      page.locator("text=Contact the team owner for a new invitation")
    ).toBeVisible();
  });

  test("should handle invalid invitation token", async ({ page }) => {
    const invalidToken = "invalid-token-000";
    await page.goto(`/invitations/accept/${invalidToken}`);

    // Error message should be displayed
    await expect(page.locator("text=Invalid invitation")).toBeVisible();
  });
});
