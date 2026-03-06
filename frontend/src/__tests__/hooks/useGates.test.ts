/**
 * useGates Hook Tests
 *
 * @module frontend/src/__tests__/hooks/useGates.test
 * @description Tests for gate list, detail, filtering, submit, and approve hooks
 * @sdlc SDLC 6.1.1
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

// Mock telemetry
vi.mock("@/lib/telemetry", () => ({
  trackFirstGatePassed: vi.fn(),
  trackEvent: vi.fn(),
  TELEMETRY_EVENTS: { GATE_APPROVAL_REQUESTED: "gate_approval_requested" },
}));

// Mock API functions
const mockGetGates = vi.fn();
const mockGetGate = vi.fn();
const mockGetGateApprovals = vi.fn();
const mockSubmitGate = vi.fn();
const mockApproveGate = vi.fn();
vi.mock("@/lib/api", () => ({
  getGates: (...args: unknown[]) => mockGetGates(...args),
  getGate: (...args: unknown[]) => mockGetGate(...args),
  getGateApprovals: (...args: unknown[]) => mockGetGateApprovals(...args),
  submitGate: (...args: unknown[]) => mockSubmitGate(...args),
  approveGate: (...args: unknown[]) => mockApproveGate(...args),
}));

import { useGates, useGate, useProjectGates, useGatesByStage, useGateApprovals, gateKeys } from "@/hooks/useGates";

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

describe("useGates", () => {
  it("fetches gate list successfully", async () => {
    const gates = [
      { id: "g1", gate_type: "G1_CONSULTATION", status: "DRAFT" },
      { id: "g2", gate_type: "G2_SECURITY", status: "APPROVED" },
    ];
    mockGetGates.mockResolvedValueOnce(gates);

    const { result } = renderHook(() => useGates(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(gates);
  });

  it("passes filter options to API", async () => {
    mockGetGates.mockResolvedValueOnce([]);

    const options = { project_id: "p1", stage: "BUILD" };
    const { result } = renderHook(() => useGates(options), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockGetGates).toHaveBeenCalledWith(options);
  });

  it("handles API error", async () => {
    mockGetGates.mockRejectedValueOnce(new Error("Server error"));

    const { result } = renderHook(() => useGates(), { wrapper });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

describe("useProjectGates", () => {
  it("passes project_id filter to useGates", async () => {
    mockGetGates.mockResolvedValueOnce([]);

    const { result } = renderHook(() => useProjectGates("p1"), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockGetGates).toHaveBeenCalledWith({ project_id: "p1" });
  });
});

describe("useGatesByStage", () => {
  it("passes stage filter to useGates", async () => {
    mockGetGates.mockResolvedValueOnce([]);

    const { result } = renderHook(() => useGatesByStage("BUILD"), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockGetGates).toHaveBeenCalledWith({ stage: "BUILD" });
  });
});

describe("useGate", () => {
  it("fetches single gate by ID", async () => {
    const gate = { id: "g1", gate_type: "G1_CONSULTATION", status: "DRAFT" };
    mockGetGate.mockResolvedValueOnce(gate);

    const { result } = renderHook(() => useGate("g1"), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(gate);
  });

  it("does not fetch when gateId is undefined", () => {
    const { result } = renderHook(() => useGate(undefined), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockGetGate).not.toHaveBeenCalled();
  });
});

describe("useGateApprovals", () => {
  it("fetches approvals for a gate", async () => {
    const approvals = [{ id: "a1", decision: "approved", reviewer_id: "u2" }];
    mockGetGateApprovals.mockResolvedValueOnce(approvals);

    const { result } = renderHook(() => useGateApprovals("g1"), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(approvals);
  });
});

describe("gateKeys", () => {
  it("generates correct cache key structure", () => {
    expect(gateKeys.all).toEqual(["gates"]);
    expect(gateKeys.lists()).toEqual(["gates", "list"]);
    expect(gateKeys.detail("g1")).toEqual(["gates", "detail", "g1"]);
  });
});
