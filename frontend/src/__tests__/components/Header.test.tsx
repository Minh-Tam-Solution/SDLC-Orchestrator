/**
 * Header Tests — Sprint 212 Track A2
 *
 * Tests user name display, breadcrumb rendering,
 * profile dropdown, and logout action.
 *
 * @module frontend/src/__tests__/components/Header.test
 * @sprint 212
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/app/projects",
}));

// Mock next/link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock useAuth
const mockLogout = vi.fn().mockResolvedValue(undefined);
vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({
    user: { name: "Jane Doe", email: "jane@example.com", roles: ["admin"] },
    isAuthenticated: true,
    isLoading: false,
    logout: mockLogout,
  }),
}));

// Mock useWorkspace — no organizations to simplify Header rendering
vi.mock("@/contexts/WorkspaceContext", () => ({
  useWorkspace: () => ({
    selectedOrganization: null,
    selectedTeam: null,
    organizations: [],
    teams: [],
    isLoadingOrganizations: false,
    isLoadingTeams: false,
    selectOrganization: vi.fn(),
    selectTeam: vi.fn(),
    hasOrganizations: false,
  }),
}));

// Mock useUserTier
vi.mock("@/hooks/useUserTier", () => ({
  useUserTier: () => ({
    effectiveTier: "pro",
    organizationCount: 1,
    isLoading: false,
  }),
}));

// Mock TierBadge as simple span to avoid deep dependency chain
vi.mock("@/components/user/TierBadge", () => ({
  TierBadge: ({ tier }: { tier: string }) => <span data-testid="tier-badge">{tier}</span>,
}));

import { Header } from "@/components/dashboard/Header";

describe("Header", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock window.location for logout redirect
    Object.defineProperty(window, "location", {
      value: { href: "" },
      writable: true,
    });
  });

  it("displays user name and role", () => {
    render(<Header />);

    expect(screen.getByText("Jane Doe")).toBeInTheDocument();
    expect(screen.getByText(/admin/)).toBeInTheDocument();
  });

  it("renders breadcrumbs for the current path", () => {
    render(<Header />);

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Projects")).toBeInTheDocument();
  });

  it("opens profile dropdown and shows Sign out button", () => {
    render(<Header />);

    // Click the profile button (identified by the avatar initial)
    const avatarInitial = screen.getByText("J");
    const profileButton = avatarInitial.closest("button");
    expect(profileButton).toBeTruthy();
    fireEvent.click(profileButton!);

    expect(screen.getByText("Sign out")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("calls logout when Sign out is clicked", async () => {
    render(<Header />);

    // Open profile dropdown
    const avatarInitial = screen.getByText("J");
    fireEvent.click(avatarInitial.closest("button")!);

    // Click Sign out
    fireEvent.click(screen.getByText("Sign out"));

    expect(mockLogout).toHaveBeenCalled();
  });
});
