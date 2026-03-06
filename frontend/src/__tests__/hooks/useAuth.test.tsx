/**
 * useAuth Hook Tests
 *
 * @module frontend/src/__tests__/hooks/useAuth.test
 * @description Tests for AuthProvider context, login, logout, refresh, and role checking
 * @sdlc SDLC 6.1.1 - Sprint 63 httpOnly Cookie Migration
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";

// Mock next/navigation (required by some downstream imports)
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

// Mock API functions
const mockGetCurrentUser = vi.fn();
const mockLogout = vi.fn();
const mockRefreshToken = vi.fn();
vi.mock("@/lib/api", () => ({
  getCurrentUser: (...args: unknown[]) => mockGetCurrentUser(...args),
  logout: (...args: unknown[]) => mockLogout(...args),
  refreshToken: (...args: unknown[]) => mockRefreshToken(...args),
}));

import { AuthProvider, useAuth, useHasRole } from "@/hooks/useAuth";

function wrapper({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

describe("useAuth", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("throws when used outside AuthProvider", () => {
    expect(() => {
      renderHook(() => useAuth());
    }).toThrow("useAuth must be used within an AuthProvider");
  });

  it("initializes with loading state then resolves to unauthenticated when no cookie", async () => {
    mockGetCurrentUser.mockRejectedValueOnce(new Error("Unauthorized"));

    const { result } = renderHook(() => useAuth(), { wrapper });

    // Initially loading
    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it("fetches user on mount and sets authenticated state", async () => {
    const mockUser = { id: "u1", email: "test@example.com", roles: ["dev"] };
    mockGetCurrentUser.mockResolvedValueOnce(mockUser);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual(mockUser);
    expect(result.current.error).toBeNull();
  });

  it("login fetches user profile after backend sets cookies", async () => {
    // First call on mount - unauthenticated
    mockGetCurrentUser.mockRejectedValueOnce(new Error("No session"));

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Second call after login
    const mockUser = { id: "u2", email: "admin@test.com", roles: ["admin"] };
    mockGetCurrentUser.mockResolvedValueOnce(mockUser);

    await act(async () => {
      await result.current.login({ access_token: "tok", refresh_token: "ref", token_type: "bearer" });
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual(mockUser);
  });

  it("logout clears user state and calls API", async () => {
    const mockUser = { id: "u1", email: "test@test.com", roles: ["dev"] };
    mockGetCurrentUser.mockResolvedValueOnce(mockUser);
    mockLogout.mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });

    await act(async () => {
      await result.current.logout();
    });

    expect(mockLogout).toHaveBeenCalledTimes(1);
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it("refreshAuth returns true on success", async () => {
    mockGetCurrentUser.mockRejectedValueOnce(new Error("Expired"));

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const refreshedUser = { id: "u1", email: "test@test.com", roles: ["pm"] };
    mockRefreshToken.mockResolvedValueOnce({ access_token: "new", refresh_token: "new-ref" });
    mockGetCurrentUser.mockResolvedValueOnce(refreshedUser);

    let success: boolean = false;
    await act(async () => {
      success = await result.current.refreshAuth();
    });

    expect(success).toBe(true);
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual(refreshedUser);
  });

  it("getAccessToken returns null (httpOnly cookie model)", async () => {
    mockGetCurrentUser.mockResolvedValueOnce({ id: "u1", email: "a@b.com", roles: [] });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.getAccessToken()).toBeNull();
  });
});

describe("useHasRole", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns true when user has a matching role", async () => {
    mockGetCurrentUser.mockResolvedValueOnce({ id: "u1", email: "a@b.com", roles: ["admin", "dev"] });

    const { result } = renderHook(() => useHasRole(["admin"]), { wrapper });

    await waitFor(() => {
      expect(result.current).toBe(true);
    });
  });

  it("returns false when user lacks the required role", async () => {
    mockGetCurrentUser.mockResolvedValueOnce({ id: "u1", email: "a@b.com", roles: ["dev"] });

    const { result } = renderHook(() => useHasRole(["cto", "ceo"]), { wrapper });

    await waitFor(() => {
      expect(result.current).toBe(false);
    });
  });
});
