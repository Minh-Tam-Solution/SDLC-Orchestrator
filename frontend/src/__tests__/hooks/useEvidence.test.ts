/**
 * useEvidence Hook Tests
 *
 * @module frontend/src/__tests__/hooks/useEvidence.test
 * @description Tests for evidence list, detail, upload, and integrity check hooks
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
  trackFirstEvidenceUploaded: vi.fn(),
  trackEvent: vi.fn(),
  TELEMETRY_EVENTS: {},
}));

// Mock API functions
const mockGetEvidenceList = vi.fn();
const mockGetEvidence = vi.fn();
const mockUploadEvidence = vi.fn();
const mockCheckEvidenceIntegrity = vi.fn();
vi.mock("@/lib/api", () => ({
  getEvidenceList: (...args: unknown[]) => mockGetEvidenceList(...args),
  getEvidence: (...args: unknown[]) => mockGetEvidence(...args),
  uploadEvidence: (...args: unknown[]) => mockUploadEvidence(...args),
  checkEvidenceIntegrity: (...args: unknown[]) => mockCheckEvidenceIntegrity(...args),
}));

import {
  useEvidenceList,
  useEvidence,
  useGateEvidence,
  useEvidenceByType,
  evidenceKeys,
} from "@/hooks/useEvidence";

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

describe("useEvidenceList", () => {
  it("fetches evidence list successfully", async () => {
    const evidenceItems = [
      { id: "e1", evidence_type: "TEST_RESULTS", status: "uploaded" },
      { id: "e2", evidence_type: "CODE_REVIEW", status: "evidence_locked" },
    ];
    mockGetEvidenceList.mockResolvedValueOnce(evidenceItems);

    const { result } = renderHook(() => useEvidenceList(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(evidenceItems);
  });

  it("passes filter options to API", async () => {
    mockGetEvidenceList.mockResolvedValueOnce([]);

    const options = { gate_id: "g1", evidence_type: "SAST_REPORT" };
    renderHook(() => useEvidenceList(options), { wrapper });

    await waitFor(() => {
      expect(mockGetEvidenceList).toHaveBeenCalledWith(options);
    });
  });

  it("handles API error", async () => {
    mockGetEvidenceList.mockRejectedValueOnce(new Error("Forbidden"));

    const { result } = renderHook(() => useEvidenceList(), { wrapper });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

describe("useGateEvidence", () => {
  it("filters evidence by gate ID", async () => {
    mockGetEvidenceList.mockResolvedValueOnce([]);

    renderHook(() => useGateEvidence("g1"), { wrapper });

    await waitFor(() => {
      expect(mockGetEvidenceList).toHaveBeenCalledWith({ gate_id: "g1" });
    });
  });
});

describe("useEvidenceByType", () => {
  it("filters evidence by type", async () => {
    mockGetEvidenceList.mockResolvedValueOnce([]);

    renderHook(() => useEvidenceByType("TEST_RESULTS"), { wrapper });

    await waitFor(() => {
      expect(mockGetEvidenceList).toHaveBeenCalledWith({ evidence_type: "TEST_RESULTS" });
    });
  });
});

describe("useEvidence", () => {
  it("fetches single evidence item by ID", async () => {
    const evidence = { id: "e1", evidence_type: "DESIGN_DOCUMENT", sha256_hash: "abc123" };
    mockGetEvidence.mockResolvedValueOnce(evidence);

    const { result } = renderHook(() => useEvidence("e1"), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(evidence);
  });

  it("does not fetch when evidenceId is undefined", () => {
    const { result } = renderHook(() => useEvidence(undefined), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockGetEvidence).not.toHaveBeenCalled();
  });
});

describe("evidenceKeys", () => {
  it("generates correct cache key structure", () => {
    expect(evidenceKeys.all).toEqual(["evidence"]);
    expect(evidenceKeys.lists()).toEqual(["evidence", "list"]);
    expect(evidenceKeys.detail("e1")).toEqual(["evidence", "detail", "e1"]);
  });
});
