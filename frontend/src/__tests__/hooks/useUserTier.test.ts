/**
 * useUserTier Hook Tests
 *
 * @module frontend/src/__tests__/hooks/useUserTier.test
 * @description Tests for tier calculation logic and useUserTier hook
 * @sdlc SDLC 6.1.1 - Sprint 146
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import React from "react";

// Mock the api object used by useUserTier
const mockApiGet = vi.fn();
vi.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockApiGet(...args),
  },
}));

// Mock TierBadge type export
vi.mock("@/components/user/TierBadge", () => ({}));

import { useUserTier, calculateEffectiveTier } from "@/hooks/useUserTier";
import type { UserOrganization } from "@/hooks/useUserTier";

let queryClient: QueryClient;

function wrapper({ children }: { children: ReactNode }) {
  return React.createElement(QueryClientProvider, { client: queryClient }, children);
}

beforeEach(() => {
  vi.clearAllMocks();
  queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
});

describe("calculateEffectiveTier", () => {
  it("returns 'free' when no organizations", () => {
    expect(calculateEffectiveTier([])).toBe("free");
  });

  it("returns 'free' when organizations is null-ish", () => {
    expect(calculateEffectiveTier(null as unknown as UserOrganization[])).toBe("free");
  });

  it("returns the highest tier among organizations", () => {
    const orgs: UserOrganization[] = [
      { id: "o1", name: "Org1", slug: "org1", plan: "free", role: "member", joined_at: "2026-01-01" },
      { id: "o2", name: "Org2", slug: "org2", plan: "pro", role: "admin", joined_at: "2026-01-01" },
      { id: "o3", name: "Org3", slug: "org3", plan: "starter", role: "member", joined_at: "2026-01-01" },
    ];
    expect(calculateEffectiveTier(orgs)).toBe("pro");
  });

  it("returns 'enterprise' and short-circuits for enterprise tier", () => {
    const orgs: UserOrganization[] = [
      { id: "o1", name: "Org1", slug: "org1", plan: "starter", role: "member", joined_at: "2026-01-01" },
      { id: "o2", name: "Org2", slug: "org2", plan: "enterprise", role: "owner", joined_at: "2026-01-01" },
      { id: "o3", name: "Org3", slug: "org3", plan: "pro", role: "member", joined_at: "2026-01-01" },
    ];
    expect(calculateEffectiveTier(orgs)).toBe("enterprise");
  });

  it("returns single org plan when only one organization", () => {
    const orgs: UserOrganization[] = [
      { id: "o1", name: "Org1", slug: "org1", plan: "starter", role: "owner", joined_at: "2026-01-01" },
    ];
    expect(calculateEffectiveTier(orgs)).toBe("starter");
  });
});

describe("useUserTier", () => {
  it("returns user profile with effective tier", async () => {
    const profile = {
      id: "u1",
      email: "test@example.com",
      name: "Test User",
      effective_tier: "pro" as const,
      organizations: [
        { id: "o1", name: "Org1", slug: "org1", plan: "pro", role: "admin", joined_at: "2026-01-01" },
      ],
    };
    mockApiGet.mockResolvedValueOnce({ data: profile });

    const { result } = renderHook(() => useUserTier(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.effectiveTier).toBe("pro");
    expect(result.current.hasPro).toBe(true);
    expect(result.current.hasEnterprise).toBe(false);
    expect(result.current.organizationCount).toBe(1);
  });

  it("defaults to 'free' when API fails", async () => {
    mockApiGet.mockRejectedValueOnce(new Error("Unauthorized"));

    const { result } = renderHook(() => useUserTier(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.effectiveTier).toBe("free");
    expect(result.current.organizationCount).toBe(0);
  });
});
