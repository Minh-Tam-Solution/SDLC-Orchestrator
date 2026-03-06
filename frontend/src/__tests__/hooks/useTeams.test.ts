/**
 * useTeams Hook Tests
 *
 * @module frontend/src/__tests__/hooks/useTeams.test
 * @description Tests for team list, detail, members, and stats hooks
 * @sdlc SDLC 6.1.1 - Sprint 84
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import React from "react";

// Mock useAuth
vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({ isAuthenticated: true, isLoading: false, user: { id: "u1" } }),
}));

// Mock API functions
const mockGetTeams = vi.fn();
const mockGetTeam = vi.fn();
const mockGetTeamStats = vi.fn();
const mockGetTeamMembers = vi.fn();
const mockCreateTeam = vi.fn();
const mockUpdateTeam = vi.fn();
const mockDeleteTeam = vi.fn();
const mockAddTeamMember = vi.fn();
const mockUpdateTeamMemberRole = vi.fn();
const mockRemoveTeamMember = vi.fn();
vi.mock("@/lib/api", () => ({
  getTeams: (...args: unknown[]) => mockGetTeams(...args),
  getTeam: (...args: unknown[]) => mockGetTeam(...args),
  getTeamStats: (...args: unknown[]) => mockGetTeamStats(...args),
  getTeamMembers: (...args: unknown[]) => mockGetTeamMembers(...args),
  createTeam: (...args: unknown[]) => mockCreateTeam(...args),
  updateTeam: (...args: unknown[]) => mockUpdateTeam(...args),
  deleteTeam: (...args: unknown[]) => mockDeleteTeam(...args),
  addTeamMember: (...args: unknown[]) => mockAddTeamMember(...args),
  updateTeamMemberRole: (...args: unknown[]) => mockUpdateTeamMemberRole(...args),
  removeTeamMember: (...args: unknown[]) => mockRemoveTeamMember(...args),
}));

import { useTeams, useTeam, useTeamStats, useTeamMembers, teamKeys } from "@/hooks/useTeams";

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

describe("useTeams", () => {
  it("fetches team list successfully", async () => {
    const teams = { items: [{ id: "t1", name: "Backend" }], total: 1 };
    mockGetTeams.mockResolvedValueOnce(teams);

    const { result } = renderHook(() => useTeams(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(teams);
  });

  it("passes filter params to API", async () => {
    mockGetTeams.mockResolvedValueOnce({ items: [], total: 0 });

    renderHook(() => useTeams({ organization_id: "org1" }), { wrapper });

    await waitFor(() => {
      expect(mockGetTeams).toHaveBeenCalledWith({ organization_id: "org1" });
    });
  });
});

describe("useTeam", () => {
  it("fetches single team by ID", async () => {
    const team = { id: "t1", name: "Backend", members_count: 5 };
    mockGetTeam.mockResolvedValueOnce(team);

    const { result } = renderHook(() => useTeam("t1"), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(team);
  });

  it("does not fetch when teamId is undefined", () => {
    const { result } = renderHook(() => useTeam(undefined), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockGetTeam).not.toHaveBeenCalled();
  });
});

describe("useTeamMembers", () => {
  it("fetches team members", async () => {
    const members = { items: [{ user_id: "u1", role: "owner" }], total: 1 };
    mockGetTeamMembers.mockResolvedValueOnce(members);

    const { result } = renderHook(() => useTeamMembers("t1"), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(members);
    expect(mockGetTeamMembers).toHaveBeenCalledWith("t1", undefined);
  });
});

describe("useTeamStats", () => {
  it("fetches team statistics", async () => {
    const stats = { member_count: 5, project_count: 3, gate_pass_rate: 0.85 };
    mockGetTeamStats.mockResolvedValueOnce(stats);

    const { result } = renderHook(() => useTeamStats("t1"), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(stats);
  });
});

describe("teamKeys", () => {
  it("generates correct cache key structure", () => {
    expect(teamKeys.all).toEqual(["teams"]);
    expect(teamKeys.detail("t1")).toEqual(["teams", "detail", "t1"]);
    expect(teamKeys.stats("t1")).toEqual(["teams", "detail", "t1", "stats"]);
    expect(teamKeys.members("t1")).toEqual(["teams", "detail", "t1", "members"]);
  });
});
