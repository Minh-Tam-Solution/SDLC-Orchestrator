/**
 * AuthGuard Tests — Sprint 212 Track A2
 *
 * Tests child rendering when authenticated, redirect when
 * unauthenticated, and loading skeleton during auth check.
 *
 * @module frontend/src/__tests__/components/AuthGuard.test
 * @sprint 212
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => "/app/projects",
}));

// Auth mock — overridden per test via mockReturnValue
const mockUseAuth = vi.fn();
vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => mockUseAuth(),
}));

import { AuthGuard } from "@/components/auth/AuthGuard";

describe("AuthGuard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders children when authenticated", () => {
    mockUseAuth.mockReturnValue({
      isLoading: false,
      isAuthenticated: true,
      user: { name: "Test User" },
    });

    render(
      <AuthGuard>
        <div data-testid="protected-content">Secret Page</div>
      </AuthGuard>
    );

    expect(screen.getByTestId("protected-content")).toBeInTheDocument();
    expect(screen.getByText("Secret Page")).toBeInTheDocument();
  });

  it("shows loading skeleton during auth check", () => {
    mockUseAuth.mockReturnValue({
      isLoading: true,
      isAuthenticated: false,
      user: null,
    });

    render(
      <AuthGuard>
        <div>Protected</div>
      </AuthGuard>
    );

    // Loading skeleton shows Vietnamese text
    expect(screen.getByText(/xác thực/i)).toBeInTheDocument();
    expect(screen.queryByText("Protected")).not.toBeInTheDocument();
  });

  it("redirects to login when not authenticated", () => {
    mockUseAuth.mockReturnValue({
      isLoading: false,
      isAuthenticated: false,
      user: null,
    });

    render(
      <AuthGuard>
        <div>Protected</div>
      </AuthGuard>
    );

    expect(mockPush).toHaveBeenCalledWith(
      expect.stringContaining("/login?redirect=")
    );
    expect(screen.queryByText("Protected")).not.toBeInTheDocument();
  });

  it("uses custom fallbackPath when provided", () => {
    mockUseAuth.mockReturnValue({
      isLoading: false,
      isAuthenticated: false,
      user: null,
    });

    render(
      <AuthGuard fallbackPath="/auth/signin">
        <div>Protected</div>
      </AuthGuard>
    );

    expect(mockPush).toHaveBeenCalledWith(
      expect.stringContaining("/auth/signin?redirect=")
    );
  });
});
