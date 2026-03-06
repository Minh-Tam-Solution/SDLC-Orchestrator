/**
 * useKillSwitch Hook Tests
 *
 * @module frontend/src/__tests__/hooks/useKillSwitch.test
 * @description Tests for governance mode, kill switch check, and role authorization hooks
 * @sdlc SDLC 6.1.1 - Sprint 113
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import React from "react";

// Configurable auth mock
let mockAuthUser: Record<string, unknown> | null = { id: "u1", roles: ["dev"], is_platform_admin: false };
vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({
    isAuthenticated: !!mockAuthUser,
    isLoading: false,
    user: mockAuthUser,
  }),
}));

// Mock kill-switch types (the module only exports types, no runtime values)
vi.mock("@/lib/types/kill-switch", () => ({}));

// Mock API functions
const mockGetGovernanceMode = vi.fn();
const mockCheckKillSwitch = vi.fn();
const mockGetBreakGlassRequests = vi.fn();
const mockGetModeHistory = vi.fn();
const mockGetGovernanceAuditLog = vi.fn();
const mockGetKillSwitchDashboard = vi.fn();
const mockSetGovernanceMode = vi.fn();
const mockTriggerRollback = vi.fn();
const mockCreateBreakGlass = vi.fn();
const mockResolveBreakGlass = vi.fn();
vi.mock("@/lib/api", () => ({
  getGovernanceMode: (...args: unknown[]) => mockGetGovernanceMode(...args),
  checkKillSwitch: (...args: unknown[]) => mockCheckKillSwitch(...args),
  getBreakGlassRequests: (...args: unknown[]) => mockGetBreakGlassRequests(...args),
  getModeHistory: (...args: unknown[]) => mockGetModeHistory(...args),
  getGovernanceAuditLog: (...args: unknown[]) => mockGetGovernanceAuditLog(...args),
  getKillSwitchDashboard: (...args: unknown[]) => mockGetKillSwitchDashboard(...args),
  setGovernanceMode: (...args: unknown[]) => mockSetGovernanceMode(...args),
  triggerRollback: (...args: unknown[]) => mockTriggerRollback(...args),
  createBreakGlass: (...args: unknown[]) => mockCreateBreakGlass(...args),
  resolveBreakGlass: (...args: unknown[]) => mockResolveBreakGlass(...args),
}));

import {
  useGovernanceMode,
  useKillSwitchCheck,
  useCanChangeMode,
  useBreakGlassAuthorization,
  killSwitchKeys,
} from "@/hooks/useKillSwitch";

let queryClient: QueryClient;

function wrapper({ children }: { children: ReactNode }) {
  return React.createElement(QueryClientProvider, { client: queryClient }, children);
}

beforeEach(() => {
  vi.clearAllMocks();
  mockAuthUser = { id: "u1", roles: ["dev"], is_platform_admin: false };
  queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
});

describe("useGovernanceMode", () => {
  it("fetches current governance mode", async () => {
    const modeData = {
      mode: "FULL",
      last_changed: "2026-02-01T00:00:00Z",
      changed_by: "cto",
      auto_rollback_enabled: true,
      rollback_criteria_met: false,
    };
    mockGetGovernanceMode.mockResolvedValueOnce(modeData);

    const { result } = renderHook(() => useGovernanceMode(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(modeData);
  });

  it("handles API error", async () => {
    mockGetGovernanceMode.mockRejectedValueOnce(new Error("Forbidden"));

    const { result } = renderHook(() => useGovernanceMode(), { wrapper });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

describe("useKillSwitchCheck", () => {
  it("fetches kill switch criteria check result", async () => {
    const checkResult = { triggered: false, criteria: [], threshold: 80 };
    mockCheckKillSwitch.mockResolvedValueOnce(checkResult);

    const { result } = renderHook(() => useKillSwitchCheck(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(checkResult);
  });
});

describe("useCanChangeMode", () => {
  it("returns false for regular dev role", () => {
    mockAuthUser = { id: "u1", roles: ["dev"], is_platform_admin: false };

    const { result } = renderHook(() => useCanChangeMode(), { wrapper });

    expect(result.current).toBe(false);
  });

  it("returns true for CTO role", () => {
    mockAuthUser = { id: "u1", roles: ["CTO"], is_platform_admin: false };

    const { result } = renderHook(() => useCanChangeMode(), { wrapper });

    expect(result.current).toBe(true);
  });

  it("returns true for admin role", () => {
    mockAuthUser = { id: "u1", roles: ["admin"], is_platform_admin: false };

    const { result } = renderHook(() => useCanChangeMode(), { wrapper });

    expect(result.current).toBe(true);
  });

  it("returns true for platform admin", () => {
    mockAuthUser = { id: "u1", roles: ["dev"], is_platform_admin: true };

    const { result } = renderHook(() => useCanChangeMode(), { wrapper });

    expect(result.current).toBe(true);
  });
});

describe("useBreakGlassAuthorization", () => {
  it("returns null for regular user", () => {
    mockAuthUser = { id: "u1", roles: ["dev"], is_platform_admin: false };

    const { result } = renderHook(() => useBreakGlassAuthorization(), { wrapper });

    expect(result.current).toBeNull();
  });

  it("returns 'ceo' for CEO role", () => {
    mockAuthUser = { id: "u1", roles: ["CEO"], is_platform_admin: false };

    const { result } = renderHook(() => useBreakGlassAuthorization(), { wrapper });

    expect(result.current).toBe("ceo");
  });

  it("returns 'ceo' for platform admin", () => {
    mockAuthUser = { id: "u1", roles: ["dev"], is_platform_admin: true };

    const { result } = renderHook(() => useBreakGlassAuthorization(), { wrapper });

    expect(result.current).toBe("ceo");
  });

  it("returns 'cto' for CTO role", () => {
    mockAuthUser = { id: "u1", roles: ["CTO"], is_platform_admin: false };

    const { result } = renderHook(() => useBreakGlassAuthorization(), { wrapper });

    expect(result.current).toBe("cto");
  });

  it("returns 'tech_lead' for tech_lead role", () => {
    mockAuthUser = { id: "u1", roles: ["tech_lead"], is_platform_admin: false };

    const { result } = renderHook(() => useBreakGlassAuthorization(), { wrapper });

    expect(result.current).toBe("tech_lead");
  });
});

describe("killSwitchKeys", () => {
  it("generates correct cache key structure", () => {
    expect(killSwitchKeys.all).toEqual(["kill-switch"]);
    expect(killSwitchKeys.mode()).toEqual(["kill-switch", "mode"]);
    expect(killSwitchKeys.check()).toEqual(["kill-switch", "check"]);
    expect(killSwitchKeys.dashboard()).toEqual(["kill-switch", "dashboard"]);
  });
});
