/**
 * Sidebar Tests — Sprint 212 Track A2d
 *
 * Tests core nav item rendering and feature flag filtering.
 *
 * @module frontend/src/__tests__/sidebar.test
 * @sprint 212
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/app",
}));

// Mock next/link
vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: { children: React.ReactNode; href: string; [k: string]: unknown }) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

// Mock useAuth
vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({
    user: { id: "u1", email: "test@example.com", is_superuser: false },
    isAuthenticated: true,
    isLoading: false,
  }),
}));

import { Sidebar } from "@/components/dashboard/Sidebar";

describe("Sidebar", () => {
  it("renders core nav items (Dashboard, Projects, Gates, Evidence, Policies, OTT Gateway)", () => {
    render(<Sidebar />);

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Projects")).toBeInTheDocument();
    expect(screen.getByText("Gates")).toBeInTheDocument();
    expect(screen.getByText("Evidence")).toBeInTheDocument();
    expect(screen.getByText("Policies")).toBeInTheDocument();
    expect(screen.getByText("OTT Gateway")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("hides flagged pages when feature flags are not set", () => {
    // By default all FF_* env vars are undefined/falsy, so flagGroup items are filtered out
    render(<Sidebar />);

    // These pages have flagGroup and should be hidden when flags are off
    expect(screen.queryByText("CEO Dashboard")).not.toBeInTheDocument();
    expect(screen.queryByText("Planning")).not.toBeInTheDocument();
    expect(screen.queryByText("Context Authority")).not.toBeInTheDocument();
    expect(screen.queryByText("VCR")).not.toBeInTheDocument();
    expect(screen.queryByText("CLI Tokens")).not.toBeInTheDocument();
    expect(screen.queryByText("App Builder")).not.toBeInTheDocument();
  });

  it("does not render Admin Panel for non-superuser", () => {
    render(<Sidebar />);

    expect(screen.queryByText("Admin Panel")).not.toBeInTheDocument();
    expect(screen.queryByText("System Settings")).not.toBeInTheDocument();
  });
});
